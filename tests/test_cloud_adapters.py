import asyncio
import hashlib
import json
import threading
from contextlib import contextmanager
from types import SimpleNamespace as NS
from unittest.mock import Mock

import pyodbc
import pytest
from azure.core.exceptions import AzureError
from fastapi import HTTPException

from service import azure_services as cloud, domain, profile, sql_store, store
from service.cancellation import WorkflowCancellation, WorkflowCancelled, run_blocking
from service.cloud_errors import CloudServiceError, SqlStoreError


CLIENT_ID = "40000000-0000-0000-0000-000000000004"


@pytest.fixture
def cloud_environment(monkeypatch):
    settings = {
        "BENEFITS_PROFILE": "starter",
        "BENEFITS_SQL_SERVER": "synthetic.database.windows.net",
        "BENEFITS_SQL_DATABASE": "benefits",
        "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": CLIENT_ID,
        "BENEFITS_SEARCH_ENDPOINT": "https://synthetic.search.windows.net",
        "BENEFITS_SEARCH_INDEX": "criteria-v1",
        "BENEFITS_DOCUMENT_ENDPOINT": "https://synthetic.cognitiveservices.azure.com",
        "BENEFITS_MODEL_ENDPOINT": "https://synthetic.openai.azure.com",
        "BENEFITS_MODEL_DEPLOYMENT": "benefits-model",
        "BENEFITS_MODEL_REGION": "canadaeast", "BENEFITS_MODEL_TYPE": "Standard",
        "BENEFITS_MODEL_NAME": "gpt-4.1-mini", "BENEFITS_MODEL_VERSION": "2025-04-14",
        "BENEFITS_DOCUMENT_REGION": "canadacentral",
    }
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    return settings


def test_cloud_configuration_requires_approved_regional_model(cloud_environment):
    cloud.validate_configuration()
    connection_string = sql_store.SqlConfiguration.from_environment().connection_string()
    assert "Authentication=ActiveDirectoryMsi" in connection_string
    assert f"UID={CLIENT_ID}" in connection_string
    assert "Encrypt=yes;TrustServerCertificate=no" in connection_string
    assert "PWD=" not in connection_string


