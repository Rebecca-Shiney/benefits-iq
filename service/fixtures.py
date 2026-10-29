"""Fictional operational context; no real people, employers or service promises."""

EMPLOYERS = {
    "SYN-EMP-A": {"name": "Northstar Design Group", "plan": "Northstar Enhanced Health", "region": "Ontario"},
    "SYN-EMP-B": {"name": "Harbour & Pine Co.", "plan": "Harbour Extended Health", "region": "British Columbia"},
}
MEMBERS = [
    "Avery Morgan", "Jordan Ellis", "Riley Chen", "Taylor Reed",
    "Cameron Brooks", "Robin Hale", "Casey Rowan", "Quinn Parker",
    "Morgan Lane", "Sydney Blair", "Alex Monroe", "Drew Bennett",
]
SCENARIOS = [
    "complete", "incomplete", "conflicting", "renewal", "source-gap",
    "complete", "incomplete", "complete", "conflicting", "complete", "incomplete", "renewal",
]
RECEIVED_HOURS_AGO = [18, 83, 106, 9, 133, 38, 67, 25, 90, 4, 151, 42]
TASKS = {
    "verify_form": {"title": "Verify incomplete form fields", "role": "reviewer", "team": "Clinical intake"},
    "resolve_evidence": {"title": "Reconcile source evidence", "role": "reviewer", "team": "Clinical review"},
    "member_follow_up": {"title": "Prepare a member follow-up draft", "role": "contact", "team": "Contact centre"},
    "renewal_review": {"title": "Prepare the renewal review", "role": "reviewer", "team": "Clinical review"},
}
