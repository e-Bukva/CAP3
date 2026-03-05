#!/usr/bin/env python3
"""
Генерация HTML из документа через GPT.

Алгоритм:
1. Берёт Redact/proposal.md (или PDF из input/ в аварийном режиме)
2. Загружает в GPT
3. Сохраняет HTML и снимок MD в generated/sessions/{baseName}_{timestamp}/
"""

import os
import re
import shutil
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.gpt_prompts import HTML_TEMPLATE
from tools.file_utils import (
    PATHS,
    create_full_html_document,
    create_session_directory,
    create_session_timestamp,
    resolve_session_base_name,
)
from tools.gpt_client import generate_html_from_file, initialize_openai

load_dotenv()

_PREPOSITION_RE = re.compile(
    r'\b(в|и|с|к|у|о|а|но|не|на|из|по|за|от|до|со|во|об|при|для)\s+(\S+)',
    re.IGNORECASE,
)


def fix_prepositions(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for text_node in soup.find_all(string=True):
        if text_node.parent.name in ("style", "script"):
            continue
        new_html = _PREPOSITION_RE.sub(
            r'<span style="white-space:nowrap">\1 \2</span>',
            str(text_node),
        )
        if new_html != str(text_node):
            text_node.replace_with(BeautifulSoup(new_html, "html.parser"))
    return str(soup)


def main() -> None:
    import time

    print("\n🤖 Генерация HTML из документа\n")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "your-openai-api-key-here":
        print("✗ Ошибка: OPENAI_API_KEY не найден")
        print("\n📝 Создайте файл .env:")
        print("OPENAI_API_KEY=sk-ваш-ключ")
        print("OPENAI_MODEL=gpt-4o\n")
        sys.exit(1)

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
    initialize_openai(api_key, model)
    print(f"✓ API готов ({model})\n")

    print("📁 Поиск файла...")

    file_info = None

    redact_proposal = PATHS["redact"] / "proposal.md"
    if redact_proposal.exists():
        file_info = {"name": "proposal.md", "path": redact_proposal, "stats": redact_proposal.stat()}
        print("✓ Найден: Redact/proposal.md\n")

    if file_info is None:
        print("✗ Файл Redact/proposal.md не найден")
        print("  Запустите сначала: python tools/extract_markdown.py\n")

        pdf_files = [
            {"name": f.name, "path": f, "stats": f.stat()}
            for f in PATHS["input"].iterdir()
            if not f.name.startswith(".") and f.suffix.lower() == ".pdf"
        ]

        if not pdf_files:
            print("  Также не найден PDF в input/. Нечего обрабатывать.\n")
            sys.exit(0)

        file_info = pdf_files[0]
        print(f"⚠️  Аварийный режим: генерация напрямую из PDF ({file_info['name']})")
        print("   Рекомендуется использовать: python tools/extract_markdown.py → редактировать → python tools/generate_html.py\n")
        print("❓ Продолжить? (Ctrl+C для отмены)\n")
        time.sleep(3)

    size_kb = file_info["stats"].st_size // 1024
    print(f"✓ Обрабатываем: {file_info['name']} ({size_kb} KB)\n")

    print(f"🧠 Отправка в {model}...")

    try:
        result = generate_html_from_file(file_info["path"], model)

        html_size_kb = len(result["html"]) / 1024
        usage = result["usage"]
        print(f"✓ HTML получен ({html_size_kb:.1f} KB)")
        print(
            f"  Токены: {usage['prompt_tokens']} промпт + "
            f"{usage['completion_tokens']} ответ = {usage['total_tokens']}\n"
        )

        session_timestamp = create_session_timestamp()
        base_name = resolve_session_base_name()
        session_path = create_session_directory(session_timestamp, base_name)
        print(f"📁 Сессия: {base_name}_{session_timestamp}\n")

        full_html = create_full_html_document(result["html"], HTML_TEMPLATE)
        full_html = fix_prepositions(full_html)

        # Копируем print.css в папку сессии (нужен для рендера)
        src_css = PATHS["src"] / "print.css"
        if src_css.exists():
            shutil.copy2(src_css, session_path / "print.css")

        html_path = session_path / f"{base_name}.html"
        html_path.write_text(full_html, encoding="utf-8")
        print(f"💾 HTML: {html_path}\n")

        if file_info["path"].suffix.lower() == ".md":
            md_snapshot = session_path / f"{base_name}.md"
            shutil.copy2(file_info["path"], md_snapshot)
            print(f"💾 MD снимок: {md_snapshot}\n")

        print("✅ Готово! Теперь запустите:")
        print("   python tools/make_pdf.py\n")

    except Exception as e:
        print(f"✗ Ошибка: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
