import os


def profile() -> str:
    value = os.environ.get("BENEFITS_PROFILE", "local")
    if value not in {"local", "starter"}:
        raise RuntimeError("BENEFITS_PROFILE must be local or starter. Enterprise integrations are not implemented.")
    return value


def starter() -> bool:
    return profile() == "starter"
