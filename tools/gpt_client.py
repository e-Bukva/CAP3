"""Клиент для работы с OpenAI API."""

import sys
from pathlib import Path

import requests
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.gpt_prompts import EXTRACT_MARKDOWN_PROMPT, SYSTEM_PROMPT, get_extract_markdown_prompt
from tools.file_utils import strip_markdown_wrapper

_client: OpenAI | None = None
_api_key: str | None = None


def initialize_openai(api_key: str, model: str = "gpt-4.1") -> dict:
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




def extract_markdown_from_pdf(file_path: Path, model: str) -> dict:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован. Вызовите initialize_openai() сначала.")

    file_id = _upload_file(file_path)
    print(f"  🧠 Извлечение Markdown через {model}...")

    data = _call_responses_api({
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
                    {"type": "input_file", "file_id": file_id},
                ],
            },
        ],
        "max_output_tokens": 16000,
    })

    markdown, usage = _extract_text_from_response(data)
    return {
        "markdown": strip_markdown_wrapper(markdown),
        "usage": usage,
        "model": data.get("model"),
        "file_id": file_id,
    }


def extract_markdown_from_text(file_path: Path, model: str) -> dict:
    if _client is None:
        raise RuntimeError("OpenAI клиент не инициализирован. Вызовите initialize_openai() сначала.")

    content = file_path.read_text(encoding="utf-8")
    print(f"  📄 Чтение файла: {file_path.name}...")
    print(f"  🧠 Извлечение Markdown через {model}...")

    data = _call_responses_api({
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
    })

    markdown, usage = _extract_text_from_response(data)
    return {
        "markdown": strip_markdown_wrapper(markdown),
        "usage": usage,
        "model": data.get("model"),
    }


def generate_html_from_file(file_path: Path, model: str = "gpt-4.1") -> dict:
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


