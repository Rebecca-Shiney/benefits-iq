# Benefits IQ accelerator deployment plan

## Status and approval boundary

**Validated: Canadian data/private-application phase. Foundation, both image scans and the real managed-identity positive/four-negative proof are complete. Data and both private-hosting templates passed actual-ID provider validation/what-if. No application/data services or public URL are deployed yet. Enterprise governance remains gated.**

The user explicitly superseded end-user sign-in with credential-free selectable
synthetic views, then approved public URL access with abuse restrictions.
Showcase personas are NOT authenticated roles; anyone can select any enabled
view and perform enabled synthetic actions. No reviewer assignment, SPA
registration or user app-role bootstrap is a showcase prerequisite. Keep future
authenticated Starter code isolated and label it not verified live.

The backend remains private and accepts only its exact managed-identity caller,
with signed tenant/issuer/audience/lifetime and app-only caller client/principal
checks. No application secret or demo HMAC sharing in deployed showcase mode.
User data must be limited to original synthetic fixtures. Public writes must be
structured/bounded, with anonymous demo actor provenance, explicit human actions
and idempotency; chat tools remain read-only. No uploads, arbitrary remote URL
retrieval, external sending, arbitrary case creation or stored freeform chat.
Enforce request/model/concurrency/rate budgets server-side, warn against sensitive
input, and retain Canadian regional inference. This supersedes the pending
end-user ACL alternative below; service caller ACL verification remains required.
Stage minimal MI proof before other paid services where feasible. No Fabric or
Purview operations are authorized. Do not equate public personas with privacy,
verified human identity, production security or healthcare compliance.

The user explicitly approved replacing the affected CopilotKit UI/runtime and
AG-UI JavaScript client with a first-party accessible chat and authenticated
bounded streaming proxy to the genuine Python MAF/AG-UI service. This supersedes
the prior mandatory-CopilotKit wait decision. Preserve all existing operational
dashboard behavior and backend trust boundaries. Remove affected installed
paths rather than retaining them as an unused local option. CopilotKit may be
reintroduced after a compatible patched upstream stack and renewed dependency,
protocol, authorization, privacy, accessibility and build/browser validation.
No release date is promised. Continue cloud preparation only after checks pass;
this amendment itself is not evidence that the dependency gate is resolved.

The user approved implementation and paid deployment, including resuming
`dbtdemo` F2 and creating required Entra registrations and least-privilege
assignments where existing permissions allow. The disclosed approximately
USD455-USD1,015/month allowance is neither a cap nor a verified quote.
The user subsequently approved a simpler default Starter profile. This
supersedes the Fabric/Purview prerequisite pause for Starter only. Existing
paid approval covers the previously approved core Azure services. Do not resume
`dbtdemo`, create capacity or change any Fabric workspace for Starter.
Complete remaining prerequisite/quota checks and dependency/authentication
remediation before public exposure. Foundation-only provisioning has occurred;
application/data services and public exposure remain gated.

Approval excludes shared-capacity changes of any kind for Starter, changes to other workspaces,
tenant-wide admin consent/settings, permission bypasses and extra paid scope.
Stop for approval if actual service choices/baseline materially exceed the
allowance. Missing permissions remain explicit blockers.

The original implementation and dashboard revision remain on the existing branch.
Neither source attachment has been changed or committed.

### Current staged deployment preparation

The user explicitly approved standard ACR managed builds for source/images only,
with **Canadian build execution unverified**. This is not permission for
non-Canadian workload data or model processing. Keep the planned Basic registry;
do not add Premium, a preview dedicated pool or a separate builder. The reason is
the absence of Docker/Podman/BuildKit/installed WSL on this host and avoiding
extra builder setup/cost. The README discloses uncertainty rather than asserting
that foreign processing is proven, and describes approved local or separately
approved region-pinned builders as strict-build-residency alternatives.

The selected recipe is **AZCLI + staged Bicep**, through `scripts/deploy.py`,
not the earlier proposed azd hooks. The user allowed a clearly documented single
entry command. Default execution checks Azure context, compiles templates and
checks committed build inputs without Azure writes; it is not a full quota or
service-readiness certificate. Deployment requires the azure-validate ->
azure-deploy workflow and the already approved scope.

Prepared stages: ownership/state lock -> owned resource audience -> minimal
foundation -> immutable API build/complete exact-digest vulnerability and secret
scan -> real MI positive/four-negative proof -> Canadian data services ->
version/hash-preserving SQL/Search setup -> API-MI runtime permission, scoped
Search and fresh OCR proof -> private API/web -> frontend/private-backend and
real-model acceptance -> correctly configured public frontend -> repeat
acceptance, reverting private on failure. Python ingress is never external.
Existing public frontend ingress is retracted before upgrading dependencies;
this intentionally favors safe, explicit downtime over unimplemented blue/green.

Owned API registration configuration is tested locally; Graph writes/actual
owner/default-user rights remain deployment gates, not assumed tenant admin.
No role/consent/credential/owner grant is added to bypass a refusal. Discovery
errors or ownership/configuration collisions stop rather than create fallbacks.
Actual image/receipt association is checked; no substring-only success test.

All four Bicep entry templates compile. Local suite: 249 passed, 11 optional
HTTP tests skipped in the full unit run; those 11 then passed separately against
the existing local preview. Full npm and locked Python audits report no known
vulnerabilities. Candidate distroless Node24 and Azure Linux3/Python3.12 base
scans have no High/Critical findings, but are not final-image acceptance.
The first complete API build passed its Python 3.12 tests/ODBC check, then its
final-image scan blocked on bundled tooling. Removing unused system/venv
pip/setuptools resolved those findings in the replacement API image. Its
exact-digest scan passed; the frontend image and live identity proof have also
passed, as recorded below. Data/private application validation remains next.
The owned API audience and Canadian foundation now exist; no application is
deployed or live-verified. See the execution evidence below.

Azure Monitor/Log Analytics is the actual prepared telemetry surface:
sanitized console/system events, no HTTP/payload categories, no workspace shared
key, 30-day retention and a 0.1-GB/day ingestion allowance (not a hard spend cap).
No separate Application Insights resource/connection is implemented for showcase.
SQL is Entra-only with the Azure-services firewall rule, which permits Azure
origins outside this subscription and is not private networking.

The distinct setup identity retains SQL bootstrap administration and scoped
Search index administration for explicit manual migrations/reruns. This revises
the earlier proposed immediate revocation: runtime identities remain separately
restricted, jobs have no ingress/schedule/automatic retry, and retained setup
privilege is disclosed rather than falsely described as removed. No shared
resource, capacity or workspace is touched; no automatic deletion/reset is added.

### Showcase implementation and earlier local evidence

The explicit `showcase` profile now has anonymous allowlisted view selection,
backend signed app-only caller validation (`idtyp`, absent `scp`, exact tenant,
issuer, API audience, lifetime, distinct web client `azp` and principal `oid`),
fixed-prompt/no-history chat, finite synthetic form/rationale values,
preview-only communications and backend request-body boundaries. Authenticated
Starter remains separate; no HMAC/service secret is used by cloud showcase.

The two fixed SQL quota rows enforce global model reservations (100/day, 5/minute)
and workflow POST reservations (300/day, 30/minute) with transaction locks.
Deploy a single backend replica/worker for its two-stream semaphore. Python
model deadline is 90 seconds; Next is 95 seconds. Installed MAF client
`function_invocation_configuration` limits iterations to 2, functions to 3
(SDK best effort), duration to 45 seconds (SDK best effort), serial tools,
one invocation per tool and 500 output tokens per model call. No hard aggregate
token/spend cap is claimed. Tasks are finite per case/kind, briefs capped at ten
per case, decisions immutable and audit actors explicitly anonymous.

Local evidence: 196 backend tests pass including all 11 real-HTTP checks against a
separately running preview; 21 request/protocol tests pass, production build/typecheck pass,
full npm and locked Python audits report zero vulnerabilities, and 14 browser tests pass with one
optional screenshot check skipped. Showcase browser presentation uses a clearly
mocked cloud-profile response over the local backend; independent signed-token
and direct-route negative tests do not represent live cloud proof. No public
Azure URL or live managed-identity/model/storage connection is claimed.

