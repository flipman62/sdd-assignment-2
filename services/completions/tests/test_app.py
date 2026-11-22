from datetime import date

import app


class FakeCursor:
    def __init__(self, rows=None, row=None):
        self.rows = rows or []
        self.row = row

    def execute(self, *_args):
        return None

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor

    def close(self):
        return None


def test_health(monkeypatch):
    monkeypatch.setattr(app, "health_check", lambda: True)

    response = app.app.test_client().get("/health")

    assert response.status_code == 200
    assert response.json["db"] == "ok"


def test_record_rejects_future_date(monkeypatch):
    monkeypatch.setattr(app, "habit_exists", lambda _habit_id: True)

    response = app.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": "2999-01-01"},
    )

    assert response.status_code == 400


def test_missing_habit(monkeypatch):
    monkeypatch.setattr(app, "habit_exists", lambda _habit_id: False)

    response = app.app.test_client().post(
        "/habits/999/completions",
        json={"completion_date": date.today().isoformat()},
    )

    assert response.status_code == 404


def test_habits_service_unavailable(monkeypatch):
    def unavailable(_habit_id):
        raise app.HabitServiceUnavailable

    monkeypatch.setattr(app, "habit_exists", unavailable)

    response = app.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": date.today().isoformat()},
    )

    assert response.status_code == 503
    assert response.json["error"] == "habits service unavailable"


def test_list_completions(monkeypatch):
    cursor = FakeCursor(rows=[(date(2026, 11, 22),)])
    monkeypatch.setattr(app, "connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().get("/habits/1/completions")

    assert response.status_code == 200
    assert response.json["completions"] == ["2026-11-22"]


def test_record_completion(monkeypatch):
    monkeypatch.setattr(app, "habit_exists", lambda _habit_id: True)
    cursor = FakeCursor(row=None)
    monkeypatch.setattr(app, "connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": "2026-11-22"},
    )

    assert response.status_code == 200
    assert response.json["already_recorded"] is False


def test_duplicate_completion(monkeypatch):
    monkeypatch.setattr(app, "habit_exists", lambda _habit_id: True)
    cursor = FakeCursor(row=(1,))
    monkeypatch.setattr(app, "connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": "2026-11-22"},
    )

    assert response.status_code == 200
    assert response.json["already_recorded"] is True


def test_streak(monkeypatch):
    cursor = FakeCursor(rows=[(date.today(),), (date.today(),)])
    monkeypatch.setattr(app, "connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().get("/habits/1/streak")

    assert response.status_code == 200
    assert response.json["streak"] == 1


def test_invalid_completion_date(monkeypatch):
    monkeypatch.setattr(app, "habit_exists", lambda _habit_id: True)

    response = app.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": "bad"},
    )

    assert response.status_code == 400
