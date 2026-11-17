from sqlalchemy import text

PASSWORD = "correct-horse-battery"
EMAIL = "guardian@example.com"


def register(client, email=EMAIL, password=PASSWORD, name="Amina"):
    return client.post(
        "/auth/register", json={"email": email, "password": password, "display_name": name}
    )


def login(client, email=EMAIL, password=PASSWORD):
    return client.post("/auth/login", json={"email": email, "password": password})


def signed_in(client):
    assert register(client).status_code == 201
    r = login(client)
    assert r.status_code == 200
    return r.json()["csrf_token"]


def sql(db_engine, statement):
    with db_engine.begin() as conn:
        conn.execute(text(statement))


# ---------- registration ----------

def test_register_creates_guardian_and_hides_password(client):
    r = register(client, email="Guardian@Example.com")
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == EMAIL
    assert body["display_name"] == "Amina"
    assert "password" not in body and "password_hash" not in body


def test_password_is_stored_as_argon2id(client, db_engine):
    register(client)
    with db_engine.connect() as conn:
        stored = conn.execute(text("SELECT password_hash FROM users")).scalar_one()
    assert stored.startswith("$argon2id$")


def test_duplicate_email_is_rejected_case_insensitively(client):
    assert register(client).status_code == 201
    assert register(client, email="GUARDIAN@example.com").status_code == 409


def test_weak_password_is_rejected(client):
    assert register(client, password="short").status_code == 422
    assert register(client, password="password123").status_code == 422
    assert register(client, password=EMAIL).status_code == 422


def test_invalid_email_is_rejected(client):
    assert register(client, email="not-an-email").status_code == 422


# ---------- login / session ----------

def test_login_sets_httponly_lax_cookie_and_returns_csrf(client):
    register(client)
    r = login(client)
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "elimu_session=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert r.json()["csrf_token"]
    assert r.json()["user"]["email"] == EMAIL


def test_wrong_password_and_unknown_email_give_same_error(client):
    register(client)
    wrong = login(client, password="wrong-password-123")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_me_requires_a_session(client):
    assert client.get("/auth/me").status_code == 401
    signed_in(client)
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["user"]["email"] == EMAIL


def test_expired_session_is_rejected(client, db_engine):
    signed_in(client)
    sql(db_engine, "UPDATE sessions SET expires_at = now() - interval '1 minute'")
    assert client.get("/auth/me").status_code == 401


def test_inactive_and_deleted_accounts_cannot_sign_in(client, db_engine):
    register(client)
    sql(db_engine, "UPDATE users SET is_active = false")
    assert login(client).status_code == 401
    sql(db_engine, "UPDATE users SET is_active = true, deleted_at = now()")
    assert login(client).status_code == 401


def test_login_is_rate_limited_per_email(client):
    register(client)
    statuses = [login(client, password="wrong-password-123").status_code for _ in range(9)]
    assert statuses[:8] == [401] * 8
    last = login(client, password="wrong-password-123")
    assert statuses[8] == 429
    assert last.status_code == 429
    assert "retry-after" in {k.lower() for k in last.headers}


# ---------- logout / CSRF ----------

def test_logout_requires_csrf_token(client):
    csrf = signed_in(client)
    assert client.post("/auth/logout").status_code == 403
    assert client.post("/auth/logout", headers={"X-CSRF-Token": "wrong"}).status_code == 403
    assert client.get("/auth/me").status_code == 200  # still signed in
    assert client.post("/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/auth/me").status_code == 401


def test_logout_without_session_is_unauthorised(client):
    assert client.post("/auth/logout", headers={"X-CSRF-Token": "x"}).status_code == 401


# ---------- password reset ----------

def reset_token_from(outbox):
    return outbox.sent[-1][1].split("token=")[1]


def test_reset_request_never_reveals_whether_account_exists(client, outbox):
    register(client)
    known = client.post("/auth/password-reset/request", json={"email": EMAIL})
    unknown = client.post("/auth/password-reset/request", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [to for to, _ in outbox.sent] == [EMAIL]


def test_reset_flow_changes_password_revokes_sessions_and_is_single_use(client, outbox):
    signed_in(client)
    client.post("/auth/password-reset/request", json={"email": EMAIL})
    token = reset_token_from(outbox)

    new_password = "a-brand-new-passphrase"
    r = client.post(
        "/auth/password-reset/confirm", json={"token": token, "new_password": new_password}
    )
    assert r.status_code == 204
    assert client.get("/auth/me").status_code == 401  # old session revoked
    assert login(client).status_code == 401  # old password no longer works
    assert login(client, password=new_password).status_code == 200

    again = client.post(
        "/auth/password-reset/confirm", json={"token": token, "new_password": "another-passphrase-1"}
    )
    assert again.status_code == 400


def test_weak_new_password_is_rejected_without_burning_the_token(client, outbox):
    register(client)
    client.post("/auth/password-reset/request", json={"email": EMAIL})
    token = reset_token_from(outbox)
    weak = client.post(
        "/auth/password-reset/confirm", json={"token": token, "new_password": "short"}
    )
    assert weak.status_code == 422
    ok = client.post(
        "/auth/password-reset/confirm", json={"token": token, "new_password": "a-brand-new-passphrase"}
    )
    assert ok.status_code == 204


def test_expired_or_bogus_reset_token_is_rejected(client, outbox, db_engine):
    register(client)
    client.post("/auth/password-reset/request", json={"email": EMAIL})
    token = reset_token_from(outbox)
    sql(db_engine, "UPDATE password_reset_tokens SET expires_at = now() - interval '1 minute'")
    body = {"token": token, "new_password": "a-brand-new-passphrase"}
    assert client.post("/auth/password-reset/confirm", json=body).status_code == 400
    bogus = {"token": "x" * 43, "new_password": "a-brand-new-passphrase"}
    assert client.post("/auth/password-reset/confirm", json=bogus).status_code == 400


def test_new_reset_request_invalidates_the_previous_link(client, outbox):
    register(client)
    client.post("/auth/password-reset/request", json={"email": EMAIL})
    first = reset_token_from(outbox)
    client.post("/auth/password-reset/request", json={"email": EMAIL})
    body = {"token": first, "new_password": "a-brand-new-passphrase"}
    assert client.post("/auth/password-reset/confirm", json=body).status_code == 400
