import json
from datetime import datetime, timedelta

import pytest

from service.store import connection, initialize
from test_workflow import client, decision_payload, headers, run, view


def workbench(client, query="", user="reviewer-a"):
    response = client.get("/api/workbench" + query, headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()


def detail(client, case="SYN-CASE-001", user="reviewer-a"):
    response = client.get(f"/api/cases/{case}/operations", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()


def test_authorized_counts_aging_targets_and_filters(client):
    a = workbench(client)
    b = workbench(client, user="reviewer-b")
    assert a["summary"]["total"] == b["summary"]["total"] == 6
    assert {c["id"] for c in a["items"]}.isdisjoint(c["id"] for c in b["items"])
    assert a["summary"]["active"] == 6 and a["summary"]["unassigned"] == 2
    assert a["summary"]["overdue"] == 2
    assert a["summary"]["intake_gaps"] == 1 and a["summary"]["conflicts"] == 1
    assert b["summary"]["source_gaps"] == 1
    for c in a["items"]:
        assert c["age_hours"] > 0
        duration = datetime.fromisoformat(c["target"]) - datetime.fromisoformat(c["received"])
        assert duration.total_seconds() == (24 if c["priority"] == "priority" else 72) * 3600
    assert workbench(client, "?search=Jordan")["items"][0]["id"] == "SYN-CASE-002"
    assert not workbench(client, "?search=SYN-CASE-004")["items"]
    assert not workbench(client, "?search=not-a-member")["items"]
    assert len(workbench(client, "?priority=priority")["items"]) == 1
    assert len(workbench(client, "?owner=mine")["items"]) == 4
    assert len(workbench(client, "?owner=unassigned")["items"]) == 2
    assert workbench(client, "?search=absent")["summary"] == a["summary"]


@pytest.mark.parametrize("sort,key,reverse", [
    ("oldest", "received", False), ("newest", "received", True), ("target", "target", False),
])
def test_queue_sort_is_server_applied(client, sort, key, reverse):
    items = workbench(client, "?sort=" + sort)["items"]
    values = [c[key] for c in items]
    assert values == sorted(values, reverse=reverse)


@pytest.mark.parametrize("query", ["?sort=arbitrary", "?owner=reviewer-b", "?priority=urgent", "?state=automatically_approved", "?search=" + "x" * 101])
def test_invalid_filters_explicitly_rejected(client, query):
    assert client.get("/api/workbench" + query, headers=headers()).status_code == 422


def test_workbench_employer_and_contact_privacy(client):
    for user in ("employer-a", "employer-b"):
        assert client.get("/api/workbench", headers=headers(user)).status_code == 403
        assert client.get("/api/cases/SYN-CASE-001/operations", headers=headers(user)).status_code == 403
    contact = workbench(client, user="contact-a")
    serialized = json.dumps(contact)
    for forbidden in ("Avery", "Jordan", "prescriber", "Synthetic Therapy", "SYN-MEMBER", "source_gap", "resolve_evidence"):
        assert forbidden not in serialized
    assert all(t["role"] == "contact" for t in contact["tasks"])
    assert not workbench(client, "?search=Avery", "contact-a")["items"]
    case = detail(client, user="contact-a")
    assert "documents" not in case and "missing_fields" not in case and "owners" not in case
    assert client.get("/api/cases/SYN-CASE-004/operations", headers=headers("contact-a")).status_code == 403


def test_assignment_validated_audited_and_versioned(client):
    url = "/api/cases/SYN-CASE-001/assignment"
    body = {"version": 1, "owner": "unassigned", "priority": "priority"}
    for owner in ("reviewer-b", "contact-a", "employer-a", "unknown"):
        response = client.post(url, headers=headers(), json={**body, "owner": owner})
        assert response.status_code == 422
    assert client.post(url, headers=headers("contact-a"), json=body).status_code == 403
    assert client.post(url, headers=headers("reviewer-b"), json=body).status_code == 403
    assert client.post(url, headers=headers(), json=body).status_code == 200
    assert client.post(url, headers=headers(), json=body).status_code == 409
    case = view(client)
    assert case["version"] == 2 and case["state"] == "received" and case["decision"] is None
    assert case["timeline"][-1]["event"] == "routing_updated"
    ops = detail(client)
    assert ops["owner"] == "unassigned" and ops["priority"] == "priority"
    assert datetime.fromisoformat(ops["target"]) - datetime.fromisoformat(ops["received"]) == timedelta(hours=24)
    initialize()
    assert detail(client)["owner"] == "unassigned"


def test_task_lifecycle_concurrency_and_duplicate_guard(client):
    base = "/api/cases/SYN-CASE-002/tasks"
    response = client.post(base, headers=headers(), json={"kind": "member_follow_up"})
    assert response.status_code == 200
    task = response.json()
    assert client.post(base, headers=headers(), json={"kind": "member_follow_up"}).status_code == 409
    url = base + "/" + task["id"]
    started = client.post(url, headers=headers("contact-a"), json={"version": 1, "state": "in_progress"})
    assert started.status_code == 200 and started.json()["version"] == 2
    assert client.post(url, headers=headers(), json={"version": 1, "state": "done"}).status_code == 409
    done = client.post(url, headers=headers("contact-a"), json={"version": 2, "state": "done"})
    assert done.status_code == 200
    assert view(client, "SYN-CASE-002")["state"] == "received"
    reopened = client.post(url, headers=headers(), json={"version": 3, "state": "open"})
    assert reopened.status_code == 200
    assert client.post(url, headers=headers(), json={"version": 4, "state": "open"}).status_code == 409
    events = view(client, "SYN-CASE-002", "contact-a")["timeline"]
    assert any(e["event"] == "follow_up_task_updated" for e in events)


@pytest.mark.parametrize("kind", ["verify_form", "resolve_evidence", "renewal_review"])
def test_task_role_scope_cannot_be_forged(client, kind):
    base = "/api/cases/SYN-CASE-001/tasks"
    assert client.post(base, headers=headers("contact-a"), json={"kind": kind}).status_code == 403
    assert client.post(base, headers=headers("employer-a"), json={"kind": kind}).status_code == 403
    assert client.post(base, headers=headers("reviewer-b"), json={"kind": kind}).status_code == 403
    response = client.post(base, headers=headers(), json={"kind": kind})
    assert response.status_code == 200
    task = response.json()
    assert client.post(base + "/" + task["id"], headers=headers("contact-a"),
                       json={"version": task["version"], "state": "done"}).status_code == 403
    assert task["id"] not in json.dumps(detail(client, user="contact-a"))


def test_task_case_binding_and_no_arbitrary_notes(client):
    task = detail(client)["tasks"][0]
    assert client.post(f'/api/cases/SYN-CASE-002/tasks/{task["id"]}', headers=headers(),
                       json={"version": task["version"], "state": "done"}).status_code == 403
    assert client.post("/api/cases/SYN-CASE-001/tasks", headers=headers(),
                       json={"kind": "member_follow_up", "note": "Private text"}).status_code == 422
    assert client.post("/api/cases/SYN-CASE-001/tasks", headers=headers(),
                       json={"kind": "approve"}).status_code == 422


def test_sources_and_completeness_match_actual_fixtures(client):
    incomplete = detail(client, "SYN-CASE-002")
    conflict = detail(client, "SYN-CASE-003")
    stale = detail(client, "SYN-CASE-005", "reviewer-b")
    assert incomplete["verified_fields"] == 4 and incomplete["missing_fields"] == ["prescriber"]
    assert conflict["conflict"]
    assert any(d["status"] == "conflict" for d in conflict["documents"])
    assert stale["source_gap"]
    assert next(d for d in stale["documents"] if d["kind"] == "Local criteria fixture")["status"] == "stale"
    case = view(client, "SYN-CASE-002")
    case["member360"]["fields"]["prescriber"].update(value="Fictional verified clinic", confidence=1)
    client.post("/api/cases/SYN-CASE-002/form", headers=headers(),
                json={"version": case["version"], "fields": case["member360"]["fields"]})
    assert detail(client, "SYN-CASE-002")["verified_fields"] == 5
    verified_form = detail(client, "SYN-CASE-002")["documents"][0]
    assert verified_form["version"] == "form-verified-case-v2"
    assert workbench(client)["summary"]["intake_gaps"] == 0


def test_metrics_track_real_case_and_task_changes(client):
    run(client)
    assert len(workbench(client, "?state=review_ready")["items"]) == 1
    assert workbench(client)["summary"]["review_ready"] == 1
    payload = decision_payload(view(client))
    assert client.post("/api/cases/SYN-CASE-001/decision", headers=headers(), json=payload).status_code == 200
    assert workbench(client)["summary"]["active"] == 5
    assert workbench(client)["summary"]["review_ready"] == 0
    assert client.post("/api/cases/SYN-CASE-001/assignment", headers=headers(),
                       json={"version": view(client)["version"], "owner": "reviewer-a", "priority": "standard"}).status_code == 409
    task = detail(client)["tasks"][0]
    assert client.post(f'/api/cases/SYN-CASE-001/tasks/{task["id"]}', headers=headers(),
                       json={"version": task["version"], "state": "done"}).status_code == 200
    assert workbench(client)["summary"]["open_tasks"] == 5
    assert view(client)["decision"]["outcome"] == "approved"


def test_outbox_is_actor_scoped_and_never_sent(client):
    url = "/api/cases/SYN-CASE-001/communication"
    client.post(url, headers=headers(), json={"text": "Reviewer-only draft", "confirmed": True})
    client.post(url, headers=headers("contact-a"), json={"text": "Safe contact draft", "confirmed": True})
    assert [d["text"] for d in detail(client)["outbox"]] == ["Reviewer-only draft"]
    assert [d["text"] for d in detail(client, user="contact-a")["outbox"]] == ["Safe contact draft"]


def test_additive_seed_preserves_tasks_operations_decisions_and_dates(client):
    ops = detail(client)
    task = ops["tasks"][0]
    client.post(f'/api/cases/SYN-CASE-001/tasks/{task["id"]}', headers=headers(),
                json={"version": 1, "state": "done"})
    run(client)
    original = view(client)
    client.post("/api/cases/SYN-CASE-001/decision", headers=headers(), json=decision_payload(original))
    decision = view(client)["decision"]
    initialize()
    after = detail(client)
    assert after["received"] == ops["received"] and after["target"] == ops["target"]
    assert after["tasks"][0]["state"] == "done"
    assert view(client)["decision"] == decision
    with connection() as db:
        assert db.execute("SELECT count(*) FROM cases").fetchone()[0] == 12
        assert db.execute("SELECT count(*) FROM tasks").fetchone()[0] == 12
    for item in workbench(client)["items"]:
        timeline = view(client, item["id"])["timeline"]
        assert datetime.fromisoformat(item["received"]) <= datetime.fromisoformat(timeline[0]["created"])


def test_upgrade_from_original_five_case_database_preserves_verified_content(client):
    run(client)
    original = view(client)
    with connection() as db:
        db.execute("DROP TABLE tasks")
        db.execute("DROP TABLE case_operations")
        db.execute("DELETE FROM audit WHERE case_id>'SYN-CASE-005'")
        db.execute("DELETE FROM cases WHERE id>'SYN-CASE-005'")
        payload = json.loads(db.execute("SELECT payload FROM cases WHERE id='SYN-CASE-001'").fetchone()[0])
        payload["name"] = "Synthetic Member 001"
        payload["fields"]["prescriber"]["value"] = "Previously verified fictional clinic"
        db.execute("UPDATE cases SET payload=? WHERE id='SYN-CASE-001'", (json.dumps(payload),))
    initialize()
    upgraded = view(client)
    assert upgraded["brief"] == original["brief"] and upgraded["version"] == original["version"]
    assert upgraded["member360"]["fields"]["prescriber"]["value"] == "Previously verified fictional clinic"
    assert upgraded["member360"]["name"] == "Avery Morgan (fictional)"
    assert len(workbench(client)["items"]) == 6
    assert detail(client)["tasks"][0]["state"] == "open"
