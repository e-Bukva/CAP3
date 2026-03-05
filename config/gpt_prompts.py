"""Промпты для ChatGPT API."""

SYSTEM_PROMPT = """Ты — эксперт по оформлению коммерческих предложений. Твоя задача:

=== БАЗОВЫЕ ТРЕБОВАНИЯ ===

1. Структурировать текст пользователя в HTML формат по образцу шаблона
2. КРИТИЧЕСКИ ВАЖНО: НЕ изменяй текст пользователя, сохраняй его дословно
3. Определи разделы автоматически (прайс-лист, условия оплаты, объем работ, график и т.д.)
4. Используй те же CSS классы что в шаблоне
5. Если в тексте есть таблицы — оформи их как <table class="table no-break">
6. Если есть списки — оформи как <ul>
7. Сохраняй числовые значения, даты, названия точно как в оригинале
8. Определяй нумерацию разделов автоматически (01., 02., 03. и т.д.)
9. Для таблиц с ценами используй структуру: thead с заголовками, tbody с данными
10. Для итоговых сумм используй <div class="totals no-break"> с lead-row структурой
11. Для примечаний используй <div class="notes no-break">
12. ИГНОРИРУЙ колонтитулы, номера страниц, повторяющиеся элементы оформления — используй только основной содержательный текст документа


СТРУКТУРА ШАБЛОНА:

Каждый раздел оформляется так:
<section class="section page-start" id="раздел-id">
  <h2>01. Название раздела</h2>
  <!-- Содержимое раздела -->
</section>

ТАБЛИЦЫ (пример прайс-листа):
<table class="table no-break">
  <colgroup>
    <col />
    <col style="width:28%" />
  </colgroup>
  <thead>
    <tr><th>Stage</th><th class="num">Price (EUR)</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>1. Название этапа</strong></td>
      <td class="num"><strong>16 500,00</strong></td>
    </tr>
    <tr><td class="indent">Подэтап</td><td class="num muted">—</td></tr>
  </tbody>
</table>

ИТОГОВЫЕ СУММЫ:
<div class="totals no-break" aria-label="Total">
  <span class="totals-label">Total</span>
  <span class="totals-dots"></span>
  <span class="totals-value">33 400,00</span>
</div>

ПРИМЕЧАНИЯ:
<div class="notes no-break">
  <p>(1) Текст примечания.</p>
  <p>(2) Еще одно примечание.</p>
</div>

СПИСКИ:
<ul>
  <li>Элемент списка</li>
  <li>Другой элемент</li>
</ul>

DELIVERABLE (итоги раздела — ОБЯЗАТЕЛЬНО оборачивай в <p>):
<p><strong>Deliverable:</strong></p>
<ul>
  <li>Документ или результат</li>
</ul>

ПОДЗАГОЛОВКИ:
<h3>Подзаголовок раздела</h3>
<h3 class="muted">Подзаголовок второго уровня</h3>

КЛАССЫ:
- .page-start — начать раздел с новой страницы
- .no-break — запретить разрыв элемента между страницами
- .num — выравнивание чисел по правому краю (для таблиц)
- .indent — отступ для вложенных строк таблицы
- .muted — приглушенный текст
- .tight — компактная таблица (для графиков)

Верни ТОЛЬКО содержимое <body> (без тега body), готовое для вставки в HTML документ.
НЕ используй markdown обёртки вроде ```html.
Начинай сразу с первого <section>."""


def get_initial_prompt(extracted_text: str) -> str:
    return f"""Исходный текст коммерческого предложения:

{extracted_text}

Пожалуйста, структурируй этот текст в HTML согласно шаблону. Сохраняй весь текст без изменений, только добавь правильную разметку."""


def get_correction_prompt(current_html: str, user_correction: str) -> str:
    return f"""У меня есть HTML коммерческого предложения. Нужно внести следующие корректировки:

{user_correction}

Текущий HTML:
{current_html}

Пожалуйста, внеси указанные изменения, сохраняя структуру и стиль оформления. Верни полный исправленный HTML (только содержимое body, без тега)."""


