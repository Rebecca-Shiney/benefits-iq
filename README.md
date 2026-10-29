# Benefits IQ

**Better evidence. Human decisions.** An original, synthetic-data special-
authorization and Member 360 demonstration for the October SE Build.

Next.js App Router + TypeScript with first-party React chat connects to a
separate Python Microsoft Agent Framework service through its genuine AG-UI
adapter. SQLite owns cases, versioned briefs, human decisions, local drafts and
audit history, operational routing and team tasks. Neither chat nor streamed state
can record a clinical decision.

## Accelerator profiles and current status

The approved accelerator now defaults to a **public, credential-free synthetic
showcase** using Azure-native services. An authenticated Starter path is retained
for future integration, and Enterprise integrations remain opt-in/planned. This is a
deliberate change from the original guide: reduce tenant-admin onboarding and
standing capacity cost, improve reuse and one-command setup, and retain core
managed-identity service authentication, constrained demo views, audit and
explicit human-action controls. Anonymous demo views are not authenticated roles.

**Status: Canadian private networking, secretless SQL access, synthetic seeding
and fresh Search/OCR proofs have succeeded. Applications exist privately;
end-to-end acceptance is still in progress. No public application URL exists.**
Both runtime images passed exact-digest scans, and real managed-identity caller
validation passed its positive/four-negative proof. SQL/database, Search,
Document Intelligence and the approved regional model deployment now exist.
The approved VNet-integrated environment, SQL private endpoint and DNS now exist.
Actual probes verified private-only SQL resolution, managed-identity login,
runtime permission boundaries, source documents, governed Search and fresh OCR.
The first private application acceptance stopped on its incorrect expectation
of 404 rather than the API's correct 405 rejection of case creation; that test
contract is corrected, not a bypass of the denial. Real model/streaming, remaining
view/negative checks and browser/public acceptance are not yet claimed complete.
Existing resources incur charges while held privately.
The working loopback demo below is unchanged in scope. `scripts/deploy.py` now
implements the staged cloud entry point; **its full Azure execution is not yet verified**.
No cloud URL, fabricated
integration success or healthcare-compliance claim is supplied.

| Profile | Intended scope | Current implementation status |
|---|---|---|
| Local demo | Credential-free synthetic workflow, SQLite, deterministic MAF/AG-UI and explicit demo personas | Working local application; not Entra or cloud services |
| Showcase (default cloud) | Public selectable synthetic views; real Next.js/Python, regional inference, governed Search, OCR and durable Azure SQL; exact managed-identity backend caller | Anonymous views, finite-input restrictions, signed caller validation and persistent budgets implemented/tested locally; IaC/bootstrap and live cloud proof remain unfinished |
| Authenticated Starter (future opt-in) | Entra user roles/employer bindings plus managed-identity service calling | Retained signed-token/MSAL implementation and local tests; user registration/assignments/bootstrap and live verification are not implemented |
| Enterprise (opt-in) | Actual Fabric/OneLake, aggregate-only employer semantic model, Purview and customer-specific policies | Planned integration profile only; not connected or verified |

### Showcase quickstart contract and minimal inputs

The deployment entry is Python + Azure CLI + staged Bicep, **not `azd up`**.
Explicit stages make it possible to prove managed-identity issuance before
creating the more expensive data services, scan actual image digests, and test
private applications before enabling public frontend ingress. This avoids
unimplemented azd hooks or a misleading one-step success claim.

