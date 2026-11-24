// Phase 8: two Container Apps (layouts, solver), one shared Azure SQL logical
// server with one database per service, and one Storage Account for the
// static UI. Deploy into the already-existing resource group
// rg-lgonzalez-ieu2024:
//
//   az deployment group create \
//     --resource-group rg-lgonzalez-ieu2024 \
//     --template-file infra/main.bicep \
//     --parameters infra/main.bicepparam
//
// Two things this template deliberately does NOT do, because they are
// data-plane operations ARM/Bicep can't express without a deploymentScript
// (not worth the extra complexity for two services): enabling the storage
// account's static website feature, and creating the per-service SQL logins
// and database users. Both are plain `az`/`sqlcmd` steps, run once, after
// this deploys.

@description('Azure region. Must be one of the subscription\'s allowed regions AND support the Azure SQL free offer (check both with az policy assignment list and the free-offer region list before deploying — do not assume a classmate\'s region works, per the Azure deployment guide).')
param location string

@description('Admin login for the shared Azure SQL logical server.')
param sqlAdminLogin string

@secure()
@description('Admin password for the shared Azure SQL logical server.')
param sqlAdminPassword string

@secure()
@description('Password for the layouts service\'s own contained database user (the user itself is created separately via sqlcmd, not by this template).')
param layoutsDbPassword string

@secure()
@description('Password for the solver service\'s own contained database user (the user itself is created separately via sqlcmd, not by this template).')
param solverDbPassword string

@description('Value reported by each /health endpoint as GIT_SHA. Only meaningful once a real image is deployed (see container-app.bicep); the pipeline updates this at deploy time, not this template.')
param imageTag string = 'dev'

@description('The UI\'s static website origin, for the services\' CORS allowlist. Azure only assigns the real <account>.<zone>.web.core.windows.net hostname once the storage account exists below, so the first deploy won\'t have the final value — rerun with the real one once az storage account show reports it.')
param uiOrigin string

var prefix = 'lgonzalez-ieu2024'

resource logs 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource containerEnv 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource sqlServer 'Microsoft.Sql/servers@2023-05-01-preview' = {
  name: '${prefix}-sql'
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
  }
}

// Lets the Container Apps reach the server without a static/predictable
// egress IP to allowlist (Consumption plan doesn't give one). Azure's own
// services ignore this rule's literal 0.0.0.0-0.0.0.0 range and treat it as
// "allow Azure resources" instead.
resource allowAzureServices 'Microsoft.Sql/servers/firewallRules@2023-05-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// Free offer: General Purpose, serverless, Gen5, 0.5-1 vCore, locally
// redundant backups (A2 §7.3 — Azure's current default is geo-redundant for
// new databases in most regions, so this has to be set explicitly, not
// assumed). Deliberately NOT setting autoPauseDelay or a max size — the
// guide's own troubleshooting table says passing those (even matching the
// forced defaults: 60 min pause, 32GB) gets rejected with "Only default
// value ... is allowed for Free Limit database". Let the free-limit
// defaults apply.
//
// Open question, not confirmed by either A2 or the deployment guide (both
// describe both databases on the free offer with no stated per-subscription
// cap — this caveat is from general Azure knowledge, not from either
// document): the free offer may only apply to one database per
// subscription. Check after deploying (`az sql db show` on each) and note
// the real outcome in ADR-8 either way.
resource layoutsDb 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: '${prefix}-layouts-db'
  location: location
  sku: {
    name: 'GP_S_Gen5'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: 1
  }
  properties: {
    minCapacity: json('0.5')
    useFreeLimit: true
    freeLimitExhaustionBehavior: 'AutoPause'
    requestedBackupStorageRedundancy: 'Local'
  }
}

resource solverDb 'Microsoft.Sql/servers/databases@2023-05-01-preview' = {
  parent: sqlServer
  name: '${prefix}-solver-db'
  location: location
  sku: {
    name: 'GP_S_Gen5'
    tier: 'GeneralPurpose'
    family: 'Gen5'
    capacity: 1
  }
  properties: {
    minCapacity: json('0.5')
    useFreeLimit: true
    freeLimitExhaustionBehavior: 'AutoPause'
    requestedBackupStorageRedundancy: 'Local'
  }
}

// The pipeline signs in as this identity (OIDC federated credential — added
// separately via `az identity federated-credential create`, since the exact
// subject depends on the GitHub repo and sometimes needs the numeric-ID
// fallback too; see the deployment guide's step 6 and its "watch out").
resource githubIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-github'
  location: location
}

resource githubIdentityContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(resourceGroup().id, githubIdentity.id, 'Contributor')
  scope: resourceGroup()
  properties: {
    principalId: githubIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b24988ac-6180-42a0-ab88-20f7382dd24c')
  }
}

resource ui 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: '${replace(prefix, '-', '')}ui'
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    // Static website serving needs anonymous read on the $web container;
    // enabling the static website feature itself is a post-deploy CLI step
    // (see the header comment above).
    allowBlobPublicAccess: true
  }
}

module layouts 'modules/container-app.bicep' = {
  name: 'layouts'
  params: {
    name: '${prefix}-layouts'
    location: location
    environmentId: containerEnv.id
    targetPort: 8000
    databaseUrl: 'mssql://layouts_user:${layoutsDbPassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${layoutsDb.name}'
    uiOrigin: uiOrigin
    gitSha: imageTag
    additionalEnv: []
  }
}

module solver 'modules/container-app.bicep' = {
  name: 'solver'
  params: {
    name: '${prefix}-solver'
    location: location
    environmentId: containerEnv.id
    targetPort: 8001
    databaseUrl: 'mssql://solver_user:${solverDbPassword}@${sqlServer.properties.fullyQualifiedDomainName}:1433/${solverDb.name}'
    uiOrigin: uiOrigin
    gitSha: imageTag
    additionalEnv: [
      {
        name: 'LAYOUTS_URL'
        value: 'https://${layouts.outputs.fqdn}'
      }
    ]
  }
}

output layoutsUrl string = 'https://${layouts.outputs.fqdn}'
output solverUrl string = 'https://${solver.outputs.fqdn}'
output uiStorageAccount string = ui.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output githubIdentityClientId string = githubIdentity.properties.clientId
