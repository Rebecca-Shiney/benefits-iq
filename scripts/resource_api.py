"""Owned, single-tenant resource audience; no visitor identity or consent grants."""

from uuid import UUID

GRAPH = "https://graph.microsoft.com/v1.0"


class RegistrationError(RuntimeError):
    pass


def canonical_guid(value):
    try:
        valid = isinstance(value, str) and str(UUID(value)) == value
    except ValueError:
        valid = False
    if not valid:
        raise RegistrationError("CANONICAL_RESOURCE_ID_REQUIRED")
    return value


def collection(graph, path, query=None):
    result = graph("GET", path, query=query)
    if (not isinstance(result, dict) or not isinstance(result.get("value"), list)
            or result.get("@odata.nextLink")):
        raise RegistrationError("RESOURCE_DISCOVERY_INCOMPLETE")
    return result["value"]


def validate_application(app, display_name, tags):
    if (app.get("displayName") != display_name or set(app.get("tags") or []) != set(tags)
            or app.get("signInAudience") != "AzureADMyOrg"):
        raise RegistrationError("RESOURCE_APPLICATION_OWNERSHIP_COLLISION")
    for field in ("requiredResourceAccess", "appRoles", "passwordCredentials", "keyCredentials"):
        if app.get(field):
            raise RegistrationError("RESOURCE_APPLICATION_CONFIGURATION_DRIFT")
    api = app.get("api") or {}
    if (api.get("requestedAccessTokenVersion") != 2 or api.get("oauth2PermissionScopes")
            or api.get("preAuthorizedApplications") or api.get("knownClientApplications")
            or api.get("acceptMappedClaims")):
        raise RegistrationError("RESOURCE_APPLICATION_CONFIGURATION_DRIFT")
    claims = app.get("optionalClaims") or {}
    access = claims.get("accessToken") or []
    if (len(access) != 1 or access[0].get("name") != "idtyp"
            or access[0].get("source") or access[0].get("additionalProperties")
            or claims.get("idToken") or claims.get("saml2Token")):
        raise RegistrationError("RESOURCE_APPLICATION_CLAIMS_DRIFT")
    if (any((app.get(kind) or {}).get("redirectUris") for kind in ("web", "spa", "publicClient"))
            or (app.get("web") or {}).get("implicitGrantSettings", {}).get("enableAccessTokenIssuance")
            or (app.get("web") or {}).get("implicitGrantSettings", {}).get("enableIdTokenIssuance")
            or app.get("isFallbackPublicClient")):
        raise RegistrationError("RESOURCE_APPLICATION_VISITOR_AUTH_UNEXPECTED")


def ensure_resource_api(graph, environment_id, owner_id):
    """graph(method, relative_path, body=None, query=None) must fail on HTTP errors.

    Recover by exact environment tag/name after an ambiguous create; never retry
    creates blindly, adopt a name collision, add credentials or grant consent.
    """
    environment_id = canonical_guid(environment_id)
    owner_id = canonical_guid(owner_id)
    name = f"Benefits IQ showcase API {environment_id}"
    tags = ["BenefitsIQ", f"environment:{environment_id}", "profile:showcase"]
    apps = collection(graph, "/applications", {"$filter": f"displayName eq '{name}'"})
    if len(apps) > 1:
        raise RegistrationError("RESOURCE_APPLICATION_NAME_AMBIGUOUS")
    if not apps:
        graph("POST", "/applications", body={
            "displayName": name, "signInAudience": "AzureADMyOrg", "tags": tags,
            "requiredResourceAccess": [],
            "api": {"requestedAccessTokenVersion": 2},
            "optionalClaims": {"accessToken": [{"name": "idtyp", "essential": False}]},
        })
        apps = collection(graph, "/applications", {"$filter": f"displayName eq '{name}'"})
        if len(apps) != 1:
            raise RegistrationError("RESOURCE_APPLICATION_CREATE_RECONCILIATION_REQUIRED")
    app = apps[0]
    validate_application(app, name, tags)
    object_id, client_id = canonical_guid(app["id"]), canonical_guid(app["appId"])
    owners = collection(graph, f"/applications/{object_id}/owners", {"$select": "id"})
    if not any(item.get("id") == owner_id for item in owners):
        raise RegistrationError("RESOURCE_APPLICATION_DEPLOYER_OWNERSHIP_REQUIRED")
    uri = f"api://{client_id}"
    if app.get("identifierUris") not in ([], [uri]):
        raise RegistrationError("RESOURCE_APPLICATION_AUDIENCE_DRIFT")
    if not app["identifierUris"]:
        graph("PATCH", f"/applications/{object_id}", body={"identifierUris": [uri]})
        updated = graph("GET", f"/applications/{object_id}")
        validate_application(updated, name, tags)
        if updated.get("identifierUris") != [uri]:
            raise RegistrationError("RESOURCE_APPLICATION_AUDIENCE_NOT_APPLIED")
    principals = collection(graph, "/servicePrincipals", {"$filter": f"appId eq '{client_id}'"})
    if not principals:
        graph("POST", "/servicePrincipals", body={"appId": client_id, "appRoleAssignmentRequired": False})
        principals = collection(graph, "/servicePrincipals", {"$filter": f"appId eq '{client_id}'"})
    if len(principals) != 1:
        raise RegistrationError("RESOURCE_PRINCIPAL_RECONCILIATION_REQUIRED")
    principal = principals[0]
    if (principal.get("appId") != client_id or principal.get("accountEnabled") is not True
            or principal.get("appRoleAssignmentRequired") is not False
            or principal.get("servicePrincipalType") != "Application"):
        raise RegistrationError("RESOURCE_PRINCIPAL_ACL_PATTERN_UNAVAILABLE")
    return {"objectId": object_id, "clientId": client_id,
            "principalId": canonical_guid(principal["id"]), "audience": uri}
