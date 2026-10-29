import json
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from service.domain import Identity
from service.entra_auth import EntraAuthError, EntraAuthenticator, EntraConfiguration


TENANT = "10000000-0000-0000-0000-000000000001"
API = "20000000-0000-0000-0000-000000000002"
SPA = "30000000-0000-0000-0000-000000000003"
RUNTIME = "40000000-0000-0000-0000-000000000004"
USER = "50000000-0000-0000-0000-000000000005"


@pytest.fixture(scope="module")
def key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture
def authenticator(monkeypatch, key):
    config = EntraConfiguration(TENANT, API, SPA, RUNTIME, {
        USER: Identity(USER, "reviewer", "SYN-EMP-A"),
    })
    auth = EntraAuthenticator(config)
    monkeypatch.setattr(auth.keys, "get_signing_key_from_jwt",
                        lambda token: SimpleNamespace(key=key.public_key()))
    return auth


def token(key, *, application=False, **overrides):
    current = int(time.time())
    claims = {
        "iss": f"https://login.microsoftonline.com/{TENANT}/v2.0", "tid": TENANT,
        "aud": API, "ver": "2.0", "iat": current, "nbf": current, "exp": current + 300,
        "oid": RUNTIME if application else USER,
        "azp": RUNTIME if application else SPA,
        "roles": ["Benefits.Runtime"] if application else ["Benefits.Reviewer"],
    }
    if not application:
        claims["scp"] = "access_as_user"
    claims.update(overrides)
    return "Bearer " + jwt.encode(claims, key, algorithm="RS256", headers={"kid": "test-key"})


def test_real_signatures_and_both_trust_boundaries(authenticator, key):
    identity = authenticator.authenticate(token(key, application=True), token(key))
    assert identity == Identity(USER, "reviewer", "SYN-EMP-A")
    assert identity.id != "reviewer-a"


@pytest.mark.parametrize("changes", [
    {"tid": API}, {"aud": SPA}, {"iss": "https://example.invalid/"},
    {"exp": 1}, {"nbf": int(time.time()) + 3600}, {"ver": "1.0"},
    {"oid": "reviewer-a"}, {"exp": None},
])
def test_wrong_tenant_audience_issuer_lifetime_and_actor_are_denied(authenticator, key, changes):
    with pytest.raises(EntraAuthError, match="ENTRA_TOKEN_INVALID"):
        authenticator.authenticate(token(key, application=True), token(key, **changes))


@pytest.mark.parametrize("changes, code", [
    ({"azp": API}, "USER_SCOPE_DENIED"),
    ({"scp": "unrelated_scope"}, "USER_SCOPE_DENIED"),
    ({"scp": None}, "USER_SCOPE_DENIED"),
    ({"roles": ["Benefits.Employer"]}, "USER_ACCESS_NOT_ASSIGNED"),
    ({"roles": "Benefits.Reviewer"}, "USER_ACCESS_NOT_ASSIGNED"),
    ({"oid": API}, "USER_ACCESS_NOT_ASSIGNED"),
])
def test_user_scope_role_and_explicit_employer_binding(authenticator, key, changes, code):
    with pytest.raises(EntraAuthError, match=code):
        authenticator.authenticate(token(key, application=True), token(key, **changes))


@pytest.mark.parametrize("changes", [
    {"azp": SPA}, {"roles": []}, {"roles": "Benefits.Runtime"}, {"scp": "access_as_user"},
])
def test_service_token_cannot_be_substituted_by_a_user_or_other_application(authenticator, key, changes):
    with pytest.raises(EntraAuthError, match="RUNTIME_IDENTITY_DENIED"):
        authenticator.authenticate(token(key, application=True, **changes), token(key))


def test_missing_caller_is_denied_before_user_key_lookup(authenticator, key, monkeypatch):
    def unexpected_lookup(_):
        pytest.fail("No metadata lookup is allowed before checking the bearer format.")
    monkeypatch.setattr(authenticator.keys, "get_signing_key_from_jwt", unexpected_lookup)
    with pytest.raises(EntraAuthError, match="ENTRA_TOKEN_REQUIRED"):
        authenticator.authenticate("", token(key))


def test_unsigned_and_forged_tokens_are_denied(authenticator, key):
    unsigned = "Bearer " + jwt.encode({"oid": USER}, "", algorithm="none", headers={"kid": "test-key"})
    with pytest.raises(EntraAuthError, match="ENTRA_TOKEN_INVALID"):
        authenticator.authenticate(token(key, application=True), unsigned)
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(EntraAuthError, match="ENTRA_TOKEN_INVALID"):
        authenticator.authenticate(token(key, application=True), token(other_key))


