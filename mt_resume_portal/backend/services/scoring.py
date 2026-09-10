from __future__ import annotations

import math
import re
from typing import Any

import numpy as np
from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from backend.services.openai_service import embed_texts, generate_candidate_insights
from backend.utils import clamp, compact_list


PARAMETER_MAX = {
    "semantic_jd_fit": 30.0,
    "skills_match": 25.0,
    "education_fit": 15.0,
    "experience_projects": 20.0,
    "leadership_communication": 5.0,
    "resume_completeness": 5.0,
}


def evaluate_candidate(
    job_description: str,
    job_structured: dict[str, Any],
    resume_text: str,
    profile: dict[str, Any],
) -> dict[str, Any]:
    semantic_similarity = semantic_text_similarity(job_description, resume_text)
    semantic_score = round(_scaled_semantic_score(semantic_similarity) * PARAMETER_MAX["semantic_jd_fit"], 2)

    matched_skills, missing_skills, skill_ratio = skill_match(job_structured, profile)
    skills_score = round(skill_ratio * PARAMETER_MAX["skills_match"], 2)

    education_score = round(education_fit(job_structured, profile) * PARAMETER_MAX["education_fit"], 2)
    exp_score = round(experience_project_fit(job_structured, profile, resume_text) * PARAMETER_MAX["experience_projects"], 2)
    leadership_score = round(leadership_fit(profile, resume_text) * PARAMETER_MAX["leadership_communication"], 2)
    completeness_score = round(resume_completeness(profile) * PARAMETER_MAX["resume_completeness"], 2)

    parameter_scores = {
        "semantic_jd_fit": semantic_score,
        "skills_match": skills_score,
        "education_fit": education_score,
        "experience_projects": exp_score,
        "leadership_communication": leadership_score,
        "resume_completeness": completeness_score,
    }
    total_score = round(sum(parameter_scores.values()), 2)
    recommendation = recommendation_label(total_score)
    insights = generate_candidate_insights(job_structured, profile, parameter_scores, matched_skills, missing_skills)

    return {
        "total_score": total_score,
        "recommendation": recommendation,
        "semantic_similarity": round(semantic_similarity, 4),
        "parameter_scores": parameter_scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "strengths": insights.get("strengths", []),
        "concerns": insights.get("concerns", []),
        "interview_questions": insights.get("interview_questions", []),
    }


def semantic_text_similarity(a: str, b: str) -> float:
    # Prefer OpenAI embeddings. If unavailable, use local TF-IDF similarity for offline testing.
    vectors = embed_texts([a, b])
    if vectors and len(vectors) == 2:
        va = np.array(vectors[0], dtype=float)
        vb = np.array(vectors[1], dtype=float)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        if denom == 0:
            return 0.0
        return float(np.dot(va, vb) / denom)

    try:
        matrix = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=1).fit_transform([a, b])
        return float(cosine_similarity(matrix[0], matrix[1])[0][0])
    except Exception:
        return 0.0


def _scaled_semantic_score(sim: float) -> float:
    # OpenAI embedding cosine values are often clustered. This maps weak->0 and strong->1.
    # TF-IDF fallback can also use the same scale without breaking the score.
    return clamp((sim - 0.18) / 0.52)


def skill_match(job_structured: dict[str, Any], profile: dict[str, Any]) -> tuple[list[str], list[str], float]:
    required = _normalize_many(job_structured.get("must_have_skills", []))
    preferred = _normalize_many(job_structured.get("nice_to_have_skills", []))
    candidate_skills = _normalize_many(
        profile.get("technical_skills", [])
        + profile.get("business_skills", [])
        + profile.get("soft_skills", [])
        + profile.get("certifications", [])
        + profile.get("management_trainee_signals", [])
    )

    if not required and not preferred:
        return [], [], 0.5

    matched_required = _fuzzy_matches(required, candidate_skills)
    matched_preferred = _fuzzy_matches(preferred, candidate_skills)
    missing_required = [s for s in required if s not in matched_required]

    required_ratio = len(matched_required) / len(required) if required else 1.0
    preferred_ratio = len(matched_preferred) / len(preferred) if preferred else 0.0
    ratio = clamp(required_ratio * 0.78 + preferred_ratio * 0.22)

    matched_readable = compact_list([_title_skill(x) for x in matched_required + matched_preferred], 20)
    missing_readable = compact_list([_title_skill(x) for x in missing_required], 20)
    return matched_readable, missing_readable, ratio


