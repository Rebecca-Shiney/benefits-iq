# Benefits IQ

**Better evidence. Human decisions.** An original, synthetic-data special-
authorization and Member 360 demonstration for the October SE Build.

Next.js App Router + TypeScript + CopilotKit presentation/runtime connects to a
separate Python Microsoft Agent Framework service through its genuine AG-UI
adapter. SQLite owns cases, versioned briefs, human decisions, local drafts and
audit history, operational routing and team tasks. Neither chat nor streamed state
can record a clinical decision.

## Run locally (no cloud account or model key needed)

Requirements: Python 3.11+ and Node.js 22+; tested using Python 3.11 and Node 24.
From the repository root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.lock.txt
npm ci --no-fund --no-audit
.\.venv\Scripts\python scripts\demo.py
```

Open the ready URL printed by the launcher (default `http://127.0.0.1:3000`).
The launcher binds **both processes to loopback**, generates an ephemeral shared
service credential, disables tracing/telemetry, verifies readiness and stops its
children when interrupted. Do not expose this identity-switching demo publicly.
If ports are in use, specify `--web-port 3020 --api-port 8020`. No source attachment
is needed at runtime.

**Dependency caveat:** the recorded npm production-dependency scan has no
critical findings after updating Next.js, but still reports 28 high, 5 moderate
and 6 low findings through CopilotKit's transitive dependency graph (39 total).
Some patched versions are unavailable in the configured registry or would require
incompatible major overrides. Do not expose this demo publicly or treat it as
production-ready; re-scan and remediate with upstream-compatible releases before
deployment. Compatible `npm audit fix` was attempted; no forced downgrades or
unsafe cross-major overrides were applied.

For a production-mode *local* preview, first run `npm run build`, then:

```powershell
.\.venv\Scripts\python scripts\demo.py --production
```

The explicit persona switcher creates an eight-hour signed, HTTP-only, strict
SameSite demo cookie. This is **not Entra authentication**. The browser never sees
the runtime-to-service credential. Next.js checks the signed session; the Python
capability layer independently checks role and employer/case access.

## Demonstration path

1. Select **Clinical reviewer / Employer A** and open the workspace.
   Workload cards show actual authorized records, not fabricated live metrics.
   Search by case, fictional member name or member identifier; combine status,
   priority and ownership filters and sort by target, age or priority.
2. Select `SYN-CASE-002` (incomplete). The **Overview** checklist exposes the
   intake gap. Open **Intake**, then run intake. The missing/low-confidence
   prescriber is flagged; an editable doctor-office information draft is prepared,
   not sent. Verify the source field, enter a synthetic value and confirm the
   verified fields. A form edit invalidates any previous brief.
3. Select `SYN-CASE-001` (complete). Run intake, then open **Evidence** and
   prepare evidence. Expand
   citations to inspect original fictional plan, form, claims, criteria and public
   fixture passages with their versions/timestamps.
4. Read the matrix, open **Decision**, choose approve, decline or request more information, enter a
   rationale and explicitly confirm. Record **your** decision. Reload to see the
   durable decision, reviewer identity, evidence version and audit history.
5. Switch to **Contact centre / Employer A**. See only public status and ownership,
   not the clinical fields, claims, criteria or reviewer rationale.
6. Switch to an **Account manager**. See only the authorized employer's separate
   aggregate portfolio; rare cells and associated measures are suppressed.
7. Reviewer A's conflicting case is `SYN-CASE-003`. Reviewer B sees
   `SYN-CASE-004` (renewal within 30 days) and `SYN-CASE-005` (stale criteria).
8. Open case-bound chat. Ask "Check evidence", "Check intake completeness" or
   "Current status". Text and sanitized read-only tool lifecycles stream through
   CopilotKit -> Python's real MAF/AG-UI bridge. Synthetic mode is deterministic,
   clearly labeled, and never claims a model was called.
9. In **Overview**, save a reviewer owner or operational priority. Only the same
   employer's review team is allowed. Record versions and audit events advance;
   clinical outcomes do not change. Decided cases cannot be rerouted.
10. Inspect **Documents** for the actual structured form, plan passage, matching
    criteria version/expiry and claim references. A source gap is not inferred away.
    Human form verification advances the structured form's revision and invalidates
    the current brief; earlier evidence versions remain preserved.
