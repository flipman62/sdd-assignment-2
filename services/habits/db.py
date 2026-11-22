import os
import time
from pathlib import Path
from urllib.parse import unquote, urlparse

import pymssql


def database_config():
    database_url = os.environ["DATABASE_URL"]
    parsed = urlparse(database_url)
    if parsed.scheme not in {"mssql", "mssql+pymssql"}:
        raise RuntimeError("DATABASE_URL must use the mssql+pymssql scheme")
    if not parsed.hostname or not parsed.username or not parsed.password or not parsed.path.strip("/"):
        raise RuntimeError("DATABASE_URL must include host, credentials, and database")

    return {
        "host": parsed.hostname,
        "port": parsed.port or 1433,
        "user": unquote(parsed.username),
        "password": unquote(parsed.password),
        "database": parsed.path.strip("/"),
        "login_timeout": int(os.environ.get("DB_CONNECT_TIMEOUT_S", "30")),
    }


def connect():
    config = database_config()
    return pymssql.connect(
        server=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        login_timeout=config["login_timeout"],
        timeout=config["login_timeout"],
        autocommit=True,
    )


def run_migrations():
    migration_dir = Path(__file__).parent / "migrations"
    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            IF OBJECT_ID(N'dbo.schema_migrations', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.schema_migrations (
                    name NVARCHAR(255) NOT NULL PRIMARY KEY,
                    applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
                );
            END
            """
        )

        for migration_path in sorted(migration_dir.glob("*.sql")):
            cursor.execute(
                "SELECT 1 FROM dbo.schema_migrations WHERE name = %s",
                (migration_path.name,),
            )
            if cursor.fetchone():
                continue

            cursor.execute(migration_path.read_text())
            cursor.execute(
                "INSERT INTO dbo.schema_migrations (name) VALUES (%s)",
                (migration_path.name,),
            )
    finally:
        connection.close()


def run_migrations_with_retry(attempts=30, delay_seconds=2):
    for attempt in range(attempts):
        try:
            run_migrations()
            return
        except pymssql.Error:
            if attempt == attempts - 1:
                raise
            time.sleep(delay_seconds)


def health_check():
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.execute(
            """
            IF OBJECT_ID(N'dbo.health_probe', N'U') IS NULL
            BEGIN
                CREATE TABLE dbo.health_probe (
                    id INT NOT NULL PRIMARY KEY,
                    checked_at DATETIME2 NOT NULL
                );
            END
            """
        )
        cursor.execute(
            "MERGE dbo.health_probe AS target "
            "USING (VALUES (1, SYSUTCDATETIME())) AS source(id, checked_at) "
            "ON target.id = source.id "
            "WHEN MATCHED THEN UPDATE SET checked_at = source.checked_at "
            "WHEN NOT MATCHED THEN INSERT (id, checked_at) VALUES (source.id, source.checked_at);"
        )
        return True
    finally:
        connection.close()
