from typing import Literal

from pydantic import BaseModel, Field


class _RFPSkillRequirement(BaseModel):
  name: str
  level: Literal["Beginner", "Intermediate", "Advanced", "Expert"]
  mandatory: bool


class RFPRead(BaseModel):
  id: str
  title: str | None = None
  client: str | None = None
  budget: str | None = None
  needed_skills: list[_RFPSkillRequirement] = Field(default_factory=list)
