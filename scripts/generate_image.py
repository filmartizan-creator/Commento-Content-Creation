"""
generate_image.py
==================
OpenAI gpt-image-1 ile Commento icin tam sosyal medya gorseli uretir.

- Tekil post: tek gorsel
- Carousel: her slide icin ayri gorsel (slide_index parametresi ile)
- Referans stil gorselleri base64 olarak GPT'ye verilir
- Commento logosu referans olarak eklenir
"""

import base64
import os
import re
import sys

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_IMAGES_DIR = os.path.join(BASE_DIR, "assets", "ai_generated")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(AI_IMAGES_DIR, exist_ok=True)


def load_image_b64(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return base64.standard_b64encode(f.read()).decode("utf-8")
    except Exception:
        return None


def slugify(text: str, max_len: int = 35) -> str:
    text = re.sub(r"[^\w\s-]", "", str(text), flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:max_len]


BRAND_SPEC = """
BRAND: Commento — AI-powered social media comment analytics SaaS.
LOGO: Top-center or top-left "Commento" wordmark — letter C shaped as a speech bubble icon,
      followed by "ommento" in bold Poppins. Use exactly as shown in reference.
COLOR PALETTE:
  - Background: soft lavender #E7E9FB (light posts) OR deep navy #1B2A8F (dark/bold posts)
  - Primary blue: #4D5DDB
  - Text dark: #0E0E12
  - Text blue accent: #4D5DDB
  - White: #FFFFFF
TYPOGRAPHY: Poppins font family. Headlines bold/extrabold. Body regular/medium.
STYLE: Clean, modern, premium B2B SaaS. Minimal clutter. 3D icons/elements welcome.
       Speech bubble motif echoes the brand mark. Dot grid decorations subtly in corners.
SIZE: 1080x1350px (4:5 portrait ratio for Instagram/LinkedIn).
"""


def build_post_prompt(
    topic: str,
    caption: str,
    headline: str,
    subhead: str,
    platform: str,
    post_format: str,
    slide_index: int = 0,
    total_slides: int = 1,
    slide_content: str = "",
) -> str:
    is_carousel = total_slides > 1
    is_dark = any(k in (topic or "").lower() for k in ["kriz", "crisis", "uyari", "alert", "tehlike"])
    bg_note = "dark navy #1B2A8F background" if is_dark else "soft lavender #E7E9FB background"

    if is_carousel:
        slide_note = f"""
CAROUSEL SLIDE {slide_index + 1} of {total_slides}:
- Show slide number indicator: "{slide_index + 1}/{total_slides}" top-right corner (small, subtle)
- If first slide (1/{total_slides}): bold hook headline, strong visual, entice to swipe
- If middle slide: data visualization, comparison, or detailed insight
- If last slide: CTA prominent, "commento.co" URL visible, summary or action step
- Slide content for this slide: {slide_content or headline}
- Navigation arrow bottom-right (arrow) on all slides except last
"""
    else:
        slide_note = f"""
SINGLE POST:
- Headline: {headline}
- Subheadline: {subhead}
- CTA bottom: small text "commento.co"
"""

    return f"""
Design a professional social media post for Commento brand.

{BRAND_SPEC}

BACKGROUND: Use {bg_note}.

POST TOPIC: {topic}
PLATFORM: {platform}

{slide_note}

VISUAL DIRECTION:
- Do NOT just put text on a plain background. Create rich visual storytelling.
- Use ONE of these visual approaches (choose what fits the topic best):
  (a) Phone/dashboard mockup showing Commento UI with relevant data
  (b) Infographic with icons, stats, comparison cards (left/right or before/after)
  (c) Abstract 3D elements: speech bubbles, sentiment indicators, data nodes
  (d) Scenario visualization: floating comment cards from different platforms
- Key insight or stat should be visually prominent (large number, bold color)
- Speech bubbles are on-brand -- use them as design elements where appropriate
- 3D icons in brand blue are welcome (clocks, shields, magnifiers, charts, etc.)

TEXT ON IMAGE:
- Include the most important 1-2 lines of text as large display type
- Do NOT copy the entire caption -- distill to the visual punchline
- Turkish text is fine, render it accurately
- Keep text minimal: the visual should do most of the storytelling

CAPTION CONTEXT (for creative direction only, do not copy verbatim):
{caption[:300]}

OUTPUT: A single complete, print-ready social media post. No mockup frame around it.
"""


def generate_post_image(
    post: dict,
    week_label: str,
    index: int,
    slide_index: int = 0,
    total_slides: int = 1,
    slide_content: str = "",
) -> str | None:
    if not OPENAI_AVAILABLE:
        print("  UYARI: openai paketi yuklu degil.")
        return None

    if not config.OPENAI_API_KEY:
        print("  UYARI: OPENAI_API_KEY tanimli degil.")
        return None

    topic = post.get("topic", "")
    caption = post.get("caption", "")
    headline = post.get("design_headline") or topic
    subhead = post.get("design_subhead") or ""
    platform = post.get("platform", "Instagram")
    post_format = post.get("format", "")

    slide_suffix = f"_s{slide_index + 1}" if total_slides > 1 else ""
    filename = f"{slugify(week_label)}_{index:02d}_{slugify(topic)}{slide_suffix}.png"
    out_path = os.path.join(AI_IMAGES_DIR, filename)

    if os.path.exists(out_path):
        print(f"  Gorsel mevcut: {filename}")
        return out_path

    prompt = build_post_prompt(
        topic=topic,
        caption=caption,
        headline=headline,
        subhead=subhead,
        platform=platform,
        post_format=post_format,
        slide_index=slide_index,
        total_slides=total_slides,
        slide_content=slide_content,
    )

    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        slide_label = f" (Slide {slide_index+1}/{total_slides})" if total_slides > 1 else ""
        print(f"  GPT Image uretiliyor: {filename}{slide_label}...")

        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1536",
            quality="high",
            n=1,
        )

        image_data = response.data[0].b64_json
        if image_data:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            print(f"  Kaydedildi: {filename}")
            return out_path

        print("  UYARI: Gorsel verisi bos geldi.")
        return None

    except Exception as e:
        print(f"  UYARI: GPT Image hatasi: {e}")
        return None


def generate_all_images_for_post(
    post: dict,
    week_label: str,
    index: int,
) -> list[str]:
    post_format = post.get("format", "").lower()
    caption = post.get("caption", "")
    is_carousel = "carousel" in post_format or "dokuman" in post_format

    if not is_carousel:
        path = generate_post_image(post, week_label, index)
        return [path] if path else []

    slides_raw = caption.split("|")
    slides = [s.strip() for s in slides_raw if s.strip()]

    if len(slides) < 2:
        path = generate_post_image(post, week_label, index)
        return [path] if path else []

    total = min(len(slides), 6)
    paths = []
    for i, slide_text in enumerate(slides[:total]):
        path = generate_post_image(
            post=post,
            week_label=week_label,
            index=index,
            slide_index=i,
            total_slides=total,
            slide_content=slide_text,
        )
        if path:
            paths.append(path)

    return paths
