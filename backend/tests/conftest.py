"""Test fixtures. Auth tests run against a separate PostgreSQL database named <name>_test,
created on demand and migrated with Alembic, so development data is never touched."""
import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.main import app
from app.services.email import get_email_sender

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _test_url():
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return make_url(explicit)
    base = make_url(get_settings().database_url)
    return base.set(database=f"{base.database}_test")


def _ensure_database(url) -> None:
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def db_engine():
    url = _test_url()
    assert url.database.endswith("_test"), "refusing to run tests against a non-test database"
    _ensure_database(url)
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url.render_as_string(hide_password=False).replace("%", "%%"))
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    yield engine
    engine.dispose()


class FakeEmailSender:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    def send_password_reset(self, to: str, reset_url: str) -> None:
        self.sent.append((to, reset_url))


@pytest.fixture
def outbox() -> FakeEmailSender:
    return FakeEmailSender()


@pytest.fixture
def client(db_engine, outbox):
    with db_engine.begin() as conn:
        conn.execute(text("TRUNCATE audit_logs, consent_records, learners, password_reset_tokens, sessions, user_roles, users CASCADE"))
    limiter.reset()
    factory = sessionmaker(bind=db_engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_email_sender] = lambda: outbox
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