11. Open **Tasks** to create a typed team handoff, start it, complete it or reopen it.
    The **Team tasks** board opens the corresponding authorized case. Contact-centre
    users receive only member-follow-up tasks, not clinical task titles or details.
    Task completion is explicit and independent of intake checks or decisions.
12. In **Status**, run a streaming status check, edit/confirm a local draft and
    inspect **your persona's** saved drafts. No external send occurs. **Activity**
    shows persisted, role-filtered events; reviewers also see the action's actor.

### Operational dashboard semantics

The local dataset has **12 fictional members/cases across two fictional employers**:
Northstar Design Group and Harbour & Pine Co. Original cases 001-005 retain their
guide scenarios; additional cases make queue and handoff work meaningful. Six cases
belong to each group; neither group can search or retrieve the other's records.
Contact-centre queue results contain case IDs and operational status, not member
names, clinical fields, claims or source-gap flags.

All four KPI cards are computed server-side over the entire authorized group,
independently of the current queue filters. Active means not approved/declined;
requests for information remain active. Ready for review means an actual saved
`review_ready` state, not an implied clinical recommendation. Open-task counts
respect task-role visibility. The snapshot time is explicit; **Refresh data**
reloads the durable store. This is not a real-time insurer feed.

Received dates, priorities, intake channels and team ownership are synthetic local
fixtures. Internal service targets are **24 hours for priority / 72 hours for
standard**, measured from receipt. “Past service target” applies only to active
cases; these are neither promised clinical deadlines nor coverage decisions.
Dates are established once and remain durable across restarts. New handoffs have
their own 24-hour task due date; rerouting a case does not silently rewrite tasks.
Tasks are fixed, role-safe templates rather than arbitrary shared clinical notes.
An existing open task of the same kind returns an explicit duplicate error.

The dashboard supplies useful empty, loading and structured error states, native
keyboard-operable controls and a responsive queue. No upload, calendar connector,
provider messaging, payment, integration-health indicator or pretend live trend
is presented as a working feature.

Repeated seeding never overwrites saved case state. To start a fresh disposable
dataset, stop the demo and select a **new** database path:

```powershell
$env:BENEFITS_DB = "data\demo-second-run.db"
.\.venv\Scripts\python scripts\demo.py
```

## What actually runs

| Requirement | Local implementation |
|---|---|
| At least five members / two employers | Twelve original structured synthetic forms, claims and scenarios; two versioned plans and three criteria sets in `service/catalog.py` |
| Operations dashboard | Authorized server-side queue search/filter/sort; ownership, priority, age and synthetic targets; four record-derived KPI cards |
| Case context & source register | Intake completeness, conflict/source-gap visibility, actual fixture passages and revisions; role-safe overview and section navigation |
| Tasks & handoffs | Durable typed team tasks, role-specific visibility, duplicate guard, explicit lifecycle, optimistic versions and metadata-only audit events |
| Intake | Structured fixture extraction, confidence handling, required fields, source navigation, verified edit and member-match guards; **not PDF OCR** |
| Evidence | Cited prior-therapy matrix, versioned briefs, conflicts, source gaps and stale-policy escalation |
| Orchestration | Deterministic intent routing plus bounded specialist capabilities; unsupported intent requires clarification |
| Human decision | Independent authorized endpoint, explicit confirmation, immutable decision, optimistic concurrency and idempotent retries |
| Status | Contact-centre-safe public state, next owner, filtered timeline and editable unsent update |
| Employer | Separate synthetic portfolio, group scope, minimum cell 10, suppression, no clinical drill-through |
| Renewal | Authorized portfolio look-ahead (30/60/90 days) and unsent outreach draft; no automatic extension or scheduled sends |
| Agent definitions | All six versioned agent definitions contain purpose, tools, skills, memory and guardrails; three reusable skill procedures |
| Typed contracts | Pydantic validated forms, member/claims, criteria, eligibility, briefs, decisions and domain activities; Zod activity allowlist on the client |
| Streaming | Real MAF AG-UI text/tool bridge plus versioned workflow SSE activities, cancellation, safe errors and explicit incomplete-run handling |
| Communications | Explicitly confirmed **local outbox only**; no external connector exists |
| Persistence | Transactional SQLite cases, evidence, decisions, routing, tasks, metadata-only audits and actor-scoped confirmed drafts; no chat persistence |

