import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app

PASSWORD = "correct-horse-battery"


def sign_in(client, email="guardian@example.com"):
    client.post(
        "/auth/register", json={"email": email, "password": PASSWORD, "display_name": "Amina"}
    )
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200
    return r.json()["csrf_token"]


def add(client, csrf, nickname="Zuri", grade=6, accepted=True, version=None):
    version = version or client.get("/learners/consent-notice").json()["version"]
    return client.post(
        "/learners",
        headers={"X-CSRF-Token": csrf},
        json={
            "nickname": nickname,
            "grade": grade,
            "consent": {"notice_version": version, "accepted": accepted},
        },
    )


def test_consent_notice_is_public_and_marked_draft(client):
    r = client.get("/learners/consent-notice")
    assert r.status_code == 200
    body = r.json()
    assert body["is_draft"] is True
    assert body["version"] and "DRAFT" in body["text"]


def test_creating_a_learner_needs_sign_in_and_csrf(client):
    assert add(client, "x", version="0.1-draft").status_code == 401
    csrf = sign_in(client)
    r = client.post(
        "/learners",
        json={"nickname": "Zuri", "grade": 6, "consent": {"notice_version": "0.1-draft", "accepted": True}},
    )
    assert r.status_code == 403
    assert add(client, csrf).status_code == 201


def test_consent_must_be_accepted_and_current(client):
    csrf = sign_in(client)
    assert add(client, csrf, accepted=False).status_code == 422
    assert add(client, csrf, version="0.0-old").status_code == 409
    assert client.get("/learners").json() == []


def test_consent_record_stores_version_and_fingerprint(client, db_engine):
    csrf = sign_in(client)
    assert add(client, csrf).status_code == 201
    with db_engine.connect() as conn:
        row = conn.execute(
            text("SELECT notice_version, notice_sha256, purpose, withdrawn_at FROM consent_records")
        ).one()
    assert row.notice_version == "0.1-draft"
    assert len(row.notice_sha256) == 64
    assert row.purpose == "learner_profile"
    assert row.withdrawn_at is None


@pytest.mark.parametrize("grade,expected", [(3, 422), (4, 201), (9, 201), (10, 422)])
def test_grade_must_be_4_to_9(client, grade, expected):
    csrf = sign_in(client)
    assert add(client, csrf, grade=grade).status_code == expected


@pytest.mark.parametrize("nickname", ["", "   ", "kid@example.com", "0712345678", "x" * 51])
def test_nickname_rules_discourage_personal_data(client, nickname):
    csrf = sign_in(client)
    assert add(client, csrf, nickname=nickname).status_code == 422


def test_nicknames_are_unique_per_guardian_until_removed(client):
    csrf = sign_in(client)
    first = add(client, csrf, nickname="Zuri")
    assert first.status_code == 201
    assert add(client, csrf, nickname="ZURI").status_code == 409
    client.delete(f"/learners/{first.json()['id']}", headers={"X-CSRF-Token": csrf})
    assert add(client, csrf, nickname="Zuri").status_code == 201


def test_a_guardian_has_a_limit_on_learners(client):
    csrf = sign_in(client)
    for i in range(6):
        assert add(client, csrf, nickname=f"Kid{i}").status_code == 201
    assert add(client, csrf, nickname="Kid6").status_code == 409


def test_guardians_cannot_see_or_change_each_others_learners(client):
    csrf_a = sign_in(client, "a@example.com")
    learner_id = add(client, csrf_a).json()["id"]

    other = TestClient(app)
    csrf_b = sign_in(other, "b@example.com")
    assert other.get("/learners").json() == []
    assert other.get(f"/learners/{learner_id}").status_code == 404
    headers = {"X-CSRF-Token": csrf_b}
    assert other.patch(f"/learners/{learner_id}", headers=headers, json={"grade": 7}).status_code == 404
    assert other.delete(f"/learners/{learner_id}", headers=headers).status_code == 404
    assert client.get(f"/learners/{learner_id}").json()["grade"] == 6


def test_update_changes_grade_and_nickname(client):
    csrf = sign_in(client)
    learner_id = add(client, csrf).json()["id"]
    headers = {"X-CSRF-Token": csrf}
    r = client.patch(f"/learners/{learner_id}", headers=headers, json={"grade": 7, "nickname": "Zuri K"})
    assert r.status_code == 200
    assert r.json()["grade"] == 7 and r.json()["nickname"] == "Zuri K"
    assert client.patch(f"/learners/{learner_id}", headers=headers, json={}).status_code == 422
    assert client.patch(f"/learners/{learner_id}", headers=headers, json={"grade": 12}).status_code == 422


def test_removing_a_learner_hides_it_and_withdraws_consent(client, db_engine):
    csrf = sign_in(client)
    learner_id = add(client, csrf).json()["id"]
    assert client.delete(f"/learners/{learner_id}", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/learners").json() == []
    assert client.get(f"/learners/{learner_id}").status_code == 404
    with db_engine.connect() as conn:
        withdrawn = conn.execute(text("SELECT withdrawn_at FROM consent_records")).scalar_one()
    assert withdrawn is not None
