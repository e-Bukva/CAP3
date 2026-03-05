#!/usr/bin/env python3
"""
Генератор PDF из HTML с использованием Playwright.
A4, поля 15 мм, поддержка логотипа в футере, контроль разрывов.

Использование:
  python tools/make_pdf.py                    # обычный запуск
  python tools/make_pdf.py --logo=blue-rakun  # с логотипом
  python tools/make_pdf.py --logo=spa-bureau
  python tools/make_pdf.py --test             # тестовый режим
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.file_utils import PATHS

PROJECT_ROOT = Path(__file__).parent.parent

CONFIG = {
    "format": "A4",
    "margin": {
        "top": "20mm",
        "right": "20mm",
        "bottom": "40mm",
        "left": "20mm",
    },
    "print_background": True,
    "prefer_css_page_size": True,
    "use_timestamp": False,
    "timeout_navigation": 30000,
    "timeout_after_load": 500,
}


def log(message: str, kind: str = "info") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    prefix = {"info": "✓", "warn": "⚠", "error": "✗", "step": "→"}.get(kind, "ℹ")
    print(f"[{ts}] {prefix} {message}")


def find_latest_session() -> tuple[Path, str]:
    sessions_dir = PROJECT_ROOT / "generated" / "sessions"
    if not sessions_dir.exists():
        raise FileNotFoundError(
            "Папка generated/sessions не найдена. Запустите сначала: python tools/generate_html.py"
        )

    sessions = sorted(
        (d for d in sessions_dir.iterdir() if d.is_dir()),
        key=lambda d: d.name,
        reverse=True,
    )
    if not sessions:
        raise FileNotFoundError(
            "Сессии не найдены. Запустите сначала: python tools/generate_html.py"
        )

    latest = sessions[0]
    html_files = [f for f in latest.iterdir() if f.suffix.lower() == ".html"]
    if not html_files:
        raise FileNotFoundError(f"HTML не найден в сессии: {latest}")

    html_file = html_files[0]
    log(f"Найдена сессия: {latest.name}")
    log(f"HTML файл: {html_file}")
    return html_file, html_file.stem


def load_logo_config(logo_key: str | None = None) -> dict:
    config_path = PROJECT_ROOT / "logo-config.json"
    if not config_path.exists():
        log("Конфиг логотипа не найден, логотип отключён", "warn")
        return {"enabled": False}

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))

        if logo_key and config.get("alternatives", {}).get(logo_key):
            alt = config["alternatives"][logo_key]
            if isinstance(alt, str):
                config["logo"]["path"] = alt
            else:
                config["logo"]["path"] = alt["path"]
                if "width" in alt:
                    config["logo"]["width"] = alt["width"]
                if "opacity" in alt:
                    config["logo"]["opacity"] = alt["opacity"]
                if "margin" in alt:
                    config["logo"]["margin"] = {**config["logo"].get("margin", {}), **alt["margin"]}
            log(f"Выбран логотип: {logo_key} → {config['logo']['path']} ({config['logo']['width']})")
        elif logo_key:
            available = ", ".join(config.get("alternatives", {}).keys())
            log(f"Логотип '{logo_key}' не найден в alternatives, использую по умолчанию", "warn")
            log(f"Доступные: {available}", "warn")
        else:
            log(f"Используется логотип по умолчанию: {config['logo']['path']} ({config['logo']['width']})")

        log("Конфигурация логотипа загружена")
        return config
    except Exception as e:
        log(f"Ошибка чтения конфига: {e}", "warn")
        return {"enabled": False}


def generate_file_name(base_name: str, logo_key: str | None = None) -> str:
    if not CONFIG["use_timestamp"]:
        return f"{base_name}.pdf"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if logo_key:
        return f"{base_name}_{logo_key}_{ts}.pdf"
    return f"{base_name}_{ts}.pdf"


def generate_pdf(logo_key: str | None = None) -> dict:
    from playwright.sync_api import sync_playwright

    start_time = time.time()
    log("=== Генерация PDF началась ===", "step")

    html_file, base_name = find_latest_session()
    out_dir = html_file.parent

    logo_config = load_logo_config(logo_key)

    log("Запуск Chromium...", "step")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-web-security", "--disable-features=IsolateOrigins,site-per-process"],
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        html_url = "file:///" + str(html_file).replace("\\", "/")
        log(f"Загрузка страницы: {html_url}", "step")
        page.goto(html_url, wait_until="load", timeout=CONFIG["timeout_navigation"])

        log("Применение печатных стилей...", "step")
        page.emulate_media(media="print")

        if CONFIG["timeout_after_load"] > 0:
            page.wait_for_timeout(CONFIG["timeout_after_load"])

        log("Адаптивное склеивание маленьких секций...", "step")
        merged = page.evaluate("""
            () => {
                // A4 с нашими полями (~55mm): usable ≈ 242mm ≈ 915px при 96dpi.
                // Порог "маленькой" секции: < 25% высоты страницы ≈ 228px (~60mm).
                const SMALL_PX = 230;
                const sections = Array.from(document.querySelectorAll('.page-start'));
                let count = 0;
                sections.forEach((section, idx) => {
                    if (idx === 0) return;
                    const h = section.getBoundingClientRect().height;
                    if (h < SMALL_PX) {
                        section.classList.remove('page-start');
                        section.dataset.autoMerged = String(Math.round(h)) + 'px';
                        count++;
                    }
                });
                return count;
            }
        """)
        if merged:
            log(f"Склеено маленьких секций: {merged}", "info")

        log("Оборачивание чисел с пробелами в nowrap-span...", "step")
        page.evaluate("""() => {
            const walker = document.createTreeWalker(
                document.body, NodeFilter.SHOW_TEXT
            );
            const nodes = [];
            let node;
            while (node = walker.nextNode()) {
                if (node.parentElement.closest('td, th')) continue;
                if (/\\d[ \\t]+\\d/.test(node.textContent)) nodes.push(node);
            }
            nodes.forEach(n => {
                const parts = n.textContent.split(/(\\d+(?:[ \\t]+\\d+)+)/g);
                if (parts.length < 2) return;
                const frag = document.createDocumentFragment();
                parts.forEach(part => {
                    if (/^\\d+(?:[ \\t]+\\d+)+$/.test(part)) {
                        const span = document.createElement('span');
                        span.style.whiteSpace = 'nowrap';
                        span.textContent = part;
                        frag.appendChild(span);
                    } else {
                        frag.appendChild(document.createTextNode(part));
                    }
                });
                n.parentNode.replaceChild(frag, n);
            });
        }""")

        file_name = generate_file_name(base_name, logo_key)
        out_path = out_dir / file_name
        log(f"Генерация PDF: {out_path}", "step")

        pdf_options: dict = {
            "path": str(out_path),
            "format": CONFIG["format"],
            "margin": CONFIG["margin"],
            "print_background": CONFIG["print_background"],
            "prefer_css_page_size": CONFIG["prefer_css_page_size"],
            "display_header_footer": False,
        }

        if logo_config.get("enabled"):
            logo_path = PROJECT_ROOT / logo_config["logo"]["path"]
            if logo_path.exists():
                logo_bytes = logo_path.read_bytes()
                ext = logo_path.suffix.lstrip(".").lower()
                mime_types = {
                    "png": "image/png",
                    "jpg": "image/jpeg",
                    "jpeg": "image/jpeg",
                    "svg": "image/svg+xml",
                    "gif": "image/gif",
                }
                mime = mime_types.get(ext, "image/png")
                logo_b64 = base64.b64encode(logo_bytes).decode("ascii")
                logo_data_url = f"data:{mime};base64,{logo_b64}"

                logo_width = logo_config["logo"].get("width", "35mm")
                logo_opacity = logo_config["logo"].get("opacity", 0.9)
                from_edge = (
                    logo_config["logo"].get("margin", {}).get("fromEdge")
                    or logo_config["logo"].get("margin", {}).get("top", "5mm")
                )

                pdf_options["display_header_footer"] = True
                pdf_options["header_template"] = "<div></div>"
                pdf_options["footer_template"] = f"""
                  <div style="width:100%;height:35mm;position:relative;font-size:1px;">
                    <div style="position:absolute;bottom:{from_edge};left:0;right:0;text-align:center;">
                      <img src="{logo_data_url}" style="width:{logo_width};opacity:{logo_opacity};display:inline-block;" />
                    </div>
                  </div>
                """
                log(f"Логотип будет добавлен в футер ({ext.upper()}, {len(logo_bytes) // 1024}KB)")

        page.pdf(**pdf_options)
        browser.close()

    elapsed = time.time() - start_time
    log(f"=== PDF готов: {out_path} ({elapsed:.2f}s) ===")
    return {"success": True, "path": str(out_path), "elapsed": elapsed}


def run_tests(logo_key: str | None = None) -> None:
    log("=== Тестовый режим ===", "step")
    result = generate_pdf(logo_key)
    if result["success"]:
        log("✓ T1: Базовая генерация прошла успешно")
        log("✓ T2: Файл создан без ошибок")
        log("✓ T3: Проверьте вручную:", "warn")
        log("  - Пагинация и разрывы разделов", "warn")
        log("  - Кириллица отображается корректно", "warn")
        log("  - Таблицы не разорваны", "warn")
        log("  - Логотип в футере (если включён)", "warn")


def main() -> None:
    parser = argparse.ArgumentParser(description="Генерация PDF из HTML через Playwright")
    parser.add_argument("--logo", metavar="KEY", help="Ключ логотипа из logo-config.json (blue-rakun, spa-bureau)")
    parser.add_argument("--test", action="store_true", help="Тестовый режим")
    args = parser.parse_args()

    try:
        if args.test:
            run_tests(args.logo)
        else:
            generate_pdf(args.logo)
    except Exception as e:
        log(f"Ошибка генерации: {e}", "error")
        sys.exit(1)


if __name__ == "__main__":
    main()
