IF OBJECT_ID(N'dbo.completions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.completions (
        id INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        habit_id INT NOT NULL,
        completion_date DATE NOT NULL,
        created_at DATETIME2 NOT NULL CONSTRAINT DF_completions_created_at DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_completions_habit_date UNIQUE(habit_id, completion_date)
    );
END