Read-only subscription recheck confirms the approved subscription/tenant remain
enabled and the deployer has subscription Owner/User Access Administrator
authority. This does not grant tenant-wide Entra consent or prove owned-app
writes. Remaining work includes the resource API registration, phase-gated
infrastructure/bootstrap, remote image build/validation, real MI claim proof,
SQL/Search/OCR/model seeding/read-write acceptance and only then public exposure.
At that earlier local milestone no Azure write had occurred. The later
foundation execution below supersedes this status; no Fabric operation occurred.

### Foundation IaC research and staging

The official AVM pattern index was checked first. Use the supported
`avm/ptn/azd/acr-container-app:0.5.0` pattern for the later hosting resources,
with pre-created user-assigned identities, actual built image references,
insecure ingress disabled and only private ingress until acceptance.
The broad ACA landing-zone pattern would add unrelated networking/compute
scope; use AVM resource modules for the minimal foundation instead:
`avm/res/managed-identity/user-assigned-identity:0.6.0`,
`avm/res/container-registry/registry:0.13.1`,
`avm/res/operational-insights/workspace:0.16.1` and
`avm/res/app/managed-environment:0.16.0`.
Published versions were verified against MCR, not guessed from examples.

The available tool catalog has no Azure documentation/Bicep MCP contributions.
Use primary Microsoft documentation, official AVM sources/MCR metadata and the
installed Bicep compiler for schema checking; do not fabricate MCP validation.
Resource/module telemetry is disabled. Container logs use the supported
`azure-monitor` destination plus diagnostic settings, not a stored workspace
shared key. Explicit console/system categories avoid enabling HTTP/payload
logging. The foundation has no public application, SQL/Search/OCR/model resource,
Fabric operation or visitor app registration. It is not a ready accelerator.

`infra/foundation.bicep` and its AVM resource module compile successfully without
provisioning. `infra/job.bicep` also compiles. It restricts the manual job to the
prepared identity proof or synthetic setup command, a digest-addressed private
`benefits-api` image, one replica/completion, no automatic retry and an existing
managed identity. Fixed showcase/tracing-off settings override caller-supplied
job environment values. The AVM container-job toolkit pattern was inspected
first but introduces Key Vault/image-import/scheduling services outside this
minimal job; use published `avm/res/app/job:0.7.2` instead. Actual job/image
execution and its orchestration remain outstanding. Read-only provider metadata
confirms Canada East support for environments, container apps and jobs; this
is not quota, deployment or application acceptance evidence.

Sources:
- https://azure.github.io/Azure-Verified-Modules/indexes/bicep/bicep-pattern-modules/
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/azd/acr-container-app
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/managed-identity/user-assigned-identity
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/container-registry/registry
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/operational-insights/workspace
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/app/managed-environment
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/ptn/app/container-job-toolkit
- https://github.com/Azure/bicep-registry-modules/tree/main/avm/res/app/job
- https://learn.microsoft.com/en-us/azure/container-apps/log-options
- https://learn.microsoft.com/en-us/azure/azure-resource-manager/management/resource-name-rules

## 1. Goal and requirements

Modernize the existing application into a reusable accelerator whose intended
deployment entry point is `python scripts\deploy.py --subscription <guid> --deploy`.
Deploy actual cloud-backed capabilities,
not the loopback demo with different URLs.

### User-approved profiles and reason for the change

**The public showcase is the default, strictly synthetic-data-only cloud profile.**
Authenticated Starter is retained as a future opt-in path, not deployed or live-verified.
Use the
already planned Azure SQL database for versioned synthetic source records,
binary synthetic intake documents and a separate sufficiently large synthetic
aggregate snapshot, in addition to transactional case/audit storage. Separate
source read permissions/schema from workflow writes. This avoids adding a
storage service, Fabric capacity or label-discovery permission to the minimum
deployment. No healthcare-compliance claim or real health data is permitted.

The showcase must deploy actual Next.js/Python services, regional model inference,
governed Search, Document Intelligence OCR, durable SQL and privacy-safe
server telemetry, using Entra/managed identities with no persisted application
secrets. It retains backend response/employer/case constraints for each freely
selectable anonymous view, explicit synthetic human actions,
concurrency/idempotency and audit controls. Employer output uses authorized
SQL aggregate snapshots and suppression, **not** a Fabric semantic model.
Anonymous view selection is not authenticated role authorization or privacy
between visitors. Initial reviewer enrollment and the pending end-user ACL
investigation are superseded for showcase, not deployment prerequisites.

**Enterprise is an opt-in integration profile, currently planned, not
implemented.** It adds actual Fabric/OneLake sources, a separate employer
semantic model, Purview and customer-specific policies, with explicit licensing,
capacity, tenant-setting and label/application-right checks. It is not a
production-healthcare certification.

The change reduces tenant-admin onboarding and standing capacity cost and
improves reuse/one-command setup without dropping core security. It is an
approved change from the original guide, not an assertion that SQL is OneLake
or that SQL aggregates are a semantic model. The deeper Fabric-specific
discovery and guide mapping below are Enterprise reference material only.

| Starter resource / connection | Region / boundary |
|---|---|
| Public Next.js and internal Python Container Apps, setup job, ACR | Canada East; only frontend public, no visitor sign-in; exact managed-identity caller token required by private Python |
| Entra-only Azure SQL | Canada East; versioned synthetic sources/documents, transactional case/audit, separate aggregate snapshot |
| Azure AI Search Basic | Canada East; governed/versioned criteria, backend-enforced query filters |
| Azure OpenAI | Canada East regional Standard `gpt-4.1-mini` `2025-04-14`; no Global/DataZone fallback |
| Document Intelligence S0 | Canada Central; actual binary OCR with confidence/source evidence |
| Server-only Azure Monitor/Log Analytics | Canada East; sanitized console/system metadata, no browser/payload tracing; no separate Application Insights resource |
| Fabric/Purview/semantic model | Not created, resumed, queried or claimed by Starter |

| Requirement | Proposed treatment / approval state |
|---|---|
| Classification | Internal, synthetic-data accelerator; not a production health-data service |
| Initial scale | Small review team; scale and model limits need confirmation |
| Cost posture | Cost-optimized, consumption where appropriate; no reservations |
| Subscription / tenant | Approved `85489118-9695-41ac-ba0f-e14ba8837c91`; tenant `eec5bf3a-3dfb-4af5-8487-9b189e5aa20f`. Starter core execution is approved subject to readiness/security/permission checks; Enterprise governance remains separate. |
| Azure / Fabric regions | Approved Canada-first topology below. Ask before any non-Canadian application-data processing. |
| Fabric entitlement | Enterprise-only reference. Starter must not resume/change `dbtdemo` or any capacity/workspace. Enterprise reuse still requires applicable governance/access/headroom checks. |
| Human boundary | Only an authorized human may approve, decline or request more information |
| Privacy | Backend role/case/employer checks, aggregate-only employer data, sanitized telemetry |
| Credentials | No persisted application secrets; managed identities and short-lived Entra tokens |
| Identity residency exception | User accepted existing Entra tenant for sign-in/managed identities with its non-regional identity/control-plane boundary; no exception for application-data processing |
| Regional inference choice | User selected Canada East `gpt-4.1-mini` `2025-04-14`, `Standard`, and accepted migration before reported `2027-04-14` retirement; no GlobalStandard fallback |
| Source documents | Approved 24-page PDF informs requirements; no attachment uploads or wholesale copying |

Interactive deployer sign-in and local Azure CLI/azd token caches are unavoidable.
They are distinct from persisted application credentials. Do not promise that
literally no credential exists anywhere.

## 2. Read-only discovery

- Guide pages 3 and 11 distinguish Fabric/OneLake member/plan/claims sources
  from the authoritative transactional case backend. They allow Foundry IQ
  **or a governed search index** for criteria retrieval.
- Guide pages 15-18 and 22 keep Next.js/CopilotKit as mediator to a separate
  Python Microsoft Agent Framework/AG-UI service.
- Pages 12 and 22 require Entra, least privilege and governance controls;
  pages 20-24 require sanitized streaming and authoritative human decisions.
- Existing cloud blockers: shared service secret, HMAC demo sessions/personas,
  SQLite, local source/extraction fixtures and an API-key OpenAI client.
  None may silently remain as a cloud fallback.
- Azure CLI 2.91.0 and azd 1.35.1 are installed. Docker is not on PATH.
  No azd defaults were configured. No credential files or token values were
  inspected or printed.
- One enabled subscription is visible: `ME-MngEnvMCAP179315-shprabhakar-1`,
  ID `85489118-9695-41ac-ba0f-e14ba8837c91`; tenant
  `eec5bf3a-3dfb-4af5-8487-9b189e5aa20f`. The user subsequently selected
  this subscription and authorized target-specific read-only checks only.
