-- NOT NULL + DEFAULT, not nullable: SQL Server backfills every existing row
-- with 'ui' in the same statement (every layout today is created through
-- the static UI), and new inserts can omit the column entirely and still
-- get the default, so create_layout() needs no change. A later client
-- (e.g. a script seeding layouts directly) could report something else.
ALTER TABLE layouts ADD source NVARCHAR(16) NOT NULL DEFAULT 'ui';
GO
