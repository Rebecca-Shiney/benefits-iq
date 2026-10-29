import hashlib
import io
import json
import os
import re
from functools import lru_cache
from uuid import UUID

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.exceptions import AzureError
from azure.identity import ManagedIdentityCredential
from azure.search.documents import SearchClient

from .contracts import Extraction
from .cloud_errors import CloudServiceError, SqlStoreError
from .store import connection, now


def endpoint(name, suffix):
    value = os.environ.get(name, "")
    if not re.fullmatch(r"https://[a-z0-9-]+\." + re.escape(suffix) + r"/?", value):
        raise RuntimeError(f"{name} must be an explicit Azure HTTPS resource endpoint.")
    return value.rstrip("/")


def validate_configuration():
    endpoint("BENEFITS_SEARCH_ENDPOINT", "search.windows.net")
    endpoint("BENEFITS_DOCUMENT_ENDPOINT", "cognitiveservices.azure.com")
    endpoint("BENEFITS_MODEL_ENDPOINT", "openai.azure.com")
    client_id = os.environ.get("BENEFITS_MANAGED_IDENTITY_CLIENT_ID", "")
    if str(UUID(client_id)) != client_id.lower():
        raise RuntimeError("BENEFITS_MANAGED_IDENTITY_CLIENT_ID is required.")
    for name in ("BENEFITS_SEARCH_INDEX", "BENEFITS_MODEL_DEPLOYMENT"):
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", os.environ.get(name, "")):
            raise RuntimeError(f"{name} must be explicitly configured.")
    expected = {
        "BENEFITS_MODEL_REGION": "canadaeast", "BENEFITS_MODEL_TYPE": "Standard",
        "BENEFITS_MODEL_NAME": "gpt-4.1-mini", "BENEFITS_MODEL_VERSION": "2025-04-14",
        "BENEFITS_DOCUMENT_REGION": "canadacentral",
    }
    if any(os.environ.get(name) != value for name, value in expected.items()):
        raise RuntimeError("UNAPPROVED_SERVICE_PLACEMENT_OR_MODEL: approved Canadian regional configuration is required.")


@lru_cache(maxsize=1)
def credential():
    return ManagedIdentityCredential(client_id=os.environ["BENEFITS_MANAGED_IDENTITY_CLIENT_ID"])


@lru_cache(maxsize=1)
def search_client():
    return SearchClient(endpoint("BENEFITS_SEARCH_ENDPOINT", "search.windows.net"),
                        os.environ["BENEFITS_SEARCH_INDEX"], credential(),
                        connection_timeout=10, read_timeout=30, retry_total=2)


@lru_cache(maxsize=1)
def document_client():
    return DocumentIntelligenceClient(endpoint("BENEFITS_DOCUMENT_ENDPOINT", "cognitiveservices.azure.com"),
                                      credential(), connection_timeout=10, read_timeout=60, retry_total=2)


def source_record(db, kind, source_id, employer):
    row = db.execute(
        "SELECT payload FROM source_records WHERE kind=? AND id=? AND active=1 "
        "AND employer=?", (kind, source_id, employer),
    ).fetchone()
    if row is None:
        raise SqlStoreError("SYNTHETIC_SOURCE_RECORD_REQUIRED")
    return json.loads(row["payload"])


def member_payload(db, row):
    source = source_record(db, "member", row["member"], row["employer"])
    current = json.loads(row["payload"])
    if source["member_id"] != row["member"]:
        raise SqlStoreError("SOURCE_MEMBER_BINDING_INVALID")
    return {**source, "fields": current["fields"], "form_version": current["form_version"]}


def plan_document(plan_id, employer):
    with connection() as db:
        return source_record(db, "plan", plan_id, employer)


