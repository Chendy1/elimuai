import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.permissions import P_CONTENT_PUBLISH, P_CONTENT_REVIEW, P_CURRICULUM_MANAGE
from app.db.session import get_db
from app.models import Curriculum, CurriculumSource, CurriculumVersion
from app.schemas import curriculum as s
from app.services import curriculum as svc
from app.services.auth import AuthContext

router = APIRouter(prefix="/admin/curriculum", tags=["curriculum-admin"])

READ = Depends(require_permission(P_CURRICULUM_MANAGE))
MANAGE = Depends(require_permission(P_CURRICULUM_MANAGE, csrf=True))
REVIEW = Depends(require_permission(P_CONTENT_REVIEW, csrf=True))
PUBLISH = Depends(require_permission(P_CONTENT_PUBLISH, csrf=True))


def call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except svc.NotFound:
        raise HTTPException(status_code=404, detail="Not found.")
    except svc.Conflict as exc:
        raise HTTPException(status_code=409, detail=exc.payload())


def _curriculum(c: Curriculum) -> dict[str, Any]:
    return {"id": c.id, "code": c.code, "name": c.name, "country_code": c.country_code}


def _version(v: CurriculumVersion) -> dict[str, Any]:
    return {"id": v.id, "curriculum_id": v.curriculum_id, "label": v.label,
            "status": v.status, "published_at": v.published_at}


def _source(r: CurriculumSource) -> dict[str, Any]:
    return {"id": r.id, "title": r.title, "publisher": r.publisher, "edition_label": r.edition_label,
            "original_filename": r.original_filename, "page_count": r.page_count,
            "license_status": r.license_status, "license_notes": r.license_notes}


# ---- curricula and versions ----

@router.get("/curricula")
def list_curricula(ctx: AuthContext = READ, db: Session = Depends(get_db)):
    return [_curriculum(c) for c in db.scalars(select(Curriculum).order_by(Curriculum.code))]


@router.post("/curricula", status_code=201)
def create_curriculum(body: s.CurriculumCreate, ctx: AuthContext = MANAGE, db: Session = Depends(get_db)):
    return _curriculum(call(svc.create_curriculum, db, ctx.user, body.code, body.name, body.country_code))


@router.get("/curricula/{curriculum_id}/versions")
def list_versions(curriculum_id: uuid.UUID, ctx: AuthContext = READ, db: Session = Depends(get_db)):
    rows = db.scalars(select(CurriculumVersion).where(CurriculumVersion.curriculum_id == curriculum_id)
                      .order_by(CurriculumVersion.created_at))
    return [_version(v) for v in rows]


@router.post("/curricula/{curriculum_id}/versions", status_code=201)
def create_version(curriculum_id: uuid.UUID, body: s.VersionCreate, ctx: AuthContext = MANAGE,
                   db: Session = Depends(get_db)):
    return _version(call(svc.create_version, db, ctx.user, curriculum_id, body.label))


@router.get("/versions/{version_id}/tree")
def version_tree(version_id: uuid.UUID, ctx: AuthContext = READ, db: Session = Depends(get_db)):
    return call(svc.version_tree, db, version_id)


@router.post("/versions/{version_id}/publish")
def publish(version_id: uuid.UUID, ctx: AuthContext = PUBLISH, db: Session = Depends(get_db)):
    return _version(call(svc.publish_version, db, ctx.user, version_id))


@router.post("/versions/{version_id}/archive")
def archive(version_id: uuid.UUID, ctx: AuthContext = PUBLISH, db: Session = Depends(get_db)):
    return _version(call(svc.archive_version, db, ctx.user, version_id))


# ---- structure ----

@router.post("/versions/{version_id}/grades", status_code=201)
def create_grade(version_id: uuid.UUID, body: s.GradeCreate, ctx: AuthContext = MANAGE,
                 db: Session = Depends(get_db)):
    g = call(svc.create_grade, db, version_id, body.level, body.name)
    return {"id": g.id, "level": g.level, "name": g.name}


@router.post("/grades/{grade_id}/learning-areas", status_code=201)
def create_area(grade_id: uuid.UUID, body: s.AreaCreate, ctx: AuthContext = MANAGE,
                db: Session = Depends(get_db)):
    a = call(svc.create_learning_area, db, grade_id, body.name, body.sort_order, body.source_page_id)
    return {"id": a.id, "name": a.name}


@router.patch("/learning-areas/{area_id}")
def update_area(area_id: uuid.UUID, body: s.AreaUpdate, ctx: AuthContext = MANAGE,
                db: Session = Depends(get_db)):
    a = call(svc.update_learning_area, db, ctx.user, area_id, body.name, body.sort_order, body.archived)
    return {"id": a.id, "name": a.name, "archived": a.archived_at is not None}


@router.post("/learning-areas/{area_id}/units", status_code=201)
def create_unit(area_id: uuid.UUID, body: s.UnitCreate, ctx: AuthContext = MANAGE,
                db: Session = Depends(get_db)):
    u = call(svc.create_unit, db, area_id, body.number, body.title, body.sort_order, body.source_page_id)
    return {"id": u.id, "number": u.number, "title": u.title}


@router.post("/learning-areas/{area_id}/strands", status_code=201)
def create_strand(area_id: uuid.UUID, body: s.StrandCreate, ctx: AuthContext = MANAGE,
                  db: Session = Depends(get_db)):
    st = call(svc.create_strand, db, area_id, body)
    return {"id": st.id, "number": st.number, "name": st.name}


@router.post("/strands/{strand_id}/sub-strands", status_code=201)
def create_sub_strand(strand_id: uuid.UUID, body: s.SubStrandCreate, ctx: AuthContext = MANAGE,
                      db: Session = Depends(get_db)):
    sub = call(svc.create_sub_strand, db, strand_id, body)
    return {"id": sub.id, "number": sub.number, "name": sub.name}


# ---- review ----

@router.post("/review", status_code=204)
def review(body: s.ReviewRequest, ctx: AuthContext = REVIEW, db: Session = Depends(get_db)) -> None:
    call(svc.set_review, db, ctx.user, body.kind, body.id, body.status, body.comment)


# ---- sources and licensing ----

@router.get("/sources")
def list_sources(ctx: AuthContext = READ, db: Session = Depends(get_db)):
    return [_source(r) for r in db.scalars(select(CurriculumSource).order_by(CurriculumSource.title))]


@router.post("/sources", status_code=201)
def create_source(body: s.SourceCreate, ctx: AuthContext = MANAGE, db: Session = Depends(get_db)):
    return _source(call(svc.create_source, db, ctx.user, body))


@router.patch("/sources/{source_id}/license")
def set_license(source_id: uuid.UUID, body: s.LicenseUpdate, ctx: AuthContext = MANAGE,
                db: Session = Depends(get_db)):
    return _source(call(svc.set_license, db, ctx.user, source_id, body.license_status, body.license_notes))
