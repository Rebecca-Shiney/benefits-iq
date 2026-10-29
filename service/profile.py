import os


def profile() -> str:
    value = os.environ.get("BENEFITS_PROFILE", "local")
    if value not in {"local", "starter", "showcase"}:
        raise RuntimeError("BENEFITS_PROFILE must be local, showcase or starter. Enterprise integrations are not implemented.")
    return value


def starter() -> bool:
    return profile() == "starter"


def cloud() -> bool:
    return profile() in {"starter", "showcase"}


def showcase() -> bool:
    return profile() == "showcase"
