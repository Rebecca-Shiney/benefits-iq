"""Private-environment acceptance; never submit a clinical decision."""

import json
import logging.config
import os
import re
from uuid import uuid4

import httpx
from azure.core.exceptions import AzureError
from azure.identity import ManagedIdentityCredential

from .cloud_entrypoint import logging_configuration
from .entra_auth import CallerConfiguration, EntraAuthError, ManagedCallerAuthenticator
from .showcase import OPTIONS


class AcceptanceError(RuntimeError):
    pass


def origin(value):
    if not re.fullmatch(r"https://[a-z0-9.-]+\.azurecontainerapps\.io", value or ""):
        raise AcceptanceError("OWNED_CONTAINER_APP_HTTPS_ORIGIN_REQUIRED")
    return value


def expect(response, status=200):
    if response.status_code != status:
        raise AcceptanceError(f"CLOUD_ACCEPTANCE_UNEXPECTED_HTTP_{response.status_code}_EXPECTED_{status}")
    return response


def stream(client, path, body, headers=None, require_text=False, required_tool=None):
    events, content = [], bytearray()
    with client.stream("POST", path, json=body, headers=headers) as response:
        expect(response)
        if not response.headers.get("content-type", "").startswith("text/event-stream"):
            raise AcceptanceError("CLOUD_ACCEPTANCE_STREAM_REQUIRED")
        for chunk in response.iter_bytes(chunk_size=8192):
            if len(content) + len(chunk) > 250_000:
                raise AcceptanceError("CLOUD_ACCEPTANCE_STREAM_LIMIT")
            content.extend(chunk)
        for line in content.decode("utf-8").splitlines():
            if line.startswith("data: "):
                if len(events) >= 500:
                    raise AcceptanceError("CLOUD_ACCEPTANCE_STREAM_LIMIT")
                event = json.loads(line[6:])
                if not isinstance(event, dict):
                    raise AcceptanceError("CLOUD_ACCEPTANCE_EVENT_INVALID")
                events.append(event)
    if (not events or events[0].get("type") != "RUN_STARTED"
            or events[-1].get("type") != "RUN_FINISHED"
            or sum(event.get("type") == "RUN_FINISHED" for event in events) != 1
            or any(event.get("type") == "RUN_ERROR" for event in events)
            or (require_text and not any(event.get("type") == "TEXT_MESSAGE_CONTENT"
                                        and isinstance(event.get("delta"), str) and event["delta"].strip()
                                        for event in events))):
        raise AcceptanceError("CLOUD_ACCEPTANCE_STREAM_NOT_SUCCESSFUL")
    if required_tool:
        calls = [event for event in events if event.get("type") == "TOOL_CALL_START"
                 and event.get("toolCallName") == required_tool]
        if (len(calls) != 1 or not calls[0].get("toolCallId")
                or not any(event.get("type") == "TOOL_CALL_END"
                           and event.get("toolCallId") == calls[0]["toolCallId"] for event in events)):
            raise AcceptanceError("CLOUD_ACCEPTANCE_REQUIRED_READ_TOOL_NOT_COMPLETED")


