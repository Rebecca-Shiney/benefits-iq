import asyncio
import hmac
import json
import logging
import os
import secrets
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from time import monotonic
from typing import Literal

from agent_framework_ag_ui import AgentFrameworkAgent, add_agent_framework_fastapi_endpoint
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response, StreamingResponse

from . import domain, operations
from .agents import ConfiguredModelOrchestrator, SyntheticOrchestrator, request_context
from .contracts import Activity, AssignmentInput, DecisionInput, DraftInput, FormInput, PublicQuery, RunRequest, TaskInput, TaskUpdate
from .store import audit, connection, initialize, now
from .profile import profile, starter
from .entra_auth import EntraAuthError, EntraAuthenticator, EntraConfiguration
from .cloud_errors import CloudServiceError, SqlStoreError
from .cancellation import WorkflowCancellation, WorkflowCancelled, run_blocking


logger = logging.getLogger("benefits")


@asynccontextmanager
async def lifespan(app):
    if starter():
        if any(os.environ.get(name) for name in ("BENEFITS_SERVICE_SECRET", "OPENAI_API_KEY", "AZURE_CLIENT_SECRET")):
            raise RuntimeError("STARTER_DISALLOWS_STATIC_APPLICATION_CREDENTIALS")
        app.state.entra = EntraAuthenticator(EntraConfiguration.from_environment())
        from .azure_services import validate_configuration
        validate_configuration()
    else:
        secret = os.environ.get("BENEFITS_SERVICE_SECRET", "")
        if len(secret) < 32:
            raise RuntimeError("BENEFITS_SERVICE_SECRET must contain at least 32 characters.")
    initialize()
    yield


