-- Run once against `master` on the Azure SQL logical server (the two
-- databases themselves already exist — Bicep creates them). Azure SQL
-- Database doesn't support USE to jump to another database in the same
-- connection like db/init.sql's single sqlcmd session does on a full SQL
-- Server instance, so creating the per-service logins (here, server-level)
-- and creating the matching users (azure-init-db-user.sql, one connection
-- per database) are necessarily separate sqlcmd calls.

IF NOT EXISTS (SELECT 1 FROM sys.sql_logins WHERE name = 'layouts_user')
    CREATE LOGIN layouts_user WITH PASSWORD = '$(LayoutsPassword)';
GO

IF NOT EXISTS (SELECT 1 FROM sys.sql_logins WHERE name = 'solver_user')
    CREATE LOGIN solver_user WITH PASSWORD = '$(SolverPassword)';
GO
