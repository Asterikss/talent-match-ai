from typing import Any, Literal

from pydantic import BaseModel, Field

### Matching Algorithm models


class CandidateMatch(BaseModel):
  programmer_id: str
  programmer_name: str
  role: str | None = None
  total_score: float
  skill_match_percent: float
  missing_mandatory_skills: list[str] = Field(default_factory=list)
  missing_optional_skills: list[str] = Field(default_factory=list)
  status: Literal["available", "available_soon", "unavailable"]
  days_until_available: int | None = None
  current_project_end_date: str | None = None
  current_project_name: str | None = None


class MatchResponse(BaseModel):
  rfp_id: str
  perfect_matches: list[CandidateMatch] = Field(default_factory=list)
  future_matches: list[CandidateMatch] = Field(default_factory=list)
  partial_matches: list[CandidateMatch] = Field(default_factory=list)


class AssignmentRequest(BaseModel):
  programmer_ids: list[str]


class ProgrammerRead(BaseModel):
  id: str
  name: str | None = None
  role: str | None = None
  location: str | None = None
  is_assigned: bool = False
  current_project: str | None = None
  skills: dict[str, list[str]] = Field(
    default_factory=lambda: {
      "Expert": [],
      "Advanced": [],
      "Intermediate": [],
      "Beginner": [],
    }
  )


class ProjectRead(BaseModel):
  id: str
  title: str | None = None
  client: str | None = None
  status: str | None = None
  description: str | None = None
  required_skills: list[str] = Field(default_factory=list)
  assigned_team: list[dict[str, Any]] = Field(default_factory=list)


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