@pytest.mark.parametrize("name,value", [
    ("BENEFITS_MODEL_TYPE", "GlobalStandard"), ("BENEFITS_MODEL_REGION", "eastus"),
    ("BENEFITS_MODEL_VERSION", "latest"), ("BENEFITS_DOCUMENT_REGION", "eastus"),
    ("BENEFITS_SEARCH_ENDPOINT", "http://synthetic.search.windows.net"),
    ("BENEFITS_MODEL_ENDPOINT", "https://synthetic.openai.azure.com.attacker.invalid"),
    ("BENEFITS_MANAGED_IDENTITY_CLIENT_ID", ""),
])
def test_cloud_configuration_never_silently_substitutes(cloud_environment, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises((RuntimeError, ValueError)):
        cloud.validate_configuration()


@pytest.mark.parametrize("name,value", [
    ("BENEFITS_SQL_SERVER", "synthetic.database.windows.net;PWD=injected"),
    ("BENEFITS_SQL_DATABASE", "benefits;TrustServerCertificate=yes"),
    ("BENEFITS_MANAGED_IDENTITY_CLIENT_ID", ""),
])
def test_sql_configuration_rejects_missing_or_injected_values(cloud_environment, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError, match="SQL_CONFIGURATION_INVALID"):
        sql_store.SqlConfiguration.from_environment()


def test_unsupported_profile_has_no_fixture_fallback(monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "enterprise")
    with pytest.raises(RuntimeError, match="Enterprise integrations are not implemented"):
        profile.profile()


def test_sql_rows_and_results_preserve_mapping_and_positional_access():
    cursor = Mock(description=[("id",), ("version",)])
    cursor.fetchone.return_value = ("SYN-CASE-001", 7)
    result = sql_store.SqlResult(cursor)
    row = result.fetchone()
    assert row[0] == row["id"] == "SYN-CASE-001" and row[1] == 7
    assert dict(row) == {"id": "SYN-CASE-001", "version": 7}
    cursor.close.assert_called_once()
    assert result.fetchone() is None


def test_sql_single_writer_lock_and_idempotent_seed_translation():
    cursor = Mock(description=[("lock_result",)])
    cursor.fetchone.return_value = (0,)
    raw = Mock()
    raw.cursor.return_value = cursor
    db = sql_store.SqlConnection(raw)
    db.execute("BEGIN IMMEDIATE")
    lock_statement = cursor.execute.call_args.args[0]
    assert "sys.sp_getapplock" in lock_statement and "@LockOwner='Transaction'" in lock_statement
    cursor.description = None
    db.execute("INSERT OR IGNORE INTO cases VALUES(?,?)", ("SYN-CASE-001", "value"))
    statement, values = cursor.execute.call_args.args
    assert "WITH(UPDLOCK,HOLDLOCK)" in statement
    assert values == ("SYN-CASE-001", "SYN-CASE-001", "value")
    cursor.fetchone.return_value = (-1,)
    cursor.description = [("lock_result",)]
    with pytest.raises(SqlStoreError, match="CASE_WRITE_BUSY_RETRY"):
        db.execute("BEGIN IMMEDIATE")


@pytest.fixture
def sql_raw(cloud_environment, monkeypatch):
    raw = Mock()
    monkeypatch.setattr(pyodbc, "drivers", lambda: ["ODBC Driver 18 for SQL Server"])
    monkeypatch.setattr(pyodbc, "connect", Mock(return_value=raw))
    return raw


def test_sql_transaction_commits_or_rolls_back_and_closes(sql_raw):
    with sql_store.connection():
        pass
    sql_raw.commit.assert_called_once()
    sql_raw.close.assert_called_once()
    sql_raw.reset_mock()
    with pytest.raises(ValueError, match="synthetic-failure"):
        with sql_store.connection():
            raise ValueError("synthetic-failure")
    sql_raw.rollback.assert_called_once()
    sql_raw.commit.assert_not_called()
    sql_raw.close.assert_called_once()


def test_sql_error_is_a_sanitized_capability_failure(sql_raw):
    with pytest.raises(SqlStoreError, match="SQL_OPERATION_FAILED") as failure:
        with sql_store.connection():
            raise pyodbc.OperationalError("provider message must not reach clients")
    assert "provider message" not in str(failure.value)
    sql_raw.rollback.assert_called_once()


def test_sql_cancellation_rolls_back_before_commit(sql_raw):
    with WorkflowCancellation() as cancellation:
        with pytest.raises(WorkflowCancelled):
            with sql_store.connection():
                cancellation.cancel()
    sql_raw.rollback.assert_called_once()
    sql_raw.commit.assert_not_called()


def test_sql_driver_requirement_is_explicit(cloud_environment, monkeypatch):
    monkeypatch.setattr(pyodbc, "drivers", lambda: ["ODBC Driver 17 for SQL Server"])
    with pytest.raises(SqlStoreError, match="ODBC_DRIVER_18_REQUIRED"):
        with sql_store.connection():
            pytest.fail("Cloud may not use a local SQLite fallback.")


def test_search_uses_server_scope_and_escapes_odata_literals(monkeypatch):
    client = Mock()
    client.search.return_value = [{"id": "criteria", "version": "v1"}]
    monkeypatch.setattr(cloud, "search_client", lambda: client)
    payload = {"plan": "SYN-PLAN-A", "fields": {
        "drug": {"value": "Synthetic O'Brien"}, "indication": {"value": "Synthetic indication X"},
    }}
    assert cloud.retrieve_criteria(payload, "SYN-EMP-A")["version"] == "v1"
    parameters = client.search.call_args.kwargs
    assert parameters["search_text"] is None and parameters["top"] == 2
    assert "employer eq 'SYN-EMP-A'" in parameters["filter"]
    assert "Synthetic O''Brien" in parameters["filter"]
    assert "synthetic eq true and active eq true" in parameters["filter"]
    client.search.return_value = []
    assert cloud.retrieve_criteria(payload, "SYN-EMP-A") is None
    client.search.return_value = [{}, {}]
    with pytest.raises(CloudServiceError, match="AMBIGUOUS_CRITERIA_SOURCE"):
        cloud.retrieve_criteria(payload, "SYN-EMP-A")
    client.search.side_effect = AzureError("provider details")
    with pytest.raises(CloudServiceError, match="CRITERIA_SEARCH_UNAVAILABLE"):
        cloud.retrieve_criteria(payload, "SYN-EMP-A")


def test_source_record_query_requires_employer_and_active_version():
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"payload": '{"member_id":"SYN-MEMBER-001"}'}
    result = cloud.source_record(db, "member", "SYN-MEMBER-001", "SYN-EMP-A")
    assert result["member_id"] == "SYN-MEMBER-001"
    statement, values = db.execute.call_args.args
    assert "active=1" in statement and "employer=?" in statement
    assert values == ("member", "SYN-MEMBER-001", "SYN-EMP-A")
    db.execute.return_value.fetchone.return_value = None
    with pytest.raises(SqlStoreError, match="SYNTHETIC_SOURCE_RECORD_REQUIRED"):
        cloud.source_record(db, "member", "SYN-MEMBER-001", "SYN-EMP-B")


