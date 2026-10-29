import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from scripts import deploy


SUBSCRIPTION = "10000000-0000-0000-0000-000000000001"


def azure(monkeypatch, output):
    monkeypatch.setattr(deploy.shutil, "which", lambda _: "az")
    instance = deploy.Azure(SUBSCRIPTION)
    instance.text = Mock(return_value=output)
    return instance


def test_empty_patch_is_allowed_but_empty_read_is_not(monkeypatch, tmp_path):
    monkeypatch.setattr(deploy, "WORK", tmp_path)
    instance = azure(monkeypatch, "")
    assert instance.graph("PATCH", "/applications/example", body={"identifierUris": []}) is None
    with pytest.raises(deploy.DeploymentError, match="COMMAND_JSON_RESPONSE_INVALID"):
        instance.graph("GET", "/applications/example")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("sql_public", ["Disabled", "Enabled"])
@pytest.mark.parametrize("symbolic", [True, False])
def test_preflight_scopes_graph_me_but_not_global_extension_commands(monkeypatch, tmp_path, sql_public, symbolic):
    instance = Mock(subscription=SUBSCRIPTION, executable="az")
    instance.run.return_value = {"id": SUBSCRIPTION, "state": "Enabled",
                                 "environmentName": "AzureCloud", "user": {"type": "user"}}
    instance.graph.return_value = {"id": SUBSCRIPTION}
    scanner = tmp_path / "trivy.exe"
    scanner.touch()
    monkeypatch.setenv("BENEFITS_TRIVY", str(scanner))
    for key in ("AZURE_CLIENT_SECRET", "OPENAI_API_KEY", "BENEFITS_SERVICE_SECRET"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(deploy, "WORK", tmp_path)
    resource = {"type": "Microsoft.Sql/servers", "properties": {"publicNetworkAccess": sql_public}}
    (tmp_path / "data.compiled.json").write_text(json.dumps({
        "resources": {"sql": resource} if symbolic else [resource],
    }), encoding="utf-8")
    execute = Mock(return_value='{"name":"containerapp"}')
    monkeypatch.setattr(deploy, "command", execute)
    monkeypatch.setattr(deploy, "context_files", Mock())
    policy_check = Mock()
    monkeypatch.setattr(deploy, "policy_preflight", policy_check)
    if sql_public != "Disabled":
        with pytest.raises(deploy.DeploymentError, match="UNCONDITIONAL_PRIVATE_SQL_TEMPLATE_REQUIRED"):
            deploy.preflight(instance)
        policy_check.assert_not_called()
        instance.graph.assert_not_called()
        return
    account, owner, path = deploy.preflight(instance)
    policy_check.assert_called_once_with(instance, private_sql=True)
    instance.graph.assert_called_once_with("GET", "/me", query={"$select": "id"})
    assert owner == SUBSCRIPTION and path == str(scanner)
    assert execute.call_args.args[0][:5] == ["az", "extension", "show", "--name", "containerapp"]
    assert "--subscription" not in execute.call_args.args[0]


def test_policy_preflight_reads_ancestors_and_stops_on_nested_sql_control():
    instance = Mock(subscription=SUBSCRIPTION)
    scope = "/providers/Microsoft.Management/managementGroups/synthetic-governance"
    parent = scope + "/providers/Microsoft.Authorization/policySetDefinitions/parent"
    child = scope + "/providers/Microsoft.Authorization/policySetDefinitions/child"
    sql = scope + "/providers/Microsoft.Authorization/policyDefinitions/AzureSQL_PublicNetwork_Modify"
    instance.run.side_effect = [
        {"value": [{"properties": {"scope": scope, "policyDefinitionId": parent}}]},
        {"properties": {"policyDefinitions": [{"policyDefinitionId": child}]}},
        {"properties": {"policyDefinitions": [{"policyDefinitionId": sql}]}},
    ]
    with pytest.raises(deploy.DeploymentError, match="INHERITED_SQL_NETWORK_POLICY_REVIEW_REQUIRED"):
        deploy.policy_preflight(instance)
    first = instance.run.call_args_list[0].args
    assert first[4] == (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION}"
        "/providers/Microsoft.Authorization/policyAssignments")
    assert "--url-parameters" in first and "api-version=2023-04-01" in first
    assert "--scope" not in first


