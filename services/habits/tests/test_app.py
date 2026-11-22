import app


class FakeCursor:
    def __init__(self, rows=None, row=None, rowcount=0, fetch_results=None):
        self.rows = rows or []
        self.row = row
        self.rowcount = rowcount
        self.fetch_results = list(fetch_results or [])
        self.fetch_index = 0

    def execute(self, *_args):
        return None

    def fetchall(self):
        return self.rows

    def fetchone(self):
        if self.fetch_index < len(self.fetch_results):
            result = self.fetch_results[self.fetch_index]
            self.fetch_index += 1
            return result
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


def test_health_database_failure(monkeypatch):
    def unavailable():
        raise OSError("database unavailable")

    monkeypatch.setattr(app, "health_check", unavailable)

    response = app.app.test_client().get("/health")

    assert response.status_code == 503
    assert response.json["db"] == "unavailable"


def test_list_habits(monkeypatch):
    cursor = FakeCursor(rows=[(1, "Read")])
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().get("/habits")

    assert response.status_code == 200
    assert response.json == [{"id": 1, "name": "Read"}]


def test_create_validates_name():
    response = app.app.test_client().post("/habits", json={"name": "   "})

    assert response.status_code == 400


def test_get_missing_habit(monkeypatch):
    cursor = FakeCursor(row=None)
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().get("/habits/999")

    assert response.status_code == 404


def test_get_habit(monkeypatch):
    cursor = FakeCursor(row=(1, "Read"))
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().get("/habits/1")

    assert response.status_code == 200
    assert response.json == {"id": 1, "name": "Read"}


def test_create_habit(monkeypatch):
    cursor = FakeCursor(fetch_results=[None, (1, "Read")])
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().post("/habits", json={"name": " Read "})

    assert response.status_code == 201
    assert response.json == {"id": 1, "name": "Read"}


def test_duplicate_habit(monkeypatch):
    cursor = FakeCursor(row=(1, "Read"))
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().post("/habits", json={"name": "Read"})

    assert response.status_code == 409


def test_delete_habit(monkeypatch):
    cursor = FakeCursor(rowcount=1)
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().delete("/habits/1")

    assert response.status_code == 204


def test_delete_missing_habit(monkeypatch):
    cursor = FakeCursor(rowcount=0)
    monkeypatch.setattr("db.connect", lambda: FakeConnection(cursor))

    response = app.app.test_client().delete("/habits/999")

    assert response.status_code == 404
