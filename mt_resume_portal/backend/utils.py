from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def safe_json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    stem = Path(filename).stem
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "resume"
    return f"{stem[:110]}{suffix}"


def compact_list(values: list[Any], max_items: int = 30) -> list[Any]:
    out: list[Any] = []
    seen = set()
    for item in values or []:
        text = str(item).strip()
        key = text.lower()
        if text and key not in seen:
            out.append(text)
            seen.add(key)
        if len(out) >= max_items:
            break
    return out
