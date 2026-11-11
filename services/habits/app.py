import os

from flask import Flask, jsonify


app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "db": "not-configured", "version": os.environ.get("GIT_SHA", "dev")})


@app.get("/habits")
def list_habits():
    return jsonify([])


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )
