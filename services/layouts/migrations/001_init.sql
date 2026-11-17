CREATE TABLE layouts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    created_at NVARCHAR(32) NOT NULL,
    cue_x FLOAT NOT NULL,
    cue_y FLOAT NOT NULL
);
GO

CREATE TABLE layout_balls (
    id INT IDENTITY(1,1) PRIMARY KEY,
    layout_id INT NOT NULL REFERENCES layouts(id),
    ball_number INT NOT NULL,
    x FLOAT NOT NULL,
    y FLOAT NOT NULL
);
GO

CREATE TABLE attempts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    layout_id INT NOT NULL REFERENCES layouts(id),
    created_at NVARCHAR(32) NOT NULL,
    succeeded BIT,
    notes NVARCHAR(MAX)
);
GO
