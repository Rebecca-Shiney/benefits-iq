import json
import secrets
from pathlib import Path


OPTIONS = json.loads((Path(__file__).resolve().parents[1] / "agents" / "showcase-options.json").read_text())
LIMITS = {"model": (100, 5), "write": (300, 30)}
BODY_READ_SECONDS = 10


def identities():
    from .domain import IDENTITIES, Identity
    return {f"anonymous-demo:{key}": Identity(f"anonymous-demo:{key}", value.role, value.employer)
            for key, value in IDENTITIES.items()}


def selected_view(persona):
    return identities().get(f"anonymous-demo:{persona}")


def field_values(case_id, name):
    from .store import synthetic_case_records
    row = next((row for row in synthetic_case_records() if row["id"] == case_id), None)
    if row is None or name not in row["payload"]["fields"]:
        return []
    return list(dict.fromkeys([row["payload"]["fields"][name]["value"] or "",
                               *OPTIONS["corrections"].get(name, [])]))


def reserve(kind):
    from .domain import fail
    from .store import connection, now
    daily, per_minute = LIMITS[kind]
    timestamp = now()
    day, minute = timestamp[:10], timestamp[:16]
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM showcase_usage WHERE name=?", (kind,)).fetchone()
        day_count = row["day_count"] if row is not None and row["day"] == day else 0
        minute_count = row["minute_count"] if row is not None and row["minute"] == minute else 0
        if day_count >= daily:
            fail(429, f"PUBLIC_{kind.upper()}_DAILY_LIMIT")
        if minute_count >= per_minute:
            fail(429, f"PUBLIC_{kind.upper()}_MINUTE_LIMIT")
        if row is None:
            db.execute("INSERT INTO showcase_usage VALUES(?,?,?,?,?)", (kind, day, 1, minute, 1))
        else:
            db.execute("UPDATE showcase_usage SET day=?,day_count=?,minute=?,minute_count=? WHERE name=?",
                       (day, day_count + 1, minute, minute_count + 1, kind))


class PublicBodyBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from .profile import showcase
        if scope["type"] != "http" or not showcase():
            return await self.app(scope, receive, send)
        import asyncio
        from starlette.responses import JSONResponse
        headers = dict(scope.get("headers", []))
        status, code = 413, "PUBLIC_BODY_LIMIT"
        body = bytearray()
        if headers.get(b"content-encoding", b"identity").lower() != b"identity":
            status, code = 415, "ENCODING_NOT_SUPPORTED"
        else:
            accepted = False
            try:
                async with asyncio.timeout(BODY_READ_SECONDS):
                    while True:
                        chunk = await receive()
                        if chunk["type"] == "http.disconnect":
                            return
                        chunk_body = chunk.get("body", b"")
                        if len(body) + len(chunk_body) > 24_000:
                            break
                        body.extend(chunk_body)
                        if not chunk.get("more_body"):
                            if body and headers.get(b"content-type", b"").split(b";")[0].lower() != b"application/json":
                                status, code = 415, "JSON_ONLY_NO_UPLOADS"
                                break
                            accepted = True
                            break
            except TimeoutError:
                status, code = 408, "BODY_READ_TIMEOUT"
            if accepted:
                delivered = False

                async def replay():
                    nonlocal delivered
                    if not delivered:
                        delivered = True
                        return {"type": "http.request", "body": bytes(body), "more_body": False}
                    return await receive()
                return await self.app(scope, replay, send)
        response = JSONResponse({"error": {"code": code, "traceId": secrets.token_hex(12)}}, status_code=status)
        await response(scope, receive, send)
