from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.config import UPLOAD_DIR
from backend.database import SessionLocal, init_db
from backend.models import Candidate, Evaluation, Job
from backend.services.document_extraction import extract_text_from_file
from backend.services.openai_service import parse_job_description, parse_resume
from backend.services.scoring import evaluate_candidate
from backend.utils import to_json

DEMO_JD = """
We are hiring Management Trainees for a 12-month rotational program across Sales, Operations,
Finance and Business Analytics. Candidates should be graduates with strong communication,
problem solving, teamwork, Excel, Power BI or SQL exposure, comfort with data analysis,
presentation skills, and learning agility. Responsibilities include market analysis, process
improvement projects, stakeholder reporting, business reviews, and supporting managers with
operational execution. Nice to have: Python, financial analysis, CRM/SAP exposure, leadership in
clubs or campus initiatives.
"""

SAMPLE_RESUMES = {
    "ananya_sharma.txt": """
Ananya Sharma
ananya.sharma@example.com | +91 98765 43210 | linkedin.com/in/ananyasharma
BBA, Marketing and Business Analytics, Delhi University, 2026
Skills: Excel, Power BI, SQL, market research, communication, presentation, teamwork, stakeholder management
Experience: Sales Strategy Intern, BrightFoods, 3 months. Built weekly sales dashboard in Power BI,
analysed regional revenue variance, presented findings to area managers.
Projects: Campus retail expansion case study using Excel and SQL; recommended store-level promotional actions.
Achievements: President of Entrepreneurship Cell; coordinated a 25-member team for annual business fest.
""",
    "rohan_mehta.txt": """
Rohan Mehta
rohan.mehta@example.com | +91 91234 56789
Bachelor of Commerce, 2025
Skills: Excel, financial analysis, communication, SAP basics, teamwork
Experience: Finance Intern at Apex Services for 2 months. Assisted with invoice reconciliation and monthly MIS reports.
Project: Working capital analysis for FMCG sector using Excel.
Achievement: Led college finance club workshop.
""",
    "kritika_rao.txt": """
Kritika Rao
kritika.rao@example.com
BA English, 2026
Skills: writing, communication, event management, teamwork
Experience: Content volunteer for university magazine.
Achievements: Organized debate competition.
""",
}


def main() -> None:
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with SessionLocal() as session:
        structured = parse_job_description("Management Trainee", DEMO_JD)
        job = Job(title="Management Trainee", job_description=DEMO_JD.strip(), structured_json=to_json(structured))
        session.add(job)
        session.commit()
        session.refresh(job)

        for filename, text in SAMPLE_RESUMES.items():
            path = Path(UPLOAD_DIR) / filename
            path.write_text(text.strip(), encoding="utf-8")
            raw_text = extract_text_from_file(path)
            profile = parse_resume(raw_text)
            candidate = Candidate(
                job_id=job.id,
                full_name=profile.get("full_name") or "Unknown candidate",
                email=profile.get("email") or "",
                phone=profile.get("phone") or "",
                file_name=filename,
                file_path=str(path),
                raw_text=raw_text,
                profile_json=to_json(profile),
                status="evaluated",
                consent=True,
            )
            session.add(candidate)
            session.commit()
            session.refresh(candidate)

            eval_data = evaluate_candidate(DEMO_JD, structured, raw_text, profile)
            evaluation = Evaluation(
                candidate_id=candidate.id,
                job_id=job.id,
                total_score=eval_data["total_score"],
                recommendation=eval_data["recommendation"],
                semantic_similarity=eval_data["semantic_similarity"],
                parameter_scores_json=to_json(eval_data["parameter_scores"]),
                matched_skills_json=to_json(eval_data["matched_skills"]),
                missing_skills_json=to_json(eval_data["missing_skills"]),
                strengths_json=to_json(eval_data["strengths"]),
                concerns_json=to_json(eval_data["concerns"]),
                interview_questions_json=to_json(eval_data["interview_questions"]),
            )
            session.add(evaluation)
            session.commit()

        print(f"Seeded demo job ID: {job.id} with {len(SAMPLE_RESUMES)} candidate resumes.")


if __name__ == "__main__":
    main()
