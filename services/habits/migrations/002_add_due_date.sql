IF COL_LENGTH(N'dbo.habits', N'due_date') IS NULL
BEGIN
    ALTER TABLE dbo.habits
    ADD due_date NVARCHAR(10) NULL;
END
