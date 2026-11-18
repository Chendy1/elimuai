import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import permissions as perms
from app.main import app
from app.services.admin import bootstrap_super_admin

PASSWORD = "correct-horse-battery"


# ---------- helpers ----------

def register_and_login(client, email):
    client.post(
        "/auth/register", json={"email": email, "password": PASSWORD, "display_name": "Person"}
    )
    r = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert r.status_code == 200
    return r.json()


@pytest.fixture
def make_admin(db_engine):
    def _make(email="root@example.com"):
        with Session(db_engine) as db:
            bootstrap_super_admin(db, email=email, password=PASSWORD, display_name="Root")
        return email

    return _make


def admin_session(make_admin, email="root@example.com"):
    make_admin(email)
    admin = TestClient(app)
    body = admin.post("/auth/login", json={"email": email, "password": PASSWORD}).json()
    return admin, body["csrf_token"], body["user"]["id"]


def user_id_of(admin, email):
    users = admin.get("/admin/users").json()
    return next(u["id"] for u in users if u["email"] == email)


# ---------- the matrix itself (pure) ----------

def test_super_admin_holds_every_administrative_permission_but_not_own_scoped_ones():
    admin_perms = perms.ROLE_PERMISSIONS[perms.SUPER_ADMIN]
    assert admin_perms == perms.ALL_PERMISSIONS - perms.OWN_SCOPED_PERMISSIONS
    assert not perms.has_permission([perms.SUPER_ADMIN], perms.P_LEARNERS_MANAGE_OWN)


def test_own_scoped_permissions_come_from_exactly_one_role():
    for permission in perms.OWN_SCOPED_PERMISSIONS:
        holders = [r for r in perms.ALL_ROLES if permission in perms.permissions_for(r)]
        assert len(holders) == 1


def test_every_role_is_defined_and_permissions_are_known():
    assert set(perms.ROLE_PERMISSIONS) == set(perms.ALL_ROLES)
    for granted in perms.ROLE_PERMISSIONS.values():
        assert granted <= perms.ALL_PERMISSIONS


def test_least_privilege_for_key_roles():
    assert perms.permissions_for(perms.GUARDIAN) == {perms.P_LEARNERS_MANAGE_OWN}
    assert perms.permissions_for(perms.INSTITUTIONAL_PARTNER) == {perms.P_REPORTS_AGGREGATE_READ}
    for role in perms.ALL_ROLES:
        if role != perms.SUPER_ADMIN:
            assert not perms.has_permission([role], perms.P_USERS_MANAGE_ROLES)
            assert not perms.has_permission([role], perms.P_AUDIT_READ)
    assert perms.permissions_for("made_up_role") == frozenset()


def test_roles_table_matches_the_code(db_engine):
    with db_engine.connect() as conn:
        names = {r[0] for r in conn.execute(text("SELECT name FROM roles"))}
    assert names == set(perms.ALL_ROLES)


# ---------- registration and sessions ----------

def test_registration_assigns_guardian_role(client):
    body = register_and_login(client, "g@example.com")
    assert body["roles"] == ["guardian"]
    assert client.get("/auth/me").json()["roles"] == ["guardian"]


# ---------- enforcement ----------

ADMIN_GETS = ["/admin/users", "/admin/roles", "/admin/audit-logs"]


@pytest.mark.parametrize("path", ADMIN_GETS)
def test_admin_endpoints_need_sign_in_and_permission(client, path):
    assert client.get(path).status_code == 401
    register_and_login(client, "g@example.com")
    assert client.get(path).status_code == 403


def test_a_super_admin_without_guardian_role_cannot_use_guardian_endpoints(client, make_admin):
    admin, csrf, _ = admin_session(make_admin)
    assert admin.get("/learners").status_code == 403
    r = admin.post(
        "/learners",
        headers={"X-CSRF-Token": csrf},
        json={"nickname": "Zuri", "grade": 6, "consent": {"notice_version": "0.1-draft", "accepted": True}},
    )
    assert r.status_code == 403


def test_admin_lists_users_with_roles(client, make_admin):
    register_and_login(client, "g@example.com")
    admin, _, _ = admin_session(make_admin)
    users = {u["email"]: u for u in admin.get("/admin/users").json()}
    assert users["g@example.com"]["roles"] == ["guardian"]
    assert users["root@example.com"]["roles"] == ["super_admin"]
    assert admin.get("/admin/users?limit=0").status_code == 422
    assert "super_admin" in admin.get("/admin/roles").json()


# ---------- changing roles ----------

def test_admin_can_grant_a_role_and_it_takes_effect(client, make_admin):
    register_and_login(client, "g@example.com")
    admin, csrf, _ = admin_session(make_admin)
    target = user_id_of(admin, "g@example.com")
    headers = {"X-CSRF-Token": csrf}

    r = admin.put(f"/admin/users/{target}/roles", headers=headers, json={"roles": ["guardian", "teacher"]})
    assert r.status_code == 200
    assert r.json()["roles"] == ["guardian", "teacher"]
    assert client.get("/auth/me").json()["roles"] == ["guardian", "teacher"]


