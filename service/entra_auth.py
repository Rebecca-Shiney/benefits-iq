import json
import os
from dataclasses import dataclass
from uuid import UUID

import jwt

from .domain import Identity


ROLE_CLAIMS = {
    "reviewer": "Benefits.Reviewer",
    "contact": "Benefits.Contact",
    "employer": "Benefits.Employer",
}


class EntraAuthError(Exception):
    def __init__(self, code: str, status: int = 401):
        super().__init__(code)
        self.code = code
        self.status = status


def guid(value: str) -> str:
    if not isinstance(value, str) or str(UUID(value)) != value.lower():
        raise ValueError("A canonical Entra GUID is required.")
    return value.lower()


@dataclass(frozen=True)
class EntraConfiguration:
    tenant_id: str
    api_client_id: str
    spa_client_id: str
    runtime_client_id: str
    identities: dict[str, Identity]

    @classmethod
    def from_environment(cls):
        try:
            ids = [guid(os.environ[name]) for name in (
                "BENEFITS_TENANT_ID", "BENEFITS_API_CLIENT_ID",
                "BENEFITS_SPA_CLIENT_ID", "BENEFITS_RUNTIME_CLIENT_ID",
            )]
            raw = os.environ["BENEFITS_IDENTITY_BINDINGS"]
            if len(raw) > 65_536:
                raise ValueError("Identity configuration exceeds its limit.")
            bindings = json.loads(raw)
            if not isinstance(bindings, dict) or not 1 <= len(bindings) <= 128:
                raise ValueError("Explicit approved object-ID bindings are required.")
            identities = {}
            for oid, binding in bindings.items():
                oid = guid(oid)
                if not isinstance(binding, dict) or set(binding) != {"role", "employer"}:
                    raise ValueError("Each binding requires exactly a role and employer.")
                if binding["role"] not in ROLE_CLAIMS or binding["employer"] not in {"SYN-EMP-A", "SYN-EMP-B"}:
                    raise ValueError("Unknown synthetic role or employer binding.")
                if oid in identities:
                    raise ValueError("Duplicate object-ID binding.")
                identities[oid] = Identity(oid, binding["role"], binding["employer"])
            return cls(*ids, identities)
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("ENTRA_CONFIGURATION_INVALID: explicit tenant, application IDs and approved identity bindings are required.") from error

    @property
    def issuer(self):
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"


class EntraAuthenticator:
    def __init__(self, config: EntraConfiguration):
        self.config = config
        self.keys = jwt.PyJWKClient(
            f"https://login.microsoftonline.com/{config.tenant_id}/discovery/v2.0/keys",
            cache_keys=True, max_cached_keys=16, lifespan=3600, timeout=10,
        )

    def _claims(self, authorization: str):
        if not authorization.startswith("Bearer ") or len(authorization) > 16_384:
            raise EntraAuthError("ENTRA_TOKEN_REQUIRED")
        token = authorization[7:]
        try:
            header = jwt.get_unverified_header(token)
            if header.get("alg") != "RS256" or not isinstance(header.get("kid"), str) or not 1 <= len(header["kid"]) <= 128:
                raise EntraAuthError("ENTRA_TOKEN_INVALID")
            key = self.keys.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, key.key, algorithms=["RS256"], audience=self.config.api_client_id,
                issuer=self.config.issuer, leeway=30,
                options={"require": ["exp", "iat", "nbf", "iss", "aud", "tid", "oid", "ver"], "strict_aud": True},
            )
            if claims["ver"] != "2.0" or claims["tid"] != self.config.tenant_id:
                raise EntraAuthError("ENTRA_TOKEN_INVALID")
            guid(claims["oid"])
            return claims
        except jwt.PyJWKClientConnectionError as error:
            raise EntraAuthError("ENTRA_KEYS_UNAVAILABLE", 503) from error
        except (jwt.PyJWTError, ValueError, TypeError) as error:
            raise EntraAuthError("ENTRA_TOKEN_INVALID") from error

    def authenticate(self, runtime_authorization: str, user_authorization: str) -> Identity:
        caller = self._claims(runtime_authorization)
        caller_roles = caller.get("roles")
        if (caller.get("azp") != self.config.runtime_client_id or caller.get("scp")
                or not isinstance(caller_roles, list) or "Benefits.Runtime" not in caller_roles):
            raise EntraAuthError("RUNTIME_IDENTITY_DENIED")

        user = self._claims(user_authorization)
        scopes = user.get("scp")
        if (user.get("azp") != self.config.spa_client_id or not isinstance(scopes, str)
                or "access_as_user" not in scopes.split()):
            raise EntraAuthError("USER_SCOPE_DENIED")
        identity = self.config.identities.get(user["oid"].lower())
        roles = user.get("roles")
        if identity is None or not isinstance(roles, list) or ROLE_CLAIMS[identity.role] not in roles:
            raise EntraAuthError("USER_ACCESS_NOT_ASSIGNED", 403)
        return identity
