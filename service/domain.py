import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import date, timedelta

from fastapi import HTTPException

from .contracts import Brief, CriteriaLookup, DecisionInput, Eligibility, EvidenceItem, Extraction, FormInput, Member360, Source
from .catalog import CRITERIA, PLANS
from .store import audit, connection, now
from .profile import starter


@dataclass(frozen=True)
class Identity:
    id: str
    role: str
    employer: str


IDENTITIES = {
    "reviewer-a": Identity("reviewer-a", "reviewer", "SYN-EMP-A"),
    "reviewer-b": Identity("reviewer-b", "reviewer", "SYN-EMP-B"),
    "contact-a": Identity("contact-a", "contact", "SYN-EMP-A"),
    "employer-a": Identity("employer-a", "employer", "SYN-EMP-A"),
    "employer-b": Identity("employer-b", "employer", "SYN-EMP-B"),
}
REQUIRED_FIELDS = {"member_id", "drug", "indication", "prescriber", "prior_therapy"}


def identities():
    if starter():
        from .entra_auth import EntraConfiguration
        return EntraConfiguration.from_environment().identities
    return IDENTITIES


def member_payload(db, row):
    if starter():
        from .azure_services import member_payload as cloud_payload
        return cloud_payload(db, row)
    return json.loads(row["payload"])


def plan_document(plan_id, employer):
    if starter():
        from .azure_services import plan_document as cloud_plan
        return cloud_plan(plan_id, employer)
    return PLANS[plan_id]


def source_criterion(payload, employer):
    if starter():
        from .azure_services import source_criterion as cloud_criterion
        return cloud_criterion(payload, employer)
    return CRITERIA.get((payload["plan"], payload["fields"]["drug"]["value"], payload["fields"]["indication"]["value"]))


def fail(status: int, code: str):
    raise HTTPException(status, detail={"code": code, "traceId": secrets.token_hex(12)})


def authorize(identity: Identity, row, reviewer=False):
    if not row or identity.employer != row["employer"] or identity.role == "employer":
        fail(403, "CASE_ACCESS_DENIED")
    if reviewer and identity.role != "reviewer":
        fail(403, "REVIEWER_REQUIRED")


def load(db, identity: Identity, case_id: str, reviewer=False):
    row = db.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    authorize(identity, row, reviewer)
    return row


def check_version(row, version: int):
    if row["version"] != version:
        fail(409, "STALE_CASE_REFRESH_REQUIRED")


def status_payload(row):
    labels = {
        "received": "Your request has been received.",
        "intake_checked": "Your request is being prepared for review.",
        "intake_incomplete": "Your form needs verification before clinical review.",
        "review_ready": "Your request is waiting for a clinical reviewer.",
        "approved": "Your request was approved by a clinical reviewer.",
        "declined": "Your request was declined by a clinical reviewer.",
        "information_requested": "Additional information has been requested.",
    }
    return {
        "id": row["id"], "state": row["state"], "version": row["version"],
        "message": labels[row["state"]],
        "next_owner": "Contact centre" if row["state"] == "information_requested" else "Intake review team" if row["state"] == "intake_incomplete" else "Clinical review team",
        "expiry": row["expiry"],
    }


def case_view(identity: Identity, case_id: str):
    with connection() as db:
        row = load(db, identity, case_id)
        result = status_payload(row)
        timeline = db.execute(
            "SELECT id,event,created,trace,actor FROM audit WHERE case_id=? ORDER BY id", (case_id,)
        ).fetchall()
        # Contact centre receives public status events only, not internal action names.
        public = {"form_received", "human_decision_saved", "communication_confirmed",
                  "follow_up_task_created", "follow_up_task_updated"}
        result["timeline"] = [
            {k: x[k] for k in x.keys() if k != "actor" or identity.role == "reviewer"}
            for x in timeline if identity.role == "reviewer" or x["event"] in public
        ]
        result["update_draft"] = result["message"] + " Please contact the support team for the next step. No decision date is promised."
        if identity.role == "reviewer":
            payload = Member360.model_validate(member_payload(db, row)).model_dump()
            result.update({
                "employer": row["employer"], "member": row["member"], "scenario": row["scenario"],
                "member360": payload,
                "brief": Brief.model_validate_json(row["brief"]).model_dump() if row["brief"] else None,
                "decision": json.loads(row["decision"]) if row["decision"] else None,
                "missing_information_draft": "Please verify the following form fields: " + ", ".join(missing_fields(payload)) if missing_fields(payload) else None,
            })
        return result


