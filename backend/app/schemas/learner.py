import re
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

_PHONE_LIKE = re.compile(r"\d{6,}")


def clean_nickname(value: str) -> str:
    v = value.strip()
    if not 1 <= len(v) <= 50:
        raise ValueError("Nickname must be 1 to 50 characters.")
    if "@" in v or _PHONE_LIKE.search(v):
        raise ValueError("Please use a nickname only: no email addresses or phone numbers.")
    return v


class ConsentIn(BaseModel):
    notice_version: str = Field(min_length=1, max_length=32)
    accepted: bool

    @field_validator("accepted")
    @classmethod
    def _must_accept(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Consent is required to create a learner profile.")
        return v


class LearnerCreate(BaseModel):
    nickname: str
    grade: int = Field(ge=4, le=9)
    consent: ConsentIn

    @field_validator("nickname")
    @classmethod
    def _nickname(cls, v: str) -> str:
        return clean_nickname(v)


class LearnerUpdate(BaseModel):
    nickname: str | None = None
    grade: int | None = Field(default=None, ge=4, le=9)

    @field_validator("nickname")
    @classmethod
    def _nickname(cls, v: str | None) -> str | None:
        return None if v is None else clean_nickname(v)

    @model_validator(mode="after")
    def _something_to_update(self) -> "LearnerUpdate":
        if self.nickname is None and self.grade is None:
            raise ValueError("Nothing to update.")
        return self


class LearnerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nickname: str
    grade: int


class ConsentNoticeOut(BaseModel):
    version: str
    title: str
    text: str
    is_draft: bool
