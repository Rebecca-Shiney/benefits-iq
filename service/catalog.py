"""Original fictional policies for this demo; not clinical guidance."""

PLANS = {
    "SYN-PLAN-A": {
        "version": "plan-a-v1", "as_of": "2026-10-01",
        "covered_drugs": ["Synthetic Therapy Alpha"],
        "passage": "Fictional employer A plan: active members may submit Therapy Alpha for human review.",
    },
    "SYN-PLAN-B": {
        "version": "plan-b-v1", "as_of": "2026-10-01",
        "covered_drugs": ["Synthetic Therapy Alpha", "Synthetic Therapy Beta"],
        "passage": "Fictional employer B plan: Therapy Alpha and Beta require a human special-authorization review.",
    },
}

CRITERIA = {
    ("SYN-PLAN-A", "Synthetic Therapy Alpha", "Synthetic indication X"): {
        "id": "SYN-CRITERIA-ALPHA-A", "version": "criteria-alpha-v1",
        "as_of": "2026-10-01", "valid_until": "2027-10-01",
        "passage": "Active coverage, verified prescriber and documented prior therapy are required for evidence completeness.",
    },
    ("SYN-PLAN-B", "Synthetic Therapy Alpha", "Synthetic indication X"): {
        "id": "SYN-CRITERIA-ALPHA-B", "version": "criteria-alpha-b-v1",
        "as_of": "2026-10-01", "valid_until": "2027-10-01",
        "passage": "Verify employer B coverage, prescriber and prior therapy; renewal requires a new human review.",
    },
    ("SYN-PLAN-B", "Synthetic Therapy Beta", "Synthetic indication X"): {
        "id": "SYN-CRITERIA-BETA-B", "version": "criteria-beta-b-v0",
        "as_of": "2025-01-01", "valid_until": "2025-12-31",
        "passage": "Expired synthetic policy. Never use as current clinical-review criteria.",
    },
}
