"""Curriculum engine tests. All content here is obviously fake demo data."""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.main import app
from app.services.curriculum import add_source_page

PASSWORD = "correct-horse-battery"
BASE = "/admin/curriculum"
SHA = "a" * 64


# ---------- helpers ----------

def session_as(db_engine, email, role=None):
    c = TestClient(app)
    c.post("/auth/register", json={"email": email, "password": PASSWORD, "display_name": "Person"})
    if role:
        with db_engine.begin() as conn:
            conn.execute(
                text("INSERT INTO user_roles (user_id, role_name) SELECT id, :r FROM users WHERE email = :e"),
                {"r": role, "e": email},
            )
    csrf = c.post("/auth/login", json={"email": email, "password": PASSWORD}).json()["csrf_token"]
    return c, {"X-CSRF-Token": csrf}


@pytest.fixture
def admin(client, db_engine):
    return session_as(db_engine, "cadmin@example.com", "curriculum_admin")


def post(c, h, url, body):
    return c.post(url, headers=h, json=body)


def make_curriculum(c, h, code="demo-cbe"):
    r = post(c, h, f"{BASE}/curricula", {"code": code, "name": "Demo curriculum"})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def make_tree(c, h, curriculum_id, label="Demo v1", source_page_id=None, area_name="Demo Area"):
    v = post(c, h, f"{BASE}/curricula/{curriculum_id}/versions", {"label": label}).json()
    g = post(c, h, f"{BASE}/versions/{v['id']}/grades", {"level": 6, "name": "Grade 6"}).json()
    a = post(c, h, f"{BASE}/grades/{g['id']}/learning-areas",
             {"name": area_name, "source_page_id": source_page_id})
    assert a.status_code == 201, a.text
    a = a.json()
    st = post(c, h, f"{BASE}/learning-areas/{a['id']}/strands", {
        "number": "1.0", "name": "Demo Strand",
        "rubric": [{"indicator": "Demo indicator", "exceeds": "E", "meets": "M", "approaches": "A", "below": "B"}],
    }).json()
    sub = post(c, h, f"{BASE}/strands/{st['id']}/sub-strands", {
        "number": "1.1", "name": "Demo Sub-strand", "suggested_lessons": 5,
        "topics": ["Demo topic one", "Demo topic two"],
        "outcomes": [{"code": "a", "text": "Demo outcome one"}, {"code": "b", "text": "Demo outcome two"}],
        "experiences": ["Demo experience"],
        "inquiry_questions": ["Demo question?"],
        "competencies": [{"code": "critical_thinking", "description": "Demo note"}],
        "values": [{"name": "Unity", "description": "Demo"}],
        "pcis": [{"name": "Safety"}],
    })
    assert sub.status_code == 201, sub.text
    return {"version": v["id"], "grade": g["id"], "area": a["id"], "strand": st["id"], "sub": sub.json()["id"]}


def approve(c, h, kind, node_id):
    r = post(c, h, f"{BASE}/review", {"kind": kind, "id": node_id, "status": "approved"})
    assert r.status_code == 204, r.text


def approve_all(c, h, ids):
    approve(c, h, "learning_area", ids["area"])
    approve(c, h, "strand", ids["strand"])
    approve(c, h, "sub_strand", ids["sub"])


def tree_area(c, version_id):
    return c.get(f"{BASE}/versions/{version_id}/tree").json()["grades"][0]["learning_areas"][0]


# ---------- permissions ----------

def test_admin_curriculum_endpoints_are_permission_protected(client, db_engine, admin):
    guardian, gh = session_as(db_engine, "g@example.com")
    assert guardian.get(f"{BASE}/curricula").status_code == 403
    assert post(guardian, gh, f"{BASE}/curricula", {"code": "x-cbe", "name": "X"}).status_code == 403
    anon = TestClient(app)
    assert anon.get(f"{BASE}/curricula").status_code == 401

    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    reviewer, rh = session_as(db_engine, "rev@example.com", "content_reviewer")
    assert reviewer.get(f"{BASE}/curricula").status_code == 403  # cannot manage structure
    assert post(reviewer, rh, f"{BASE}/review",
                {"kind": "strand", "id": ids["strand"], "status": "in_review"}).status_code == 204
    assert post(reviewer, rh, f"{BASE}/versions/{ids['version']}/publish", {}).status_code == 403


def test_core_competencies_are_seeded(db_engine):
    with db_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM core_competencies")).scalar() == 7


# ---------- structure and duplicates ----------

