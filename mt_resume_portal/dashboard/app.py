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

        /* ===== MAIN THEME ===== */
        :root {
            --bg: #f5f7ff;
            --card: #ffffff;
            --navy: #111827;
            --purple: #6d5dfc;
            --blue: #3b82f6;
            --cyan: #06b6d4;
            --pink: #ec4899;
            --green: #10b981;
            --orange: #f59e0b;
            --muted: #64748b;
            --border: #e5e7eb;
        }

        /* ===== PAGE ===== */
        .stApp {
            background:
                radial-gradient(circle at 10% 0%, rgba(109,93,252,0.12), transparent 30%),
                radial-gradient(circle at 90% 10%, rgba(6,182,212,0.10), transparent 28%),
                var(--bg);
            color: var(--navy);
        }

        .block-container {
            max-width: 1400px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* ===== SIDEBAR ===== */
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #1e1b4b 100%);
            border-right: none;
        }

        section[data-testid="stSidebar"] * {
            color: white !important;
        }

        section[data-testid="stSidebar"] .stButton button {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 12px;
        }

        section[data-testid="stSidebar"] .stButton button:hover {
            background: rgba(255,255,255,0.16);
            border-color: rgba(255,255,255,0.3);
        }

        /* ===== HEADINGS ===== */
        h1 {
            font-size: 2.5rem !important;
            font-weight: 800 !important;
            letter-spacing: -1px;
            color: #111827 !important;
        }

        h2 {
            font-weight: 750 !important;
            color: #111827 !important;
        }

        h3 {
            font-weight: 700 !important;
            color: #1f2937 !important;
        }

        /* ===== METRIC CARDS ===== */
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.9);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 30px rgba(15,23,42,0.06);
            transition: all 0.2s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            box-shadow: 0 14px 35px rgba(109,93,252,0.14);
        }

        div[data-testid="stMetricLabel"] {
            color: var(--muted) !important;
            font-weight: 600;
        }

        div[data-testid="stMetricValue"] {
            color: #111827 !important;
            font-weight: 800;
        }

        /* ===== BUTTONS ===== */
        .stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.65rem 1.2rem !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

        /* ===== INPUTS ===== */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"],
        .stNumberInput input {
            border-radius: 12px !important;
            border: 1px solid #dbe1ea !important;
            background: white !important;
        }

        /* ===== UPLOAD BOX ===== */
        section[data-testid="stFileUploader"] {
            background: linear-gradient(
                135deg,
                rgba(109,93,252,0.06),
                rgba(59,130,246,0.06)
            );
            border: 2px dashed rgba(109,93,252,0.35);
            border-radius: 18px;
            padding: 12px;
        }

        /* ===== ALERTS ===== */
        div[data-testid="stAlert"] {
            border-radius: 14px;
            border: none;
        }

        /* ===== DATAFRAME ===== */
        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: 0 6px 20px rgba(15,23,42,0.05);
        }

        /* ===== TABS ===== */
        button[data-baseweb="tab"] {
            font-weight: 700;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--purple) !important;
        }

        /* ===== CUSTOM HERO ===== */
        .hero {
            background: linear-gradient(
                135deg,
                #111827 0%,
                #312e81 55%,
                #4f46e5 100%
            );
            border-radius: 24px;
            padding: 32px 36px;
            margin-bottom: 26px;
            color: white;
            box-shadow: 0 18px 45px rgba(49,46,129,0.25);
        }

        .hero h1 {
            color: white !important;
            margin-bottom: 8px;
        }

        .hero p {
            color: rgba(255,255,255,0.78);
            font-size: 1.05rem;
            margin-bottom: 0;
        }

        /* ===== SECTION CARD ===== */
        .section-card {
            background: rgba(255,255,255,0.92);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 24px;
            margin: 14px 0;
            box-shadow: 0 8px 28px rgba(15,23,42,0.05);
        }

        /* ===== SCORE BADGES ===== */
        .score-high {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            background: rgba(16,185,129,0.12);
            color: #047857;
            font-weight: 800;
        }

        .score-medium {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            background: rgba(245,158,11,0.14);
            color: #b45309;
            font-weight: 800;
        }

        .score-low {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            background: rgba(239,68,68,0.12);
            color: #b91c1c;
            font-weight: 800;
        }

        /* ===== FOOTER ===== */
        .footer {
            text-align: center;
            color: #94a3b8;
            font-size: 0.85rem;
            padding: 30px 0 10px;
        }
/* ===== FORCE DARK MODE ===== */

.stApp {
    background: #0b1020 !important;
    color: #f8fafc !important;
}

/* Main content */
.block-container {
    background: transparent !important;
}

/* All normal text */
.stApp p,
.stApp span,
.stApp label,
.stApp div {
    color: #f8fafc;
}

/* Headings */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4,
.stApp h5,
.stApp h6 {
    color: #ffffff !important;
}

/* ===== TEXT INPUTS ===== */

