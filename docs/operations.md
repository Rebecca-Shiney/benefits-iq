# Benefits IQ operations guide

[Overview and quickstarts](../README.md) | [Architecture](../README.md#architecture) |
[Detailed deployment plan and receipts](../.azure/deployment-plan.md)

This guide expands the README without changing the deployed profiles. Historical
approval decisions, failed attempts, exact image digests and job execution IDs
remain in the deployment plan, not duplicated here.

## Deployment stages and source handling

[`scripts/deploy.py`](../scripts/deploy.py) is the staged Azure CLI/Bicep entry.
The README contains the exact preflight/full commands. `--phase foundation
--deploy` stops after the minimal identity/image proof, before data/app services.
There is no `azure.yaml`, `azd up` integration or hidden hand-seeding step.

The full path is: ownership/state lock -> owned resource API audience ->
foundation -> API image tests/scan -> exact MI proof -> web image tests/scan ->
data/private network -> private SQL login -> synthetic seed -> runtime
SQL/Search/fresh OCR proof -> private applications/model acceptance -> public
frontend -> repeated acceptance. ARM success or `/health` is not acceptance.

Preflight checks the signed-in interactive deployer, compiles all templates,
reads ancestor-inclusive ARM policy assignments/nested initiatives and requires
unconditional private-only SQL with no firewall rule. Denied, partial or malformed
policy discovery fails explicitly; this is not a general evaluator of arbitrary
policy conditions/overrides/exemptions or a quota/readiness certificate.
Each ARM create must have successful Provider validation/what-if and no Delete
change. Missing permission never means that a service/capacity is absent.

Build context is committed, allowlisted source, including named versioned agent
definitions. Symlinks, uncommitted inputs, missing required files, attachments,
databases, `.env`, CLI caches and `.azure` artifacts are excluded or rejected.
No original uploaded document is needed to generate synthetic PDFs.

Standard ACR managed builds use the planned Basic registry. Canadian worker
execution is unverified; the accepted source/image-only exception is not
permission for non-Canadian workload data/inference. Strict build residency
requires an approved local builder or supported region-pinned build service with
separate setup/cost approval. Dedicated ACR pools require Premium and have preview
region limits; they are not provisioned automatically.

The scanner downloads its public vulnerability DB before obtaining an ephemeral
registry token through the deployer's Azure CLI session. The token exists only
in the scanner environment, never command arguments/files/state receipts.
All secret matches and known language-package vulnerabilities block acceptance;
the OS threshold is High/Critical, not zero OS advisories. Final-image results
must identify the exact digest and include OS/language results. Non-root runtime
imports/ODBC are tested; unused pip/setuptools were removed rather than ignored.

## Security and runtime limits

### Visitor views versus service identity

Public showcase is `BENEFITS_PROFILE=showcase`. Its unsigned, allowlisted persona
cookie is a **view preference, not a credential**. Backend selected-view/case/
employer checks and response shaping remain enforced, but anyone may select any
enabled view. Human demo actions are anonymous, not verified clinical acts.

Next.js builds the backend request; browser authorization/runtime-token headers
are not trusted or forwarded. Python independently verifies the signed app-only
token's exact tenant, issuer, audience, lifetime, `idtyp=app`, absent `scp`, web MI
client (`azp`) and distinct principal (`oid`). The owned API audience registration
is for service tokens, not visitor sign-in. Setup/runtime resource permissions
remain distinct. Non-secret endpoints and IDs are configuration, not secrets.

No persisted application key/client secret, registry-admin credential or local
demo HMAC fallback is used by showcase. Interactive deployer authentication and
short-lived CLI token caches are different from stored application credentials.
The future user-authenticated code uses memory-cached SPA tokens and independent
user/runtime validation; enrollment/bootstrap and live user verification remain
unimplemented, not a feature enabled by sharing this repository.

### Public input, streaming and storage

Only one canonical preset question is forwarded, with server-generated IDs and
no browser-supplied history, tools, context or state. Values/rationales are finite
synthetic options from [`agents/showcase-options.json`](../agents/showcase-options.json)
and built-in form alternatives. Case search accepts built-in case IDs.
Public communications are fixed previews; the save route returns 403.
No uploads, arbitrary fetch/send or new-case endpoints exist.

| Boundary | Limit/behavior |
|---|---|
| Global model allowance | 100 accepted runs per UTC day; 5/minute |
| Global writes | 300 POST attempts per UTC day; 30/minute |
| Per selected view | 120 calls/minute, in process; not verified-person fairness |
| Concurrency | One backend replica/worker, two model slots; excess returns 429 |
| Model loop | Two iterations, three function calls, 45-second best-effort tool budget, no concurrent tools, one invocation per read tool |
| Output | 500 tokens per model call; fixed prompts/instructions and bounded seeded tool results |
| Python body | JSON-only, no compression, 24,000 bytes, 10-second body-read deadline |
| Chat stream | 256 KiB, 2,048 events, 16,000 text characters; bounded frames/message/tool counts |
| Public deadlines | 90 seconds Python; 95 seconds frontend |

Two transaction-locked SQL counter rows persist reservations across restarts and
reset by UTC day/minute without growing counter history. Accepted failed or
cancelled requests consume reservations. Visitors share the budget and can
exhaust it. SDK limits are not a hard aggregate token or financial cap.

The first-party stream reader checks lifecycle/case/run ordering and read-tool
names. It forwards text/sanitized lifecycle metadata, not raw/custom events,
tool arguments/results or state snapshots. Partial replies stay incomplete;
there is no automatic replay/retry, durable stream resume or retained transcript.
Text is escaped React text, not model-generated HTML/Markdown.

SQL/SQLite owns authoritative cases, not AG-UI state. Writes check versions;
exact decision retries are idempotent and changed content with the same key
fails. Decisions are immutable; reopening/amendments need a future governed flow.
Earlier briefs remain available after form edits invalidate the current brief.
Cancellation observed before the commit checkpoint stops pending work, but
cannot undo a commit already begun. Refresh authoritative state before retrying.

One task per case/kind and at most ten briefs/case bound repeated creation.
Duplicate completed tasks cannot be recreated. Anonymous actors are labelled
`anonymous-demo:<view>`, never verified users. No automatic destructive reset,
freeform public rationale/outbox or chat history is persisted. Source gaps,
low-confidence fields and conflicts are not clinical outcomes.

Employer snapshots are separate synthetic portfolio data, with minimum cell 10
and associated-measure suppression. They are not a live feed, DAX query or
statistics inferred from the twelve individual case fixtures. Internal service
targets are 24h priority/72h standard from synthetic receipt, not clinical or
coverage promises; KPI cards reflect selected-group records, not live insurer metrics.

### Regions, networking and telemetry

Workload processing uses Canada East, except Document Intelligence in Canada
Central. The model stays regional Standard `gpt-4.1-mini` `2025-04-14`,
`NoAutoUpgrade`, with migration before the reported April 14, 2027 retirement.
Preflight refuses to deploy that model after the retirement boundary. No
Global/DataZone, alternate-model, SQLite or deterministic-response fallback
pretends to be a working cloud connection.

Inherited policy disabling public SQL is respected. A new VNet-integrated
Consumption environment, SQL private endpoint and private DNS were approved
because the old environment cannot change network type. The original environment
and existing resources remain; no exemption/public-SQL reenablement or NSP was
used. DNS must resolve only within the approved endpoint subnet, followed by
TLS-verified ODBC MI login before seeding and independent runtime-source proof.
The SQL contained identity uses the MI client-ID SID form, verified by real login.

Private DNS and Entra identity/control-plane services are nonregional boundaries,
not blanket Canadian processing guarantees. Other data-service public endpoints
have local/key auth disabled and scoped MI authorization; this is not an
all-private-endpoint architecture.

Only sanitized server console/system metadata goes to Canada East Log Analytics:
30-day retention, 0.1-GB/day ingestion allowance, no browser/health-payload tracing
or separately deployed Application Insights. Error codes/trace IDs remain
observable without raw provider errors, prompts, tokens or tool payloads.

## Upgrades, recovery and cleanup

1. Preserve `.azure/showcase-<environment>.json`, ownership tags and the original
   dedicated resource inventory. Recover existing state; never discard it, clear
   a live lock or choose a new environment merely to evade a failed deployment.
2. Commit reviewed application changes, validate them and rerun the same deployment
   command/environment. Check any prior process/ARM/job execution before clearing
   a genuinely stale specific lock. Never start competing deployers.
3. Expect downtime: the orchestrator first makes an existing frontend internal
   while revalidating dependencies. Source/index version/hash drift fails rather
   than overwriting evidence; case reseeding preserves decisions/edits/audit.
   Fresh source probes do not mutate cases. Acceptance skips workflow writes when
   evidence or a human decision already exists.
4. Inspect the reported phase/execution on failure. Public acceptance failure
   attempts to restore private ingress. Paid resources can remain allocated;
   no automatic cleanup or rollback of committed human decisions is promised.

Same-environment recovery/rerun passed live. A later upgrade from an already
public release and deliberately injected rollback failures were not separately
exercised live. The setup identity retains SQL bootstrap administration/scoped
Search administration for explicit manual maintenance; it is not serving ingress
and is not silently claimed revoked. Jobs have no schedule or automatic retry.
This is not production privileged-access management, migrations or backup tooling.

**Cleanup requires separate destructive-action approval.** Inventory only the
recorded dedicated group; for example, after recovering the state:

```powershell
$subscription = "<approved-subscription-guid>"
$resourceGroup = "<dedicated-group-from-retained-state>"
az resource list --resource-group $resourceGroup --subscription $subscription --output table
```

Compare every resource/tag and the owned API registration with the state, agree
on export/retention of synthetic audit records and obtain approval for that exact
inventory. An authorized operator can then remove only the approved dedicated
resources/registration. Do not manually delete the platform-managed `ME_vnet_...`
group or broad directories. Never delete/resize/resume/pause shared capacity
(including `dbtdemo` F2), alter other workspaces or assume GitHub sharing grants
application access. No deletion or successful cleanup test is implied here.

## Local development

The **Get to know your dashboard** button starts an optional, role-specific
walkthrough. Use Next/Back or the arrow keys, Escape/Close/Skip to leave, and the
same button to restart. It skips unavailable sections and closes if the case,
workspace, operations view or manually selected tab changes. Reviewer walkthroughs
visit form/source/evidence/decision tabs without running or submitting anything;
contact and employer steps never include reviewer-only panels. The native modal
keeps keyboard focus in the guide, returns it to the button on close, uses instant
scrolling (including reduced-motion use) and adapts to narrow screens. Closing
restores the initial tab unless the dashboard context changed. No tour progress,
case edits, model requests or audit records are saved.

See the README for dependency installation and the loopback launcher. It uses
SQLite, a freshly generated shared service credential, signed HTTP-only strict
SameSite demo cookies and disabled telemetry. These are not Entra credentials or
an internet-hardened ingress. Node identity helpers remain server-external rather
than being bundled into the browser.

```powershell
# Alternate ports, or a previously built production-mode LOCAL preview.
.\.venv\Scripts\python scripts\demo.py --web-port 3020 --api-port 8020
npm run build
.\.venv\Scripts\python scripts\demo.py --production
```

These are alternatives, not concurrent commands on the same ports. Stop an
existing preview before replacing `.next`. To use a fresh disposable dataset,
stop the demo and select a **new** path rather than deleting an existing DB:

```powershell
$env:BENEFITS_DB = "data\demo-second-run.db"
.\.venv\Scripts\python scripts\demo.py
```

Back up existing DBs before upgrades. Startup additively seeds missing fixture/
operation/task rows without replacing decisions, verified fields, briefs or
completed tasks; it is not production schema/retention/reopen tooling. Rollback
uses the prior revision against a separately copied DB, not silent decision
rollback. For incidents, stop the demo and preserve its DB/trace ID locally;
do not export clinical payloads or enable sensitive-data tracing.

The optional legacy `scripts/demo.py --live` path requires explicit
`OPENAI_API_KEY`/`OPENAI_MODEL` configuration and an approved provider/geography.
It is **not** secretless Starter, not the credential-free local default, not an
approved non-Canadian path and never a cloud fallback. Missing credentials fail
explicitly. Live behavior is not proved by the credential-free suite.
For manual local processes, [`.env.example`](../.env.example) lists settings;
the same random 32+-character secret must be server-side in both. Next reads
`.env.local`; uvicorn needs `--env-file`. Never use `NEXT_PUBLIC_` for credentials.
The ephemeral-credential launcher is preferred; do not persist a cloud secret.

### Development checks

```powershell
.\.venv\Scripts\python -m pytest -q
npm run typecheck
node --test tests\request-policy.test.mjs tests\chat-protocol.test.mjs
npm run build
npm audit
npm audit --omit=dev
```

With the launcher already running, a second PowerShell terminal can run actual
two-process checks. Match its printed port:

```powershell
$env:BENEFITS_TEST_URL = "http://127.0.0.1:3000"
.\.venv\Scripts\python -m pytest -q tests\test_http_demo.py
npx playwright install chromium
npm run test:browser
```

The eleven HTTP checks skip without that URL. Browser tests intentionally make
local operational writes on case 006, restore owner/task state and leave audit
events; they never record a clinical decision. Use a disposable DB, a fresh
process or time between suites to respect rate limits. Optional
`BENEFITS_SCREENSHOT_DIR` names an existing capture folder.
Showcase presentation tests use explicitly mocked loopback configuration, not
live MI/cloud proof. Local suites do not call paid services; separate deployment
acceptance jobs do. Point-in-time audits and actual image scans are distinct.
Locks are `package-lock.json` and `requirements.lock.txt`; keep them committed.

Set `BENEFITS_ENABLE_CHAT`, `BENEFITS_ENABLE_INTAKE`,
`BENEFITS_ENABLE_EVIDENCE`, `BENEFITS_ENABLE_RENEWAL`,
`BENEFITS_ENABLE_EMPLOYER` or `BENEFITS_ENABLE_ACTIVITIES` to `0` to disable those
surfaces/APIs. Local warm-start targets (first workflow event <1s, evidence <3s)
are demo targets, not production SLAs or model latency promises.

## CopilotKit reinstatement

Only the optional conversation UI/runtime/AG-UI JavaScript dependency path was
replaced. The operational React/backend dashboard remains intact. Patched direct
Zod 4 remains; the removed CopilotKit/Zod 3 and former body-parser/tarball paths
are not left installed behind unused feature flags. Dependency remediation and
the earlier pytest advisory upgrade are recorded in the deployment plan.

CopilotKit can return after compatible patched versions exist and are validated,
not on a promised date. Require:

- Supported CopilotKit/AG-UI JS versions with no affected transitive Zod path;
  no unsafe cross-major alias/override.
- Fresh locked installation, full/production package audits and final-image scans.
- Verified installed APIs and genuine Python MAF/AG-UI compatibility.
- Equivalent independent caller/case/view checks, body/time/token bounds and
  sanitized stream parsing; no client tools/state allowed to mutate the case.
- Keyboard/accessibility, errors/cancel/retry, privacy/negative-path and live
  backend tests; no retained transcripts, autonomous actions or changed
  operational/decision APIs.

We currently maintain history rendering, composer, focus/live announcements,
limits and stream/protocol recovery rather than taking those conveniences from
CopilotKit. Closing/case/persona change/reload clears chat. No scheduled upstream
monitoring is configured.

## Future Enterprise and collaborator access

Enterprise is planned, not a working switch. Before provisioning, verify Canadian
placement, capacity reuse consent/headroom, Fabric licensing/workspace/OneLake
rights, applicable service-principal tenant settings, semantic-model creation/
query rights and customer policies. Discover suitable capacity and request reuse
first; offer a new F2 only if none is suitable/approved and after cost approval.
Discovery denial/failure is not absence. No shared-capacity changes or extra
tenant-wide consent/settings are authorized by Starter.

Administrators must supply approved label GUID/display names, active/published
status and Lakehouse/SemanticModel applicability, licensing/applying-principal
rights, encryption/export restrictions, and handling/access/retention policy.
Use supported `ApplyOrFail` application plus readback; a GUID alone proves no
right to apply a label. Earlier Graph discovery returned
`403 InsufficientGraphPermissions`; no extra consent was granted. This never
blocks the synthetic showcase, and Azure tags are not Purview labels.

Future Entra enrollment must verify the person's tenant object ID, obtain
explicit role/employer approval and implement the app-role/backend binding.
GitHub access, a name or sharing the repository never performs enrollment.
There is no working onboarding command yet. Real carrier data, Foundry IQ,
live public-program sources, Teams/email sends, healthcare compliance and
production migration/retention/recovery all remain separate, unverified scope.

## Cost assumptions

Allowances are light-use planning estimates, not quotes/caps or actual invoices:

| Component | Monthly US$ allowance |
|---|---|
| Search | 80-120 |
| SQL/storage | 20-220 |
| Apps/setup/build/registry | 20-90 |
| Model/OCR/telemetry/source operations | 20-70 |
| Policy-driven SQL Defender planning line | 15 |
| Original Azure-native subtotal | **155-515** |
| Approved private networking increment | **35-50** |
| Revised light-use total | **190-565**, plus retained environment charges/caveats |

Public Canadian meters checked October 29, 2026: Search Basic
US$0.101/unit-hour (~$73.73/730h); general-purpose Gen5 SQL serverless compute
US$0.62611/vCore-hour. Continuous 0.5/1-vCore equivalents are ~$229/$457 monthly
**before storage/Defender**, with memory-based charging potentially higher.
The SQL allowance assumes effective pauses/light use; polling can prevent pause,
and sustained activity can exceed the total range. No free tier or auto-pause
guarantee is claimed.

Network illustration: two Canada East static IPs at $0.005/h each, standard
load-balancer meter $0.025/h, private-endpoint meter $0.01/h and first DNS zone
$0.50/month total ~$33.35/730h **before processing/queries**. Hence the $35-50
increment, with no NAT, dedicated compute or Premium registry. Old resources
remain allocated. Actual agreement, tax, licenses, storage, traffic and final
meters govern; alerts are not hard spending caps.

No Fabric running charge is created by showcase. Historical F2/Enterprise
allowances in the plan are not verified quotes or permission to resume capacity.
Shared/unrelated workload charges are outside these estimates.

## References

- [Microsoft Agent Framework AG-UI](https://learn.microsoft.com/en-us/agent-framework/integrations/by-component/ui/ag-ui/)
- [AG-UI protocol](https://docs.ag-ui.com/introduction)
- [Optional future CopilotKit integration](https://docs.copilotkit.ai/microsoft-agent-framework)
- [Container Apps network type](https://learn.microsoft.com/en-us/azure/container-apps/networking#virtual-network-type)
- [Managed VNet resources and billing](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks#managed-resources)
- [ACR dedicated agent pools](https://learn.microsoft.com/en-us/azure/container-registry/tasks-agent-pools)
- [Azure Retail Prices API](https://prices.azure.com/api/retail/prices)
