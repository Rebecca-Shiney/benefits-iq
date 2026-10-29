import asyncio
import importlib
import json
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from service import domain, operations, showcase, store
from service.agents import SyntheticOrchestrator
from service.entra_auth import CallerConfiguration, EntraAuthError, ManagedCallerAuthenticator
from test_entra_auth import API, RUNTIME, TENANT, USER, key, token

PRINCIPAL = "60000000-0000-0000-0000-000000000006"


@pytest.fixture
def caller(monkeypatch, key):
    auth = ManagedCallerAuthenticator(CallerConfiguration(TENANT, API, RUNTIME, PRINCIPAL))
    monkeypatch.setattr(auth.keys, "get_signing_key_from_jwt",
                        lambda value: SimpleNamespace(key=key.public_key()))
    return auth


def test_roleless_signed_app_token_requires_exact_managed_caller(caller, key):
    assert caller.authenticate_caller(token(key, application=True, oid=PRINCIPAL, idtyp="app", roles=None)) is None


@pytest.mark.parametrize("changes", [
    {"oid": USER}, {"oid": RUNTIME}, {"azp": USER}, {"idtyp": "user"}, {"idtyp": None}, {"scp": ""},
    {"tid": API}, {"aud": "https://management.azure.com/"},
    {"iss": "https://example.invalid/"}, {"exp": 1}, {"ver": "1.0"},
])
def test_showcase_caller_rejects_claim_substitutions(caller, key, changes):
    claims = {"idtyp": "app", "oid": PRINCIPAL, **changes}
    with pytest.raises(EntraAuthError):
        caller.authenticate_caller(token(key, application=True, **claims))


