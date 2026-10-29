"""Verify runtime data permissions and fresh cloud reads without changing cases."""

import io
import json
import logging.config
import os

from azure.core.exceptions import AzureError

from . import azure_services as cloud
from .cloud_entrypoint import logging_configuration
from .cloud_errors import CloudServiceError, SqlStoreError
from .cloud_seed import seed_bundle
from .store import connection


def main():
    if (os.environ.get("BENEFITS_PROFILE") != "showcase"
            or os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true"):
        raise RuntimeError("EXPLICIT_SHOWCASE_SOURCE_PROOF_REQUIRED")
    if any(os.environ.get(key) for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET")):
        raise RuntimeError("SOURCE_PROOF_DISALLOWS_STATIC_CREDENTIALS")
    cloud.validate_configuration()
    logging.config.dictConfig(logging_configuration())
    with connection() as db:
        permissions = db.execute(
            "SELECT HAS_PERMS_BY_NAME('dbo.source_records','OBJECT','INSERT') AS source_write,"
            "HAS_PERMS_BY_NAME('dbo.decisions','OBJECT','UPDATE') AS decision_rewrite,"
            "HAS_PERMS_BY_NAME(DB_NAME(),'DATABASE','CREATE TABLE') AS ddl,"
            "HAS_PERMS_BY_NAME('dbo.decisions','OBJECT','INSERT') AS decision_insert"
        ).fetchone()
        if (any(permissions[name] != 0 for name in ("source_write", "decision_rewrite", "ddl"))
                or permissions["decision_insert"] != 1):
            raise RuntimeError("RUNTIME_SQL_PERMISSION_BOUNDARY_FAILED")
        row = db.execute("SELECT * FROM cases WHERE id=?", ("SYN-CASE-001",)).fetchone()
        if row is None:
            raise RuntimeError("SYNTHETIC_PROOF_CASE_REQUIRED")
        document = cloud.intake_document(db, row)
        content = bytes(document["content"])
    expected = seed_bundle()["criteria"][0]
    payload = {"plan": expected["plan"], "fields": {
        key: {"value": expected[key]} for key in ("drug", "indication")
    }}
    found = cloud.retrieve_criteria(payload, expected["employer"])
    source = cloud.source_criterion(payload, expected["employer"])
    if (found is None or source is None or found["version"] != expected["version"]
            or found["passage"] != expected["passage"]):
        raise RuntimeError("LIVE_GOVERNED_SEARCH_SOURCE_PROOF_FAILED")
    result = cloud.document_client().begin_analyze_document(
        "prebuilt-layout", body=io.BytesIO(content), content_type="application/pdf",
        features=["keyValuePairs"],
    ).result(timeout=120)
    extraction = cloud.parse_document(result, document["source_id"], document["version"], document["content_hash"])
    if extraction["fields"]["member_id"]["value"] != row["member"]:
        raise RuntimeError("LIVE_OCR_SOURCE_PROOF_FAILED")
    print(json.dumps({"status": "runtime_sources_verified", "case_mutated": False,
                      "checks": ["runtime_sql_permissions", "sql_source_binary_document",
                                 "live_scoped_search", "fresh_document_intelligence"]}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, AzureError, CloudServiceError, SqlStoreError, TimeoutError, ValueError, KeyError) as error:
        logging.getLogger("benefits").error("Source proof failed type=%s", type(error).__name__)
        raise SystemExit("RUNTIME_SOURCE_PROOF_FAILED") from None
