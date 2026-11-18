import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.permissions import ALL_ROLES


class AdminUserOut(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    is_active: bool
    roles: list[str]


class RolesUpdate(BaseModel):
    roles: list[str] = Field(min_length=1, max_length=len(ALL_ROLES))

    @field_validator("roles")
    @classmethod
    def _known_roles(cls, v: list[str]) -> list[str]:
        unknown = [r for r in v if r not in ALL_ROLES]
        if unknown:
            raise ValueError("Unknown role: " + ", ".join(unknown))
        return sorted(set(v))


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    actor_user_id: uuid.UUID | None
    action: str
    target_type: str | None
    target_id: str | None
    details: dict[str, Any] | None
