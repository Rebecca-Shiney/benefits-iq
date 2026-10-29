import copy
import hashlib
import json
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

from service.cloud_errors import CloudServiceError, SqlStoreError
from service.cloud_seed import criteria_index, seed_bundle, seed_search, seed_sources
from service import cloud_seed


@pytest.fixture
def bundle():
    return seed_bundle()


@pytest.fixture
def db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE source_records(kind,id,version,employer,payload,content_hash,as_of,active,
                                    PRIMARY KEY(kind,id,version));
        CREATE TABLE source_documents(case_id PRIMARY KEY,source_id,version,content_hash,content,as_of);
        CREATE TABLE portfolio_aggregates(employer,period,members,specialty_utilizers,cost,dataset,as_of,
                                         PRIMARY KEY(employer,period));
    """)
    yield db
    db.close()


def test_original_bundle_is_deterministic_and_does_not_read_edited_case_payloads(bundle):
    repeated = seed_bundle()
    assert bundle == repeated
    assert len(bundle["documents"]) == 12
    assert len(bundle["records"]) == 17
    assert len(bundle["criteria"]) == 3
    assert len(bundle["aggregates"]) == 6
    for document in bundle["documents"]:
        assert document["content"].startswith(b"%PDF")
        assert hashlib.sha256(document["content"]).hexdigest() == document["content_hash"]
    bundle["records"][0]["payload"] = '{"edited":"human correction"}'
    assert repeated == seed_bundle()
    assert all(record["id"].startswith("SYN-") for record in repeated["records"])
    incomplete = json.loads(next(r["payload"] for r in repeated["records"] if r["id"] == "SYN-MEMBER-002"))
    assert incomplete["fields"]["prescriber"]["value"] is None


def test_sql_source_rerun_is_additive_and_unchanged(db, bundle):
    seed_sources(db, bundle)
    before = db.iterdump()
    expected = list(before)
    seed_sources(db, bundle)
    assert list(db.iterdump()) == expected


@pytest.mark.parametrize("table,mutation,code", [
    ("source_records", "content_hash='wrong'", "SOURCE_VERSION_HASH_COLLISION"),
    ("source_records", "payload='{}'", "SOURCE_VERSION_HASH_COLLISION"),
    ("source_records", "active=0", "SOURCE_VERSION_HASH_COLLISION"),
    ("source_documents", "content=X'0000'", "SOURCE_DOCUMENT_MIGRATION_REQUIRED"),
    ("source_documents", "version='new-version'", "SOURCE_DOCUMENT_MIGRATION_REQUIRED"),
    ("portfolio_aggregates", "cost=1", "AGGREGATE_VERSION_MIGRATION_REQUIRED"),
])
def test_seed_collision_is_explicit_and_never_overwrites(db, bundle, table, mutation, code):
    seed_sources(db, bundle)
    db.execute(f"UPDATE {table} SET {mutation}")
    expected = list(db.iterdump())
    with pytest.raises(SqlStoreError, match=code):
        seed_sources(db, bundle)
    assert list(db.iterdump()) == expected


def test_new_source_version_requires_migration_instead_of_replacing_active_evidence(db, bundle):
    seed_sources(db, bundle)
    proposed = copy.deepcopy(bundle)
    proposed["records"][0]["version"] = "member-v2"
    with pytest.raises(SqlStoreError, match="SOURCE_VERSION_MIGRATION_REQUIRED"):
        seed_sources(db, proposed)


def search_mocks(bundle):
    indexes, documents = Mock(), Mock()
    indexes.get_index.return_value = criteria_index("benefits-criteria-v1")
    documents.get_document.side_effect = lambda key: next(d for d in bundle["criteria"] if d["id"] == key)
    return indexes, documents


def test_search_rerun_does_not_write_existing_sources(bundle):
    indexes, documents = search_mocks(bundle)
    seed_search(bundle, indexes, documents, "benefits-criteria-v1")
    indexes.create_index.assert_not_called()
    documents.upload_documents.assert_not_called()


def test_missing_index_and_documents_are_created_with_bound_metadata(bundle):
    indexes, documents = search_mocks(bundle)
    indexes.get_index.side_effect = ResourceNotFoundError()
    documents.get_document.side_effect = ResourceNotFoundError()
    documents.upload_documents.return_value = [
        SimpleNamespace(succeeded=True, key=record["id"]) for record in bundle["criteria"]
    ]
    seed_search(bundle, indexes, documents, "benefits-criteria-v1")
    fields = {field.name for field in indexes.create_index.call_args.args[0].fields}
    assert {"employer", "plan", "drug", "indication", "synthetic", "active", "content_hash"} <= fields
    assert documents.upload_documents.call_args.args[0] == bundle["criteria"]


def test_discovery_failure_is_not_absence(bundle):
    indexes, documents = search_mocks(bundle)
    indexes.get_index.side_effect = HttpResponseError("not allowed")
    with pytest.raises(HttpResponseError):
        seed_search(bundle, indexes, documents, "benefits-criteria-v1")
    indexes.create_index.assert_not_called()
    documents.upload_documents.assert_not_called()


def test_schema_and_source_drift_stop_without_overwrite(bundle):
    indexes, documents = search_mocks(bundle)
    indexes.get_index.return_value.fields.pop()
    with pytest.raises(CloudServiceError, match="SEARCH_SCHEMA_MIGRATION_REQUIRED"):
        seed_search(bundle, indexes, documents, "benefits-criteria-v1")
    indexes, documents = search_mocks(bundle)
    changed = {**bundle["criteria"][0], "passage": "unexpected change"}
    documents.get_document.side_effect = lambda key: changed
    with pytest.raises(CloudServiceError, match="SEARCH_SOURCE_VERSION_COLLISION"):
        seed_search(bundle, indexes, documents, "benefits-criteria-v1")
    documents.upload_documents.assert_not_called()


def test_partial_index_failure_never_reports_success(bundle):
    indexes, documents = search_mocks(bundle)
    documents.get_document.side_effect = ResourceNotFoundError()
    documents.upload_documents.return_value = [
        SimpleNamespace(succeeded=False, key=record["id"]) for record in bundle["criteria"]
    ]
    with pytest.raises(CloudServiceError, match="SEARCH_SOURCE_UPLOAD_FAILED"):
        seed_search(bundle, indexes, documents, "benefits-criteria-v1")


@pytest.mark.parametrize("name,value", [
    ("BENEFITS_PROFILE", "local"),
    ("BENEFITS_SETUP_MODE", "0"),
    ("OTEL_SDK_DISABLED", "false"),
])
def test_setup_is_never_an_implicit_runtime_side_effect(monkeypatch, name, value):
    for key, setting in {"BENEFITS_PROFILE": "starter", "BENEFITS_SETUP_MODE": "1",
                         "OTEL_SDK_DISABLED": "true"}.items():
        monkeypatch.setenv(key, setting)
    monkeypatch.setenv(name, value)
    client = Mock()
    monkeypatch.setattr(cloud_seed, "SearchIndexClient", client)
    with pytest.raises(RuntimeError, match="EXPLICIT_SYNTHETIC_STARTER_SETUP_REQUIRED"):
        cloud_seed.main()
    client.assert_not_called()


def test_runtime_identity_cannot_be_used_as_setup_identity(monkeypatch):
    identity = "11111111-1111-4111-8111-111111111111"
    for key, setting in {"BENEFITS_PROFILE": "starter", "BENEFITS_SETUP_MODE": "1",
                         "OTEL_SDK_DISABLED": "true", "BENEFITS_RUNTIME_SQL_CLIENT_ID": identity,
                         "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": identity}.items():
        monkeypatch.setenv(key, setting)
    monkeypatch.setattr(cloud_seed, "validate_configuration", lambda: None)
    with pytest.raises(RuntimeError, match="SEPARATE_SETUP_AND_RUNTIME_IDENTITIES_REQUIRED"):
        cloud_seed.main()
