-- Idempotent: safe to run on every `docker compose up`. Creates one
-- database per service and one login per service, each scoped to its own
-- database only (no service can reach the other's data through the DB).
-- Passwords come in as sqlcmd scripting variables, not hardcoded here.

IF DB_ID('layouts') IS NULL
    CREATE DATABASE layouts;
GO

IF DB_ID('solver') IS NULL
    CREATE DATABASE solver;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'layouts_user')
    CREATE LOGIN layouts_user WITH PASSWORD = '$(LayoutsPassword)';
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = 'solver_user')
    CREATE LOGIN solver_user WITH PASSWORD = '$(SolverPassword)';
GO

USE layouts;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'layouts_user')
    CREATE USER layouts_user FOR LOGIN layouts_user;
GO
ALTER ROLE db_owner ADD MEMBER layouts_user;
GO

USE solver;
GO
IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = 'solver_user')
    CREATE USER solver_user FOR LOGIN solver_user;
GO
ALTER ROLE db_owner ADD MEMBER solver_user;
GO
