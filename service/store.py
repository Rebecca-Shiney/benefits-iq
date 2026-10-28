import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    path = Path(os.environ.get("BENEFITS_DB", "data/benefits.db"))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
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


def initialize():
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
        """)
        for i, scenario in enumerate(
            ["complete", "incomplete", "conflicting", "renewal", "source-gap"], 1
        ):
            case_id = f"SYN-CASE-{i:03}"
            employer = "SYN-EMP-A" if i <= 3 else "SYN-EMP-B"
            fields = {
                "member_id": {"value": f"SYN-MEMBER-{i:03}", "confidence": 1.0},
                "drug": {"value": "Synthetic Therapy Alpha" if i != 5 else "Synthetic Therapy Beta", "confidence": 0.99},
                "indication": {"value": "Synthetic indication X", "confidence": 0.96},
                "prescriber": {"value": None if i == 2 else "Synthetic Clinic", "confidence": 0.4 if i == 2 else 0.99},
                "prior_therapy": {"value": "none" if i == 3 else "Synthetic prior therapy", "confidence": 0.95},
            }
            for name in fields:
                fields[name]["source"] = f"SYN-FORM-{i:03}#{name}"
            payload = {
                "name": f"Synthetic Member {i:03}", "member_id": f"SYN-MEMBER-{i:03}",
                "plan": "SYN-PLAN-A" if i <= 3 else "SYN-PLAN-B",
                "coverage": "active", "fields": fields,
                "claims": [{"id": f"SYN-CLAIM-{i:03}", "therapy": "Synthetic prior therapy", "date": "2026-09-01", "version": "claims-v1"}],
                "form_source": f"SYN-FORM-{i:03}", "form_version": "form-v1",
            }
            expiry = (date.today() + timedelta(days=21)).isoformat() if i == 4 else None
            db.execute(
                "INSERT OR IGNORE INTO cases VALUES(?,?,?,?,?,1,?,NULL,NULL,?)",
                (case_id, employer, f"SYN-MEMBER-{i:03}", scenario, "received",
                 json.dumps(payload), expiry),
            )
            if not db.execute("SELECT 1 FROM audit WHERE case_id=?", (case_id,)).fetchone():
                audit(db, case_id, "synthetic-seed", "form_received", "seed-v1")