def test_policy_preflight_handles_unenforced_assignments_and_initiative_cycles():
    instance = Mock(subscription=SUBSCRIPTION)
    root = "/providers/Microsoft.Authorization/"
    initiative = root + "policySetDefinitions/synthetic-cycle"
    instance.run.side_effect = [
        {"value": [
            {"properties": {"enforcementMode": "DoNotEnforce",
                            "policyDefinitionId": root + "policyDefinitions/AzureSQL_PublicNetwork_Modify"}},
            {"properties": {"policyDefinitionId": initiative}},
        ]},
        {"properties": {"policyDefinitions": [{"policyDefinitionId": initiative}]}},
    ]
    deploy.policy_preflight(instance)
    assert instance.run.call_count == 2


@pytest.mark.parametrize("response", [
    {}, {"value": None}, {"value": [None]}, {"value": [{}]},
    {"value": [], "nextLink": "https://management.azure.com/more"},
])
def test_policy_preflight_does_not_treat_partial_inventory_as_absence(response):
    instance = Mock(subscription=SUBSCRIPTION)
    instance.run.return_value = response
    with pytest.raises(deploy.DeploymentError, match="EFFECTIVE_POLICY_"):
        deploy.policy_preflight(instance)


def test_policy_preflight_surfaces_denied_reads_and_malformed_initiatives():
    instance = Mock(subscription=SUBSCRIPTION)
    instance.run.side_effect = deploy.DeploymentError("AZ_REST_AuthorizationFailed")
    with pytest.raises(deploy.DeploymentError, match="AZ_REST_AuthorizationFailed"):
        deploy.policy_preflight(instance)
    instance.run.side_effect = [
        {"value": [{"properties": {"policyDefinitionId":
                                   "/providers/Microsoft.Authorization/policySetDefinitions/synthetic"}}]},
        {},
    ]
    with pytest.raises(deploy.DeploymentError, match="EFFECTIVE_POLICY_INITIATIVE_RESPONSE_INVALID"):
        deploy.policy_preflight(instance)


def test_known_modifier_is_compatible_only_with_explicit_private_sql_topology():
    instance = Mock(subscription=SUBSCRIPTION)
    instance.run.return_value = {"value": [{"properties": {"policyDefinitionId":
        "/providers/Microsoft.Authorization/policyDefinitions/AzureSQL_PublicNetwork_Modify"}}]}
    deploy.policy_preflight(instance, private_sql=True)
    with pytest.raises(deploy.DeploymentError, match="INHERITED_SQL_NETWORK_POLICY_REVIEW_REQUIRED"):
        deploy.policy_preflight(instance)


def test_state_replace_is_atomic_and_leaves_no_temporary_file(monkeypatch, tmp_path):
    monkeypatch.setattr(deploy, "WORK", tmp_path)
    path = tmp_path / "state.json"
    deploy.save_state(path, {"phase": 1})
    deploy.save_state(path, {"phase": 2})
    assert json.loads(path.read_text()) == {"phase": 2}
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("attached", [True, False])
def test_only_owned_sql_endpoints_azure_generated_nic_can_be_untagged(attached):
    instance = Mock(subscription=SUBSCRIPTION)
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION}
    base, group = deploy.names(state)
    endpoint_id = (f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{group}"
                   f"/providers/Microsoft.Network/privateEndpoints/pe-sql-{base}")
    nic_id = (f"/subscriptions/{SUBSCRIPTION}/resourceGroups/{group}"
              "/providers/Microsoft.Network/networkInterfaces/generated")
    instance.run.side_effect = [
        True, {"location": "canadaeast", "tags": deploy.tags(state)},
        [{"id": endpoint_id, "type": "Microsoft.Network/privateEndpoints", "tags": deploy.tags(state)},
         {"id": nic_id, "type": "Microsoft.Network/networkInterfaces"}],
        {"networkInterfaces": [{"id": nic_id if attached else nic_id + "-foreign"}]},
    ]
    if attached:
        deploy.verify_ownership(instance, state)
    else:
        with pytest.raises(deploy.DeploymentError, match="UNOWNED_RESOURCE_IN_DEDICATED_GROUP"):
            deploy.verify_ownership(instance, state)


@pytest.mark.parametrize("name", ["../outside", "Aaa", "ab", "a--b", "a" * 12, "ends-"])
def test_environment_cannot_escape_state_directory(name):
    with pytest.raises(deploy.DeploymentError, match="ENVIRONMENT_REQUIRES"):
        deploy.validate_environment(name)


def report(image):
    return {"SchemaVersion": 2, "ArtifactType": "container_image",
            "Metadata": {"RepoDigests": [image]},
            "Results": [{"Class": "os-pkgs"}, {"Class": "lang-pkgs"}]}


