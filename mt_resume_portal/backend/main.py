from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from backend.config import ALLOWED_EXTENSIONS, MAX_FILE_MB, UPLOAD_DIR
from backend.database import get_session, init_db
from backend.models import Candidate, Evaluation, Job
from backend.schemas import CandidateOut, JobCreate, JobOut, RankingRow, ReportOut
from backend.services.document_extraction import ExtractionError, extract_text_from_file
from backend.services.openai_service import parse_job_description, parse_resume
from backend.services.reports import rankings_to_csv, rankings_to_html
from backend.services.scoring import evaluate_candidate
from backend.utils import safe_filename, safe_json_loads, to_json

app = FastAPI(
    title="Management Trainee Resume Screening Portal",
    description="Human-reviewed CV extraction, scoring, reporting, and dashboard API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/jobs", response_model=JobOut)
def create_job(payload: JobCreate, session: Session = Depends(get_session)) -> JobOut:
    structured = parse_job_description(payload.title, payload.job_description)
    job = Job(
        title=payload.title.strip(),
        job_description=payload.job_description.strip(),
        structured_json=to_json(structured),
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return _job_out(job)


@app.get("/jobs", response_model=list[JobOut])
def list_jobs(session: Session = Depends(get_session)) -> list[JobOut]:
    jobs = session.query(Job).order_by(Job.created_at.desc()).all()
    return [_job_out(job) for job in jobs]


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_session)) -> JobOut:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_out(job)


@app.post("/jobs/{job_id}/candidates", response_model=CandidateOut)
async def upload_candidate(
    job_id: int,
    file: Annotated[UploadFile, File()],
    consent: Annotated[bool, Form()] = False,
    session: Session = Depends(get_session),
) -> CandidateOut:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not consent:
        raise HTTPException(status_code=400, detail="Candidate consent is required before storing or processing the CV.")
    candidate = await _process_uploaded_file(session, job, file, consent)
    evaluation = _get_eval_dict(session, candidate.id)
    return _candidate_out(candidate, evaluation)


@app.post("/jobs/{job_id}/candidates/bulk", response_model=list[CandidateOut])
async def upload_candidates_bulk(
    job_id: int,
    files: Annotated[list[UploadFile], File()],
    consent: Annotated[bool, Form()] = False,
    session: Session = Depends(get_session),
) -> list[CandidateOut]:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not consent:
        raise HTTPException(status_code=400, detail="Company confirmation of candidate consent is required.")

    results: list[CandidateOut] = []
    for file in files:
        candidate = await _process_uploaded_file(session, job, file, consent)
        results.append(_candidate_out(candidate, _get_eval_dict(session, candidate.id)))
    return results


@app.get("/candidates/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: int, session: Session = Depends(get_session)) -> CandidateOut:
    candidate = session.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return _candidate_out(candidate, _get_eval_dict(session, candidate.id))


@app.get("/jobs/{job_id}/rankings", response_model=list[RankingRow])
def get_rankings(job_id: int, session: Session = Depends(get_session)) -> list[RankingRow]:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return [RankingRow(**row) for row in _ranking_rows(session, job_id)]


@app.get("/jobs/{job_id}/report", response_model=ReportOut)
def get_report(
    job_id: int,
    min_score: float = 70,
    top_n: int = 30,
    session: Session = Depends(get_session),
) -> ReportOut:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = _ranking_rows(session, job_id)
    filtered = [row for row in rows if row["total_score"] >= min_score][: max(1, top_n)]
    avg = round(sum(row["total_score"] for row in rows) / len(rows), 2) if rows else 0.0
    return ReportOut(
        job=_job_out(job),
        threshold=min_score,
        total_candidates=len(rows),
        recommended_count=len(filtered),
        average_score=avg,
        candidates=[RankingRow(**row) for row in filtered],
    )


@app.get("/jobs/{job_id}/report.csv")
def get_report_csv(
    job_id: int,
    min_score: float = 70,
    top_n: int = 30,
    session: Session = Depends(get_session),
) -> PlainTextResponse:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = [row for row in _ranking_rows(session, job_id) if row["total_score"] >= min_score][: max(1, top_n)]
    csv_text = rankings_to_csv(rows)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_candidate_report.csv"},
    )


@app.get("/jobs/{job_id}/report.html")
def get_report_html(
    job_id: int,
    min_score: float = 70,
    top_n: int = 30,
    session: Session = Depends(get_session),
) -> HTMLResponse:
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    rows = [row for row in _ranking_rows(session, job_id) if row["total_score"] >= min_score][: max(1, top_n)]
    html_text = rankings_to_html(job.title, min_score, rows)
    return HTMLResponse(
        html_text,
        headers={"Content-Disposition": f"attachment; filename=job_{job_id}_candidate_report.html"},
    )


