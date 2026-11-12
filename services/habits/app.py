import os

from flask import Flask, jsonify, request


app = Flask(__name__)
habits = {}
next_habit_id = 1


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "db": "not-configured",
            "version": os.environ.get("GIT_SHA", "dev"),
        }
    )


@app.get("/habits")
def list_habits():
    return jsonify(list(habits.values()))


@app.post("/habits")
def create_habit():
    global next_habit_id

    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "name must be a non-empty string"}), 400

    habit_name = name.strip()
    if any(habit["name"].casefold() == habit_name.casefold() for habit in habits.values()):
        return jsonify({"error": "a habit with that name already exists"}), 409

    habit = {"id": next_habit_id, "name": habit_name}
    habits[next_habit_id] = habit
    next_habit_id += 1
    return jsonify(habit), 201


@app.delete("/habits/<int:habit_id>")
def delete_habit(habit_id):
    if habit_id not in habits:
        return jsonify({"error": "habit not found"}), 404

    del habits[habit_id]
    return "", 204


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