def test_scan_must_be_complete_and_bound_to_the_actual_image():
    image = "synthetic.azurecr.io/benefits-api@sha256:" + "a" * 64
    assert deploy.scan_findings(report(image), image) == []
    for invalid in ({}, report("another-image"), {**report(image), "Results": []},
                    {**report(image), "ArtifactType": "filesystem"}):
        with pytest.raises(deploy.DeploymentError, match="EXACT_IMAGE_SCAN_REQUIRED"):
            deploy.scan_findings(invalid, image)
    finding = {"VulnerabilityID": "synthetic-test-id", "Severity": "HIGH"}
    value = report(image)
    value["Results"][0]["Vulnerabilities"] = [finding]
    assert deploy.scan_findings(value, image) == [finding]
    value["Results"][0] = {"Class": "os-pkgs", "Secrets": [{"RuleID": "synthetic-rule"}]}
    assert deploy.scan_findings(value, image) == [{"RuleID": "synthetic-rule"}]
    value["Results"][0] = {"Class": "os-pkgs", "Vulnerabilities": [{"Severity": "LOW"}]}
    assert deploy.scan_findings(value, image) == []
    value["Results"][1]["Vulnerabilities"] = [{"Severity": "MEDIUM"}]
    assert deploy.scan_findings(value, image) == [{"Severity": "MEDIUM"}]


def test_build_reads_committed_bytes_not_mutable_worktree(monkeypatch):
    execute = Mock(return_value=SimpleNamespace(returncode=0, stdout=b"committed source"))
    monkeypatch.setattr(deploy.subprocess, "run", execute)
    assert deploy.committed_content(Path("service") / "app.py") == b"committed source"
    assert execute.call_args.args[0] == ["git", "show", "HEAD:service/app.py"]
    execute.return_value.returncode = 1
    with pytest.raises(deploy.DeploymentError, match="COMMITTED_BUILD_SOURCE_UNAVAILABLE"):
        deploy.committed_content(Path("service") / "app.py")


def test_scanner_uses_only_an_ephemeral_exact_registry_token_after_public_database_update(monkeypatch):
    instance = Mock()
    endpoint = "synthetic.azurecr.io"
    instance.run.return_value = {"loginServer": endpoint, "accessToken": "synthetic-ephemeral-token"}
    image = endpoint + "/benefits-api@sha256:" + "a" * 64
    state = {"foundation": {"registryName": "synthetic", "registryEndpoint": endpoint}}
    execute = Mock(side_effect=["", json.dumps(report(image))])
    monkeypatch.setattr(deploy, "command", execute)
    monkeypatch.setenv("TRIVY_PASSWORD", "synthetic-unrelated-credential")
    assert deploy.scan_image(instance, state, image, "trivy") == []
    database, scan = execute.call_args_list
    assert "--download-db-only" in database.args[0]
    assert "TRIVY_PASSWORD" not in database.kwargs["env"]
    assert scan.kwargs["env"]["TRIVY_PASSWORD"] == "synthetic-ephemeral-token"
    assert "--skip-db-update" in scan.args[0] and "--skip-java-db-update" in scan.args[0]
    assert not any("synthetic-ephemeral-token" in argument for argument in scan.args[0])
    assert "synthetic-ephemeral-token" not in json.dumps(state)
    instance.run.return_value["loginServer"] = "another.azurecr.io"
    execute.reset_mock(side_effect=True)
    execute.side_effect = [""]
    with pytest.raises(deploy.DeploymentError, match="EXACT_REGISTRY_SHORT_LIVED_TOKEN_REQUIRED"):
        deploy.scan_image(instance, state, image, "trivy")
    assert execute.call_count == 1


def test_build_context_requires_agent_definitions_without_including_arbitrary_documents(monkeypatch, tmp_path):
    expected = [*deploy.ROOT_CONTEXT]
    for folder, names in (("infra", deploy.INFRA_CONTEXT), ("tests", deploy.IMAGE_TESTS),
                          ("agents", deploy.AGENT_CONTEXT)):
        expected.extend(str(Path(folder) / name) for name in names)
    excluded = [str(Path(folder) / name) for folder, name in (
        ("agents", "private-notes.md"), ("service", "private-notes.md"),
        ("app", "attachment.docx"), ("app", "attachment.pdf"))]
    execute = Mock(side_effect=["\0".join([*expected, *excluded]), ""])
    monkeypatch.setattr(deploy, "ROOT", tmp_path)
    monkeypatch.setattr(deploy, "command", execute)
    files = deploy.context_files()
    assert Path("agents") / "orchestrator.md" in files
    assert set(files) == {Path(name) for name in expected}
    execute.side_effect = ["\0".join(name for name in expected
                                   if Path(name).name != "orchestrator.md")]
    with pytest.raises(deploy.DeploymentError, match="COMMITTED_BUILD_CONTEXT_INCOMPLETE"):
        deploy.context_files()


