import os
from datetime import date, timedelta
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from flask import Flask, jsonify, request


app = Flask(__name__)
completions = {}


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
    return jsonify(
        {
            "status": "ok",
            "db": "not-configured",
            "version": os.environ.get("GIT_SHA", "dev"),
        }
    )


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

    habit_completions = completions.setdefault(habit_id, set())
    already_recorded = parsed_date.isoformat() in {
        value.isoformat() for value in habit_completions
    }
    habit_completions.add(parsed_date)

    return jsonify(
        {
            "habit_id": habit_id,
            "completion_date": parsed_date.isoformat(),
            "already_recorded": already_recorded,
        }
    ), 200


@app.get("/habits/<int:habit_id>/completions")
def list_completions(habit_id):
    completion_dates = sorted(completions.get(habit_id, set()), reverse=True)
    return jsonify(
        {
            "habit_id": habit_id,
            "completions": [value.isoformat() for value in completion_dates],
        }
    )


@app.get("/habits/<int:habit_id>/streak")
def streak(habit_id):
    completed_dates = completions.get(habit_id, set())
    reference_date = date.today()
    streak_count = 0

    while reference_date in completed_dates:
        streak_count += 1
        reference_date -= timedelta(days=1)

    return jsonify({"habit_id": habit_id, "streak": streak_count})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
