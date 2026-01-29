from typing import Literal

from pydantic import BaseModel, Field


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
