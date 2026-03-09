# HTML-to-PDF Generator (Python)

Генератор PDF коммерческих предложений из Markdown с использованием GPT и Playwright.

## Пайплайн

```
Markdown → [GPT] → HTML → [Playwright] → PDF
               ↑
    (опционально) PDF/DOCX → [GPT] → Markdown
```

## Быстрый старт

### 1. Установить зависимости

```bash
pip install -r requirements.txt
playwright install chromium
```

> Зависимости: `openai`, `python-dotenv`, `requests`, `playwright`, `beautifulsoup4`, `streamlit`, `markdown`

### 2. Создать файл `.env`

```bash
cp .env.example .env
# Вставьте ваш OPENAI_API_KEY в .env
```

### 3а. Запустить веб-приложение (рекомендуется)

```bash
streamlit run app.py
```

Браузер откроется автоматически на `http://localhost:8501`.
Чтобы остановить — `Ctrl+C` в терминале.

#### Интерфейс — два шага

**Шаг 1 — Редактор MD**

| Элемент | Описание |
|---|---|
| Боковая панель | API Key, модель GPT, логотип, кнопка сброса |
| Поле «Название проекта» | Имя файла будущего PDF (без расширения) |
| Текстовый редактор | Вводите или вставляйте Markdown вручную |
| «Импортировать из PDF / DOCX» | Раскройте панель, загрузите файл — GPT извлечёт Markdown |
| Кнопка «Сгенерировать HTML» | Запускает GPT, переходит на шаг 2 |

**Шаг 2 — HTML и PDF**

| Элемент | Описание |
|---|---|
| Вкладка «Предпросмотр HTML» | Визуальный предпросмотр сгенерированного HTML |
| Вкладка «Генерация PDF» | Кнопка запуска Playwright, кнопка скачивания готового PDF |
| «← Редактировать MD» | Вернуться к редактору и изменить текст |
| «Перегенерировать HTML» | Вернуться к редактору и перезапустить GPT |

#### Типичный сценарий работы

```
1. Открыть http://localhost:8501
2. Боковая панель → ввести API Key (если не задан в .env)
3. Ввести название проекта
4. Вставить готовый Markdown в редактор
   — или раскрыть «Импортировать из PDF/DOCX» и загрузить файл
5. Нажать «Сгенерировать HTML через GPT»
6. На шаге 2: проверить предпросмотр
7. Вкладка «Генерация PDF» → «Сгенерировать PDF» → скачать
```

> **Совет:** API Key можно не вводить каждый раз — достаточно прописать
> `OPENAI_API_KEY=sk-...` в файле `.env` в корне проекта.

### 3б. CLI-пайплайн

```bash
# Шаг 1 (опционально): извлечь Markdown из PDF/DOCX
python tools/extract_markdown.py

# Шаг 2: отредактировать Redact/proposal.md (например в Obsidian)

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
├── app.py                  # Streamlit веб-приложение
├── config/
│   └── gpt_prompts.py      # системные промпты и HTML-шаблон (включает Google Fonts)
├── tools/
│   ├── file_utils.py       # утилиты файловой системы
│   ├── gpt_client.py       # клиент OpenAI API
│   ├── extract_markdown.py # PDF/DOCX → Markdown
│   ├── generate_html.py    # Markdown → HTML (CLI)
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
| `OPENAI_MODEL` | Модель GPT | `gpt-4.1` |

## Логотипы

Положите файлы логотипов в `src/assets/logos/` и настройте `logo-config.json`.

## Changelog

См. [CHANGELOG.md](./CHANGELOG.md).
