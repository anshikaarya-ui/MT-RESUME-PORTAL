from __future__ import annotations

import json
import os
import re
from typing import Any

try:
    from openai import OpenAI
except Exception:  # OpenAI package is optional for local fallback mode.
    OpenAI = None  # type: ignore

from backend.config import MAX_LLM_CHARS, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL, OPENAI_MODEL
from backend.utils import clean_text, compact_list

COMMON_SKILLS = [
    "excel", "power bi", "tableau", "sql", "python", "r", "statistics", "analytics",
    "communication", "stakeholder management", "presentation", "leadership", "teamwork",
    "problem solving", "project management", "market research", "financial analysis",
    "sales", "operations", "supply chain", "data analysis", "machine learning",
    "marketing", "crm", "sap", "snowflake", "business analysis", "strategy",
]

PROTECTED_ATTRIBUTES = (
    "age, date of birth, gender, race, ethnicity, religion, caste, disability, marital status, "
    "pregnancy, sexuality, nationality, photo attractiveness, family background, political views"
)


def _client():
    if not OPENAI_API_KEY or OpenAI is None:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def _trim(text: str, limit: int = MAX_LLM_CHARS) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    return text[: limit // 2] + "\n\n[...middle removed...]\n\n" + text[-limit // 2 :]


RESUME_SCHEMA: dict[str, Any] = {
    "name": "resume_profile",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "full_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "location": {"type": "string"},
            "linkedin": {"type": "string"},
            "portfolio": {"type": "string"},
            "summary": {"type": "string"},
            "total_experience_years": {"type": "number"},
            "education": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "degree": {"type": "string"},
                        "field": {"type": "string"},
                        "institution": {"type": "string"},
                        "year": {"type": "string"},
                        "score_or_gpa": {"type": "string"},
                    },
                    "required": ["degree", "field", "institution", "year", "score_or_gpa"],
                },
            },
            "experience": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "role": {"type": "string"},
                        "company": {"type": "string"},
                        "duration": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["role", "company", "duration", "description"],
                },
            },
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "tools": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "description", "tools"],
                },
            },
            "technical_skills": {"type": "array", "items": {"type": "string"}},
            "business_skills": {"type": "array", "items": {"type": "string"}},
            "soft_skills": {"type": "array", "items": {"type": "string"}},
            "certifications": {"type": "array", "items": {"type": "string"}},
            "achievements": {"type": "array", "items": {"type": "string"}},
            "languages": {"type": "array", "items": {"type": "string"}},
            "management_trainee_signals": {"type": "array", "items": {"type": "string"}},
            "resume_quality_notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "full_name", "email", "phone", "location", "linkedin", "portfolio", "summary",
            "total_experience_years", "education", "experience", "projects", "technical_skills",
            "business_skills", "soft_skills", "certifications", "achievements", "languages",
            "management_trainee_signals", "resume_quality_notes",
        ],
    },
}

JOB_SCHEMA: dict[str, Any] = {
    "name": "job_description_profile",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "job_title": {"type": "string"},
            "business_goal": {"type": "string"},
            "must_have_skills": {"type": "array", "items": {"type": "string"}},
            "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
            "required_education": {"type": "array", "items": {"type": "string"}},
            "required_experience": {"type": "string"},
            "responsibilities": {"type": "array", "items": {"type": "string"}},
            "success_traits": {"type": "array", "items": {"type": "string"}},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "scoring_notes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "job_title", "business_goal", "must_have_skills", "nice_to_have_skills",
            "required_education", "required_experience", "responsibilities", "success_traits",
            "keywords", "scoring_notes",
        ],
    },
}

INSIGHT_SCHEMA: dict[str, Any] = {
    "name": "candidate_review_insights",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "strengths": {"type": "array", "items": {"type": "string"}},
            "concerns": {"type": "array", "items": {"type": "string"}},
            "interview_questions": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["strengths", "concerns", "interview_questions"],
    },
}


def _structured_call(schema: dict[str, Any], system: str, user: str) -> dict[str, Any]:
    client = _client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_schema", "json_schema": schema},
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)


