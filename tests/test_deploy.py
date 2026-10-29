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


def test_preflight_scopes_graph_me_but_not_global_extension_commands(monkeypatch, tmp_path):
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
    execute = Mock(return_value='{"name":"containerapp"}')
    monkeypatch.setattr(deploy, "command", execute)
    monkeypatch.setattr(deploy, "context_files", Mock())
    account, owner, path = deploy.preflight(instance)
    instance.graph.assert_called_once_with("GET", "/me", query={"$select": "id"})
    assert owner == SUBSCRIPTION and path == str(scanner)
    assert execute.call_args.args[0][:5] == ["az", "extension", "show", "--name", "containerapp"]
    assert "--subscription" not in execute.call_args.args[0]


def test_state_replace_is_atomic_and_leaves_no_temporary_file(monkeypatch, tmp_path):
    monkeypatch.setattr(deploy, "WORK", tmp_path)
    path = tmp_path / "state.json"
    deploy.save_state(path, {"phase": 1})
    deploy.save_state(path, {"phase": 2})
    assert json.loads(path.read_text()) == {"phase": 2}
    assert list(tmp_path.iterdir()) == [path]


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
                          "checks": ["real_model_agui_stream", "chat_read_only",
                                     "selected_view_shapes", "direct_upload_send_create_rejection"]}),
])
def test_job_receipt_requires_proof_fields_not_a_status_substring(purpose, receipt):
    assert deploy.valid_receipt(purpose, receipt)
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
    instance.run.side_effect = [{}, {"properties": {
        "provisioningState": "Succeeded", "outputs": {"verified": {"value": True}},
    }}]
    state = {"environment": "synthetic", "environmentId": SUBSCRIPTION}
    assert deploy.deploy_template(instance, state, "job", {}) == {"verified": True}
    calls = instance.run.call_args_list
    assert calls[0].args[:3] == ("deployment", "group", "validate")
    assert calls[1].args[:3] == ("deployment", "group", "create")
    instance.run.reset_mock(side_effect=True)
    instance.run.side_effect = deploy.DeploymentError("RequestDisallowedByPolicy")
    with pytest.raises(deploy.DeploymentError, match="RequestDisallowedByPolicy"):
        deploy.deploy_template(instance, state, "job", {})
    assert instance.run.call_count == 1


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
    instance.text.return_value = json.dumps({"Log": json.dumps(receipt)})
    result = deploy.job(instance, state, "identity-proof", {"resourceId": "identity"}, {},
                        "managed_identity_caller_verified")
    assert result["receipt"] == receipt and result["image"] == state["apiImage"]
    assert "governed-job" in instance.text.call_args.args
    execution["properties"]["template"]["containers"][0]["image"] = "wrong-image"
    instance.run.side_effect = [{"name": "execution-2"}, execution]
    with pytest.raises(deploy.DeploymentError, match="IMAGE_MISMATCH"):
        deploy.job(instance, state, "identity-proof", {"resourceId": "identity"}, {},
                   "managed_identity_caller_verified")