- Read-only Fabric capacity discovery found inactive `testingcapacity`
  (F64, Canada Central), `dbtdemo` (F2, Canada East), `legacyapp` and
  `smartmeter` (F64, Canada East), `testingcanadaeast` (F16, Canada East),
  and `fabricapp12` (F16, West US 3). An active West US 3 trial and a
  PPU-reserved listing also exist. Visibility proves neither assignment
  permission nor eligibility. No capacity has been resumed.
- Historical pre-remediation production npm audit reported 42 affected packages:
  30 high, 6 moderate, 6 low, 0 critical. Some transitive paths lack a
  straightforward fix. Remediation, compatibility checks and a new scan
  are required before public exposure; authentication is not a waiver.
- Historical pre-replacement audit: compatible updates and targeted overrides
  first reduced it to 25 high affected entries/two roots, then
  **20 high affected package entries, one root**, transitive Zod 3 constrained
  collections (`GHSA-mrhx-c7xc-m3w5`, affected `<4.6.6`, patched `4.6.6`).
  body-parser `GHSA-27r3-jxmh-p828` is now resolved using its official immutable
  `2.4.0` release tarball, commit
  `b4744d739e1e2e5257f2ddac31eed191aa5152a4`; npm returned 404 for that release
  when checked. Lockfile integrity is retained. No clean-audit claim is made.
  Stable AG-UI `1.0.3` still requires `zod:^3.25.76`; CopilotKit `1.79.1`
  retains affected paths. `2.0.0-next.1` is an older prerelease, not a fix.
  The earlier mandatory-CopilotKit wait decision was superseded by explicit
  user approval of the first-party replacement recorded above. No unsafe
  cross-major override or exposure waiver was used.
  The Next.js JSON boundaries now reject compression, enforce a streamed
  32,000-byte limit independent of Content-Length, bound collection/depth/node
  shape before SDK parsing, and use a smaller demo-session limit. These are
  defense-in-depth controls, not evidence that the advisories are fixed.
- Current post-replacement full and production npm audit: **zero known
  vulnerabilities**. Removed 828 packages, including all installed CopilotKit/
  AG-UI JavaScript/Zod 3 paths, and obsolete runtime overrides. Python MAF/AG-UI
  remains. `components/case-chat.tsx`, `app/api/chat/route.ts` and
  `lib/chat-protocol.ts` replace only the conversational surfaces. Operational
  dashboard APIs/components and human decision controls are preserved.
  Proxy requests reject browser state/tools/system roles; only sanitized
  allowlisted lifecycle/text events are forwarded. Chat is in memory only,
  case-bound, bounded and manually retryable; partial replies remain incomplete.
  The dependency gate can clear after targeted replacement verification, but
  missing deployment artifacts/permissions/live checks still block readiness.
  CopilotKit may return only with compatible patched supported dependencies,
  fresh locked install/audit, installed API validation and equivalent
  authentication/isolation/privacy/cancel/accessibility/build/browser tests.
  No promised release date or scheduled monitoring.

### Historical local preparation milestone, not cloud evidence

Implemented Starter dispatch with no SQLite/demo-identity fallback; independent
Next.js/Python Entra JWT validation; managed-identity runtime caller; public
MSAL in-memory login and actual installed `/auth` redirect bridge. SQL uses
ODBC 18 managed identity, transaction-owned application locks, sanitized
failures and rollback on cancellation observed before commit. No runtime DDL
or seed fallback is introduced.

Actual SQL source/member/plan/aggregate, scoped Search, binary OCR/confidence/
span/cache and MAF Azure client adapters are implemented locally. Source PDF
downloads require reviewer/case authorization, and human corrections supersede
OCR. Async workflow/model capabilities offload blocking I/O; committed
authoritative changes still require refresh after disconnect. Tests use actual
signed JWTs and mocked cloud/ODBC boundaries, not a deployed service.

`infra/schema.sql` is initial idempotent DDL only. Container definitions are now
prepared in `infra/Dockerfile.web` / `infra/Dockerfile.api`, with digest-pinned
official base-image manifests verified through Docker Hub metadata, non-root
runtime users, an allowlisted `.dockerignore` and official ODBC 18 installation.
`service/cloud_entrypoint.py` enforces Starter/tracing-off and formats raw library
logs as sanitized metadata while retaining application error codes/traces.
Formatter/mode guard tests pass, but Docker is absent: image build/run/scanning
is not claimed. Current npm full/production audit remains zero.

The user explicitly approved the verified signed-in deployer object
`6b167e8a-0d5c-467d-9917-bf34e2102fcf` in tenant
`eec5bf3a-3dfb-4af5-8487-9b189e5aa20f` as the initial
`Benefits.Reviewer`, restricted to `SYN-EMP-A`. Everyone else remains denied.
This is an approved application binding, not a grant of Azure/tenant rights.
No Entra role has been assigned yet. Do not enroll Hira now or infer an Entra
identity from a name. Future enrollment needs verified tenant/object identity,
explicit approved role/employer scope and an app-role assignment plus matching
backend binding. GitHub repository access never grants application access.
Provide an idempotent explicit collaborator enrollment command in bootstrap.

`service/cloud_seed.py` now generates original deterministic synthetic PDFs,
version/hash-checked member/plan/criteria sources, a separate aggregate snapshot
and a governed Search index. Source/index discovery errors are not absence;
reruns skip unchanged data and reject version/content/schema collisions rather
than overwrite evidence. It derives pristine sources from original fixtures,
not potentially edited authoritative cases. Case reseeding preserves workflow
history. Eighteen seed tests cover determinism, additive reruns, drift,
partial upload failures, explicit setup mode and separate runtime identity.

`infra/grant-runtime.sql` prepares a separate runtime contained principal using
the managed identity **client ID** and `WITH SID ... TYPE=E`, explicitly documented
for Azure SQL Database in CREATE USER example K:
https://learn.microsoft.com/en-us/sql/t-sql/statements/create-user-transact-sql?view=azuresqldb-current#k-create-a-contained-database-user-from-a-microsoft-entra-principal-without-validation
This resolves the earlier documentary ambiguity, not live verification. It
avoids directory lookup/Directory Readers for this grant path. Source writes,
audit/decision/history rewrites and DDL are denied. Broad generic
`db_datareader`/`db_datawriter` hook examples are not used because they violate
this application's approved immutable-source/append-only boundary.

Bicep/resource templates, Entra/bootstrap/setup-job orchestration,
deployment/rerun diagnostics and live verification are still unfinished.
SQL startup currently requires an initialized schema; setup must
run before application startup, not rely on the runtime to create tables.
Keep this plan out of Ready for Validation until these and replacement validation
are resolved. No app registration/resource/role assignment has been created.

### Historical read-only identity alternatives (superseded for showcase)

The user has no administrator available and requested investigation, not an
authorization change. Tenant policy reports app creation allowed. Active direct
directory roles and complete role-assignable group discovery did not show an
application-role assigner; however, ownership/default user rights are separate,
so absence of a directory role alone is not a definitive failed-write result.
No Graph write was attempted. Existing CLI delegation includes owned-application
updates and app-role assignment scopes; these do not by themselves establish
resource-specific user authority. Token inspection emitted capability booleans
only; no token was displayed or persisted.

The documented candidate is owned single-tenant SPA/API registration, a
preauthorized `access_as_user` scope only for our SPA, and protected default-deny
OID/role/employer bindings. Require independent signed tenant/issuer/audience,
version/lifetime and actor validation in Next/Python. For the backend caller,
require app-only `idtyp=app`, no delegated scope, exact web MI client ID (`azp`)
and principal ID (`oid`); the user token alone is insufficient. Configure API v2
tokens and optional access-token `idtyp`. This would not depend on Graph app-role
assignment; unknown users/callers remain denied by the resource servers.

Tradeoff: app-specific authorization moves from centrally assigned Entra roles
to protected deployment configuration. Assignment-required must be false for
role-less token issuance, which is not the same as granting application access.
No groups/Graph permissions are needed for the initial single-user binding.
Tenant consent/Conditional Access restrictions remain authoritative. Actual
owned-app configuration, delegated sign-in and managed-identity token issuance
have not been proved and cannot be established against nonexistent registrations
and identities with read-only checks. Paid provisioning stays paused pending an
approved, demonstrated bootstrap path. Current authentication code is unchanged.