def queue(identity: Identity):
    if identity.role == "employer":
        fail(403, "AGGREGATE_ONLY")
    with connection() as db:
        rows = db.execute("SELECT * FROM cases WHERE employer=? ORDER BY id", (identity.employer,)).fetchall()
        return [status_payload(x) for x in rows]


def missing_fields(payload):
    return sorted(
        name for name in REQUIRED_FIELDS
        if not payload["fields"].get(name, {}).get("value")
        or payload["fields"][name]["confidence"] < 0.85
    )


def extract_authorization_form(identity: Identity, case_id: str):
    with connection() as db:
        row = load(db, identity, case_id, True)
        payload = json.loads(row["payload"])
    if starter() and not payload["form_version"].startswith("form-verified-"):
        from .azure_services import extract_document
        return extract_document(row)
    else:
        return Extraction(fields=payload["fields"], missing=missing_fields(payload),
                          source_version=payload["form_version"], as_of=now()).model_dump()


def get_member_360(identity: Identity, case_id: str):
    with connection() as db:
        return Member360.model_validate(member_payload(db, load(db, identity, case_id, True))).model_dump()


def check_plan_eligibility(identity: Identity, case_id: str):
    payload = get_member_360(identity, case_id)
    return eligibility_for(payload, identity.employer)


def eligibility_for(payload, employer):
    plan = plan_document(payload["plan"], employer)
    valid = payload["coverage"] == "active" and payload["fields"]["drug"]["value"] in plan["covered_drugs"]
    return Eligibility(eligible=valid, reason_codes=[] if valid else ["DRUG_PLAN_REVIEW_REQUIRED"],
                       source=payload["plan"], source_version=plan["version"], as_of=plan["as_of"]).model_dump()


def get_claims_history(identity: Identity, case_id: str):
    return get_member_360(identity, case_id)["claims"]


def retrieve_drug_criteria(identity: Identity, case_id: str):
    payload = get_member_360(identity, case_id)
    if starter():
        from .azure_services import retrieve_criteria
        criterion = retrieve_criteria(payload, identity.employer)
    else:
        criterion = source_criterion(payload, identity.employer)
    if not criterion or criterion["valid_until"] < date.today().isoformat():
        return CriteriaLookup(version=None, passages=[], gap="Criteria absent or stale for this drug/indication/plan; human escalation required.").model_dump()
    return CriteriaLookup(version=criterion["version"], passages=[
        Source(id=criterion["id"], version=criterion["version"], as_of=criterion["as_of"],
               title="Synthetic Therapy Alpha criteria",
               passage=criterion["passage"]).model_dump()
    ], gap=None).model_dump()


def lookup_public_program(program: str):
    # An enum, not free text, is the only accepted lookup input. No external send occurs.
    if program != "synthetic-specialty-assistance":
        fail(422, "GENERAL_PROGRAM_QUERY_ONLY")
    return Source(id="SYN-PUBLIC-PROGRAM", version="public-fixture-v1", as_of="2026-10-01",
                  title="Synthetic public assistance reference (not live policy)",
                  passage="Program eligibility needs separate verification; no entitlement is inferred.").model_dump()