@pytest.fixture
def public_client(tmp_path, monkeypatch, key, caller):
    module = importlib.import_module("service.app")
    from service import agents, azure_services
    for name in ("BENEFITS_SERVICE_SECRET", "OPENAI_API_KEY", "AZURE_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setenv("BENEFITS_DB", str(tmp_path / "synthetic.db"))
    monkeypatch.setattr(module.CallerConfiguration, "from_environment", lambda: caller.config)
    monkeypatch.setattr(module, "ManagedCallerAuthenticator", lambda config: caller)
    monkeypatch.setattr(azure_services, "validate_configuration", lambda: None)
    # Only external adapters are replaced: the public auth, routes and AG-UI bridge execute normally.
    for target in (store, domain, operations):
        monkeypatch.setattr(target, "cloud", lambda: False)
    monkeypatch.setattr(agents, "model_agent", lambda: SyntheticOrchestrator())
    module.requests_by_user.clear()
    with TestClient(module.app) as client:
        with store.connection() as db:
            db.execute("CREATE TABLE showcase_usage(name TEXT PRIMARY KEY, day TEXT, day_count INTEGER, "
                       "minute TEXT, minute_count INTEGER)")
            for employer, owner in (("SYN-EMP-A", "reviewer-a"), ("SYN-EMP-B", "reviewer-b")):
                db.execute("UPDATE case_operations SET owner=? WHERE case_id IN "
                           "(SELECT id FROM cases WHERE employer=?) AND owner=?",
                           (f"anonymous-demo:{owner}", employer, owner))
        yield client


def public_headers(key, view="reviewer-a", case="SYN-CASE-001"):
    return {"X-Benefits-Runtime-Authorization": token(key, application=True, oid=PRINCIPAL, idtyp="app", roles=None),
            "X-Benefits-User": view, "X-Benefits-Case": case}


def test_public_views_are_anonymous_but_backend_caller_auth_is_required(public_client, key):
    assert public_client.get("/api/session").status_code == 401
    assert public_client.get("/api/session", headers={"X-Benefits-User": "reviewer-a"}).status_code == 401
    result = public_client.get("/api/session", headers=public_headers(key)).json()
    assert result["id"] == "anonymous-demo:reviewer-a" and result["profile"] == "showcase"
    assert public_client.get("/api/session", headers=public_headers(key, "administrator")).status_code == 401
    assert public_client.get("/api/cases/SYN-CASE-004", headers=public_headers(key)).status_code == 403
    assert public_client.get("/api/cases", headers=public_headers(key, "employer-a")).status_code == 403
    contact = public_client.get("/api/cases/SYN-CASE-001", headers=public_headers(key, "contact-a")).json()
    assert not {"member360", "brief", "decision", "showcase_fields"} & contact.keys()
    assert all("actor" not in event for event in contact["timeline"])
    reviewer = public_client.get("/api/cases/SYN-CASE-001", headers=public_headers(key)).json()
    assert reviewer["showcase_fields"]["member_id"] == ["SYN-MEMBER-001"]


def test_freeform_writes_search_uploads_and_send_paths_are_rejected(public_client, key):
    headers = public_headers(key)
    fields = public_client.get("/api/cases/SYN-CASE-001", headers=headers).json()["member360"]["fields"]
    fields["prescriber"]["value"] = "Untrusted submitted health text"
    result = public_client.post("/api/cases/SYN-CASE-001/form", headers=headers, json={"version": 1, "fields": fields})
    assert result.status_code == 422 and "Untrusted submitted" not in result.text
    assert public_client.get("/api/workbench?search=untrusted", headers=headers).status_code == 422
    assert public_client.post("/api/cases/SYN-CASE-001/communication", headers=headers,
                              json={"text": "Untrusted submitted health text", "confirmed": True}).status_code == 403
    assert public_client.post("/api/upload", headers=headers, files={"file": ("sample.txt", b"untrusted")}).status_code == 415
    assert public_client.post("/api/cases", headers=headers, json={}).status_code == 405
    for path in ("/api/send", "/api/cases", "/api/fetch"):
        assert public_client.post(path, headers=headers, json={"url": "https://example.invalid/"}).status_code in {404, 405}
    assert public_client.post("/ag-ui-live", headers={**headers, "Content-Type": "application/json"},
                              content=b"x" * 24_001).status_code == 413
    assert public_client.post("/ag-ui-live", headers={**headers, "Content-Encoding": "gzip"}, content=b"x").status_code == 415
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM communications").fetchone()[0] == 0
        assert "Untrusted submitted" not in db.execute("SELECT payload FROM cases WHERE id='SYN-CASE-001'").fetchone()[0]


def chat_body(**overrides):
    return {"threadId": "SYN-CASE-001", "runId": str(uuid4()),
            "messages": [{"id": f"{uuid4()}-user", "role": "user", "content": showcase.OPTIONS["prompts"][0]}],
            "tools": [], "context": [], "state": {}, "forwardedProps": {}, **overrides}


@pytest.mark.parametrize("changes", [
    {"messages": [{"id": "m", "role": "user", "content": "Untrusted free text"}]},
    {"messages": ["invalid"]}, {"messages": {}},
    {"messages": [{"id": "m", "role": "assistant", "content": "Current status"}]},
    {"context": [{"description": "Untrusted supplied context", "value": "value"}]},
    {"tools": [{"name": "save_decision"}]}, {"state": {"decision": "approved"}},
    {"threadId": "SYN-CASE-004"}, {"customPrompt": "untrusted"},
])
def test_public_chat_accepts_only_one_case_bound_preset(public_client, key, changes):
    result = public_client.post("/ag-ui-live", headers=public_headers(key), json=chat_body(**changes))
    assert result.status_code == 422
    assert "Untrusted" not in result.text
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM showcase_usage").fetchone()[0] == 0


def test_valid_showcase_stream_preserves_maf_protocol_and_readonly_case(public_client, key):
    headers = public_headers(key)
    before = public_client.get("/api/cases/SYN-CASE-001", headers=headers).json()
    result = public_client.post("/ag-ui-live", headers=headers, json=chat_body())
    assert result.status_code == 200 and result.headers["content-type"].startswith("text/event-stream")
    events = [json.loads(line[6:]) for line in result.text.splitlines() if line.startswith("data: ")]
    assert events[0]["type"] == "RUN_STARTED" and events[-1]["type"] == "RUN_FINISHED"
    after = public_client.get("/api/cases/SYN-CASE-001", headers=headers).json()
    assert all(after[field] == before[field] for field in ("version", "state", "decision", "brief", "member360"))
    assert after["timeline"][-1]["actor"] == "anonymous-demo:reviewer-a"
    with store.connection() as db:
        assert db.execute("SELECT day_count FROM showcase_usage WHERE name='model'").fetchone()[0] == 1
    assert importlib.import_module("service.app").app.state.model_slots._value == 2


def test_global_persistent_budgets_are_bounded_and_reset_without_new_rows(public_client, monkeypatch):
    monkeypatch.setattr(store, "now", lambda: "2026-10-29T12:00:00+00:00")
    for _ in range(5):
        showcase.reserve("model")
    with pytest.raises(HTTPException) as limited:
        showcase.reserve("model")
    assert limited.value.detail["code"] == "PUBLIC_MODEL_MINUTE_LIMIT"
    monkeypatch.setattr(store, "now", lambda: "2026-10-29T12:01:00+00:00")
    showcase.reserve("model")
    with store.connection() as db:
        db.execute("UPDATE showcase_usage SET day_count=100 WHERE name='model'")
    with pytest.raises(HTTPException) as limited:
        showcase.reserve("model")
    assert limited.value.detail["code"] == "PUBLIC_MODEL_DAILY_LIMIT"
    monkeypatch.setattr(store, "now", lambda: "2026-10-30T00:00:00+00:00")
    showcase.reserve("model")
    with store.connection() as db:
        row = db.execute("SELECT * FROM showcase_usage").fetchone()
        assert row["day_count"] == row["minute_count"] == 1
        assert db.execute("SELECT count(*) FROM showcase_usage").fetchone()[0] == 1


def test_concurrency_and_exhausted_budget_fail_before_model(public_client, key):
    module = importlib.import_module("service.app")
    module.app.state.model_slots = asyncio.Semaphore(0)
    result = public_client.post("/ag-ui-live", headers=public_headers(key), json=chat_body())
    assert result.status_code == 429 and result.json()["error"]["code"] == "PUBLIC_MODEL_BUSY"
    module.app.state.model_slots = asyncio.Semaphore(2)
    for _ in range(5):
        showcase.reserve("model")
    result = public_client.post("/ag-ui-live", headers=public_headers(key), json=chat_body())
    assert result.status_code == 429
    assert module.app.state.model_slots._value == 2


def test_public_human_action_presets_idempotency_and_anonymous_audit(public_client, key):
    headers = public_headers(key)
    result = public_client.post("/api/cases/SYN-CASE-001/run", headers=headers,
                               json={"intent": "evidence", "version": 1})
    assert result.status_code == 200 and "RUN_FINISHED" in result.text
    case = public_client.get("/api/cases/SYN-CASE-001", headers=headers).json()
    body = {"version": case["version"], "brief_version": case["brief"]["version"], "outcome": "information_requested",
            "reason": "Untrusted user rationale", "confirmed": True, "idempotency_key": str(uuid4())}
    path = "/api/cases/SYN-CASE-001/decision"
    assert public_client.post(path, headers=headers, json=body).status_code == 422
    body["reason"] = showcase.OPTIONS["reasons"][1]
    saved = public_client.post(path, headers=headers, json=body)
    assert saved.status_code == 200 and saved.json()["reviewer"] == "anonymous-demo:reviewer-a"
    assert public_client.post(path, headers=headers, json=body).json() == saved.json()
    final = public_client.get("/api/cases/SYN-CASE-001", headers=headers).json()
    assert final["timeline"][-1]["actor"] == "anonymous-demo:reviewer-a"


def test_finite_public_task_and_evidence_growth(public_client, key):
    headers = public_headers(key)
    with store.connection() as db:
        db.execute("UPDATE tasks SET state='done' WHERE case_id='SYN-CASE-001'")
        count = db.execute("SELECT count(*) FROM tasks").fetchone()[0]
    duplicate = public_client.post("/api/cases/SYN-CASE-001/tasks", headers=headers, json={"kind": "member_follow_up"})
    assert duplicate.status_code == 409
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM tasks").fetchone()[0] == count
    for version in range(1, 11):
        response = public_client.post("/api/cases/SYN-CASE-001/run", headers=headers,
                                      json={"intent": "evidence", "version": version})
        assert response.status_code == 200 and "RUN_FINISHED" in response.text
    response = public_client.post("/api/cases/SYN-CASE-001/run", headers=headers,
                                  json={"intent": "evidence", "version": 11})
    assert "SHOWCASE_BRIEF_LIMIT" in response.text
    with store.connection() as db:
        assert db.execute("SELECT count(*) FROM briefs WHERE case_id='SYN-CASE-001'").fetchone()[0] == 10


def test_public_model_uses_installed_sdk_limits_and_individually_bounded_tools(monkeypatch):
    from unittest.mock import Mock
    from agent_framework.openai import OpenAIChatClient
    from service import agents, azure_services
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setenv("BENEFITS_MODEL_DEPLOYMENT", "synthetic-test")
    monkeypatch.setenv("BENEFITS_MODEL_ENDPOINT", "https://synthetic.openai.azure.com")
    actual_client = OpenAIChatClient(api_key="synthetic-test-not-a-credential", model="not-used")
    monkeypatch.setattr(azure_services, "credential", lambda: None)
    monkeypatch.setattr(agents, "OpenAIChatClient", lambda **kwargs: actual_client)
    captured = Mock()
    monkeypatch.setattr(agents, "Agent", captured)
    context = agents.request_context.set((showcase.selected_view("reviewer-a"), "SYN-CASE-001"))
    try:
        agents.model_agent()
    finally:
        agents.request_context.reset(context)
    config = actual_client.function_invocation_configuration
    assert config["max_iterations"] == 2 and config["max_function_calls"] == 3
    assert config["allow_concurrent_invocation"] is False and config["include_detailed_errors"] is False
    assert config["max_duration_seconds"] == 45.0
    assert captured.call_args.kwargs["default_options"] == {"store": False, "max_tokens": 500}
    tools = captured.call_args.kwargs["tools"]
    assert {tool.name for tool in tools} == {"get_case_status", "read_intake_completeness", "read_criteria_version"}
    assert all(tool.max_invocations == 1 for tool in tools)


def test_write_budget_precedes_mutation(public_client, key):
    showcase.reserve("write")
    with store.connection() as db:
        db.execute("UPDATE showcase_usage SET day_count=300 WHERE name='write'")
    result = public_client.post("/api/cases/SYN-CASE-001/assignment", headers=public_headers(key),
                                json={"version": 1, "owner": "unassigned", "priority": "standard"})
    assert result.status_code == 429 and result.json()["error"]["code"] == "PUBLIC_WRITE_DAILY_LIMIT"
    assert public_client.get("/api/cases/SYN-CASE-001", headers=public_headers(key)).json()["version"] == 1


@pytest.mark.parametrize("slow_body", [False, True])
def test_body_deadline_does_not_limit_the_response(monkeypatch, slow_body):
    from starlette.responses import JSONResponse
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setattr(showcase, "BODY_READ_SECONDS", 0.01)
    events = []

    async def receive():
        if slow_body:
            await asyncio.sleep(0.03)
        return {"type": "http.request", "body": b"{}", "more_body": False}

    async def endpoint(scope, incoming, send):
        assert (await incoming())["body"] == b"{}"
        await asyncio.sleep(0.03)
        await JSONResponse({"ok": True})(scope, incoming, send)

    async def send(event):
        events.append(event)

    asyncio.run(showcase.PublicBodyBoundary(endpoint)(
        {"type": "http", "headers": [(b"content-type", b"application/json")]}, receive, send))
    assert events[0]["status"] == (408 if slow_body else 200)


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_or_cancellation_releases_model_slot_and_case_context(public_client, monkeypatch, cancel):
    from contextlib import asynccontextmanager
    from service.agents import request_context
    module = importlib.import_module("service.app")
    monkeypatch.setattr(module, "SHOWCASE_RUN_SECONDS", 0.01)

    async def body():
        return chat_body()

    request = SimpleNamespace(headers={"x-benefits-case": "SYN-CASE-001"}, app=module.app,
                              url=SimpleNamespace(path="/ag-ui-live"), json=body)

    async def exercise():
        expected = asyncio.CancelledError if cancel else TimeoutError
        with pytest.raises(expected):
            async with asynccontextmanager(module.agent_auth)(request, showcase.selected_view("reviewer-a")):
                if cancel:
                    raise asyncio.CancelledError()
                await asyncio.sleep(0.1)
        with pytest.raises(LookupError):
            request_context.get()
        assert module.app.state.model_slots._value == 2
    asyncio.run(exercise())
