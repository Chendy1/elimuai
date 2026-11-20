import uuid
from collections import defaultdict
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    CoreCompetency,
    Curriculum,
    CurriculumSource,
    CurriculumSourcePage,
    CurriculumValue,
    CurriculumVersion,
    Grade,
    KeyInquiryQuestion,
    LearningArea,
    LearningExperience,
    LearningOutcome,
    PertinentContemporaryIssue,
    RubricIndicator,
    Strand,
    SubStrand,
    SubStrandCompetency,
    SubStrandPci,
    SubStrandValue,
    Topic,
    Unit,
    User,
)
from app.services import audit
from app.services.auth import utcnow

REVIEWABLE = {"learning_area": LearningArea, "unit": Unit, "strand": Strand, "sub_strand": SubStrand}
READ_ONLY = "Published or archived versions are read-only. Create a new draft version to make changes."


class NotFound(Exception):
    pass


class Conflict(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def payload(self) -> Any:
        return {"message": self.message, "details": self.details} if self.details else self.message


def _commit(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict(message) from exc


def _flush(db: Session, message: str) -> None:
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict(message) from exc


# ---------- locating the version a node belongs to ----------

def _version_of(db: Session, kind: str, node_id: uuid.UUID) -> CurriculumVersion:
    on_version = CurriculumVersion.id == Grade.curriculum_version_id
    if kind == "grade":
        q = select(CurriculumVersion).join(Grade, on_version).where(Grade.id == node_id)
    else:
        q = (
            select(CurriculumVersion)
            .join(Grade, on_version)
            .join(LearningArea, LearningArea.grade_id == Grade.id)
        )
        if kind == "learning_area":
            q = q.where(LearningArea.id == node_id)
        elif kind == "unit":
            q = q.join(Unit, Unit.learning_area_id == LearningArea.id).where(Unit.id == node_id)
        elif kind == "strand":
            q = q.join(Strand, Strand.learning_area_id == LearningArea.id).where(Strand.id == node_id)
        elif kind == "sub_strand":
            q = (
                q.join(Strand, Strand.learning_area_id == LearningArea.id)
                .join(SubStrand, SubStrand.strand_id == Strand.id)
                .where(SubStrand.id == node_id)
            )
        else:
            raise ValueError(kind)
    version = db.scalar(q)
    if version is None:
        raise NotFound
    return version


def _draft_version_of(db: Session, kind: str, node_id: uuid.UUID) -> CurriculumVersion:
    version = _version_of(db, kind, node_id)
    if version.status != "draft":
        raise Conflict(READ_ONLY)
    return version


def _check_source_page(db: Session, source_page_id: uuid.UUID | None) -> None:
    if source_page_id is not None and db.get(CurriculumSourcePage, source_page_id) is None:
        raise Conflict("That source page does not exist.")


# ---------- creating structure ----------

def create_curriculum(db: Session, actor: User | None, code: str, name: str, country_code: str) -> Curriculum:
    row = Curriculum(code=code, name=name, country_code=country_code)
    db.add(row)
    _flush(db, "A curriculum with that code already exists.")
    audit.record(db, actor_id=actor.id if actor else None, action="curriculum.created", target_type="curriculum", target_id=str(row.id))
    _commit(db, "A curriculum with that code already exists.")
    return row


def create_version(db: Session, actor: User | None, curriculum_id: uuid.UUID, label: str) -> CurriculumVersion:
    if db.get(Curriculum, curriculum_id) is None:
        raise NotFound
    row = CurriculumVersion(curriculum_id=curriculum_id, label=label)
    db.add(row)
    _flush(db, "That curriculum already has a version with that label.")
    audit.record(db, actor_id=actor.id if actor else None, action="curriculum.version_created", target_type="curriculum_version", target_id=str(row.id))
    _commit(db, "That curriculum already has a version with that label.")
    return row


def create_grade(db: Session, version_id: uuid.UUID, level: int, name: str) -> Grade:
    version = db.get(CurriculumVersion, version_id)
    if version is None:
        raise NotFound
    if version.status != "draft":
        raise Conflict(READ_ONLY)
    row = Grade(curriculum_version_id=version_id, level=level, name=name)
    db.add(row)
    _commit(db, "That version already has a grade with that level.")
    return row


def create_learning_area(db: Session, grade_id: uuid.UUID, name: str, sort_order: int, source_page_id: uuid.UUID | None) -> LearningArea:
    _draft_version_of(db, "grade", grade_id)
    _check_source_page(db, source_page_id)
    row = LearningArea(grade_id=grade_id, name=name, sort_order=sort_order, source_page_id=source_page_id)
    db.add(row)
    _commit(db, "That grade already has an active learning area with that name.")
    return row


def update_learning_area(db: Session, actor: User, area_id: uuid.UUID, name: str | None, sort_order: int | None, archived: bool | None) -> LearningArea:
    area = db.get(LearningArea, area_id)
    if area is None:
        raise NotFound
    _draft_version_of(db, "learning_area", area_id)
    if name is not None:
        area.name = name
    if sort_order is not None:
        area.sort_order = sort_order
    if archived is True and area.archived_at is None:
        area.archived_at = utcnow()
        audit.record(db, actor_id=actor.id, action="curriculum.learning_area_archived", target_type="learning_area", target_id=str(area.id))
    elif archived is False:
        area.archived_at = None
    _commit(db, "That grade already has an active learning area with that name.")
    return area


def create_unit(db: Session, area_id: uuid.UUID, number: str, title: str, sort_order: int, source_page_id: uuid.UUID | None) -> Unit:
    _draft_version_of(db, "learning_area", area_id)
    _check_source_page(db, source_page_id)
    row = Unit(learning_area_id=area_id, number=number, title=title, sort_order=sort_order, source_page_id=source_page_id)
    db.add(row)
    _commit(db, "Could not create that unit.")
    return row


def create_strand(db: Session, area_id: uuid.UUID, body: Any) -> Strand:
    _draft_version_of(db, "learning_area", area_id)
    _check_source_page(db, body.source_page_id)
    if body.unit_id is not None:
        unit = db.get(Unit, body.unit_id)
        if unit is None or unit.learning_area_id != area_id:
            raise Conflict("That unit does not belong to this learning area.")
    strand = Strand(
        learning_area_id=area_id, unit_id=body.unit_id, number=body.number, name=body.name,
        sort_order=body.sort_order, source_page_id=body.source_page_id,
    )
    db.add(strand)
    db.flush()
    for i, r in enumerate(body.rubric):
        db.add(RubricIndicator(
            strand_id=strand.id, indicator=r.indicator, exceeds=r.exceeds, meets=r.meets,
            approaches=r.approaches, below=r.below, sort_order=i,
        ))
    _commit(db, "Could not create that strand.")
    return strand


def _get_or_create_named(db: Session, model: Any, name: str) -> Any:
    name = name.strip()
    found = db.scalar(select(model).where(func.lower(model.name) == name.lower()))
    if found is not None:
        return found
    row = model(name=name)
    db.add(row)
    db.flush()
    return row


def create_sub_strand(db: Session, strand_id: uuid.UUID, body: Any) -> SubStrand:
    _draft_version_of(db, "strand", strand_id)
    _check_source_page(db, body.source_page_id)
    sub = SubStrand(
        strand_id=strand_id, number=body.number, name=body.name,
        suggested_lessons=body.suggested_lessons, link_to_other_areas=body.link_to_other_areas,
        sort_order=body.sort_order, source_page_id=body.source_page_id,
    )
    db.add(sub)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise Conflict("That strand already has a sub-strand with that number.") from exc
    for i, name in enumerate(body.topics):
        db.add(Topic(sub_strand_id=sub.id, name=name, sort_order=i))
    for i, o in enumerate(body.outcomes):
        db.add(LearningOutcome(sub_strand_id=sub.id, code=o.code, text=o.text, sort_order=i))
    for i, text in enumerate(body.experiences):
        db.add(LearningExperience(sub_strand_id=sub.id, text=text, sort_order=i))
    for i, text in enumerate(body.inquiry_questions):
        db.add(KeyInquiryQuestion(sub_strand_id=sub.id, text=text, sort_order=i))
    seen: set[str] = set()
    for c in body.competencies:
        if db.get(CoreCompetency, c.code) is None:
            db.rollback()
            raise Conflict(f"Unknown core competency: {c.code}")
        if c.code not in seen:
            seen.add(c.code)
            db.add(SubStrandCompetency(sub_strand_id=sub.id, competency_code=c.code, description=c.description))
    seen_ids: set[uuid.UUID] = set()
    for v in body.values:
        value = _get_or_create_named(db, CurriculumValue, v.name)
        if value.id not in seen_ids:
            seen_ids.add(value.id)
            db.add(SubStrandValue(sub_strand_id=sub.id, value_id=value.id, description=v.description))
    seen_ids = set()
    for p in body.pcis:
        pci = _get_or_create_named(db, PertinentContemporaryIssue, p.name)
        if pci.id not in seen_ids:
            seen_ids.add(pci.id)
            db.add(SubStrandPci(sub_strand_id=sub.id, pci_id=pci.id, description=p.description))
    _commit(db, "Could not create that sub-strand.")
    return sub


# ---------- review ----------

def set_review(db: Session, reviewer: User, kind: str, node_id: uuid.UUID, status: str, comment: str | None) -> None:
    node = db.get(REVIEWABLE[kind], node_id)
    if node is None:
        raise NotFound
    _draft_version_of(db, kind, node_id)
    node.review_status = status
    if comment is not None:  # approving without a comment keeps the importer's notes
        node.review_comment = comment
    node.reviewed_by_id = reviewer.id
    node.reviewed_at = utcnow()
    audit.record(db, actor_id=reviewer.id, action="curriculum.review_set", target_type=kind,
                 target_id=str(node_id), details={"status": status})
    db.commit()


def _scoped(model: Any, version_id: uuid.UUID):
    """All rows of `model` in a version, excluding anything under an archived learning area."""
    q = select(model)
    if model is LearningArea:
        q = q.join(Grade, Grade.id == LearningArea.grade_id)
    elif model is Unit:
        q = q.join(LearningArea, LearningArea.id == Unit.learning_area_id).join(Grade, Grade.id == LearningArea.grade_id)
    elif model is Strand:
        q = q.join(LearningArea, LearningArea.id == Strand.learning_area_id).join(Grade, Grade.id == LearningArea.grade_id)
    else:
        q = (
            q.join(Strand, Strand.id == SubStrand.strand_id)
            .join(LearningArea, LearningArea.id == Strand.learning_area_id)
            .join(Grade, Grade.id == LearningArea.grade_id)
        )
    return q.where(Grade.curriculum_version_id == version_id, LearningArea.archived_at.is_(None))


def unapproved_counts(db: Session, version_id: uuid.UUID) -> dict[str, int]:
    out = {}
    for kind, model in REVIEWABLE.items():
        sub = _scoped(model, version_id).where(model.review_status != "approved").subquery()
        out[kind] = db.scalar(select(func.count()).select_from(sub))
    return out


def unlicensed_sources(db: Session, version_id: uuid.UUID) -> list[str]:
    titles: set[str] = set()
    for model in REVIEWABLE.values():
        sub = _scoped(model, version_id).subquery()
        rows = db.scalars(
            select(CurriculumSource.title)
            .join(CurriculumSourcePage, CurriculumSourcePage.source_id == CurriculumSource.id)
            .where(
                CurriculumSource.license_status != "granted",
                CurriculumSourcePage.id.in_(select(sub.c.source_page_id).where(sub.c.source_page_id.is_not(None))),
            )
        )
        titles.update(rows)
    return sorted(titles)


# ---------- publishing ----------

def publish_version(db: Session, actor: User, version_id: uuid.UUID) -> CurriculumVersion:
    version = db.get(CurriculumVersion, version_id)
    if version is None:
        raise NotFound
    if version.status != "draft":
        raise Conflict("Only a draft version can be published.")
    sub_count = db.scalar(select(func.count()).select_from(_scoped(SubStrand, version_id).subquery()))
    if sub_count == 0:
        raise Conflict("A version with no sub-strands cannot be published.")
    counts = unapproved_counts(db, version_id)
    if any(counts.values()):
        raise Conflict("All content must be approved before publishing.", {"unapproved": counts})
    sources = unlicensed_sources(db, version_id)
    if sources:
        raise Conflict("Every source must have written permission recorded as granted.", {"sources": sources})
    db.execute(
        update(CurriculumVersion)
        .where(CurriculumVersion.curriculum_id == version.curriculum_id,
               CurriculumVersion.status == "published", CurriculumVersion.id != version.id)
        .values(status="archived")
    )
    version.status = "published"
    version.published_at = utcnow()
    audit.record(db, actor_id=actor.id, action="curriculum.version_published", target_type="curriculum_version", target_id=str(version.id))
    db.commit()
    return version


def archive_version(db: Session, actor: User, version_id: uuid.UUID) -> CurriculumVersion:
    version = db.get(CurriculumVersion, version_id)
    if version is None:
        raise NotFound
    if version.status == "archived":
        raise Conflict("That version is already archived.")
    version.status = "archived"
    audit.record(db, actor_id=actor.id, action="curriculum.version_archived", target_type="curriculum_version", target_id=str(version.id))
    db.commit()
    return version


# ---------- sources ----------

def create_source(db: Session, actor: User, body: Any) -> CurriculumSource:
    row = CurriculumSource(
        title=body.title, publisher=body.publisher, edition_label=body.edition_label,
        original_filename=body.original_filename, file_sha256=body.file_sha256, page_count=body.page_count,
    )
    db.add(row)
    _flush(db, "A source with that file fingerprint is already registered.")
    audit.record(db, actor_id=actor.id, action="curriculum.source_registered", target_type="curriculum_source", target_id=str(row.id))
    _commit(db, "A source with that file fingerprint is already registered.")
    return row


def set_license(db: Session, actor: User, source_id: uuid.UUID, status: str, notes: str | None) -> CurriculumSource:
    source = db.get(CurriculumSource, source_id)
    if source is None:
        raise NotFound
    source.license_status = status
    source.license_notes = notes
    audit.record(db, actor_id=actor.id, action="curriculum.source_license_set", target_type="curriculum_source",
                 target_id=str(source.id), details={"license_status": status})
    db.commit()
    return source


def add_source_page(db: Session, source_id: uuid.UUID, pdf_page: int, printed_page: str | None, text: str) -> CurriculumSourcePage:
    """Used by the importer (Phase 3.2) to store page text with both page numbers."""
    row = CurriculumSourcePage(source_id=source_id, pdf_page=pdf_page, printed_page=printed_page, text=text)
    db.add(row)
    _commit(db, "That source already has that page.")
    return row


# ---------- reading ----------

def _group(db: Session, model: Any, attr: str, ids: list[uuid.UUID], *order: Any) -> dict[uuid.UUID, list[Any]]:
    out: dict[uuid.UUID, list[Any]] = defaultdict(list)
    if ids:
        for row in db.scalars(select(model).where(getattr(model, attr).in_(ids)).order_by(*order)):
            out[getattr(row, attr)].append(row)
    return out


def _review(node: Any) -> dict[str, Any]:
    return {
        "review_status": node.review_status,
        "review_comment": node.review_comment,
        "source_page_id": node.source_page_id,
    }


def build_area_tree(db: Session, area: LearningArea, admin: bool) -> dict[str, Any]:
    units = list(db.scalars(select(Unit).where(Unit.learning_area_id == area.id).order_by(Unit.sort_order, Unit.number)))
    strands = list(db.scalars(select(Strand).where(Strand.learning_area_id == area.id).order_by(Strand.sort_order, Strand.number)))
    strand_ids = [s.id for s in strands]
    subs = list(db.scalars(
        select(SubStrand).where(SubStrand.strand_id.in_(strand_ids)).order_by(SubStrand.sort_order, SubStrand.number)
    )) if strand_ids else []
    sub_ids = [s.id for s in subs]

    topics = _group(db, Topic, "sub_strand_id", sub_ids, Topic.sort_order)
    outcomes = _group(db, LearningOutcome, "sub_strand_id", sub_ids, LearningOutcome.sort_order)
    experiences = _group(db, LearningExperience, "sub_strand_id", sub_ids, LearningExperience.sort_order)
    questions = _group(db, KeyInquiryQuestion, "sub_strand_id", sub_ids, KeyInquiryQuestion.sort_order)
    rubrics = _group(db, RubricIndicator, "strand_id", strand_ids, RubricIndicator.sort_order)

    comps: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    vals: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    pcis: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    if sub_ids:
        for sid, code, name, desc in db.execute(
            select(SubStrandCompetency.sub_strand_id, CoreCompetency.code, CoreCompetency.name, SubStrandCompetency.description)
            .join(CoreCompetency, CoreCompetency.code == SubStrandCompetency.competency_code)
            .where(SubStrandCompetency.sub_strand_id.in_(sub_ids)).order_by(CoreCompetency.code)
        ):
            comps[sid].append({"code": code, "name": name, "description": desc})
        for sid, name, desc in db.execute(
            select(SubStrandValue.sub_strand_id, CurriculumValue.name, SubStrandValue.description)
            .join(CurriculumValue, CurriculumValue.id == SubStrandValue.value_id)
            .where(SubStrandValue.sub_strand_id.in_(sub_ids)).order_by(CurriculumValue.name)
        ):
            vals[sid].append({"name": name, "description": desc})
        for sid, name, desc in db.execute(
            select(SubStrandPci.sub_strand_id, PertinentContemporaryIssue.name, SubStrandPci.description)
            .join(PertinentContemporaryIssue, PertinentContemporaryIssue.id == SubStrandPci.pci_id)
            .where(SubStrandPci.sub_strand_id.in_(sub_ids)).order_by(PertinentContemporaryIssue.name)
        ):
            pcis[sid].append({"name": name, "description": desc})

    subs_by_strand: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)
    for s in subs:
        d = {
            "id": s.id, "number": s.number, "name": s.name, "suggested_lessons": s.suggested_lessons,
            "link_to_other_areas": s.link_to_other_areas,
            "topics": [t.name for t in topics[s.id]],
            "outcomes": [{"code": o.code, "text": o.text} for o in outcomes[s.id]],
            "experiences": [e.text for e in experiences[s.id]],
            "inquiry_questions": [q.text for q in questions[s.id]],
            "competencies": comps[s.id], "values": vals[s.id], "pcis": pcis[s.id],
        }
        if admin:
            d.update(_review(s))
        subs_by_strand[s.strand_id].append(d)

    def strand_dict(st: Strand) -> dict[str, Any]:
        d = {
            "id": st.id, "number": st.number, "name": st.name, "unit_id": st.unit_id,
            "rubric": [
                {"indicator": r.indicator, "exceeds": r.exceeds, "meets": r.meets,
                 "approaches": r.approaches, "below": r.below}
                for r in rubrics[st.id]
            ],
            "sub_strands": subs_by_strand[st.id],
        }
        if admin:
            d.update(_review(st))
        return d

    def unit_dict(u: Unit) -> dict[str, Any]:
        d = {"id": u.id, "number": u.number, "title": u.title}
        if admin:
            d.update(_review(u))
        return d

    tree = {
        "id": area.id, "name": area.name, "sort_order": area.sort_order,
        "units": [unit_dict(u) for u in units], "strands": [strand_dict(s) for s in strands],
    }
    if admin:
        tree.update(_review(area))
        tree["archived"] = area.archived_at is not None
    return tree


def version_tree(db: Session, version_id: uuid.UUID) -> dict[str, Any]:
    version = db.get(CurriculumVersion, version_id)
    if version is None:
        raise NotFound
    grades = list(db.scalars(select(Grade).where(Grade.curriculum_version_id == version_id).order_by(Grade.level)))
    out = []
    for g in grades:
        areas = db.scalars(select(LearningArea).where(LearningArea.grade_id == g.id).order_by(LearningArea.sort_order, LearningArea.name))
        out.append({"id": g.id, "level": g.level, "name": g.name,
                    "learning_areas": [build_area_tree(db, a, admin=True) for a in areas]})
    return {"id": version.id, "label": version.label, "status": version.status, "grades": out}


def published_version(db: Session, curriculum_code: str) -> CurriculumVersion | None:
    return db.scalar(
        select(CurriculumVersion).join(Curriculum, Curriculum.id == CurriculumVersion.curriculum_id)
        .where(Curriculum.code == curriculum_code, CurriculumVersion.status == "published")
    )


def public_grades(db: Session, version: CurriculumVersion) -> list[Grade]:
    return list(db.scalars(select(Grade).where(Grade.curriculum_version_id == version.id).order_by(Grade.level)))


def public_areas(db: Session, version: CurriculumVersion, level: int) -> list[LearningArea]:
    return list(db.scalars(
        select(LearningArea).join(Grade, Grade.id == LearningArea.grade_id)
        .where(Grade.curriculum_version_id == version.id, Grade.level == level,
               LearningArea.archived_at.is_(None), LearningArea.review_status == "approved")
        .order_by(LearningArea.sort_order, LearningArea.name)
    ))


def public_area_tree(db: Session, curriculum_code: str, area_id: uuid.UUID) -> dict[str, Any]:
    area = db.scalar(
        select(LearningArea).join(Grade, Grade.id == LearningArea.grade_id)
        .join(CurriculumVersion, CurriculumVersion.id == Grade.curriculum_version_id)
        .join(Curriculum, Curriculum.id == CurriculumVersion.curriculum_id)
        .where(LearningArea.id == area_id, Curriculum.code == curriculum_code,
               CurriculumVersion.status == "published", LearningArea.archived_at.is_(None))
    )
    if area is None:
        raise NotFound
    return build_area_tree(db, area, admin=False)


def source_page_detail(db: Session, page_id: uuid.UUID) -> dict[str, Any]:
    page = db.get(CurriculumSourcePage, page_id)
    if page is None:
        raise NotFound
    source = db.get(CurriculumSource, page.source_id)

    def neighbour(pdf_page: int) -> uuid.UUID | None:
        return db.scalar(select(CurriculumSourcePage.id).where(
            CurriculumSourcePage.source_id == page.source_id, CurriculumSourcePage.pdf_page == pdf_page))

    return {
        "id": page.id, "source_id": page.source_id, "source_title": source.title,
        "license_status": source.license_status, "pdf_page": page.pdf_page,
        "printed_page": page.printed_page, "text": page.text,
        "previous_page_id": neighbour(page.pdf_page - 1), "next_page_id": neighbour(page.pdf_page + 1),
    }
