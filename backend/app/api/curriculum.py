"""Learner-facing curriculum reads. Only a published version is visible, and only to signed-in users."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_session_context
from app.db.session import get_db
from app.services import curriculum as svc
from app.services.auth import AuthContext

router = APIRouter(prefix="/curriculum", tags=["curriculum"])

DEFAULT_CODE = "kenya-cbe"
NOT_PUBLISHED = HTTPException(status_code=404, detail="No published curriculum is available yet.")


@router.get("/grades")
def grades(curriculum: str = Query(DEFAULT_CODE, max_length=50),
           ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    version = svc.published_version(db, curriculum)
    if version is None:
        raise NOT_PUBLISHED
    return [{"level": g.level, "name": g.name} for g in svc.public_grades(db, version)]


@router.get("/grades/{level}/learning-areas")
def learning_areas(level: int, curriculum: str = Query(DEFAULT_CODE, max_length=50),
                   ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    version = svc.published_version(db, curriculum)
    if version is None:
        raise NOT_PUBLISHED
    return [{"id": a.id, "name": a.name} for a in svc.public_areas(db, version, level)]


@router.get("/learning-areas/{area_id}")
def learning_area(area_id: uuid.UUID, curriculum: str = Query(DEFAULT_CODE, max_length=50),
                  ctx: AuthContext = Depends(get_session_context), db: Session = Depends(get_db)):
    try:
        return svc.public_area_tree(db, curriculum, area_id)
    except svc.NotFound:
        raise HTTPException(status_code=404, detail="Not found.")
