IF DB_ID(N'habits_db') IS NULL
BEGIN
    CREATE DATABASE habits_db;
END;
GO

IF DB_ID(N'completions_db') IS NULL
BEGIN
    CREATE DATABASE completions_db;
END;
GO

USE habits_db;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'habits_user')
BEGIN
    CREATE LOGIN habits_user WITH PASSWORD = 'HABITS_PASSWORD_PLACEHOLDER';
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'habits_user')
BEGIN
    CREATE USER habits_user FOR LOGIN habits_user;
END;
GO

ALTER ROLE db_owner ADD MEMBER habits_user;
GO

USE completions_db;
GO

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'completions_user')
BEGIN
    CREATE LOGIN completions_user WITH PASSWORD = 'COMPLETIONS_PASSWORD_PLACEHOLDER';
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = N'completions_user')
BEGIN
    CREATE USER completions_user FOR LOGIN completions_user;
END;
GO

ALTER ROLE db_owner ADD MEMBER completions_user;
GO
