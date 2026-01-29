from typing import Any

from pydantic import BaseModel, Field


class ProjectRead(BaseModel):
  id: str
  title: str | None = None
  client: str | None = None
  status: str | None = None
  description: str | None = None
  required_skills: list[str] = Field(default_factory=list)
  assigned_team: list[dict[str, Any]] = Field(default_factory=list)


class ProjectAssignmentRequest(BaseModel):
  programmer_ids: list[str]