Primary references:
- ACL and role-less app-only tokens: https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-client-creds-grant-flow#access-control-lists
- Subject/actor and app-only validation: https://learn.microsoft.com/en-us/entra/identity-platform/claims-validation
- Explicit SPA preauthorization: https://learn.microsoft.com/en-us/graph/api/resources/preauthorizedapplication?view=graph-rest-1.0
- Non-admin owned-app update rights: https://learn.microsoft.com/en-us/graph/api/application-update?view=graph-rest-1.0
- `idtyp` claim: https://learn.microsoft.com/en-us/entra/identity-platform/optional-claims-reference
- The user subsequently approved **planning reuse** of existing `dbtdemo` F2.
  ARM confirms it belongs to the selected subscription, resource group
  `testing`, region Canada East, SKU F2, state `Paused`, provisioning state
  `Succeeded`. Its resource ID is
  `/subscriptions/85489118-9695-41ac-ba0f-e14ba8837c91/resourceGroups/testing/providers/Microsoft.Fabric/capacities/dbtdemo`.
  This was initially planning consent. Scoped resumption was subsequently
  approved in the final execution decision, then paused by the governance gate.

### Selected-subscription evidence, 2026-10-28

- Management permission enumeration includes wildcard management actions,
  with no data actions in the returned permission entries. This does not
  prove Entra administrator, Fabric administrator or downstream data access.
- Required App, CognitiveServices, Search, SQL, Fabric and ContainerRegistry
  providers are registered. Microsoft.Quota reports NotRegistered, but
  `az quota list/show` and usage reads for Container Apps nevertheless
  succeeded. Do not register it or infer a blocker from registration alone.
- Provider metadata advertises both Canada Central and Canada East for
  Container Apps environments, Search services and SQL servers. This is
  not proof of every SKU's availability or actual deployable capacity.
- Container Apps environment quota is 50 and usage is 0 in each of Canada
  Central and Canada East; one new environment would make the total 1/50
  in either candidate. CPU/memory, other services and final-region quotas
  remain unvalidated.
- Three visible enforced policy initiatives concern database protection.
  `DataProtectionSecurityCenter` includes definition
  `36d49e87-48c4-4f2e-beed-ba4ed02b71f5`, whose effect is
  `DeployIfNotExists` on `Microsoft.Sql/servers`: enable Azure Defender.
  Include possible Defender for SQL charges in the final estimate and
  verify effective settings; do not disable the policy to meet a budget.
  Resource-group/other effective policies must still be checked after
  the target resource group is determined.

### Model geography and lifecycle restrictions

The subscription's model catalog and quota reads distinguish these options:

| Candidate | Verified catalog/quota evidence | Decision consequence |
|---|---|---|
| Canada Central regional pay-per-token chat | No `Standard` or `DataZoneStandard` chat SKU in the returned catalog, including legacy lifecycle states | Do not promise Canadian-only inference from a Canada Central endpoint |
| Canada East `gpt-4.1-mini`, `2025-04-14`, `Standard` | `Legacy`; quota name `OpenAI.Standard.gpt4.1-mini`, limit 5000 / usage 0, raw unit `Count`; inference/SKU deprecation `2027-04-14` | A geography-based candidate exists, but requires explicit acceptance of lifecycle/migration risk and real capacity/API validation |
| Canada East `gpt-4o`, `2024-11-20`, `Standard` | `Legacy`; quota limit 150 / usage 0, raw unit `Count` | Older alternative, not a recommended reusable-accelerator default |
| `gpt-5.4-mini`, `2026-03-17`, either Canadian region | GA, `GlobalStandard`; quota limit 1000 / usage 10, raw unit `Count` | Modern pay-per-token candidate only if global processing is explicitly acceptable |
| `gpt-5-mini`, `2025-08-07`, Canada East | GA, `GlobalStandard`; quota limit 1000 / usage 0, raw unit `Count` | Another global-processing option; no deployment or price verification yet |

These are live read-only catalog/quota observations, not reservation of model
capacity or successful inference tests. Raw quota `Count` values must not be
misstated as literal tokens/minute without the model-specific unit conversion.
The earlier hyphen-based usage-name filter omitted the actual
`gpt4.1-mini` regional quota name; the exact name above was subsequently
queried and verified.

Microsoft's deployment-type documentation states that `GlobalStandard` may
process in any Azure region. `Standard` processing remains within the selected
Azure geography, potentially across regions in that geography; it does not
guarantee one specific Canadian region. A Canadian resource location alone
is therefore not a Canadian-only inference guarantee. The subsequently approved
Canada-first policy and proposed topology are recorded below; no model is deployed.

### Approved Canada-first topology; readiness not yet validated

The user subsequently selected **Canada-first; ask before any non-Canadian
processing**. Global/DataZone inference is not approved. The prior model
comparisons are discovery only, not permission to use those alternatives.

| Component | Proposed Canadian placement | Evidence / remaining gate |
|---|---|---|
| Next.js, internal Python API and setup job | Canada East | Provider advertises region; environment count 1/50 after deployment. CPU/environment deployment checks remain. |
| Azure OpenAI inference | Canada East, `gpt-4.1-mini` `2025-04-14`, `Standard` only | User selected this regional model and accepted migration before reported `2027-04-14` retirement. Regional capacity API reports `availableCapacity: 5000`; quota limit 5000 / usage 0. No capacity reserved. |
| Case/audit SQL | Canada East, `GP_S_Gen5_1`, min 0.5 / max 1 vCore | Subscription capabilities report Serverless/Available, min 0.5 supported, auto-pause supported. Propose LRS backups for this synthetic POC; no cross-geography replica. Defender policy cost and Entra bootstrap remain. |
| Governed AI Search | Canada East, Basic, one replica/partition | Regional usage API reports Basic usage 0 / limit 12. Generic quota CLI returned no entries, not unlimited quota. Physical service provisioning still untested. |
| Document Intelligence | Canada Central, single-service FormRecognizer S0 | `account list-skus` returns S0 with no listed restrictions in Canada Central, and an empty list in Canada East. Do not promise all services can reside solely in Canada East. |
| ACR, Log Analytics | Canada East resources | Actual provisioning/telemetry still needs validation. Standard managed build execution location is unverified and narrowly user-approved for source/images only. No separate Application Insights is deployed. |
| Enterprise-only Fabric workspace, OneLake and aggregate model | Canada East, historical `dbtdemo` F2 reuse plan | Not part of Starter. Prior governance/headroom/licensing/access gates remain; Starter must not resume or modify capacity/workspaces. |

Model-capacity discovery used the documented location-based capacity endpoint,
not only model-catalog presence. A bounded Windows URL-quoting error was corrected;
the successful authenticated read returned the exact regional model/version/SKU
above. CognitiveServices quota CLI returned BadRequest; documented service
usage/capacity/SKU APIs supplied the successful evidence instead.

This topology keeps the proposed workload data planes in Canada, subject to
their documented service commitments. It is not a guarantee that every
identity/control-plane operation is Canadian. Microsoft Entra is a non-regional
service with geo-located Core Store/authentication components; its documentation
does not offer a Canada-only Core Store location. The existing tenant's actual
placement has not been verified. Obtain explicit user acceptance/clarification
for changes beyond the boundary accepted below.

The user explicitly accepted use of the existing Entra tenant for sign-in and
managed identities while keeping application-data processing in Canadian
regions. This narrowly accepts Entra's non-regional authentication and
identity/control-plane behavior, which cannot be guaranteed to remain in
Canada. It does **not** authorize global model inference, other non-Canadian
application-data processing, new tenant/bootstrap permission changes or paid
deployment. The user subsequently selected the regional legacy model and
accepted migration before its reported retirement, then approved the complete
deployment/bootstrap scope. The later Starter simplification removes the
Fabric/Purview gate for Starter only; other readiness/security/permission checks remain.

The approved inference choice is explicitly `gpt-4.1-mini`, version
`2025-04-14`, `Standard`, Canada East. Keep the model/version/type parameterized
and visible in readiness diagnostics. Fail if that regional choice is unavailable;
do not silently upgrade to a global deployment, change processing geography or
claim a replacement model is approved. Record the reported retirement date
`2027-04-14` and require a separately verified/approved migration beforehand.
Model selection alone did not authorize paid provisioning; the subsequent
execution approval did. Starter retains that core approval without any
Fabric/Purview operation; Enterprise governance remains gated.

