import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.permissions import SUPER_ADMIN
from app.core.security import hash_password
from app.models import User, UserRole
from app.services import audit
from app.services.auth import get_roles, get_user_by_email, normalize_email


class UserNotFound(Exception):
    pass


class LastSuperAdmin(Exception):
    pass


def _count_super_admins(db: Session) -> int:
    return db.scalar(
        select(func.count())
        .select_from(UserRole)
        .join(User, User.id == UserRole.user_id)
        .where(
            UserRole.role_name == SUPER_ADMIN,
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
    )


def _out(user: User, roles: list[str]) -> dict[str, Any]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "is_active": user.is_active,
        "roles": sorted(roles),
    }


def list_users(db: Session, limit: int, offset: int) -> list[dict[str, Any]]:
    users = list(
        db.scalars(
            select(User)
            .where(User.deleted_at.is_(None))
            .order_by(User.created_at, User.id)
            .offset(offset)
            .limit(limit)
        )
    )
    ids = [u.id for u in users]
    by_user: dict[uuid.UUID, list[str]] = defaultdict(list)
    if ids:
        for uid, role in db.execute(
            select(UserRole.user_id, UserRole.role_name).where(UserRole.user_id.in_(ids))
        ):
            by_user[uid].append(role)
    return [_out(u, by_user[u.id]) for u in users]


def set_roles(db: Session, *, actor: User, target_id: uuid.UUID, roles: list[str]) -> dict[str, Any]:
    target = db.scalar(select(User).where(User.id == target_id, User.deleted_at.is_(None)))
    if target is None:
        raise UserNotFound
    current = sorted(get_roles(db, target.id))
    new = sorted(set(roles))
    if SUPER_ADMIN in current and SUPER_ADMIN not in new and _count_super_admins(db) <= 1:
        raise LastSuperAdmin
    db.execute(delete(UserRole).where(UserRole.user_id == target.id))
    db.add_all([UserRole(user_id=target.id, role_name=r) for r in new])
    audit.record(
        db, actor_id=actor.id, action="user.roles_changed", target_type="user",
        target_id=str(target.id), details={"from": current, "to": new},
    )
    db.commit()
    return _out(target, new)


def bootstrap_super_admin(
    db: Session, *, email: str, password: str | None, display_name: str = "Administrator"
) -> User:
    """Create a super administrator (or grant the role to an existing account). Idempotent."""
    user = get_user_by_email(db, email)
    if user is None:
        if not password:
            raise ValueError("A password is required to create a new account.")
        user = User(
            email=normalize_email(email),
            password_hash=hash_password(password),
            display_name=display_name,
        )
        db.add(user)
        db.flush()
    if SUPER_ADMIN not in get_roles(db, user.id):
        db.add(UserRole(user_id=user.id, role_name=SUPER_ADMIN))
        audit.record(
            db, actor_id=user.id, action="user.superadmin_granted", target_type="user",
            target_id=str(user.id),
        )
    db.commit()
    return user