Prerequisites: Python 3.11+, Git, an interactively signed-in Azure CLI with
Bicep and the `containerapp` extension, plus a verified
[Trivy](https://github.com/aquasecurity/trivy/releases) executable. Set
`BENEFITS_TRIVY` to its absolute path if it is not on PATH. The script refuses
uncommitted application/build-context changes. It never uploads the working
directory wholesale: context comes from committed, allowlisted source files,
with no attachments, databases, `.env`, CLI caches or `.azure` artifacts.
Named versioned agent definitions are required build inputs; arbitrary Markdown
notes and uploaded documents are not included.

```powershell
az login
python scripts\deploy.py --subscription <subscription-guid> --environment benefits-iq
# After approved scope and successful azure-validate / azure-deploy handoff:
python scripts\deploy.py --subscription <subscription-guid> --environment benefits-iq --deploy
```

The default command performs read-only Azure context checks, local compilation
and build-input checks. It now reads ancestor-inclusive ARM policy assignments
and nested initiatives, failing closed on incomplete/denied discovery before
another build or paid write. The compiled SQL template must unconditionally
disable public access and contain no firewall rules; the approved private
topology is compatible with the discovered SQL modifier. This conservative
gate does not evaluate arbitrary
policy conditions, overrides or exemptions. **It is not a quota/policy or live-service acceptance
certificate**. The execution path creates/adopts only its recorded, tagged
environment, configures the owned resource audience, provisions the minimal
foundation, builds/scans the API, proves exact MI claims, creates data services,
seeds SQL/Search, verifies runtime SQL permissions/Search/fresh OCR, and tests
private apps/model streams before public exposure. No hidden hand-seeding or
source attachment is required. ARM success or `/health` alone is not acceptance.

**Resolved topology blocker:** inherited management-group assignment
`MCAPSGovDeployPolicies` applies `AzureSQL_PublicNetwork_Modify`, which changed
SQL public network access to `Disabled`. The Azure-services firewall rule then
failed with `DenyPublicEndpointEnabled`, despite successful Provider validation
and what-if. Earlier subscription/RG-only policy listings did not reveal the
inherited assignment; those listings were incomplete evidence, not policy clearance.
SQL remains Entra-only. No policy exemption, exclusion tag or public-network
reenablement is attempted. Do not discard saved state or retry the old public-SQL
template. The user subsequently approved compliant private connectivity.

The **user-approved and provisioned**, compliant revision adds a
Canadian VNet, delegated app subnet, separate SQL endpoint subnet, SQL private
endpoint/private DNS and a new VNet-integrated Consumption environment.
[The existing environment cannot change network type](https://learn.microsoft.com/en-us/azure/container-apps/networking#virtual-network-type);
it and the existing data services would be preserved, not deleted or duplicated.
The approved additional network planning allowance is US$35-US$50/month; see costs below.
SQL Network Security Perimeter support is documented
[preview](https://learn.microsoft.com/en-us/azure/azure-sql/database/network-security-perimeter?view=azuresql),
not a verified alternate connection. No NSP is provisioned.

**User-approved build-plane exception:** standard ACR managed builds are used
with the planned Basic registry because this host has no Docker, Podman,
BuildKit or installed WSL. This is simpler and avoids an additional regional
builder's setup and cost. **Canadian execution of the standard build workers
is unverified**; this does not establish that foreign execution occurs. The
exception covers application source/images only, never secrets, real health
data, uploaded documents, application-data processing or model inference.
Strict build-residency alternatives are an approved local builder or a supported
region-pinned builder with separate setup/cost approval. Microsoft's documented
[dedicated ACR pools](https://learn.microsoft.com/en-us/azure/container-registry/tasks-agent-pools)
require Premium and are preview-region limited, including Canada Central.
They are not automatically provisioned.

Image scanning downloads its public vulnerability database before acquiring a
short-lived registry token through the deployer's existing Azure CLI sign-in.
That token is passed only in the scanner process environment for the exact
registry scan, never a command argument, file or environment-state receipt.
This is not an application client secret or a registry admin password.
All secret matches and known language-package vulnerabilities block acceptance;
the OS-package threshold is High/Critical, not a claim of zero OS advisories.
The API runtime removes unused system/venv pip and setuptools, rather than
ignoring their bundled dependency findings, and verifies imports/ODBC as its
non-root runtime user after removal.

Minimum non-secret inputs are subscription and Canadian resource regions.
Discover tenant/deployer context; generate resource/application IDs and configure
the frontend origin from its actual URL. Showcase needs no end-user registration,
reviewer assignment, login or consent. It still needs an owned backend resource
API registration for the managed-identity audience and app-only token claims,
not an app registration for visitor sign-in. One-time deployer sign-in,
permission to create that registration and scoped Azure role assignments,
and applicable tenant policy
cannot be bypassed by a deployment button. Missing permission must stop setup with
an actionable error, not weaken service authentication or claim that a service is absent.

| What the Azure-native showcase will create/connect | Placement / connection |
|---|---|
| Next.js frontend/runtime, internal Python API and setup job | Canada East Container Apps; only frontend public, Python independently validates the exact managed-identity caller; single backend replica/worker bounds concurrent model runs |
| ACR and separate managed identities | Canada East; admin/key credentials disabled, identity-based image pulls and data access |
| Entra-only Azure SQL | Canada East; authoritative cases/tasks/briefs/decisions/audit plus versioned synthetic source rows, binary intake documents and separate aggregate snapshots |
| Azure AI Search Basic | Canada East; versioned governed criteria populated from synthetic SQL sources, backend-enforced query scope |
| Azure OpenAI model | Canada East regional **Standard**, `gpt-4.1-mini`, version `2025-04-14`; no Global/DataZone fallback |
| Document Intelligence S0 | Canada Central; actual binary document analysis, confidence and source evidence |
| Server-only Azure Monitor / Log Analytics | Canada East; sanitized console/system metadata, 30-day retention and 0.1-GB/day ingestion allowance; no browser/payload tracing or separately deployed Application Insights |

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
| User-approved public anonymous showcase replaces end-user sign-in as the default | Demonstrate each role-specific dashboard without visitor credentials or user-role assignment prerequisites | Anyone can select every view and perform enabled synthetic actions; no verified person, authenticated role isolation or healthcare-compliance claim. Authenticated Starter remains future work |
| Exact managed-identity caller ACL replaces mandatory runtime app-role assignment for showcase | Supported resource-ACL authorization without storing secrets or requiring a user-role grant | One owned resource API registration and actual token/negative-path proof are still required; tenant/issuer/audience/app-only `azp` and principal `oid` remain mandatory |
| Preset chat, form values and rationales; preview-only communications in showcase | Avoid accepting/persisting arbitrary visitor health text or exposing an open-ended model proxy | No freeform assistant conversation, arbitrary form correction or saved outbox in public mode; local/future authenticated paths retain their existing controls |
| Canadian regional legacy model pinned explicitly | Preserve approved Canadian workload processing; avoid silent global inference | Migration must be verified/approved before reported **April 14, 2027** retirement |
| First-party chat/proxy replaces CopilotKit UI/runtime and AG-UI JavaScript client | User-approved removal of vulnerable required Zod 3 paths without an unsafe cross-major override | We maintain the small chat UI/protocol reader; genuine Python MAF/AG-UI remains. CopilotKit can return after compatible patched releases are validated |
| Bounded request/response parsing | Limit malformed/oversized input and sanitize streamed events independently of UI libraries | Limits, cancellation and protocol compatibility remain application responsibilities |
| pytest patched from 9.0.2 to 9.0.3 | Resolve `CVE-2025-71176` / `GHSA-6w46-j5rx-g56g` without a cross-major override | Locked Python dependency audit is clean; this does not replace full built-image/OS scanning |
| Staged Python/Azure CLI/Bicep entry instead of proposed azd hooks | Make identity/image/private-acceptance gates explicit and resumable | We maintain the small deployment orchestrator; no `azd up` support is claimed |
| Standard managed ACR builds, with build-location uncertainty explicitly accepted by the user | No local Linux builder; reduce additional setup and builder cost | Canadian build execution is unverified; this narrow source/image exception does not change Canadian workload-data/inference requirements |
| User-approved private SQL endpoint/DNS and new Canadian VNet-integrated Consumption environment | Respect the inherited policy disabling public SQL; the existing environment cannot change network type | Approximately US$35-US$50/month additional networking; retain old resources, no exemption or public SQL re-enablement. Private DNS is a non-regional infrastructure name-resolution service, not a Canadian data-store guarantee |
| Distroless Node 24 and Azure Linux 3 / Python 3.12 runtime candidates | Remove known High/Critical paths found in the prior Debian runtime candidates without broad vulnerability ignores | Local Python remains 3.11-compatible; actual final images, ODBC/native packages and Python 3.12 behavior still require build/run/scan acceptance |

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

`app/api/chat/route.ts` resolves the selected demo view (or independently
authenticates the user in future authenticated Starter), checks the selected
case through the backend, then forwards a server-built request to the genuine
Python `/ag-ui` or `/ag-ui-live` endpoint. Showcase uses a managed-identity-only
private backend; future authenticated Starter keeps separate user/runtime
Entra validation. `lib/chat-protocol.ts`
validates lifecycle ordering/case/run IDs and allowlisted read-only tool names.
It forwards text and sanitized lifecycle events, never tool arguments/results,
raw/custom events or state snapshots. Requests are bounded to 24,000 bytes;
responses to 256 KiB, 2,048 events and 16,000 text characters, with bounded frames,
tool/message counts and a three-minute server deadline outside showcase.
Showcase uses a 90-second Python run deadline and 95-second frontend deadline.
Disconnected runs are
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

The future authenticated Starter code independently validates signed user and runtime tokens in
Python, validates user tokens again in Next.js, and uses an in-memory MSAL public
client with the installed redirect bridge (`/auth`). Its demo headers are ignored;
missing configuration fails explicitly. Showcase instead validates a signed
app-only token's exact tenant/issuer/audience/lifetime, `idtyp=app`, absent `scp`,
web managed-identity client ID (`azp`) and distinct principal ID (`oid`) in Python.
No browser-supplied authorization or runtime-token header is forwarded.
Azure identity remains a
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
integration evidence**. The SQL schema is in `infra/schema.sql`. Prepared image
definitions are `infra/Dockerfile.web` and `infra/Dockerfile.api`: official
base-image manifests are digest-pinned, runtime users are non-root, and an
allowlisted `.dockerignore` excludes local state, credentials and attachments.
The API image installs Microsoft's official ODBC 18 package (accepting its EULA
at build time), enforces cloud mode/tracing-off and formats library failures
as metadata without raw provider messages or tracebacks. Operational error codes
and traces remain observable.

Docker is unavailable on the current host; approved managed builds are being
used instead. The first complete API image built, but its final-image scan
found vulnerable bundled Python tooling absent from the application lockfile
audit. Removing unused system/venv pip and setuptools resolved those findings:
the replacement API image passed its exact-digest scan and final non-root
SDK/ODBC assertions. The frontend image also passed, and a real private job
verified managed-identity issuance plus four wrong-configuration denials.
Live data/model connections and the application remain acceptance gates.
Candidate distroless Node 24 and Microsoft Azure Linux 3 Python
3.12 base scans alone are **not final-image results**. Full image/package and secret
scanning must precede public exposure; incomplete or wrong-digest scan reports
fail closed.
`infra/foundation.bicep`, `infra/data.bicep`, `infra/job.bicep` and
`infra/hosting.bicep` compile; audience/bootstrap/private-acceptance and runtime
source probes have local tests; live SQL/Search/OCR/model execution remains
outstanding. The private identity-proof job has actual Azure execution evidence.
The source/bootstrap implementation is `service/cloud_seed.py`: it generates
original deterministic synthetic PDFs, inserts version/hash-checked SQL sources
and a separate aggregate snapshot, and creates/seeds a governed Search index.
It refuses source/index drift instead of overwriting evidence; case reseeding
preserves human edits, decisions and audit. `infra/grant-runtime.sql` prepares
read-only source permissions and append-only audit/decision/brief writes, not
broad database reader/writer roles. It uses the documented Azure SQL contained
principal SID form, with the managed identity's **client ID**, avoiding directory
lookup grants. These paths are locally tested, **not executed against Azure SQL
or Search**; live principal/permission and rerun checks remain mandatory.
`service/identity_probe.py` is the prepared first-stage cloud job command
(`python -m service.identity_probe`): it requests a token using only the actual
web managed identity, runs the same signature/claim validator and four negative
checks, and emits no token. Its unit tests use signed synthetic tokens. It has
**not** run in Azure and is not evidence that token issuance works yet.

The user explicitly superseded initial reviewer enrollment with a public
showcase. No initial reviewer or Hira assignment is created or required.
Neither the unexecuted bootstrap nor `/health` liveness is proof of ready
cloud connections. The role-less app-only caller path has signed-token tests,
not live managed-identity issuance proof yet.

**Future collaborator onboarding:** GitHub access and application/clinical
authorization are separate. The public showcase intentionally grants no
verified-person identity: Hira, like anyone with the eventual URL, can select demo
views without enrollment. For a future authenticated deployment, verify the
person's tenant object ID, obtain explicit role/employer approval, assign the
application role and matching backend binding; neither GitHub sharing nor a name
performs that enrollment. No working enrollment command is advertised.

### Public showcase restrictions and shared state

The public profile is `BENEFITS_PROFILE=showcase`, not the loopback launcher's
`local` mode. Its unsigned, allowlisted persona cookie is a view preference,
**not a credential**. Backend response shapes still exclude clinical details
from the contact view and member details from employer aggregates, and constrain
case/employer fixtures for each selected view. Anyone can choose a different
view; these are not privacy boundaries between anonymous visitors.

Both proxy and Python reject non-preset chat; only one canonical user question
is sent, with server-generated IDs and no assistant/history/context/state/tools
from the browser. The three prompts and synthetic rationales are in
`agents/showcase-options.json`. Form corrections are restricted server-side to
original built-in values and finite synthetic alternatives, with source/member
checks. Search accepts only built-in case IDs. Communications are fixed previews;
the save endpoint returns 403 in showcase. There are no upload, arbitrary remote
URL fetch, external send or case-creation endpoints. Direct Python requests also
enforce JSON-only bodies, compression rejection, a 24,000-byte body limit and a
10-second read deadline, independently of Next.js.

Public model quotas are **100 accepted runs/day and 5/minute globally**;
workflow-write quotas are **300 POST attempts/day and 30/minute globally**.
The two fixed SQL counter rows use transaction locks, survive process restarts,
and reset by UTC day/minute without accumulating counter-history rows. Failed or
cancelled accepted requests still consume their reservation. Each selected view
also has a 120-call/minute in-process limit. A single backend replica/worker
permits at most two model runs simultaneously; excess requests return 429.
The installed MAF client uses `max_iterations=2`, `max_function_calls=3`,
45-second best-effort tool-loop budgeting, non-concurrent tools and at most one
invocation per read-only tool. Each model call is limited to 500 output tokens;
inputs are fixed prompts/instructions and bounded seeded case-tool results.
The SDK's loop/function limits are not a hard aggregate token or financial cap.
No automatic retry, transcript retention or unrestricted model proxy is offered.

Visitors share durable state and quotas. Any visitor can exhaust the allowance;
there is no identity-based fairness guarantee. One task per case/kind and at most
ten evidence briefs per case bound repeated creation; completed tasks cannot be
duplicated. Explicit synthetic decisions remain immutable and record actors such
as `anonymous-demo:reviewer-a`, **never a verified user**. A later visitor can see
that a case has already been decided. There is no destructive automatic reset,
new-case endpoint, saved freeform rationale or editable public outbox. Using a
fresh dedicated demo environment is distinct from deleting/resetting existing
records; destructive cleanup still requires approval.

### Security guarantees versus non-guarantees

All cloud paths retain backend-enforced response/case/employer constraints,
explicit human decision actions, durable audit, optimistic version
checks/idempotency and aggregate suppression. Managed identities, Entra data-plane
permissions and short-lived tokens replace application keys/client secrets. No
application secrets belong in `.env`, azd state, repo, images, logs or Key Vault as
a workaround. Non-secret endpoints, public client IDs and approved object-ID
bindings are configuration. In showcase, human actions are anonymous synthetic
actions, not authorized clinical decisions by verified reviewers.

This does **not** mean no credential ever exists: interactive deployer sign-in and
short-lived CLI/azd token caches are unavoidable and distinct from persisted
application credentials. SPA tokens should use memory caching; never expose
service credentials to the browser. Showcase never uses the local HMAC/service
secret, and its selector must not be described as authentication. Neither cloud
profile silently falls back to SQLite, deterministic model responses or fake
service success.

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

Public Canadian meters rechecked on October 29, 2026: Search Basic is
US$0.101/unit-hour (about $73.73 over 730 hours); Gen5 general-purpose SQL
serverless compute is US$0.62611/vCore-hour. Continuous 0.5/1-vCore
equivalents are about $229/$457 monthly **before storage and Defender**;
serverless memory-based billing can also raise the charged compute.
The $20-$220 SQL allowance assumes effective pauses/light use, not a continuous
maximum. Sustained activity can exceed the overall planning range. No free
SQL/search tier, hard spending cap or guaranteed auto-pause is claimed.
Source: [Azure Retail Prices API](https://prices.azure.com/api/retail/prices);
actual agreement/billing meters still govern.

The user explicitly approved the private-SQL revision and additional allowance. Additional
published network meters checked October 29, 2026: two Canada East static public
IPs at $0.005/hour each, global standard load-balancer meter $0.025/hour,
global standard private-endpoint meter $0.01/hour, and first private DNS zone
$0.50/month: approximately **$33.35/730 hours before data processing and queries**.
Allow roughly **US$35-US$50/month extra**, not a quote/cap, and no NAT gateway,
dedicated compute or Premium registry. [Managed VNet resources are separately
billed](https://learn.microsoft.com/en-us/azure/container-apps/custom-virtual-networks#managed-resources),
including ingress/egress IPs and the load balancer. This would raise the original
light-use planning range to roughly US$190-US$565/month, excluding the existing
environment's retained charges and SQL's sustained-activity caveat above.
Do not treat the original US$515 upper allowance as a hard cap or guaranteed cost.

Starter removes the prior $300-$500/month continuous-F2 compute allowance;
it creates no Fabric running charge. Enterprise's historical combined
$455-$1,015/month illustration is not a verified F2 quote and does not authorize
Starter to touch capacity. Shared storage/unrelated workloads are outside these
accelerator estimates. Exact final meters remain to be confirmed.

For reproducible local upgrades, commit dependency manifests/lockfiles, run
`npm ci` and `pip install -r requirements.lock.txt`, then the validation commands
below. Stop a running production preview before replacing its `.next` output.
Cloud upgrades use the same environment/state and deployment command after
committing and validating changes. Preserve `.azure/showcase-<environment>.json`:
it records non-secret ownership IDs, actual image digests and phase receipts.
Do not delete it to evade a failed deployment or create duplicate resources.
A rerun first makes an existing frontend internal: **upgrades intentionally
have downtime** while dependencies are revalidated. Version/hash-checked seeds
preserve human decisions/audit, and source probes perform fresh OCR/Search
without changing cases. Acceptance skips workflow writes when prior evidence
or a human decision exists. Public acceptance failure attempts to return the
frontend to private ingress. No cloud upgrade is claimed verified yet.

Setup uses a distinct, non-serving identity with SQL bootstrap administration
and scoped Search index administration. That privilege is **retained for
explicit manual migrations/seeding**, not silently claimed revoked; runtime
identities have separate constrained SQL/Search permissions. Setup jobs have
no ingress, schedule or automatic retry. This is a demo maintenance tradeoff,
not a production privileged-access-management solution.

The revised SQL template keeps public access Disabled and creates no
Azure-services firewall rule. Setup/API jobs and applications use a separate
VNet-integrated environment, private endpoint and private DNS; the original
default-network environment remains untouched. A read-only setup-identity probe
must resolve the SQL hostname only inside the endpoint subnet and connect using
ODBC managed-identity authentication with certificate validation before seeding.
Control-plane checks also require an Approved SQL endpoint and Entra-only SQL.
Runtime-source proof independently repeats private DNS and constrained SQL
permission checks. These private SQL/source gates have passed live; final
application/model/public acceptance remains incomplete.
Other data-service public endpoints retain disabled local/key auth and scoped
managed-identity authorization; this is not an all-services-private topology.

On failure, inspect the reported phase/execution and recorded dedicated resource
group before rerunning. Paid resources can remain allocated after failure.
An existing deployment lock requires checking the original process, ARM
deployment and running jobs before manually clearing that specific stale file;
never launch a competing deployment or automatically delete resources.

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

These eleven HTTP checks are skipped when the URL is unset; the backend suite does
not pretend that an in-process test proves a working Next.js runtime.

For repeatable browser acceptance checks against the running demo:

Use a freshly started demo process, or wait a minute between back-to-back suites.
The backend's 120-requests-per-identity/minute limit remains enabled; accumulated
requests from earlier checks can correctly produce `RATE_LIMIT_RETRY_LATER`.

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
`tests/browser/showcase.spec.ts` verifies the anonymous presentation, structured
inputs and keyboard/preset/history behavior against a loopback backend with
explicitly mocked profile presentation; it is not managed-identity/cloud proof.
`tests/test_showcase.py` separately exercises signed caller JWTs, direct-route
negative paths, persistent quotas, concurrency/cancellation/timeouts, bounded
growth, anonymous human-action audit and the genuine MAF/AG-UI bridge with a
deterministic test agent instead of claiming a live model call.

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
- **Limits (local):** 120 calls/minute/demo identity, bounded conversations,
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

Live managed-identity issuance/data-plane connectivity, IaC/bootstrap and cloud
acceptance remain unverified. Future Entra end-user enrollment, Fabric/OneLake
member/claims connectors; Foundry IQ governed retrieval; live public-program
sources; Purview labeling/retention; Teams/email handoffs; approved external
communications; Canadian residency/private connectivity validation; multi-user
production storage, migrations, retention/deletion and recovery operations.
Thread persistence remains disabled until retention/privacy approval.
Only the dedicated Canadian foundation and owned API audience have been
created so far; the application and its live data/model integrations are not
deployed or accepted. The foundation can incur registry/telemetry charges while
held and is not automatically deleted.

The account-manager experience is included, not silently deferred. Renewal is a
bounded extension, not an automatic clinical renewal. A pre-existing fictional
renewal authorization in the seed is not represented as a new agent decision.

## Design decisions

1. **Runtime boundary:** Local Next.js uses an ephemeral server-only demo secret;
   showcase selects anonymous views and delegates with its managed identity.
   The private Python service independently validates its caller and view constraints.
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
