"""Staged, secretless showcase deployment. Default operation is read-only."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from datetime import date
from uuid import uuid4

if __package__:
    from .resource_api import GRAPH, ensure_resource_api, canonical_guid
else:
    from resource_api import GRAPH, ensure_resource_api, canonical_guid

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / ".azure"
TEMPLATES = ("foundation", "job", "data", "network", "hosting")
IMAGE_TESTS = ("test_cloud_adapters.py", "test_cloud_seed.py", "test_entra_auth.py",
               "test_identity_probe.py", "test_showcase.py", "test_cloud_acceptance.py",
               "test_cloud_source_probe.py", "test_sql_network_probe.py")
ROOT_CONTEXT = ("package.json", "package-lock.json", "requirements.lock.txt", "next.config.mjs",
                "next-env.d.ts", "tsconfig.json", ".dockerignore")
INFRA_CONTEXT = ("Dockerfile.api", "Dockerfile.web", "schema.sql", "grant-runtime.sql")
AGENT_CONTEXT = ("orchestrator.md", "intake.md", "evidence.md", "member-status.md",
                 "renewal.md", "employer-insight.md", "showcase-options.json")


class DeploymentError(RuntimeError):
    pass


def command(args, timeout=180, env=None):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                                timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired as error:
        raise DeploymentError("COMMAND_TIMED_OUT_RECONCILE_STATE_BEFORE_RETRY") from error
    if result.returncode:
        code = re.search(r'"code"\s*:\s*"([A-Za-z0-9_]+)"|(?:ERROR: )?\(([A-Za-z0-9_]+)\)',
                         result.stderr)
        suffix = next((part for part in code.groups() if part), "") if code else "COMMAND_FAILED"
        operation = re.sub(r"[^A-Za-z0-9_]", "_", args[1].upper()) if len(args) > 1 else "COMMAND"
        raise DeploymentError(f"{Path(args[0]).stem.upper()}_{operation}_{suffix}")
    return result.stdout


def json_output(value):
    try:
        return json.loads(value)
    except ValueError as error:
        raise DeploymentError("COMMAND_JSON_RESPONSE_INVALID") from error


class Azure:
    def __init__(self, subscription):
        self.subscription = canonical_guid(subscription)
        self.executable = shutil.which("az")
        if not self.executable:
            raise DeploymentError("AZURE_CLI_REQUIRED")

    def text(self, *args, timeout=180):
        return command([self.executable, *args, "--subscription", self.subscription,
                        "--only-show-errors", "--output", "json"], timeout)

    def run(self, *args, timeout=180, allow_empty=False):
        value = self.text(*args, timeout=timeout)
        if allow_empty and not value.strip():
            return None
        return json_output(value)

    def graph(self, method, path, body=None, query=None):
        args = ["rest", "--method", method, "--url", GRAPH + path]
        if query:
            args += ["--url-parameters", *(f"{key}={value}" for key, value in query.items())]
        if body is None:
            return self.run(*args)
        with json_file(body) as filename:
            return self.run(*args, "--body", "@" + filename, allow_empty=method == "PATCH")


class json_file:
    def __init__(self, content):
        self.content = content

    def __enter__(self):
        WORK.mkdir(exist_ok=True)
        handle = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", suffix=".json",
                                             prefix="deployment-", dir=WORK, delete=False)
        self.path = Path(handle.name)
        with handle:
            json.dump(self.content, handle)
        return str(self.path)

    def __exit__(self, *args):
        self.path.unlink(missing_ok=True)


def save_state(path, state):
    with json_file(state) as temporary:
        os.replace(temporary, path)


def validate_environment(environment):
    if not re.fullmatch(r"[a-z][a-z0-9-]{1,9}[a-z0-9]", environment) or "--" in environment:
        raise DeploymentError("ENVIRONMENT_REQUIRES_3_TO_11_LOWERCASE_LETTERS_DIGITS_DASHES")


def load_state(azure, environment, tenant):
    validate_environment(environment)
    path = WORK / f"showcase-{environment}.json"
    if path.exists():
        state = json_output(path.read_text(encoding="utf-8"))
        if (state.get("subscription") != azure.subscription or state.get("tenant") != tenant
                or state.get("environment") != environment):
            raise DeploymentError("EXISTING_ENVIRONMENT_CONTEXT_MISMATCH")
        canonical_guid(state["environmentId"])
    else:
        groups = azure.run("group", "list",
                           "--query", "[?tags.\"azd-env-name\"=='" + environment + "']")
        if groups:
            raise DeploymentError("ENVIRONMENT_ALREADY_EXISTS_RECOVER_ITS_STATE_DO_NOT_CREATE_A_DUPLICATE")
        state = {"subscription": azure.subscription, "tenant": tenant, "environment": environment,
                 "environmentId": str(uuid4())}
        save_state(path, state)
    return path, state


def names(state):
    base = f"biq-{state['environment']}-{state['environmentId'].replace('-', '')[:12]}"
    return base, f"rg-{base}"


def tags(state):
    return {"azd-env-name": state["environment"], "benefits-iq-environment-id": state["environmentId"],
            "benefits-iq-profile": "showcase", "data-classification": "synthetic-only"}


def verify_ownership(azure, state):
    _, group = names(state)
    if azure.run("group", "exists", "--name", group):
        existing = azure.run("group", "show", "--name", group)
        if existing.get("location") != "canadaeast" or any(
                existing.get("tags", {}).get(key) != value for key, value in tags(state).items()):
            raise DeploymentError("RESOURCE_GROUP_OWNERSHIP_COLLISION")
        resources = azure.run("resource", "list", "--resource-group", group)
        for resource in resources:
            if "/" not in resource["type"].split("/", 1)[-1] and any(
                    (resource.get("tags") or {}).get(key) != value for key, value in tags(state).items()):
                if resource["type"].lower() == "microsoft.network/networkinterfaces":
                    endpoint_id = (f"/subscriptions/{azure.subscription}/resourceGroups/{group}"
                                   f"/providers/Microsoft.Network/privateEndpoints/pe-sql-{names(state)[0]}")
                    endpoint = next((item for item in resources
                                     if item["id"].lower() == endpoint_id.lower()
                                     and all((item.get("tags") or {}).get(key) == value
                                             for key, value in tags(state).items())), None)
                    if endpoint is not None:
                        actual = azure.run("network", "private-endpoint", "show", "--ids", endpoint_id)
                        if any(nic.get("id", "").lower() == resource["id"].lower()
                               for nic in actual.get("networkInterfaces", [])):
                            continue
                raise DeploymentError("UNOWNED_RESOURCE_IN_DEDICATED_GROUP")


def policy_preflight(azure, *, private_sql=False):
    """Inventory ancestors; reject legacy public SQL under the known modifier.

    This is a conservative topology gate, not an evaluator of policy conditions,
    parameter overrides, exemptions or compliance.
    """
    response = azure.run(
        "rest", "--method", "get", "--url",
        f"https://management.azure.com/subscriptions/{azure.subscription}"
        "/providers/Microsoft.Authorization/policyAssignments",
        "--url-parameters", "api-version=2023-04-01")
    if not isinstance(response, dict) or not isinstance(response.get("value"), list):
        raise DeploymentError("EFFECTIVE_POLICY_ASSIGNMENT_RESPONSE_INVALID")
    if response.get("nextLink"):
        raise DeploymentError("EFFECTIVE_POLICY_PAGINATION_REQUIRES_REVIEW")
    pending = []
    for assignment in response["value"]:
        properties = assignment.get("properties") if isinstance(assignment, dict) else None
        if not isinstance(properties, dict) or not properties.get("policyDefinitionId"):
            raise DeploymentError("EFFECTIVE_POLICY_ASSIGNMENT_RESPONSE_INVALID")
        if properties.get("enforcementMode", "Default") != "DoNotEnforce":
            pending.append(properties["policyDefinitionId"])
    visited = set()
    while pending:
        reference = pending.pop()
        if not isinstance(reference, str) or not re.fullmatch(
                r"/(?:[A-Za-z0-9_.-]+/)*(?:policySetDefinitions|policyDefinitions)/[A-Za-z0-9_.-]+",
                reference, re.IGNORECASE):
            raise DeploymentError("EFFECTIVE_POLICY_DEFINITION_REFERENCE_INVALID")
        normalized = reference.lower()
        if normalized.endswith("/policydefinitions/azuresql_publicnetwork_modify"):
            if not private_sql:
                raise DeploymentError("INHERITED_SQL_NETWORK_POLICY_REVIEW_REQUIRED")
            continue
        if "/policysetdefinitions/" not in normalized or normalized in visited:
            continue
        visited.add(normalized)
        if len(visited) > 32:
            raise DeploymentError("EFFECTIVE_POLICY_INITIATIVE_LIMIT_REQUIRES_REVIEW")
        initiative = azure.run(
            "rest", "--method", "get", "--url", "https://management.azure.com" + reference,
            "--url-parameters", "api-version=2023-04-01")
        properties = initiative.get("properties") if isinstance(initiative, dict) else None
        definitions = properties.get("policyDefinitions") if isinstance(properties, dict) else None
        if not isinstance(definitions, list):
            raise DeploymentError("EFFECTIVE_POLICY_INITIATIVE_RESPONSE_INVALID")
        for definition in definitions:
            if not isinstance(definition, dict) or not definition.get("policyDefinitionId"):
                raise DeploymentError("EFFECTIVE_POLICY_INITIATIVE_RESPONSE_INVALID")
            pending.append(definition["policyDefinitionId"])


def preflight(azure):
    if date.today() >= date(2027, 4, 14):
        raise DeploymentError("APPROVED_MODEL_RETIREMENT_REACHED_NEW_CANADIAN_MODEL_APPROVAL_REQUIRED")
    if any(os.environ.get(key) for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET")):
        raise DeploymentError("DEPLOYMENT_DISALLOWS_STATIC_APPLICATION_CREDENTIALS")
    account = azure.run("account", "show")
    if (account.get("id") != azure.subscription or account.get("state") != "Enabled"
            or account.get("environmentName") != "AzureCloud" or account.get("user", {}).get("type") != "user"):
        raise DeploymentError("INTERACTIVE_DEPLOYER_IN_APPROVED_AZURE_CONTEXT_REQUIRED")
    WORK.mkdir(exist_ok=True)
    for template in TEMPLATES:
        command([azure.executable, "bicep", "build", "--file", str(ROOT / "infra" / f"{template}.bicep"),
                 "--outfile", str(WORK / f"{template}.compiled.json")])
    compiled = json_output((WORK / "data.compiled.json").read_text(encoding="utf-8"))
    sql = [resource for resource in compiled.get("resources", [])
           if resource.get("type", "").lower() == "microsoft.sql/servers"]
    if (len(sql) != 1 or sql[0].get("condition") is not None
            or sql[0].get("properties", {}).get("publicNetworkAccess") != "Disabled"
            or any(resource.get("type", "").lower() == "microsoft.sql/servers/firewallrules"
                   for resource in compiled.get("resources", []))):
        raise DeploymentError("UNCONDITIONAL_PRIVATE_SQL_TEMPLATE_REQUIRED")
    policy_preflight(azure, private_sql=True)
    owner = azure.graph("GET", "/me", query={"$select": "id"})["id"]
    canonical_guid(owner)
    extension = json_output(command([azure.executable, "extension", "show", "--name", "containerapp",
                                     "--only-show-errors", "--output", "json"]))
    if extension.get("name") != "containerapp":
        raise DeploymentError("CONTAINERAPP_EXTENSION_REQUIRED")
    scanner = os.environ.get("BENEFITS_TRIVY") or shutil.which("trivy")
    if not scanner or not Path(scanner).is_file():
        raise DeploymentError("TRIVY_SCANNER_REQUIRED_SET_BENEFITS_TRIVY_TO_VERIFIED_EXECUTABLE")
    context_files()
    return account, owner, scanner


def deploy_template(azure, state, template, parameters):
    verify_ownership(azure, state)
    options = ["deployment", "sub" if template == "foundation" else "group", "create",
               "--name", f"benefits-iq-{template}-{state['environmentId'][:8]}",
               "--template-file", str(ROOT / "infra" / f"{template}.bicep")]
    options += (["--location", "canadaeast"] if template == "foundation"
                else ["--resource-group", names(state)[1]])
    with json_file({key: {"value": value} for key, value in parameters.items()}) as filename:
        validation = [*options]
        validation[2] = "validate"
        azure.run(*validation, "--parameters", "@" + filename, "--validation-level", "Provider", timeout=2400)
        preview = [*options]
        preview[2] = "what-if"
        changes = azure.run(*preview, "--parameters", "@" + filename, "--validation-level", "Provider",
                            "--no-pretty-print", "--result-format", "ResourceIdOnly", timeout=2400)
        if (changes.get("status") != "Succeeded" or changes.get("error")
                or not isinstance(changes.get("changes"), list)):
            raise DeploymentError("SUCCESSFUL_COMPLETE_WHAT_IF_REQUIRED")
        if any(change.get("changeType") == "Delete" for change in changes["changes"]):
            raise DeploymentError("RESOURCE_DELETION_NOT_APPROVED")
        result = azure.run(*options, "--parameters", "@" + filename, timeout=2400)
    if result.get("properties", {}).get("provisioningState") != "Succeeded":
        raise DeploymentError("ARM_DEPLOYMENT_NOT_SUCCESSFUL")
    return {key: value["value"] for key, value in result["properties"]["outputs"].items()}


def context_files():
    tracked = command(["git", "ls-files", "-z"]).split("\0")
    files = []
    for name in filter(None, tracked):
        path = Path(name)
        parts = path.parts
        allowed = (name in ROOT_CONTEXT or (len(parts) == 2 and parts[0] == "infra" and parts[1] in INFRA_CONTEXT)
                   or (len(parts) == 2 and parts[0] == "tests" and parts[1] in IMAGE_TESTS)
                   or (len(parts) == 2 and parts[0] == "agents" and parts[1] in AGENT_CONTEXT)
                   or (parts[0] in {"service", "app", "components", "lib"}
                       and path.suffix.lower() in {".py", ".json", ".ts", ".tsx", ".css", ".mjs"}))
        if allowed:
            source = ROOT / path
            if source.is_symlink() or not source.resolve().is_relative_to(ROOT):
                raise DeploymentError("BUILD_CONTEXT_LINK_DENIED")
            files.append(path)
    expected = {Path(path) for path in ROOT_CONTEXT}
    expected.update(Path("infra") / path for path in INFRA_CONTEXT)
    expected.update(Path("tests") / path for path in IMAGE_TESTS)
    expected.update(Path("agents") / path for path in AGENT_CONTEXT)
    missing = expected - set(files)
    if missing:
        raise DeploymentError("COMMITTED_BUILD_CONTEXT_INCOMPLETE")
    dirty = command(["git", "status", "--porcelain", "--", *(str(path) for path in files)])
    if dirty.strip():
        raise DeploymentError("COMMIT_REVIEWED_APPLICATION_CHANGES_BEFORE_BUILD")
    return sorted(files)


def committed_content(path):
    result = subprocess.run(["git", "show", f"HEAD:{path.as_posix()}"], cwd=ROOT,
                            capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise DeploymentError("COMMITTED_BUILD_SOURCE_UNAVAILABLE")
    return result.stdout


def scan_findings(report, image):
    if (not isinstance(report, dict) or report.get("SchemaVersion") != 2
            or report.get("ArtifactType") != "container_image"
            or image not in report.get("Metadata", {}).get("RepoDigests", [])
            or not isinstance(report.get("Results"), list)
            or not {"os-pkgs", "lang-pkgs"}.issubset({result.get("Class") for result in report["Results"]})):
        raise DeploymentError("COMPLETE_EXACT_IMAGE_SCAN_REQUIRED")
    return [item for result in report["Results"] for kind in ("Vulnerabilities", "Secrets")
            for item in result.get(kind, [])
            if (kind == "Secrets" or result["Class"] == "lang-pkgs"
                or item.get("Severity") not in {"LOW", "MEDIUM"})]


def scan_image(azure, state, image, scanner):
    cache = str(WORK / "scan-cache")
    environment = {key: value for key, value in os.environ.items()
                   if key not in {"TRIVY_USERNAME", "TRIVY_PASSWORD", "TRIVY_REGISTRY_TOKEN"}}
    command([str(scanner), "image", "--quiet", "--download-db-only", "--cache-dir", cache,
             "--skip-version-check"], timeout=1000, env=environment)
    login = azure.run("acr", "login", "--name", state["foundation"]["registryName"], "--expose-token")
    if (login.get("loginServer") != state["foundation"]["registryEndpoint"]
            or not isinstance(login.get("accessToken"), str) or not login["accessToken"]):
        raise DeploymentError("EXACT_REGISTRY_SHORT_LIVED_TOKEN_REQUIRED")
    scan_environment = {**environment, "TRIVY_USERNAME": "00000000-0000-0000-0000-000000000000",
                        "TRIVY_PASSWORD": login["accessToken"]}
    report = json_output(command([
        str(scanner), "image", "--quiet", "--image-src", "remote", "--scanners", "vuln,secret",
        "--format", "json", "--cache-dir", cache, "--timeout", "15m", "--skip-version-check",
        "--skip-db-update", "--skip-java-db-update", image,
    ], timeout=1000, env=scan_environment))
    return scan_findings(report, image)


def build_image(azure, state, component, scanner):
    files = context_files()
    content = hashlib.sha256()
    blobs = [(path, committed_content(path)) for path in files]
    if sum(len(blob) for _, blob in blobs) > 20_000_000:
        raise DeploymentError("ALLOWLISTED_BUILD_CONTEXT_LIMIT")
    for path, blob in blobs:
        content.update(path.as_posix().encode() + b"\0" + blob)
    identifier = content.hexdigest()[:16]
    with tempfile.TemporaryDirectory(prefix="image-context-", dir=WORK) as directory:
        for path, blob in blobs:
            target = Path(directory) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
        run = azure.run("acr", "build", "--registry", state["foundation"]["registryName"],
                        "--image", f"benefits-{component}:{identifier}", "--file",
                        str(Path(directory) / "infra" / f"Dockerfile.{component}"), "--platform", "linux/amd64",
                        "--no-logs", directory, timeout=1800)
    run_id = run["runId"]
    deadline = time.monotonic() + 1800
    while True:
        result = azure.run("acr", "task", "show-run", "--registry", state["foundation"]["registryName"],
                           "--run-id", run_id)
        if result["status"] == "Succeeded":
            break
        if result["status"] in {"Failed", "Canceled", "Error", "Timeout"}:
            raise DeploymentError(f"IMAGE_BUILD_{result['status'].upper()}_INSPECT_ACR_RUN_{run_id}")
        if time.monotonic() >= deadline:
            raise DeploymentError(f"IMAGE_BUILD_WAIT_EXPIRED_RECONCILE_ACR_RUN_{run_id}")
        time.sleep(10)
    digest = azure.run("acr", "repository", "show", "--name", state["foundation"]["registryName"],
                       "--image", f"benefits-{component}:{identifier}", "--query", "digest")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise DeploymentError("BUILT_IMAGE_DIGEST_REQUIRED")
    image = f"{state['foundation']['registryEndpoint']}/benefits-{component}@{digest}"
    findings = scan_image(azure, state, image, scanner)
    if findings:
        safe = [{"id": item.get("VulnerabilityID") or item.get("RuleID"),
                 "severity": item.get("Severity"), "package": item.get("PkgName")}
                for item in findings]
        save_state(WORK / f"{component}-image-findings.json", {"image": image, "findings": safe})
        raise DeploymentError(f"{component.upper()}_IMAGE_FINDINGS_BLOCK_EXPOSURE")
    return digest


def job(azure, state, purpose, identity, variables, receipt):
    foundation = state["foundation"]
    prefix = {"identity-proof": "p", "private-sql": "q", "synthetic-setup": "s",
              "runtime-sources": "r", "cloud-acceptance": "v"}[purpose]
    environment = foundation if purpose == "identity-proof" else state["network"]
    if purpose != "identity-proof":
        prefix = "n-" + prefix
    name = f"{prefix}-{names(state)[0]}"
    deploy_template(azure, state, "job", {
        "name": name, "tags": tags(state), "environmentResourceId": environment["environmentResourceId"],
        "identityResourceId": identity["resourceId"], "registryEndpoint": foundation["registryEndpoint"],
        "imageDigest": state["apiImage"], "purpose": purpose, "environmentVariables": variables,
    })
    execution = azure.run("containerapp", "job", "start", "--name", name,
                          "--resource-group", names(state)[1])
    execution_name = execution["name"]
    deadline = time.monotonic() + 1000
    while True:
        current = azure.run("containerapp", "job", "execution", "show", "--name", name,
                            "--job-execution-name", execution_name, "--resource-group", names(state)[1])
        status = current.get("properties", {}).get("status")
        if status in {"Succeeded", "Failed", "Stopped", "Degraded"}:
            break
        if time.monotonic() >= deadline:
            raise DeploymentError(f"JOB_WAIT_EXPIRED_RECONCILE_{execution_name}")
        time.sleep(10)
    if status != "Succeeded":
        raise DeploymentError(f"JOB_{purpose.upper().replace('-', '_')}_FAILED_INSPECT_{execution_name}")
    expected_image = f"{foundation['registryEndpoint']}/benefits-api@{state['apiImage']}"
    containers = current["properties"].get("template", {}).get("containers", [])
    if (len(containers) != 1 or containers[0].get("name") != "governed-job"
            or containers[0].get("image") != expected_image):
        raise DeploymentError("JOB_EXECUTION_IMAGE_MISMATCH")
    logs = azure.text("containerapp", "job", "logs", "show", "--name", name,
                      "--execution", execution_name, "--resource-group", names(state)[1],
                      "--container", "governed-job", "--format", "text", "--tail", "100")
    result = job_receipt(logs, purpose, receipt)
    return {"execution": execution_name, "status": receipt, "image": state["apiImage"],
            "receipt": result}


def job_receipt(logs, purpose, receipt):
    receipts = []
    for line in logs.splitlines():
        match = re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?"
            r"(?:Z|[+-]\d{2}:\d{2}) stdout F (\{.*\})", line)
        if match:
            result = json_output(match.group(1))
            if result.get("status") == receipt:
                receipts.append(result)
    if len(receipts) != 1 or not valid_receipt(purpose, receipts[0]):
        raise DeploymentError(f"JOB_{purpose.upper().replace('-', '_')}_VALID_COMPLETE_RECEIPT_REQUIRED")
    return receipts[0]


def valid_receipt(purpose, receipt):
    if purpose == "private-sql":
        return (receipt.get("schema_mutated") is False
                and type(receipt.get("resolved_address_count")) is int
                and receipt["resolved_address_count"] > 0
                and set(receipt.get("checks", [])) == {"private_dns", "managed_identity_sql"})
    if purpose == "identity-proof":
        return (receipt.get("token_exposed") is False
                and receipt.get("data_services_exercised") is False
                and set(receipt.get("negative_checks", [])) == {
                    "api_client_id", "runtime_client_id", "runtime_principal_id", "tenant_id"})
    if purpose == "synthetic-setup":
        return all(type(receipt.get(key)) is int and receipt[key] > 0
                   for key in ("source_records", "documents", "criteria", "aggregate_cells"))
    if purpose == "runtime-sources":
        return (receipt.get("case_mutated") is False
                and {"runtime_sql_permissions", "sql_source_binary_document", "live_scoped_search",
                     "fresh_document_intelligence"}.issubset(receipt.get("checks", [])))
    return (receipt.get("clinical_decision_submitted") is False
            and type(receipt.get("workflow_write_exercised")) is bool
            and {"real_model_agui_stream", "chat_read_only", "selected_view_shapes",
                 "direct_upload_send_create_rejection"}.issubset(receipt.get("checks", [])))


def host(azure, state, component, variables, public=False):
    identity = state["foundation"][component + "Identity"]
    return deploy_template(azure, state, "hosting", {
        "name": component + "-" + names(state)[0], "tags": tags(state),
        "environmentName": state["network"]["environmentName"],
        "registryName": state["foundation"]["registryName"], "identityName": identity["name"],
        "identityResourceId": identity["resourceId"], "identityPrincipalId": identity["principalId"],
        "component": component, "imageDigest": state[component + "Image"],
        "environmentVariables": variables, "publicFrontend": public,
    })


def deploy(azure, path, state, owner, scanner, foundation_only=False):
    verify_ownership(azure, state)
    if azure.run("group", "exists", "--name", names(state)[1]):
        apps = azure.run("resource", "list", "--resource-group", names(state)[1],
                         "--resource-type", "Microsoft.App/containerApps")
        web_name = "web-" + names(state)[0]
        if any(app["name"] == web_name for app in apps):
            azure.run("containerapp", "ingress", "enable", "--name", web_name,
                      "--resource-group", names(state)[1], "--type", "internal",
                      "--target-port", "3000", "--transport", "auto", "--allow-insecure", "false")
    state["resourceApi"] = ensure_resource_api(azure.graph, state["environmentId"], owner)
    save_state(path, state)
    foundation = deploy_template(azure, state, "foundation", {
        "environmentName": state["environment"], "environmentId": state["environmentId"],
    })["foundation"]
    state["foundation"] = foundation
    save_state(path, state)
    state["apiImage"] = build_image(azure, state, "api", scanner)
    save_state(path, state)
    caller = {"BENEFITS_TENANT_ID": state["tenant"],
              "BENEFITS_API_CLIENT_ID": state["resourceApi"]["clientId"],
              "BENEFITS_RUNTIME_CLIENT_ID": foundation["webIdentity"]["clientId"],
              "BENEFITS_RUNTIME_PRINCIPAL_ID": foundation["webIdentity"]["principalId"]}
    state["identityProof"] = job(azure, state, "identity-proof", foundation["webIdentity"],
                                 caller, "managed_identity_caller_verified")
    save_state(path, state)
    state["webImage"] = build_image(azure, state, "web", scanner)
    save_state(path, state)
    if foundation_only:
        print(json.dumps({"status": "identity_foundation_verified", "cloud_application_deployed": False,
                          "environmentState": str(path.relative_to(ROOT))}))
        return
    base = names(state)[0]
    data = deploy_template(azure, state, "data", {
        "name": base, "tags": tags(state), "setupIdentityName": foundation["setupIdentity"]["name"],
        "setupPrincipalId": foundation["setupIdentity"]["principalId"],
        "apiPrincipalId": foundation["apiIdentity"]["principalId"],
    })["environmentVariables"]
    state["data"] = data
    save_state(path, state)
    state["network"] = deploy_template(azure, state, "network", {
        "name": base, "tags": tags(state), "logsResourceId": foundation["logsResourceId"],
    })["network"]
    save_state(path, state)
    sql = azure.run("sql", "server", "show", "--resource-group", names(state)[1], "--name", "sql-" + base)
    if sql.get("publicNetworkAccess") != "Disabled":
        raise DeploymentError("LIVE_SQL_PUBLIC_NETWORK_MUST_REMAIN_DISABLED")
    aad = azure.run(
        "rest", "--method", "get", "--url",
        "https://management.azure.com" + sql["id"] + "/azureADOnlyAuthentications/Default",
        "--url-parameters", "api-version=2025-01-01")
    if aad.get("properties", {}).get("azureADOnlyAuthentication") is not True:
        raise DeploymentError("LIVE_SQL_ENTRA_ONLY_AUTHENTICATION_REQUIRED")
    endpoint = azure.run("network", "private-endpoint", "show", "--ids",
                         state["network"]["sqlEndpointResourceId"])
    links = endpoint.get("privateLinkServiceConnections", [])
    if (len(links) != 1 or links[0].get("privateLinkServiceId", "").lower() != sql["id"].lower()
            or links[0].get("groupIds") != ["sqlServer"]
            or links[0].get("privateLinkServiceConnectionState", {}).get("status") != "Approved"):
        raise DeploymentError("APPROVED_PRIVATE_SQL_ENDPOINT_REQUIRED")
    data = {**data, "BENEFITS_SQL_PRIVATE_CIDR": state["network"]["sqlPrivateCidr"]}
    state["data"] = data
    state["privateSql"] = job(azure, state, "private-sql", foundation["setupIdentity"], {
        **data, "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": foundation["setupIdentity"]["clientId"],
    }, "private_sql_verified")
    save_state(path, state)
    state["syntheticSetup"] = job(azure, state, "synthetic-setup", foundation["setupIdentity"], {
        **data, "BENEFITS_SETUP_MODE": "1",
        "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": foundation["setupIdentity"]["clientId"],
        "BENEFITS_RUNTIME_SQL_CLIENT_ID": foundation["apiIdentity"]["clientId"],
    }, "synthetic_setup_complete")
    save_state(path, state)
    state["runtimeSources"] = job(azure, state, "runtime-sources", foundation["apiIdentity"], {
        **data, "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": foundation["apiIdentity"]["clientId"],
    }, "runtime_sources_verified")
    save_state(path, state)
    state["api"] = host(azure, state, "api", {
        **data, **caller, "BENEFITS_MANAGED_IDENTITY_CLIENT_ID": foundation["apiIdentity"]["clientId"],
    })
    web_variables = {**caller, "BENEFITS_SERVICE_URL": state["api"]["uri"],
                     "BENEFITS_APP_ORIGIN": "https://private-preflight.invalid"}
    private = host(azure, state, "web", web_variables)
    web_variables["BENEFITS_APP_ORIGIN"] = private["uri"]
    host(azure, state, "web", web_variables)
    state["acceptance"] = job(azure, state, "cloud-acceptance", foundation["webIdentity"],
                              web_variables, "private_cloud_acceptance_complete")
    save_state(path, state)
    if ".internal." not in private["uri"]:
        raise DeploymentError("PRIVATE_FRONTEND_FQDN_REQUIRED_BEFORE_PUBLICATION")
    web_variables["BENEFITS_APP_ORIGIN"] = private["uri"].replace(".internal.", ".", 1)
    state["web"] = host(azure, state, "web", web_variables, public=True)
    if state["web"]["uri"] != web_variables["BENEFITS_APP_ORIGIN"]:
        host(azure, state, "web", web_variables, public=False)
        raise DeploymentError("UNEXPECTED_PUBLIC_ORIGIN_FRONTEND_RETURNED_TO_PRIVATE")
    try:
        state["publicAcceptance"] = job(azure, state, "cloud-acceptance", foundation["webIdentity"],
                                         web_variables, "private_cloud_acceptance_complete")
    except (RuntimeError, ValueError, KeyError, TypeError, OSError):
        host(azure, state, "web", web_variables, public=False)
        raise
    save_state(path, state)
    print(json.dumps({"status": "showcase_deployed", "url": state["web"]["uri"],
                      "environmentState": str(path.relative_to(ROOT)), "synthetic_only": True}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subscription", required=True)
    parser.add_argument("--environment", default="benefits-iq")
    parser.add_argument("--deploy", action="store_true", help="Perform approved staged Azure writes.")
    parser.add_argument("--phase", choices=("foundation", "full"), default="full",
                        help="Foundation stops after private managed-identity proof, before data/app services.")
    args = parser.parse_args()
    validate_environment(args.environment)
    azure = Azure(args.subscription)
    account, owner, scanner = preflight(azure)
    if not args.deploy:
        print(json.dumps({"status": "read_only_preflight_complete", "cloud_deployed": False}))
        return
    path = WORK / f"showcase-{args.environment}.json"
    lock = path.with_suffix(".lock")
    try:
        with lock.open("x", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
    except FileExistsError as error:
        raise DeploymentError("DEPLOYMENT_LOCK_EXISTS_RECONCILE_PRIOR_RUN_FIRST") from error
    try:
        path, state = load_state(azure, args.environment, canonical_guid(account["tenantId"]))
        deploy(azure, path, state, owner, scanner, foundation_only=args.phase == "foundation")
    finally:
        lock.unlink()


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, KeyError) as error:
        print(json.dumps({"status": "deployment_stopped", "code": str(error)
                          if isinstance(error, RuntimeError) else "INVALID_DEPLOYMENT_RESPONSE"}))
        raise SystemExit(1) from None
