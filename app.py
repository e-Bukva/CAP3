#!/usr/bin/env python3
"""
Streamlit-приложение для генерации PDF коммерческих предложений.

Flow: Редактировать MD → Сгенерировать HTML → Скачать PDF
      (опционально: импорт из PDF/DOCX для извлечения MD)
"""

import json
import os
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))

load_dotenv()

from config.gpt_prompts import HTML_TEMPLATE
from tools.file_utils import (
    PATHS,
    create_full_html_document,
    create_session_directory,
    create_session_timestamp,
    ensure_dir,
)
from tools.generate_html import fix_prepositions
from tools.gpt_client import (
    extract_markdown_from_pdf,
    extract_markdown_from_text,
    generate_html_from_file,
    initialize_openai,
)
from tools.make_pdf import generate_pdf, load_logo_config

# ─── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="КП Генератор",
    page_icon="📄",
    layout="wide",
)

# ─── Session state ────────────────────────────────────────────────────────────

_DEFAULTS: dict = {
    "step": 1,
    "api_key": os.environ.get("OPENAI_API_KEY", ""),
    "model": os.environ.get("OPENAI_MODEL", "gpt-4.1"),
    "logo_key": None,
    "proposal_name": "",
    "markdown_text": "",
    "html_content": "",
    "session_path": None,
    "pdf_path": None,
}

for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─── Helpers ──────────────────────────────────────────────────────────────────


def _init_api() -> None:
    initialize_openai(st.session_state.api_key, st.session_state.model)


def _save_source_meta(name: str, source_file_name: str = "manual") -> None:
    ensure_dir(PATHS["input"])
    meta = {"sourceFile": source_file_name, "name": name}
    meta_path = PATHS["input"] / "source.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")



def _reset() -> None:
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Настройки")

    api_key_val = st.text_input(
        "OpenAI API Key",
        value=st.session_state.api_key,
        type="password",
        placeholder="sk-...",
    )
    if api_key_val:
        st.session_state.api_key = api_key_val

    model_options = [
        "gpt-4.1",       # smartest non-reasoning, default
        "gpt-4.1-mini",  # smaller, faster
        "gpt-4.1-nano",  # fastest, cheapest
        "gpt-5-mini",    # faster GPT-5
        "gpt-5.4",       # most capable
    ]
    default_model = (
        st.session_state.model if st.session_state.model in model_options else model_options[0]
    )
    st.session_state.model = st.selectbox(
        "Модель", model_options, index=model_options.index(default_model)
    )

    st.divider()

    logo_cfg = load_logo_config()
    logo_alternatives = list(logo_cfg.get("alternatives", {}).keys())
    logo_options = ["— без логотипа —"] + logo_alternatives
    selected_logo = st.selectbox("Логотип в PDF", logo_options)
    st.session_state.logo_key = None if selected_logo == "— без логотипа —" else selected_logo

    st.divider()

    if st.button("🔄 Начать заново", use_container_width=True):
        _reset()
        st.rerun()

# ─── Header ───────────────────────────────────────────────────────────────────

st.title("📄 Генератор коммерческих предложений")

_STEP_LABELS = ["1. Редактор MD", "2. HTML и PDF"]
_step_cols = st.columns(2)
for _i, (_col, _label) in enumerate(zip(_step_cols, _STEP_LABELS), 1):
    with _col:
        if _i < st.session_state.step:
            st.success(_label)
        elif _i == st.session_state.step:
            st.info(f"**{_label}**")
        else:
            st.caption(_label)

st.divider()

# ─── STEP 1: MD Editor (primary) + optional file import ───────────────────────

