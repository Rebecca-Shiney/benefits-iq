"""Prove private SQL resolution and keyless SQL access before seeding."""

import ipaddress
import json
import os
import socket

from .cloud_errors import SqlStoreError
from .sql_store import SqlConfiguration, connection


def verify_private_dns(config):
    try:
        network = ipaddress.ip_network(os.environ["BENEFITS_SQL_PRIVATE_CIDR"], strict=True)
    except (ValueError, KeyError) as error:
        raise RuntimeError("SQL_PRIVATE_CIDR_REQUIRED") from error
    if network.version != 4 or not network.is_private or network.prefixlen < 24:
        raise RuntimeError("SQL_PRIVATE_CIDR_INVALID")
    addresses = {
        ipaddress.ip_address(record[4][0])
        for record in socket.getaddrinfo(config.server, 1433, type=socket.SOCK_STREAM)
    }
    if not addresses or any(address not in network for address in addresses):
        raise RuntimeError("SQL_DNS_MUST_RESOLVE_ONLY_TO_APPROVED_PRIVATE_SUBNET")
    return len(addresses)


def main():
    if (os.environ.get("BENEFITS_PROFILE") != "showcase"
            or os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true"):
        raise RuntimeError("EXPLICIT_PRIVATE_SQL_PROOF_REQUIRED")
    if any(os.environ.get(key) for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET")):
        raise RuntimeError("PRIVATE_SQL_PROOF_DISALLOWS_STATIC_CREDENTIALS")
    count = verify_private_dns(SqlConfiguration.from_environment())
    with connection() as db:
        row = db.execute("SELECT 1 AS connected").fetchone()
        if row is None or row["connected"] != 1:
            raise RuntimeError("MANAGED_IDENTITY_SQL_PROOF_FAILED")
    print(json.dumps({"status": "private_sql_verified", "schema_mutated": False,
                      "resolved_address_count": count,
                      "checks": ["private_dns", "managed_identity_sql"]}))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, SqlStoreError, OSError, ValueError) as error:
        raise SystemExit(error.code if isinstance(error, SqlStoreError)
                         else str(error) if isinstance(error, RuntimeError)
                         else "PRIVATE_SQL_PROOF_UNAVAILABLE") from None
