# Benefits IQ

**Better evidence. Human decisions.** An original, synthetic-data special-
authorization and Member 360 demonstration for the October SE Build.

Next.js App Router + TypeScript with first-party React chat connects to a
separate Python Microsoft Agent Framework service through its genuine AG-UI
adapter. SQLite owns cases, versioned briefs, human decisions, local drafts and
audit history, operational routing and team tasks. Neither chat nor streamed state
can record a clinical decision.

## Accelerator profiles and current status

The approved accelerator now has a **synthetic-only Azure-native Starter**
default and a separate **opt-in Enterprise integration** profile. This is a
deliberate change from the original guide: reduce tenant-admin onboarding and
standing capacity cost, improve reuse and one-command setup, and retain core
authentication, authorization, privacy, audit and human-decision controls.

**Status: cloud implementation is in progress, not deployed or live-verified.**
The working loopback demo below is unchanged in scope. `azd up` is the intended
cloud entry point, **not yet a working quickstart on this branch**: infrastructure,
bootstrap and runtime adapters are still being prepared. No cloud URL, fabricated
integration success or healthcare-compliance claim is supplied.

| Profile | Intended scope | Current implementation status |
|---|---|---|
| Local demo | Credential-free synthetic workflow, SQLite, deterministic MAF/AG-UI and explicit demo personas | Working local application; not Entra or cloud services |
| Starter (default cloud) | Real Next.js/Python services, regional inference, governed Search, OCR and durable Azure SQL with managed identities | Runtime adapters and signed authentication paths implemented locally; IaC/bootstrap and live cloud proof remain unfinished |
| Enterprise (opt-in) | Actual Fabric/OneLake, aggregate-only employer semantic model, Purview and customer-specific policies | Planned integration profile only; not connected or verified |

### Starter quickstart contract and minimal inputs

Keep using the local quickstart below until the cloud entry point is implemented
and validated. The intended Starter sequence is one-time interactive Azure/azd
sign-in, confirmed subscription/Canadian region, then `azd up` from the repository
root. Bootstrap must discover prerequisites with explicit errors, generate and
connect the resources, initialize schema, seed only synthetic records/documents,
populate Search and verify readiness. No hidden hand-seeding or source attachment
is required. An ARM deployment alone will not count as a working accelerator.

Minimum non-secret inputs are subscription, Canadian resource regions and
approved Entra object-ID-to-role/employer bindings. Discover tenant/deployer
context; generate resource/application IDs and configure redirects from the actual
frontend URL rather than asking users to type every endpoint. Initial access is
explicit and default-deny. One-time deployer sign-in, permission to create
registrations and scoped role assignments, and applicable tenant consent policy
cannot be bypassed by a deployment button. Missing permission must stop setup with
an actionable error, not switch to demo identity or claim that a service is absent.

| What Starter will create/connect | Placement / connection |
|---|---|
| Next.js frontend/runtime, internal Python API and setup job | Canada East Container Apps; frontend validates Entra user, backend independently checks user and managed-identity caller |
| ACR and separate managed identities | Canada East; admin/key credentials disabled, identity-based image pulls and data access |
| Entra-only Azure SQL | Canada East; authoritative cases/tasks/briefs/decisions/audit plus versioned synthetic source rows, binary intake documents and separate aggregate snapshots |
| Azure AI Search Basic | Canada East; versioned governed criteria populated from synthetic SQL sources, backend-enforced query scope |
| Azure OpenAI model | Canada East regional **Standard**, `gpt-4.1-mini`, version `2025-04-14`; no Global/DataZone fallback |
| Document Intelligence S0 | Canada Central; actual binary document analysis, confidence and source evidence |
| Server-only Azure Monitor/Application Insights | Canada East; sanitized operational metadata, no browser/health-payload tracing |

Starter **does not** create/resume Fabric capacity, alter existing workspaces,
request Purview Graph permissions, apply labels, create a Fabric semantic model,
send external communications or connect production carrier systems. In particular,
it must not resume or modify the shared `dbtdemo` F2. Its employer view will query
separate SQL aggregate snapshots with suppression, not pretend to run DAX or
OneLake. SQL synthetic source storage uses the already planned service rather
than introducing a new storage account or capacity dependency.

### What changed from the guide, and why

