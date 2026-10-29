import json
import logging
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from .fixtures import MEMBERS, RECEIVED_HOURS_AGO, SCENARIOS, TASKS
from .profile import starter
from .cancellation import check_cancelled


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    check_cancelled()
    if starter():
        from .sql_store import connection as sql_connection
        with sql_connection() as db:
            yield db
        return
    path = Path(os.environ.get("BENEFITS_DB", "data/benefits.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        check_cancelled()
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def audit(db, case_id: str, actor: str, event: str, trace: str):
    db.execute(
        "INSERT INTO audit(case_id,actor,event,trace,created) VALUES(?,?,?,?,?)",
        (case_id, actor, event, trace, now()),
    )
    logging.getLogger("benefits").info("Workflow audit staged event=%s trace=%s", event, trace)


def initialize():
    if starter():
        from .sql_store import verify_schema
        verify_schema()
        return
    with connection() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
          id TEXT PRIMARY KEY, employer TEXT NOT NULL, member TEXT NOT NULL,
          scenario TEXT NOT NULL, state TEXT NOT NULL, version INTEGER NOT NULL,
          payload TEXT NOT NULL, brief TEXT, decision TEXT, expiry TEXT
        );
        CREATE TABLE IF NOT EXISTS audit (
          id INTEGER PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
          actor TEXT NOT NULL, event TEXT NOT NULL, trace TEXT NOT NULL, created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS decisions (
          key TEXT PRIMARY KEY, case_id TEXT NOT NULL, actor TEXT NOT NULL,
          fingerprint TEXT NOT NULL, response TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS communications (
          id INTEGER PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
          actor TEXT NOT NULL, text TEXT NOT NULL, created TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS briefs (
          case_id TEXT NOT NULL REFERENCES cases(id), version INTEGER NOT NULL,
          payload TEXT NOT NULL, actor TEXT NOT NULL, created TEXT NOT NULL,
          PRIMARY KEY(case_id,version)
        );
        CREATE TABLE IF NOT EXISTS case_operations (
          case_id TEXT PRIMARY KEY REFERENCES cases(id), received TEXT NOT NULL,
          target TEXT NOT NULL, priority TEXT NOT NULL, owner TEXT NOT NULL,
          channel TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks (
          id TEXT PRIMARY KEY, case_id TEXT NOT NULL REFERENCES cases(id),
          kind TEXT NOT NULL, role TEXT NOT NULL, state TEXT NOT NULL,
          due TEXT NOT NULL, version INTEGER NOT NULL, created TEXT NOT NULL,
          updated TEXT NOT NULL, actor TEXT NOT NULL
        );
        """)
        seed_records(db)


def synthetic_case_records():
    for i, scenario in enumerate(SCENARIOS, 1):
        case_id = f"SYN-CASE-{i:03}"
        employer = "SYN-EMP-A" if i in {1, 2, 3, 6, 8, 10} else "SYN-EMP-B"
        fields = {
            "member_id": {"value": f"SYN-MEMBER-{i:03}", "confidence": 1.0},
            "drug": {"value": "Synthetic Therapy Alpha" if i != 5 else "Synthetic Therapy Beta", "confidence": 0.99},
            "indication": {"value": "Synthetic indication X", "confidence": 0.96},
            "prescriber": {"value": None if scenario == "incomplete" else "Synthetic Clinic", "confidence": 0.4 if scenario == "incomplete" else 0.99},
            "prior_therapy": {"value": "none" if scenario == "conflicting" else "Synthetic prior therapy", "confidence": 0.95},
        }
        for name in fields:
            fields[name]["source"] = f"SYN-FORM-{i:03}#{name}"
        payload = {
            "name": MEMBERS[i - 1] + " (fictional)", "member_id": f"SYN-MEMBER-{i:03}",
            "plan": "SYN-PLAN-A" if employer == "SYN-EMP-A" else "SYN-PLAN-B",
            "coverage": "active", "fields": fields,
            "claims": [{"id": f"SYN-CLAIM-{i:03}", "therapy": "Synthetic prior therapy", "date": "2026-09-01", "version": "claims-v1"}],
            "form_source": f"SYN-FORM-{i:03}", "form_version": "form-v1",
        }
        expiry = (date.today() + timedelta(days=21 if i == 4 else 8)).isoformat() if scenario == "renewal" else None
        yield {"id": case_id, "employer": employer, "member": f"SYN-MEMBER-{i:03}",
               "scenario": scenario, "payload": payload, "expiry": expiry}


def seed_records(db, reviewer_owners=None):
    owners = {"SYN-EMP-A": "reviewer-a", "SYN-EMP-B": "reviewer-b"} if reviewer_owners is None else reviewer_owners
    for i, record in enumerate(synthetic_case_records(), 1):
        case_id, employer, scenario = record["id"], record["employer"], record["scenario"]
        payload, expiry = record["payload"], record["expiry"]
        db.execute(
            "INSERT OR IGNORE INTO cases VALUES(?,?,?,?,?,1,?,NULL,NULL,?)",
            (case_id, employer, f"SYN-MEMBER-{i:03}", scenario, "received", json.dumps(payload), expiry),
        )
        received = datetime.now(timezone.utc) - timedelta(hours=RECEIVED_HOURS_AGO[i - 1])
        first_event = db.execute("SELECT min(created) FROM audit WHERE case_id=?", (case_id,)).fetchone()[0]
        if first_event:
            received = min(received, datetime.fromisoformat(first_event))
        else:
            db.execute("INSERT INTO audit(case_id,actor,event,trace,created) VALUES(?,?,?,?,?)",
                       (case_id, "synthetic-seed", "form_received", "seed-v1", received.isoformat()))
        stored = db.execute("SELECT payload FROM cases WHERE id=?", (case_id,)).fetchone()
        old_payload = json.loads(stored["payload"])
        if old_payload["name"] == f"Synthetic Member {i:03}":
            old_payload["name"] = payload["name"]
            db.execute("UPDATE cases SET payload=? WHERE id=?", (json.dumps(old_payload), case_id))
        priority = "priority" if i in {3, 5, 9} else "standard"
        owner = "unassigned" if i in {2, 5, 10} else owners.get(employer, "unassigned")
        db.execute("INSERT OR IGNORE INTO case_operations VALUES(?,?,?,?,?,?)",
                   (case_id, received.isoformat(), (received + timedelta(hours=24 if priority == "priority" else 72)).isoformat(),
                    priority, owner, "Synthetic fax intake" if i % 2 else "Synthetic portal intake"))
        kind = {"incomplete": "verify_form", "conflicting": "resolve_evidence",
                "source-gap": "resolve_evidence", "renewal": "renewal_review"}.get(scenario, "member_follow_up")
        operation = db.execute("SELECT received,target FROM case_operations WHERE case_id=?", (case_id,)).fetchone()
        db.execute("INSERT OR IGNORE INTO tasks VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (f"seed-{case_id}-{kind}", case_id, kind, TASKS[kind]["role"], "open",
                    operation["target"], 1, operation["received"], operation["received"], "synthetic-seed"))
