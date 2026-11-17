-- layout_id is a plain column, not a foreign key: layouts lives in a
-- separate database now, so referential integrity across the seam is
-- handled in code (services/solver/client.py), not by the schema.
CREATE TABLE solves (
    id INT IDENTITY(1,1) PRIMARY KEY,
    layout_id INT NOT NULL,
    computed_at NVARCHAR(32) NOT NULL,
    possible BIT NOT NULL,
    failed_at INT,
    order_json NVARCHAR(MAX),
    game_mode NVARCHAR(32),
    my_group NVARCHAR(16)
);
GO
