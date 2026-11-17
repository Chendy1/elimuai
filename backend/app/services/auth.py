from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    dummy_hash,
    hash_password,
    hash_token,
    new_token,
    password_needs_rehash,
    verify_password,
)
from app.models import AuthSession, PasswordResetToken, User

LAST_SEEN_REFRESH = timedelta(minutes=5)


class EmailAlreadyRegistered(Exception):
    pass


@dataclass
class AuthContext:
    user: User
    session: AuthSession


def utcnow() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == normalize_email(email), User.deleted_at.is_(None))
    )


def create_user(db: Session, *, email: str, password: str, display_name: str) -> User:
    email = normalize_email(email)
    if db.scalar(select(User.id).where(User.email == email)) is not None:
        raise EmailAlreadyRegistered
    user = User(email=email, password_hash=hash_password(password), display_name=display_name.strip())
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:  # lost a race with another registration
        db.rollback()
        raise EmailAlreadyRegistered from exc
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = get_user_by_email(db, email)
    if user is None or not user.is_active:
        verify_password(dummy_hash(), password)  # keep timing similar
        return None
    if not verify_password(user.password_hash, password):
        return None
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    user.last_login_at = utcnow()
    db.commit()
    return user


def create_session(db: Session, user: User) -> tuple[AuthSession, str]:
    raw = new_token()
    now = utcnow()
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(raw),
        csrf_token=new_token(),
        expires_at=now + timedelta(hours=get_settings().session_ttl_hours),
        last_seen_at=now,
    )
    db.add(session)
    db.commit()
    return session, raw


def get_valid_session(db: Session, raw_token: str) -> AuthContext | None:
    now = utcnow()
    row = db.execute(
        select(AuthSession, User)
        .join(User, User.id == AuthSession.user_id)
        .where(
            AuthSession.token_hash == hash_token(raw_token),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > now,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
    ).first()
    if row is None:
        return None
    session, user = row
    if now - session.last_seen_at > LAST_SEEN_REFRESH:
        session.last_seen_at = now
        db.commit()
    return AuthContext(user=user, session=session)


def revoke_session(db: Session, session: AuthSession) -> None:
    session.revoked_at = utcnow()
    db.commit()


def create_reset_token(db: Session, user: User) -> str:
    db.execute(
        delete(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id, PasswordResetToken.used_at.is_(None)
        )
    )
    raw = new_token()
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw),
            expires_at=utcnow() + timedelta(minutes=get_settings().reset_token_ttl_minutes),
        )
    )
    db.commit()
    return raw


def consume_reset_token(db: Session, raw_token: str, new_password: str) -> bool:
    now = utcnow()
    token = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == hash_token(raw_token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        .with_for_update()
    )
    if token is None:
        return False
    user = db.get(User, token.user_id)
    if user is None or not user.is_active or user.deleted_at is not None:
        return False
    user.password_hash = hash_password(new_password)
    token.used_at = now
    db.execute(
        update(AuthSession)
        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()
    return True