def test_duplicates_and_bad_input_are_rejected(admin):
    c, h = admin
    cid = make_curriculum(c, h)
    assert post(c, h, f"{BASE}/curricula", {"code": "demo-cbe", "name": "Again"}).status_code == 409
    assert post(c, h, f"{BASE}/curricula", {"code": "Bad Code!", "name": "X"}).status_code == 422

    ids = make_tree(c, h, cid)
    assert post(c, h, f"{BASE}/curricula/{cid}/versions", {"label": "Demo v1"}).status_code == 409
    assert post(c, h, f"{BASE}/versions/{ids['version']}/grades", {"level": 6, "name": "Dup"}).status_code == 409
    assert post(c, h, f"{BASE}/versions/{ids['version']}/grades", {"level": 13, "name": "X"}).status_code == 422
    assert post(c, h, f"{BASE}/grades/{ids['grade']}/learning-areas", {"name": "demo area"}).status_code == 409
    dup = post(c, h, f"{BASE}/strands/{ids['strand']}/sub-strands", {"number": "1.1", "name": "Again"})
    assert dup.status_code == 409


def test_sub_strand_content_is_stored_and_read_back(admin, db_engine):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    sub = tree_area(c, ids["version"])["strands"][0]["sub_strands"][0]
    assert sub["suggested_lessons"] == 5
    assert sub["topics"] == ["Demo topic one", "Demo topic two"]
    assert [o["code"] for o in sub["outcomes"]] == ["a", "b"]
    assert sub["competencies"][0]["code"] == "critical_thinking"
    assert sub["values"][0]["name"] == "Unity"
    assert sub["pcis"][0]["name"] == "Safety"
    strand = tree_area(c, ids["version"])["strands"][0]
    assert strand["rubric"][0]["meets"] == "M"
    assert sub["review_status"] == "draft"

    # values are shared across sub-strands, matched case-insensitively
    second = post(c, h, f"{BASE}/strands/{ids['strand']}/sub-strands",
                  {"number": "1.2", "name": "Second", "values": [{"name": "unity"}]})
    assert second.status_code == 201
    with db_engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM curriculum_values")).scalar() == 1


def test_unknown_competency_is_rejected(admin):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    r = post(c, h, f"{BASE}/strands/{ids['strand']}/sub-strands",
             {"number": "9.9", "name": "X", "competencies": [{"code": "made_up"}]})
    assert r.status_code == 409


def test_a_strand_can_only_use_a_unit_from_its_own_learning_area(admin):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    other = post(c, h, f"{BASE}/grades/{ids['grade']}/learning-areas", {"name": "Other Area"}).json()
    unit = post(c, h, f"{BASE}/learning-areas/{ids['area']}/units", {"number": "1.0", "title": "Demo Unit"}).json()
    bad = post(c, h, f"{BASE}/learning-areas/{other['id']}/strands",
               {"number": "1.0", "name": "S", "unit_id": unit["id"]})
    assert bad.status_code == 409
    good = post(c, h, f"{BASE}/learning-areas/{ids['area']}/strands",
                {"number": "2.0", "name": "S2", "unit_id": unit["id"]})
    assert good.status_code == 201


# ---------- review and publishing ----------

def test_review_changes_status_and_validates_input(admin):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    r = post(c, h, f"{BASE}/review",
             {"kind": "sub_strand", "id": ids["sub"], "status": "rejected", "comment": "Check outcome b"})
    assert r.status_code == 204
    sub = tree_area(c, ids["version"])["strands"][0]["sub_strands"][0]
    assert sub["review_status"] == "rejected" and sub["review_comment"] == "Check outcome b"
    assert post(c, h, f"{BASE}/review", {"kind": "sub_strand", "id": ids["sub"], "status": "shipped"}).status_code == 422
    missing = str(uuid.uuid4())
    assert post(c, h, f"{BASE}/review", {"kind": "strand", "id": missing, "status": "approved"}).status_code == 404


def test_nothing_is_published_until_everything_is_approved(admin):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    publish = f"{BASE}/versions/{ids['version']}/publish"

    blocked = post(c, h, publish, {})
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["details"]["unapproved"]["sub_strand"] == 1

    approve(c, h, "learning_area", ids["area"])
    approve(c, h, "strand", ids["strand"])
    assert post(c, h, publish, {}).status_code == 409  # sub-strand still unapproved

    approve(c, h, "sub_strand", ids["sub"])
    ok = post(c, h, publish, {})
    assert ok.status_code == 200 and ok.json()["status"] == "published"
    assert post(c, h, publish, {}).status_code == 409  # already published


def test_an_empty_version_cannot_be_published(admin):
    c, h = admin
    cid = make_curriculum(c, h)
    v = post(c, h, f"{BASE}/curricula/{cid}/versions", {"label": "Empty"}).json()
    assert post(c, h, f"{BASE}/versions/{v['id']}/publish", {}).status_code == 409


def test_published_versions_are_read_only(admin):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    approve_all(c, h, ids)
    assert post(c, h, f"{BASE}/versions/{ids['version']}/publish", {}).status_code == 200
    assert post(c, h, f"{BASE}/grades/{ids['grade']}/learning-areas", {"name": "Late Area"}).status_code == 409
    assert post(c, h, f"{BASE}/review", {"kind": "strand", "id": ids["strand"], "status": "draft"}).status_code == 409
    assert c.patch(f"{BASE}/learning-areas/{ids['area']}", headers=h, json={"name": "New"}).status_code == 409


