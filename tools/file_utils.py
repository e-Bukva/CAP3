"""Утилиты для работы с файловой системой и версионированием."""

import json
import shutil
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


def initialize_directories() -> list[str]:
    created = []
    for name, path in PATHS.items():
        if ensure_dir(path):
            created.append(name)
    return created


def scan_input_folder() -> list[dict]:
    input_dir = PATHS["input"]
    if not input_dir.exists():
        return []

    supported = {".docx", ".pdf", ".md", ".markdown"}
    files = []
    for f in input_dir.iterdir():
        if f.name.startswith("."):
            continue
        if f.suffix.lower() in supported:
            files.append({"name": f.name, "path": f, "stats": f.stat()})
    return files


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
    if meta and meta.get("baseName"):
        return meta["baseName"]

    input_dir = PATHS["input"]
    if input_dir.exists():
        for f in input_dir.iterdir():
            if not f.name.startswith(".") and f.suffix.lower() == ".pdf":
                return f.stem

    return "proposal"


def create_session_directory(timestamp: str, base_name: str) -> Path:
    folder_name = f"{base_name}_{timestamp}" if base_name else timestamp
    session_path = PATHS["sessions"] / folder_name
    ensure_dir(session_path)
    return session_path


def copy_source_to_session(source_path: Path, session_path: Path) -> Path:
    dest = session_path / f"source_{source_path.name}"
    shutil.copy2(source_path, dest)
    return dest


def save_html_version(session_path: Path, version: str | int, content: str) -> Path:
    file_name = "proposal_final.html" if version == "final" else f"proposal_v{version}.html"
    file_path = session_path / file_name
    file_path.write_text(content, encoding="utf-8")
    return file_path


def read_html_version(session_path: Path, version: str | int) -> str | None:
    file_name = "proposal_final.html" if version == "final" else f"proposal_v{version}.html"
    file_path = session_path / file_name
    if not file_path.exists():
        return None
    return file_path.read_text(encoding="utf-8")


def get_session_versions(session_path: Path) -> list[str]:
    if not session_path.exists():
        return []
    files = sorted(
        f.name for f in session_path.iterdir()
        if f.name.startswith("proposal_v") or f.name == "proposal_final.html"
    )
    return files


def get_next_version_number(session_path: Path) -> int:
    import re
    versions = get_session_versions(session_path)
    numbers = []
    for v in versions:
        m = re.match(r"proposal_v(\d+)\.html", v)
        if m:
            numbers.append(int(m.group(1)))
    return max(numbers) + 1 if numbers else 1


def create_full_html_document(body_content: str, template: dict) -> str:
    return (
        f"{template['doctype']}\n"
        f"<html lang=\"en\">\n"
        f"{template['head']}\n"
        f"{template['body_start']}\n\n"
        f"{body_content}\n\n"
        f"{template['body_end']}"
    )


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def get_session_info(session_path: Path) -> dict | None:
    if not session_path.exists():
        return None
    versions = get_session_versions(session_path)
    source_files = [f.name for f in session_path.iterdir() if f.name.startswith("source_")]
    return {
        "timestamp": session_path.name,
        "path": session_path,
        "versions": len(versions),
        "source_file": source_files[0] if source_files else None,
    }
