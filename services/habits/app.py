import os
import time

import pymssql
from flask import Flask, jsonify, request

from db import health_check, run_migrations_with_retry


app = Flask(__name__)


@app.before_request
def start_request_timer():
    request.environ["request_started_at"] = time.perf_counter()


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    allowed_origins = {
        value.strip()
        for value in os.environ.get("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
        if value.strip()
    }
    if origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
    started_at = request.environ.get("request_started_at")
    duration_ms = (time.perf_counter() - started_at) * 1000 if started_at else 0
    print(
        f'method={request.method} path={request.path} '
        f'status={response.status_code} duration_ms={duration_ms:.2f}',
        flush=True,
    )
    return response


@app.get("/health")
def health():
    try:
        health_check()
        return jsonify(
            {
                "status": "ok",
                "db": "ok",
                "version": os.environ.get("GIT_SHA", "dev"),
            }
        )
    except (pymssql.Error, OSError, RuntimeError):
        return jsonify(
            {
                "status": "unhealthy",
                "db": "unavailable",
                "version": os.environ.get("GIT_SHA", "dev"),
            }
        ), 503


@app.get("/habits")
def list_habits():
    from db import connect

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM dbo.habits ORDER BY id")
        return jsonify([{"id": row[0], "name": row[1]} for row in cursor.fetchall()])
    finally:
        connection.close()


@app.get("/habits/<int:habit_id>")
def get_habit(habit_id):
    from db import connect

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT id, name FROM dbo.habits WHERE id = %d", (habit_id,))
        row = cursor.fetchone()
        if row is None:
            return jsonify({"error": "habit not found"}), 404
        return jsonify({"id": row[0], "name": row[1]})
    finally:
        connection.close()


@app.post("/habits")
def create_habit():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name must be a non-empty string"}), 400

    habit_name = name.strip()
    from db import connect

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id FROM dbo.habits WHERE LOWER(name) = LOWER(%s)",
            (habit_name,),
        )
        if cursor.fetchone():
            return jsonify({"error": "a habit with that name already exists"}), 409
        cursor.execute(
            "INSERT INTO dbo.habits (name) OUTPUT INSERTED.id, INSERTED.name "
            "VALUES (%s)",
            (habit_name,),
        )
        row = cursor.fetchone()
        return jsonify({"id": row[0], "name": row[1]}), 201
    except pymssql.IntegrityError:
        return jsonify({"error": "a habit with that name already exists"}), 409
    finally:
        connection.close()


@app.delete("/habits/<int:habit_id>")
def delete_habit(habit_id):
    from db import connect

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM dbo.habits WHERE id = %d", (habit_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "habit not found"}), 404
        return "", 204
    finally:
        connection.close()


if __name__ == "__main__":
    run_migrations_with_retry()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
