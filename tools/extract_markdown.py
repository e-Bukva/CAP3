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

import requests
from dotenv import load_dotenv
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.gpt_prompts import EXTRACT_MARKDOWN_PROMPT, get_extract_markdown_prompt
from tools.file_utils import PATHS, ensure_dir

load_dotenv()


def extract_markdown_from_pdf(pdf_path: Path, api_key: str, model: str) -> dict:
    print("  📤 Загрузка PDF в OpenAI...")

    client = OpenAI(api_key=api_key)
    with open(pdf_path, "rb") as f:
        file_obj = client.files.create(file=f, purpose="user_data")

    print(f"  ✓ Файл загружен: {file_obj.id}")
    print(f"  🧠 Извлечение Markdown через {model}...")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": EXTRACT_MARKDOWN_PROMPT}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": get_extract_markdown_prompt()},
                        {"type": "input_file", "file_id": file_obj.id},
                    ],
                },
            ],
            "max_output_tokens": 16000,
        },
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")

    data = response.json()

    if data.get("status") == "incomplete":
        reason = data.get("incomplete_details", {}).get("reason", "unknown")
        raise RuntimeError(f"Ответ неполный: {reason}")

    message_output = next((item for item in data["output"] if item["type"] == "message"), None)
    if not message_output or not message_output.get("content"):
        raise RuntimeError("Не найден message в output")

    text_content = next(
        (item for item in message_output["content"] if item["type"] == "output_text"), None
    )
    if not text_content:
        raise RuntimeError("Не найден output_text в content")

    markdown = text_content["text"].strip()
    if markdown.startswith("```markdown"):
        markdown = markdown[len("```markdown\n"):].rstrip("`").rstrip()
    elif markdown.startswith("```"):
        markdown = markdown[4:].rstrip("`").rstrip()

    return {
        "markdown": markdown,
        "usage": {
            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            "total_tokens": data.get("usage", {}).get("total_tokens", 0),
        },
        "model": data.get("model"),
        "file_id": file_obj.id,
    }


def extract_markdown_from_text(file_path: Path, api_key: str, model: str) -> dict:
    content = file_path.read_text(encoding="utf-8")
    print(f"  📄 Чтение файла: {file_path.name}...")
    print(f"  🧠 Извлечение Markdown через {model}...")

    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                EXTRACT_MARKDOWN_PROMPT
                                + "\n\n"
                                + get_extract_markdown_prompt()
                                + "\n\n"
                                + content
                            ),
                        }
                    ],
                }
            ],
            "max_output_tokens": 16000,
        },
        timeout=120,
    )

    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")

    data = response.json()

    if data.get("status") == "incomplete":
        reason = data.get("incomplete_details", {}).get("reason", "unknown")
        raise RuntimeError(f"Ответ неполный: {reason}")

    message_output = next((item for item in data["output"] if item["type"] == "message"), None)
    if not message_output or not message_output.get("content"):
        raise RuntimeError("Не найден message в output")

    output_text = next(
        (item for item in message_output["content"] if item["type"] == "output_text"), None
    )
    if not output_text:
        raise RuntimeError("Не найден output_text")

    markdown = output_text["text"].strip()
    if markdown.startswith("```markdown"):
        markdown = markdown[len("```markdown\n"):].rstrip("`").rstrip()
    elif markdown.startswith("```"):
        markdown = markdown[4:].rstrip("`").rstrip()

    return {
        "markdown": markdown,
        "usage": {
            "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            "total_tokens": data.get("usage", {}).get("total_tokens", 0),
        },
        "model": data.get("model"),
    }


def main() -> None:
    import os

    print("\n📄 Извлечение Markdown из документа\n")

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or api_key == "your-openai-api-key-here":
        print("✗ Ошибка: OPENAI_API_KEY не найден")
        print("\n📝 Создайте файл .env:")
        print("OPENAI_API_KEY=sk-ваш-ключ")
        print("OPENAI_MODEL=gpt-4o\n")
        sys.exit(1)

    model = os.environ.get("OPENAI_MODEL", "gpt-5")
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
            result = extract_markdown_from_pdf(source_file, api_key, model)
        else:
            result = extract_markdown_from_text(source_file, api_key, model)

        size_kb = len(result["markdown"]) / 1024
        usage = result["usage"]
        print(f"✓ Markdown извлечён ({size_kb:.1f} KB)")
        print(
            f"  Токены: {usage['prompt_tokens']} промпт + "
            f"{usage['completion_tokens']} ответ = {usage['total_tokens']}\n"
        )

        proposal_path.write_text(result["markdown"], encoding="utf-8")
        print(f"💾 Сохранено: {proposal_path}\n")

        source_meta = {"sourceFile": source_file.name, "baseName": source_file.stem}
        source_meta_path = PATHS["input"] / "source.json"
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
