targetScope = 'resourceGroup'

@minLength(3)
@maxLength(32)
param name string
@allowed(['canadaeast'])
param location string = 'canadaeast'
param tags object
param environmentName string
param registryName string
param identityName string
param identityResourceId string
param identityPrincipalId string
@allowed(['web', 'api'])
param component string
@minLength(71)
@maxLength(71)
param imageDigest string
param environmentVariables object
param publicFrontend bool = false

var port = component == 'api' ? 8000 : 3000
var fixedEnvironment = union(environmentVariables, {
  BENEFITS_PROFILE: 'showcase'
  OTEL_SDK_DISABLED: 'true'
  NEXT_TELEMETRY_DISABLED: '1'
})

module app 'br/public:avm/ptn/azd/acr-container-app:0.5.0' = {
  name: 'benefits-iq-${component}'
  params: {
    name: name
    location: location
    tags: tags
    containerAppsEnvironmentName: environmentName
    containerRegistryName: registryName
    identityName: identityName
    identityType: 'UserAssigned'
    userAssignedIdentityResourceId: identityResourceId
    principalId: identityPrincipalId
    imageName: '${registryName}.azurecr.io/benefits-${component}@${imageDigest}'
    env: [for entry in items(fixedEnvironment): { name: entry.key, value: string(entry.value) }]
    containerMinReplicas: 1
    containerMaxReplicas: 1
    containerCpuCoreCount: '0.5'
    containerMemory: '1Gi'
    ingressEnabled: true
    ingressAllowInsecure: false
    external: component == 'web' && publicFrontend
    targetPort: port
    revisionMode: 'Single'
    containerProbes: [
      { type: 'Startup', tcpSocket: { port: port }, periodSeconds: 5, failureThreshold: 10 }
      { type: 'Liveness', tcpSocket: { port: port }, periodSeconds: 30, failureThreshold: 3 }
      { type: 'Readiness', tcpSocket: { port: port }, periodSeconds: 10, failureThreshold: 3 }
    ]
    enableTelemetry: false
  }
}

output resourceId string = app.outputs.resourceId
output uri string = app.outputs.uri
