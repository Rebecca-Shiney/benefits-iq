import json
import logging

import pytest

from service.cloud_entrypoint import SafeFormatter, main


def test_provider_message_and_traceback_are_never_formatted():
    try:
        raise ValueError("synthetic private provider payload")
    except ValueError:
        import sys
        record = logging.LogRecord("uvicorn.error", logging.ERROR, "", 1,
                                   "synthetic private provider traceback", (), sys.exc_info())
    output = SafeFormatter().format(record)
    assert "private" not in output and "traceback" not in output
    assert json.loads(output)["exception_type"] == "ValueError"
    assert json.loads(output)["event"] == "library_error"


def test_approved_operational_metadata_remains_observable():
    record = logging.LogRecord("benefits", logging.ERROR, "", 1,
                               "Cloud capability unavailable code=%s trace=%s", ("SEARCH_UNAVAILABLE", "trace-1"), None)
    output = json.loads(SafeFormatter().format(record))
    assert "code=SEARCH_UNAVAILABLE" in output["message"] and "trace=trace-1" in output["message"]


@pytest.mark.parametrize("code", ["InvalidApiVersionParameter", "SYN-sensitive-value"])
def test_nested_provider_status_is_observable_without_response_or_unknown_code(code):
    inner = RuntimeError("synthetic private provider response")
    inner.status_code = 400
    inner.body = {"code": code, "message": "synthetic private provider response"}
    wrapper = RuntimeError("synthetic private wrapper")
    wrapper.__cause__ = inner
    record = logging.LogRecord("agent_framework", logging.ERROR, "", 1,
                               "synthetic private prompt", (), (RuntimeError, wrapper, None))
    output = SafeFormatter().format(record)
    parsed = json.loads(output)
    assert parsed["upstream_status"] == 400
    assert "private" not in output and "SYN-sensitive-value" not in output
    assert parsed.get("upstream_code") == ("InvalidApiVersionParameter" if code in {
        "InvalidApiVersionParameter"} else None)


def test_cloud_entrypoint_cannot_start_local_demo(monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "local")
    with pytest.raises(RuntimeError, match="CLOUD_ENTRYPOINT_REQUIRES_STARTER"):
        main()


def test_cloud_entrypoint_cannot_enable_sensitive_sdk_tracing(monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "starter")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
    with pytest.raises(RuntimeError, match="CLOUD_TRACING_MUST_BE_DISABLED"):
        main()
