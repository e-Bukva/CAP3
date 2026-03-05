# HTML-to-PDF Generator (Python)

Генератор PDF коммерческих предложений из HTML с использованием GPT и Playwright.

## Пайплайн

```
PDF/DOCX → [extract] → Redact/proposal.md → [редактировать] → [generate] → HTML → [pdf] → PDF
```

## Быстрый старт

### 1. Установить зависимости

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Создать файл `.env`

```bash
cp .env.example .env
# Вставьте ваш OPENAI_API_KEY в .env
```

### 3. Положить документ в `input/`

Поддерживаются `.pdf`, `.docx`, `.doc`.

### 4. Запустить пайплайн

```bash
# Шаг 1: извлечь Markdown из PDF/DOCX
python tools/extract_markdown.py

# Шаг 2: отредактировать Redact/proposal.md в Obsidian (опционально)

# Шаг 3: сгенерировать HTML через GPT
python tools/generate_html.py

# Шаг 4: создать PDF
python tools/make_pdf.py
```

## Команды make_pdf.py

```bash
python tools/make_pdf.py                    # обычный запуск
python tools/make_pdf.py --logo=blue-rakun  # с логотипом blue-rakun
python tools/make_pdf.py --logo=spa-bureau  # с логотипом spa-bureau
python tools/make_pdf.py --test             # тестовый режим
```

## Структура проекта

```
9_CP_Python/
├── config/
│   └── gpt_prompts.py      # системные промпты и HTML-шаблон
├── tools/
│   ├── file_utils.py       # утилиты файловой системы
│   ├── gpt_client.py       # клиент OpenAI API
│   ├── extract_markdown.py # PDF/DOCX → Markdown
│   ├── generate_html.py    # Markdown → HTML
│   └── make_pdf.py         # HTML → PDF (Playwright)
├── src/
│   ├── print.css           # стили для печати
│   └── assets/logos/       # логотипы компаний
├── input/                  # входные документы (PDF, DOCX)
├── Redact/                 # proposal.md для редактирования
├── generated/sessions/     # результаты сессий (HTML, PDF)
├── logo-config.json        # конфигурация логотипов
├── .env                    # OPENAI_API_KEY (не коммитить!)
└── requirements.txt
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `OPENAI_API_KEY` | Ключ API OpenAI | — |
| `OPENAI_MODEL` | Модель GPT | `gpt-5` |

## Логотипы

Положите файлы логотипов в `src/assets/logos/` и настройте `logo-config.json`.