def document_result(**changes):
    values = {
        "key_value_pairs": [NS(key=NS(content="Member ID:"), value=NS(
            content="SYN-MEMBER-001", spans=[NS(offset=0, length=14)]), confidence=0.99)],
        "pages": [NS(lines=[NS(content="prescriber: Synthetic Clinic", spans=[NS(offset=15, length=27)])],
                     words=[NS(confidence=0.61, span=NS(offset=15, length=10))])],
        "model_id": "prebuilt-layout",
    }
    return NS(**(values | changes))


def test_ocr_preserves_actual_confidence_spans_and_missing_fields():
    result = cloud.parse_document(document_result(), "SYN-FORM-001", "form-v1", "hash")
    assert result["fields"]["member_id"]["value"] == "SYN-MEMBER-001"
    assert result["fields"]["member_id"]["confidence"] == 0.99
    assert result["fields"]["prescriber"]["confidence"] == 0.61
    assert result["fields"]["drug"]["value"] is None
    assert set(result["missing"]) == {"drug", "indication", "prescriber", "prior_therapy"}
    assert result["spans"][0] == {"field": "member_id", "offset": 0, "length": 14}
    assert result["method"] == "azure-document-intelligence"


def test_ocr_does_not_truncate_oversized_extracted_values():
    result = document_result(key_value_pairs=[NS(
        key=NS(content="drug"), value=NS(content="x" * 1001, spans=[]), confidence=0.99)])
    with pytest.raises(CloudServiceError, match="EXTRACTED_FIELD_LIMIT"):
        cloud.parse_document(result, "SYN-FORM-001", "v1", "hash")


@pytest.mark.parametrize("content,valid_hash", [
    (b"not a PDF", True), (b"%PDF-valid", False), (b"%PDF" + b"x" * 2_000_000, True),
], ids=["invalid-magic", "hash-mismatch", "over-limit"])
def test_pdf_integrity_is_checked_before_analysis(content, valid_hash):
    db = Mock()
    db.execute.return_value.fetchone.return_value = {
        "content": content, "content_hash": hashlib.sha256(content).hexdigest() if valid_hash else "wrong",
    }
    with pytest.raises(SqlStoreError, match="INTAKE_DOCUMENT_INTEGRITY_FAILED"):
        cloud.intake_document(db, {"id": "SYN-CASE-001"})


