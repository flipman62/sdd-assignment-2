import os

from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "db": "not-configured", "version": os.environ.get("GIT_SHA", "dev")})


@app.get("/habits/<int:habit_id>/completions")
def list_completions(habit_id):
    return jsonify({"habit_id": habit_id, "completions": []})


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
