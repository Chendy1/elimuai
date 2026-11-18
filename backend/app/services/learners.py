import uuid

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.consent import NOTICE_VERSION, PURPOSE, notice_sha256
from app.models import ConsentRecord, Learner, User
from app.services import audit
from app.services.auth import utcnow

MAX_LEARNERS = 6


class LearnerLimitReached(Exception):
    pass


class DuplicateNickname(Exception):
    pass


def list_learners(db: Session, guardian_id: uuid.UUID) -> list[Learner]:
    return list(
        db.scalars(
            select(Learner)
            .where(Learner.guardian_id == guardian_id, Learner.deleted_at.is_(None))
            .order_by(Learner.created_at)
        )
    )


def get_owned(db: Session, guardian_id: uuid.UUID, learner_id: uuid.UUID) -> Learner | None:
    """Only the owning guardian's active learners; anything else looks like 'not found'."""
    return db.scalar(
        select(Learner).where(
            Learner.id == learner_id,
            Learner.guardian_id == guardian_id,
            Learner.deleted_at.is_(None),
        )
    )


def create_learner(db: Session, guardian: User, nickname: str, grade: int) -> Learner:
    count = db.scalar(
        select(func.count())
        .select_from(Learner)
        .where(Learner.guardian_id == guardian.id, Learner.deleted_at.is_(None))
    )
    if count >= MAX_LEARNERS:
        raise LearnerLimitReached
    learner = Learner(guardian_id=guardian.id, nickname=nickname, grade=grade)
    db.add(learner)
    try:
        db.flush()
        db.add(
            ConsentRecord(
                learner_id=learner.id,
                guardian_id=guardian.id,
                purpose=PURPOSE,
                notice_version=NOTICE_VERSION,
                notice_sha256=notice_sha256(),
            )
        )
        audit.record(
            db, actor_id=guardian.id, action="learner.created", target_type="learner",
            target_id=str(learner.id), details={"grade": grade, "consent_version": NOTICE_VERSION},
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateNickname from exc
    return learner


def update_learner(
    db: Session, learner: Learner, nickname: str | None, grade: int | None
) -> Learner:
    changed = []
    if nickname is not None:
        learner.nickname = nickname
        changed.append("nickname")
    if grade is not None:
        learner.grade = grade
        changed.append("grade")
    audit.record(
        db, actor_id=learner.guardian_id, action="learner.updated", target_type="learner",
        target_id=str(learner.id), details={"changed": changed},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateNickname from exc
    return learner


def remove_learner(db: Session, learner: Learner) -> None:
    """Soft delete and withdraw consent. Permanent erasure is designed in a later phase."""
    now = utcnow()
    learner.deleted_at = now
    db.execute(
        update(ConsentRecord)
        .where(ConsentRecord.learner_id == learner.id, ConsentRecord.withdrawn_at.is_(None))
        .values(withdrawn_at=now)
    )
    audit.record(
        db, actor_id=learner.guardian_id, action="learner.removed", target_type="learner",
        target_id=str(learner.id), details={"consent_withdrawn": True},
    )
    db.commit()
