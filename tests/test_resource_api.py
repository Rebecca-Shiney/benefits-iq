from copy import deepcopy

import pytest

from scripts.resource_api import RegistrationError, ensure_resource_api

ENVIRONMENT = "10000000-0000-0000-0000-000000000001"
OWNER = "20000000-0000-0000-0000-000000000002"
OBJECT = "30000000-0000-0000-0000-000000000003"
CLIENT = "40000000-0000-0000-0000-000000000004"
PRINCIPAL = "50000000-0000-0000-0000-000000000005"


class Graph:
    def __init__(self):
        self.app = None
        self.principal = None
        self.owner = OWNER
        self.calls = []
        self.incomplete = False

    def __call__(self, method, path, body=None, query=None):
        self.calls.append((method, path, deepcopy(body)))
        if method == "POST" and path == "/applications":
            self.app = {**deepcopy(body), "id": OBJECT, "appId": CLIENT, "identifierUris": []}
            return deepcopy(self.app)
        if method == "GET" and path == "/applications":
            return {"value": [deepcopy(self.app)] if self.app else [],
                    **({"@odata.nextLink": "not-followed"} if self.incomplete else {})}
        if method == "GET" and path.endswith("/owners"):
            return {"value": [{"id": self.owner}]}
        if method == "GET" and path == f"/applications/{OBJECT}":
            return deepcopy(self.app)
        if method == "PATCH" and path == f"/applications/{OBJECT}":
            self.app.update(deepcopy(body))
            return None
        if method == "POST" and path == "/servicePrincipals":
            self.principal = {**body, "id": PRINCIPAL, "accountEnabled": True,
                              "servicePrincipalType": "Application"}
            return deepcopy(self.principal)
        if method == "GET" and path == "/servicePrincipals":
            return {"value": [deepcopy(self.principal)] if self.principal else []}
        raise AssertionError((method, path, body, query))


def initialized():
    graph = Graph()
    ensure_resource_api(graph, ENVIRONMENT, OWNER)
    graph.calls.clear()
    return graph


def test_resource_audience_is_owned_roleless_secretless_and_idempotent():
    graph = Graph()
    result = ensure_resource_api(graph, ENVIRONMENT, OWNER)
    assert result == {"objectId": OBJECT, "clientId": CLIENT, "principalId": PRINCIPAL,
                      "audience": f"api://{CLIENT}"}
    assert graph.app["api"]["requestedAccessTokenVersion"] == 2
    assert graph.app["optionalClaims"]["accessToken"] == [{"name": "idtyp", "essential": False}]
    assert graph.app["requiredResourceAccess"] == []
    assert graph.principal["appRoleAssignmentRequired"] is False
    assert all("addPassword" not in path and "appRoleAssignments" not in path
               and "oauth2PermissionGrants" not in path for _, path, _ in graph.calls)
    graph.calls.clear()
    assert ensure_resource_api(graph, ENVIRONMENT, OWNER) == result
    assert all(method == "GET" for method, _, _ in graph.calls)


@pytest.mark.parametrize("field,value", [
    ("tags", ["somebody-elses-app"]),
    ("signInAudience", "AzureADMultipleOrgs"),
    ("requiredResourceAccess", [{"resourceAppId": CLIENT}]),
    ("passwordCredentials", [{"keyId": PRINCIPAL}]),
    ("keyCredentials", [{"keyId": PRINCIPAL}]),
    ("appRoles", [{"value": "Unexpected.Role"}]),
    ("identifierUris", ["api://different-audience"]),
    ("optionalClaims", {"accessToken": []}),
    ("api", {"requestedAccessTokenVersion": 1}),
    ("spa", {"redirectUris": ["https://example.invalid"]}),
    ("web", {"implicitGrantSettings": {"enableIdTokenIssuance": True}}),
    ("isFallbackPublicClient", True),
])
def test_existing_resource_drift_is_not_silently_overwritten(field, value):
    graph = initialized()
    graph.app[field] = value
    with pytest.raises(RegistrationError):
        ensure_resource_api(graph, ENVIRONMENT, OWNER)
    assert all(method == "GET" for method, _, _ in graph.calls)


def test_missing_owner_never_self_grants_ownership():
    graph = initialized()
    graph.owner = PRINCIPAL
    with pytest.raises(RegistrationError, match="DEPLOYER_OWNERSHIP_REQUIRED"):
        ensure_resource_api(graph, ENVIRONMENT, OWNER)
    assert all(method == "GET" for method, _, _ in graph.calls)


def test_discovery_failure_is_not_absence_and_never_creates():
    graph = Graph()
    graph.incomplete = True
    with pytest.raises(RegistrationError, match="DISCOVERY_INCOMPLETE"):
        ensure_resource_api(graph, ENVIRONMENT, OWNER)
    assert all(method == "GET" for method, _, _ in graph.calls)


def test_assignment_required_policy_is_not_disabled_on_existing_principal():
    graph = initialized()
    graph.principal["appRoleAssignmentRequired"] = True
    with pytest.raises(RegistrationError, match="ACL_PATTERN_UNAVAILABLE"):
        ensure_resource_api(graph, ENVIRONMENT, OWNER)
    assert all(method == "GET" for method, _, _ in graph.calls)


def test_permission_denial_does_not_trigger_alternative_writes():
    calls = []

    def forbidden(method, path, **kwargs):
        calls.append((method, path))
        raise PermissionError("Authorization_RequestDenied")

    with pytest.raises(PermissionError, match="Authorization_RequestDenied"):
        ensure_resource_api(forbidden, ENVIRONMENT, OWNER)
    assert calls == [("GET", "/applications")]
