import app


def test_health():
    response = app.app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_list_habits_starts_empty():
    response = app.app.test_client().get("/habits")

    assert response.status_code == 200
    assert response.json == []
