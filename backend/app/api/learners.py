import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.permissions import P_LEARNERS_MANAGE_OWN
from app.consent import NOTICE_TEXT, NOTICE_TITLE, NOTICE_VERSION
from app.db.session import get_db
from app.schemas.learner import ConsentNoticeOut, LearnerCreate, LearnerOut, LearnerUpdate
from app.services import learners as svc
from app.services.auth import AuthContext

router = APIRouter(prefix="/learners", tags=["learners"])

READ = Depends(require_permission(P_LEARNERS_MANAGE_OWN))
WRITE = Depends(require_permission(P_LEARNERS_MANAGE_OWN, csrf=True))

NOT_FOUND = HTTPException(status_code=404, detail="Learner not found.")
DUPLICATE = HTTPException(status_code=409, detail="You already have a learner with that nickname.")


@router.get("/consent-notice", response_model=ConsentNoticeOut)
def consent_notice():
    return ConsentNoticeOut(
        version=NOTICE_VERSION, title=NOTICE_TITLE, text=NOTICE_TEXT, is_draft=True
    )


@router.get("", response_model=list[LearnerOut])
def list_my_learners(ctx: AuthContext = READ, db: Session = Depends(get_db)):
    return svc.list_learners(db, ctx.user.id)


@router.post("", response_model=LearnerOut, status_code=201)
def create_learner(
    body: LearnerCreate, ctx: AuthContext = WRITE, db: Session = Depends(get_db)
):
    if body.consent.notice_version != NOTICE_VERSION:
        raise HTTPException(
            status_code=409,
            detail="The consent notice has changed. Please review the current notice and try again.",
        )
    try:
        return svc.create_learner(db, ctx.user, body.nickname, body.grade)
    except svc.LearnerLimitReached:
        raise HTTPException(
            status_code=409, detail=f"You can add up to {svc.MAX_LEARNERS} learners."
        )
    except svc.DuplicateNickname:
        raise DUPLICATE


@router.get("/{learner_id}", response_model=LearnerOut)
def get_learner(
    learner_id: uuid.UUID,
    ctx: AuthContext = READ,
    db: Session = Depends(get_db),
):
    learner = svc.get_owned(db, ctx.user.id, learner_id)
    if learner is None:
        raise NOT_FOUND
    return learner


@router.patch("/{learner_id}", response_model=LearnerOut)
def update_learner(
    learner_id: uuid.UUID,
    body: LearnerUpdate,
    ctx: AuthContext = WRITE,
    db: Session = Depends(get_db),
):
    learner = svc.get_owned(db, ctx.user.id, learner_id)
    if learner is None:
        raise NOT_FOUND
    try:
        return svc.update_learner(db, learner, body.nickname, body.grade)
    except svc.DuplicateNickname:
        raise DUPLICATE


@router.delete("/{learner_id}", status_code=204)
def delete_learner(
    learner_id: uuid.UUID, ctx: AuthContext = WRITE, db: Session = Depends(get_db)
) -> None:
    learner = svc.get_owned(db, ctx.user.id, learner_id)
    if learner is None:
        raise NOT_FOUND
    svc.remove_learner(db, learner)
