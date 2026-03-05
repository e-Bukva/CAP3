"""Клиент для работы с OpenAI API."""

import sys
from pathlib import Path

import requests
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.gpt_prompts import SYSTEM_PROMPT, get_initial_prompt, get_correction_prompt
from tools.file_utils import strip_markdown_wrapper

_client: OpenAI | None = None
_api_key: str | None = None


def initialize_openai(api_key: str, model: str = "gpt-5") -> dict:
    global _client, _api_key
    if not api_key:
        raise ValueError("OpenAI API ключ не предоставлен")
    _client = OpenAI(api_key=api_key)
    _api_key = api_key
    return {"client": _client, "model": model}


def validate_api_key(api_key: str) -> bool:
    try:
        test_client = OpenAI(api_key=api_key)
        test_client.models.list()
        return True
    except Exception:
        return False


def _upload_file(file_path: Path) -> str:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован")
    print(f"  📤 Загрузка файла: {file_path.name}...")
    with open(file_path, "rb") as f:
        file_obj = _client.files.create(file=f, purpose="user_data")
    print(f"  ✓ Файл загружен: {file_obj.id}")
    return file_obj.id


def _call_responses_api(payload: dict) -> dict:
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key}",
        },
        json=payload,
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")
    return response.json()


def _extract_text_from_response(data: dict) -> tuple[str, dict]:
    if data.get("status") == "incomplete":
        reason = data.get("incomplete_details", {}).get("reason", "unknown")
        raise RuntimeError(f"Ответ неполный: {reason}")

    message_output = next((item for item in data["output"] if item["type"] == "message"), None)
    if not message_output or not message_output.get("content"):
        raise RuntimeError(f"Не найден message в output: {data['output']}")

    text_content = next(
        (item for item in message_output["content"] if item["type"] == "output_text"), None
    )
    if not text_content:
        raise RuntimeError("Не найден output_text в content")

    text = text_content["text"].strip()
    usage = {
        "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
        "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
        "total_tokens": data.get("usage", {}).get("total_tokens", 0),
    }
    return text, usage




def generate_html_from_file(file_path: Path, model: str = "gpt-5") -> dict:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован. Вызовите initialize_openai() сначала.")

    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return _generate_from_pdf(file_path, model)
    else:
        content = file_path.read_text(encoding="utf-8")
        print(f"  📄 Чтение файла: {file_path.name}...")
        return _generate_from_text(content, model)


def _generate_from_pdf(file_path: Path, model: str) -> dict:
    file_id = _upload_file(file_path)

    data = _call_responses_api({
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            "Преобразуй содержимое этого документа в HTML по шаблону из system prompt. "
                            "КРИТИЧЕСКИ ВАЖНО: игнорируй колонтитулы, номера страниц и повторяющиеся элементы оформления."
                        ),
                    },
                    {"type": "input_file", "file_id": file_id},
                ],
            },
        ],
        "max_output_tokens": 16000,
    })

    html, usage = _extract_text_from_response(data)
    return {
        "html": strip_markdown_wrapper(html),
        "usage": usage,
        "model": data.get("model"),
        "file_id": file_id,
    }


def _generate_from_text(text_content: str, model: str) -> dict:
    data = _call_responses_api({
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            SYSTEM_PROMPT
                            + "\n\nПреобразуй следующий текст в HTML по шаблону. "
                            "КРИТИЧЕСКИ ВАЖНО: игнорируй колонтитулы, номера страниц и повторяющиеся элементы оформления.\n\n"
                            + text_content
                        ),
                    }
                ],
            }
        ],
        "max_output_tokens": 16000,
    })

    html, usage = _extract_text_from_response(data)
    return {
        "html": strip_markdown_wrapper(html),
        "usage": usage,
        "model": data.get("model"),
    }


def generate_html_from_text(extracted_text: str, model: str = "gpt-5") -> dict:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован. Вызовите initialize_openai() сначала.")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": get_initial_prompt(extracted_text)},
            ],
            "max_completion_tokens": 4000,
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")

    data = response.json()
    html = data["choices"][0]["message"]["content"].strip()
    return {
        "html": strip_markdown_wrapper(html),
        "usage": data.get("usage"),
        "model": data.get("model"),
    }


def apply_corrections(current_html: str, user_correction: str, model: str = "gpt-5") -> dict:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован. Вызовите initialize_openai() сначала.")

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {_api_key}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": get_correction_prompt(current_html, user_correction)},
            ],
            "max_completion_tokens": 4000,
        },
        timeout=120,
    )
    if not response.ok:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")

    data = response.json()
    html = data["choices"][0]["message"]["content"].strip()
    return {
        "html": strip_markdown_wrapper(html),
        "usage": data.get("usage"),
        "model": data.get("model"),
    }


def analyze_html_structure(html: str) -> dict:
    import re as _re

    sections = []
    for m in _re.finditer(r'<section[^>]*id="([^"]*)"[^>]*>[\s\S]*?<h2[^>]*>(.*?)</h2>', html):
        title = _re.sub(r"<[^>]*>", "", m.group(2)).strip()
        sections.append({"id": m.group(1), "title": title})

    if not sections:
        for m in _re.finditer(r"<h2[^>]*>(.*?)</h2>", html):
            title = _re.sub(r"<[^>]*>", "", m.group(1)).strip()
            sections.append({"title": title})

    return {
        "sections": sections,
        "table_count": len(_re.findall(r"<table", html)),
        "list_count": len(_re.findall(r"<ul", html)),
        "character_count": len(html),
        "has_content": bool(sections) or "<p" in html,
    }


def validate_html(html: str) -> dict:
    import re as _re

    errors, warnings = [], []

    if not html or not html.strip():
        errors.append("HTML пустой")
        return {"valid": False, "errors": errors, "warnings": warnings}

    open_tags = len(_re.findall(r"<section", html))
    close_tags = len(_re.findall(r"</section>", html))
    if open_tags != close_tags:
        warnings.append(f"Несоответствие тегов <section>: открыто {open_tags}, закрыто {close_tags}")

    if not ("<h2" in html or "<h3" in html):
        warnings.append("HTML не содержит заголовков")

    if "```html" in html or "```" in html:
        errors.append("HTML содержит markdown обёртки — требуется очистка")

    return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


def format_token_usage(usage: dict | None) -> str:
    if not usage:
        return "N/A"
    return (
        f"Промпт: {usage.get('prompt_tokens', 0)}, "
        f"Ответ: {usage.get('completion_tokens', 0)}, "
        f"Всего: {usage.get('total_tokens', 0)}"
    )