| Changed | Reason | Tradeoff / deferred feature |
|---|---|---|
| Azure-native synthetic SQL sources in Starter instead of mandatory Fabric/OneLake | Reuse planned durable SQL; reduce capacity cost, license/admin setup and onboarding questions | No OneLake/DirectLake integration in Starter; actual Fabric belongs to opt-in Enterprise |
| SQL aggregate snapshots instead of a mandatory employer semantic model | Preserve scoped/suppressed portfolio output without a Fabric dependency | Seeded synthetic snapshot, not a live operational feed or semantic model |
| Purview labels/customer governance move to Enterprise prerequisites | Avoid requiring label discovery/admin permissions for a strictly synthetic demo | No Purview labeling or enterprise-governance/compliance claim in Starter |
| Governed Azure AI Search selected over IQ-branded retrieval | The guide permits a governed search/API alternative; use an explicit, testable service boundary | No claim that Foundry IQ, Work IQ or Web IQ is deployed |
| Public SPA PKCE and managed-identity connections replace deployed demo credentials | No stored application client secret or browser-selected identity trust | Deployer sign-in, app registration rights and real user authorization still required |
| Canadian regional legacy model pinned explicitly | Preserve approved Canadian workload processing; avoid silent global inference | Migration must be verified/approved before reported **April 14, 2027** retirement |
| First-party chat/proxy replaces CopilotKit UI/runtime and AG-UI JavaScript client | User-approved removal of vulnerable required Zod 3 paths without an unsafe cross-major override | We maintain the small chat UI/protocol reader; genuine Python MAF/AG-UI remains. CopilotKit can return after compatible patched releases are validated |
| Bounded request/response parsing | Limit malformed/oversized input and sanitize streamed events independently of UI libraries | Limits, cancellation and protocol compatibility remain application responsibilities |

### Chat replacement and adding CopilotKit back

The user approved this contained replacement after the installed CopilotKit/
AG-UI JavaScript dependency paths could not be remediated compatibly. Those
packages and their unused local-demo paths are **removed**, not hidden behind a
feature flag. The deployable tree retains direct patched Zod `4.6.7`, with no
Zod 3 or forced cross-major alias.

The operational dashboard was **not rebuilt or reduced**: queue/search/filter/
sort, KPIs, ownership/priority/aging, documents, form verification, evidence,
tasks, renewals, employer aggregates, human decisions and audit remain on the
same React/backend paths. Only the optional conversational panel changed.
`components/case-chat.tsx` provides plain, escaped text messages, keyboard-accessible
controls, live status/error announcements, explicit cancel/retry/clear, incomplete
reply labels and in-memory context. Closing chat, changing case/persona or
reloading clears it. No transcript/list/resume endpoint or automatic retry exists.
Attachments, arbitrary frontend actions and autonomous decisions are not added.

`app/api/chat/route.ts` independently authenticates the user, checks the selected
case through the backend, then forwards a server-built request to the genuine
Python `/ag-ui` or `/ag-ui-live` endpoint. Starter keeps separate user/runtime
Entra validation and managed-identity service calling. `lib/chat-protocol.ts`
validates lifecycle ordering/case/run IDs and allowlisted read-only tool names.
It forwards text and sanitized lifecycle events, never tool arguments/results,
raw/custom events or state snapshots. Requests are bounded to 24,000 bytes;
responses to 256 KiB, 2,048 events and 16,000 text characters, with bounded frames,
tool/message counts and a three-minute server deadline. Disconnected runs are
not silently resumed; partial text is never marked complete.

The tradeoff is that we maintain composer/history rendering, stream parsing,
limits, keyboard/focus behavior, cancellation, errors/retries and protocol tests
instead of receiving those conveniences from CopilotKit. Conversation text is
plain React text, not model-generated HTML or Markdown rendering.

**CopilotKit can be added back once a compatible patched upstream stack is
available and validated; no release date is promised.** Reinstatement requires:
compatible supported CopilotKit/AG-UI JavaScript versions with no affected
transitive Zod path; a fresh locked install/full and production audit; verified
installed API/protocol compatibility; equivalent independent authentication,
case/role isolation, bounded/sanitized streams and cancellation; no default
server transcript retention/list/resume; and passing type/build, real HTTP,
keyboard/accessibility and browser workflows. Replacing the two small chat
surfaces must not move human decisions into chat or alter operational APIs.

### Implemented preparation versus deployment

