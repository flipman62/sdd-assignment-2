targetScope = 'resourceGroup'

@description('Resource name prefix')
param prefix string

@description('Azure region')
param location string = resourceGroup().location

@description('Origin of the Azure Storage static website')
param uiOrigin string

@secure()
@description('Habits database login password')
param habitsDatabasePassword string

@secure()
@description('Completions database login password')
param completionsDatabasePassword string

@description('Git SHA used in the deployed image tags')
param gitSha string

@description('GitHub owner of the public GHCR packages')
param registryUsername string

var sqlServerName = '${prefix}-sql'
var habitsDatabaseName = '${prefix}-habits-db'
var completionsDatabaseName = '${prefix}-completions-db'
var environmentName = '${prefix}-env'
var habitsAppName = '${prefix}-habits'
var completionsAppName = '${prefix}-completions'
var habitsImage = 'ghcr.io/${registryUsername}/habits:${gitSha}'
var completionsImage = 'ghcr.io/${registryUsername}/completions:${gitSha}'

resource sqlServer 'Microsoft.Sql/servers@2023-08-01' existing = {
  name: sqlServerName
}

resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2025-01-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

resource habitsApp 'Microsoft.App/containerApps@2025-01-01' = {
  name: habitsAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: 'ghcr.io'
        }
      ]
      secrets: [
        {
          name: 'database-url'
          value: 'mssql+pymssql://habits_user:${uriComponent(habitsDatabasePassword)}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${habitsDatabaseName}'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'habits'
          image: habitsImage
          env: [
            { name: 'PORT', value: '8000' }
            { name: 'GIT_SHA', value: gitSha }
            { name: 'CORS_ORIGINS', value: uiOrigin }
            { name: 'DB_CONNECT_TIMEOUT_S', value: '30' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

var habitsUrl = 'https://${habitsApp.properties.configuration.ingress.fqdn}'

resource completionsApp 'Microsoft.App/containerApps@2025-01-01' = {
  name: completionsAppName
  location: location
  properties: {
    managedEnvironmentId: containerEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: 'ghcr.io'
        }
      ]
      secrets: [
        {
          name: 'database-url'
          value: 'mssql+pymssql://completions_user:${uriComponent(completionsDatabasePassword)}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${completionsDatabaseName}'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'completions'
          image: completionsImage
          env: [
            { name: 'PORT', value: '8000' }
            { name: 'GIT_SHA', value: gitSha }
            { name: 'CORS_ORIGINS', value: uiOrigin }
            { name: 'DB_CONNECT_TIMEOUT_S', value: '30' }
            { name: 'HABITS_URL', value: habitsUrl }
            { name: 'HABITS_TIMEOUT_S', value: '2' }
            { name: 'DATABASE_URL', secretRef: 'database-url' }
          ]
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

output habitsFqdn string = habitsApp.properties.configuration.ingress.fqdn
output completionsFqdn string = completionsApp.properties.configuration.ingress.fqdn
