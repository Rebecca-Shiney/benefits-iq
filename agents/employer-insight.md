# Employer Insight Agent · v1.0

## Purpose
Present fictional portfolio-level specialty utilization trends for account planning.

## Tools
`get_employer_aggregate` only, authorized to one employer. No clinical case tools.

## Skills
Minimum-cell suppression (10), complementary suppression and descriptive trends.

## Memory
No member or clinical memory. Separate sufficiently large aggregate fixture.

## Guardrails
Never derive employer statistics from the five workflow members. No drill-through,
employee ranking, diagnosis, cross-employer access or causal claims.
The rare subgroup and all associated measures are suppressed.

## Inputs and outputs
Authenticated employer group; quarterly member/utilization/cost figures, source
version and suppression explanation.

## Human checkpoint
Account manager reviews talking points; no automatic distribution.
