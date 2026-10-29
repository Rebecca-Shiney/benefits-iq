import asyncio
import os
import secrets
from contextvars import ContextVar
from pathlib import Path

from agent_framework import Agent, AgentResponse, AgentResponseUpdate, BaseAgent, Content, Message, ResponseStream
from agent_framework.openai import OpenAIChatClient

from . import domain
from .store import audit, connection
from .profile import starter
from .cancellation import run_blocking


request_context: ContextVar[tuple[domain.Identity, str]] = ContextVar("request_context")


def route_intent(text: str) -> str:
    normalized = text.lower()
    if any(w in normalized for w in ("approve", "decline", "reject", "send", "pay")):
        return "human_checkpoint"
    if any(w in normalized for w in ("employer", "trend", "aggregate")):
        return "employer"
    if any(w in normalized for w in ("renew", "expir")):
        return "renewal"
    if any(w in normalized for w in ("intake", "form", "missing", "complete")):
        return "intake"
    if any(w in normalized for w in ("evidence", "criteria", "claim", "review")):
        return "evidence"
    if any(w in normalized for w in ("status", "update", "where")):
        return "status"
    return "escalation"


class SyntheticOrchestrator(BaseAgent):
    """Deterministic specialist routing using the real MAF streaming protocol."""

    def __init__(self):
        super().__init__(id="health_benefits_orchestrator", name="Benefits IQ",
                         description="Deterministic synthetic workflow; no live AI connection.")

    def run(self, messages=None, *, stream=False, session=None, **kwargs):
        identity, case_id = request_context.get()
        latest = ""
        for message in messages or []:
            if isinstance(message, Message) and message.role == "user":
                latest = message.text
        intent = route_intent(latest)

        async def updates():
            message_id, call_id = secrets.token_hex(12), secrets.token_hex(12)
            tool = {"intake": "extract_authorization_form", "evidence": "retrieve_drug_criteria",
                    "status": "get_case_status", "renewal": "get_expiring_authorizations"}.get(intent)
            if tool:
                yield AgentResponseUpdate(contents=[Content.from_function_call(
                    call_id=call_id, name=tool, arguments="{}")], role="assistant")
            if intent == "intake":
                data = domain.extract_authorization_form(identity, case_id)
                text = "Intake Agent: " + ("Verify these missing or uncertain fields: " + ", ".join(data["missing"]) if data["missing"] else "Required fields are present.") + " Use Run intake to persist the check."
            elif intent == "evidence":
                criteria = domain.retrieve_drug_criteria(identity, case_id)
                text = "Evidence Agent: " + (criteria["gap"] or "Versioned synthetic criteria are available.") + " Use Prepare evidence to save the cited matrix. A human must decide."
            elif intent == "status":
                text = "Status Agent: " + domain.case_view(identity, case_id)["message"]
            elif intent == "renewal":
                result = domain.renewals(identity, 30)
                text = f"Renewal Agent: {len(result)} authorizations in your permitted portfolio expire within 30 days. No renewal or outreach has been sent."
            elif intent == "human_checkpoint":
                text = "A human checkpoint is required. Chat cannot record clinical decisions, pay claims or send communications. Use the authorized decision panel or confirmed local communication action."
            elif intent == "employer":
                text = "Employer Insight is available only in the separate authorized aggregate view. Clinical tools are not assigned to that view."
            else:
                text = "Please choose intake completeness, evidence preparation or case status. Unsupported requests require human clarification."
            if tool:
                with connection() as db:
                    audit(db, case_id, identity.id, f"agent_{tool}", call_id)
                yield AgentResponseUpdate(contents=[Content.from_function_result(
                    call_id=call_id, result={"status": "completed", "mode": "synthetic"})], role="tool")
            for word in ("Synthetic mode - no model call. " + text).split(" "):
                await asyncio.sleep(0.015)
                yield AgentResponseUpdate(contents=[Content.from_text(word + " ")], role="assistant", message_id=message_id)

        response = ResponseStream(updates(), finalizer=lambda parts: AgentResponse(
            messages=[Message("assistant", "".join(p.text for p in parts))]))
        if stream:
            return response
        return response.get_final_response()


def model_agent():
    if not starter() and (not os.environ.get("OPENAI_API_KEY") or not os.environ.get("OPENAI_MODEL")):
        domain.fail(503, "LIVE_MODEL_NOT_CONFIGURED")
    identity, case_id = request_context.get()
    # Bind context at construction; a model cannot choose another member or case.
    async def get_case_status() -> str:
        """Return the permitted case's public status, without clinical detail."""
        return (await run_blocking(domain.case_view, identity, case_id))["message"]

    async def read_intake_completeness() -> str:
        """Check the current synthetic form. No authoritative state is modified."""
        return str((await run_blocking(domain.extract_authorization_form, identity, case_id))["missing"])

    async def read_criteria_version() -> str:
        """Return the governed synthetic criteria version or explicit source gap."""
        result = await run_blocking(domain.retrieve_drug_criteria, identity, case_id)
        return result["gap"] or result["version"]

    tools = [get_case_status]
    if identity.role == "reviewer":
        tools.extend([read_intake_completeness, read_criteria_version])
    prompt = (Path(__file__).parent.parent / "agents" / "orchestrator.md").read_text()
    if starter():
        from .azure_services import credential, endpoint
        client = OpenAIChatClient(
            model=os.environ["BENEFITS_MODEL_DEPLOYMENT"],
            azure_endpoint=endpoint("BENEFITS_MODEL_ENDPOINT", "openai.azure.com"),
            credential=credential(), api_version="2024-10-21",
        )
    else:
        client = OpenAIChatClient(model=os.environ["OPENAI_MODEL"])
    return Agent(
        name="health_benefits_orchestrator",
        client=client,
        default_options={"store": False, "max_tokens": 1500},
        instructions=prompt + "\nYou have only read-only, case-bound capabilities. Never infer clinical facts. "
        "State that all evidence sources are synthetic. Tell the user to use controlled UI actions for intake, evidence saves and human decisions.",
        tools=tools,
    )


class ConfiguredModelOrchestrator(SyntheticOrchestrator):
    def run(self, messages=None, *, stream=False, session=None, **kwargs):
        return model_agent().run(messages, stream=stream)