def test_publishing_a_new_version_archives_the_previous_one(admin):
    c, h = admin
    cid = make_curriculum(c, h)
    v1 = make_tree(c, h, cid, label="Demo v1")
    approve_all(c, h, v1)
    assert post(c, h, f"{BASE}/versions/{v1['version']}/publish", {}).status_code == 200

    v2 = make_tree(c, h, cid, label="Demo v2")
    approve_all(c, h, v2)
    assert post(c, h, f"{BASE}/versions/{v2['version']}/publish", {}).status_code == 200

    status = {v["label"]: v["status"] for v in c.get(f"{BASE}/curricula/{cid}/versions").json()}
    assert status == {"Demo v1": "archived", "Demo v2": "published"}


def test_archived_learning_areas_do_not_block_publishing_and_are_hidden(admin, db_engine):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h, "kenya-cbe"))
    approve_all(c, h, ids)
    extra = post(c, h, f"{BASE}/grades/{ids['grade']}/learning-areas", {"name": "Never Approved"}).json()
    assert post(c, h, f"{BASE}/versions/{ids['version']}/publish", {}).status_code == 409
    r = c.patch(f"{BASE}/learning-areas/{extra['id']}", headers=h, json={"archived": True})
    assert r.status_code == 200 and r.json()["archived"] is True
    assert post(c, h, f"{BASE}/versions/{ids['version']}/publish", {}).status_code == 200

    learner_side, _ = session_as(db_engine, "g@example.com")
    areas = learner_side.get("/curriculum/grades/6/learning-areas").json()
    assert [a["name"] for a in areas] == ["Demo Area"]


# ---------- licensing gate ----------

def test_sources_need_recorded_permission_before_publishing(admin, db_engine):
    c, h = admin
    src = post(c, h, f"{BASE}/sources", {
        "title": "Demo design", "publisher": "Demo publisher", "file_sha256": SHA, "page_count": 10,
    })
    assert src.status_code == 201 and src.json()["license_status"] == "not_requested"
    source_id = src.json()["id"]
    assert post(c, h, f"{BASE}/sources", {"title": "Again", "publisher": "P", "file_sha256": SHA}).status_code == 409

    with Session(db_engine) as db:
        page = add_source_page(db, uuid.UUID(source_id), 7, "vii", "Demo page text")
        page_id = str(page.id)

    ids = make_tree(c, h, make_curriculum(c, h), source_page_id=page_id)
    approve_all(c, h, ids)
    publish = f"{BASE}/versions/{ids['version']}/publish"
    blocked = post(c, h, publish, {})
    assert blocked.status_code == 409
    assert blocked.json()["detail"]["details"]["sources"] == ["Demo design"]

    bad = c.patch(f"{BASE}/sources/{source_id}/license", headers=h, json={"license_status": "maybe"})
    assert bad.status_code == 422
    for status in ("requested", "denied"):
        c.patch(f"{BASE}/sources/{source_id}/license", headers=h, json={"license_status": status})
        assert post(c, h, publish, {}).status_code == 409

    granted = c.patch(f"{BASE}/sources/{source_id}/license", headers=h,
                      json={"license_status": "granted", "license_notes": "Demo letter ref"})
    assert granted.status_code == 200
    assert post(c, h, publish, {}).status_code == 200


# ---------- learner-facing reads ----------

def test_learners_only_see_published_curriculum(admin, db_engine):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h, "kenya-cbe"))
    guardian, _ = session_as(db_engine, "g@example.com")

    assert TestClient(app).get("/curriculum/grades").status_code == 401
    assert guardian.get("/curriculum/grades").status_code == 404

    approve_all(c, h, ids)
    assert guardian.get(f"/curriculum/learning-areas/{ids['area']}").status_code == 404  # still draft
    assert post(c, h, f"{BASE}/versions/{ids['version']}/publish", {}).status_code == 200

    assert guardian.get("/curriculum/grades").json() == [{"level": 6, "name": "Grade 6"}]
    areas = guardian.get("/curriculum/grades/6/learning-areas").json()
    assert [a["name"] for a in areas] == ["Demo Area"]
    tree = guardian.get(f"/curriculum/learning-areas/{areas[0]['id']}").json()
    sub = tree["strands"][0]["sub_strands"][0]
    assert sub["outcomes"][0]["text"] == "Demo outcome one"
    assert "review_status" not in tree and "review_status" not in sub
    assert guardian.get("/curriculum/grades/9/learning-areas").json() == []


# ---------- audit ----------

def test_curriculum_actions_are_audited(admin, db_engine):
    c, h = admin
    ids = make_tree(c, h, make_curriculum(c, h))
    approve_all(c, h, ids)
    post(c, h, f"{BASE}/versions/{ids['version']}/publish", {})
    with db_engine.connect() as conn:
        actions = {r[0] for r in conn.execute(text("SELECT action FROM audit_logs"))}
    assert {"curriculum.created", "curriculum.version_created", "curriculum.review_set",
            "curriculum.version_published"} <= actions
