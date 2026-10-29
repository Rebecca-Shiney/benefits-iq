import json
import logging.config
import os
import re
from dataclasses import replace

from azure.core.exceptions import AzureError
from azure.identity import ManagedIdentityCredential

from .cloud_entrypoint import logging_configuration
from .entra_auth import CallerConfiguration, EntraAuthError, ManagedCallerAuthenticator


def main():
    if (os.environ.get("BENEFITS_PROFILE") != "showcase"
            or os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true"):
        raise RuntimeError("EXPLICIT_SHOWCASE_IDENTITY_PROOF_REQUIRED")
    if any(os.environ.get(name) for name in ("BENEFITS_SERVICE_SECRET", "AZURE_CLIENT_SECRET", "OPENAI_API_KEY")):
        raise RuntimeError("IDENTITY_PROOF_DISALLOWS_STATIC_CREDENTIALS")
    logging.config.dictConfig(logging_configuration())
    config = CallerConfiguration.from_environment()
    with ManagedIdentityCredential(client_id=config.runtime_client_id) as credential:
        token = credential.get_token(f"api://{config.api_client_id}/.default")
    authorization = "Bearer " + token.token
    validator = ManagedCallerAuthenticator(config)
    validator.authenticate_caller(authorization)
    zero = "00000000-0000-0000-0000-000000000000"
    denied = []
    for field in ("api_client_id", "runtime_client_id", "runtime_principal_id", "tenant_id"):
        wrong = ManagedCallerAuthenticator(replace(config, **{field: zero}))
        wrong.keys = validator.keys
        try:
            wrong.authenticate_caller(authorization)
        except EntraAuthError as error:
            if error.status != 401:
                raise
            denied.append(field)
        else:
            raise RuntimeError("MANAGED_IDENTITY_NEGATIVE_PATH_ACCEPTED")
    print(json.dumps({"status": "managed_identity_caller_verified", "negative_checks": denied,
                      "token_exposed": False, "data_services_exercised": False}))


if __name__ == "__main__":
    try:
        main()
    except (AzureError, EntraAuthError, RuntimeError) as error:
        code = error.code if isinstance(error, EntraAuthError) else "MANAGED_IDENTITY_PROOF_FAILED"
        aad_code = re.search(r"\bAADSTS\d{3,10}\b", str(error))
        if aad_code:
            code += "_" + aad_code.group()
        logging.getLogger("benefits").error("Identity proof failed code=%s type=%s", code, type(error).__name__)
        raise SystemExit(code) from None