def prepare_brief(identity: Identity, case_id: str, version: int, trace_id: str | None = None):
    payload = get_member_360(identity, case_id)
    criteria = retrieve_drug_criteria(identity, case_id)
    eligibility = check_plan_eligibility(identity, case_id)
    claims = get_claims_history(identity, case_id)
    missing = missing_fields(payload)
    conflict = payload["fields"]["prior_therapy"]["value"] == "none" and bool(claims)
    policy_sources = [Source.model_validate(s) for s in criteria["passages"]]
    form = Source(id=payload["form_source"], version=payload["form_version"],
                  as_of="2026-10-01", title="Synthetic authorization form",
                  passage="Verified structured fields; uncertain fields are not inferred.")
    coverage_document = plan_document(payload["plan"], identity.employer)
    plan = Source(id=payload["plan"], version=coverage_document["version"], as_of=coverage_document["as_of"],
                  title="Synthetic plan coverage", passage=coverage_document["passage"])
    claim_sources = [Source(id=c["id"], version=c["version"], as_of=c["date"],
                            title="Synthetic prior therapy claim", passage=c["therapy"]) for c in claims]
    gap = criteria["gap"]
    items = [
        EvidenceItem(criterion="Plan eligibility", state="unknown" if gap else "supported" if eligibility["eligible"] else "missing",
                     explanation=f"Active coverage checked against {coverage_document['version']}; reviewer must resolve any mismatch.",
                     sources=[plan] + policy_sources),
        EvidenceItem(criterion="Verified prescriber", state="unknown" if gap else "missing" if "prescriber" in missing else "supported",
                     explanation="Low confidence is treated as missing; no inferred prescriber.",
                     sources=[form] + policy_sources),
        EvidenceItem(criterion="Prior therapy", state="unknown" if gap else "conflict" if conflict else "supported" if claims and "prior_therapy" not in missing else "missing",
                     explanation="Form and claims conflict." if conflict else "Cited synthetic claims establish prior therapy evidence, not a clinical outcome.",
                     sources=[form] + claim_sources + policy_sources),
        EvidenceItem(criterion="Public program consideration", state="unknown",
                     explanation="Fixture reference only; verify eligibility separately.",
                     sources=[Source.model_validate(lookup_public_program("synthetic-specialty-assistance"))]),
    ]
    brief = Brief(version=1, criteria_version=criteria["version"], items=items,
                  gaps=missing + ([gap] if gap else []),
                  conflicts=["Form reports no prior therapy but claims record therapy."] if conflict else [])
    trace = trace_id or secrets.token_hex(12)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = load(db, identity, case_id, True)
        check_version(row, version)
        if row["decision"]:
            fail(409, "DECIDED_CASE_IMMUTABLE")
        latest_version = db.execute("SELECT max(version) FROM briefs WHERE case_id=?", (case_id,)).fetchone()[0]
        brief.version = (latest_version or 0) + 1
        db.execute("INSERT INTO briefs VALUES(?,?,?,?,?)",
                   (case_id, brief.version, brief.model_dump_json(), identity.id, now()))
        db.execute("UPDATE cases SET brief=?,state='review_ready',version=version+1 WHERE id=?",
                   (brief.model_dump_json(), case_id))
        for event in ("member_360_checked", "claims_checked", "criteria_retrieved", "public_fixture_checked", "evidence_brief_saved"):
            audit(db, case_id, identity.id, event, trace)
    return {"brief": brief.model_dump(), "traceId": trace, "version": version + 1}


def brief_history(identity: Identity, case_id: str):
    with connection() as db:
        load(db, identity, case_id, True)
        rows = db.execute("SELECT payload,actor,created FROM briefs WHERE case_id=? ORDER BY version", (case_id,)).fetchall()
        return [{"brief": Brief.model_validate_json(r["payload"]).model_dump(),
                 "actor": r["actor"], "created": r["created"]} for r in rows]


def intake(identity: Identity, case_id: str, version: int, trace_id: str | None = None):
    result = extract_authorization_form(identity, case_id)
    payload = get_member_360(identity, case_id)
    eligibility = eligibility_for({**payload, "fields": result["fields"]}, identity.employer)
    trace = trace_id or secrets.token_hex(12)
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = load(db, identity, case_id, True)
        check_version(row, version)
        if row["decision"]:
            fail(409, "DECIDED_CASE_IMMUTABLE")
        state = "intake_incomplete" if result["missing"] else "intake_checked"
        if starter():
            payload = json.loads(row["payload"])
            payload["fields"] = result["fields"]
            payload["form_version"] = result["source_version"]
            db.execute("UPDATE cases SET payload=?,brief=NULL,state=?,version=version+1 WHERE id=?",
                       (json.dumps(payload), state, case_id))
        else:
            db.execute("UPDATE cases SET state=?,version=version+1 WHERE id=?", (state, case_id))
        audit(db, case_id, identity.id, "intake_completeness", trace)
    return {**result, "eligibility": eligibility, "traceId": trace, "version": version + 1,
            "draft": "Please verify the following form fields: " + ", ".join(result["missing"]) if result["missing"] else None}


