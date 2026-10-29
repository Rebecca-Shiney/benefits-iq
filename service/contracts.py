from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Outcome(StrEnum):
    APPROVE = "approved"
    DECLINE = "declined"
    MORE = "information_requested"


class CaseAction(Contract):
    version: int = Field(ge=1)


class DecisionInput(CaseAction):
    outcome: Outcome
    reason: str = Field(min_length=10, max_length=1000)
    brief_version: int = Field(ge=1)
    idempotency_key: str = Field(min_length=16, max_length=100)
    confirmed: Literal[True]

    @field_validator("reason")
    @classmethod
    def meaningful_reason(cls, value: str):
        if len(value.strip()) < 10:
            raise ValueError("A meaningful human rationale is required.")
        return value.strip()


class FormField(Contract):
    value: str | None = Field(max_length=1000)
    confidence: float = Field(ge=0, le=1)
    source: str

    @field_validator("value")
    @classmethod
    def normalized_value(cls, value: str | None):
        return value.strip() or None if value is not None else None


class FormInput(CaseAction):
    fields: dict[str, FormField]


class Source(Contract):
    id: str
    version: str
    as_of: str
    title: str
    passage: str


class EvidenceItem(Contract):
    criterion: str
    state: Literal["supported", "missing", "conflict", "unknown"]
    explanation: str
    sources: list[Source]


class Brief(Contract):
    schema_version: Literal["1.0"] = "1.0"
    version: int
    criteria_version: str | None
    items: list[EvidenceItem]
    gaps: list[str]
    conflicts: list[str]
    prepared_by: Literal["deterministic-synthetic"] = "deterministic-synthetic"


class DraftInput(Contract):
    text: str = Field(min_length=1, max_length=2000)
    confirmed: Literal[True]

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value: str):
        if not value.strip():
            raise ValueError("Draft cannot be blank.")
        return value.strip()


class RunRequest(Contract):
    intent: Literal["intake", "evidence", "status"]
    version: int = Field(ge=1)


class PublicQuery(Contract):
    program: Literal["synthetic-specialty-assistance"]


class Activity(Contract):
    activity: Literal[
        "intake_completeness", "criteria_evidence", "case_status",
        "reviewer_decision_requested", "missing_information_draft",
        "member_update_draft", "employer_aggregate",
    ]
    version: Literal["1.0"] = "1.0"
    caseId: str
    traceId: str
    data: dict[str, str | int | list[str]]


class Claim(Contract):
    id: str
    therapy: str
    date: str
    version: str


class Member360(Contract):
    name: str
    member_id: str
    plan: str
    coverage: Literal["active", "inactive"]
    fields: dict[str, FormField]
    claims: list[Claim]
    form_source: str
    form_version: str


class Extraction(Contract):
    fields: dict[str, FormField]
    missing: list[str]
    source_version: str
    as_of: str


class Eligibility(Contract):
    eligible: bool
    reason_codes: list[str]
    source: str
    source_version: str
    as_of: str


class CriteriaLookup(Contract):
    version: str | None
    passages: list[Source]
    gap: str | None


class AssignmentInput(CaseAction):
    owner: str = Field(max_length=40)
    priority: Literal["standard", "priority"]


class TaskInput(Contract):
    kind: Literal["verify_form", "resolve_evidence", "member_follow_up", "renewal_review"]


class TaskUpdate(CaseAction):
    state: Literal["open", "in_progress", "done"]
