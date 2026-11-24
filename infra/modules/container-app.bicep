@description('Container App name, also used as the container name inside it.')
param name string

param location string

@description('Resource ID of the Container Apps managed environment this app runs in.')
param environmentId string

@description('Full image reference. Defaults to the Microsoft quickstart placeholder — the deployment guide has the real GHCR image replace this after infra is up, via `az containerapp update`, not a Bicep redeploy.')
param image string = 'mcr.microsoft.com/k8se/quickstart:latest'

@description('Port the container listens on (must match the Dockerfile EXPOSE/PORT for this service).')
param targetPort int

@secure()
@description('Full mssql:// connection string for this service\'s own database.')
param databaseUrl string

@description('Origin the Flask app should allow via CORS (the UI\'s static website URL).')
param uiOrigin string

@description('Commit SHA being deployed, reported back by /health.')
param gitSha string

@description('Extra environment variables beyond DATABASE_URL/UI_ORIGIN/GIT_SHA, e.g. LAYOUTS_URL for solver.')
param additionalEnv array = []

resource app 'Microsoft.App/containerApps@2023-05-01' = {
  name: name
  location: location
  properties: {
    managedEnvironmentId: environmentId
    configuration: {
      // Ingress is external because the UI calls both services directly from the
      // browser (system.yaml: ui.calls: [layouts, solver]). CORS is deliberately
      // NOT configured here — the Flask apps already handle it via UI_ORIGIN, and
      // turning it on at the proxy too would just mask a misconfigured origin
      // instead of failing loudly.
      ingress: {
        external: true
        targetPort: targetPort
        transport: 'auto'
      }
      // No registries/credentials: the GHCR packages are public (per the Azure
      // deployment guide — they start private, the first deploy's pull fails on
      // purpose, then they're made public and every deploy after that works
      // anonymously).
      registries: []
      secrets: [
        {
          name: 'database-url'
          value: databaseUrl
        }
      ]
    }
    template: {
      containers: [
        {
          name: name
          image: image
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
          env: concat(
            [
              {
                name: 'DATABASE_URL'
                secretRef: 'database-url'
              }
              {
                name: 'UI_ORIGIN'
                value: uiOrigin
              }
              {
                name: 'GIT_SHA'
                value: gitSha
              }
              // The free-offer database can take up to ~60s to resume from
              // AutoPause (deployment guide, step 8's cold-start watch-out).
              // migrate.py's run_migrations() calls get_db() before the
              // container even starts listening, so this retry budget has
              // to outlast a full resume, not just a local-compose race —
              // ~3+6+9+...+21 = 84s across 8 attempts. Container Apps'
              // own "port not ready" 503 during that window is expected
              // and accepted (A2 §7.5); the CD health check polls for
              // minutes, not seconds.
              {
                name: 'DB_CONNECT_RETRIES'
                value: '8'
              }
              {
                name: 'DB_CONNECT_RETRY_DELAY_S'
                value: '3'
              }
            ],
            additionalEnv
          )
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

output fqdn string = app.properties.configuration.ingress.fqdn