@pytest.mark.parametrize("purpose,receipt", [
    ("identity-proof", {"token_exposed": False, "data_services_exercised": False,
                        "negative_checks": ["api_client_id", "runtime_client_id",
                                            "runtime_principal_id", "tenant_id"]}),
    ("synthetic-setup", {"source_records": 12, "documents": 12, "criteria": 4, "aggregate_cells": 6}),
    ("cloud-acceptance", {"clinical_decision_submitted": False, "workflow_write_exercised": True,
                          "checks": ["real_model_agui_stream", "required_case_bound_read_tools", "chat_read_only",
                                     "selected_view_shapes", "direct_upload_send_create_rejection"]}),
])
def test_job_receipt_requires_proof_fields_not_a_status_substring(purpose, receipt):
    assert deploy.valid_receipt(purpose, receipt)
    if purpose == "cloud-acceptance":
        assert not deploy.valid_receipt(purpose, {
            **receipt, "checks": [check for check in receipt["checks"] if check != "required_case_bound_read_tools"]})
    assert not deploy.valid_receipt(purpose, {"status": "looks successful"})
    assert not deploy.valid_receipt(purpose, {})


def test_resource_collision_stops_before_registration_or_provisioning(monkeypatch):
    verify = Mock(side_effect=deploy.DeploymentError("RESOURCE_GROUP_OWNERSHIP_COLLISION"))
    register = Mock()
    monkeypatch.setattr(deploy, "verify_ownership", verify)
    monkeypatch.setattr(deploy, "ensure_resource_api", register)
    with pytest.raises(deploy.DeploymentError, match="OWNERSHIP_COLLISION"):
        deploy.deploy(Mock(), Path("unused"), {}, "owner", "scanner")
    register.assert_not_called()


def test_failed_identity_proof_never_creates_expensive_data_services(monkeypatch, tmp_path):
    instance = Mock()
    instance.run.return_value = False
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    monkeypatch.setattr(deploy, "ensure_resource_api", Mock(return_value={"clientId": "api"}))
    template = Mock(return_value={"foundation": {"webIdentity": {
        "clientId": "web", "principalId": "web-principal"}}})
    monkeypatch.setattr(deploy, "deploy_template", template)
    monkeypatch.setattr(deploy, "build_image", Mock(return_value="digest"))
    monkeypatch.setattr(deploy, "save_state", Mock())
    monkeypatch.setattr(deploy, "job", Mock(side_effect=deploy.DeploymentError("PROOF_FAILED")))
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION, "tenant": SUBSCRIPTION}
    with pytest.raises(deploy.DeploymentError, match="PROOF_FAILED"):
        deploy.deploy(instance, tmp_path / "state.json", state, "owner", "scanner")
    assert [call.args[2] for call in template.call_args_list] == ["foundation"]


def test_rerun_retracts_existing_public_frontend_before_changing_dependencies(monkeypatch, tmp_path):
    instance = Mock()
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION}
    instance.run.side_effect = [True, [{"name": "web-" + deploy.names(state)[0]}], {}]
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    registration = Mock(side_effect=deploy.DeploymentError("REGISTRATION_STOP"))
    monkeypatch.setattr(deploy, "ensure_resource_api", registration)
    with pytest.raises(deploy.DeploymentError, match="REGISTRATION_STOP"):
        deploy.deploy(instance, tmp_path / "state.json", state, "owner", "scanner")
    ingress = instance.run.call_args.args
    assert ingress[:3] == ("containerapp", "ingress", "enable")
    assert ingress[ingress.index("--type") + 1] == "internal"
    assert ingress[ingress.index("--allow-insecure") + 1] == "false"


