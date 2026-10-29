targetScope = 'resourceGroup'

@minLength(3)
@maxLength(32)
param name string

@allowed(['canadaeast'])
param location string = 'canadaeast'
param tags object
param environmentResourceId string
param identityResourceId string
param registryEndpoint string

@minLength(71)
@maxLength(71)
param imageDigest string

@allowed(['identity-proof', 'private-sql', 'synthetic-setup', 'runtime-sources', 'cloud-acceptance'])
param purpose string
param environmentVariables object

var commands = {
  'identity-proof': 'service.identity_probe'
  'private-sql': 'service.sql_network_probe'
  'synthetic-setup': 'service.cloud_seed'
  'runtime-sources': 'service.cloud_source_probe'
  'cloud-acceptance': 'service.cloud_acceptance'
}
var fixedEnvironment = union(environmentVariables, {
  BENEFITS_PROFILE: 'showcase'
  OTEL_SDK_DISABLED: 'true'
})

module job 'br/public:avm/res/app/job:0.7.2' = {
  name: 'benefits-iq-${purpose}'
  params: {
    name: name
    location: location
    tags: tags
    environmentResourceId: environmentResourceId
    managedIdentities: { userAssignedResourceIds: [identityResourceId] }
    registries: [{ server: registryEndpoint, identity: identityResourceId }]
    triggerType: 'Manual'
    manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
    replicaRetryLimit: 0
    replicaTimeout: purpose == 'identity-proof' ? 120 : 900
    containers: [
      {
        name: 'governed-job'
        image: '${registryEndpoint}/benefits-api@${imageDigest}'
        command: ['python', '-m', commands[purpose]]
        env: [for entry in items(fixedEnvironment): { name: entry.key, value: string(entry.value) }]
        resources: { cpu: '0.5', memory: '1Gi' }
      }
    ]
    enableTelemetry: false
  }
}

output jobName string = job.outputs.name
output jobResourceId string = job.outputs.resourceId
