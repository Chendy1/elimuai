import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.services import curriculum as cs
from app.services.importer import propose_from_source
from tests.layout_fixtures import PAGES

PASSWORD = "correct-horse-battery"
BASE = "/admin/curriculum"
SHA = "b" * 64


def admin_session(db_engine):
    c = TestClient(app)
    c.post("/auth/register", json={"email": "ca@example.com", "password": PASSWORD, "display_name": "Admin"})
    with db_engine.begin() as conn:
        conn.execute(text("INSERT INTO user_roles (user_id, role_name) SELECT id, 'curriculum_admin' FROM users"))
    csrf = c.post("/auth/login", json={"email": "ca@example.com", "password": PASSWORD}).json()["csrf_token"]
    return c, {"X-CSRF-Token": csrf}


def setup(db_engine, pages=PAGES):
    c, h = admin_session(db_engine)
    cur = c.post(f"{BASE}/curricula", headers=h, json={"code": "demo-cbe", "name": "Demo"}).json()
    version = c.post(f"{BASE}/curricula/{cur['id']}/versions", headers=h, json={"label": "Draft"}).json()
    src = c.post(f"{BASE}/sources", headers=h,
                 json={"title": "Demo design", "publisher": "Demo publisher", "file_sha256": SHA}).json()
    with Session(db_engine) as db:
        for p in pages:
            cs.add_source_page(db, uuid.UUID(src["id"]), p.pdf_page, p.printed_page, p.text)
    return c, h, version["id"], uuid.UUID(src["id"])


def run(db_engine, version_id, source_id, **kw):
    with Session(db_engine) as db:
        return propose_from_source(db, source_id=source_id, version_id=uuid.UUID(version_id),
                                   grade_level=6, grade_name="Grade 6", area_name="Demo Mathematics", **kw)


def test_dry_run_reports_counts_and_writes_nothing(client, db_engine):
    c, h, version_id, source_id = setup(db_engine)
    result = run(db_engine, version_id, source_id, dry_run=True)
    assert (result.strands, result.sub_strands, result.outcomes) == (2, 3, 6)
    assert result.written is False
    assert any("PCI text has no name" in w for w in result.warnings)
    tree = c.get(f"{BASE}/versions/{version_id}/tree").json()
    assert tree["grades"] == []


def test_proposal_creates_draft_records_with_sources_and_notes(client, db_engine):
    c, h, version_id, source_id = setup(db_engine)
    result = run(db_engine, version_id, source_id)
    assert result.written is True

    area = c.get(f"{BASE}/versions/{version_id}/tree").json()["grades"][0]["learning_areas"][0]
    assert area["name"] == "Demo Mathematics" and area["review_status"] == "draft"
    assert [s["number"] for s in area["strands"]] == ["1.0", "2.0"]
    first = area["strands"][0]["sub_strands"][0]
    assert first["review_status"] == "draft" and first["source_page_id"]
    assert [o["code"] for o in first["outcomes"]] == ["a", "b", "c"]
    assert first["competencies"][0]["code"] == "critical_thinking"
    assert "Auto-extracted from PDF pages 13-13" in first["review_comment"]
    assert "PCI text has no name" in first["review_comment"]
    assert len(area["strands"][0]["rubric"]) == 2
    second = area["strands"][0]["sub_strands"][1]
    assert second["pcis"][0]["name"] == "Safety"


def test_proposed_records_cannot_be_published_until_reviewed(client, db_engine):
    c, h, version_id, source_id = setup(db_engine)
    run(db_engine, version_id, source_id)
    blocked = c.post(f"{BASE}/versions/{version_id}/publish", headers=h, json={})
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["details"]["unapproved"]["sub_strand"] == 3


def test_running_the_proposal_twice_is_refused(client, db_engine):
    _, _, version_id, source_id = setup(db_engine)
    run(db_engine, version_id, source_id)
    with pytest.raises(cs.Conflict):
        run(db_engine, version_id, source_id)


def test_unsupported_layouts_are_reported_not_guessed(client, db_engine):
    from tests.layout_fixtures import Page

    _, _, version_id, source_id = setup(db_engine, pages=[Page(1, None, "Just prose.\nNothing to parse.")])
    with pytest.raises(cs.Conflict):
        run(db_engine, version_id, source_id)


def test_proposal_needs_a_draft_version_and_a_known_source(client, db_engine):
    c, h, version_id, source_id = setup(db_engine)
    with Session(db_engine) as db, pytest.raises(cs.NotFound):
        propose_from_source(db, source_id=uuid.uuid4(), version_id=uuid.UUID(version_id), grade_level=6,
                            grade_name="Grade 6", area_name="X")
    with db_engine.begin() as conn:
        conn.execute(text("UPDATE curriculum_versions SET status = 'archived'"))
    with pytest.raises(cs.Conflict):
        run(db_engine, version_id, source_id)
