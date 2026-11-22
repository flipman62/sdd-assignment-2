IF OBJECT_ID(N'dbo.habits', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.habits (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        name NVARCHAR(255) NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_habits_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_habits_name UNIQUE(name)
    );
END