def frontend_checks(client):
    expect(client.post("/api/session", json={"user": "reviewer-a"}))
    detail = expect(client.get("/api/backend/cases/SYN-CASE-001")).json()
    before_decision = detail["decision"]
    expect(client.get("/api/backend/cases/SYN-CASE-004"), 403)
    document = expect(client.get("/api/backend/cases/SYN-CASE-001/document"))
    if (not document.headers.get("content-type", "").startswith("application/pdf")
            or not document.content.startswith(b"%PDF-")):
        raise AcceptanceError("CLOUD_SYNTHETIC_BINARY_DOCUMENT_REQUIRED")
    wrote_workflow = not detail["brief"] and not before_decision
    if wrote_workflow:
        stream(client, "/api/backend/cases/SYN-CASE-001/run",
               {"intent": "intake", "version": detail["version"]})
        detail = expect(client.get("/api/backend/cases/SYN-CASE-001")).json()
        stream(client, "/api/backend/cases/SYN-CASE-001/run",
               {"intent": "evidence", "version": detail["version"]})
    saved = expect(client.get("/api/backend/cases/SYN-CASE-001")).json()
    if ((wrote_workflow and saved["version"] <= detail["version"]) or not saved["brief"]
            or not saved["brief"]["criteria_version"] or saved["decision"] != before_decision):
        raise AcceptanceError("CLOUD_WORKFLOW_DURABILITY_OR_HUMAN_BOUNDARY_FAILED")
    for prompt, required in zip(OPTIONS["prompts"][:2], ("get_case_status", "read_intake_completeness")):
        stream(client, "/api/chat", {"messages": [{
            "id": str(uuid4()), "role": "user", "content": prompt,
        }]}, {"X-Benefits-Case": "SYN-CASE-001"}, require_text=True, required_tool=required)
    after_chat = expect(client.get("/api/backend/cases/SYN-CASE-001")).json()
    if after_chat["version"] != saved["version"] or after_chat["decision"] != before_decision:
        raise AcceptanceError("CLOUD_CHAT_MUTATED_AUTHORITATIVE_WORKFLOW")
    expect(client.post("/api/chat", json={"messages": [{
        "id": str(uuid4()), "role": "user", "content": "not an approved public preset",
    }]}, headers={"X-Benefits-Case": "SYN-CASE-001"}), 422)
    expect(client.post("/api/backend/cases", json={}), 405)
    expect(client.post("/api/backend/cases/SYN-CASE-001/communication",
                       json={"text": "Demo preview only", "confirmed": True}), 403)
    expect(client.post("/api/backend/cases/SYN-CASE-001/form",
                       content=b"synthetic upload rejection probe",
                       headers={"Content-Type": "application/octet-stream"}), 415)
    expect(client.post("/api/session", json={"user": "contact-a"}))
    contact = expect(client.get("/api/backend/cases/SYN-CASE-001")).json()
    if any(field in contact for field in ("member360", "brief", "decision", "member")):
        raise AcceptanceError("CLOUD_CONTACT_VIEW_SHAPE_FAILED")
    expect(client.post("/api/session", json={"user": "employer-a"}))
    expect(client.get("/api/backend/cases"), 403)
    expect(client.get("/api/backend/employers/SYN-EMP-B/aggregate"), 403)
    aggregate = expect(client.get("/api/backend/employers/SYN-EMP-A/aggregate")).json()
    if not aggregate or "SYN-CASE-" in json.dumps(aggregate) or "SYN-MEM-" in json.dumps(aggregate):
        raise AcceptanceError("CLOUD_EMPLOYER_AGGREGATE_SHAPE_FAILED")
    return {"status": "private_cloud_acceptance_complete", "clinical_decision_submitted": False,
            "workflow_write_exercised": wrote_workflow,
            "checks": ["sql_source_binary_document", "saved_versioned_evidence",
                       "real_model_agui_stream", "required_case_bound_read_tools", "chat_read_only",
                       "selected_view_shapes", "direct_upload_send_create_rejection"]
                      + (["ocr_intake", "durable_workflow_write"] if wrote_workflow else [])}


def main():
    if (os.environ.get("BENEFITS_PROFILE") != "showcase"
            or os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true"):
        raise AcceptanceError("EXPLICIT_SHOWCASE_CLOUD_ACCEPTANCE_REQUIRED")
    if any(os.environ.get(name) for name in ("BENEFITS_SERVICE_SECRET", "AZURE_CLIENT_SECRET", "OPENAI_API_KEY")):
        raise AcceptanceError("CLOUD_ACCEPTANCE_DISALLOWS_STATIC_CREDENTIALS")
    logging.config.dictConfig(logging_configuration())
    frontend = origin(os.environ.get("BENEFITS_APP_ORIGIN"))
    backend = origin(os.environ.get("BENEFITS_SERVICE_URL"))
    config = CallerConfiguration.from_environment()
    with ManagedIdentityCredential(client_id=config.runtime_client_id) as credential:
        token = credential.get_token(f"api://{config.api_client_id}/.default")
    authorization = "Bearer " + token.token
    ManagedCallerAuthenticator(config).authenticate_caller(authorization)
    with httpx.Client(timeout=180, follow_redirects=False, trust_env=False) as direct:
        expect(direct.get(backend + "/api/cases", headers={"X-Benefits-User": "reviewer-a"}), 401)
        headers = {
            "X-Benefits-User": "reviewer-a", "X-Benefits-Runtime-Authorization": authorization,
        }
        expect(direct.get(backend + "/api/cases", headers=headers))
        expect(direct.post(backend + "/api/cases", headers=headers, json={}), 405)
        expect(direct.post(backend + "/api/cases/SYN-CASE-001/communication", headers=headers,
                           json={"text": "Demo preview only", "confirmed": True}), 403)
        expect(direct.post(backend + "/api/public-program", headers=headers,
                           json={"program": "https://example.invalid/not-a-program"}), 422)
        expect(direct.post(backend + "/api/cases/SYN-CASE-001/form",
                           headers={**headers, "Content-Type": "application/octet-stream"},
                           content=b"synthetic upload rejection probe"), 415)
    with httpx.Client(base_url=frontend, headers={"Origin": frontend}, timeout=180,
                      follow_redirects=False, trust_env=False) as client:
        print(json.dumps(frontend_checks(client)))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, AzureError, EntraAuthError, httpx.HTTPError, ValueError, KeyError) as error:
        code = str(error) if isinstance(error, AcceptanceError) else "CLOUD_ACCEPTANCE_FAILED"
        logging.getLogger("benefits").error("Acceptance failed code=%s type=%s", code, type(error).__name__)
        raise SystemExit(code) from None
