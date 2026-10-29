import json

import httpx
import pytest

from service import cloud_acceptance as acceptance


ORIGIN = "https://synthetic.internal.example.canadaeast.azurecontainerapps.io"


def events(*values):
    return "".join("data: " + json.dumps(value) + "\n\n" for value in values)


START = {"type": "RUN_STARTED"}
TEXT = {"type": "TEXT_MESSAGE_CONTENT", "delta": "Synthetic response"}
FINISH = {"type": "RUN_FINISHED"}


def test_stream_requires_ordered_finish_and_model_text_when_requested():
    for payload in (events(START, FINISH), events(START, TEXT, FINISH)):
        with httpx.Client(base_url=ORIGIN, transport=httpx.MockTransport(
                lambda request: httpx.Response(200, text=payload,
                                              headers={"Content-Type": "text/event-stream"}))) as client:
            acceptance.stream(client, "/run", {})
    with httpx.Client(base_url=ORIGIN, transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text=events(START, FINISH),
                                          headers={"Content-Type": "text/event-stream"}))) as client:
        with pytest.raises(acceptance.AcceptanceError, match="NOT_SUCCESSFUL"):
            acceptance.stream(client, "/chat", {}, require_text=True)


@pytest.mark.parametrize("payload", [
    events(FINISH), events(START), events(START, {"type": "RUN_ERROR"}, FINISH),
    events(START, FINISH, TEXT), events(START, FINISH, FINISH),
    events(START, *([TEXT] * 500), FINISH), events(START, {"type": "TEXT_MESSAGE_CONTENT", "delta": "x" * 250_000}, FINISH),
    "data: []\n\n",
], ids=["finish-only", "unfinished", "run-error", "late-text", "duplicate-finish",
        "event-limit", "byte-limit", "invalid-shape"])
def test_stream_rejects_errors_incomplete_runs_limits_and_invalid_events(payload):
    with httpx.Client(base_url=ORIGIN, transport=httpx.MockTransport(
            lambda request: httpx.Response(200, text=payload,
                                          headers={"Content-Type": "text/event-stream"}))) as client:
        with pytest.raises(acceptance.AcceptanceError):
            acceptance.stream(client, "/run", {})


@pytest.mark.parametrize("value", [None, "http://example.azurecontainerapps.io",
                                 "https://example.azurecontainerapps.io.attacker.invalid",
                                 ORIGIN + "/path", ORIGIN + ":443", "https://example.invalid"])
def test_acceptance_rejects_non_container_app_origins(value):
    with pytest.raises(acceptance.AcceptanceError):
        acceptance.origin(value)


@pytest.mark.parametrize("existing", [False, True])
def test_acceptance_preserves_human_state_and_does_not_repeat_workflow_on_reruns(existing):
    state = {"version": 4, "brief": {"criteria_version": "synthetic-v1"} if existing else None,
             "decision": {"outcome": "request-more-info"} if existing else None}
    requests, persona = [], ["reviewer-a"]

    def handle(request):
        path = request.url.path
        requests.append((request.method, path))
        if path == "/api/session":
            persona[0] = json.loads(request.content)["user"]
            return httpx.Response(200, json={})
        if path.endswith("/run"):
            state["version"] += 1
            if json.loads(request.content)["intent"] == "evidence":
                state["brief"] = {"criteria_version": "synthetic-v1"}
            return httpx.Response(200, text=events(START, FINISH),
                                  headers={"Content-Type": "text/event-stream"})
        if path == "/api/chat":
            question = json.loads(request.content)["messages"][0]["content"]
            if question not in acceptance.OPTIONS["prompts"]:
                return httpx.Response(422)
            return httpx.Response(200, text=events(START, TEXT, FINISH),
                                  headers={"Content-Type": "text/event-stream"})
        if path.endswith("/document"):
            return httpx.Response(200, content=b"%PDF-synthetic-fixture",
                                  headers={"Content-Type": "application/pdf"})
        if path.endswith("/SYN-CASE-004") or path.endswith("/communication") or path.endswith("/SYN-EMP-B/aggregate"):
            return httpx.Response(403)
        if path.endswith("/form"):
            return httpx.Response(415)
        if path == "/api/backend/cases":
            return httpx.Response(403 if request.method == "GET" else 404)
        if path.endswith("/aggregate"):
            return httpx.Response(200, json={"dataset": "synthetic-aggregate", "members": 100})
        if path.endswith("/SYN-CASE-001"):
            return httpx.Response(200, json=state if persona[0] == "reviewer-a" else {"status": "synthetic"})
        raise AssertionError(f"Unexpected acceptance request: {request.method} {path}")

    with httpx.Client(base_url=ORIGIN, transport=httpx.MockTransport(handle)) as client:
        receipt = acceptance.frontend_checks(client)
    assert receipt["clinical_decision_submitted"] is False
    assert receipt["workflow_write_exercised"] is not existing
    assert state["version"] == (4 if existing else 6)
    assert sum(path.endswith("/run") for _, path in requests) == (0 if existing else 2)
    assert not any(path.endswith("/decision") for _, path in requests)
