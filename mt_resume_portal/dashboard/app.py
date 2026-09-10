from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="MT Talent Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
          --apple-bg: #f5f5f7;
          --apple-card: rgba(255,255,255,.82);
          --apple-text: #1d1d1f;
          --apple-muted: #6e6e73;
          --apple-blue: #0071e3;
          --apple-line: rgba(210,210,215,.9);
          --apple-green: #34c759;
          --apple-orange: #ff9500;
          --apple-red: #ff3b30;
        }
        html, body, [class*="css"] {
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif !important;
          color: var(--apple-text);
        }
        .stApp {
          background:
            radial-gradient(circle at top left, rgba(0,113,227,.10), transparent 30%),
            radial-gradient(circle at 70% 10%, rgba(52,199,89,.09), transparent 22%),
            var(--apple-bg);
        }
        section[data-testid="stSidebar"] {
          background: rgba(255,255,255,.70);
          backdrop-filter: blur(24px);
          border-right: 1px solid var(--apple-line);
        }
        .hero {
          padding: 36px 34px;
          border: 1px solid var(--apple-line);
          border-radius: 34px;
          background: linear-gradient(135deg, rgba(255,255,255,.92), rgba(237,244,255,.88));
          box-shadow: 0 26px 70px rgba(0,0,0,.07);
          margin-bottom: 22px;
        }
        .hero h1 {
          font-size: 52px;
          line-height: 1.02;
          letter-spacing: -.055em;
          margin: 0 0 8px;
          font-weight: 800;
        }
        .hero p {
          color: var(--apple-muted);
          font-size: 18px;
          max-width: 920px;
          margin: 0;
        }
        .glass-card {
          padding: 24px;
          border-radius: 28px;
          border: 1px solid var(--apple-line);
          background: var(--apple-card);
          backdrop-filter: blur(20px);
          box-shadow: 0 18px 42px rgba(0,0,0,.055);
          height: 100%;
        }
        .metric-card {
          padding: 22px 22px 18px;
          border-radius: 26px;
          background: rgba(255,255,255,.86);
          border: 1px solid var(--apple-line);
          box-shadow: 0 12px 30px rgba(0,0,0,.045);
        }
        .metric-label { color: var(--apple-muted); font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em; }
        .metric-value { font-size: 38px; font-weight: 800; letter-spacing: -.05em; margin-top: 4px; }
        .small-muted { color: var(--apple-muted); font-size: 14px; }
        .pill {
          display: inline-block;
          padding: 7px 12px;
          border-radius: 999px;
          background: rgba(0,113,227,.10);
          color: var(--apple-blue);
          font-weight: 700;
          font-size: 13px;
          margin-right: 6px;
          margin-bottom: 6px;
        }
        div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button {
          border-radius: 999px !important;
          border: 0 !important;
          background: #111111 !important;
          color: #ffffff !important;
          padding: 0.7rem 1.15rem !important;
          font-weight: 700 !important;
          box-shadow: 0 10px 24px rgba(0,0,0,.12);
        }
        div[data-testid="stFileUploader"] section {
          border-radius: 24px !important;
          border: 1px dashed rgba(0,113,227,.45) !important;
          background: rgba(255,255,255,.62) !important;
        }
        .review-note {
          border-left: 4px solid var(--apple-blue);
          padding: 12px 14px;
          background: rgba(0,113,227,.07);
          border-radius: 14px;
          color: #1d1d1f;
          margin: 12px 0 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(path: str, **params: Any) -> Any:
    response = requests.get(f"{API_BASE}{path}", params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def api_post_json(path: str, payload: dict[str, Any]) -> Any:
    response = requests.post(f"{API_BASE}{path}", json=payload, timeout=120)
    response.raise_for_status()
    return response.json()


def api_post_files(path: str, files: list, data: dict[str, Any]) -> Any:
    response = requests.post(f"{API_BASE}{path}", files=files, data=data, timeout=300)
    response.raise_for_status()
    return response.json()


def show_api_status() -> bool:
    try:
        api_get("/health")
        return True
    except Exception as exc:
        st.error(f"Backend API is not reachable at {API_BASE}. Start it with: uvicorn backend.main:app --reload")
        st.caption(str(exc))
        return False


@st.cache_data(ttl=15)
def get_jobs() -> list[dict[str, Any]]:
    return api_get("/jobs")


@st.cache_data(ttl=10)
def get_rankings(job_id: int) -> list[dict[str, Any]]:
    return api_get(f"/jobs/{job_id}/rankings")


def hero(title: str, subtitle: str) -> None:
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def metric_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-label">{label}</div>
          <div class="metric-value">{value}</div>
          <div class="small-muted">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def dataframe_from_rankings(rows: list[dict[str, Any]]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "parameter_scores" in df.columns:
        scores_df = pd.json_normalize(df["parameter_scores"]).add_prefix("score_")
        df = pd.concat([df.drop(columns=["parameter_scores"]), scores_df], axis=1)
    for col in ["matched_skills", "missing_skills", "strengths", "concerns", "interview_questions"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    return df


def create_job_page() -> None:
    hero(
        "Create a role rubric.",
        "Paste the Management Trainee job description. The system turns it into structured requirements and scoring signals.",
    )
    st.markdown(
        "<div class='review-note'>Use job-relevant criteria only. Do not include protected attributes or demographic preferences in the JD.</div>",
        unsafe_allow_html=True,
    )
    with st.form("create_job"):
        title = st.text_input("Role title", value="Management Trainee")
        jd = st.text_area(
            "Job description",
            height=320,
            placeholder="Paste responsibilities, eligibility, must-have skills, nice-to-have skills, and success traits...",
        )
        submitted = st.form_submit_button("Create role")
    if submitted:
        if len(jd.strip()) < 20:
            st.warning("Please paste a fuller job description.")
            return
        with st.spinner("Creating structured role rubric..."):
            try:
                job = api_post_json("/jobs", {"title": title, "job_description": jd})
                get_jobs.clear()
                st.success(f"Created role: {job['title']}")
                with st.expander("Structured rubric extracted from JD", expanded=True):
                    st.json(job["structured"])
            except Exception as exc:
                st.error("Could not create the job.")
                st.caption(str(exc))


def candidate_portal_page() -> None:
    hero(
        "Candidate CV upload.",
        "A clean application flow for candidates. CVs are parsed, stored, and evaluated for recruiter review.",
    )
    jobs = get_jobs()
    if not jobs:
        st.info("Create a job first from the 'Create Job' page.")
        return

    job_labels = {f"{job['title']} · ID {job['id']}": job for job in jobs}
    selected_label = st.selectbox("Apply for", list(job_labels.keys()))
    job = job_labels[selected_label]

    left, right = st.columns([1.05, 0.95], gap="large")
    with left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload CV", type=["pdf", "docx", "txt"], accept_multiple_files=False)
        consent = st.checkbox("I consent to my CV being stored and processed for this recruitment process.")
        submit = st.button("Submit application", disabled=uploaded is None or not consent)
        st.markdown("</div>", unsafe_allow_html=True)

        if submit and uploaded is not None:
            with st.spinner("Uploading and evaluating CV..."):
                try:
                    files = [("file", (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream"))]
                    result = api_post_files(f"/jobs/{job['id']}/candidates", files, {"consent": "true"})
                    get_rankings.clear()
                    st.success("Application submitted successfully.")
                    st.markdown(f"**Candidate:** {result['full_name']}")
                    if result.get("evaluation"):
                        st.markdown(f"**Review score:** {result['evaluation']['total_score']}/100")
                        st.caption("This score is for recruiter review only, not an automated hiring decision.")
                except Exception as exc:
                    st.error("Upload failed.")
                    st.caption(str(exc))

    with right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader(job["title"])
        st.write(job["job_description"][:1400] + ("..." if len(job["job_description"]) > 1400 else ""))
        st.markdown("</div>", unsafe_allow_html=True)


def dashboard_page() -> None:
    hero(
        "Talent intelligence dashboard.",
        "Upload 100+ CVs, compare candidates against the JD, and generate a shortlist report for human review.",
    )
    jobs = get_jobs()
    if not jobs:
        st.info("Create a job first from the 'Create Job' page.")
        return

    job_labels = {f"{job['title']} · ID {job['id']}": job for job in jobs}
    selected_label = st.selectbox("Select role", list(job_labels.keys()))
    job = job_labels[selected_label]

    with st.expander("Bulk upload CVs", expanded=False):
        uploaded_files = st.file_uploader(
            "Upload multiple PDFs/DOCX/TXT files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True,
        )
        consent = st.checkbox("I confirm the company has candidate permission to process these CVs.", key="bulk_consent")
        if st.button("Process uploaded CVs", disabled=not uploaded_files or not consent):
            with st.spinner("Processing resumes. This can call the LLM once per CV when OPENAI_API_KEY is configured..."):
                try:
                    files = [
                        ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                        for f in uploaded_files
                    ]
                    result = api_post_files(f"/jobs/{job['id']}/candidates/bulk", files, {"consent": "true"})
                    get_rankings.clear()
                    st.success(f"Processed {len(result)} CV(s).")
                except Exception as exc:
                    st.error("Bulk upload failed.")
                    st.caption(str(exc))

    rows = get_rankings(job["id"])
    df = dataframe_from_rankings(rows)

    total = len(df)
    avg = round(df["total_score"].mean(), 1) if total else 0
    recommended = int((df["total_score"] >= 70).sum()) if total else 0
    strong = int((df["total_score"] >= 85).sum()) if total else 0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    with c1:
        metric_card("Candidates", str(total), "CVs evaluated")
    with c2:
        metric_card("Average score", f"{avg}", "Out of 100")
    with c3:
        metric_card("Recommended", str(recommended), "Score >= 70")
    with c4:
        metric_card("Strong review", str(strong), "Score >= 85")

    if df.empty:
        st.info("No candidates evaluated yet. Upload CVs above.")
        return

    chart_col, side_col = st.columns([1.6, 1.0], gap="large")
    with chart_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        top_chart = df.sort_values("total_score", ascending=False).head(20)
        fig = px.bar(
            top_chart,
            x="total_score",
            y="full_name",
            orientation="h",
            title="Top candidates by total score",
            labels={"total_score": "Score", "full_name": "Candidate"},
            range_x=[0, 100],
        )
        fig.update_layout(
            height=max(420, 28 * len(top_chart)),
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=10, r=20, t=52, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.subheader("Report controls")
        threshold = st.slider("Shortlist threshold", 0, 100, 70, 1)
        top_n = st.slider("Max candidates in report", 1, 100, 30, 1)
        report_rows = df[df["total_score"] >= threshold].sort_values("total_score", ascending=False).head(top_n)
        st.metric("Candidates in report", len(report_rows))

        csv_response = requests.get(
            f"{API_BASE}/jobs/{job['id']}/report.csv",
            params={"min_score": threshold, "top_n": top_n},
            timeout=60,
        )
        html_response = requests.get(
            f"{API_BASE}/jobs/{job['id']}/report.html",
            params={"min_score": threshold, "top_n": top_n},
            timeout=60,
        )
        st.download_button(
            "Download CSV report",
            data=csv_response.text,
            file_name=f"candidate_report_{job['id']}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
        )
        st.download_button(
            "Download HTML report",
            data=html_response.text,
            file_name=f"candidate_report_{job['id']}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.subheader("Candidate ranking table")
    display_cols = [
        "candidate_id",
        "full_name",
        "email",
        "total_score",
        "recommendation",
        "semantic_similarity",
        "matched_skills",
        "missing_skills",
        "score_semantic_jd_fit",
        "score_skills_match",
        "score_education_fit",
        "score_experience_projects",
        "score_leadership_communication",
        "score_resume_completeness",
    ]
    existing_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(
        df[existing_cols].sort_values("total_score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Candidate deep-dive notes"):
        candidate_names = df.sort_values("total_score", ascending=False)["full_name"].tolist()
        selected_name = st.selectbox("Candidate", candidate_names)
        row = df[df["full_name"] == selected_name].iloc[0].to_dict()
        st.markdown(f"### {row.get('full_name')} · {row.get('total_score')}/100")
        st.markdown("**Strengths**")
        st.write(row.get("strengths", ""))
        st.markdown("**Concerns / missing evidence**")
        st.write(row.get("concerns", ""))
        st.markdown("**Suggested interview questions**")
        st.write(row.get("interview_questions", ""))


def main() -> None:
    inject_css()
    st.sidebar.title("MT Talent Intelligence")
    st.sidebar.caption("CV extraction · semantic scoring · recruiter dashboard")
    page = st.sidebar.radio("Navigate", ["Company Dashboard", "Candidate Portal", "Create Job"], index=0)
    st.sidebar.markdown("---")
    st.sidebar.caption("Human-in-the-loop screening system. Do not use as an automated final decision maker.")

    if not show_api_status():
        return

    if page == "Create Job":
        create_job_page()
    elif page == "Candidate Portal":
        candidate_portal_page()
    else:
        dashboard_page()


if __name__ == "__main__":
    main()
