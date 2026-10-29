targetScope = 'subscription'

@minLength(3)
@maxLength(11)
param environmentName string

@minLength(36)
@maxLength(36)
param environmentId string

@allowed(['canadaeast'])
param location string = 'canadaeast'

var suffix = take(replace(environmentId, '-', ''), 12)
var name = 'biq-${environmentName}-${suffix}'
var tags = {
  'azd-env-name': environmentName
  'benefits-iq-environment-id': environmentId
  'benefits-iq-profile': 'showcase'
  'data-classification': 'synthetic-only'
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2025-04-01' = {
  name: 'rg-${name}'
  location: location
  tags: tags
}

module foundation './modules/foundation.bicep' = {
  name: 'benefits-iq-foundation'
  scope: resourceGroup
  params: {
    name: name
    location: location
    tags: tags
  }
}

output AZURE_RESOURCE_GROUP string = resourceGroup.name
output foundation object = {
  registryName: foundation.outputs.registryName
  registryEndpoint: foundation.outputs.registryEndpoint
  environmentName: foundation.outputs.environmentName
  environmentResourceId: foundation.outputs.environmentResourceId
  logsResourceId: foundation.outputs.logsResourceId
  webIdentity: foundation.outputs.webIdentity
  apiIdentity: foundation.outputs.apiIdentity
  setupIdentity: foundation.outputs.setupIdentity
}
