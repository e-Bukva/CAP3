#!/usr/bin/env python3
"""
Streamlit-приложение для генерации PDF коммерческих предложений.

Flow: Загрузить файл → Извлечь MD → Редактировать → Сгенерировать HTML → Скачать PDF
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

import markdown as md_lib
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
    "model": os.environ.get("OPENAI_MODEL", "gpt-5"),
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


def _save_source_meta(name: str, source_file_name: str) -> None:
    ensure_dir(PATHS["input"])
    meta = {"sourceFile": source_file_name, "name": name}
    meta_path = PATHS["input"] / "source.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def _md_to_html(text: str) -> str:
    return md_lib.markdown(text, extensions=["tables", "fenced_code"])


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

    model_options = ["gpt-5", "gpt-4o", "gpt-4o-mini"]
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

_STEP_LABELS = ["1. Загрузка и извлечение", "2. Редактирование MD", "3. HTML и PDF"]
_step_cols = st.columns(3)
for _i, (_col, _label) in enumerate(zip(_step_cols, _STEP_LABELS), 1):
    with _col:
        if _i < st.session_state.step:
            st.success(_label)
        elif _i == st.session_state.step:
            st.info(f"**{_label}**")
        else:
            st.caption(_label)

st.divider()

# ─── STEP 1: Upload + name + extract ──────────────────────────────────────────

if st.session_state.step == 1:
    st.subheader("Загрузите исходный документ")

    col_file, col_name = st.columns([3, 2])

    with col_file:
        uploaded = st.file_uploader(
            "PDF или Word файл",
            type=["pdf", "docx", "doc"],
            help="Исходное коммерческое предложение",
        )

    with col_name:
        name_val = st.text_input(
            "Название проекта",
            value=st.session_state.proposal_name,
            placeholder="например: Бювет_Космос",
            help="Используется как имя файла PDF",
        )
        st.session_state.proposal_name = name_val.strip()

    if not st.session_state.api_key:
        st.warning("Введите OpenAI API Key в боковой панели")
    elif not uploaded:
        st.info("Загрузите PDF или Word файл")
    elif not st.session_state.proposal_name:
        st.warning("Введите название проекта")
    else:
        if st.button("🚀 Извлечь Markdown", type="primary", use_container_width=True):
            with st.spinner("Загружаем файл и извлекаем структуру через GPT…"):
                try:
                    _init_api()
                    ensure_dir(PATHS["input"])
                    input_path = PATHS["input"] / uploaded.name
                    input_path.write_bytes(uploaded.getvalue())

                    suffix = Path(uploaded.name).suffix.lower()
                    if suffix == ".pdf":
                        result = extract_markdown_from_pdf(input_path, st.session_state.model)
                    else:
                        result = extract_markdown_from_text(input_path, st.session_state.model)

                    st.session_state.markdown_text = result["markdown"]
                    _save_source_meta(st.session_state.proposal_name, uploaded.name)

                    usage = result["usage"]
                    st.success(
                        f"✓ Готово — {len(result['markdown']) / 1024:.1f} KB, "
                        f"{usage['total_tokens']} токенов"
                    )
                    st.session_state.step = 2
                    st.rerun()
                except Exception as exc:
                    st.error(f"Ошибка: {exc}")

# ─── STEP 2: Edit MD + live preview ───────────────────────────────────────────

elif st.session_state.step == 2:
    st.subheader(f"Редактирование: {st.session_state.proposal_name}")

    col_editor, col_preview = st.columns(2)

    with col_editor:
        st.markdown("**Markdown**")
        md_text = st.text_area(
            label="md_editor",
            value=st.session_state.markdown_text,
            height=580,
            label_visibility="collapsed",
        )
        st.session_state.markdown_text = md_text

    with col_preview:
        st.markdown("**Предпросмотр**")
        preview_html = _md_to_html(md_text)
        st.components.v1.html(
            f"""
            <div style="font-family:sans-serif;font-size:14px;line-height:1.65;
                        padding:12px 16px;color:#1f2937">
              {preview_html}
            </div>
            """,
            height=580,
            scrolling=True,
        )

    st.divider()

    col_back, col_generate = st.columns([1, 2])
    with col_back:
        if st.button("← Назад", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with col_generate:
        if st.button("🤖 Сгенерировать HTML через GPT", type="primary", use_container_width=True):
            if not st.session_state.api_key:
                st.error("Введите OpenAI API Key")
            else:
                with st.spinner("Генерируем HTML через GPT…"):
                    try:
                        _init_api()

                        ensure_dir(PATHS["redact"])
                        proposal_md_path = PATHS["redact"] / "proposal.md"
                        proposal_md_path.write_text(
                            st.session_state.markdown_text, encoding="utf-8"
                        )

                        result = generate_html_from_file(
                            proposal_md_path, st.session_state.model
                        )

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
                        st.session_state.step = 3
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Ошибка: {exc}")

# ─── STEP 3: HTML preview + PDF ───────────────────────────────────────────────

elif st.session_state.step == 3:
    st.subheader(f"HTML и PDF: {st.session_state.proposal_name}")

    tab_preview, tab_pdf = st.tabs(["👁 Предпросмотр HTML", "🖨 Генерация PDF"])

    with tab_preview:
        st.components.v1.html(st.session_state.html_content, height=820, scrolling=True)

    with tab_pdf:
        col_gen, col_download = st.columns([1, 1])

        with col_gen:
            if st.button("🖨 Сгенерировать PDF", type="primary", use_container_width=True):
                with st.spinner("Рендерим PDF через Playwright…"):
                    try:
                        result = generate_pdf(st.session_state.logo_key)
                        st.session_state.pdf_path = result["path"]
                        st.success(f"✓ Готово за {result['elapsed']:.1f}с")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Ошибка: {exc}")

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

    col_back_md, col_regen = st.columns(2)
    with col_back_md:
        if st.button("← Редактировать MD", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col_regen:
        if st.button("🔄 Перегенерировать HTML", use_container_width=True):
            st.session_state.step = 2
            st.session_state.html_content = ""
            st.session_state.pdf_path = None
            st.rerun()