def education_fit(job_structured: dict[str, Any], profile: dict[str, Any]) -> float:
    req_text = " ".join(job_structured.get("required_education", [])).lower()
    educations = profile.get("education", []) or []
    if not req_text:
        return 0.9 if educations else 0.55

    candidate_text = " ".join(
        " ".join(str(v) for v in edu.values()) if isinstance(edu, dict) else str(edu)
        for edu in educations
    ).lower()
    if not candidate_text:
        return 0.15

    degree_keywords = ["bachelor", "graduate", "bba", "b.tech", "btech", "mba", "master", "pgdm", "degree"]
    required_degree_words = [kw for kw in degree_keywords if kw in req_text]
    if not required_degree_words:
        return 0.85
    if any(kw in candidate_text for kw in required_degree_words):
        return 1.0
    if any(kw in candidate_text for kw in degree_keywords):
        return 0.72
    return 0.35


def experience_project_fit(job_structured: dict[str, Any], profile: dict[str, Any], resume_text: str) -> float:
    exp_count = len(profile.get("experience", []) or [])
    project_count = len(profile.get("projects", []) or [])
    years = _safe_float(profile.get("total_experience_years", 0))
    text = resume_text.lower()

    internship_signal = 1 if any(x in text for x in ["intern", "trainee", "campus", "placement", "project", "case study"]) else 0
    responsibility_terms = _normalize_many(job_structured.get("responsibilities", []) + job_structured.get("keywords", []))
    resume_terms = _normalize_many(re.findall(r"[A-Za-z][A-Za-z +.#-]{2,}", text)[:500])
    relevance = 0.0
    if responsibility_terms:
        rel_matches = _fuzzy_matches(responsibility_terms[:40], resume_terms, threshold=86)
        relevance = min(0.35, len(rel_matches) / max(10, len(responsibility_terms)) * 0.35)

    base = min(0.38, exp_count * 0.12 + project_count * 0.08 + internship_signal * 0.08)
    years_component = min(0.27, years * 0.09)
    return clamp(base + years_component + relevance + 0.18)


def leadership_fit(profile: dict[str, Any], resume_text: str) -> float:
    text = resume_text.lower()
    signals = profile.get("management_trainee_signals", []) + profile.get("achievements", []) + profile.get("soft_skills", [])
    signal_text = " ".join(str(s) for s in signals).lower()
    keywords = [
        "lead", "leader", "captain", "coordinated", "managed", "organized", "presented",
        "volunteer", "club", "committee", "communication", "stakeholder", "team", "initiative",
    ]
    hits = sum(1 for kw in keywords if kw in text or kw in signal_text)
    return clamp(hits / 7)


def resume_completeness(profile: dict[str, Any]) -> float:
    fields = [
        bool(profile.get("full_name")) and profile.get("full_name") != "Unknown candidate",
        bool(profile.get("email") or profile.get("phone")),
        bool(profile.get("education")),
        bool(profile.get("technical_skills") or profile.get("business_skills") or profile.get("soft_skills")),
        bool(profile.get("experience") or profile.get("projects") or profile.get("achievements")),
    ]
    return sum(1 for x in fields if x) / len(fields)


def recommendation_label(total_score: float) -> str:
    if total_score >= 85:
        return "Strong human review"
    if total_score >= 70:
        return "Recommended for human review"
    if total_score >= 55:
        return "Backup review pool"
    return "Do not prioritize"


def _normalize_many(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen = set()
    for value in values or []:
        text = _normalize_skill(str(value))
        if text and text not in seen and len(text) <= 80:
            out.append(text)
            seen.add(text)
    return out


def _normalize_skill(skill: str) -> str:
    skill = skill.lower().replace("&", " and ")
    skill = re.sub(r"[^a-z0-9+#. ]+", " ", skill)
    skill = re.sub(r"\s+", " ", skill).strip()
    aliases = {
        "ms excel": "excel",
        "microsoft excel": "excel",
        "advanced excel": "excel",
        "powerbi": "power bi",
        "structured query language": "sql",
        "communication skills": "communication",
        "problem solving skills": "problem solving",
    }
    return aliases.get(skill, skill)


def _fuzzy_matches(required: list[str], candidate: list[str], threshold: int = 84) -> list[str]:
    matches: list[str] = []
    for req in required:
        if not req:
            continue
        best = max((fuzz.token_set_ratio(req, cand) for cand in candidate), default=0)
        if best >= threshold or req in candidate:
            matches.append(req)
    return matches


def _title_skill(skill: str) -> str:
    special = {"sql": "SQL", "python": "Python", "power bi": "Power BI", "sap": "SAP", "crm": "CRM"}
    return special.get(skill, skill.title())


def _safe_float(value: Any) -> float:
    try:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return 0.0
        return float(value)
    except Exception:
        return 0.0
