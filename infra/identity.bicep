targetScope = 'resourceGroup'

@description('Resource name prefix')
param prefix string

@description('GitHub repository owner')
param repoOwner string

@description('GitHub repository name')
param repoName string

@description('Immutable GitHub repository owner ID')
param repoOwnerId string

@description('Immutable GitHub repository ID')
param repoId string

var identityName = '${prefix}-github'
var contributorRoleId = 'b24988ac-6180-42a0-ab88-20f7382dd24c'
var storageBlobDataContributorRoleId = 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'

resource githubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' = {
  name: identityName
  location: resourceGroup().location
}

// Keep deployment permissions limited to this resource group.
resource contributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, githubIdentity.id, contributorRoleId)
  properties: {
    principalId: githubIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
  }
}

resource storageDataRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, githubIdentity.id, storageBlobDataContributorRoleId)
  properties: {
    principalId: githubIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', storageBlobDataContributorRoleId)
  }
}

resource githubMainCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = {
  parent: githubIdentity
  name: 'github-main-branch'
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${repoOwner}/${repoName}:ref:refs/heads/main'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

resource githubMainNumericCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2024-11-30' = {
  parent: githubIdentity
  name: 'github-main-numeric-ids'
  dependsOn: [
    githubMainCredential
  ]
  properties: {
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${repoOwner}@${repoOwnerId}/${repoName}@${repoId}:ref:refs/heads/main'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

output identityClientId string = githubIdentity.properties.clientId
output identityPrincipalId string = githubIdentity.properties.principalId