Public-reference calls, external telemetry, web/model fallback and any other
outbound processing with unverified geography must remain unavailable until
approved. No non-Canadian inference, workload upload or paid service operation
has been performed; checks to date were read-only management/public-doc queries.

## 3. Components and deployment recipe

| Component | Existing location | Cloud change required |
|---|---|---|
| Next.js App Router, first-party chat/proxy | `app`, `components`, `lib` | Container hosting; Entra SPA login/token validation; secretless backend caller |
| Python MAF/AG-UI and governed APIs | `service` | Internal hosting; independent caller/user checks; real cloud adapters |
| Transactional workflow store | `service/store.py` | Entra-only SQL adapter preserving atomic decisions, idempotency and audit |
| Versioned definitions and synthetic sources | `agents`, `skills`, `service/catalog.py`, `service/fixtures.py` | Starter SQL source/document/aggregate seed and criteria index; Enterprise-only OneLake/model integration |
| Local launcher | `scripts/demo.py` | Preserve explicit local mode; do not treat it as the deployment command |

**Selected recipe:** AZCLI with parameterized, staged Bicep and
`scripts/deploy.py`. No `azure.yaml`/`azd up` support is claimed.
Do not run `azd init -t` over this existing repository. Use standard ACR builds
with the user-approved build-location exception; validate the build
path rather than pretending Docker is installed.

The one-command lifecycle must automate resource wiring, schema setup,
synthetic documents/data and index population. Semantic-model creation is Enterprise-only.
One-time tenant consent, licenses and admin-governed settings cannot honestly
be bypassed by a deployment button. Preflight must name missing prerequisites
and stop before creating paid resources where possible.

Capacity selection is an explicit reusable accelerator behavior: discover
suitable existing capacities first and ask whether they may be reused. If
none is suitable/approved, offer a new F2, subject to normal final cost and
provisioning approval. A discovery/authorization error is not proof that no
capacity exists and must not trigger paid fallback provisioning.

For Starter, create no capacity resource or Fabric workspace and perform no
capacity lifecycle action. The prior Enterprise reuse plan must not be executed
by Starter. Do not resize, delete, redeclare/overwrite, resume, pause or change
the ownership of `dbtdemo`; do not reassign or alter existing workspaces.
Any future Enterprise activation must pass its own governance/owner/headroom
gates. Never automatically pause a shared capacity as accelerator cleanup.

## 4. Enterprise guide-to-service mapping

The selections below describe the **full guide / opt-in Enterprise architecture**,
not default Starter resources or deployed integrations.
Additional tenant-wide settings, consent, non-Canadian processing or paid scope
still require separate approval.

| Guide capability | Classification | Proposed implementation and boundary |
|---|---|---|
| Fabric/OneLake member, plan, coverage and claims sources (pp. 3, 11) | Required core | Actual Fabric workspace/lakehouse containing versioned synthetic sources; authenticated OneLake reads. Ordinary Azure blob storage is not a replacement. |
| Authoritative cases, tasks, decisions, briefs and audit (pp. 3, 11) | Required core; store choice proposed | Entra-only Azure SQL, separate from analytical sources; immutable decisions and atomic audit/idempotency. |
| Foundry IQ or governed criteria search (pp. 3, 11) | Guide-permitted alternative | Azure AI Search with version, effective-date, plan/drug/indication metadata and server-enforced filters; no premium/preview agentic retrieval dependency. |
| Agent reasoning and streaming | Required core | Azure OpenAI with managed identity through the installed MAF OpenAI client; approved Canada East Standard `gpt-4.1-mini` `2025-04-14`, subject to final quota/readiness validation. No global/data-zone fallback. |
| Intake document extraction | Required core | Single-service Document Intelligence with custom subdomain and Entra auth; binary document submission from authorized OneLake reads, not public SAS URLs. Preserve OCR confidence/source spans and human verification. |
| Employer trends (p. 11) | Required core | Real aggregate-only semantic model, separate sufficiently large synthetic aggregate dataset and small-cell suppression. Never derive employer trends from only the 12 workflow members. |
| User and service authentication (pp. 12, 22) | Required core | Entra SPA + PKCE; distinct managed identities, backend authorization and default-deny user/employer mappings. |
| Monitoring/privacy (pp. 12, 22) | Required core | Server-only Azure Monitor/Application Insights with Entra ingestion, local ingestion auth disabled, sanitized events; no browser SDK or health-payload tracing. |
| Purview labels and handling (pp. 12, 22) | Required governance; tenant prerequisite | Verify license, label IDs/policies, item support, admin authority and actual application. Azure tags are not Purview labels. Missing controls block a claim of full guide compliance. |
| Public-program information via approved API or Web IQ (pp. 3, 11) | Guide-permitted alternative | Allowlisted official public-reference/API adapter with no member details in requests. Final approved sources, network behavior and citation freshness must be documented. |
| Work IQ/internal Teams or email (p. 11) | Conditional/manual | Requires relevant authorized tenant context, scopes and consent. Not a mandatory synthetic V1 connection and never a fabricated successful integration. |
| Teams handoff, external sends, production carrier adapters, expanded renewal automation (p. 13) | Extension | Existing internal tasks and renewal navigation stay functional. No automatic external sends, claims-payment actions or production carrier connections are added. |

For employer models, verify the semantic-model definition/import path against
the actual tenant. A candidate is a versioned aggregate-only import generated
from authorized OneLake aggregate input, without an external credential-bearing
data source. This is a seeded snapshot, not a live operational feed.
Do not silently enable DirectLake SSO or model RLS: service-principal
Execute Queries does not support RLS/SSO-enabled models. The governed backend
must enforce employer scope and expose only allowlisted aggregate queries.
Check payload errors/partial results even when Execute Queries returns HTTP 200.
If the proposed model path is unsupported, report the exact blocker before
substituting an API fixture.

## 5. Secretless architecture and least privilege

Browser -> public Next.js Container App -> internal Python Container App ->
authorized Azure data planes. Only Next.js has public application ingress.
Fabric connections in this section apply only to the opt-in Enterprise profile.
The first three identity bullets below describe the **future authenticated
profile**, not anonymous showcase. Showcase trusts no browser credential/role:
it accepts only an allowlisted selected demo view plus an independently signed
exact MI caller, with the constraints recorded above.

- Use supported MSAL authorization-code + PKCE for a public SPA client and
  a tenant-specific API registration. No Entra client secret. Prefer in-memory
  browser token cache; do not implement a custom OAuth protocol.
- Next.js validates user signature, issuer, tenant, audience, scopes and roles.
  It obtains a separate managed-identity service-caller token for Python.
  Python independently validates the caller token and original user access
  token. Strip untrusted forwarded service headers.
- Backend derives role and employer access from approved tenant/object-ID
  mappings. Browser role/employer headers and the demo identity switch are
  not trusted or available in deployed mode.
- Runtime identity: backend invoke permission and registry pull only.
  Backend identity: SQL application permissions, Enterprise-only scoped OneLake reads,
  Search Index Data Reader, model invocation, Document Intelligence analysis
  and sanitized telemetry ingestion. Verify exact built-in/custom roles.
- Setup identity: separate manual schema/seed/index administration. Enterprise-only
  setup additionally requires Fabric item/data-role and semantic-model rights.
  Separate DDL/index writes from runtime.
  Showcase retains scoped setup privilege for explicit migrations/reruns,
  isolated from runtime and disclosed in README; it is not claimed revoked.
- OneLake requires the Storage token audience, unlike Fabric REST management.
  Use the approved regional OneLake endpoint, not an unexamined global
  endpoint. Workspace Viewer alone does not grant data-plane reads under
  the current OneLake security model: grant explicit read-only scoped roles.
  Do not solve this by giving the runtime workspace Contributor.
- Fabric API use by managed identities requires the Fabric administrator's
  tenant setting and permitted principal scope. Setup requires workspace
  administration/contributor rights as appropriate to the operation.
  OneLake role updates must preserve unrelated roles and use ETags.
- SQL uses Entra-only authentication: no SQL admin password, even in a
  conditional IaC branch. Bootstrap an approved Entra administrator and
  contained runtime principal with application-only permissions. Validate
  object-ID-based creation without assuming broad Directory Readers access.
- Disable ACR admin auth and Azure AI Search/Cognitive Services local/key
  auth where supported. Use managed-identity registry pull and short-lived
  deployer/federated build credentials.
