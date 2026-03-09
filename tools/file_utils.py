"""Утилиты для работы с файловой системой и версионированием."""

import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

PATHS = {
    "input": PROJECT_ROOT / "input",
    "redact": PROJECT_ROOT / "Redact",
    "generated": PROJECT_ROOT / "generated",
    "sessions": PROJECT_ROOT / "generated" / "sessions",
    "src": PROJECT_ROOT / "src",
}


def ensure_dir(path: Path) -> bool:
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        return True
    return False



def create_session_timestamp() -> str:
    now = datetime.now()
    return now.strftime("%Y%m%d_%H%M%S")


def read_source_metadata() -> dict | None:
    meta_path = PATHS["input"] / "source.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def resolve_session_base_name() -> str:
    meta = read_source_metadata()
    if meta:
        return meta.get("name") or meta.get("baseName") or "proposal"
    return "proposal"


def create_session_directory(timestamp: str, base_name: str) -> Path:
    folder_name = f"{base_name}_{timestamp}" if base_name else timestamp
    session_path = PATHS["sessions"] / folder_name
    ensure_dir(session_path)
    return session_path



def create_full_html_document(body_content: str, template: dict) -> str:
    return (
        f"{template['doctype']}\n"
        f"<html lang=\"en\">\n"
        f"{template['head']}\n"
        f"{template['body_start']}\n\n"
        f"{body_content}\n\n"
        f"{template['body_end']}"
    )


def strip_markdown_wrapper(text: str) -> str:
    """Удалить markdown code fence обёртку (```markdown, ```html, ```) если GPT её добавил.

    Поддерживает CRLF и любые пробельные символы после закрывающего fence.
    """
    text = re.sub(r"^```(?:markdown|html|)\r?\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text.strip()


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