async def _process_uploaded_file(session: Session, job: Job, upload: UploadFile, consent: bool) -> Candidate:
    filename = safe_filename(upload.filename or "resume.pdf")
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type {suffix}. Use PDF, DOCX, or TXT.")

    content = await upload.read()
    if len(content) > MAX_FILE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max size is {MAX_FILE_MB} MB.")

    stored_name = f"{uuid.uuid4().hex}_{filename}"
    path = UPLOAD_DIR / stored_name
    path.write_bytes(content)

    try:
        raw_text = extract_text_from_file(path)
        profile = parse_resume(raw_text)
        status = "evaluated"
    except ExtractionError as exc:
        raw_text = ""
        profile = {
            "full_name": "Unknown candidate",
            "email": "",
            "phone": "",
            "resume_quality_notes": [str(exc)],
        }
        status = "extraction_failed"

    candidate = Candidate(
        job_id=job.id,
        full_name=(profile.get("full_name") or "Unknown candidate")[:180],
        email=(profile.get("email") or "")[:250],
        phone=(profile.get("phone") or "")[:60],
        file_name=filename,
        file_path=str(path),
        raw_text=raw_text,
        profile_json=to_json(profile),
        status=status,
        consent=consent,
    )
    session.add(candidate)
    session.commit()
    session.refresh(candidate)

    if status == "evaluated":
        evaluation_data = evaluate_candidate(
            job_description=job.job_description,
            job_structured=safe_json_loads(job.structured_json, {}),
            resume_text=raw_text,
            profile=profile,
        )
        evaluation = Evaluation(
            candidate_id=candidate.id,
            job_id=job.id,
            total_score=evaluation_data["total_score"],
            recommendation=evaluation_data["recommendation"],
            semantic_similarity=evaluation_data["semantic_similarity"],
            parameter_scores_json=to_json(evaluation_data["parameter_scores"]),
            matched_skills_json=to_json(evaluation_data["matched_skills"]),
            missing_skills_json=to_json(evaluation_data["missing_skills"]),
            strengths_json=to_json(evaluation_data["strengths"]),
            concerns_json=to_json(evaluation_data["concerns"]),
            interview_questions_json=to_json(evaluation_data["interview_questions"]),
        )
        session.add(evaluation)
        session.commit()
    return candidate


def _job_out(job: Job) -> JobOut:
    return JobOut(
        id=job.id,
        title=job.title,
        job_description=job.job_description,
        structured=safe_json_loads(job.structured_json, {}),
        created_at=job.created_at,
    )


def _candidate_out(candidate: Candidate, evaluation: dict | None = None) -> CandidateOut:
    return CandidateOut(
        id=candidate.id,
        job_id=candidate.job_id,
        full_name=candidate.full_name,
        email=candidate.email,
        phone=candidate.phone,
        file_name=candidate.file_name,
        status=candidate.status,
        profile=safe_json_loads(candidate.profile_json, {}),
        created_at=candidate.created_at,
        evaluation=evaluation,
    )


def _get_eval_dict(session: Session, candidate_id: int | None) -> dict | None:
    if candidate_id is None:
        return None
    evaluation = session.query(Evaluation).filter(Evaluation.candidate_id == candidate_id).first()
    if not evaluation:
        return None
    return {
        "id": evaluation.id,
        "total_score": evaluation.total_score,
        "recommendation": evaluation.recommendation,
        "semantic_similarity": evaluation.semantic_similarity,
        "parameter_scores": safe_json_loads(evaluation.parameter_scores_json, {}),
        "matched_skills": safe_json_loads(evaluation.matched_skills_json, []),
        "missing_skills": safe_json_loads(evaluation.missing_skills_json, []),
        "strengths": safe_json_loads(evaluation.strengths_json, []),
        "concerns": safe_json_loads(evaluation.concerns_json, []),
        "interview_questions": safe_json_loads(evaluation.interview_questions_json, []),
        "created_at": evaluation.created_at,
    }


def _ranking_rows(session: Session, job_id: int) -> list[dict]:
    evaluations = session.query(Evaluation).filter(Evaluation.job_id == job_id).order_by(Evaluation.total_score.desc()).all()
    rows = []
    for ev in evaluations:
        candidate = session.get(Candidate, ev.candidate_id)
        if not candidate:
            continue
        rows.append(
            {
                "candidate_id": candidate.id,
                "full_name": candidate.full_name,
                "email": candidate.email,
                "phone": candidate.phone,
                "total_score": ev.total_score,
                "recommendation": ev.recommendation,
                "semantic_similarity": ev.semantic_similarity,
                "parameter_scores": safe_json_loads(ev.parameter_scores_json, {}),
                "matched_skills": safe_json_loads(ev.matched_skills_json, []),
                "missing_skills": safe_json_loads(ev.missing_skills_json, []),
                "strengths": safe_json_loads(ev.strengths_json, []),
                "concerns": safe_json_loads(ev.concerns_json, []),
                "interview_questions": safe_json_loads(ev.interview_questions_json, []),
                "uploaded_at": candidate.created_at,
            }
        )
    return rows
