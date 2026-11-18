-- Nullable, so every row saved by 001 keeps its data; only new solves
-- from here on actually measure and store a duration.
ALTER TABLE solves ADD duration_ms FLOAT NULL;
GO
