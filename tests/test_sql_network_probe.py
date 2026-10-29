import json
import socket
from contextlib import contextmanager
from unittest.mock import Mock

import pytest

from service import sql_network_probe as probe


@pytest.fixture
def dependencies(monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    monkeypatch.setenv("BENEFITS_SQL_PRIVATE_CIDR", "10.84.0.32/27")
    monkeypatch.setenv("BENEFITS_SQL_SERVER", "synthetic.database.windows.net")
    monkeypatch.setenv("BENEFITS_SQL_DATABASE", "benefits")
    monkeypatch.setenv("BENEFITS_MANAGED_IDENTITY_CLIENT_ID", "10000000-0000-0000-0000-000000000001")
    for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET"):
        monkeypatch.delenv(key, raising=False)
    resolve = Mock(return_value=[
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.84.0.36", 1433)),
    ])
    monkeypatch.setattr(probe.socket, "getaddrinfo", resolve)
    db = Mock()
    db.execute.return_value.fetchone.return_value = {"connected": 1}
    entered = Mock()

    @contextmanager
    def connection():
        entered()
        yield db

    monkeypatch.setattr(probe, "connection", connection)
    return resolve, db, entered


def test_private_dns_and_real_sql_connection_contract_are_read_only(dependencies, capsys):
    resolve, db, entered = dependencies
    probe.main()
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {"status": "private_sql_verified", "schema_mutated": False,
                       "resolved_address_count": 1, "checks": ["private_dns", "managed_identity_sql"]}
    resolve.assert_called_once_with("synthetic.database.windows.net", 1433, type=socket.SOCK_STREAM)
    entered.assert_called_once()
    db.execute.assert_called_once_with("SELECT 1 AS connected")


@pytest.mark.parametrize("addresses", [[], ["20.0.0.1"], ["10.84.0.1"],
                                      ["10.84.0.36", "20.0.0.1"], ["::1"]])
def test_public_mixed_missing_and_wrong_private_resolution_stop_before_sql(dependencies, addresses):
    resolve, db, entered = dependencies
    resolve.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 1433))
                            for ip in addresses]
    with pytest.raises(RuntimeError, match="SQL_DNS_MUST_RESOLVE_ONLY"):
        probe.main()
    entered.assert_not_called()
    db.execute.assert_not_called()


@pytest.mark.parametrize("network", ["", "0.0.0.0/0", "10.0.0.0/8", "10.84.0.36/27", "::1/128"])
def test_invalid_or_overbroad_network_cannot_weaken_proof(dependencies, monkeypatch, network):
    monkeypatch.setenv("BENEFITS_SQL_PRIVATE_CIDR", network)
    with pytest.raises(RuntimeError, match="SQL_PRIVATE_CIDR"):
        probe.main()
    dependencies[0].assert_not_called()
    dependencies[2].assert_not_called()


def test_missing_sql_result_is_not_success(dependencies):
    dependencies[1].execute.return_value.fetchone.return_value = None
    with pytest.raises(RuntimeError, match="MANAGED_IDENTITY_SQL_PROOF_FAILED"):
        probe.main()


def test_private_sql_probe_requires_explicit_secretless_showcase(dependencies, monkeypatch):
    monkeypatch.setenv("BENEFITS_PROFILE", "local")
    with pytest.raises(RuntimeError, match="EXPLICIT_PRIVATE_SQL_PROOF_REQUIRED"):
        probe.main()
    monkeypatch.setenv("BENEFITS_PROFILE", "showcase")
    monkeypatch.setenv("AZURE_CLIENT_SECRET", "synthetic-forbidden-value")
    with pytest.raises(RuntimeError, match="DISALLOWS_STATIC_CREDENTIALS"):
        probe.main()
    dependencies[0].assert_not_called()
