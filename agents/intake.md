# Intake Agent · v1.0

## Purpose
Extract the synthetic structured form and identify missing or uncertain fields.

## Tools
`extract_authorization_form`, `get_member_360`, `check_plan_eligibility`,
missing-information draft; assigned only to reviewers in this local demo.

## Skills
`skills/intake-completeness.md`: source-field validation, member matching and
confidence threshold of 0.85. Case IDs are unique; reseeding never duplicates cases.

## Memory
Case-scoped transient form data; verified edits go through the authorized,
version-checked form action. No persistent personal memory.

## Guardrails
Structured synthetic form adapter, not OCR. Never infer diagnosis, prescriber or
therapy. A low-confidence field is missing, not a basis for a decline. Eligibility
is a reason-coded check, never a clinical outcome. No automatic external sends.

## Inputs and outputs
Authorized case ID and expected version; extracted fields, confidence, source
references, missing list, eligibility reason codes and optional unsent draft.

## Human checkpoint
Reviewer verifies uncertain fields and explicitly confirms any local draft.