def parse_resume(text: str) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        return heuristic_resume_parse(text)

    system = (
        "You extract resume information for a human-reviewed hiring workflow. "
        "Only use facts explicitly present in the resume. Do not infer or store protected attributes: "
        f"{PROTECTED_ATTRIBUTES}. If a field is missing, return an empty string, 0, or empty array. "
        "Do not evaluate the candidate here; extract only."
    )
    user = f"Resume text:\n\n{_trim(text)}"
    try:
        data = _structured_call(RESUME_SCHEMA, system, user)
        return _postprocess_resume(data)
    except Exception:
        return heuristic_resume_parse(text)


def parse_job_description(title: str, jd_text: str) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        return heuristic_job_parse(title, jd_text)

    system = (
        "You turn job descriptions into a structured matching rubric for human-reviewed recruitment. "
        "Focus on job-relevant skills, responsibilities, education, experience, and success traits. "
        "Never include protected attributes or demographic preferences."
    )
    user = f"Job title: {title}\n\nJob description:\n{_trim(jd_text)}"
    try:
        data = _structured_call(JOB_SCHEMA, system, user)
        return _postprocess_job(data, title)
    except Exception:
        return heuristic_job_parse(title, jd_text)


def generate_candidate_insights(
    job_structured: dict[str, Any],
    profile: dict[str, Any],
    scores: dict[str, float],
    matched_skills: list[str],
    missing_skills: list[str],
) -> dict[str, list[str]]:
    if not OPENAI_API_KEY:
        return fallback_insights(profile, scores, matched_skills, missing_skills)

    system = (
        "You write concise recruiter notes for a human reviewer. Use only job-relevant evidence. "
        "Do not mention or infer protected attributes. Do not make a hiring decision. "
        "The output is guidance for interview screening only."
    )
    user_payload = {
        "job": job_structured,
        "candidate_profile": profile,
        "scores": scores,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }
    try:
        data = _structured_call(INSIGHT_SCHEMA, system, json.dumps(user_payload, ensure_ascii=False))
        return {
            "strengths": compact_list(data.get("strengths", []), 5),
            "concerns": compact_list(data.get("concerns", []), 5),
            "interview_questions": compact_list(data.get("interview_questions", []), 6),
        }
    except Exception:
        return fallback_insights(profile, scores, matched_skills, missing_skills)


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    client = _client()
    if client is None:
        return None
    try:
        response = client.embeddings.create(
            model=OPENAI_EMBEDDING_MODEL,
            input=[_trim(t, 8000) for t in texts],
        )
        return [item.embedding for item in response.data]
    except Exception:
        return None


def _postprocess_resume(data: dict[str, Any]) -> dict[str, Any]:
    data["technical_skills"] = compact_list(data.get("technical_skills", []), 60)
    data["business_skills"] = compact_list(data.get("business_skills", []), 40)
    data["soft_skills"] = compact_list(data.get("soft_skills", []), 30)
    data["certifications"] = compact_list(data.get("certifications", []), 30)
    data["achievements"] = compact_list(data.get("achievements", []), 30)
    data["management_trainee_signals"] = compact_list(data.get("management_trainee_signals", []), 20)
    return data


def _postprocess_job(data: dict[str, Any], title: str) -> dict[str, Any]:
    data["job_title"] = data.get("job_title") or title
    for key in ["must_have_skills", "nice_to_have_skills", "required_education", "responsibilities", "success_traits", "keywords"]:
        data[key] = compact_list(data.get(key, []), 50)
    return data


