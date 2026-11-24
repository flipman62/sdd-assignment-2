import os
import re
import time

import pymssql


def main():
    server = os.environ["SQL_SERVER_FQDN"]
    admin_password = os.environ["SQL_ADMIN_PASSWORD"]
    habits_password = os.environ["HABITS_DB_PASSWORD"]
    completions_password = os.environ["COMPLETIONS_DB_PASSWORD"]
    prefix = os.environ["AZURE_RESOURCE_PREFIX"]

    habits_database = f"{prefix}-habits-db"
    completions_database = f"{prefix}-completions-db"
    sql = open("db/azure-init.sql", encoding="utf-8").read()
    sql = sql.replace("HABITS_DATABASE_PLACEHOLDER", habits_database)
    sql = sql.replace("COMPLETIONS_DATABASE_PLACEHOLDER", completions_database)
    sql = sql.replace("HABITS_PASSWORD_PLACEHOLDER", habits_password)
    sql = sql.replace("COMPLETIONS_PASSWORD_PLACEHOLDER", completions_password)

    connection = None
    for attempt in range(30):
        try:
            connection = pymssql.connect(
                server=server,
                user="sqladmin",
                password=admin_password,
                database="master",
                login_timeout=30,
                timeout=30,
                autocommit=True,
            )
            break
        except pymssql.Error:
            if attempt == 29:
                raise
            time.sleep(2)

    try:
        batches = re.split(r"(?im)^\s*GO\s*$", sql)
        cursor = connection.cursor()
        for batch in batches:
            batch = batch.strip()
            if batch:
                cursor.execute(batch)
    finally:
        connection.close()


if __name__ == "__main__":
    main()