def verify_form(identity: Identity, case_id: str, request: FormInput):
    if set(request.fields) != REQUIRED_FIELDS:
        fail(422, "EXACT_FORM_FIELDS_REQUIRED")
    if any(f.source != f"{case_id.replace('SYN-CASE', 'SYN-FORM')}#{name}" for name, f in request.fields.items()):
        fail(422, "FORM_SOURCE_MISMATCH")
    if request.fields["member_id"].value != case_id.replace("SYN-CASE", "SYN-MEMBER"):
        fail(422, "MEMBER_MISMATCH")
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = load(db, identity, case_id, True)
        check_version(row, request.version)
        if row["decision"]:
            fail(409, "DECIDED_CASE_IMMUTABLE")
        payload = json.loads(row["payload"])
        payload["fields"] = {k: v.model_dump() for k, v in request.fields.items()}
        payload["form_version"] = f"form-verified-case-v{row['version'] + 1}"
        db.execute("UPDATE cases SET payload=?,brief=NULL,state='received',version=version+1 WHERE id=?",
                   (json.dumps(payload), case_id))
        audit(db, case_id, identity.id, "form_human_verified", secrets.token_hex(12))
    return case_view(identity, case_id)


def record_human_decision(identity: Identity, case_id: str, request: DecisionInput):
    fingerprint = hashlib.sha256(request.model_dump_json().encode()).hexdigest()
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = load(db, identity, case_id, True)
        existing = db.execute("SELECT * FROM decisions WHERE [key]=?", (request.idempotency_key,)).fetchone()
        if existing:
            if existing["case_id"] != case_id or existing["actor"] != identity.id or existing["fingerprint"] != fingerprint:
                fail(409, "IDEMPOTENCY_KEY_REUSED")
            return json.loads(existing["response"])
        check_version(row, request.version)
        if row["decision"]:
            fail(409, "DECISION_ALREADY_RECORDED")
        if not row["brief"] or Brief.model_validate_json(row["brief"]).version != request.brief_version:
            fail(409, "CURRENT_EVIDENCE_BRIEF_REQUIRED")
        decision = {
            "outcome": request.outcome, "reason": request.reason, "reviewer": identity.id,
            "timestamp": now(), "brief_version": request.brief_version, "traceId": secrets.token_hex(12),
        }
        db.execute("UPDATE cases SET decision=?,state=?,version=version+1 WHERE id=?",
                   (json.dumps(decision), request.outcome, case_id))
        audit(db, case_id, identity.id, "human_decision_saved", decision["traceId"])
        response = {**decision, "version": request.version + 1}
        db.execute("INSERT INTO decisions VALUES(?,?,?,?,?)",
                   (request.idempotency_key, case_id, identity.id, fingerprint, json.dumps(response)))
    return response


def employer_aggregate(identity: Identity, employer: str):
    if identity.role != "employer" or identity.employer != employer:
        fail(403, "EMPLOYER_SCOPE_DENIED")
    if starter():
        from .azure_services import aggregate
        return aggregate(employer)
    # Separate fictional portfolio; never derive cells from the workflow members.
    return {"employer": employer, "dataset": "separate-synthetic-portfolio-v1", "as_of": "2026-10-01",
            "minimum_cell": 10, "rows": [
                {"period": "2026 Q2", "members": 160 if employer.endswith("A") else 140, "specialty_utilizers": 24, "cost": 48000},
                {"period": "2026 Q3", "members": 170 if employer.endswith("A") else 150, "specialty_utilizers": 28, "cost": 56000},
                {"period": "Rare subgroup", "members": None, "specialty_utilizers": None, "cost": None},
            ], "suppression": "Cells below 10 and associated totals suppressed. No member drill-through or causal inference."}


def renewals(identity: Identity, window: int):
    if identity.role != "reviewer":
        fail(403, "REVIEWER_REQUIRED")
    if window not in {30, 60, 90}:
        fail(422, "CONFIGURED_RENEWAL_WINDOW_REQUIRED")
    with connection() as db:
        rows = db.execute(
            "SELECT * FROM cases WHERE employer=? AND expiry BETWEEN ? AND ?",
            (identity.employer, date.today().isoformat(), (date.today() + timedelta(days=window)).isoformat()),
        ).fetchall()
        return [{**status_payload(r), "draft": "Please begin the renewal review before the recorded expiry. This draft does not extend coverage."} for r in rows]
