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

> Зависимости: `openai`, `python-dotenv`, `requests`, `playwright`, `beautifulsoup4`

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

## Типографика PDF

При генерации HTML и PDF автоматически применяются два типографических фикса:

| Фикс | Где | Что делает |
|---|---|---|
| Предлоги | `generate_html.py` | Оборачивает предлог + следующее слово в `nowrap`-span, предотвращая висячие предлоги |
| Числа с пробелами | `make_pdf.py` | Оборачивает `22 500`, `1 338 750` и т. п. в `nowrap`-span (вне ячеек таблицы) |

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
│   ├── print.css           # стили для печати (A4, типографика, nowrap)
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

## Changelog

См. [CHANGELOG.md](./CHANGELOG.md).