.stTextInput input,
.stTextArea textarea,
.stNumberInput input {
    background-color: #151b2e !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border: 1px solid #374151 !important;
    border-radius: 12px !important;
    caret-color: #ffffff !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder,
.stNumberInput input::placeholder {
    color: #94a3b8 !important;
    opacity: 1 !important;
}

/* Text while typing */
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    background-color: #1b2338 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    border-color: #7c6cff !important;
    box-shadow: 0 0 0 1px #7c6cff !important;
}

/* ===== SELECT BOX / DROPDOWNS ===== */

.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background-color: #151b2e !important;
    color: #ffffff !important;
    border-color: #374151 !important;
}

.stSelectbox [data-baseweb="select"] *,
.stMultiSelect [data-baseweb="select"] * {
    color: #ffffff !important;
}

/* Dropdown menu */
div[data-baseweb="popover"],
div[data-baseweb="menu"] {
    background-color: #151b2e !important;
}

div[data-baseweb="menu"] li {
    background-color: #151b2e !important;
    color: #ffffff !important;
}

div[data-baseweb="menu"] li:hover {
    background-color: #252d46 !important;
}

/* ===== FILE UPLOADER ===== */

section[data-testid="stFileUploader"] {
    background: #11182b !important;
    border: 2px dashed #5865d8 !important;
    border-radius: 16px !important;
}

section[data-testid="stFileUploader"] * {
    color: #ffffff !important;
}

/* ===== BUTTONS ===== */

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #2563eb) !important;
    color: #ffffff !important;
    border: none !important;
}

.stButton > button p,
.stButton > button span {
    color: #ffffff !important;
}

/* ===== METRIC CARDS ===== */

div[data-testid="stMetric"] {
    background: #151b2e !important;
    border: 1px solid #29324a !important;
}

div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
}

div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #ffffff !important;
}

/* ===== DATAFRAMES / TABLES ===== */

div[data-testid="stDataFrame"] {
    background: #111827 !important;
    border: 1px solid #29324a !important;
}

/* ===== TABS ===== */

button[data-baseweb="tab"] {
    color: #94a3b8 !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #a78bfa !important;
}

/* ===== EXPANDERS ===== */

div[data-testid="stExpander"] {
    background: #11182b !important;
    border: 1px solid #29324a !important;
    border-radius: 14px !important;
}

div[data-testid="stExpander"] * {
    color: #f8fafc !important;
}

/* ===== CHECKBOXES ===== */

.stCheckbox label,
.stCheckbox label span {
    color: #ffffff !important;
}

/* ===== RADIO BUTTONS ===== */

.stRadio label,
.stRadio label span {
    color: #ffffff !important;
}

/* ===== SLIDERS ===== */

.stSlider label {
    color: #ffffff !important;
}

/* ===== ALERTS ===== */

div[data-testid="stAlert"] {
    background: #151b2e !important;
    color: #ffffff !important;
}

/* ===== CODE / JSON ===== */

.stCodeBlock,
code {
    background: #080d18 !important;
    color: #e2e8f0 !important;
}

/* ===== SIDEBAR ===== */

section[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #080c18 0%,
        #111633 100%
    ) !important;
}

section[data-testid="stSidebar"] * {
    color: #ffffff !important;
}

/* Sidebar inputs */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    background: #151b2e !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
}

/* ===== DIVIDERS ===== */

hr {
    border-color: #29324a !important;
}
        /* Fix disabled buttons in dark mode */
.stButton > button:disabled {
    background: #6366f1 !important;
    color: #ffffff !important;
    -webkit-text-fill-color: #ffffff !important;
    opacity: 1 !important;
    border: none !important;
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

def welcome_page() -> None:
    st.markdown("## ✦ AI RECRUITMENT PLATFORM")

    st.title("MT Talent Intelligence")

    st.subheader(
        "AI-powered recruitment & candidate–job matching"
    )

    st.write("")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### ✦ AI-Powered Screening")
        st.write(
            "Extract structured information from resumes "
            "and job descriptions."
        )

    with col2:
        st.markdown("### ◎ Intelligent Matching")
        st.write(
            "Compare candidate profiles with role requirements "
            "using automated scoring."
        )

    with col3:
        st.markdown("### ▦ Recruiter Dashboard")
        st.write(
            "Review rankings, candidate insights, reports, "
            "and recruitment metrics."
        )

    st.write("")
    st.write("")

    _, button_col, _ = st.columns([1, 2, 1])

    with button_col:
        if st.button(
            "Enter Demo Workspace →",
            use_container_width=True
        ):
            st.session_state.entered_workspace = True
            st.rerun()

    st.caption(
        "Human-in-the-loop recruitment system · "
        "For demonstration purposes"
    )
def main() -> None:
    inject_css()
    if "entered_workspace" not in st.session_state:
        st.session_state.entered_workspace = False

    if not st.session_state.entered_workspace:
        welcome_page()
        return
        
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
