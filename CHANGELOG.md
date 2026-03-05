# Changelog

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