def test_provider_validation_precedes_every_resource_write(monkeypatch):
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    monkeypatch.setattr(deploy, "WORK", deploy.ROOT / ".azure")
    instance = Mock()
    instance.run.side_effect = [{}, {"status": "Succeeded", "changes": []}, {"properties": {
        "provisioningState": "Succeeded", "outputs": {"verified": {"value": True}},
    }}]
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION}
    assert deploy.deploy_template(instance, state, "job", {}) == {"verified": True}
    calls = instance.run.call_args_list
    assert calls[0].args[:3] == ("deployment", "group", "validate")
    assert calls[1].args[:3] == ("deployment", "group", "what-if")
    assert calls[2].args[:3] == ("deployment", "group", "create")
    instance.run.reset_mock(side_effect=True)
    instance.run.side_effect = deploy.DeploymentError("RequestDisallowedByPolicy")
    with pytest.raises(deploy.DeploymentError, match="RequestDisallowedByPolicy"):
        deploy.deploy_template(instance, state, "job", {})
    assert instance.run.call_count == 1


def test_resource_deletions_in_preview_stop_before_create(monkeypatch):
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    instance = Mock()
    instance.run.side_effect = [
        {}, {"status": "Succeeded", "changes": [{"changeType": "Delete"}]},
    ]
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION}
    with pytest.raises(deploy.DeploymentError, match="RESOURCE_DELETION_NOT_APPROVED"):
        deploy.deploy_template(instance, state, "network", {})
    assert instance.run.call_count == 2


def test_foundation_phase_stops_before_data_or_public_apps(monkeypatch, capsys):
    instance = Mock()
    instance.run.return_value = False
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    monkeypatch.setattr(deploy, "ensure_resource_api", Mock(return_value={"clientId": "api"}))
    template = Mock(return_value={"foundation": {"webIdentity": {
        "clientId": "web", "principalId": "web-principal"}}})
    monkeypatch.setattr(deploy, "deploy_template", template)
    build = Mock(return_value="digest")
    monkeypatch.setattr(deploy, "build_image", build)
    monkeypatch.setattr(deploy, "save_state", Mock())
    monkeypatch.setattr(deploy, "job", Mock(return_value={"verified": True}))
    host = Mock()
    monkeypatch.setattr(deploy, "host", host)
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION, "tenant": SUBSCRIPTION}
    deploy.deploy(instance, deploy.WORK / "test-state.json", state, "owner", "scanner", foundation_only=True)
    assert [call.args[2] for call in template.call_args_list] == ["foundation"]
    assert [call.args[2] for call in build.call_args_list] == ["api", "web"]
    host.assert_not_called()
    assert json.loads(capsys.readouterr().out)["cloud_application_deployed"] is False


def test_full_deploy_requires_private_sql_receipt_before_seeding_or_app_hosting(monkeypatch, tmp_path):
    instance = Mock()
    sql_id = "/subscriptions/" + SUBSCRIPTION + "/resourceGroups/synthetic/providers/Microsoft.Sql/servers/synthetic"
    instance.run.side_effect = [
        False, {"id": sql_id, "publicNetworkAccess": "Disabled"},
        {"properties": {"azureADOnlyAuthentication": True}},
        {"privateLinkServiceConnections": [{"privateLinkServiceId": sql_id, "groupIds": ["sqlServer"],
                                           "privateLinkServiceConnectionState": {"status": "Approved"}}]},
    ]
    identity = {"name": "synthetic", "clientId": "client", "principalId": "principal",
                "resourceId": "identity"}
    foundation = {"webIdentity": identity, "apiIdentity": identity, "setupIdentity": identity,
                  "logsResourceId": "logs"}
    network = {"environmentName": "vnet-environment", "environmentResourceId": "private-environment",
               "sqlEndpointResourceId": "private-endpoint", "sqlPrivateCidr": "10.84.0.32/27"}
    monkeypatch.setattr(deploy, "verify_ownership", Mock())
    monkeypatch.setattr(deploy, "ensure_resource_api", Mock(return_value={"clientId": "audience"}))
    template = Mock(side_effect=[
        {"foundation": foundation}, {"environmentVariables": {"BENEFITS_SQL_SERVER": "synthetic.database.windows.net"}},
        {"network": network},
    ])
    monkeypatch.setattr(deploy, "deploy_template", template)
    monkeypatch.setattr(deploy, "build_image", Mock(return_value="digest"))
    monkeypatch.setattr(deploy, "save_state", Mock())
    proof = Mock(side_effect=[{"verified": True}, deploy.DeploymentError("PRIVATE_SQL_PROOF_STOPPED")])
    monkeypatch.setattr(deploy, "job", proof)
    hosting = Mock()
    monkeypatch.setattr(deploy, "host", hosting)
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION, "tenant": SUBSCRIPTION}
    with pytest.raises(deploy.DeploymentError, match="PRIVATE_SQL_PROOF_STOPPED"):
        deploy.deploy(instance, tmp_path / "state.json", state, "owner", "scanner")
    assert [call.args[2] for call in template.call_args_list] == ["foundation", "data", "network"]
    assert [call.args[2] for call in proof.call_args_list] == ["identity-proof", "private-sql"]
    assert proof.call_args.args[4]["BENEFITS_SQL_PRIVATE_CIDR"] == network["sqlPrivateCidr"]
    hosting.assert_not_called()