Structured workflow actions deliberately remain separate from free-form chat.
Chat has no case-write, decision, payment, arbitrary URL or external-send tools.
The installed MAF `BaseAgent`/`ResponseStream` protocol is used for deterministic
chat, not a fake endpoint pretending to be a model.
An incomplete intake uses `intake_incomplete`, never a clinical
`information_requested` outcome. Only an explicit human decision records the latter.

## Optional genuine model-backed chat

Only enable this intentionally: model requests may incur charges and transmit
synthetic conversation text to your configured OpenAI service.

```powershell
$env:OPENAI_API_KEY = "<your local secret>"
$env:OPENAI_MODEL = "<an accessible tool-calling model ID>"
.\.venv\Scripts\python scripts\demo.py --live
```

`--live` constructs an actual MAF `Agent` with `OpenAIChatClient`, this repository's
orchestrator instructions and role-restricted, case-bound read-only functions.
Only the selected case is accessible, even if a prompt requests another one.
Missing configuration fails explicitly (`LIVE_MODEL_NOT_CONFIGURED`); unavailable
providers/models fail as errors, never silently fall back to fixtures. Live
provider behavior needs credentials and is **not claimed verified** by the
credential-free test suite.

For manual process deployment, `.env.example` lists server settings. Supply the
same random secret of at least 32 characters to both processes. Next loads
`.env.local`; uvicorn does not unless launched with `--env-file`. Keep keys
server-side, never under `NEXT_PUBLIC_`. The convenience launcher is preferred.

## Validation and API compatibility

```powershell
.\.venv\Scripts\python -m pytest -q
npm run typecheck
npm run build
npm audit --omit=dev
```

For the real two-process session/runtime/stream checks, run the launcher first,
then in a second PowerShell terminal:

```powershell
$env:BENEFITS_TEST_URL = "http://127.0.0.1:3000"
.\.venv\Scripts\python -m pytest -q tests\test_http_demo.py
```

These six HTTP checks are skipped when the URL is unset; the backend suite does
not pretend that an in-process test proves a working Next.js runtime.

For repeatable browser acceptance checks against the running demo:

```powershell
npx playwright install chromium
$env:BENEFITS_TEST_URL = "http://127.0.0.1:3020" # use your launcher's actual port
npm run test:browser
```

These checks use the real UI for filters, sorting, routing, task transitions,
source navigation, role-safe status streaming, renewal navigation, employer
suppression, keyboard interaction and mobile geometry. They intentionally make
local operational writes on case 006, restore its owner/task state, and leave the
corresponding audit history. Use a disposable demo DB for repeatable test runs;
the browser checks never record a clinical decision. Optional
`BENEFITS_SCREENSHOT_DIR` saves desktop/mobile captures in an existing local folder;
otherwise that capture-only check is skipped. No screenshot is fabricated.

Tests exercise the actual installed MAF bridge, all clinical outcomes, role and
employer isolation, public-query privacy, uncertain extraction, claims conflicts,
missing/stale criteria, version conflicts, idempotency, form invalidation, durable
reseed, cancellation, streamed-state rejection, prompt injection as data and
confirmed local drafts, operational filtering/counts, task role privacy,
cross-case task binding, owner validation, stale task writes and additive reseed
preservation. No test calls a paid model or cloud service.

Frontend exact versions are in `package.json`/`package-lock.json`; Python direct
pins are in `requirements.txt` and the full tested resolution is in
`requirements.lock.txt`. Package APIs were checked against installed signatures:
MAF uses `Agent`, `BaseAgent`, `ResponseStream`, `AgentFrameworkAgent` and
`add_agent_framework_fastapi_endpoint`. CopilotKit's runtime/provider exports are
checked by TypeScript/build, not copied blindly from the implementation guide.

## Boundaries and operational notes

- **Authoritative state:** Only explicit capability actions write cases. AG-UI
  state, client tools and forwarded properties are rejected at the bridge.
  Model-bound tools cannot select a different case. No shared clinical threads.
- **Privacy:** Do not use real member, provider, employer or health information.
  Public lookup is an enum-only **fixture**, not web search. No member details
  can be added to its request schema.
