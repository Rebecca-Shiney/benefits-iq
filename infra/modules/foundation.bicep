targetScope = 'resourceGroup'

param name string
param location string
param tags object

module webIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.6.0' = {
  name: 'web-identity'
  params: {
    name: 'id-web-${name}'
    location: location
    tags: tags
    enableTelemetry: false
  }
}

module apiIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.6.0' = {
  name: 'api-identity'
  params: {
    name: 'id-api-${name}'
    location: location
    tags: tags
    enableTelemetry: false
  }
}

module setupIdentity 'br/public:avm/res/managed-identity/user-assigned-identity:0.6.0' = {
  name: 'setup-identity'
  params: {
    name: 'id-setup-${name}'
    location: location
    tags: tags
    enableTelemetry: false
  }
}

module registry 'br/public:avm/res/container-registry/registry:0.13.1' = {
  name: 'registry'
  params: {
    name: replace('cr${name}', '-', '')
    location: location
    tags: tags
    acrSku: 'Basic'
    acrAdminUserEnabled: false
    anonymousPullEnabled: false
    roleAssignmentMode: 'LegacyRegistryPermissions'
    exportPolicyStatus: 'enabled'
    retentionPolicyStatus: 'disabled'
    zoneRedundancy: 'Disabled'
    publicNetworkAccess: 'Enabled'
    networkRuleSetDefaultAction: 'Allow'
    roleAssignments: [
      { principalId: webIdentity.outputs.principalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'AcrPull' }
      { principalId: apiIdentity.outputs.principalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'AcrPull' }
      { principalId: setupIdentity.outputs.principalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'AcrPull' }
    ]
    enableTelemetry: false
  }
}

module logs 'br/public:avm/res/operational-insights/workspace:0.16.1' = {
  name: 'logs'
  params: {
    name: 'law-${name}'
    location: location
    tags: tags
    skuName: 'PerGB2018'
    dataRetention: 30
    dailyQuotaGb: '0.1'
    forceCmkForQuery: false
    features: {
      disableLocalAuth: true
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    enableTelemetry: false
  }
}

module environment 'br/public:avm/res/app/managed-environment:0.16.0' = {
  name: 'environment'
  params: {
    name: 'cae-${name}'
    location: location
    tags: tags
    zoneRedundant: false
    publicNetworkAccess: 'Enabled'
    workloadProfiles: [
      { name: 'Consumption', workloadProfileType: 'Consumption' }
    ]
    appLogsConfiguration: { destination: 'azure-monitor' }
    diagnosticSettings: [
      {
        name: 'sanitized-container-logs'
        workspaceResourceId: logs.outputs.resourceId
        logCategoriesAndGroups: [
          { category: 'ContainerAppConsoleLogs' }
          { category: 'ContainerAppSystemLogs' }
        ]
      }
    ]
    enableTelemetry: false
  }
}

output registryName string = registry.outputs.name
output registryEndpoint string = registry.outputs.loginServer
output environmentName string = environment.outputs.name
output environmentResourceId string = environment.outputs.resourceId
output logsResourceId string = logs.outputs.resourceId
output webIdentity object = {
  name: webIdentity.outputs.name
  resourceId: webIdentity.outputs.resourceId
  clientId: webIdentity.outputs.clientId
  principalId: webIdentity.outputs.principalId
}
output apiIdentity object = {
  name: apiIdentity.outputs.name
  resourceId: apiIdentity.outputs.resourceId
  clientId: apiIdentity.outputs.clientId
  principalId: apiIdentity.outputs.principalId
}
output setupIdentity object = {
  name: setupIdentity.outputs.name
  resourceId: setupIdentity.outputs.resourceId
  clientId: setupIdentity.outputs.clientId
  principalId: setupIdentity.outputs.principalId
}