def test_private_jobs_use_new_environment_without_mutating_original_proof_job(monkeypatch):
    template = Mock(side_effect=deploy.DeploymentError("BEFORE_JOB_WRITE"))
    monkeypatch.setattr(deploy, "deploy_template", template)
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION, "apiImage": "digest",
             "foundation": {"environmentResourceId": "original", "registryEndpoint": "registry"},
             "network": {"environmentResourceId": "private"}}
    with pytest.raises(deploy.DeploymentError, match="BEFORE_JOB_WRITE"):
        deploy.job(Mock(), state, "private-sql", {"resourceId": "identity"}, {}, "private_sql_verified")
    parameters = template.call_args.args[3]
    assert parameters["environmentResourceId"] == "private" and parameters["name"].startswith("n-q-")
    with pytest.raises(deploy.DeploymentError, match="BEFORE_JOB_WRITE"):
        deploy.job(Mock(), state, "identity-proof", {"resourceId": "identity"}, {}, "managed_identity_caller_verified")
    parameters = template.call_args.args[3]
    assert parameters["environmentResourceId"] == "original" and parameters["name"].startswith("p-")


def test_job_receipt_is_bound_to_actual_execution_image(monkeypatch):
    monkeypatch.setattr(deploy, "deploy_template", Mock())
    instance = Mock()
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION, "apiImage": "sha256:" + "a" * 64,
             "foundation": {"environmentResourceId": "environment", "registryEndpoint": "synthetic.azurecr.io"}}
    expected_image = "synthetic.azurecr.io/benefits-api@" + state["apiImage"]
    execution = {"properties": {"status": "Succeeded", "template": {"containers": [
        {"name": "governed-job", "image": expected_image},
    ]}}}
    receipt = {"status": "managed_identity_caller_verified", "token_exposed": False,
               "data_services_exercised": False, "negative_checks": [
                   "api_client_id", "runtime_client_id", "runtime_principal_id", "tenant_id"]}
    instance.run.side_effect = [{"name": "execution-1"}, execution]
    instance.text.return_value = "2026-10-29T14:37:46.6513296Z stdout F " + json.dumps(receipt)
    result = deploy.job(instance, state, "identity-proof", {"resourceId": "identity"}, {},
                        "managed_identity_caller_verified")
    assert result["receipt"] == receipt and result["image"] == state["apiImage"]
    assert "governed-job" in instance.text.call_args.args
    assert instance.text.call_args.args[instance.text.call_args.args.index("--format") + 1] == "text"
    execution["properties"]["template"]["containers"][0]["image"] = "wrong-image"
    instance.run.side_effect = [{"name": "execution-2"}, execution]
    with pytest.raises(deploy.DeploymentError, match="IMAGE_MISMATCH"):
        deploy.job(instance, state, "identity-proof", {"resourceId": "identity"}, {},
                   "managed_identity_caller_verified")


@pytest.mark.parametrize("framing", ["unframed", "stderr", "partial", "duplicate", "embedded"])
def test_job_receipt_rejects_partial_unstructured_or_spoofed_log_records(framing):
    receipt = {"status": "managed_identity_caller_verified", "token_exposed": False,
               "data_services_exercised": False, "negative_checks": [
                   "api_client_id", "runtime_client_id", "runtime_principal_id", "tenant_id"]}
    payload = json.dumps(receipt)
    valid = "2026-10-29T14:37:46.6513296Z stdout F " + payload
    invalid = {
        "unframed": payload,
        "stderr": valid.replace("stdout", "stderr"),
        "partial": valid.replace("stdout F ", "stdout P "),
        "duplicate": valid + "\n" + valid,
        "embedded": "2026-10-29T14:37:46Z stdout F " + json.dumps({"message": payload}),
    }
    with pytest.raises(deploy.DeploymentError, match="VALID_COMPLETE_RECEIPT_REQUIRED"):
        deploy.job_receipt(invalid[framing], "identity-proof", receipt["status"])