def test_role_changes_need_csrf_valid_roles_and_an_existing_user(client, make_admin):
    register_and_login(client, "g@example.com")
    admin, csrf, _ = admin_session(make_admin)
    target = user_id_of(admin, "g@example.com")
    url = f"/admin/users/{target}/roles"
    assert admin.put(url, json={"roles": ["teacher"]}).status_code == 403
    headers = {"X-CSRF-Token": csrf}
    assert admin.put(url, headers=headers, json={"roles": ["wizard"]}).status_code == 422
    assert admin.put(url, headers=headers, json={"roles": []}).status_code == 422
    missing = "00000000-0000-0000-0000-000000000000"
    assert admin.put(f"/admin/users/{missing}/roles", headers=headers, json={"roles": ["teacher"]}).status_code == 404


def test_guardians_cannot_change_roles(client, make_admin):
    guardian = register_and_login(client, "g@example.com")
    admin, _, _ = admin_session(make_admin)
    target = user_id_of(admin, "g@example.com")
    r = client.put(
        f"/admin/users/{target}/roles",
        headers={"X-CSRF-Token": guardian["csrf_token"]},
        json={"roles": ["super_admin"]},
    )
    assert r.status_code == 403
    assert client.get("/auth/me").json()["roles"] == ["guardian"]


def test_the_last_super_admin_cannot_be_removed(client, make_admin):
    admin, csrf, admin_id = admin_session(make_admin, "root@example.com")
    headers = {"X-CSRF-Token": csrf}
    url = f"/admin/users/{admin_id}/roles"
    assert admin.put(url, headers=headers, json={"roles": ["guardian"]}).status_code == 409

    make_admin("second@example.com")
    assert admin.put(url, headers=headers, json={"roles": ["guardian"]}).status_code == 200


def test_bootstrap_is_idempotent_and_can_promote_an_existing_account(client, db_engine):
    register_and_login(client, "g@example.com")
    with Session(db_engine) as db:
        bootstrap_super_admin(db, email="g@example.com", password=None)
        bootstrap_super_admin(db, email="g@example.com", password=None)
    with db_engine.connect() as conn:
        roles = [r[0] for r in conn.execute(text(
            "SELECT role_name FROM user_roles JOIN users ON users.id = user_id "
            "WHERE email = 'g@example.com' ORDER BY role_name"))]
        grants = conn.execute(text("SELECT count(*) FROM audit_logs WHERE action = 'user.superadmin_granted'")).scalar()
    assert roles == ["guardian", "super_admin"]
    assert grants == 1


def test_bootstrap_needs_a_password_for_a_new_account(db_engine):
    with Session(db_engine) as db, pytest.raises(ValueError):
        bootstrap_super_admin(db, email="new@example.com", password=None)


# ---------- audit log ----------

def test_audit_log_records_key_events_and_only_admins_can_read_it(client, make_admin):
    guardian = register_and_login(client, "g@example.com")
    headers = {"X-CSRF-Token": guardian["csrf_token"]}
    created = client.post(
        "/learners",
        headers=headers,
        json={"nickname": "Zuri", "grade": 6, "consent": {"notice_version": "0.1-draft", "accepted": True}},
    ).json()
    client.patch(f"/learners/{created['id']}", headers=headers, json={"grade": 7})
    client.delete(f"/learners/{created['id']}", headers=headers)

    admin, csrf, _ = admin_session(make_admin)
    target = user_id_of(admin, "g@example.com")
    admin.put(f"/admin/users/{target}/roles", headers={"X-CSRF-Token": csrf}, json={"roles": ["guardian", "teacher"]})

    actions = {e["action"] for e in admin.get("/admin/audit-logs").json()}
    assert {
        "user.registered", "learner.created", "learner.updated", "learner.removed",
        "user.roles_changed", "user.superadmin_granted",
    } <= actions

    changed = admin.get("/admin/audit-logs?action=user.roles_changed").json()
    assert len(changed) == 1
    assert changed[0]["details"] == {"from": ["guardian"], "to": ["guardian", "teacher"]}
    assert changed[0]["target_id"] == target

    assert client.get("/admin/audit-logs").status_code == 403


def test_audit_details_never_contain_a_childs_nickname(client, db_engine):
    guardian = register_and_login(client, "g@example.com")
    client.post(
        "/learners",
        headers={"X-CSRF-Token": guardian["csrf_token"]},
        json={"nickname": "Zuriuniquename", "grade": 6, "consent": {"notice_version": "0.1-draft", "accepted": True}},
    )
    with db_engine.connect() as conn:
        dump = " ".join(str(r[0]) for r in conn.execute(text("SELECT details::text FROM audit_logs WHERE details IS NOT NULL")))
    assert "Zuriuniquename" not in dump


def test_password_reset_completion_is_audited(client, outbox, db_engine):
    register_and_login(client, "g@example.com")
    client.post("/auth/password-reset/request", json={"email": "g@example.com"})
    token = outbox.sent[-1][1].split("token=")[1]
    r = client.post("/auth/password-reset/confirm", json={"token": token, "new_password": "a-brand-new-passphrase"})
    assert r.status_code == 204
    with db_engine.connect() as conn:
        n = conn.execute(text("SELECT count(*) FROM audit_logs WHERE action = 'auth.password_reset_completed'")).scalar()
    assert n == 1