def test_key_service_outage_is_not_misreported_as_invalid_credentials(authenticator, key, monkeypatch):
    def unavailable(_):
        raise jwt.PyJWKClientConnectionError("Synthetic key-service outage.")
    monkeypatch.setattr(authenticator.keys, "get_signing_key_from_jwt", unavailable)
    with pytest.raises(EntraAuthError, match="ENTRA_KEYS_UNAVAILABLE") as error:
        authenticator.authenticate(token(key, application=True), token(key))
    assert error.value.status == 503


def test_explicit_nonsecret_configuration(monkeypatch):
    for name, value in {
        "BENEFITS_TENANT_ID": TENANT, "BENEFITS_API_CLIENT_ID": API,
        "BENEFITS_SPA_CLIENT_ID": SPA, "BENEFITS_RUNTIME_CLIENT_ID": RUNTIME,
        "BENEFITS_IDENTITY_BINDINGS": json.dumps({USER: {"role": "reviewer", "employer": "SYN-EMP-A"}}),
    }.items():
        monkeypatch.setenv(name, value)
    config = EntraConfiguration.from_environment()
    assert config.identities[USER].employer == "SYN-EMP-A"
    monkeypatch.setenv("BENEFITS_IDENTITY_BINDINGS", json.dumps({
        USER: {"role": "reviewer", "employer": "unapproved-employer"},
    }))
    with pytest.raises(RuntimeError, match="ENTRA_CONFIGURATION_INVALID"):
        EntraConfiguration.from_environment()


def test_missing_configuration_does_not_fall_back_to_demo_auth(monkeypatch):
    monkeypatch.delenv("BENEFITS_TENANT_ID", raising=False)
    with pytest.raises(RuntimeError, match="ENTRA_CONFIGURATION_INVALID"):
        EntraConfiguration.from_environment()


@pytest.fixture
def cloud_client(monkeypatch, key):
    import importlib
    from fastapi.testclient import TestClient
    from service import azure_services
    module = importlib.import_module("service.app")
    for name in ("BENEFITS_SERVICE_SECRET", "OPENAI_API_KEY", "AZURE_CLIENT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    for name, value in {
        "BENEFITS_PROFILE": "starter", "BENEFITS_TENANT_ID": TENANT,
        "BENEFITS_API_CLIENT_ID": API, "BENEFITS_SPA_CLIENT_ID": SPA,
        "BENEFITS_RUNTIME_CLIENT_ID": RUNTIME,
        "BENEFITS_IDENTITY_BINDINGS": json.dumps({USER: {"role": "reviewer", "employer": "SYN-EMP-A"}}),
    }.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(azure_services, "validate_configuration", lambda: None)
    monkeypatch.setattr(module, "initialize", lambda: None)
    module.requests_by_user.clear()
    with TestClient(module.app) as client:
        monkeypatch.setattr(module.app.state.entra.keys, "get_signing_key_from_jwt",
                            lambda value: SimpleNamespace(key=key.public_key()))
        yield client


def cloud_headers(key):
    return {"Authorization": token(key), "X-Benefits-Runtime-Authorization": token(key, application=True)}


def test_starter_http_requires_both_real_signed_token_boundaries(cloud_client, key):
    assert cloud_client.get("/api/session", headers={"X-Benefits-User": "reviewer-a"}).status_code == 401
    assert cloud_client.get("/api/session", headers={"Authorization": token(key)}).status_code == 401
    response = cloud_client.get("/api/session", headers={
        **cloud_headers(key), "X-Benefits-User": "employer-b",
    })
    assert response.status_code == 200
    assert response.json()["id"] == USER and response.json()["role"] == "reviewer"
    assert response.json()["employer"] == "SYN-EMP-A"
    assert response.json()["mode"] == "live" and response.json()["profile"] == "starter"


def test_starter_http_refuses_forged_role_claims(cloud_client, key):
    response = cloud_client.get("/api/session", headers={
        **cloud_headers(key), "Authorization": token(key, roles=["Benefits.Employer"]),
    })
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "USER_ACCESS_NOT_ASSIGNED"


def test_starter_liveness_never_claims_database_ready(cloud_client):
    response = cloud_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
    assert "ready" not in response.json()


@pytest.mark.parametrize("name", ["BENEFITS_SERVICE_SECRET", "OPENAI_API_KEY", "AZURE_CLIENT_SECRET"])
def test_starter_lifespan_rejects_static_application_credentials(monkeypatch, name):
    from fastapi.testclient import TestClient
    from service.app import app
    monkeypatch.setenv("BENEFITS_PROFILE", "starter")
    monkeypatch.setenv(name, "synthetic-test-only")
    with pytest.raises(RuntimeError, match="STARTER_DISALLOWS_STATIC_APPLICATION_CREDENTIALS"):
        with TestClient(app):
            pytest.fail("No cloud startup may proceed with static application credentials.")
