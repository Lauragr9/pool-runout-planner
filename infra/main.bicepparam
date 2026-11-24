using 'main.bicep'

// Nothing secret lives in this file — every password comes from an
// environment variable set in the shell before deploying (see the runbook).
// `location` has no safe default: it depends on this specific subscription's
// allowed-region policy, checked right before the first deploy, not guessed
// ahead of time.

param location = readEnvironmentVariable('AZURE_LOCATION')
param sqlAdminLogin = 'lgonzalezadmin'
param sqlAdminPassword = readEnvironmentVariable('SQL_ADMIN_PASSWORD')
param layoutsDbPassword = readEnvironmentVariable('LAYOUTS_DB_PASSWORD')
param solverDbPassword = readEnvironmentVariable('SOLVER_DB_PASSWORD')
param uiOrigin = readEnvironmentVariable('UI_ORIGIN', 'http://localhost:8080')