- **Streaming:** Work is abandoned when a disconnect is observed before the
  atomic save. Cancellation after a commit cannot undo it. Refresh from the case
  API before retrying. Event IDs are deduplicated; there is no silent replay or
  promise of durable stream resume. Slow consumers naturally backpressure the
  bounded generator. Terminal events are not duplicated.
- **Concurrency:** Every case edit or decision checks the version. An exact
  decision retry returns the saved result; changed content with the same key
  fails. Decisions are immutable; reopening/amendments need a future governed flow.
  Earlier briefs remain available to reviewers via `/api/cases/{id}/briefs`,
  including after a form edit invalidates the current brief.
- **Observability:** Sanitized activity names and trace IDs only. No raw tool
  arguments/results in the workflow stream, no browser payload logging, no health
  payloads in operational logs. Access logging and OTel are disabled by launcher.
- **Limits:** 120 authenticated calls/minute/identity, bounded conversations,
  32 KB application proxy requests and 60-second workflow proxy timeout. The
  loopback demo is not an internet-hardened ingress.
- **Feature gates:** Set `BENEFITS_ENABLE_CHAT`, `BENEFITS_ENABLE_INTAKE`,
  `BENEFITS_ENABLE_EVIDENCE`, `BENEFITS_ENABLE_RENEWAL`,
  `BENEFITS_ENABLE_EMPLOYER` or `BENEFITS_ENABLE_ACTIVITIES` to `0` to disable a
  capability/activity surface. Defaults are enabled; relevant APIs enforce gates.
- **Data:** SQLite files are ignored by Git. Back up the DB before changing a
  running demo version. Startup additively creates operational/task tables and
  missing fixture cases without replacing saved decisions, verified fields,
  evidence history or completed tasks. Only original placeholder member names are
  replaced with fictional display names. This is a local-demo schema upgrade,
  not production migration/reopen/retention tooling.
- **Rollback:** Stop both processes and run the previous Git revision against a
  separately copied database; never silently roll back a recorded human decision.
- **Incident handling:** Stop the demo, preserve the DB locally, identify the
  trace ID, and inspect metadata-only audit history. Do not export clinical
  payloads or enable sensitive-data tracing to troubleshoot.
- **Non-functional targets:** Local demo targets are first workflow event under
  1 second and synthetic evidence completion under 3 seconds after warm startup.
  These are demo targets, not production SLAs or model latency commitments.

### External prerequisites deliberately not implemented as fake integrations

Entra ID and service identity; managed keys; Fabric/OneLake member/claims
connectors; Foundry IQ governed retrieval; live public-program sources; document
OCR; Purview labeling/retention; Teams/email handoffs; approved external
communications; Canadian residency/private connectivity validation; multi-user
production storage, migrations, retention/deletion and recovery operations.
Thread persistence remains disabled until retention/privacy approval.
No Azure resources were provisioned.

The account-manager experience is included, not silently deferred. Renewal is a
bounded extension, not an automatic clinical renewal. A pre-existing fictional
renewal authorization in the seed is not represented as a new agent decision.

## Design decisions

1. **Runtime boundary:** Same-origin Next.js authenticates demo sessions and
   delegates with a server-only credential; the Python service still checks access.
2. **SQLite:** Simple durable local transactions rather than an in-memory demo
   pretending to be an authoritative store. Production storage is separate work.
3. **Controlled UI:** Known components and versioned activities, no generated HTML,
   and a human decision panel outside chat. Evidence states are never outcomes.
4. **No conversational persistence:** Avoid unsupported retention and identity
   assumptions. A stateless runtime runner avoids CopilotKit's default
   process-global thread history, including cross-session list/resume surfaces.
   Source attachments are neither modified nor committed.
5. **No residency claim:** A local demo proves no cloud region, networking,
   carrier compliance or production deployment guarantee.

## Reference documentation

- Microsoft Agent Framework AG-UI:
  https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/
- CopilotKit / Microsoft Agent Framework:
  https://docs.copilotkit.ai/microsoft-agent-framework
- CopilotKit runtime: https://docs.copilotkit.ai/backend/copilot-runtime
- AG-UI protocol: https://docs.ag-ui.com/introduction

Implemented independently from the approved guide's requirements. No code was
copied from SignalWeave or any unlicensed reference repository. The uploaded
Word/PDF documents and their full text are not part of this repository.
