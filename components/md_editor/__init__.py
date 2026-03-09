"""EasyMDE-based Markdown editor as a Streamlit component."""

import os
from pathlib import Path

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent / "frontend"

_component_func = components.declare_component(
    "md_editor",
    path=str(_FRONTEND_DIR),
)


def md_editor(value: str = "", height: int = 560, key: str | None = None) -> str:
    """
    WYSIWYG Markdown editor powered by EasyMDE.

    Returns the current markdown text as a string.
    Falls back to `value` on first render (before user edits).
    """
    result = _component_func(value=value, height=height, key=key, default=value)
    return result if result is not None else value