- Document Intelligence needs a single-service resource/custom subdomain for
  Entra SDK auth; do not use the regional endpoint or copy client-secret
  examples from the generic SDK documentation. Validate real analysis
  permissions and confidence output.
- Application Insights Entra ingestion does not support the browser JavaScript
  SDK. Configure only supported server SDKs and never emit prompts, document
  contents, member identifiers or clinical rationale.
- No application secrets in `.env`, azd state, repo, images, logs or Key Vault.
  Key Vault is intentionally not added as a secret-storage workaround.
  Non-secret resource IDs/endpoints and public client IDs are configuration.
- CI is optional and, if introduced, uses narrowly scoped OIDC federation;
  no repository client-secret credentials.

Candidate synthetic-POC networking uses internal backend ingress and
Entra-protected data endpoints. This is not a claim of end-to-end private
networking. Selected-target policies may require VNet/private endpoints,
DNS and additional cost; resolve that before approving the final plan.
Retention, backups, logs, residency and Purview controls must be explicit,
not inferred from a region name.

## 6. Resource inventory and provisioning-limit gate

The Starter inventory is **partially checked in the selected subscription and
approved regions**. The verified environment quota and
model observations above are not a complete quota validation. This draft must
not be presented as a validated execution plan.

| Resource / target | Proposed quantity | Capacity/limit evidence required after target choice |
|---|---|---|
| Resource group | 1 | Subscription permissions, naming and policy |
| Container Apps environment | 1 | Canada Central and Canada East: verified usage 0 + proposed 1 = 1 / limit 50; consumption CPU limits remain to be checked |
| Container Apps | 2 | CPU/memory, ingress, stream timeout, scale and cold-start behavior |
| Manual proof/setup/acceptance jobs | 4 definitions, one bounded execution at a time | No ingress/schedules/automatic retry; distinct caller/setup/API identities |
| ACR Basic registry | 1 | Registry count, remote-build availability, MI pull |
| User-assigned managed identities | 3 | Principal creation and role-assignment authority |
| Azure SQL server / serverless database | 1 / 1 | Entra-only administration, regional SKU availability, vCore/storage limits |
| AI Search Basic service | 1 replica, 1 partition | Tier availability, index/vector limits, regional quota |
| Azure OpenAI account / model deployment | 1 / 1 | Approved model/version/type, regional RPM/TPM quota and residency |
| Document Intelligence S0 | 1 | Regional availability, analysis rate/page limits and local-auth disablement |
| Log Analytics / Application Insights | 1 / 0 | Canadian workspace, sanitized diagnostics, local auth off, 30-day retention and daily ingestion allowance |
| Fabric capacity / workspace / lakehouse | 0 in Starter | Enterprise-only; no capacity/workspace operation in Starter |
| Fabric aggregate-only semantic model | 0 in Starter | Enterprise-only; Starter uses SQL aggregate snapshots, not a semantic model |
| Entra resource API registrations | 1 | Owned single-tenant role-less app-only audience; no visitor SPA/user assignments or extra consent |

The `azure-quotas` skill was invoked for the selected-subscription checks.
Direct quota CLI was used rather than the supplied helper because that helper
suppresses CLI errors and defaults missing usage to zero. Verified results
above came from explicit successful CLI responses, not such defaults.
After region confirmation, check supported providers
with quota CLI, one resource type at a time; use documented fallbacks only
when unsupported. Record existing usage + proposed quantity versus actual
limits and sources. Also check policies, provider registrations, Fabric
availability and model deployment quota. No quota-increase request, provider
registration or paid change is implied by read-only discovery.

## Cost decision brief

**Non-binding planning allowances in USD, not a quote or a spending cap.**
Assume a small synthetic internal demo, one Search replica, at most two app
replicas, one modest pay-per-token model deployment, about 1,000 document
pages/month, low telemetry and SQL serverless auto-pause where effective.
Taxes, agreements, licenses, private networking, heavy load and egress may add
cost. A selected-region calculator/meter quote is required before provisioning.

| Driver | Illustrative monthly allowance | Caveat |
|---|---|---|
| Fabric capacity | $0 incremental for Starter | Starter does not resume or create capacity. Enterprise continuous F2 allowance remains $300-$500, not a verified quote |
| AI Search Basic | $80-$120 | Generally a standing hourly charge; do not assume scale-to-zero |
| Azure SQL serverless + storage | $20-$220 | Can stay awake due to connections/probes; upper cost depends on max vCores/load |
| Two Container Apps, setup/build and registry | $20-$90 | Scale-to-zero/cold starts versus always-warm availability changes cost |
| Model, document pages, telemetry, source storage/operations | $20-$70 | Usage-sensitive; approved regional Standard model and basic document extraction; actual usage still unverified |
| Policy-driven Defender for SQL | $15 planning line for one protected SQL unit | Canada East published Standard Node meter is $15/month; confirm applicable deployed-resource meter |
| Newly provisioned non-Fabric subtotal, including SQL Defender | $155-$515 | Core allowance $140-$500 plus the separate $15 protection line |
| Starter total incremental allowance | $155-$515 | No Fabric compute; same core/protection allowance, not a quote or cap; no new service proposed |
| Enterprise historical continuous-capacity illustration | $455-$1,015 | Opt-in only, includes resumed F2; no capacity operation authorized by Starter |

Starter excludes all Fabric resumption charges. The following capacity
illustration is Enterprise reference only. Reusing capacity avoids a new capacity resource, not its resumed running cost
or load impact. Because `dbtdemo` is currently paused, do not report its resumed
compute as a free sunk cost. Existing capacity storage and unrelated workloads
are outside this accelerator-only allowance and require owner coordination.
An inactive F64 has 32 times the capacity units of F2;
do not resume one as a convenience. Trial expiration and PPU listings are not
a durable shared-capacity strategy.

For a scheduling illustration only, 160 approved running hours instead of a
730-hour continuous month scales the $300-$500 F2 allowance to approximately
$66-$110, making the combined allowance approximately $221-$625. This is not
permission to impose a schedule or pause the shared capacity; its owner must
approve availability for all workloads. Fabric smoothing/settlement, storage,
load and other charges may prevent simple hour scaling from matching the bill.

On 2026-10-29, fresh `prices.azure.com/api/retail/prices` Canadian Consumption
queries returned Search Basic at USD0.101/unit-hour (USD73.73/730 hours) and
SQL Database General Purpose - Serverless - Compute Gen5, 1-vCore `vCore`,
at USD0.62611/vCore-hour. The Search API's historical `serviceName` is
`Azure Cognitive Search`; the newer-name query returned no items and was not
treated as zero cost. Continuous 0.5/1-vCore equivalents are approximately
USD228.53/USD457.06 before SQL storage/Defender; memory-based compute charging
can also raise actual SQL cost. The earlier USD20-USD220 SQL allowance assumes
effective pauses/light use, not continuous maximum load. No hard cap is
promised; sustained activity can exceed the overall allowance. The selected
small-demo service scope is unchanged, with no paid regional build pool/Fabric.

The retail price API initially returned HTTP 429, then bounded Canadian queries
succeeded. Returned Fabric workload CU/storage/reservation meters did not
establish a base F2 pay-as-you-go compute quote. The resumed F2 line remains a
budget allowance, not an asserted rate; final regional pricing is still required.
Official pricing pages render dynamic regional values.

For SQL Defender, exact Canada East public non-trial Consumption meters were
verified: Standard Node $15 per `1/Month`, Standard Instance $0.020161/hour,
and Standard vCore $0.015/hour. They are alternative meters, not three charges
to sum. The one-server/one-database POC uses a $15 protection planning line
pending applicable-meter confirmation. Selected-subscription `SqlServers`
protection is already Standard with zero remaining trial time, so do not
assume a free trial. Policy-driven protection must remain enabled.

Budget alerts are notifications, not a hard cap. No reservation purchase,
automatic shared-capacity lifecycle policy or deletion is authorized. The user
accepted the allowance rather than a hard ceiling. Additional uptime/cleanup
policies require owner approval. Starter never resumes or changes capacity.

## 7. Validation Proof

Evidence date: **2026-10-29 UTC**. No provisioning had occurred at the initial validation.

Validation scope is explicitly staged: first only the dedicated Canadian
foundation and standard managed build/private MI-proof bootstrap. No SQL,
Search, OCR/model accounts, application hosting or public ingress may be
provisioned in this first phase. `--phase foundation` enforces that stop.
Remote image builds/scans and image-build Python 3.12 tests must pass before
the proof job runs; both final images must pass before progressing to data/app
validation. This does not claim that unavailable local Docker already built them.