def test_actual_binary_ocr_rejects_cross_member_result(monkeypatch):
    content = b"%PDF-synthetic-only"
    document = {"content": content, "content_hash": hashlib.sha256(content).hexdigest(),
                "source_id": "SYN-FORM-001", "version": "v1"}
    db = Mock()
    db.execute.return_value.fetchone.side_effect = [document, None]
    @contextmanager
    def connect():
        yield db
    monkeypatch.setattr(cloud, "connection", connect)
    client = Mock()
    result = document_result()
    result.key_value_pairs[0].value.content = "SYN-MEMBER-999"
    client.begin_analyze_document.return_value.result.return_value = result
    monkeypatch.setattr(cloud, "document_client", lambda: client)
    with pytest.raises(CloudServiceError, match="EXTRACTED_MEMBER_MISMATCH"):
        cloud.extract_document({"id": "SYN-CASE-001", "member": "SYN-MEMBER-001"})
    assert client.begin_analyze_document.call_args.kwargs["body"].getvalue() == content
    assert len(db.execute.call_args_list) == 2


def test_aggregate_suppression_has_no_member_drillthrough(monkeypatch):
    db = Mock()
    db.execute.return_value.fetchall.return_value = [
        {"period": "2026-09", "members": 100, "specialty_utilizers": 9, "cost": 123.45,
         "dataset": "synthetic-aggregate-v1", "as_of": "2026-10-01"},
        {"period": "2026-10", "members": 100, "specialty_utilizers": 10, "cost": 123.45,
         "dataset": "synthetic-aggregate-v1", "as_of": "2026-10-01"},
    ]
    @contextmanager
    def connect():
        yield db
    monkeypatch.setattr(cloud, "connection", connect)
    output = cloud.aggregate("SYN-EMP-A")
    assert output["rows"][0] == {"period": "2026-09", "members": None, "specialty_utilizers": None, "cost": None}
    assert output["rows"][1]["specialty_utilizers"] == 10
    assert db.execute.call_args.args[1] == ("SYN-EMP-A",)
    assert "member_id" not in json.dumps(output)


def test_case_authorization_precedes_any_ocr_or_source_call(monkeypatch):
    db = Mock()
    db.execute.return_value.fetchone.return_value = {
        "id": "SYN-CASE-004", "employer": "SYN-EMP-B",
    }
    @contextmanager
    def connect():
        yield db
    monkeypatch.setattr(domain, "connection", connect)
    extract = Mock(side_effect=AssertionError("Must not call OCR before authorization."))
    monkeypatch.setattr(cloud, "extract_document", extract)
    with pytest.raises(HTTPException) as error:
        domain.extract_authorization_form(domain.IDENTITIES["reviewer-a"], "SYN-CASE-004")
    assert error.value.status_code == 403
    extract.assert_not_called()


def test_blocking_capability_does_not_block_loop_and_cancelled_write_rolls_back(tmp_path, monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "local")
    monkeypatch.setenv("BENEFITS_DB", str(tmp_path / "cancellation.db"))
    store.initialize()
    entered, release, finished = threading.Event(), threading.Event(), threading.Event()

    def write():
        try:
            with store.connection() as db:
                db.execute("UPDATE cases SET state='intake_checked' WHERE id='SYN-CASE-001'")
                entered.set()
                assert release.wait(5)
        finally:
            finished.set()

    async def scenario():
        with WorkflowCancellation() as cancellation:
            task = asyncio.create_task(run_blocking(write))
            for _ in range(500):
                if entered.is_set():
                    break
                await asyncio.sleep(0.005)
            assert entered.is_set(), "The event loop must remain available during the worker."
            cancellation.cancel()
            release.set()
            with pytest.raises(WorkflowCancelled):
                await task
        assert finished.is_set()

    asyncio.run(scenario())
    with store.connection() as db:
        assert db.execute("SELECT state FROM cases WHERE id='SYN-CASE-001'").fetchone()[0] == "received"
