from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CriminalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None
    nickname: str
    reward: float
    latitude: float | None
    longitude: float | None
    location_note: str | None
    difficulty: int
    armed: bool
    has_crew: bool
    escape_master: bool


class HuntCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    criminal_id: int
    success: bool
    notes: str = Field(min_length=1)


class HuntUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: bool | None = None
    notes: str | None = Field(default=None, min_length=1)


class HuntOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criminal_id: int
    success: bool
    notes: str
    created_at: datetime