- [x] All validation checks pass **for the foundation/bootstrap phase**:
  - [x] Azure CLI installation: `az version`, CLI 2.91.0, containerapp extension available.
  - [x] Authentication: explicit approved subscription/tenant enabled; no default-subscription mutation.
  - [x] Bicep compilation: foundation/job/data/hosting compile; foundation now explicitly unwraps module outputs into the bootstrap's expected shape.
  - [x] Template validation: `az deployment sub validate --location canadaeast --template-file infra\foundation.bicep --parameters environmentName=benefits-iq environmentId=bb2168f9-5c9d-4961-9960-f4932b863161 --validation-level Provider --subscription 85489118-9695-41ac-ba0f-e14ba8837c91`; Succeeded, error null.
  - [x] What-if: same subscription/template/parameters with `az deployment sub what-if --validation-level Provider --no-pretty-print --result-format ResourceIdOnly`; Succeeded, error null, eight creates, no deletes. Three ACR role-assignment IDs are Unsupported because new identity principal IDs do not yet exist; static roles/scopes were checked and actual assignments/pulls must be proved after foundation creation. This is a preview limitation, not claimed runtime authorization proof.
  - [x] Project build: `npm run build`, `npm run typecheck`; 21 Node protocol/request tests pass. Latest Python run: 249 pass, 11 optional HTTP skips; those 11 previously passed separately against the preserved preview. Latest targeted bootstrap/identity/source/acceptance suite: 70 pass. Browser 14 pass, one optional screenshot capture skipped. Full npm and isolated locked Python audits report no known vulnerabilities.
  - [x] Azure Policy: actual CLI assignment read (Azure MCP is unavailable) shows the same three database-protection initiatives, no discovered denial. Provider-level foundation validation succeeds; policy-driven SQL Defender remains in the allowance and cannot be disabled.
  - [x] Renewed private job validation at `2026-10-29T14:34:03Z`: `az deployment group validate` and `what-if --validation-level Provider --result-format ResourceIdOnly --no-pretty-print` for `infra\job.bicep`, actual stored foundation/identity IDs and accepted API digest. Both Succeeded, errors null; one job Create, seven existing-resource Ignore entries, no deletion. Corrected AVM's CPU input to string `'0.5'`, not a JSON float. Local evidence: `.azure\identity-job-validation.json` (ignored). Subscription policy read still returns the three protection initiatives; an empty RG listing was not treated as absence of inherited policy.
  - [x] Real API build `cw5`, digest `sha256:e29d294ce5194d6604e72efa5b7a78c104a2f7a17bf7fdc149197a58fdf6306d`: build tests/ODBC and final non-root SDK imports/no-packaging-tools assertions pass. Exact-digest Trivy acceptance passes with OS and language results, no blocking language vulnerabilities/secrets or High/Critical OS findings. No suppression/waiver.
- [x] Data/app phase provider validation/what-if using actual foundation IDs, accepted image digests and private ingress: all three validations and previews Succeeded with errors null at `2026-10-29T14:50:35Z`-`14:50:44Z`. `data.bicep`: 13 Create changes, no Delete. Each `hosting.bicep` preview: one app Create, no Delete; predicted registry role-assignment IDs match the already-propagated API/web AcrPull assignments. Local generated evidence: `.azure\data-validation.json`, `.azure\api-hosting-validation.json`, `.azure\web-hosting-validation.json` (ignored). Preview configurations validate resource structure, not application startup or data connections.
- [x] Both actual runtime image scans and real private MI positive/four-negative proof.
- [ ] Private source/model/workflow acceptance, then public/browser checks. No clinical decision is submitted by deployment automation.

### Role Assignment Verification

Static review: web/API/setup identities receive resource-scoped AcrPull.
Only API gets Search Index Data Reader, Document Intelligence Cognitive Services
User and Cognitive Services OpenAI User. Setup gets Search Service Contributor
and Index Data Contributor, scoped to this Search service, plus SQL bootstrap
administration. Runtime SQL uses the separate constrained contained principal,
not database owner/reader/writer blanket roles. Web has no data-service role.
No subscription Owner/Contributor grant or tenant permission is generated.
Local demo uses fixtures/SQLite; no deployer data-role grant is required for it.
Actual role state, SQL permission assertions and MI pulls remain cloud gates.
The model requests 20 Standard capacity units within previously observed
available quota; these are not asserted literal TPM or a spending limit.

### Foundation execution evidence, 2026-10-29

The approved standard-build exception is recorded above. Actual owned
single-tenant resource registration/service principal creation and configuration
succeeded without a user-role assignment, consent grant, credential or owner
grant. This resolves the owned-registration permission hypothesis, **not** actual
managed-identity issuance/runtime authorization, which still requires its job.

Subscription deployment `benefits-iq-foundation-bb2168f9` created the dedicated
`rg-biq-benefits-iq-bb2168f95c9d` environment: three user-assigned identities,
Basic registry, Log Analytics and Container Apps environment, all Canada East.
Live `az role assignment list --scope <registry-resource-id>` confirms three
AcrPull assignments on that registry, matching the three managed identities.
No shared capacity/workspace or Fabric resource was touched.

ACR run `cw1` was reconciled as Failed after 1m4s, not blindly requeued: the new
venv's PATH shadowed system Python during pip bootstrapping. The Dockerfile now
uses `/usr/bin/python3` explicitly for bootstrap. Azure CLI's actual `--no-wait`
path queued the run but emitted no usable JSON; use supported `--no-logs` polling
and its completed run response rather than pretending an empty response is
success. The initial read-only CLI issue was independently fixed: Graph `/me`
uses the selected subscription/tenant, while global extension commands must not
receive an unsupported subscription flag.

Run `cw2` failed closed on a package-repository metadata signature error; no
signature checks were disabled. A bounded retry `cw3` passed signed package
installation, then exposed a missing required agent Markdown file in the
committed context. The build allowlist now requires the seven named agent
definition/options files without permitting arbitrary notes/attachments.
Run `cw4` built the API successfully. Final-image scanning, using an in-memory
short-lived deployer registry token, found bundled `msgpack` 1.1.2,
`setuptools` 70.3.0 and `urllib3` 2.7.0 advisories despite a clean application
lockfile audit. The Dockerfile removes unused system and venv packaging tools,
then verifies installed SDK imports and ODBC as the final non-root user.
No finding waiver or broad exclusion is used. Scans reject every secret match
and known language-package vulnerability; the OS threshold remains High/Critical.
The replacement API image passed as recorded above. The private proof job
initially failed provider validation before creation because AVM expects its CPU
parameter as a string; the corrected template now passes validation/what-if.
The first successful proof's terminal replica expired before receipt recovery.
A new bounded proof execution, `p-biq-benefits-iq-bb2168f95c9d-tsuubkj`,
succeeded and its validated receipt is persisted in the ignored environment
state. The signed web-MI token passed independent validation and four wrong
tenant/API-audience/caller-client/caller-principal configurations were rejected.
No token was exposed and no data service was exercised. Real CLI text logs use
timestamp/`stdout F` framing; the extension's nested JSON output was invalid.
The parser now accepts exactly one complete framed JSON receipt, not arbitrary
substrings/partial/stderr records, and retains execution/image binding.

The frontend image also built and passed exact-digest vulnerability/secret
acceptance: `sha256:468fe702db7317007fdb98240d50bae59ee9b74c3585546d46aa3b772f797620`.
Both container builds and the private MI proof are complete, not merely
candidate-base scans. The latest targeted bootstrap/proof suite has 75 passing
tests. Data/private-application provider validation and live connections are next.

Final images, private MI/source/model proofs, data services and public/browser
cloud acceptance remain outstanding. The existing foundation can incur registry/
telemetry charges while held; it is not automatically deleted. No billable SQL,
Search, Document Intelligence or OpenAI account has been created.

## 8. Implementation and rerun plan

1. Preserve the approved target, Canadian regions and revised Starter cost
   allowance. Complete remaining quotas, policies and scoped Entra/data access
   checks. Fabric/Purview prerequisites below do not gate Starter.
2. Verify user-approved first-party chat removes affected dependency paths;
   preserve actual Python MAF/AG-UI compatibility and no retained chat threads.
   Report any unremediable exposure before cloud publication.
