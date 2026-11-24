-- Run once per database (connected directly to that database, not master),
-- with -v LoginName=layouts_user or LoginName=solver_user. Maps the
-- server-level login created by azure-init-master.sql to a user scoped to
-- just this database, with the specific roles the deployment guide asks
-- for (db_ddladmin/db_datareader/db_datawriter) rather than db_owner, which
-- is what db/init.sql grants locally.

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '$(LoginName)')
    CREATE USER [$(LoginName)] FOR LOGIN [$(LoginName)];
GO

-- Per the deployment guide: db_ddladmin + db_datareader + db_datawriter
-- (enough to run migrations and serve requests), not db_owner.
ALTER ROLE db_ddladmin ADD MEMBER [$(LoginName)];
GO
ALTER ROLE db_datareader ADD MEMBER [$(LoginName)];
GO
ALTER ROLE db_datawriter ADD MEMBER [$(LoginName)];
GO
