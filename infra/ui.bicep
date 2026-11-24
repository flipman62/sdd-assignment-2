targetScope = 'resourceGroup'

@description('Globally unique Azure Storage account name for the UI')
param uiStorageName string

@description('Azure region')
param location string = resourceGroup().location

resource uiStorage 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: uiStorageName
  location: location
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
  }
}

output storageAccountName string = uiStorage.name