3. Generate staged Bicep, minimal containers/build ignores,
   bootstrap/seed scripts and cloud adapters. Never include local databases,
   `.env`, `.azure`, token caches or uploaded guide attachments in build contexts.
4. Preflight sign-in, permissions, tenant settings, licensing, model quota and
   configuration. Provision only approved resources and run authenticated setup.
   No visitor Entra redirect or user assignment is required for showcase.
5. Seed versioned synthetic member/plan/claims inputs and generated synthetic
   intake documents in Azure SQL; create/populate the real criteria index and
   separate aggregate snapshot. Populate SQL through migrations, not
   container-local files. OneLake and semantic-model setup is Enterprise-only.
6. Make reruns adopt known resource/item IDs, apply versioned migrations and
   content-hash-based seeds and preserve human decisions/audit.
   Fabric operations are Enterprise-only. Never wipe a workspace or database on redeploy.
7. Retry bounded permission propagation and throttling using service hints;
   distinguish missing consent, missing role, paused capacity, source gap,
   extraction uncertainty and service outage. No fixture fallback in cloud mode.
8. Use database-free liveness checks; implement intentional readiness/cold-start
   behavior rather than accidentally defeating SQL auto-pause or inheriting a
   60-second timeout that cannot handle actual cloud work.
9. Record sanitized setup phase/results and resumable diagnostics without secrets.
   On failure, identify billable resources left running and safe retry steps;
   do not delete, replace or resume shared resources automatically.
10. Update README with the exact command, prerequisite/bootstrap matrix,
    dependency versions, local-versus-cloud mode and costs/recovery. Mark the
    plan Ready for Validation, invoke `azure-validate`, then `azure-deploy`
    only after successful validation and provisioning approval.

## 9. Required verification before claiming deployment

| Acceptance path | Required evidence |
|---|---|
| Resource deployment | Actual resource IDs/regions and healthy app endpoints; ARM success alone is insufficient |
| Secretless operation | Local/key auth disabled as supported, MI token acquisition, no secret-bearing configuration/artifacts |
| Service trust / anonymous views | Actual app-only MI issuance; absent/expired/wrong-tenant/audience/client/principal rejected. Demo view selection is intentionally public, not a verified user role. Future Entra user login is not showcase acceptance. |
| Role/employer isolation | Reviewer/contact field boundaries and cross-employer/case denials through backend tools; employer receives only suppressed aggregates |
| Starter sources and search | Actual MI SQL source read and versioned Search criteria retrieval; source-gap/stale-version behavior; no fixture fallback |
| Extraction | Actual Document Intelligence analysis of a synthetic document, evidence spans/confidence and explicit human low-confidence verification |
| Model/AG-UI | Actual Azure model stream through MAF and first-party authenticated proxy; sanitized lifecycle/tool/domain events, cancellation, errors and reconnect isolation |
| Human workflow | Explicit authorized decision, optimistic conflicts/idempotency and durable audit survive app revision/restart |
| Starter employer aggregates | Actual authorized SQL aggregate result, minimum-cell suppression, no detail-record access; no semantic-model claim |
| Rerun/recovery | Second setup does not duplicate seeds or overwrite human history; missing prerequisite and partial-service failure are actionable |
| Governance | Verified residency, retention/backup settings and sanitized telemetry; Enterprise labels/OneLake/DAX require separate verification and are not Starter claims |
| Existing behavior | Covering backend/HTTP/browser tests and production build; no regressions in local synthetic workflow |

The current local evidence is recorded at the top of this plan. No live cloud
verification or deployed URL exists yet. The signed caller validator is wired
into cloud runtime paths and tested locally, not proof of actual MI issuance.
The existing loopback preview is not a cloud deployment.

## 10. Enterprise-only governance prerequisite and administrator checklist

The user initially chose administrator-assisted label setup, then approved the
synthetic Azure-native Starter simplification. This checklist remains an opt-in
Enterprise prerequisite, **not a Starter blocker**. Do not ask for the same
architecture decisions again or treat execution approval as tenant-wide consent.
No additional tenant-wide consent/settings were authorized.

The documented discovery endpoint
`GET https://graph.microsoft.com/v1.0/security/dataSecurityAndGovernance/sensitivityLabels`
returned HTTP403 `InsufficientGraphPermissions`. No permission was granted or
bypassed. An administrator may supply approved IDs without expanding discovery
permissions. Supplying an ID does not itself prove a right to apply the label.

Administrator-supplied values/confirmations, **no secrets**:

1. Approved tenant label GUID/display name for both Lakehouse and SemanticModel,
   or separate approved labels if the policy requires them.
2. Confirmation that the label is active/published to the deployment principal,
   supported for both item types, appropriately licensed, and that the actual
   applying principal has application rights.
3. Any encryption/export restrictions and permitted principal/application
   handling. Identify the administrator action needed if this principal cannot
   apply it; do not broaden tenant-wide consent as a shortcut.
4. Approved handling, access/export and retention policy. Review the proposed
   SQL LRS seven-day PITR and 30-day server logs. No automatic case/audit
   deletion is configured or approved.

Fabric supports creation-time `sensitivityLabelSettings` with `labelId` and
`sensitivityLabelApplyStrategy: "ApplyOrFail"` for the required item types.
Apply using this fail-closed strategy, then read back `sensitivityLabel.id` and
compare to the approved GUID. No Ignore/BestEffort fallback or Azure-tag substitute.
Graph discovery permission is not a requirement when the administrator supplies
the approved ID; actual Fabric label/license/policy/application checks remain.

Continue Starter implementation/validation and approved core deployment when
ready. Starter never resumes or changes capacity/workspaces. Enterprise
Fabric/Purview provisioning remains gated by these prerequisites. The separate
dependency and runtime-auth readiness gates must clear before public exposure.

## 11. Primary references checked

- OneLake endpoints, token audience and regional behavior:
  https://learn.microsoft.com/en-us/fabric/onelake/onelake-access-api
- Fabric MI support and required tenant setting:
  https://learn.microsoft.com/en-us/rest/api/fabric/articles/identity-support
- OneLake control/data-plane permissions:
  https://learn.microsoft.com/en-us/fabric/onelake/security/get-started-security
- OneLake role API, MI support and ETag concurrency:
  https://learn.microsoft.com/en-us/rest/api/fabric/core/onelake-data-access-security/create-or-update-data-access-roles
- Semantic-model creation, identity support and license requirement:
  https://learn.microsoft.com/en-us/rest/api/fabric/semanticmodel/items/create-semantic-model
- Execute Queries restrictions and payload errors:
  https://learn.microsoft.com/en-us/rest/api/power-bi/datasets/execute-queries
- Entra SPA authorization-code + PKCE:
  https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow
- Search RBAC/local-auth disablement (including Free-tier RBAC support):
  https://learn.microsoft.com/en-us/azure/search/search-security-enable-roles
- Document Intelligence Entra client/custom-subdomain requirements:
  https://learn.microsoft.com/en-us/python/api/overview/azure/ai-documentintelligence-readme?view=azure-python
- Application Insights Entra ingestion and browser-SDK limitation:
  https://learn.microsoft.com/en-us/azure/azure-monitor/app/azure-ad-authentication
- Model deployment-type processing geography:
  https://learn.microsoft.com/en-us/azure/foundry/foundry-models/concepts/deployment-types
- Location-based model-capacity discovery:
  https://learn.microsoft.com/en-us/rest/api/aiservices/accountmanagement/location-based-model-capacities/list?view=rest-aiservices-accountmanagement-2024-10-01
- Entra geo-located identity storage/processing boundary:
  https://learn.microsoft.com/en-us/entra/fundamentals/data-residency
- Pricing methodology, not an obtained final quote:
  https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/
  https://azure.microsoft.com/en-us/pricing/details/search/
  https://azure.microsoft.com/en-us/pricing/details/defender-for-cloud/
  https://prices.azure.com/api/retail/prices
- Official container base-image metadata (digest-pinned after read-only lookup):
  https://hub.docker.com/v2/repositories/library/node/tags/24-bookworm-slim
  https://hub.docker.com/v2/repositories/library/python/tags/3.11-slim-bookworm
- Official ODBC 18 Linux installation:
  https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server
- azd ACR remote-build support (no local Docker requirement):
  https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/remote-builds
- Azure Monitor diagnostic routing without a Log Analytics shared-key recipe:
  https://learn.microsoft.com/en-us/azure/container-apps/log-options
