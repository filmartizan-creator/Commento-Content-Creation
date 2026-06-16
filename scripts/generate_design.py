"""
generate_design.py
===================
content_*.json içindeki design_template alanına göre Şablon A/B/C/D/E'yi
doldurup PNG olarak render eder (Playwright + headless Chromium).

A: Lavanta arka plan, çarpıcı tek mesaj
B: Gradient + 3D illüstrasyon + balon (config.ILLUSTRATION_LIBRARY kullanır)
C: Koyu mavi, 3 ikonlu karşılaştırma (config.ICON_LIBRARY kullanır)
D: Büyük istatistik/sayı vurgusu, balon içinde açıklama
E: Numaralı balon kartlardan oluşan checklist/liste
"""

import json
import os
import re
import sys
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(BASE_DIR, config.TEMPLATES_DIR)
ASSETS_DIR = os.path.join(BASE_DIR, config.ASSETS_DIR)
OUTPUT_DIR = os.path.join(BASE_DIR, config.DESIGN_OUTPUT_DIR)


def fill_template(template_name: str, replacements: dict) -> str:
    template_path = os.path.join(TEMPLATES_DIR, f"template_{template_name.lower()}.html")
    with open(template_path, encoding="utf-8") as f:
        html = f.read()

    for key, value in replacements.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))

    return html


def render_html_to_png(html: str, out_path: str, working_dir: str):
    tmp_html_path = os.path.join(working_dir, "_tmp_render.html")
    with open(tmp_html_path, "w", encoding="utf-8") as f:
        f.write(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": config.RENDER_WIDTH, "height": config.RENDER_HEIGHT},
            device_scale_factor=config.DEVICE_SCALE_FACTOR,
        )
        page.goto(f"file://{os.path.abspath(tmp_html_path)}")
        page.wait_for_timeout(600)
        page.screenshot(path=out_path)
        browser.close()

    os.remove(tmp_html_path)


def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len]


def render_post(post: dict, index: int, week_label: str) -> str | None:
    template = post.get("design_template")
    if not template:
        return None

    headline = post.get("design_headline", "")
    subhead = post.get("design_subhead", "")
    out_name = f"{week_label}_{index:02d}_{slugify(post.get('topic', ''))}_template{template}.png"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    if template.upper() == "A":
        html = fill_template("a", {
            "HEADLINE": headline,
            "SUBHEAD": subhead,
            "CTA": "Yorumlarınızı anlamlandırın → commento.co",
        })

    elif template.upper() == "B":
        icon_cat = post.get("design_icon_category") or "genel"
        illustration = config.ILLUSTRATION_LIBRARY.get(icon_cat, config.DEFAULT_ILLUSTRATION)
        html = fill_template("b", {
            "ILLUSTRATION": f"../assets/illustrations/{illustration}",
            "HEADLINE": headline,
            "SUBHEAD": subhead,
            "CTA": "Yorumlarınızı anlamlandırın → commento.co",
        })

    elif template.upper() == "C":
        icon_cat = post.get("design_icon_category", "genel")
        icons = config.ICON_LIBRARY.get(icon_cat, config.ICON_LIBRARY["genel"])
        html = fill_template("c", {
            "HEADLINE": headline,
            "SUBHEAD": subhead,
            "ICON1": f"../assets/icons/{icons[0]}",
            "ICON2": f"../assets/icons/{icons[1]}",
            "ICON3": f"../assets/icons/{icons[2]}",
            "CTA": "Yorumlarınızı anlamlandırın → commento.co",
        })

    elif template.upper() == "D":
        html = fill_template("d", {
            "STAT_NUMBER": post.get("stat_number") or "",
            "STAT_UNIT": post.get("stat_unit") or "",
            "STAT_LABEL": post.get("stat_label") or subhead,
            "SUBHEAD": subhead,
            "CTA": "Yorumlarınızı anlamlandırın → commento.co",
        })

    elif template.upper() == "E":
        html = fill_template("e", {
            "HEADLINE": headline,
            "ITEM1": post.get("list_item_1") or "",
            "ITEM2": post.get("list_item_2") or "",
            "ITEM3": post.get("list_item_3") or "",
            "CTA": "Yorumlarınızı anlamlandırın → commento.co",
        })

    else:
        return None

    render_html_to_png(html, out_path, TEMPLATES_DIR)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python generate_design.py data/content_<hafta>.json")
        sys.exit(1)

    content_path = sys.argv[1]
    week_label = os.path.basename(content_path).replace("content_", "").replace(".json", "")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(content_path, encoding="utf-8") as f:
        posts = json.load(f)

    for i, post in enumerate(posts, start=1):
        out_path = render_post(post, i, week_label)
        if out_path:
            print(f"[{i}] Tasarım üretildi: {out_path}")
            post["design_image_path"] = out_path
        else:
            print(f"[{i}] Tasarım yok (görsel gerektirmeyen format)")

    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)
