import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.permissions import (
    ALL_ROLES,
    P_AUDIT_READ,
    P_USERS_MANAGE_ROLES,
    P_USERS_READ,
    ROLE_PERMISSIONS,
)
from app.db.session import get_db
from app.schemas.admin import AdminUserOut, AuditLogOut, RolesUpdate
from app.services import admin as admin_service
from app.services import audit
from app.services.auth import AuthContext

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/roles", response_model=dict[str, list[str]])
def role_matrix(ctx: AuthContext = Depends(require_permission(P_USERS_READ))):
    return {role: sorted(ROLE_PERMISSIONS[role]) for role in ALL_ROLES}


@router.get("/users", response_model=list[AdminUserOut])
def list_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    ctx: AuthContext = Depends(require_permission(P_USERS_READ)),
    db: Session = Depends(get_db),
):
    return admin_service.list_users(db, limit, offset)


@router.put("/users/{user_id}/roles", response_model=AdminUserOut)
def set_user_roles(
    user_id: uuid.UUID,
    body: RolesUpdate,
    ctx: AuthContext = Depends(require_permission(P_USERS_MANAGE_ROLES, csrf=True)),
    db: Session = Depends(get_db),
):
    try:
        return admin_service.set_roles(db, actor=ctx.user, target_id=user_id, roles=body.roles)
    except admin_service.UserNotFound:
        raise HTTPException(status_code=404, detail="User not found.")
    except admin_service.LastSuperAdmin:
        raise HTTPException(
            status_code=409, detail="At least one super administrator must remain."
        )


@router.get("/audit-logs", response_model=list[AuditLogOut])
def audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: str | None = Query(None, max_length=64),
    ctx: AuthContext = Depends(require_permission(P_AUDIT_READ)),
    db: Session = Depends(get_db),
):
    return audit.list_events(db, limit, offset, action)
