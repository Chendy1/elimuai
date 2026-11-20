import hashlib
import uuid
from dataclasses import dataclass, field

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.importer.design_parser import ParsedDesign, parse_design
from app.importer.pdf_text import extract_pdf_pages
from app.models import CurriculumSource, CurriculumSourcePage, Grade, SubStrand
from app.schemas.curriculum import (
    CompetencyIn,
    NamedItemIn,
    OutcomeIn,
    RubricIn,
    StrandCreate,
    SubStrandCreate,
)
from app.services import audit
from app.services import curriculum as curriculum_service


@dataclass
class ImportResult:
    source: CurriculumSource
    created: bool
    pages_added: int
    pages_total: int


def import_pdf(
    db: Session, *, data: bytes, filename: str | None, title: str, publisher: str,
    edition_label: str | None = None,
) -> ImportResult:
    """Register a PDF (identified by its SHA-256) and store the text of every page.
    Safe to repeat: pages already stored are skipped. Nothing here creates curriculum records,
    and a new source always starts with licence status 'not_requested'."""
    sha = hashlib.sha256(data).hexdigest()
    pages = extract_pdf_pages(data)

    source = db.scalar(select(CurriculumSource).where(CurriculumSource.file_sha256 == sha))
    created = source is None
    if source is None:
        source = CurriculumSource(
            title=title, publisher=publisher, edition_label=edition_label,
            original_filename=filename, file_sha256=sha, page_count=len(pages),
        )
        db.add(source)
        db.flush()

    existing = set(
        db.scalars(select(CurriculumSourcePage.pdf_page).where(CurriculumSourcePage.source_id == source.id))
    )
    added = 0
    for p in pages:
        if p.pdf_page not in existing:
            db.add(CurriculumSourcePage(
                source_id=source.id, pdf_page=p.pdf_page, printed_page=p.printed_page, text=p.text,
            ))
            added += 1
    source.page_count = len(pages)
    audit.record(
        db, actor_id=None, action="curriculum.source_imported", target_type="curriculum_source",
        target_id=str(source.id), details={"created": created, "pages_added": added, "pages_total": len(pages)},
    )
    db.commit()
    return ImportResult(source=source, created=created, pages_added=added, pages_total=len(pages))


@dataclass
class ProposalResult:
    strands: int
    sub_strands: int
    outcomes: int
    warnings: list[str] = field(default_factory=list)
    written: bool = False
    learning_area_id: uuid.UUID | None = None


def _summary(design: ParsedDesign) -> tuple[int, int, int]:
    subs = [sub for st in design.strands for sub in st.sub_strands]
    return len(design.strands), len(subs), sum(len(sub.outcomes) for sub in subs)


def propose_from_source(
    db: Session, *, source_id: uuid.UUID, version_id: uuid.UUID, grade_level: int, grade_name: str,
    area_name: str, dry_run: bool = False,
) -> ProposalResult:
    """Turn a source's stored page text into DRAFT curriculum records under a draft version.

    Every record starts with review_status 'draft', a pointer to the source page it came from, and a
    comment listing what the parser could not place. A person must review and approve each one."""
    source = db.get(CurriculumSource, source_id)
    if source is None:
        raise curriculum_service.NotFound
    pages = list(
        db.scalars(select(CurriculumSourcePage).where(CurriculumSourcePage.source_id == source_id)
                   .order_by(CurriculumSourcePage.pdf_page))
    )
    design = parse_design(pages)
    strands, subs, outcomes = _summary(design)
    if strands == 0 or subs == 0:
        raise curriculum_service.Conflict(
            "No strands or sub-strands were recognised. This layout is not supported yet."
        )
    result = ProposalResult(strands=strands, sub_strands=subs, outcomes=outcomes,
                            warnings=design.all_warnings())
    if dry_run:
        return result

    page_ids = {p.pdf_page: p.id for p in pages}
    grade = db.scalar(select(Grade).where(Grade.curriculum_version_id == version_id, Grade.level == grade_level))
    if grade is None:
        grade = curriculum_service.create_grade(db, version_id, grade_level, grade_name)
    area = curriculum_service.create_learning_area(
        db, grade.id, area_name, 0, page_ids.get(design.strands[0].first_page)
    )

    for si, parsed_strand in enumerate(design.strands):
        strand = curriculum_service.create_strand(db, area.id, StrandCreate(
            number=parsed_strand.number, name=parsed_strand.name[:200], sort_order=si,
            source_page_id=page_ids.get(parsed_strand.first_page),
            rubric=[RubricIn(indicator=r.indicator, exceeds=r.exceeds, meets=r.meets,
                             approaches=r.approaches, below=r.below) for r in parsed_strand.rubric],
        ))
        for ti, ps in enumerate(parsed_strand.sub_strands):
            try:
                body = SubStrandCreate(
                    number=ps.number or f"?{ti + 1}", name=(ps.name or "(name not found)")[:200],
                    suggested_lessons=ps.suggested_lessons, link_to_other_areas=ps.link_to_other_areas,
                    sort_order=ti, source_page_id=page_ids.get(ps.first_page),
                    topics=[t[:300] for t in ps.topics],
                    outcomes=[OutcomeIn(code=c, text=t) for c, t in ps.outcomes],
                    experiences=ps.experiences, inquiry_questions=ps.questions,
                    competencies=[CompetencyIn(code=c, description=d) for c, d in ps.competencies],
                    values=[NamedItemIn(name=n[:100], description=d) for n, d in ps.values],
                    pcis=[NamedItemIn(name=n, description=d) for n, d in ps.pcis],
                )
            except ValidationError as exc:
                raise curriculum_service.Conflict(f"Sub-strand {ps.number} could not be stored: {exc.errors()[0]['msg']}") from exc
            sub = curriculum_service.create_sub_strand(db, strand.id, body)
            notes = [f"Auto-extracted from PDF pages {ps.first_page}-{ps.last_page}. Check against the source page."]
            notes += [f"- {w}" for w in ps.warnings]
            notes += [f"- {n}" for n in ps.notes]
            row = db.get(SubStrand, sub.id)
            row.review_comment = "\n".join(notes)
            db.commit()

    audit.record(
        db, actor_id=None, action="curriculum.proposal_created", target_type="learning_area",
        target_id=str(area.id),
        details={"source_id": str(source_id), "strands": strands, "sub_strands": subs, "warnings": len(result.warnings)},
    )
    db.commit()
    result.written = True
    result.learning_area_id = area.id
    return result
