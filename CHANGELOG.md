# Changelog

## [Unreleased] — 2026-03-09

### Added
- **`app.py`**: Streamlit-приложение — основной интерфейс для работы с КП.
  - 2-шаговый поток: «Редактор MD» → «HTML и PDF» (MD-центричный пайплайн).
  - Импорт PDF/DOCX — опциональный, скрыт в `st.expander`.
  - HTML-предпросмотр с переопределением viewport для корректного отображения.
  - Список актуальных моделей 2026: `gpt-4.1` (по умолчанию), `gpt-4.1-mini`, `gpt-4.1-nano`, `gpt-5-mini`, `gpt-5.4`.
  - Фикс генерации PDF на Windows: `WindowsProactorEventLoopPolicy` + `ThreadPoolExecutor` для запуска Playwright из потока Streamlit.

### Changed
- **`config/gpt_prompts.py`**: В `<head>` HTML-шаблона добавлен Google Fonts
  (Montserrat 400/500/600/700 + italic, Inter 400/500/600/700).
  Гарантирует одинаковую типографику в CLI и Streamlit — независимо от системных шрифтов.
- **`tools/make_pdf.py`**: `wait_until` изменён с `"load"` на `"networkidle"`,
  таймаут навигации увеличен с 30 000 до 60 000 мс — Playwright ждёт загрузки
  Google Fonts перед рендером PDF.
- **`tools/gpt_client.py`**: Дефолтная модель обновлена с `gpt-5` → `gpt-4.1`.
- **`tools/extract_markdown.py`**, **`tools/generate_html.py`**,
  **`.env.example`**: Дефолтная модель обновлена с `gpt-4o` / `gpt-5` → `gpt-4.1`.
- **`requirements.txt`**: Добавлены `streamlit>=1.41.0` и `markdown>=3.5.0`.

---

## [Unreleased] — 2026-03-05

### Added
- **`generate_html.py`**: функция `fix_prepositions()` — оборачивает предлоги
  (в, и, с, к, у, о, а, но, не, на, из, по, за, от, до, со, во, об, при, для)
  вместе со следующим словом в `<span style="white-space:nowrap">`, предотвращая
  висячие предлоги в PDF.
- **`make_pdf.py`**: `page.evaluate()` — оборачивает числа с пробелами-разделителями
  тысяч (например `22 500`, `1 338 750`) в `<span style="white-space:nowrap">` через
  DOM-манипуляцию; ячейки таблиц (`td`, `th`) пропускаются.
- **`requirements.txt`**: добавлена зависимость `beautifulsoup4>=4.12.0`.

### Changed
- **`src/print.css`**:
  - `li` — добавлены `text-wrap: pretty`, `overflow-wrap: break-word`, `hyphens: none`.
  - `p` — добавлены `overflow-wrap: break-word`, `hyphens: none`
    (`text-wrap: pretty` намеренно убран: в Chromium PDF-рендерере он вызывает
    justify-подобное растяжение межсловных пробелов).
  - `.notes` — добавлен `text-align: left` для корректного выравнивания footnote-блока.

### Fixed
- Огромный горизонтальный разрыв между частями числа (например `22` / `500`)
  в footnote-блоке при генерации PDF: заменён подход `\u00a0` на DOM-обёртку
  `white-space:nowrap` — Chromium корректно рендерит обычный пробел внутри span.

---

## [0.2.0] — 2025 (предыдущий релиз)

- Рефакторинг: общий `strip_markdown_wrapper`, адаптивное склеивание маленьких секций PDF, поддержка логотипов.

## [0.1.0] — 2025 (первый коммит)

- Первоначальный Python-порт html-to-pdf-generator.
