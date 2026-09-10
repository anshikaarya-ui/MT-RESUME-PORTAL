from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_UPLOAD_DIR = DATA_DIR / "uploads"
DEFAULT_EXPORT_DIR = DATA_DIR / "exports"

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'resume_portal.db'}")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(DEFAULT_UPLOAD_DIR)))
EXPORT_DIR = Path(os.getenv("EXPORT_DIR", str(DEFAULT_EXPORT_DIR)))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

MAX_LLM_CHARS = int(os.getenv("MAX_LLM_CHARS", "18000"))
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "12"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