HTML_TEMPLATE = {
    "doctype": "<!doctype html>",
    "head": """<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Commercial Proposal</title>
<link rel="stylesheet" href="./print.css" media="print">
<style>
  :root{
    --blue:#1D4E8F; --blue2:#3A6EA8; --tint:#EDF2F9;
    --ink:#111827; --body:#374151; --quiet:#6B7280;
    --rule:#D1D5DB; --maxw:860px;
  }
  *,*::before,*::after{box-sizing:border-box;}
  html,body{margin:0;background:#fff;color:var(--body);
    font-family:"Gotham","Montserrat","Inter","Segoe UI",system-ui,-apple-system,Arial,sans-serif;
    font-size:13.5px;line-height:1.65;-webkit-font-smoothing:antialiased;}
  .page{max-width:var(--maxw);margin:0 auto;padding:52px 44px;}
  .section{display:flow-root;}
  .section+.section{margin-top:52px;padding-top:52px;}
  h2{margin:0 0 20px;font-size:9.5px;font-weight:700;letter-spacing:0.2em;
    text-transform:uppercase;color:var(--blue);padding-bottom:8px;border-bottom:1px solid var(--blue);}
  h3{margin:0;font-size:15px;font-weight:600;letter-spacing:-0.01em;color:var(--ink);}
  h3.muted{font-size:12px;font-weight:500;color:var(--blue2);letter-spacing:0;}
  h3+*{margin-top:10px;}
  h3.muted+*{margin-top:6px;}
  ul+h3{margin-top:32px;}
  ul+h3.muted{margin-top:14px;}
  p+h3{margin-top:32px;}
  p:has(>strong:only-child)+ul+h3{margin-top:32px!important;}
  p{margin:0;} p+p{margin-top:12px;}
  ul{margin:0;padding-left:16px;list-style-type:disc;}
  ul li{margin-top:7px;padding-left:2px;}
  ul li:first-child{margin-top:0;}
  .section>p>strong:only-child{display:inline-block;font-size:8.5px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:var(--blue);background:var(--tint);padding:2px 7px;border-radius:2px;}
  p:has(>strong:only-child){margin-top:20px!important;margin-bottom:5px;}
  p:has(>strong:only-child)+ul{margin-top:0!important;}
  .table{width:100%;border-collapse:collapse;margin-top:4px;font-size:13.5px;}
  .table thead th{padding:7px 10px;text-align:left;font-size:9px;font-weight:600;
    text-transform:uppercase;letter-spacing:0.1em;color:var(--quiet);border-bottom:1px solid var(--rule);}
  .table thead th.num{text-align:right;}
  .table tbody td{padding:9px 10px;vertical-align:top;border-bottom:1px solid var(--rule);font-variant-numeric:tabular-nums;}
  .table tbody tr:last-child td{border-bottom:none;}
  .table td.num{text-align:right;white-space:nowrap;}
  .indent{padding-left:24px!important;color:var(--quiet);font-size:13px;}
  .totals{margin-top:12px;padding-top:12px;border-top:1.5px solid var(--ink);display:flex;align-items:baseline;justify-content:space-between;}
  .totals-label{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.14em;color:var(--ink);}
  .totals-dots{display:none;}
  .totals-value{font-size:15px;font-weight:700;color:var(--ink);letter-spacing:-0.01em;font-variant-numeric:tabular-nums;}
  .notes{margin-top:20px;padding-left:14px;border-left:2px solid var(--rule);}
  .notes p{font-size:12.5px;color:var(--quiet);line-height:1.55;}
  .notes p+p{margin-top:5px;}
  .notes p:first-child{font-weight:600;color:var(--body);}
  .footer{margin-top:52px;color:var(--quiet);font-size:12px;text-align:center;}
  .pdf-logo{display:none;}
  @media print{
    *,*::before,*::after{-webkit-print-color-adjust:exact!important;print-color-adjust:exact!important;color-adjust:exact!important;}
    .page{margin:0;padding:0 36px;max-width:100%;}
    .page-start{break-before:page;page-break-before:always;}
    .page-start:first-of-type{break-before:auto;page-break-before:auto;}
    .section{page-break-inside:auto;break-inside:auto;orphans:3;widows:3;}
    .table,.totals,.notes{page-break-inside:avoid;break-inside:avoid;}
    h2,h3{page-break-after:avoid;break-after:avoid;}
    h2+*,h3+ul,h3+p{page-break-before:avoid;break-before:avoid;}
    tr{page-break-inside:avoid;break-inside:avoid;}
    .section+.section{margin-top:28px;padding-top:28px;}
    .footer{display:none;}
    .pdf-logo{display:block;position:fixed;}
    .pdf-logo img{max-width:100%;height:auto;display:block;}
  }
</style>
</head>""",
    "body_start": """<body>
  <div class="sheet">
  <main class="page">""",
    "body_end": """
    <div class="footer">© Blue Rakun</div>

  </main>
  </div>

  <!-- PDF Logo (injected dynamically during PDF generation) -->
  <div class="pdf-logo" id="pdf-logo"></div>

</body>
</html>""",
}


EXTRACT_MARKDOWN_PROMPT = """Ты — эксперт по извлечению структурированного содержимого из документов.

Твоя задача: преобразовать содержимое документа в **чистый Markdown** формат для дальнейшего редактирования.

=== КРИТИЧЕСКИ ВАЖНО ===

1. **Игнорируй** колонтитулы, номера страниц, повторяющиеся элементы оформления
2. **Сохраняй** ВСЕ содержательные данные: текст, числа, названия, даты — точно как в документе
3. **НЕ изменяй** текст пользователя, только структурируй его в Markdown

=== ФОРМАТ ВЫВОДА ===

Используй только стандартный Markdown синтаксис:

**Заголовки:**
## 1. Название раздела
### Подзаголовок

**Таблицы:**
| Название | Цена |
|----------|-----:|
| Услуга 1 | 1000 |
| Услуга 2 | 2000 |

**Списки:**
- Элемент списка
- Другой элемент
  - Вложенный элемент

**Примечания:**
> (1) Текст примечания
> (2) Еще одно примечание

**Жирный текст:** **ИТОГО**
**Разделители:** ---

=== ЧТО НЕ ДЕЛАТЬ ===

❌ НЕ используй HTML теги (<div>, <table>, <section>)
❌ НЕ добавляй markdown обёртки вроде ```markdown
❌ НЕ изменяй числа, даты, названия
❌ НЕ включай технические элементы (номера страниц, колонтитулы)

Верни только чистый Markdown, начиная сразу с первого заголовка."""


def get_extract_markdown_prompt() -> str:
    return (
        "Преобразуй содержимое этого документа в чистый Markdown формат. "
        "КРИТИЧЕСКИ ВАЖНО: игнорируй колонтитулы, номера страниц и повторяющиеся элементы оформления. "
        "Сохраняй все содержательные данные точно как в документе."
    )
