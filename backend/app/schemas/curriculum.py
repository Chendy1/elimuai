import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _clean(v: str) -> str:
    v = v.strip()
    if not v:
        raise ValueError("This field cannot be empty.")
    return v


class CurriculumCreate(BaseModel):
    code: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,49}$")
    name: str = Field(min_length=1, max_length=200)
    country_code: str = Field(default="KE", pattern=r"^[A-Z]{2}$")


class VersionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)


class GradeCreate(BaseModel):
    level: int = Field(ge=1, le=12)
    name: str = Field(min_length=1, max_length=50)


class AreaCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    sort_order: int = 0
    source_page_id: uuid.UUID | None = None


class AreaUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    sort_order: int | None = None
    archived: bool | None = None


class UnitCreate(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    title: str = Field(min_length=1, max_length=200)
    sort_order: int = 0
    source_page_id: uuid.UUID | None = None


class RubricIn(BaseModel):
    indicator: str
    exceeds: str
    meets: str
    approaches: str
    below: str


class StrandCreate(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    unit_id: uuid.UUID | None = None
    sort_order: int = 0
    source_page_id: uuid.UUID | None = None
    rubric: list[RubricIn] = Field(default_factory=list, max_length=100)


class OutcomeIn(BaseModel):
    code: str | None = Field(default=None, max_length=10)
    text: str

    @field_validator("text")
    @classmethod
    def _text(cls, v: str) -> str:
        return _clean(v)


class CompetencyIn(BaseModel):
    code: str = Field(max_length=40)
    description: str | None = None


class NamedItemIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None


class SubStrandCreate(BaseModel):
    number: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=200)
    suggested_lessons: int | None = Field(default=None, ge=0, le=500)
    link_to_other_areas: str | None = None
    sort_order: int = 0
    source_page_id: uuid.UUID | None = None
    topics: list[str] = Field(default_factory=list, max_length=100)
    outcomes: list[OutcomeIn] = Field(default_factory=list, max_length=100)
    experiences: list[str] = Field(default_factory=list, max_length=100)
    inquiry_questions: list[str] = Field(default_factory=list, max_length=50)
    competencies: list[CompetencyIn] = Field(default_factory=list, max_length=7)
    values: list[NamedItemIn] = Field(default_factory=list, max_length=20)
    pcis: list[NamedItemIn] = Field(default_factory=list, max_length=20)


class ReviewRequest(BaseModel):
    kind: Literal["learning_area", "unit", "strand", "sub_strand"]
    id: uuid.UUID
    status: Literal["draft", "in_review", "approved", "rejected"]
    comment: str | None = Field(default=None, max_length=2000)


class SourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    publisher: str = Field(min_length=1, max_length=200)
    edition_label: str | None = Field(default=None, max_length=100)
    original_filename: str | None = Field(default=None, max_length=300)
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_count: int | None = Field(default=None, ge=1)


class LicenseUpdate(BaseModel):
    license_status: Literal["not_requested", "requested", "granted", "denied"]
    license_notes: str | None = Field(default=None, max_length=2000)


class SubStrandUpdate(BaseModel):
    """Only the fields that are sent are changed. A list that is sent replaces the whole list."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    number: str | None = Field(default=None, min_length=1, max_length=20)
    suggested_lessons: int | None = Field(default=None, ge=0, le=500)
    link_to_other_areas: str | None = None
    topics: list[str] | None = Field(default=None, max_length=100)
    outcomes: list[OutcomeIn] | None = Field(default=None, max_length=100)
    experiences: list[str] | None = Field(default=None, max_length=100)
    inquiry_questions: list[str] | None = Field(default=None, max_length=50)
    competencies: list[CompetencyIn] | None = Field(default=None, max_length=7)
    values: list[NamedItemIn] | None = Field(default=None, max_length=20)
    pcis: list[NamedItemIn] | None = Field(default=None, max_length=20)

    @model_validator(mode="after")
    def _something_to_change(self) -> "SubStrandUpdate":
        if not self.model_fields_set:
            raise ValueError("Nothing to update.")
        return self


class StrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    number: str | None = Field(default=None, min_length=1, max_length=20)
    rubric: list[RubricIn] | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def _something_to_change(self) -> "StrandUpdate":
        if not self.model_fields_set:
            raise ValueError("Nothing to update.")
        return self
