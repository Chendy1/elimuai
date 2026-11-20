import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.services.importer import import_pdf
from tests.pdf_factory import make_pdf

PASSWORD = "correct-horse-battery"
BASE = "/admin/curriculum"


def session_as(db_engine, email, role=None):
    c = TestClient(app)
    c.post("/auth/register", json={"email": email, "password": PASSWORD, "display_name": "Person"})
    if role:
        with db_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO user_roles (user_id, role_name) SELECT id, :r FROM users WHERE email = :e"),
                {"r": role, "e": email},
            )
    c.post("/auth/login", json={"email": email, "password": PASSWORD})
    return c


def do_import(db_engine, pdf, title="Demo design"):
    with Session(db_engine) as db:
        result = import_pdf(db, data=pdf, filename="demo.pdf", title=title, publisher="Demo publisher",
                            edition_label="Demo edition")
        return result.source.id, result.created, result.pages_added, result.pages_total


PDF = make_pdf([["Demo cover"], ["Demo foreword", "ii"], ["Demo body text", "13"]])


def test_import_stores_pages_with_both_page_numbers(client, db_engine):
    source_id, created, added, total = do_import(db_engine, PDF)
    assert (created, added, total) == (True, 3, 3)
    with db_engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT pdf_page, printed_page FROM curriculum_source_pages ORDER BY pdf_page")).all()
        source = conn.execute(text(
            "SELECT license_status, page_count, original_filename FROM curriculum_sources")).one()
    assert [(r.pdf_page, r.printed_page) for r in rows] == [(1, None), (2, "ii"), (3, "13")]
    assert source.license_status == "not_requested"
    assert source.page_count == 3 and source.original_filename == "demo.pdf"


def test_importing_the_same_file_again_adds_nothing(client, db_engine):
    first_id, *_ = do_import(db_engine, PDF)
    second_id, created, added, total = do_import(db_engine, PDF)
    assert second_id == first_id
    assert (created, added, total) == (False, 0, 3)
    with db_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM curriculum_source_pages")).scalar() == 3
        assert conn.execute(text("SELECT count(*) FROM curriculum_sources")).scalar() == 1


def test_a_different_file_is_a_different_source(client, db_engine):
    a, *_ = do_import(db_engine, PDF)
    b, created, *_ = do_import(db_engine, make_pdf([["Another demo"]]), title="Other")
    assert a != b and created is True


def test_import_is_audited_without_storing_page_text(client, db_engine):
    do_import(db_engine, PDF)
    with db_engine.connect() as conn:
        row = conn.execute(text(
            "SELECT details::text FROM audit_logs WHERE action = 'curriculum.source_imported'")).scalar_one()
    assert "pages_added" in row and "Demo" not in row


def test_reviewers_can_read_source_pages_but_others_cannot(client, db_engine):
    source_id, *_ = do_import(db_engine, PDF)
    reviewer = session_as(db_engine, "rev@example.com", "content_reviewer")
    listing = reviewer.get(f"{BASE}/sources/{source_id}/pages")
    assert listing.status_code == 200
    assert [p["printed_page"] for p in listing.json()] == [None, "ii", "13"]
    page = reviewer.get(f"{BASE}/sources/{source_id}/pages/3").json()
    assert page["printed_page"] == "13" and "Demo body text" in page["text"]

    assert reviewer.get(f"{BASE}/sources/{source_id}/pages/99").status_code == 404
    assert reviewer.get(f"{BASE}/sources/{uuid.uuid4()}/pages").status_code == 404

    guardian = session_as(db_engine, "g@example.com")
    assert guardian.get(f"{BASE}/sources/{source_id}/pages").status_code == 403
    assert TestClient(app).get(f"{BASE}/sources/{source_id}/pages").status_code == 401


def test_unreadable_pdf_is_rejected_by_the_service(client, db_engine):
    with Session(db_engine) as db, pytest.raises(ValueError):
        import_pdf(db, data=b"not a pdf", filename="x.pdf", title="X", publisher="P")
