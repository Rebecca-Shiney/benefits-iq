"""Original synthetic setup data; never source this bundle from an edited case."""

import hashlib
import io
import json
import logging.config
import os
from pathlib import Path
from uuid import UUID

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchableField, SearchFieldDataType, SimpleField,
)
from reportlab.pdfgen.canvas import Canvas

from . import catalog
from .azure_services import credential, endpoint, validate_configuration
from .cloud_errors import CloudServiceError, SqlStoreError
from .cloud_entrypoint import logging_configuration
from .entra_auth import EntraConfiguration
from .sql_store import connection
from .store import now, seed_records, synthetic_case_records


SOURCE_DATE = "2026-10-01"
ROOT = Path(__file__).resolve().parents[1]


def encoded(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(content):
    return hashlib.sha256(content).hexdigest()


def synthetic_pdf(payload):
    output = io.BytesIO()
    pdf = Canvas(output, pagesize=(612, 792), invariant=1, pageCompression=1)
    pdf.setTitle("Benefits IQ fictional synthetic intake")
    pdf.setAuthor("Benefits IQ synthetic generator")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, 750, "SYNTHETIC DATA ONLY - NOT A CLINICAL DOCUMENT")
    for index, name in enumerate(("member_id", "drug", "indication", "prescriber", "prior_therapy")):
        value = payload["fields"][name]["value"] or "MISSING"
        pdf.drawString(40, 700 - index * 36, f"{name}: {value}")
    pdf.save()
    return output.getvalue()


def seed_bundle():
    records, documents, criteria = [], [], []

    def source(kind, source_id, version, employer, payload, as_of=SOURCE_DATE):
        content = encoded(payload)
        records.append({"kind": kind, "id": source_id, "version": version, "employer": employer,
                        "payload": content, "content_hash": digest(content.encode()), "as_of": as_of})

    for row in synthetic_case_records():
        payload = row["payload"]
        source("member", row["member"], "member-v1", row["employer"], payload)
        content = synthetic_pdf(payload)
        documents.append({"case_id": row["id"], "source_id": payload["form_source"],
                          "version": payload["form_version"], "content": content,
                          "content_hash": digest(content), "as_of": SOURCE_DATE})
    for plan_id, plan in catalog.PLANS.items():
        source("plan", plan_id, plan["version"], "SYN-EMP-" + plan_id[-1], plan, plan["as_of"])
    for (plan, drug, indication), criterion in catalog.CRITERIA.items():
        employer = "SYN-EMP-" + plan[-1]
        source("criteria", "|".join((plan, drug, indication)), criterion["version"],
               employer, criterion, criterion["as_of"])
        document = {**criterion, "employer": employer, "plan": plan, "drug": drug,
                    "indication": indication, "synthetic": True, "active": True}
        document["content_hash"] = digest(encoded(document).encode())
        criteria.append(document)
    aggregates = []
    for employer, members in (("SYN-EMP-A", 160), ("SYN-EMP-B", 140)):
        for period, count, utilizers, cost in (
            ("2026 Q2", members, 24, 48000),
            ("2026 Q3", members + 10, 28, 56000),
            ("Rare subgroup", 8, 3, 6000),
        ):
            aggregates.append((employer, period, count, utilizers, cost,
                               "starter-synthetic-portfolio-v1", SOURCE_DATE))
    return {"records": records, "documents": documents, "criteria": criteria, "aggregates": aggregates}


def seed_sources(db, bundle):
    for record in bundle["records"]:
        identity = (record["kind"], record["id"], record["version"])
        old = db.execute(
            "SELECT content_hash,payload,employer,as_of,active FROM source_records "
            "WHERE kind=? AND id=? AND version=?", identity,
        ).fetchone()
        if old is not None:
            if (any(old[name] != record[name] for name in ("content_hash", "payload", "employer", "as_of"))
                    or not old["active"]):
                raise SqlStoreError("SOURCE_VERSION_HASH_COLLISION")
            continue
        if db.execute("SELECT version FROM source_records WHERE kind=? AND id=? AND active=1",
                      identity[:2]).fetchone() is not None:
            raise SqlStoreError("SOURCE_VERSION_MIGRATION_REQUIRED")
        db.execute("INSERT INTO source_records(kind,id,version,employer,payload,content_hash,as_of,active) "
                   "VALUES(?,?,?,?,?,?,?,1)", tuple(record[name] for name in
                   ("kind", "id", "version", "employer", "payload", "content_hash", "as_of")))
    for document in bundle["documents"]:
        old = db.execute("SELECT source_id,version,content_hash,content,as_of FROM source_documents WHERE case_id=?",
                         (document["case_id"],)).fetchone()
        if old is not None:
            if any(old[name] != document[name] for name in ("source_id", "version", "content_hash", "content", "as_of")):
                raise SqlStoreError("SOURCE_DOCUMENT_MIGRATION_REQUIRED")
            continue
        db.execute("INSERT INTO source_documents(case_id,source_id,version,content_hash,content,as_of) "
                   "VALUES(?,?,?,?,?,?)", tuple(document[name] for name in
                   ("case_id", "source_id", "version", "content_hash", "content", "as_of")))
    for aggregate in bundle["aggregates"]:
        old = db.execute("SELECT members,specialty_utilizers,cost,dataset,as_of FROM portfolio_aggregates "
                         "WHERE employer=? AND period=?", aggregate[:2]).fetchone()
        if old is not None:
            if tuple(old[name] for name in ("members", "specialty_utilizers", "cost", "dataset", "as_of")) != aggregate[2:]:
                raise SqlStoreError("AGGREGATE_VERSION_MIGRATION_REQUIRED")
            continue
        db.execute("INSERT INTO portfolio_aggregates VALUES(?,?,?,?,?,?,?)", aggregate)


