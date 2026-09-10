from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=180)
    job_description: str = Field(min_length=20)


class JobOut(BaseModel):
    id: int
    title: str
    job_description: str
    structured: dict[str, Any]
    created_at: datetime


class CandidateOut(BaseModel):
    id: int
    job_id: int
    full_name: str
    email: str
    phone: str
    file_name: str
    status: str
    profile: dict[str, Any]
    created_at: datetime
    evaluation: Optional[dict[str, Any]] = None


class RankingRow(BaseModel):
    candidate_id: int
    full_name: str
    email: str
    phone: str
    total_score: float
    recommendation: str
    semantic_similarity: float
    parameter_scores: dict[str, float]
    matched_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    concerns: list[str]
    interview_questions: list[str]
    uploaded_at: datetime


class ReportOut(BaseModel):
    job: JobOut
    threshold: float
    total_candidates: int
    recommended_count: int
    average_score: float
    candidates: list[RankingRow]