def heuristic_resume_parse(text: str) -> dict[str, Any]:
    text = clean_text(text)
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    phone_match = re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    first_line = next((line for line in lines if len(line.split()) <= 6 and "@" not in line), "Unknown candidate")
    lower = text.lower()
    skills = [skill.title() for skill in COMMON_SKILLS if skill in lower]
    education = []
    edu_pattern = re.compile(r"\b(Bachelor|B\. ?Tech|BBA|MBA|Master|M\. ?Tech|B\. ?Com|M\. ?Com|PGDM|Graduate)\b", re.I)
    if edu_pattern.search(text):
        education.append({"degree": edu_pattern.search(text).group(0), "field": "", "institution": "", "year": "", "score_or_gpa": ""})
    projects = []
    if "project" in lower:
        projects.append({"name": "Project mentioned", "description": "Resume contains project experience.", "tools": skills[:5]})
    experience = []
    if any(w in lower for w in ["intern", "experience", "trainee", "associate", "analyst"]):
        experience.append({"role": "Experience mentioned", "company": "", "duration": "", "description": "Resume contains internship or work experience."})
    return _postprocess_resume(
        {
            "full_name": first_line,
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0).strip() if phone_match else "",
            "location": "",
            "linkedin": _find_url(text, "linkedin"),
            "portfolio": _find_url(text, "github") or _find_url(text, "portfolio"),
            "summary": lines[1] if len(lines) > 1 else "",
            "total_experience_years": _guess_experience_years(text),
            "education": education,
            "experience": experience,
            "projects": projects,
            "technical_skills": [s for s in skills if s.lower() not in {"communication", "leadership", "teamwork", "problem solving"}],
            "business_skills": [s for s in skills if s.lower() in {"analytics", "market research", "financial analysis", "sales", "operations", "supply chain", "business analysis", "strategy"}],
            "soft_skills": [s for s in skills if s.lower() in {"communication", "leadership", "teamwork", "problem solving", "presentation", "stakeholder management"}],
            "certifications": [],
            "achievements": [],
            "languages": [],
            "management_trainee_signals": [s for s in ["Leadership", "Communication", "Analytics", "Project experience"] if s.lower().split()[0] in lower],
            "resume_quality_notes": ["Parsed with local heuristic fallback. Add OPENAI_API_KEY for better extraction."],
        }
    )


def heuristic_job_parse(title: str, jd_text: str) -> dict[str, Any]:
    lower = jd_text.lower()
    found = [skill.title() for skill in COMMON_SKILLS if skill in lower]
    must = found[:8]
    nice = found[8:15]
    education = []
    if any(x in lower for x in ["graduate", "bachelor", "bba", "mba", "degree"]):
        education.append("Graduate or bachelor degree")
    return _postprocess_job(
        {
            "job_title": title,
            "business_goal": "Select candidates who fit the job description for human review.",
            "must_have_skills": must or ["Communication", "Problem Solving", "Teamwork"],
            "nice_to_have_skills": nice,
            "required_education": education,
            "required_experience": "Entry-level / Management Trainee suitable experience unless specified otherwise.",
            "responsibilities": _split_bullets(jd_text)[:8],
            "success_traits": ["Learning agility", "Communication", "Ownership", "Analytical thinking"],
            "keywords": found,
            "scoring_notes": ["Parsed with local heuristic fallback. Add OPENAI_API_KEY for better JD extraction."],
        },
        title,
    )


def fallback_insights(profile: dict[str, Any], scores: dict[str, float], matched_skills: list[str], missing_skills: list[str]) -> dict[str, list[str]]:
    strengths = []
    if matched_skills:
        strengths.append("Matches key skills: " + ", ".join(matched_skills[:6]))
    if profile.get("projects"):
        strengths.append("Has project experience relevant for an entry-level trainee role.")
    if profile.get("management_trainee_signals"):
        strengths.append("Shows management trainee signals: " + ", ".join(profile.get("management_trainee_signals", [])[:4]))
    concerns = []
    if missing_skills:
        concerns.append("Missing or unclear skills: " + ", ".join(missing_skills[:6]))
    if scores.get("resume_completeness", 0) < 3:
        concerns.append("Resume lacks some basic structured details such as education, projects, or contact information.")
    questions = [
        "Tell us about one project or internship where you solved a real business problem.",
        "Which part of this management trainee role interests you most, and why?",
        "Describe a time you worked with a team under a tight deadline.",
    ]
    return {"strengths": strengths[:5], "concerns": concerns[:5], "interview_questions": questions[:6]}


def _find_url(text: str, keyword: str) -> str:
    for match in re.finditer(r"https?://\S+|www\.\S+", text):
        url = match.group(0).rstrip(".,);]")
        if keyword.lower() in url.lower():
            return url
    return ""


def _split_bullets(text: str) -> list[str]:
    parts = re.split(r"[\n\r]+|(?:\s*[•*-]\s+)", text)
    return [p.strip() for p in parts if 20 <= len(p.strip()) <= 220]


def _guess_experience_years(text: str) -> float:
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs)", text, flags=re.I)
    if not matches:
        return 0.0
    try:
        return max(float(x) for x in matches)
    except Exception:
        return 0.0
