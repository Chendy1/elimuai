import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.permissions import has_permission
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.services import auth as auth_service

SESSION_COOKIE = "elimu_session"


def client_ip(request: Request) -> str:
    # Behind a proxy this needs trusted X-Forwarded-For handling (Phase 11).
    return request.client.host if request.client else "unknown"


def enforce_rate_limit(key: str, limit: int, window_seconds: int) -> None:
    retry_after = limiter.check(key, limit, window_seconds)
    if retry_after is not None:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def get_session_context(
    request: Request, db: Session = Depends(get_db)
) -> auth_service.AuthContext:
    token = request.cookies.get(SESSION_COOKIE)
    ctx = auth_service.get_valid_session(db, token) if token else None
    if ctx is None:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return ctx


def require_csrf(
    request: Request, ctx: auth_service.AuthContext = Depends(get_session_context)
) -> auth_service.AuthContext:
    sent = request.headers.get("x-csrf-token", "")
    if not secrets.compare_digest(sent.encode(), ctx.session.csrf_token.encode()):
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid.")
    return ctx


def require_permission(permission: str, *, csrf: bool = False):
    """Dependency factory: signed in, holds a role granting `permission`, and (optionally) a
    valid CSRF token. Missing permission is 403; missing session is 401."""
    base = require_csrf if csrf else get_session_context

    def dependency(
        ctx: auth_service.AuthContext = Depends(base), db: Session = Depends(get_db)
    ) -> auth_service.AuthContext:
        roles = auth_service.get_roles(db, ctx.user.id)
        if not has_permission(roles, permission):
            raise HTTPException(status_code=403, detail="You do not have permission to do that.")
        ctx.roles = roles
        return ctx

    return dependency
