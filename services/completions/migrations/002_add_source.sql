IF COL_LENGTH(N'dbo.completions', N'source') IS NULL
BEGIN
    ALTER TABLE dbo.completions
    ADD source NVARCHAR(32) NOT NULL CONSTRAINT DF_completions_source DEFAULT N'api';
END