if st.session_state.step == 1:

    # Top bar: name + import
    col_name, col_import = st.columns([2, 3])

    with col_name:
        name_val = st.text_input(
            "Название проекта",
            value=st.session_state.proposal_name,
            placeholder="например: Бювет_Космос",
            help="Используется как имя файла PDF",
        )
        st.session_state.proposal_name = name_val.strip()

    with col_import:
        with st.expander("📁 Импортировать из PDF / DOCX", expanded=False):
            uploaded = st.file_uploader(
                "Загрузите файл — Markdown будет извлечён через GPT",
                type=["pdf", "docx", "doc"],
                label_visibility="collapsed",
            )
            if uploaded:
                btn_label = f"Извлечь MD из «{uploaded.name}»"
                if not st.session_state.api_key:
                    st.warning("Введите OpenAI API Key в боковой панели")
                elif st.button(btn_label, type="primary", use_container_width=True):
                    with st.spinner("Извлекаем структуру через GPT…"):
                        try:
                            _init_api()
                            ensure_dir(PATHS["input"])
                            input_path = PATHS["input"] / uploaded.name
                            input_path.write_bytes(uploaded.getvalue())

                            suffix = Path(uploaded.name).suffix.lower()
                            if suffix == ".pdf":
                                result = extract_markdown_from_pdf(
                                    input_path, st.session_state.model
                                )
                            else:
                                result = extract_markdown_from_text(
                                    input_path, st.session_state.model
                                )

                            st.session_state.markdown_text = result["markdown"]
                            if not st.session_state.proposal_name:
                                st.session_state.proposal_name = Path(uploaded.name).stem

                            usage = result["usage"]
                            st.success(
                                f"✓ {len(result['markdown']) / 1024:.1f} KB, "
                                f"{usage['total_tokens']} токенов"
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Ошибка: {exc}")

    md_text = st.text_area(
        label="md_editor",
        value=st.session_state.markdown_text,
        height=560,
        label_visibility="collapsed",
        placeholder="Введите или вставьте Markdown текст…\n\nИли импортируйте из PDF/DOCX через панель выше.",
    )
    st.session_state.markdown_text = md_text

    st.divider()

    # Generate HTML button
    can_generate = bool(st.session_state.markdown_text.strip() and st.session_state.proposal_name)
    if not st.session_state.api_key:
        st.warning("Введите OpenAI API Key в боковой панели")
    elif not st.session_state.proposal_name:
        st.warning("Введите название проекта")
    elif not st.session_state.markdown_text.strip():
        st.info("Введите текст в редакторе или импортируйте файл")
    else:
        if st.button(
            "🤖 Сгенерировать HTML через GPT",
            type="primary",
            use_container_width=True,
            disabled=not can_generate,
        ):
            with st.spinner("Генерируем HTML через GPT…"):
                try:
                    _init_api()
                    _save_source_meta(st.session_state.proposal_name)

                    ensure_dir(PATHS["redact"])
                    proposal_md_path = PATHS["redact"] / "proposal.md"
                    proposal_md_path.write_text(
                        st.session_state.markdown_text, encoding="utf-8"
                    )

                    result = generate_html_from_file(proposal_md_path, st.session_state.model)

                    full_html = create_full_html_document(result["html"], HTML_TEMPLATE)
                    full_html = fix_prepositions(full_html)

                    timestamp = create_session_timestamp()
                    session_path = create_session_directory(
                        timestamp, st.session_state.proposal_name
                    )

                    src_css = PATHS["src"] / "print.css"
                    if src_css.exists():
                        shutil.copy2(src_css, session_path / "print.css")
                    shutil.copy2(
                        proposal_md_path,
                        session_path / f"{st.session_state.proposal_name}.md",
                    )

                    html_path = session_path / f"{st.session_state.proposal_name}.html"
                    html_path.write_text(full_html, encoding="utf-8")

                    st.session_state.html_content = full_html
                    st.session_state.session_path = str(session_path)
                    st.session_state.pdf_path = None

                    usage = result["usage"]
                    st.success(f"✓ HTML сгенерирован — {usage['total_tokens']} токенов")
                    st.session_state.step = 2
                    st.rerun()
                except Exception as exc:
                    st.error(f"Ошибка: {exc}")

# ─── STEP 2: HTML preview + PDF ───────────────────────────────────────────────

elif st.session_state.step == 2:
    st.subheader(f"HTML и PDF: {st.session_state.proposal_name}")

    tab_preview, tab_pdf = st.tabs(["👁 Предпросмотр HTML", "🖨 Генерация PDF"])

    with tab_preview:
        # Inject viewport width override so content fills the iframe properly
        preview_html = st.session_state.html_content.replace(
            "<style>",
            "<style>html,body{background:#fff!important;} .page{max-width:100%!important;padding:32px 40px!important;}",
            1,
        )
        st.components.v1.html(preview_html, height=860, scrolling=True)

    with tab_pdf:
        col_gen, col_download = st.columns([1, 1])

        with col_gen:
            if st.button("🖨 Сгенерировать PDF", type="primary", use_container_width=True):
                with st.spinner("Рендерим PDF через Playwright…"):
                    try:
                        import asyncio
                        import concurrent.futures

                        def _run_pdf(logo_key):
                            # Windows: threads get SelectorEventLoop by default,
                            # which does not support subprocesses.
                            # ProactorEventLoop is required for Playwright.
                            asyncio.set_event_loop_policy(
                                asyncio.WindowsProactorEventLoopPolicy()
                            )
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            try:
                                return generate_pdf(logo_key)
                            finally:
                                loop.close()

                        logo_key = st.session_state.logo_key
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                            result = ex.submit(_run_pdf, logo_key).result()

                        st.session_state.pdf_path = result["path"]
                        st.success(f"✓ Готово за {result['elapsed']:.1f}с")
                        st.rerun()
                    except Exception as exc:
                        import traceback
                        st.error(f"Ошибка: {exc}")
                        st.code(traceback.format_exc())

        with col_download:
            if st.session_state.pdf_path and Path(st.session_state.pdf_path).exists():
                pdf_bytes = Path(st.session_state.pdf_path).read_bytes()
                st.download_button(
                    label="⬇️ Скачать PDF",
                    data=pdf_bytes,
                    file_name=f"{st.session_state.proposal_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            else:
                st.caption("PDF появится здесь после генерации")

    st.divider()

    col_back, col_regen = st.columns(2)
    with col_back:
        if st.button("← Редактировать MD", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_regen:
        if st.button("🔄 Перегенерировать HTML", use_container_width=True):
            st.session_state.step = 1
            st.session_state.html_content = ""
            st.session_state.pdf_path = None
            st.rerun()
