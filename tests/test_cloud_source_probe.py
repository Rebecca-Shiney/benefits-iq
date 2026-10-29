import json
from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from service import cloud_source_probe as probe


@pytest.fixture
def dependencies(monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(probe.cloud, "validate_configuration", Mock())
    monkeypatch.setattr(probe.logging.config, "dictConfig", Mock())
    permissions = {"source_write": 0, "decision_rewrite": 0, "ddl": 0, "decision_insert": 1}
    db = Mock()
    db.execute.side_effect = lambda statement, *args: Mock(fetchone=lambda: (
        permissions if "HAS_PERMS_BY_NAME" in statement else {"member": "SYN-MEM-001"}))

    @contextmanager
    def connection():
        yield db

    monkeypatch.setattr(probe, "connection", connection)
    monkeypatch.setattr(probe.cloud, "intake_document", Mock(return_value={
        "content": b"%PDF-synthetic-fixture", "source_id": "SYN-DOC", "version": "v1", "content_hash": "hash",
    }))
    expected = probe.seed_bundle()["criteria"][0]
    search = Mock(return_value=expected)
    monkeypatch.setattr(probe.cloud, "retrieve_criteria", search)
    monkeypatch.setattr(probe.cloud, "source_criterion", Mock(return_value=expected))
    document = Mock()
    monkeypatch.setattr(probe.cloud, "document_client", Mock(return_value=document))
    monkeypatch.setattr(probe.cloud, "parse_document", Mock(return_value={
        "fields": {"member_id": {"value": "SYN-MEM-001"}},
    }))
    return permissions, db, search, document


def test_fresh_runtime_source_proof_is_read_only_and_bypasses_ocr_cache(dependencies, capsys):
    permissions, db, search, document = dependencies
    probe.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "runtime_sources_verified" and receipt["case_mutated"] is False
    assert len(receipt["checks"]) == 4
    assert all(call.args[0].startswith("SELECT ") for call in db.execute.call_args_list)
    search.assert_called_once()
    document.begin_analyze_document.assert_called_once()
    assert document.begin_analyze_document.call_args.kwargs["body"].getvalue() == b"%PDF-synthetic-fixture"
    document.begin_analyze_document.return_value.result.assert_called_once_with(timeout=120)


@pytest.mark.parametrize("key,value", [
    ("source_write", 1), ("decision_rewrite", 1), ("ddl", 1), ("decision_insert", 0), ("source_write", None),
])
def test_runtime_cannot_have_bootstrap_permissions(dependencies, key, value):
    dependencies[0][key] = value
    with pytest.raises(RuntimeError, match="PERMISSION_BOUNDARY"):
        probe.main()
    dependencies[2].assert_not_called()
    dependencies[3].begin_analyze_document.assert_not_called()


def test_missing_live_search_does_not_substitute_sql_or_fixture_success(dependencies):
    dependencies[2].return_value = None
    with pytest.raises(RuntimeError, match="LIVE_GOVERNED_SEARCH"):
        probe.main()
    dependencies[3].begin_analyze_document.assert_not_called()


def test_ocr_member_mismatch_stops_proof(dependencies, monkeypatch):
    monkeypatch.setattr(probe.cloud, "parse_document", Mock(return_value={
        "fields": {"member_id": {"value": "SYN-WRONG-MEMBER"}},
    }))
    with pytest.raises(RuntimeError, match="LIVE_OCR_SOURCE"):
        probe.main()
