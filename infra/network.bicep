targetScope = 'resourceGroup'

param name string
@allowed(['canadaeast'])
param location string = 'canadaeast'
param tags object
param logsResourceId string

var sqlPrivateCidr = '10.84.0.32/27'

resource sql 'Microsoft.Sql/servers@2025-01-01' existing = {
  name: 'sql-${name}'
}

resource network 'Microsoft.Network/virtualNetworks@2025-01-01' = {
  name: 'vnet-${name}'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.84.0.0/24'] }
    subnets: [
      {
        name: 'apps'
        properties: {
          addressPrefix: '10.84.0.0/27'
          delegations: [
            { name: 'container-apps', properties: { serviceName: 'Microsoft.App/environments' } }
          ]
        }
      }
      {
        name: 'private-sql'
        properties: {
          addressPrefix: sqlPrivateCidr
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
    ]
  }
}

resource zone 'Microsoft.Network/privateDnsZones@2024-06-01' = {
  name: 'privatelink${environment().suffixes.sqlServerHostname}'
  location: 'global'
  tags: tags
}

resource link 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2024-06-01' = {
  parent: zone
  name: 'sql-${name}'
  location: 'global'
  tags: tags
  properties: {
    registrationEnabled: false
    virtualNetwork: { id: network.id }
  }
}

resource endpoint 'Microsoft.Network/privateEndpoints@2025-01-01' = {
  name: 'pe-sql-${name}'
  location: location
  tags: tags
  properties: {
    subnet: { id: resourceId('Microsoft.Network/virtualNetworks/subnets', network.name, 'private-sql') }
    privateLinkServiceConnections: [
      {
        name: 'sql'
        properties: { privateLinkServiceId: sql.id, groupIds: ['sqlServer'] }
      }
    ]
  }
}

resource zoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2025-01-01' = {
  parent: endpoint
  name: 'sql'
  properties: {
    privateDnsZoneConfigs: [
      { name: 'sql', properties: { privateDnsZoneId: zone.id } }
    ]
  }
}

module appEnvironment 'br/public:avm/res/app/managed-environment:0.16.0' = {
  name: 'private-sql-environment'
  params: {
    name: 'cae-vnet-${name}'
    location: location
    tags: tags
    infrastructureSubnetResourceId: resourceId('Microsoft.Network/virtualNetworks/subnets', network.name, 'apps')
    infrastructureResourceGroupName: 'ME_vnet_${name}'
    internal: false
    zoneRedundant: false
    publicNetworkAccess: 'Enabled'
    workloadProfiles: [
      { name: 'Consumption', workloadProfileType: 'Consumption' }
    ]
    appLogsConfiguration: { destination: 'azure-monitor' }
    diagnosticSettings: [
      {
        name: 'sanitized-container-logs'
        workspaceResourceId: logsResourceId
        logCategoriesAndGroups: [
          { category: 'ContainerAppConsoleLogs' }
          { category: 'ContainerAppSystemLogs' }
        ]
      }
    ]
    enableTelemetry: false
  }
  dependsOn: [link, zoneGroup]
}

output network object = {
  environmentName: appEnvironment.outputs.name
  environmentResourceId: appEnvironment.outputs.resourceId
  virtualNetworkResourceId: network.id
  sqlEndpointResourceId: endpoint.id
  sqlPrivateCidr: sqlPrivateCidr
}