The Starter code now independently validates signed user and runtime tokens in
Python, validates user tokens again in Next.js, and uses an in-memory MSAL public
client with the installed redirect bridge (`/auth`). Deployed-mode demo headers
are ignored; missing configuration fails explicitly. Azure identity remains a
server-external Node dependency so its platform-specific credential helpers are
not bundled by Turbopack.

Actual adapters are implemented for managed-identity Azure SQL transactions,
employer-bound/versioned SQL sources, scoped Azure AI Search, binary-PDF Document
Intelligence extraction/cache and the installed MAF Azure model client. OCR
retains actual confidence/spans, rejects corrupt PDFs and member mismatches, and
never substitutes fixture extraction. Backend-authorized source PDF downloads
and explicit human corrections are supported. SQL aggregate snapshots suppress
small cells; they are not Fabric. Blocking workflow capabilities run off the
event loop; cancellation observed before the commit checkpoint rolls back
pending writes. A commit already begun cannot be undone by closing a stream:
refresh authoritative state.

These are **local implementation and mock/signed-token test results, not cloud
integration evidence**. The SQL schema is in `infra/schema.sql`; a cloud image
must supply ODBC Driver 18. Resource IaC, image build/push, Entra registration and
role bootstrap, SQL principal/schema/seed setup, Search indexing and reproducible
cloud readiness checks are not yet delivered. `azd up` must not be presented as
working, nor `/health` liveness as proof of ready cloud connections.

### Security guarantees versus non-guarantees

Both cloud profiles must retain backend-enforced role/employer/case isolation,
explicit authorized human clinical decisions, durable audit, optimistic version
checks/idempotency and aggregate suppression. Managed identities, Entra data-plane
permissions and short-lived tokens replace application keys/client secrets. No
application secrets belong in `.env`, azd state, repo, images, logs or Key Vault as
a workaround. Non-secret endpoints, public client IDs and approved object-ID
bindings are configuration.

This does **not** mean no credential ever exists: interactive deployer sign-in and
short-lived CLI/azd token caches are unavoidable and distinct from persisted
application credentials. SPA tokens should use memory caching; never expose
service credentials to the browser. Deployed mode must disable demo persona
authentication and must not silently fall back to SQLite or fixtures.

Starter is **synthetic data only**. Do not enter real member/provider/employer or
health information. It is not a healthcare-compliant production system, certified
control framework, private-network-only architecture or substitute for customer
security/governance review. Entra's non-regional identity/control-plane boundary
is the narrow user-approved exception; it does not permit non-Canadian workload
data processing or global model inference.

### Opt-in Enterprise prerequisites

Enterprise integrations are planned, not a working switch. Before implementing
or provisioning them, verify capacity reuse consent/headroom and Canadian
placement, Fabric licensing and workspace/OneLake permissions, applicable
service-principal tenant settings, semantic-model creation/query permissions and
customer policies. Discovery failure is not proof of no suitable capacity.
Discover suitable capacities and ask to reuse first; offer a new F2 only when none
is suitable/approved and after the normal cost/provisioning approval.

An administrator must supply approved label GUID/display name(s), active/published
status and applicability to Lakehouse/SemanticModel, licensing and applying
principal rights, encryption/export restrictions, and handling/access/retention
policy. Apply labels with `ApplyOrFail` and read back the item label; a GUID alone
does not prove application rights. Graph label discovery currently returns
403 `InsufficientGraphPermissions`; no extra consent/settings were granted.
This is **not a Starter prerequisite**. Azure tags are not Purview labels.

### Cost, upgrades and cleanup

The revised Starter planning allowance is approximately **US$155-US$515/month**:
Search $80-$120, SQL/storage $20-$220, apps/setup/build/registry $20-$90,
model/OCR/telemetry/source operations $20-$70, and a separate policy-driven SQL
Defender planning line of $15. These are allowances, **not a quote or cap**;
tax, agreements, licenses, load and private networking can change the total.
SQL probes/connections can prevent auto-pause. Alerts are not hard spending caps.
Model capacity discovery does not reserve inference capacity.

Starter removes the prior $300-$500/month continuous-F2 compute allowance;
it creates no Fabric running charge. Enterprise's historical combined
$455-$1,015/month illustration is not a verified F2 quote and does not authorize
Starter to touch capacity. Shared storage/unrelated workloads are outside these
accelerator estimates. Exact final meters remain to be confirmed.

