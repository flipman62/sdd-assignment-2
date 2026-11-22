import importlib.util
import sys
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_service(name):
    service_dir = ROOT / "services" / name
    sys.path.insert(0, str(service_dir))
    try:
        spec = importlib.util.spec_from_file_location(name, service_dir / "app.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


def test_completion_flow_verifies_habit(monkeypatch):
    completions = load_service("completions")
    habits = load_service("habits")

    class CompletionConnection:
        def cursor(self):
            return CompletionCursor()

        def close(self):
            return None

    class CompletionCursor:
        def execute(self, *_args):
            return None

        def fetchone(self):
            return None
    class FakeHabitDb:
        class Cursor:
            def execute(self, *_args):
                return None

            def fetchone(self):
                return (1, "Read")

        @staticmethod
        def connect():
            return type(
                "HabitConnection",
                (),
                {
                    "cursor": lambda self: FakeHabitDb.Cursor(),
                    "close": lambda self: None,
                },
            )()

    monkeypatch.setitem(sys.modules, "db", FakeHabitDb)
    monkeypatch.setattr(
        completions,
        "habit_exists",
        lambda habit_id: habits.app.test_client().get(
            f"/habits/{habit_id}"
        ).status_code == 200,
    )
    monkeypatch.setattr(completions, "connect", lambda: CompletionConnection())

    response = completions.app.test_client().post(
        "/habits/1/completions",
        json={"completion_date": date.today().isoformat()},
    )

    assert response.status_code == 200
    assert response.json["habit_id"] == 1
