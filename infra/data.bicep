targetScope = 'resourceGroup'

param name string
@allowed(['canadaeast'])
param location string = 'canadaeast'
param tags object
param setupIdentityName string
param setupPrincipalId string
param apiPrincipalId string

// Keep SQL unconditionally Entra-only; no password-auth template parameters.
resource sql 'Microsoft.Sql/servers@2025-01-01' = {
  name: 'sql-${name}'
  location: location
  tags: tags
  properties: {
    version: '12.0'
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
    administrators: {
      administratorType: 'ActiveDirectory'
      principalType: 'Application'
      login: setupIdentityName
      sid: setupPrincipalId
      tenantId: subscription().tenantId
      azureADOnlyAuthentication: true
    }
  }
}

resource database 'Microsoft.Sql/servers/databases@2025-01-01' = {
  parent: sql
  name: 'benefits'
  location: location
  tags: tags
  sku: { name: 'GP_S_Gen5', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    autoPauseDelay: 60
    minCapacity: json('0.5')
    maxSizeBytes: 34359738368
    requestedBackupStorageRedundancy: 'Local'
    zoneRedundant: false
    readScale: 'Disabled'
  }
}

resource retention 'Microsoft.Sql/servers/databases/backupShortTermRetentionPolicies@2025-01-01' = {
  parent: database
  name: 'default'
  properties: { retentionDays: 7 }
}

resource azureFirewall 'Microsoft.Sql/servers/firewallRules@2025-01-01' = {
  parent: sql
  name: 'AzureServicesWithEntraAuthentication'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

module search 'br/public:avm/res/search/search-service:0.13.0' = {
  name: 'governed-search'
  params: {
    name: 'srch-${name}'
    location: location
    tags: tags
    sku: 'basic'
    replicaCount: 1
    partitionCount: 1
    semanticSearch: 'disabled'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    roleAssignments: [
      { principalId: apiPrincipalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'Search Index Data Reader' }
      { principalId: setupPrincipalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'Search Service Contributor' }
      { principalId: setupPrincipalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'Search Index Data Contributor' }
    ]
    enableTelemetry: false
  }
}

module document 'br/public:avm/res/cognitive-services/account:0.19.1' = {
  name: 'document-intelligence'
  params: {
    name: 'doc-${name}'
    customSubDomainName: 'doc-${name}'
    kind: 'FormRecognizer'
    location: 'canadacentral'
    tags: tags
    sku: 'S0'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: true
    roleAssignments: [
      { principalId: apiPrincipalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'Cognitive Services User' }
    ]
    enableTelemetry: false
  }
}

module model 'br/public:avm/res/cognitive-services/account:0.19.1' = {
  name: 'canadian-regional-inference'
  params: {
    name: 'aoai-${name}'
    customSubDomainName: 'aoai-${name}'
    kind: 'OpenAI'
    location: location
    tags: tags
    sku: 'S0'
    disableLocalAuth: true
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: true
    deployments: [
      {
        name: 'benefits-chat'
        model: { format: 'OpenAI', name: 'gpt-4.1-mini', version: '2025-04-14' }
        sku: { name: 'Standard', capacity: 20 }
        versionUpgradeOption: 'NoAutoUpgrade'
      }
    ]
    roleAssignments: [
      { principalId: apiPrincipalId, principalType: 'ServicePrincipal', roleDefinitionIdOrName: 'Cognitive Services OpenAI User' }
    ]
    enableTelemetry: false
  }
}

output environmentVariables object = {
  BENEFITS_SQL_SERVER: sql.properties.fullyQualifiedDomainName
  BENEFITS_SQL_DATABASE: database.name
  BENEFITS_SEARCH_ENDPOINT: search.outputs.endpoint
  BENEFITS_SEARCH_INDEX: 'benefits-criteria'
  BENEFITS_DOCUMENT_ENDPOINT: document.outputs.endpoint
  BENEFITS_DOCUMENT_REGION: 'canadacentral'
  BENEFITS_MODEL_ENDPOINT: model.outputs.endpoint
  BENEFITS_MODEL_DEPLOYMENT: 'benefits-chat'
  BENEFITS_MODEL_REGION: location
  BENEFITS_MODEL_TYPE: 'Standard'
  BENEFITS_MODEL_NAME: 'gpt-4.1-mini'
  BENEFITS_MODEL_VERSION: '2025-04-14'
}
