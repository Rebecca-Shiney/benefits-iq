"""Authorized operational projections and non-clinical workflow actions."""

import json
import secrets
from datetime import date, datetime, timedelta, timezone

from . import domain
from .profile import cloud, showcase
from .contracts import AssignmentInput, TaskInput, TaskUpdate
from .fixtures import EMPLOYERS, TASKS
from .store import audit, connection, now


def task_view(row):
    return {**dict(row), "title": TASKS[row["kind"]]["title"], "team": TASKS[row["kind"]]["team"]}


def visible_tasks(db, identity, case_id=None):
    sql = "SELECT t.* FROM tasks t JOIN cases c ON c.id=t.case_id WHERE c.employer=?"
    args = [identity.employer]
    if identity.role != "reviewer":
        sql += " AND t.role=?"
        args.append(identity.role)
    if case_id:
        sql += " AND t.case_id=?"
        args.append(case_id)
    return [task_view(t) for t in db.execute(sql + " ORDER BY t.due,t.id", args).fetchall()]


def source_context(payload, employer):
    criterion = domain.source_criterion(payload, employer)
    stale = not criterion or criterion["valid_until"] < date.today().isoformat()
    missing = domain.missing_fields(payload)
    conflict = payload["fields"]["prior_therapy"]["value"] == "none" and bool(payload["claims"])
    return missing, conflict, criterion, stale


def workbench(identity, search="", state="all", priority="all", owner="all", sort="target"):
    if identity.role == "employer":
        domain.fail(403, "AGGREGATE_ONLY")
    timestamp = now()
    instant = datetime.fromisoformat(timestamp)
    with connection() as db:
        rows = db.execute(
            "SELECT c.*,o.received,o.target,o.priority,o.owner,o.channel FROM cases c "
            "JOIN case_operations o ON o.case_id=c.id WHERE c.employer=?", (identity.employer,),
        ).fetchall()
        tasks = visible_tasks(db, identity)
        payloads = {row["id"]: domain.member_payload(db, row) for row in rows} if identity.role == "reviewer" else {}
    items = []
    for row in rows:
        active = row["state"] not in {"approved", "declined"}
        target = datetime.fromisoformat(row["target"])
        item = {
            **domain.status_payload(row),
            "received": row["received"], "target": row["target"], "priority": row["priority"],
            "owner": row["owner"], "channel": row["channel"], "request_type": "Renewal" if row["expiry"] else "New request",
            "age_hours": round(max(0, (instant - datetime.fromisoformat(row["received"])).total_seconds() / 3600), 1),
            "target_state": "closed" if not active else "overdue" if target < instant
                            else "due_soon" if target <= instant + timedelta(hours=24) else "on_track",
            "open_tasks": sum(t["case_id"] == row["id"] and t["state"] != "done" for t in tasks),
        }
        if identity.role == "reviewer":
            payload = payloads[row["id"]]
            missing, conflict, _, stale = source_context(payload, identity.employer)
            item.update({"display_name": payload["name"], "member": row["member"],
                         "missing_fields": missing, "conflict": conflict, "source_gap": stale})
        else:
            item["display_name"] = "Authorized status record"
        items.append(item)
    summary = {
        "total": len(items),
        "active": sum(c["target_state"] != "closed" for c in items),
        "overdue": sum(c["target_state"] == "overdue" for c in items),
        "due_soon": sum(c["target_state"] == "due_soon" for c in items),
        "unassigned": sum(c["owner"] == "unassigned" and c["target_state"] != "closed" for c in items),
        "review_ready": sum(c["state"] == "review_ready" for c in items),
        "open_tasks": sum(t["state"] != "done" for t in tasks),
    }
    if identity.role == "reviewer":
        summary.update({"intake_gaps": sum(bool(c["missing_fields"]) for c in items),
                        "source_gaps": sum(c["source_gap"] for c in items),
                        "conflicts": sum(c["conflict"] for c in items)})
    needle = search.strip().lower()
    filtered = [
        c for c in items
        if (not needle or needle in f'{c["id"]} {c["display_name"]} {c.get("member", "")}'.lower())
        and (state == "all" or c["state"] == state)
        and (priority == "all" or c["priority"] == priority)
        and (owner == "all" or c["owner"] == ("unassigned" if owner == "unassigned" else identity.id))
    ]
    keys = {"target": lambda c: (c["target_state"] == "closed", c["target"], c["id"]),
            "oldest": lambda c: (c["received"], c["id"]),
            "newest": lambda c: (c["received"], c["id"]),
            "priority": lambda c: (c["priority"] != "priority", c["target"], c["id"])}
    filtered.sort(key=keys[sort], reverse=sort == "newest")
    return {"as_of": timestamp, "employer": {"id": identity.employer, **EMPLOYERS[identity.employer]},
            "items": filtered, "matched": len(filtered), "summary": summary,
            "tasks": tasks, "states": sorted({c["state"] for c in items}),
            "target_note": "Internal synthetic service target: 24h priority / 72h standard from receipt. Not a clinical deadline or coverage promise."}