For reproducible local upgrades, commit dependency manifests/lockfiles, run
`npm ci` and `pip install -r requirements.lock.txt`, then the validation commands
below. Stop a running production preview before replacing its `.next` output.
Cloud upgrades must use versioned migrations and content-hash seeds, preserve
human decisions/audit, retain resource IDs and pass rerun/live checks; no such
cloud upgrade is claimed verified yet.

Cloud cleanup must target only the dedicated accelerator resource group and
recorded app registrations/assignments after explicit destructive-action approval.
Review the resource list and exported/retained synthetic audit requirements first.
No cleanup command is supplied until the actual deployment/ownership inventory
exists. Never delete/resize/resume/pause shared capacity or alter other workspaces,
and never run a broad directory/resource cleanup. Local resets use a new DB path,
not destructive database replacement.

The detailed approval, architecture, current evidence and deployment gates are in
[`.azure/deployment-plan.md`](.azure/deployment-plan.md). That plan is not a cloud
deployment report.

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

**Dependency status:** after the user-approved first-party chat replacement,
both full and production npm audits report **zero known vulnerabilities**.
The installed tree has no CopilotKit, AG-UI JavaScript client or transitive Zod 3.
This removes the previously blocked
[GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5)
path rather than pretending request guards fix it. The former body-parser
dependency and its GitHub tarball override are also no longer required.
Other now-unused runtime overrides were removed. The lockfile remains committed.

An audit is a point-in-time known-advisory check, not a security certification or
cloud verification. No scheduled upstream monitoring is configured. Complete
infrastructure/bootstrap and remaining authorization/permission checks, then
run `azure-validate` before `azure-deploy`; a successful ARM deployment alone
still does not prove a working accelerator.

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
   first-party authenticated proxy -> Python's real MAF/AG-UI bridge. Synthetic mode is deterministic,
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

## Legacy optional local model-backed chat (not Starter authentication)

Only enable this intentionally: model requests may incur charges and transmit
synthetic conversation text to your configured OpenAI service.
This API-key-based local compatibility path is **not** the secretless accelerator,
must not be deployed as a fallback, and has not been approved as a non-Canadian
processing path. Do not run it against an unapproved provider/geography.

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

For manual **local** process deployment, `.env.example` lists server settings. Supply the
same random secret of at least 32 characters to both processes. Next loads
`.env.local`; uvicorn does not unless launched with `--env-file`. Keep keys
server-side, never under `NEXT_PUBLIC_`. The convenience launcher is preferred.

## Validation and API compatibility

```powershell
.\.venv\Scripts\python -m pytest -q
npm run typecheck
node --test tests\request-policy.test.mjs tests\chat-protocol.test.mjs
npm run build
npm audit --omit=dev
```

For the real two-process session/runtime/stream checks, run the launcher first,
then in a second PowerShell terminal:

```powershell
$env:BENEFITS_TEST_URL = "http://127.0.0.1:3000"
.\.venv\Scripts\python -m pytest -q tests\test_http_demo.py
```

These nine HTTP checks are skipped when the URL is unset; the backend suite does
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
`add_agent_framework_fastapi_endpoint`. First-party protocol validation is checked
against the installed Python bridge through real proxy/HTTP/browser workflows.

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
  32,000-byte streamed JSON requests, 1,024-byte demo-session requests,
  compression rejection, a 10-second body-read timeout, bounded JSON collections,
  depth/nodes and 60-second workflow proxy timeout. The
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
   assumptions. First-party chat has no server transcript store or thread
   list/resume surface, and discards incomplete turns from model context.
   Source attachments are neither modified nor committed.
5. **No residency claim:** A local demo proves no cloud region, networking,
   carrier compliance or production deployment guarantee.

## Reference documentation

- Microsoft Agent Framework AG-UI:
  https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/
- CopilotKit / Microsoft Agent Framework (optional future reinstatement reference):
  https://docs.copilotkit.ai/microsoft-agent-framework
- CopilotKit runtime (not installed): https://docs.copilotkit.ai/backend/copilot-runtime
- AG-UI protocol: https://docs.ag-ui.com/introduction

Implemented independently from the approved guide's requirements. No code was
copied from SignalWeave or any unlicensed reference repository. The uploaded
Word/PDF documents and their full text are not part of this repository.