def criteria_index(name):
    fields = [SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True)]
    fields += [SimpleField(name=field, type=SearchFieldDataType.String, filterable=True)
               for field in ("version", "as_of", "valid_until", "employer", "plan", "drug", "indication", "content_hash")]
    fields += [SimpleField(name=field, type=SearchFieldDataType.Boolean, filterable=True)
               for field in ("synthetic", "active")]
    fields.append(SearchableField(name="passage", type=SearchFieldDataType.String))
    return SearchIndex(name=name, fields=fields)


def seed_search(bundle, indexes, documents, name):
    expected = criteria_index(name)
    try:
        existing = indexes.get_index(name)
    except ResourceNotFoundError:
        indexes.create_index(expected)
    else:
        def schema(index):
            return sorted((field.name, field.type, bool(field.key), bool(field.filterable), bool(field.searchable))
                          for field in index.fields)
        if schema(existing) != schema(expected):
            raise CloudServiceError("SEARCH_SCHEMA_MIGRATION_REQUIRED")
    pending = []
    for document in bundle["criteria"]:
        try:
            old = documents.get_document(document["id"])
        except ResourceNotFoundError:
            pending.append(document)
        else:
            if any(old.get(key) != value for key, value in document.items()):
                raise CloudServiceError("SEARCH_SOURCE_VERSION_COLLISION")
    if pending:
        results = documents.upload_documents(pending)
        if (len(results) != len(pending) or any(not item.succeeded for item in results)
                or {item.key for item in results} != {item["id"] for item in pending}):
            raise CloudServiceError("SEARCH_SOURCE_UPLOAD_FAILED")


def execute_batch(db, statement, params=()):
    cursor = db.raw.cursor()
    try:
        cursor.execute(statement, params)
        while cursor.nextset():
            pass
    finally:
        cursor.close()


def main():
    if (os.environ.get("BENEFITS_PROFILE") not in {"starter", "showcase"}
            or os.environ.get("BENEFITS_SETUP_MODE") != "1"
            or os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true"):
        raise RuntimeError("EXPLICIT_SYNTHETIC_STARTER_SETUP_REQUIRED")
    validate_configuration()
    runtime = str(UUID(os.environ["BENEFITS_RUNTIME_SQL_CLIENT_ID"]))
    if runtime == os.environ["BENEFITS_MANAGED_IDENTITY_CLIENT_ID"].lower():
        raise RuntimeError("SEPARATE_SETUP_AND_RUNTIME_IDENTITIES_REQUIRED")
    from .profile import showcase
    if showcase():
        from .showcase import identities
        approved = identities()
        owners = {identity.employer: identity.id for identity in approved.values() if identity.role == "reviewer"}
    else:
        approved = EntraConfiguration.from_environment().identities
        owners = json.loads(os.environ["BENEFITS_SEED_REVIEWER_OWNERS"])
    if not isinstance(owners, dict) or set(owners) - {"SYN-EMP-A", "SYN-EMP-B"}:
        raise RuntimeError("APPROVED_SEED_OWNERS_REQUIRED")
    if not showcase():
        owners = {employer: str(UUID(owner)) for employer, owner in owners.items()}
    if any(owner not in approved or approved[owner].role != "reviewer" or approved[owner].employer != employer
           for employer, owner in owners.items()):
        raise RuntimeError("SEED_OWNER_NOT_AN_APPROVED_REVIEWER")
    logging.config.dictConfig(logging_configuration())
    bundle = seed_bundle()
    search_endpoint = endpoint("BENEFITS_SEARCH_ENDPOINT", "search.windows.net")
    name = os.environ["BENEFITS_SEARCH_INDEX"]
    with SearchIndexClient(search_endpoint, credential(), retry_total=2) as indexes, \
            SearchClient(search_endpoint, name, credential(), retry_total=2) as search, connection() as db:
        db.execute("BEGIN IMMEDIATE")
        execute_batch(db, (ROOT / "infra" / "schema.sql").read_text(encoding="utf-8"))
        seed_records(db, reviewer_owners=owners)
        seed_sources(db, bundle)
        seed_search(bundle, indexes, search, name)
        execute_batch(db, (ROOT / "infra" / "grant-runtime.sql").read_text(encoding="utf-8"), (runtime,))
        db.execute("IF NOT EXISTS(SELECT 1 FROM schema_migrations WHERE version=1) "
                   "INSERT INTO schema_migrations VALUES(1,?)", (now(),))
    print(json.dumps({"status": "synthetic_setup_complete", "source_records": len(bundle["records"]),
                      "documents": len(bundle["documents"]), "criteria": len(bundle["criteria"]),
                      "aggregate_cells": len(bundle["aggregates"])}))


if __name__ == "__main__":
    try:
        main()
    except (CloudServiceError, SqlStoreError) as error:
        raise SystemExit(error.code) from None
    except AzureError:
        raise SystemExit("AZURE_SYNTHETIC_SETUP_UNAVAILABLE") from None
