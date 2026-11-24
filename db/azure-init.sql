IF DB_ID(N'HABITS_DATABASE_PLACEHOLDER') IS NULL
BEGIN
    THROW 51000, 'Habits database was not found', 1;
END;
GO

IF DB_ID(N'COMPLETIONS_DATABASE_PLACEHOLDER') IS NULL
BEGIN
    THROW 51001, 'Completions database was not found', 1;
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'habits_user')
BEGIN
    CREATE LOGIN habits_user WITH PASSWORD = 'HABITS_PASSWORD_PLACEHOLDER';
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'completions_user')
BEGIN
    CREATE LOGIN completions_user WITH PASSWORD = 'COMPLETIONS_PASSWORD_PLACEHOLDER';
END;
GO

USE [HABITS_DATABASE_PLACEHOLDER];
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'habits_user')
BEGIN
    CREATE USER habits_user FOR LOGIN habits_user;
END;
GO

ALTER ROLE db_owner ADD MEMBER habits_user;
GO

USE [COMPLETIONS_DATABASE_PLACEHOLDER];
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'completions_user')
BEGIN
    CREATE USER completions_user FOR LOGIN completions_user;
END;
GO

ALTER ROLE db_owner ADD MEMBER completions_user;
GO
