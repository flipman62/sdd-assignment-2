import os
import time
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import pymssql
from flask import Flask, jsonify, request

from db import connect, health_check, run_migrations_with_retry


app = Flask(__name__)


@app.before_request
def start_request_timer():
    request.environ["request_started_at"] = time.perf_counter()


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")
    if origin in {"http://localhost:8080", "http://127.0.0.1:8080"}:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    started_at = request.environ.get("request_started_at")
    duration_ms = (time.perf_counter() - started_at) * 1000 if started_at else 0
    print(
        f'method={request.method} path={request.path} '
        f'status={response.status_code} duration_ms={duration_ms:.2f}',
        flush=True,
    )
    return response


class HabitServiceUnavailable(Exception):
    pass


def habit_exists(habit_id):
    base_url = os.environ.get("HABITS_URL", "http://habits:8000").rstrip("/")
    timeout = float(os.environ.get("HABITS_TIMEOUT_S", "2"))

    try:
        with urlopen(f"{base_url}/habits/{habit_id}", timeout=timeout) as response:
            return response.status == 200
    except HTTPError as error:
        if error.code == 404:
            return False
        raise HabitServiceUnavailable from error
    except (URLError, TimeoutError, OSError) as error:
        raise HabitServiceUnavailable from error


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


@app.post("/habits/<int:habit_id>/completions")
def record_completion(habit_id):
    payload = request.get_json(silent=True) or {}
    completion_date = payload.get("completion_date", date.today().isoformat())

    if not isinstance(completion_date, str):
        return jsonify({"error": "completion_date must use YYYY-MM-DD format"}), 400

    try:
        parsed_date = date.fromisoformat(completion_date)
    except ValueError:
        return jsonify({"error": "completion_date must use YYYY-MM-DD format"}), 400

    if parsed_date > date.today():
        return jsonify({"error": "future completion dates are not allowed"}), 400

    try:
        exists = habit_exists(habit_id)
    except HabitServiceUnavailable:
        return jsonify(
            {
                "error": "habits service unavailable",
                "habit_id": habit_id,
            }
        ), 503

    if not exists:
        return jsonify({"error": "habit not found"}), 404

    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM dbo.completions "
            "WHERE habit_id = %d AND completion_date = %s",
            (habit_id, parsed_date.isoformat()),
        )
        already_recorded = cursor.fetchone() is not None

        if not already_recorded:
            cursor.execute(
                "INSERT INTO dbo.completions (habit_id, completion_date) "
                "VALUES (%d, %s)",
                (habit_id, parsed_date.isoformat()),
            )

        return jsonify(
            {
                "habit_id": habit_id,
                "completion_date": parsed_date.isoformat(),
                "already_recorded": already_recorded,
            }
        ), 200
    finally:
        connection.close()


@app.get("/habits/<int:habit_id>/completions")
def list_completions(habit_id):
    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT completion_date FROM dbo.completions "
            "WHERE habit_id = %d ORDER BY completion_date DESC",
            (habit_id,),
        )
        return jsonify(
            {
                "habit_id": habit_id,
                "completions": [
                    row[0].isoformat() if hasattr(row[0], "isoformat") else str(row[0])
                    for row in cursor.fetchall()
                ],
            }
        )
    finally:
        connection.close()


@app.get("/habits/<int:habit_id>/streak")
def streak(habit_id):
    connection = connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT completion_date FROM dbo.completions WHERE habit_id = %d",
            (habit_id,),
        )
        completed_dates = {
            row[0].date() if hasattr(row[0], "date") else date.fromisoformat(str(row[0]))
            for row in cursor.fetchall()
        }
        reference_date = date.today()
        streak_count = 0

        while reference_date in completed_dates:
            streak_count += 1
            reference_date -= timedelta(days=1)

        return jsonify({"habit_id": habit_id, "streak": streak_count})
    finally:
        connection.close()


if __name__ == "__main__":
    run_migrations_with_retry()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
