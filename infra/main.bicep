targetScope = 'resourceGroup'

@description('Resource name prefix')
param prefix string

@description('Azure region')
param location string = resourceGroup().location

@secure()
@description('SQL Server administrator password')
param sqlAdministratorPassword string

@secure()
@description('Habits database login password')
param habitsDatabasePassword string

@secure()
@description('Completions database login password')
param completionsDatabasePassword string

@secure()
@description('GHCR registry password')
param registryPassword string

@description('Git SHA used in the deployed image tags')
param gitSha string

@description('GHCR registry username')
param registryUsername string

var sqlServerName = '${prefix}-sql'
var habitsDatabaseName = '${prefix}-habits-db'
var completionsDatabaseName = '${prefix}-completions-db'
var environmentName = '${prefix}-env'
var habitsAppName = '${prefix}-habits'
var completionsAppName = '${prefix}-completions'
var staticAppName = '${prefix}-ui'
var habitsImage = 'ghcr.io/${registryUsername}/habits:${gitSha}'
var completionsImage = 'ghcr.io/${registryUsername}/completions:${gitSha}'

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' existing = {
  name: sqlServerName
}

resource habitsDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' existing = {
  parent: sqlServer
  name: habitsDatabaseName
}

resource completionsDatabase 'Microsoft.Sql/servers/databases@2023-08-01-preview' existing = {
  parent: sqlServer
  name: completionsDatabaseName
}

resource containerEnvironment 'Microsoft.App/managedEnvironments@2024-10-02-preview' = {
  name: environmentName
  location: location
  properties: {}
}

resource staticApp 'Microsoft.Web/staticSites@2024-04-01' = {
  name: staticAppName
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

var staticOrigin = 'https://${staticApp.properties.defaultHostname}'

resource habitsApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
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
          username: registryUsername
          passwordSecretRef: 'ghcr-password'
        }
      ]
      secrets: [
        {
          name: 'ghcr-password'
          value: registryPassword
        }
        {
          name: 'database-url'
          value: 'mssql+pymssql://habits_user:${habitsDatabasePassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${habitsDatabaseName}'
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
            { name: 'CORS_ORIGINS', value: staticOrigin }
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

resource completionsApp 'Microsoft.App/containerApps@2024-10-02-preview' = {
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
          username: registryUsername
          passwordSecretRef: 'ghcr-password'
        }
      ]
      secrets: [
        {
          name: 'ghcr-password'
          value: registryPassword
        }
        {
          name: 'database-url'
          value: 'mssql+pymssql://completions_user:${completionsDatabasePassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${completionsDatabaseName}'
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
            { name: 'CORS_ORIGINS', value: staticOrigin }
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
output staticWebAppUrl string = 'https://${staticApp.properties.defaultHostname}'
