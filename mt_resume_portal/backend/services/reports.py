from __future__ import annotations

import csv
import html
from io import StringIO
from typing import Any


def rankings_to_csv(rows: list[dict[str, Any]]) -> str:
    output = StringIO()
    fieldnames = [
        "candidate_id",
        "full_name",
        "email",
        "phone",
        "total_score",
        "recommendation",
        "semantic_similarity",
        "matched_skills",
        "missing_skills",
        "strengths",
        "concerns",
        "interview_questions",
        "uploaded_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                "candidate_id": row.get("candidate_id"),
                "full_name": row.get("full_name"),
                "email": row.get("email"),
                "phone": row.get("phone"),
                "total_score": row.get("total_score"),
                "recommendation": row.get("recommendation"),
                "semantic_similarity": row.get("semantic_similarity"),
                "matched_skills": "; ".join(row.get("matched_skills", [])),
                "missing_skills": "; ".join(row.get("missing_skills", [])),
                "strengths": "; ".join(row.get("strengths", [])),
                "concerns": "; ".join(row.get("concerns", [])),
                "interview_questions": "; ".join(row.get("interview_questions", [])),
                "uploaded_at": row.get("uploaded_at"),
            }
        )
    return output.getvalue()


def rankings_to_html(job_title: str, threshold: float, rows: list[dict[str, Any]]) -> str:
    cards = []
    for idx, row in enumerate(rows, start=1):
        cards.append(
            f"""
            <section class="candidate-card">
              <div class="rank">#{idx}</div>
              <div class="content">
                <h2>{html.escape(str(row.get('full_name', 'Unknown')))}</h2>
                <p class="muted">{html.escape(str(row.get('email', '')))} {html.escape(str(row.get('phone', '')))}</p>
                <div class="score">{row.get('total_score', 0):.1f}<span>/100</span></div>
                <p><strong>Recommendation:</strong> {html.escape(str(row.get('recommendation', '')))}</p>
                <p><strong>Matched skills:</strong> {html.escape(', '.join(row.get('matched_skills', [])[:12]))}</p>
                <p><strong>Missing or unclear:</strong> {html.escape(', '.join(row.get('missing_skills', [])[:12]))}</p>
                <p><strong>Strengths:</strong> {html.escape('; '.join(row.get('strengths', [])))}</p>
                <p><strong>Concerns:</strong> {html.escape('; '.join(row.get('concerns', [])))}</p>
              </div>
            </section>
            """
        )

    return f"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Candidate Review Report - {html.escape(job_title)}</title>
<style>
:root {{ --bg:#f5f5f7; --card:#ffffff; --text:#1d1d1f; --muted:#6e6e73; --line:#d2d2d7; --accent:#0071e3; }}
body {{ margin:0; font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","Segoe UI",sans-serif; background:var(--bg); color:var(--text); }}
.hero {{ padding:56px 7vw 32px; background:linear-gradient(135deg,#fff,#edf4ff); border-bottom:1px solid var(--line); }}
h1 {{ font-size:42px; margin:0 0 12px; letter-spacing:-.04em; }}
.meta {{ color:var(--muted); font-size:16px; }}
.wrap {{ padding:28px 7vw 56px; }}
.candidate-card {{ display:grid; grid-template-columns:72px 1fr; gap:20px; background:rgba(255,255,255,.86); backdrop-filter:blur(20px); border:1px solid rgba(210,210,215,.9); border-radius:28px; padding:24px; margin:18px 0; box-shadow:0 20px 45px rgba(0,0,0,.06); }}
.rank {{ width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; background:#111; color:#fff; font-weight:700; }}
h2 {{ margin:0; font-size:26px; letter-spacing:-.03em; }}
.muted {{ color:var(--muted); }}
.score {{ float:right; margin-top:-48px; font-size:36px; font-weight:800; letter-spacing:-.05em; color:var(--accent); }}
.score span {{ font-size:16px; color:var(--muted); }}
p {{ line-height:1.48; }}
.footer {{ color:var(--muted); font-size:13px; margin-top:36px; }}
</style>
</head>
<body>
  <header class="hero">
    <h1>Candidate Review Report</h1>
    <div class="meta">Role: {html.escape(job_title)} | Threshold: {threshold:.1f}/100 | Candidates in report: {len(rows)}</div>
  </header>
  <main class="wrap">
    {''.join(cards) if cards else '<p>No candidates met this threshold.</p>'}
    <div class="footer">This report supports human review. It should not be used as the sole basis for hiring decisions.</div>
  </main>
</body>
</html>
"""
