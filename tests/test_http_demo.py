"""Optional real Next.js -> Python integration checks against a running local demo."""

import json
import os

import httpx
import pytest


URL = os.environ.get("BENEFITS_TEST_URL")
pytestmark = pytest.mark.skipif(not URL, reason="Set BENEFITS_TEST_URL to a running loopback demo.")


@pytest.fixture
def web():
    with httpx.Client(base_url=URL or "http://127.0.0.1:3020", timeout=30) as client:
        yield client


def login(web, user="reviewer-a"):
    response = web.post("/api/session", headers={"Origin": URL}, json={"user": user})
    assert response.status_code == 200, response.text
    return response


def test_real_web_session_origin_and_cookie(web):
    assert web.get("/api/backend/cases").status_code == 401
    assert web.post("/api/session", headers={"Origin": "https://untrusted.invalid"},
                    json={"user": "reviewer-a"}).status_code == 403
    response = login(web)
    assert web.get("/api/backend/session").json()["role"] == "reviewer"
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=strict" in response.headers["set-cookie"]


def test_real_web_scope_cannot_be_forged(web):
    login(web)
    assert web.get("/api/backend/cases/SYN-CASE-004",
                   headers={"X-Benefits-User": "reviewer-b"}).status_code == 403
    login(web, "employer-a")
    assert web.get("/api/backend/cases").status_code == 403
    assert web.get("/api/backend/employers/SYN-EMP-B/aggregate").status_code == 403
    assert web.get("/api/backend/employers/SYN-EMP-A/aggregate").status_code == 200


def test_real_copilot_runtime_discovery(web):
    login(web)
    response = web.get("/api/copilotkit/info", headers={"X-Benefits-Case": "SYN-CASE-001"})
    assert response.status_code == 200, response.text
    assert "health_benefits_orchestrator" in response.text


def test_real_runtime_case_scope_before_discovery(web):
    login(web, "reviewer-b")
    response = web.get("/api/copilotkit/info", headers={"X-Benefits-Case": "SYN-CASE-001"})
    assert response.status_code == 403


def test_real_runtime_stream_roundtrip(web):
    login(web)
    body = {"threadId": "http-test-thread", "runId": "http-test-run",
            "messages": [{"id": "http-message", "role": "user", "content": "Current status"}],
            "state": {}, "tools": [], "context": [], "forwardedProps": {}}
    response = web.post("/api/copilotkit/agent/health_benefits_orchestrator/run",
                        headers={"X-Benefits-Case": "SYN-CASE-001"}, json=body)
    assert response.status_code == 200, response.text
    events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
    types = [e["type"] for e in events]
    assert "TEXT_MESSAGE_CONTENT" in types and types.count("RUN_FINISHED") == 1, response.text
    assert "RUN_ERROR" not in types


def test_real_runtime_has_no_cross_session_thread_history(web):
    login(web, "reviewer-b")
    response = web.get("/api/copilotkit/threads", headers={"X-Benefits-Case": "SYN-CASE-004"})
    assert "http-test-thread" not in response.text


def test_real_session_json_boundary(web):
    assert web.post("/api/session", content="{",
                    headers={"Content-Type": "application/json"}).status_code == 400
    assert web.post("/api/session", content="{}",
                    headers={"Content-Type": "application/json", "Content-Encoding": "gzip"}).status_code == 415
    assert web.post("/api/session", json={"user": "a" * 1024}).status_code == 413


def test_real_authenticated_routes_reject_compression_and_oversized_shapes(web):
    login(web)
    paths = ["/api/backend/cases/SYN-CASE-001/form",
             "/api/copilotkit/agent/health_benefits_orchestrator/run"]
    for path in paths:
        headers = {"X-Benefits-Case": "SYN-CASE-001", "Content-Encoding": "gzip"}
        response = web.post(path, headers=headers, json={})
        assert response.status_code == 415, response.text
        response = web.post(path, headers={"X-Benefits-Case": "SYN-CASE-001"},
                            json={"messages": [0] * 129})
        assert response.status_code == 422, response.text
        assert response.json()["error"]["code"] == "REQUEST_SHAPE_LIMIT"


def test_real_proxy_bounds_unknown_length_body_before_buffering(web):
    login(web)
    body = json.dumps({"value": "a" * 34_000}).encode()
    response = web.post("/api/backend/cases/SYN-CASE-001/form",
                        headers={"Content-Type": "application/json"},
                        content=iter([body[:20_000], body[20_000:]]))
    assert response.status_code == 413, response.text
