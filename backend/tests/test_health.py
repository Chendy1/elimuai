from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


class OkDb:
    def execute(self, *_args, **_kwargs):
        return 1


class BrokenDb:
    def execute(self, *_args, **_kwargs):
        raise OperationalError("SELECT 1", {}, Exception("down"))


def client_with(db) -> TestClient:
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_liveness_does_not_need_database():
    r = TestClient(app).get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "elimuai-api"}


def test_readiness_ok_when_database_answers():
    r = client_with(OkDb()).get("/health/ready")
    assert r.status_code == 200
    assert r.json()["database"] == "ok"


def test_readiness_503_when_database_down():
    r = client_with(BrokenDb()).get("/health/ready")
    assert r.status_code == 503