def source_criterion(payload, employer):
    key = "|".join((payload["plan"], payload["fields"]["drug"]["value"] or "",
                    payload["fields"]["indication"]["value"] or ""))
    with connection() as db:
        row = db.execute(
            "SELECT payload FROM source_records WHERE kind='criteria' AND id=? AND employer=? AND active=1",
            (key, employer),
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def retrieve_criteria(payload, employer):
    def quoted(value):
        return "'" + value.replace("'", "''") + "'"
    values = {"employer": employer, "plan": payload["plan"],
              "drug": payload["fields"]["drug"]["value"] or "",
              "indication": payload["fields"]["indication"]["value"] or ""}
    filter_text = " and ".join(f"{key} eq {quoted(value)}" for key, value in values.items())
    try:
        results = list(search_client().search(
            search_text=None, filter=filter_text + " and synthetic eq true and active eq true",
            select=["id", "version", "as_of", "valid_until", "passage"], top=2,
        ))
    except AzureError as error:
        raise CloudServiceError("CRITERIA_SEARCH_UNAVAILABLE") from error
    if len(results) > 1:
        raise CloudServiceError("AMBIGUOUS_CRITERIA_SOURCE")
    return results[0] if results else None


def parse_document(result, source_id, source_version, content_hash):
    required = ("member_id", "drug", "indication", "prescriber", "prior_therapy")
    fields = {name: {"value": None, "confidence": 0.0, "source": f"{source_id}#{name}"} for name in required}
    spans = []

    def save(name, value, confidence, positions):
        if name not in fields:
            return
        value = value.strip() if value else ""
        if len(value) > 1000:
            raise CloudServiceError("EXTRACTED_FIELD_LIMIT")
        fields[name] = {
            "value": None if value.upper() in {"", "MISSING"} else value,
            "confidence": float(confidence or 0) if value.upper() not in {"", "MISSING"} else 0.0,
            "source": f"{source_id}#{name}",
        }
        spans.extend({"field": name, "offset": int(span.offset), "length": int(span.length)}
                     for span in positions or [])

    for pair in result.key_value_pairs or []:
        if pair.key and pair.value:
            name = re.sub(r"[^a-z_]", "", pair.key.content.lower().replace(" ", "_").rstrip(":"))
            save(name, pair.value.content, pair.confidence, pair.value.spans)
    for page in result.pages or []:
        for line in page.lines or []:
            match = re.fullmatch(r"\s*(member_id|drug|indication|prescriber|prior_therapy)\s*:\s*(.*?)\s*",
                                 line.content, flags=re.IGNORECASE)
            if not match:
                continue
            name, value = match.groups()
            name = name.lower()
            if fields[name]["value"] is not None:
                continue
            ranges = [(span.offset, span.offset + span.length) for span in line.spans or []]
            confidence = min((word.confidence for word in page.words or []
                              if word.confidence is not None and word.span is not None
                              and any(start <= word.span.offset < end for start, end in ranges)), default=0.0)
            save(name, value, confidence, line.spans)
    missing = sorted(name for name, value in fields.items() if not value["value"] or value["confidence"] < 0.85)
    extraction = Extraction(fields=fields, missing=missing, source_version=source_version, as_of=now()).model_dump()
    return {**extraction, "method": "azure-document-intelligence", "document_sha256": content_hash,
            "model_id": result.model_id, "spans": spans}


def intake_document(db, row):
    document = db.execute("SELECT * FROM source_documents WHERE case_id=?", (row["id"],)).fetchone()
    if document is None:
        raise SqlStoreError("SYNTHETIC_INTAKE_DOCUMENT_REQUIRED")
    content = bytes(document["content"])
    if len(content) > 2_000_000 or not content.startswith(b"%PDF") or hashlib.sha256(content).hexdigest() != document["content_hash"]:
        raise SqlStoreError("INTAKE_DOCUMENT_INTEGRITY_FAILED")
    return document


def extract_document(row):
    with connection() as db:
        document = intake_document(db, row)
        content = bytes(document["content"])
        cached = db.execute(
            "SELECT payload FROM document_extractions WHERE case_id=? AND source_version=? "
            "AND content_hash=? AND model_id='prebuilt-layout'",
            (row["id"], document["version"], document["content_hash"]),
        ).fetchone()
    if cached:
        return json.loads(cached["payload"])
    try:
        result = document_client().begin_analyze_document(
            "prebuilt-layout", body=io.BytesIO(content), content_type="application/pdf",
            features=["keyValuePairs"],
        ).result(timeout=120)
    except AzureError as error:
        raise CloudServiceError("DOCUMENT_ANALYSIS_UNAVAILABLE") from error
    except TimeoutError as error:
        raise CloudServiceError("DOCUMENT_ANALYSIS_TIMEOUT") from error
    extraction = parse_document(result, document["source_id"], document["version"], document["content_hash"])
    extracted_member = extraction["fields"]["member_id"]["value"]
    if extracted_member is not None and extracted_member != row["member"]:
        raise CloudServiceError("EXTRACTED_MEMBER_MISMATCH")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        if db.execute(
            "SELECT payload FROM document_extractions WHERE case_id=? AND source_version=? "
            "AND content_hash=? AND model_id='prebuilt-layout'",
            (row["id"], document["version"], document["content_hash"]),
        ).fetchone() is None:
            db.execute("INSERT INTO document_extractions VALUES(?,?,?,?,?,?)",
                       (row["id"], document["version"], document["content_hash"], "prebuilt-layout",
                        json.dumps(extraction), now()))
    return extraction


def aggregate(employer):
    with connection() as db:
        records = db.execute(
            "SELECT period,members,specialty_utilizers,cost,dataset,as_of FROM portfolio_aggregates "
            "WHERE employer=? ORDER BY period", (employer,),
        ).fetchall()
    if not records:
        raise SqlStoreError("SYNTHETIC_AGGREGATE_SETUP_REQUIRED")
    rows = []
    for row in records:
        suppress = row["members"] < 10 or row["specialty_utilizers"] < 10
        rows.append({"period": row["period"], "members": None if suppress else row["members"],
                     "specialty_utilizers": None if suppress else row["specialty_utilizers"],
                     "cost": None if suppress else float(row["cost"])})
    return {"employer": employer, "dataset": records[0]["dataset"], "as_of": records[0]["as_of"],
            "minimum_cell": 10, "rows": rows,
            "suppression": "Separate Azure SQL synthetic aggregate snapshot; cells below 10 and associated measures suppressed. No member drill-through."}
