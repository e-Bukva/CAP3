#!/usr/bin/env python3
"""
Извлечение чистого Markdown из PDF/DOCX документа.

Алгоритм:
1. Находит PDF или DOCX в input/
2. Отправляет в GPT для извлечения структурированного Markdown
3. Сохраняет proposal.md в Redact/ для редактирования в Obsidian
"""

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.file_utils import PATHS, ensure_dir
from tools.gpt_client import extract_markdown_from_pdf, extract_markdown_from_text, initialize_openai

load_dotenv()


def main() -> None:
    import os

    print("\n📄 Извлечение Markdown из документа\n")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "your-openai-api-key-here":
        print("✗ Ошибка: OPENAI_API_KEY не найден")
        print("\n📝 Создайте файл .env:")
        print("OPENAI_API_KEY=sk-ваш-ключ")
        print("OPENAI_MODEL=gpt-4.1\n")
        sys.exit(1)

    model = os.environ.get("OPENAI_MODEL", "gpt-4.1")
    initialize_openai(api_key, model)
    print(f"✓ API готов ({model})\n")

    print("📁 Поиск документа в input/...")
    supported_exts = {".pdf", ".docx", ".doc"}
    input_files = [
        f for f in PATHS["input"].iterdir()
        if not f.name.startswith(".") and f.suffix.lower() in supported_exts
    ]

    if not input_files:
        print("✗ Документы не найдены")
        print("  Положите PDF или Word файл в папку input/\n")
        sys.exit(0)

    source_file = input_files[0]
    print(f"✓ Найден: {source_file.name}\n")

    ensure_dir(PATHS["redact"])
    proposal_path = PATHS["redact"] / "proposal.md"

    if proposal_path.exists():
        import time
        print("⚠️  Файл Redact/proposal.md уже существует!")
        print("   Он будет перезаписан. Создаём резервную копию...\n")
        backup_path = PATHS["redact"] / f"proposal.backup.{int(time.time())}.md"
        backup_path.write_text(proposal_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"✓ Резервная копия: {backup_path.name}\n")

    try:
        if source_file.suffix.lower() == ".pdf":
            result = extract_markdown_from_pdf(source_file, model)
        else:
            result = extract_markdown_from_text(source_file, model)

        size_kb = len(result["markdown"]) / 1024
        usage = result["usage"]
        print(f"✓ Markdown извлечён ({size_kb:.1f} KB)")
        print(
            f"  Токены: {usage['prompt_tokens']} промпт + "
            f"{usage['completion_tokens']} ответ = {usage['total_tokens']}\n"
        )

        proposal_path.write_text(result["markdown"], encoding="utf-8")
        print(f"💾 Сохранено: {proposal_path}\n")

        source_meta_path = PATHS["input"] / "source.json"
        existing_meta = {}
        if source_meta_path.exists():
            try:
                existing_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        source_meta = {
            "sourceFile": source_file.name,
            "name": existing_meta.get("name") or source_file.stem,
        }
        source_meta_path.write_text(json.dumps(source_meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"💾 Метаданные источника: {source_meta_path}\n")

        print("✅ Готово! Теперь можно:")
        print("   1. Открыть и отредактировать Redact/proposal.md в Obsidian")
        print("   2. Запустить: python tools/generate_html.py")
        print("   3. Запустить: python tools/make_pdf.py\n")

    except Exception as e:
        print(f"✗ Ошибка: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
