# Management Trainee CV Screening Portal

An end-to-end starter system for collecting candidate CVs, extracting structured resume data, storing it in a database, scoring candidates against a Management Trainee job description, and giving the company a dashboard plus downloadable reports.

This is designed for **human-in-the-loop screening**. It should not be used as the only basis for final hiring decisions.

## What it includes

- Candidate CV upload portal using Streamlit
- Company dashboard using Streamlit + Plotly
- FastAPI backend with REST endpoints
- SQLite database through SQLAlchemy
- PDF, DOCX, and TXT resume extraction
- LLM-based resume and job-description extraction through OpenAI Structured Outputs
- Semantic matching through OpenAI embeddings
- Offline fallback parser and TF-IDF matcher for local testing without an API key
- Candidate score out of 100 across parameters
- Downloadable CSV and HTML candidate reports
- Apple-inspired UI: soft glass cards, spacing, rounded surfaces, minimal typography

## Scoring model

| Parameter | Max Points | Purpose |
|---|---:|---|
| Semantic JD fit | 30 | Embedding similarity between CV text and JD |
| Skills match | 25 | Must-have and nice-to-have skill match |
| Education fit | 15 | Education relevance based on JD |
| Experience and projects | 20 | Internships, projects, work experience, relevant responsibilities |
| Leadership and communication | 5 | Management-trainee signals such as leadership, teamwork, presentations |
| Resume completeness | 5 | Basic contact, education, skills, and evidence completeness |
| **Total** | **100** | Recruiter review score |

## Folder structure

```text
mt_resume_portal/
  backend/
    main.py                       # FastAPI routes
    models.py                     # SQLAlchemy tables
    schemas.py                    # API response models
    services/
      document_extraction.py      # PDF/DOCX/TXT extraction
      openai_service.py           # LLM extraction, embeddings, fallback parser
      scoring.py                  # Semantic scoring and parameter scoring
      reports.py                  # CSV and HTML report generation
  dashboard/
    app.py                        # Streamlit candidate portal + company dashboard
  scripts/
    seed_demo.py                  # Creates a demo job and sample candidates
  data/
    uploads/                      # Uploaded CVs
    exports/                      # Optional export folder
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
```

## Run locally

### 1. Create environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Open `.env` and add an OpenAI API key if you want LLM extraction and OpenAI embeddings:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
DATABASE_URL=sqlite:///./data/resume_portal.db
UPLOAD_DIR=./data/uploads
API_BASE_URL=http://localhost:8000
```

The app still runs without an API key using the fallback parser and local TF-IDF similarity, but scoring quality will be lower.

### 3. Start the backend

```bash
uvicorn backend.main:app --reload
```

API docs will be available at:

```text
http://localhost:8000/docs
```

### 4. Start the dashboard

Open a second terminal in the same project folder:

```bash
streamlit run dashboard/app.py
```

Dashboard URL:

```text
http://localhost:8501
```

### 5. Seed demo data

With the virtual environment active:

```bash
python scripts/seed_demo.py
```

Then refresh the Streamlit dashboard and select the seeded Management Trainee role.

## Run with Docker

```bash
cp .env.example .env
# Optional: add OPENAI_API_KEY to .env

docker compose up --build
```

Then open:

```text
http://localhost:8501
```

## API overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | API status |
| `/jobs` | POST | Create a job and structured rubric |
| `/jobs` | GET | List jobs |
| `/jobs/{job_id}` | GET | Get job details |
| `/jobs/{job_id}/candidates` | POST | Upload one candidate CV |
| `/jobs/{job_id}/candidates/bulk` | POST | Upload many CVs |
| `/jobs/{job_id}/rankings` | GET | Candidate ranking table |
| `/jobs/{job_id}/report` | GET | Shortlist report JSON |
| `/jobs/{job_id}/report.csv` | GET | Download CSV report |
| `/jobs/{job_id}/report.html` | GET | Download styled HTML report |

## Production hardening checklist

Before using this in a real recruitment process, add:

1. Authentication and role-based access for recruiters, hiring managers, and candidates.
2. Encrypted object storage for CV files instead of local disk.
3. Database migration to PostgreSQL or Snowflake-backed storage.
4. Audit logs for every score, score version, reviewer action, and final decision.
5. Candidate consent text, retention policy, deletion workflow, and privacy notice.
6. PII minimization and field-level encryption for email and phone.
7. Bias testing across score distributions and adverse-impact review by legal or HR.
8. OCR for scanned PDFs, using Tesseract, AWS Textract, Azure Document Intelligence, or Google Document AI.
9. Human override workflow and reviewer comments.
10. Monitoring for extraction failures, prompt failures, API cost, and latency.

## Important hiring-safety note

The system deliberately labels recommendations as “human review” rather than final decisions. Use it to organize candidate evidence, not to automatically accept or reject candidates. Keep protected attributes out of the JD, prompts, scoring logic, reports, and reviewer workflow.