def detail(identity, case_id):
    with connection() as db:
        row = domain.load(db, identity, case_id)
        ops = dict(db.execute("SELECT * FROM case_operations WHERE case_id=?", (case_id,)).fetchone())
        result = {
            **ops, "employer": {"id": identity.employer, **EMPLOYERS[identity.employer]},
            "tasks": visible_tasks(db, identity, case_id),
            "outbox": [dict(x) for x in db.execute(
                "SELECT id,text,created FROM communications WHERE case_id=? AND actor=? ORDER BY id DESC",
                (case_id, identity.id),
            ).fetchall()],
        }
        if identity.role == "reviewer":
            payload = domain.member_payload(db, row)
            missing, conflict, criterion, stale = source_context(payload, identity.employer)
            plan = domain.plan_document(payload["plan"], identity.employer)
            documents = [
                {"id": payload["form_source"], "title": "Authorization form", "kind": "Structured fixture",
                 "version": payload["form_version"], "as_of": "2026-10-01",
                 "status": "needs_verification" if missing else "complete",
                 "detail": f'{len(domain.REQUIRED_FIELDS) - len(missing)} / {len(domain.REQUIRED_FIELDS)} fields meet the 85% confidence threshold. No PDF upload or OCR is implied.'},
                {"id": payload["plan"], "title": EMPLOYERS[identity.employer]["plan"], "kind": "Local policy fixture",
                 "version": plan["version"], "as_of": plan["as_of"], "status": "reference",
                 "detail": plan["passage"]},
                {"id": criterion["id"] if criterion else "NO-MATCHING-CRITERIA", "title": "Drug / indication criteria",
                 "kind": "Local criteria fixture", "version": criterion["version"] if criterion else None,
                 "as_of": criterion["as_of"] if criterion else None,
                 "status": "stale" if stale else "current", "valid_until": criterion["valid_until"] if criterion else None,
                 "detail": criterion["passage"] if criterion else "No matching source. Escalate for human source verification."},
            ]
            documents.extend({"id": c["id"], "title": "Prior therapy claim", "kind": "Structured claim fixture",
                              "version": c["version"], "as_of": c["date"], "status": "conflict" if conflict else "reference",
                              "detail": c["therapy"] + ". Evidence of prior therapy only; not a payment or clinical outcome."}
                             for c in payload["claims"])
            if cloud():
                for document in documents:
                    document["kind"] = "Azure SQL synthetic source"
                documents[0]["detail"] = (
                    f'{len(domain.REQUIRED_FIELDS) - len(missing)} / {len(domain.REQUIRED_FIELDS)} fields meet the 85% threshold. '
                    "Run intake for actual Document Intelligence OCR; verified human corrections take precedence."
                )
            result.update({
                "documents": documents, "missing_fields": missing, "conflict": conflict,
                "source_gap": stale, "verified_fields": len(domain.REQUIRED_FIELDS) - len(missing),
                "field_count": len(domain.REQUIRED_FIELDS),
                "owners": [{"id": x.id, "label": "Clinical reviewer / " + x.employer} for x in domain.identities().values()
                           if x.role == "reviewer" and x.employer == identity.employer],
            })
        return result


def assign(identity, case_id, request: AssignmentInput):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        row = domain.load(db, identity, case_id, True)
        domain.check_version(row, request.version)
        if row["decision"]:
            domain.fail(409, "DECIDED_CASE_IMMUTABLE")
        owner = domain.identities().get(request.owner)
        if request.owner != "unassigned" and (not owner or owner.role != "reviewer" or owner.employer != identity.employer):
            domain.fail(422, "OWNER_OUTSIDE_REVIEW_TEAM")
        ops = db.execute("SELECT received FROM case_operations WHERE case_id=?", (case_id,)).fetchone()
        target = datetime.fromisoformat(ops["received"]) + timedelta(hours=24 if request.priority == "priority" else 72)
        db.execute("UPDATE case_operations SET owner=?,priority=?,target=? WHERE case_id=?",
                   (request.owner, request.priority, target.isoformat(), case_id))
        db.execute("UPDATE cases SET version=version+1 WHERE id=?", (case_id,))
        audit(db, case_id, identity.id, "routing_updated", secrets.token_hex(12))
    return detail(identity, case_id)


def create_task(identity, case_id, request: TaskInput):
    definition = TASKS[request.kind]
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        domain.load(db, identity, case_id)
        if identity.role != "reviewer" and definition["role"] != identity.role:
            domain.fail(403, "TASK_ROLE_DENIED")
        duplicate = db.execute("SELECT id FROM tasks WHERE case_id=? AND kind=?" +
                               ("" if showcase() else " AND state!='done'"),
                               (case_id, request.kind)).fetchone()
        if duplicate:
            domain.fail(409, "OPEN_TASK_ALREADY_EXISTS")
        timestamp = now()
        due = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        task_id = secrets.token_hex(12)
        db.execute("INSERT INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (task_id, case_id, request.kind, definition["role"], "open", due, 1, timestamp, timestamp, identity.id))
        audit(db, case_id, identity.id, "follow_up_task_created" if definition["role"] == "contact" else "internal_task_created",
              secrets.token_hex(12))
        return task_view(db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())


def update_task(identity, case_id, task_id, request: TaskUpdate):
    with connection() as db:
        db.execute("BEGIN IMMEDIATE")
        domain.load(db, identity, case_id)
        task = db.execute("SELECT * FROM tasks WHERE id=? AND case_id=?", (task_id, case_id)).fetchone()
        if not task or (identity.role != "reviewer" and task["role"] != identity.role):
            domain.fail(403, "TASK_ACCESS_DENIED")
        if task["version"] != request.version:
            domain.fail(409, "STALE_TASK_REFRESH_REQUIRED")
        transitions = {"open": {"in_progress", "done"}, "in_progress": {"open", "done"}, "done": {"open"}}
        if request.state not in transitions[task["state"]]:
            domain.fail(409, "TASK_TRANSITION_NOT_ALLOWED")
        db.execute("UPDATE tasks SET state=?,version=version+1,updated=?,actor=? WHERE id=?",
                   (request.state, now(), identity.id, task_id))
        audit(db, case_id, identity.id, "follow_up_task_updated" if task["role"] == "contact" else "internal_task_updated",
              secrets.token_hex(12))
        return task_view(db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())
