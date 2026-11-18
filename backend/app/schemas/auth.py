import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.passwords import validate_password_strength


class _EmailIn(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def _lower(cls, v: str) -> str:
        return v.strip().lower()


class RegisterRequest(_EmailIn):
    model_config = ConfigDict(str_strip_whitespace=True)

    password: str = Field(min_length=1, max_length=256)
    display_name: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _check_password(self) -> "RegisterRequest":
        validate_password_strength(self.password, self.email)
        return self


class LoginRequest(_EmailIn):
    password: str = Field(min_length=1, max_length=256)


class PasswordResetRequest(_EmailIn):
    pass


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    new_password: str = Field(min_length=1, max_length=256)

    @field_validator("new_password")
    @classmethod
    def _check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str


class SessionResponse(BaseModel):
    user: UserOut
    csrf_token: str
    roles: list[str] = Field(default_factory=list)


class MessageResponse(BaseModel):
    message: str
