import app


def test_health():
    response = app.app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_list_completions_starts_empty():
    response = app.app.test_client().get("/habits/1/completions")

    assert response.status_code == 200
    assert response.json == {"habit_id": 1, "completions": []}
