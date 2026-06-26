"""
generate_design.py
===================
Her post icin gorsel uretir.

Oncelik sirasi:
1. GPT Image (gpt-image-1) — tam post tasarimi, carousel slide'lari dahil
2. Fallback: HTML/CSS sablon sistemi (A/B/C/D/E) — GPT basarisiz olursa

Carousel icin her slide ayri gorsel olarak uretilir.
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


# ---------------------------------------------------------------------------
# HTML sablon render (fallback)
# ---------------------------------------------------------------------------

def fill_template(template_name: str, replacements: dict) -> str:
    template_path = os.path.join(TEMPLATES_DIR, f"template_{template_name.lower()}.html")
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    for key, value in replacements.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))
    return html


def render_html_to_png(html: str, out_path: str):
    tmp = os.path.join(TEMPLATES_DIR, "_tmp_render.html")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(html)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": config.RENDER_WIDTH, "height": config.RENDER_HEIGHT},
            device_scale_factor=config.DEVICE_SCALE_FACTOR,
        )
        page.goto(f"file://{os.path.abspath(tmp)}")
        page.wait_for_timeout(600)
        page.screenshot(path=out_path)
        browser.close()
    os.remove(tmp)


def render_fallback(post: dict, out_path: str) -> bool:
    """HTML sablon sistemiyle tek gorsel uretir. Basarili olursa True doner."""
    template = post.get("design_template")
    if not template:
        return False

    headline = post.get("design_headline", "")
    subhead = post.get("design_subhead", "")

    try:
        if template.upper() == "A":
            html = fill_template("a", {"HEADLINE": headline, "SUBHEAD": subhead,
                                       "CTA": "Yorumlarınızı anlamlandırın → commento.co"})
        elif template.upper() == "B":
            icon_cat = post.get("design_icon_category") or "genel"
            illustration = config.ILLUSTRATION_LIBRARY.get(icon_cat, config.DEFAULT_ILLUSTRATION)
            html = fill_template("b", {"ILLUSTRATION": f"../assets/illustrations/{illustration}",
                                       "HEADLINE": headline, "SUBHEAD": subhead,
                                       "CTA": "Yorumlarınızı anlamlandırın → commento.co"})
        elif template.upper() == "C":
            icon_cat = post.get("design_icon_category", "genel")
            icons = config.ICON_LIBRARY.get(icon_cat, config.ICON_LIBRARY["genel"])
            html = fill_template("c", {"HEADLINE": headline, "SUBHEAD": subhead,
                                       "ICON1": f"../assets/icons/{icons[0]}",
                                       "ICON2": f"../assets/icons/{icons[1]}",
                                       "ICON3": f"../assets/icons/{icons[2]}",
                                       "CTA": "Yorumlarınızı anlamlandırın → commento.co"})
        elif template.upper() == "D":
            html = fill_template("d", {"STAT_NUMBER": post.get("stat_number") or "",
                                       "STAT_UNIT": post.get("stat_unit") or "",
                                       "STAT_LABEL": post.get("stat_label") or subhead,
                                       "SUBHEAD": subhead,
                                       "CTA": "Yorumlarınızı anlamlandırın → commento.co"})
        elif template.upper() == "E":
            html = fill_template("e", {"HEADLINE": headline,
                                       "ITEM1": post.get("list_item_1") or "",
                                       "ITEM2": post.get("list_item_2") or "",
                                       "ITEM3": post.get("list_item_3") or "",
                                       "CTA": "Yorumlarınızı anlamlandırın → commento.co"})
        else:
            return False

        render_html_to_png(html, out_path)
        return True
    except Exception as e:
        print(f"  Fallback sablon hatasi: {e}")
        return False


# ---------------------------------------------------------------------------
# GPT Image uretimi
# ---------------------------------------------------------------------------

def try_gpt_images(post: dict, week_label: str, index: int) -> list[str]:
    """GPT Image ile gorsel(ler) uretmeyi dener. Bos liste = basarisiz."""
    try:
        from scripts.generate_image import generate_all_images_for_post
        return generate_all_images_for_post(post, week_label, index)
    except Exception as e:
        print(f"  GPT Image modulu hatasi: {e}")
        return []


# ---------------------------------------------------------------------------
# Ana render fonksiyonu
# ---------------------------------------------------------------------------

def slugify(text: str, max_len: int = 40) -> str:
    text = re.sub(r"[^\w\s-]", "", str(text), flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:max_len]


def render_post(post: dict, index: int, week_label: str) -> list[str]:
    """
    Bir post icin tum gorselleri uretir.
    Dondurulen liste: uretilen gorsel yollari (carousel'da birden fazla).
    Gorsel gerekmiyorsa (founder text post vb.) bos liste doner.
    """
    # Gorsel gerektirmeyen postlar (founder twitter, thread vb.)
    template = post.get("design_template")
    account_type = post.get("account_type", "company")
    post_format = post.get("format", "").lower()

    needs_visual = template is not None or account_type == "company"
    if not needs_visual:
        return []

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    topic_slug = slugify(post.get("topic", "post"))
    week_slug = slugify(week_label)

    # 1. GPT Image dene
    gpt_paths = try_gpt_images(post, week_label, index)
    if gpt_paths:
        # Gpt gorsellerini output/ klasorune kopyala
        output_paths = []
        for i, src in enumerate(gpt_paths):
            slide_suffix = f"_s{i+1}" if len(gpt_paths) > 1 else ""
            dst = os.path.join(OUTPUT_DIR, f"{week_slug}_{index:02d}_{topic_slug}{slide_suffix}_gpt.png")
            if src != dst:
                import shutil
                shutil.copy2(src, dst)
            output_paths.append(dst)
        return output_paths

    # 2. Fallback: HTML sablon
    if template:
        out_path = os.path.join(OUTPUT_DIR, f"{week_slug}_{index:02d}_{topic_slug}_template{template}.png")
        success = render_fallback(post, out_path)
        if success:
            return [out_path]

    return []


# ---------------------------------------------------------------------------
# CLI giris noktasi
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanim: python generate_design.py data/content_<hafta>.json")
        sys.exit(1)

    content_path = sys.argv[1]
    week_label = os.path.basename(content_path).replace("content_", "").replace(".json", "")

    with open(content_path, encoding="utf-8") as f:
        posts = json.load(f)

    all_image_paths = []
    for i, post in enumerate(posts, start=1):
        paths = render_post(post, i, week_label)
        if paths:
            for p in paths:
                print(f"[{i}] Gorsel: {os.path.basename(p)}")
            post["design_image_paths"] = paths
            post["design_image_path"] = paths[0]
            all_image_paths.extend(paths)
        else:
            print(f"[{i}] Gorsel yok (metin postu)")

    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f"\nToplam {len(all_image_paths)} gorsel uretildi.")