app = FastAPI(title="Benefits IQ synthetic capability API", version="1.0", lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
requests_by_user: dict[str, deque] = defaultdict(deque)


def enabled(feature: str) -> bool:
    return os.environ.get(f"BENEFITS_ENABLE_{feature.upper()}", "1") == "1"


def require_feature(feature: str):
    if not enabled(feature):
        domain.fail(403, "FEATURE_DISABLED")


async def authenticate(request: Request, authorization: str = Header(""), x_benefits_user: str = Header(""),
                       x_benefits_runtime_authorization: str = Header("")):
    if starter():
        identity = await asyncio.to_thread(request.app.state.entra.authenticate,
                                          x_benefits_runtime_authorization, authorization)
    else:
        expected = os.environ.get("BENEFITS_SERVICE_SECRET", "")
        if len(expected) < 32 or not hmac.compare_digest(authorization, "Bearer " + expected):
            domain.fail(401, "SERVICE_AUTH_REQUIRED")
        identity = domain.IDENTITIES.get(x_benefits_user)
        if not identity:
            domain.fail(401, "DEMO_SESSION_REQUIRED")
    recent = requests_by_user[identity.id]
    current = monotonic()
    while recent and recent[0] < current - 60:
        recent.popleft()
    if len(recent) >= 120:
        domain.fail(429, "RATE_LIMIT_RETRY_LATER")
    recent.append(current)
    request.state.identity = identity
    return identity


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse({"error": {"code": "INVALID_REQUEST", "traceId": secrets.token_hex(12)}}, status_code=422)


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(EntraAuthError)
async def entra_error(request, exc):
    return JSONResponse({"error": {"code": exc.code, "traceId": secrets.token_hex(12)}}, status_code=exc.status)


@app.exception_handler(SqlStoreError)
async def sql_error(request, exc):
    trace = secrets.token_hex(12)
    logger.error("SQL unavailable code=%s trace=%s", exc.code, trace)
    return JSONResponse({"error": {"code": exc.code, "traceId": trace}}, status_code=503)


@app.exception_handler(CloudServiceError)
async def cloud_error(request, exc):
    trace = secrets.token_hex(12)
    logger.error("Cloud capability unavailable code=%s trace=%s", exc.code, trace)
    return JSONResponse({"error": {"code": exc.code, "traceId": trace}}, status_code=503)


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    trace = secrets.token_hex(12)
    logger.error("Unexpected request failure trace=%s type=%s", trace, type(exc).__name__)
    return JSONResponse({"error": {"code": "INTERNAL_ERROR", "traceId": trace}}, status_code=500)


@app.get("/health")
def health():
    return {"status": "alive", "profile": profile(), "data": "synthetic-only", "schema_version": "1.0"}


@app.get("/api/session")
def session(identity=Depends(authenticate)):
    return {"id": identity.id, "role": identity.role, "employer": identity.employer,
            "mode": "live" if starter() else os.environ.get("BENEFITS_MODE", "synthetic"),
            "profile": profile(),
            "features": {f: enabled(f) for f in ("chat", "intake", "evidence", "renewal", "employer", "activities")}}


@app.get("/api/cases")
def queue(identity=Depends(authenticate)):
    return domain.queue(identity)


@app.get("/api/workbench")
def workbench(search: str = Query("", max_length=100),
              state: Literal["all", "received", "intake_checked", "intake_incomplete", "review_ready", "approved", "declined", "information_requested"] = "all",
              priority: Literal["all", "standard", "priority"] = "all",
              owner: Literal["all", "mine", "unassigned"] = "all",
              sort: Literal["target", "oldest", "newest", "priority"] = "target",
              identity=Depends(authenticate)):
    return operations.workbench(identity, search, state, priority, owner, sort)


@app.get("/api/cases/{case_id}/operations")
def case_operations(case_id: str, identity=Depends(authenticate)):
    return operations.detail(identity, case_id)


@app.post("/api/cases/{case_id}/assignment")
def assignment(case_id: str, body: AssignmentInput, identity=Depends(authenticate)):
    return operations.assign(identity, case_id, body)


@app.post("/api/cases/{case_id}/tasks")
def create_task(case_id: str, body: TaskInput, identity=Depends(authenticate)):
    return operations.create_task(identity, case_id, body)


@app.post("/api/cases/{case_id}/tasks/{task_id}")
def update_task(case_id: str, task_id: str, body: TaskUpdate, identity=Depends(authenticate)):
    return operations.update_task(identity, case_id, task_id, body)


@app.get("/api/cases/{case_id}")
def case(case_id: str, identity=Depends(authenticate)):
    return domain.case_view(identity, case_id)


@app.get("/api/cases/{case_id}/document")
def source_document(case_id: str, identity=Depends(authenticate)):
    with connection() as db:
        row = domain.load(db, identity, case_id, True)
        if not starter():
            domain.fail(404, "LOCAL_STRUCTURED_FIXTURE_ONLY")
        from .azure_services import intake_document
        document = intake_document(db, row)
    return Response(bytes(document["content"]), media_type="application/pdf", headers={
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": f'attachment; filename="{case_id}-synthetic-intake.pdf"',
    })


@app.get("/api/cases/{case_id}/briefs")
def briefs(case_id: str, identity=Depends(authenticate)):
    return domain.brief_history(identity, case_id)


@app.post("/api/cases/{case_id}/form")
def form(case_id: str, body: FormInput, identity=Depends(authenticate)):
    return domain.verify_form(identity, case_id, body)


@app.post("/api/cases/{case_id}/decision")
def decision(case_id: str, body: DecisionInput, identity=Depends(authenticate)):
    return domain.record_human_decision(identity, case_id, body)


@app.post("/api/cases/{case_id}/communication")
def communication(case_id: str, body: DraftInput, identity=Depends(authenticate)):
    with connection() as db:
        domain.load(db, identity, case_id)
        db.execute("INSERT INTO communications(case_id,actor,text,created) VALUES(?,?,?,?)",
                   (case_id, identity.id, body.text, now()))
        trace = secrets.token_hex(12)
        audit(db, case_id, identity.id, "communication_confirmed", trace)
    return {"delivery": "local-outbox-only", "external_send": False, "traceId": trace}


@app.get("/api/employers/{employer}/aggregate")
def aggregate(employer: str, identity=Depends(authenticate)):
    require_feature("employer")
    return domain.employer_aggregate(identity, employer)


@app.get("/api/renewals")
def renewal(window: int = Query(30), identity=Depends(authenticate)):
    require_feature("renewal")
    return domain.renewals(identity, window)


@app.post("/api/public-program")
def public(body: PublicQuery, identity=Depends(authenticate)):
    if identity.role != "reviewer":
        domain.fail(403, "REVIEWER_REQUIRED")
    return domain.lookup_public_program(body.program)


@app.post("/api/cases/{case_id}/run")
async def run(case_id: str, body: RunRequest, request: Request, identity=Depends(authenticate)):
    if body.intent != "status":
        require_feature(body.intent)
    def validate_case():
        with connection() as db:
            row = domain.load(db, identity, case_id, body.intent != "status")
            domain.check_version(row, body.version)
    await run_blocking(validate_case)
    run_id = secrets.token_hex(12)

    async def workflow_events(cancellation):
        sequence = 0
        capabilities = {
            "extract_authorization_form": lambda: domain.extract_authorization_form(identity, case_id),
            "check_plan_eligibility": lambda: domain.check_plan_eligibility(identity, case_id),
            "get_member_360": lambda: domain.get_member_360(identity, case_id),
            "get_claims_history": lambda: domain.get_claims_history(identity, case_id),
            "retrieve_drug_criteria": lambda: domain.retrieve_drug_criteria(identity, case_id),
            "lookup_public_program": lambda: domain.lookup_public_program("synthetic-specialty-assistance"),
            "get_case_status": lambda: domain.case_view(identity, case_id),
        }

        def encode(event):
            nonlocal sequence
            sequence += 1
            return f"id: {run_id}:{sequence}\ndata: {json.dumps(event)}\n\n"

        yield encode({"type": "RUN_STARTED", "runId": run_id, "threadId": case_id})
        try:
            for step in (["extract_authorization_form", "check_plan_eligibility"] if body.intent == "intake"
                         else ["get_member_360", "get_claims_history", "retrieve_drug_criteria", "lookup_public_program"] if body.intent == "evidence"
                         else ["get_case_status"]):
                if await request.is_disconnected():
                    cancellation.cancel()
                    return
                yield encode({"type": "STEP_STARTED", "stepName": step})
                yield encode({"type": "TOOL_CALL_START", "toolCallId": step, "toolCallName": step})
                await run_blocking(capabilities[step])
                await asyncio.sleep(0.04)
                if await request.is_disconnected():
                    cancellation.cancel()
                    return
                yield encode({"type": "TOOL_CALL_END", "toolCallId": step})
                yield encode({"type": "STEP_FINISHED", "stepName": step})
            if await request.is_disconnected():
                cancellation.cancel()
                return
            if body.intent == "intake":
                result = await run_blocking(domain.intake, identity, case_id, body.version, run_id)
                activity = Activity(activity="intake_completeness", caseId=case_id, traceId=run_id,
                                    data={"missing": result["missing"], "savedVersion": result["version"]})
            elif body.intent == "evidence":
                result = await run_blocking(domain.prepare_brief, identity, case_id, body.version, run_id)
                activity = Activity(activity="criteria_evidence", caseId=case_id, traceId=run_id,
                                    data={"savedVersion": result["version"], "briefVersion": result["brief"]["version"]})
            else:
                result = await run_blocking(domain.case_view, identity, case_id)
                activity = Activity(activity="case_status", caseId=case_id, traceId=run_id,
                                    data={"savedVersion": result["version"]})
            if enabled("activities"):
                yield encode({"type": "CUSTOM", "name": "benefits_activity", "value": activity.model_dump()})
            yield encode({"type": "STATE_SNAPSHOT", "snapshot": {"savedVersion": result["version"]}})
            yield encode({"type": "RUN_FINISHED", "threadId": case_id, "runId": run_id})
        except HTTPException as exc:
            yield encode({"type": "RUN_ERROR", "message": f"{exc.detail['code']} · trace {run_id}", "code": exc.detail["code"]})
        except asyncio.CancelledError:
            cancellation.cancel()
            raise
        except WorkflowCancelled:
            return
        except CloudServiceError as exc:
            logger.error("Workflow capability unavailable code=%s trace=%s", exc.code, run_id)
            yield encode({"type": "RUN_ERROR", "message": f"{exc.code} · trace {run_id}", "code": exc.code})
        except Exception as exc:
            logger.error("Workflow failure trace=%s type=%s", run_id, type(exc).__name__)
            yield encode({"type": "RUN_ERROR", "message": f"Workflow failed. Refresh authoritative case state. Trace {run_id}", "code": "WORKFLOW_ERROR"})

    async def events():
        with WorkflowCancellation() as cancellation:
            async for event in workflow_events(cancellation):
                yield event

    return StreamingResponse(events(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


async def agent_auth(request: Request, identity=Depends(authenticate)):
    require_feature("chat")
    case_id = request.headers.get("x-benefits-case", "")
    def validate_case():
        with connection() as db:
            domain.load(db, identity, case_id)
    await run_blocking(validate_case)
    if starter() and request.url.path != "/ag-ui-live":
        domain.fail(409, "STARTER_REQUIRES_MODEL_RUNTIME")
    if not starter() and request.url.path == "/ag-ui-live" and (
        not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_MODEL")
    ):
        domain.fail(503, "LIVE_MODEL_NOT_CONFIGURED")
    body = await request.json()
    if body.get("tools") or body.get("state") or body.get("forwardedProps"):
        domain.fail(422, "CLIENT_TOOLS_AND_STATE_NOT_ACCEPTED")
    messages = body.get("messages", [])
    if len(messages) > 40 or len(json.dumps(body)) > 24000:
        domain.fail(413, "CONVERSATION_LIMIT")
    if any(m.get("role") not in {"user", "assistant"} for m in messages):
        domain.fail(422, "UNTRUSTED_MESSAGE_ROLE")
    token = request_context.set((identity, case_id))
    try:
        yield
    finally:
        request_context.reset(token)


add_agent_framework_fastapi_endpoint(
    app, AgentFrameworkAgent(SyntheticOrchestrator(), emit_messages_snapshot=False),
    path="/ag-ui", dependencies=[Depends(agent_auth)], keepalive_seconds=10,
)
add_agent_framework_fastapi_endpoint(
    app, AgentFrameworkAgent(ConfiguredModelOrchestrator(), emit_messages_snapshot=False),
    path="/ag-ui-live", dependencies=[Depends(agent_auth)], keepalive_seconds=10,
)
