"""Curriculum structure. Content rows are created as drafts, reviewed by a human, and only
published when approved and when their sources are licensed (see services/curriculum.py)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.models.base import Base, TimestampMixin

REVIEW_STATUSES = ("draft", "in_review", "approved", "rejected")
LICENSE_STATUSES = ("not_requested", "requested", "granted", "denied")


def uuid_pk():
    return mapped_column(Uuid, primary_key=True, default=uuid.uuid4)


def review_check() -> CheckConstraint:
    return CheckConstraint(
        "review_status IN ('draft','in_review','approved','rejected')", name="review_status_valid"
    )


class ReviewMixin:
    """Review state and provenance shared by the structural rows a reviewer signs off."""

    review_status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    review_comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @declared_attr
    def reviewed_by_id(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    @declared_attr
    def source_page_id(cls) -> Mapped[uuid.UUID | None]:
        return mapped_column(ForeignKey("curriculum_source_pages.id", ondelete="SET NULL"))


class Curriculum(TimestampMixin, Base):
    __tablename__ = "curricula"

    id: Mapped[uuid.UUID] = uuid_pk()
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    country_code: Mapped[str] = mapped_column(String(2), default="KE")


class CurriculumVersion(TimestampMixin, Base):
    __tablename__ = "curriculum_versions"
    __table_args__ = (
        UniqueConstraint("curriculum_id", "label", name="uq_curriculum_versions_curriculum_label"),
        CheckConstraint("status IN ('draft','published','archived')", name="status_valid"),
        Index(
            "uq_curriculum_versions_one_published",
            "curriculum_id",
            unique=True,
            postgresql_where=text("status = 'published'"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    curriculum_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("curricula.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="draft", server_default="draft")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CurriculumSource(TimestampMixin, Base):
    """A source document (for example an official curriculum design PDF) and its licence state."""

    __tablename__ = "curriculum_sources"
    __table_args__ = (
        CheckConstraint(
            "license_status IN ('not_requested','requested','granted','denied')",
            name="license_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(200))
    edition_label: Mapped[str | None] = mapped_column(String(100))
    original_filename: Mapped[str | None] = mapped_column(String(300))
    file_sha256: Mapped[str] = mapped_column(String(64), unique=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    license_status: Mapped[str] = mapped_column(
        String(20), default="not_requested", server_default="not_requested"
    )
    license_notes: Mapped[str | None] = mapped_column(Text)


class CurriculumSourcePage(Base):
    __tablename__ = "curriculum_source_pages"
    __table_args__ = (UniqueConstraint("source_id", "pdf_page", name="uq_source_pages_source_pdf_page"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("curriculum_sources.id", ondelete="CASCADE")
    )
    pdf_page: Mapped[int] = mapped_column(Integer)
    printed_page: Mapped[str | None] = mapped_column(String(20))
    text: Mapped[str] = mapped_column(Text)


class CoreCompetency(Base):
    __tablename__ = "core_competencies"

    code: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class CurriculumValue(Base):
    __tablename__ = "curriculum_values"
    __table_args__ = (Index("uq_curriculum_values_name_lower", text("lower(name)"), unique=True),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(100))


class PertinentContemporaryIssue(Base):
    __tablename__ = "pertinent_contemporary_issues"
    __table_args__ = (Index("uq_pcis_name_lower", text("lower(name)"), unique=True),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(150))


class Grade(TimestampMixin, Base):
    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint("curriculum_version_id", "level", name="uq_grades_version_level"),
        CheckConstraint("level BETWEEN 1 AND 12", name="level_range"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    curriculum_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("curriculum_versions.id", ondelete="CASCADE"), index=True
    )
    level: Mapped[int] = mapped_column(SmallInteger)
    name: Mapped[str] = mapped_column(String(50))


class LearningArea(ReviewMixin, TimestampMixin, Base):
    __tablename__ = "learning_areas"
    __table_args__ = (
        review_check(),
        Index(
            "uq_learning_areas_grade_name_active",
            "grade_id",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("archived_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    grade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grades.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(150))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Unit(ReviewMixin, TimestampMixin, Base):
    """Optional grouping between a learning area and its strands (for example a theme)."""

    __tablename__ = "units"
    __table_args__ = (review_check(),)

    id: Mapped[uuid.UUID] = uuid_pk()
    learning_area_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_areas.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Strand(ReviewMixin, TimestampMixin, Base):
    __tablename__ = "strands"
    __table_args__ = (review_check(),)

    id: Mapped[uuid.UUID] = uuid_pk()
    learning_area_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("learning_areas.id", ondelete="CASCADE"), index=True
    )
    unit_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("units.id", ondelete="SET NULL"))
    number: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class SubStrand(ReviewMixin, TimestampMixin, Base):
    __tablename__ = "sub_strands"
    __table_args__ = (
        review_check(),
        UniqueConstraint("strand_id", "number", name="uq_sub_strands_strand_number"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strands.id", ondelete="CASCADE"), index=True
    )
    number: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(200))
    suggested_lessons: Mapped[int | None] = mapped_column(SmallInteger)
    link_to_other_areas: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = uuid_pk()
    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class LearningOutcome(Base):
    __tablename__ = "learning_outcomes"

    id: Mapped[uuid.UUID] = uuid_pk()
    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str | None] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class LearningExperience(Base):
    __tablename__ = "learning_experiences"

    id: Mapped[uuid.UUID] = uuid_pk()
    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class KeyInquiryQuestion(Base):
    __tablename__ = "key_inquiry_questions"

    id: Mapped[uuid.UUID] = uuid_pk()
    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class SubStrandCompetency(Base):
    __tablename__ = "sub_strand_competencies"

    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), primary_key=True
    )
    competency_code: Mapped[str] = mapped_column(
        ForeignKey("core_competencies.code"), primary_key=True
    )
    description: Mapped[str | None] = mapped_column(Text)


class SubStrandValue(Base):
    __tablename__ = "sub_strand_values"

    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), primary_key=True
    )
    value_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("curriculum_values.id"), primary_key=True
    )
    description: Mapped[str | None] = mapped_column(Text)


class SubStrandPci(Base):
    __tablename__ = "sub_strand_pcis"

    sub_strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sub_strands.id", ondelete="CASCADE"), primary_key=True
    )
    pci_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pertinent_contemporary_issues.id"), primary_key=True
    )
    description: Mapped[str | None] = mapped_column(Text)


class RubricIndicator(Base):
    """Official performance-level descriptors (Exceeds / Meets / Approaches / Below Expectations).
    Deliberately separate from ElimuAI's own mastery indicators."""

    __tablename__ = "rubric_indicators"

    id: Mapped[uuid.UUID] = uuid_pk()
    strand_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("strands.id", ondelete="CASCADE"), index=True
    )
    indicator: Mapped[str] = mapped_column(Text)
    exceeds: Mapped[str] = mapped_column(Text)
    meets: Mapped[str] = mapped_column(Text)
    approaches: Mapped[str] = mapped_column(Text)
    below: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
