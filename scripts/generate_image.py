"""
generate_image.py
==================
OpenAI gpt-image-1 kullanarak Sablon B icin arka plan/atmosfer gorseli uretir.
Uretilen gorsel assets/ai_generated/ klasorune kaydedilir.

Her gorsel icin konu bazli bir prompt olusturulur:
- Markanin renk paleti ve stili prompt'a dahil edilir
- Gorsel sonra HTML sablonumuzun ILLUSTRATION alanina yerlestirilir
- Uzerine logo, balon, baslik bizim sistemimiz cizer
"""

import base64
import os
import re
import sys
import time

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AI_IMAGES_DIR = os.path.join(BASE_DIR, "assets", "ai_generated")


STYLE_GUIDE = """
3D render, high quality, professional, minimalist.
Color palette: deep navy blue (#1B2A8F), medium blue (#4D5DDB), 
light lavender (#E7E9FB), white accents.
Style: clean, modern B2B SaaS aesthetic. 
NO text, NO letters, NO words in the image.
Square composition 1:1, centered subject.
Soft shadows, subtle depth, premium feel.
"""


TOPIC_PROMPTS = {
    "kriz_yonetimi": "A glowing radar screen with ripple signals emanating outward, detecting invisible threats. Deep blue tones, futuristic, 3D render.",
    "ai_moderasyon": "A sleek AI brain made of interconnected light nodes, filtering and sorting streams of data. Blue and lavender tones, 3D render.",
    "yorum_analizi": "A magnifying glass over a stream of floating speech bubbles, each bubble containing subtle emotion indicators. Navy blue, 3D render.",
    "sentiment": "Abstract human silhouette made of speech bubbles, radiating warmth and emotion. Blue to lavender gradient, 3D render.",
    "multi_platform": "Multiple social media platform icons connected by elegant light streams into a single central hub. Deep blue, 3D render.",
    "genel": "An elegant 3D speech bubble made of glass/crystal, floating in a deep blue space with subtle light reflections.",
    "kriz": "A calm eye of a storm made of swirling social media icons. Deep navy blue, dramatic lighting, 3D render.",
    "veri": "Abstract floating data nodes and connections forming a constellation pattern. Blue lavender tones, 3D render.",
    "musteri": "A warm glowing customer profile icon surrounded by orbiting speech bubbles showing satisfaction signals. Blue tones, 3D render.",
    "otomasyon": "Elegant robotic hands gently cradling a stream of social media comments. Navy blue, premium 3D render.",
}

DEFAULT_PROMPT = TOPIC_PROMPTS["genel"]


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    return re.sub(r"[\s_-]+", "-", text)[:40]


def get_image_prompt(topic: str, headline: str) -> str:
    topic_lower = (topic or "").lower()
    for key in TOPIC_PROMPTS:
        if key in topic_lower:
            base = TOPIC_PROMPTS[key]
            break
    else:
        base = DEFAULT_PROMPT

    return f"{base}\n{STYLE_GUIDE}"


def generate_ai_image(topic: str, headline: str, week_label: str, index: int) -> str | None:
    if not OPENAI_AVAILABLE:
        print("UYARI: openai paketi yuklu degil, AI gorsel atlanıyor.")
        return None

    api_key = config.OPENAI_API_KEY
    if not api_key:
        print("UYARI: OPENAI_API_KEY tanimli degil, AI gorsel atlaniyor.")
        return None

    prompt = get_image_prompt(topic, headline)
    filename = f"{slugify(week_label)}_{index:02d}_{slugify(topic or 'gorsel')}.png"
    out_path = os.path.join(AI_IMAGES_DIR, filename)

    if os.path.exists(out_path):
        print(f"  AI gorsel zaten mevcut: {filename}")
        return out_path

    try:
        client = OpenAI(api_key=api_key)
        print(f"  AI gorsel uretiliyor: {filename}...")

        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )

        image_data = response.data[0].b64_json
        if image_data:
            with open(out_path, "wb") as f:
                f.write(base64.b64decode(image_data))
            print(f"  AI gorsel kaydedildi: {filename}")
            return out_path

        print("  UYARI: AI gorsel verisi bos geldi.")
        return None

    except Exception as e:
        print(f"  UYARI: AI gorsel uretimi basarisiz: {e}")
        return None
