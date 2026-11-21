"""Learner-facing curriculum reads.

Learners (any signed-in user) see only the published version, and only approved content.
Reviewers and admins may add ?version_id=... to preview ANY version, draft included, so they can see
exactly what learners will see before anything is published."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_session_context
from app.core.permissions import P_CONTENT_REVIEW, has_permission
from app.db.session import get_db
from app.models import CurriculumVersion
from app.services import auth as auth_service
from app.services import curriculum as svc
from app.services.auth import AuthContext

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

DEFAULT_CODE = "kenya-cbe"


def resolve_version(
    db: Session, ctx: AuthContext, curriculum: str, version_id: uuid.UUID | None
) -> tuple[CurriculumVersion, bool]:
    """Return (version, is_preview)."""
    if version_id is None:
        version = svc.published_version(db, curriculum)
        if version is None:
            raise HTTPException(status_code=404, detail="No published curriculum is available yet.")
        return version, False
    roles = auth_service.get_roles(db, ctx.user.id)
    if not has_permission(roles, P_CONTENT_REVIEW):
        raise HTTPException(status_code=403, detail="Only reviewers can preview an unpublished version.")
    version = db.get(CurriculumVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Not found.")
    return version, True


@router.get("/grades")
def grades(curriculum: str = Query(DEFAULT_CODE, max_length=50), version_id: uuid.UUID | None = None,
           ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    version, _ = resolve_version(db, ctx, curriculum, version_id)
    return [{"level": g.level, "name": g.name} for g in svc.public_grades(db, version)]


@router.get("/grades/{level}/learning-areas")
def learning_areas(level: int, curriculum: str = Query(DEFAULT_CODE, max_length=50),
                   version_id: uuid.UUID | None = None,
                   ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    version, preview = resolve_version(db, ctx, curriculum, version_id)
    return [{"id": a.id, "name": a.name} for a in svc.public_areas(db, version, level, preview)]


@router.get("/learning-areas/{area_id}")
def learning_area(area_id: uuid.UUID, curriculum: str = Query(DEFAULT_CODE, max_length=50),
                  version_id: uuid.UUID | None = None,
                  ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    version, _ = resolve_version(db, ctx, curriculum, version_id)
    try:
        return svc.public_area_tree(db, version, area_id)
    except svc.NotFound:
        raise HTTPException(status_code=404, detail="Not found.")
