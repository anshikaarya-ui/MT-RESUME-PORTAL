from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from backend.database import Base


class Job(Base):
    __tablename__ = "job"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(180), index=True, nullable=False)
    job_description = Column(Text, nullable=False)
    structured_json = Column(Text, default="{}", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Candidate(Base):
    __tablename__ = "candidate"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("job.id"), index=True, nullable=False)
    full_name = Column(String(180), index=True, default="Unknown candidate", nullable=False)
    email = Column(String(250), index=True, default="", nullable=False)
    phone = Column(String(60), default="", nullable=False)
    file_name = Column(String(260), nullable=False)
    file_path = Column(String(600), nullable=False)
    raw_text = Column(Text, default="", nullable=False)
    profile_json = Column(Text, default="{}", nullable=False)
    status = Column(String(50), index=True, default="uploaded", nullable=False)
    consent = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Evaluation(Base):
    __tablename__ = "evaluation"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), index=True, nullable=False)
    job_id = Column(Integer, ForeignKey("job.id"), index=True, nullable=False)
    total_score = Column(Float, index=True, default=0, nullable=False)
    recommendation = Column(String(80), default="Needs human review", nullable=False)
    semantic_similarity = Column(Float, default=0, nullable=False)
    parameter_scores_json = Column(Text, default="{}", nullable=False)
    matched_skills_json = Column(Text, default="[]", nullable=False)
    missing_skills_json = Column(Text, default="[]", nullable=False)
    strengths_json = Column(Text, default="[]", nullable=False)
    concerns_json = Column(Text, default="[]", nullable=False)
    interview_questions_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
