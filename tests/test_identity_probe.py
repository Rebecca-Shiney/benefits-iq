import json
from types import SimpleNamespace
from unittest.mock import Mock

import jwt
import pytest

from service import identity_probe
from service.entra_auth import EntraAuthError
from test_entra_auth import API, RUNTIME, TENANT, USER, key, token

PRINCIPAL = "60000000-0000-0000-0000-000000000006"


@pytest.fixture
def probe(monkeypatch, key):
    monkeypatch.setattr(identity_probe.logging.config, "dictConfig", Mock())
    settings = {"BENEFITS_PROFILE": "showcase", "OTEL_SDK_DISABLED": "true",
                "BENEFITS_TENANT_ID": TENANT, "BENEFITS_API_CLIENT_ID": API,
                "BENEFITS_RUNTIME_CLIENT_ID": RUNTIME, "BENEFITS_RUNTIME_PRINCIPAL_ID": PRINCIPAL}
    for name, value in settings.items():
        monkeypatch.setenv(name, value)
    for name in ("BENEFITS_SERVICE_SECRET", "AZURE_CLIENT_SECRET", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    value = token(key, application=True, oid=PRINCIPAL, idtyp="app", roles=None)[7:]
    credential = Mock()
    credential.get_token.return_value = SimpleNamespace(token=value)
    context = Mock()
    context.__enter__ = Mock(return_value=credential)
    context.__exit__ = Mock(return_value=False)
    factory = Mock(return_value=context)
    monkeypatch.setattr(identity_probe, "ManagedIdentityCredential", factory)
    monkeypatch.setattr(jwt.PyJWKClient, "get_signing_key_from_jwt",
                        lambda self, value: SimpleNamespace(key=key.public_key()))
    return factory, credential, value


def test_probe_uses_only_managed_identity_and_outputs_no_token(probe, capsys):
    factory, credential, value = probe
    identity_probe.main()
    factory.assert_called_once_with(client_id=RUNTIME)
    credential.get_token.assert_called_once_with(f"api://{API}/.default")
    output = capsys.readouterr().out
    result = json.loads(output)
    assert result["status"] == "managed_identity_caller_verified"
    assert len(result["negative_checks"]) == 4 and result["data_services_exercised"] is False
    assert value not in output and "Bearer " not in output


def test_wrong_actual_caller_cannot_produce_a_success_receipt(probe, key, capsys):
    _, credential, _ = probe
    credential.get_token.return_value = SimpleNamespace(
        token=token(key, application=True, oid=USER, idtyp="app")[7:])
    with pytest.raises(EntraAuthError, match="RUNTIME_IDENTITY_DENIED"):
        identity_probe.main()
    assert "managed_identity_caller_verified" not in capsys.readouterr().out


@pytest.mark.parametrize("name,value", [
    ("BENEFITS_PROFILE", "local"), ("OTEL_SDK_DISABLED", "false"),
    ("BENEFITS_SERVICE_SECRET", "synthetic-test-not-a-credential"),
    ("AZURE_CLIENT_SECRET", "synthetic-test-not-a-credential"),
])
def test_probe_rejects_noncloud_or_static_credentials(probe, monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    with pytest.raises(RuntimeError):
        identity_probe.main()
    probe[0].assert_not_called()
