"""
generate_content.py
====================
Claude API kullanarak haftalik icerik (caption + tasarim talimatlari) uretir.

Claude'dan NDJSON formatinda cevap istenir (her satirda bir JSON nesnesi).
Bu format buyuk JSON array'lere kiyasla parse hatalarina karsi cok daha
dayaniklidir: bir satir bozuksa diger satirlar etkilenmez.
"""

import json
import os
import sys
from datetime import datetime

import anthropic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


SYSTEM_PROMPT = """Sen Commento adli bir B2B SaaS urununun icerik stratejistisin.

URUN: Commento, markalarin sosyal medya yorumlarini (Instagram, Facebook, YouTube vb.)
AI ile analiz eden, sentiment/niyet/aciliyet cikaran, kriz sinyallerini erken yakalayan
ve moderasyonu otomatiklestiren bir araçtir.

KESIN KURALLAR:
1. Icerikler Commento'nun GERCEK deger onerisiyle (yorum analizi, sentiment anlama,
   kriz erken sinyalleri, AI moderasyon, multi-platform birlestirme) baglantili olmali.
   "Yanit hizi" gibi markaya bagli, urunle dogrudan iliskisi olmayan temalardan KACIN.
2. Sirket hesaplari (LinkedIn TR/EN, Twitter/X TR/EN) icin: profesyonel, veri/icgoru
   temelli, "neden onemli" anlatan icerikler.
3. Founder hesabi icin: "build in public" tonunda, kisisel gozlem/ogrenme paylasimlari,
   daha samimi ve ilk sahis.
4. Her icerik icin SEO uyumlu, platforma ozgu hashtag seti ekle (LinkedIn: 5-6, Twitter: 2-3).
5. EN ve TR versiyonlar ayni konsepti tasimali ama birebir ceviri olmamali, dogal olmali.
6. design_template alani:
   - "A": Kisa, carpici tek mesaj (lavanta arka plan, buyuk baslik + alt metin)
   - "B": Insan/duygu/fikir temali icerik (gradient + 3D illustrasyon + balon)
   - "C": Coklu nokta/karsilastirma iceren icerik (koyu mavi, 3 ikonlu)
   - Twitter thread'ler ve founder kisisel postlar icin design_template: null
7. design_icon_category sadece template "B" veya "C" secildiginde doldurulmali,
   su degerlerden biri: kriz_yonetimi, ai_moderasyon, yorum_analizi, sentiment,
   multi_platform, genel

CIKTI FORMATI - COK ONEMLI:
Her icerik icin TEK SATIRDA, gecerli bir JSON nesnesi yaz (NDJSON / JSON Lines formati).
Toplam 14 satir olacak. Satirlar arasinda bos satir OLMASIN.
Markdown, aciklama, baslik, numara EKLEME. Sadece 12 satir JSON, baska hicbir sey yok.
Her JSON nesnesindeki string degerlerde gercek satir sonu (newline) KARAKTERI KULLANMA -
caption icindeki paragraf araları icin "\\n\\n" (escaped) kullan, asla literal enter tusu kullanma.
Her nesne tek satira sigmali.

Her satirdaki JSON nesnesi su alanlari icermeli:
platform, account_type, format, topic, caption, hashtags, design_template,
design_headline, design_subhead, design_icon_category
"""


def build_user_prompt(week_label: str, used_themes: list[str]) -> str:
    used_themes_str = "\n".join(f"- {t}" for t in used_themes) if used_themes else "(yok)"
    return f"""
Hafta etiketi: {week_label}

Daha once kullanilmis temalar (TEKRAR ETME):
{used_themes_str}

Asagidaki icerikleri uret, her biri icin TEK SATIRLIK bir JSON nesnesi yaz:

SIRKET HESAPLARI (8 post, account_type="company"):
1. LinkedIn TR - Metin Postu
2. LinkedIn EN - Metin Postu (1 ile ayni konsept)
3. LinkedIn TR - Carousel/Dokuman (caption alaninda "Slide 1: ... | Slide 2: ..." formatinda, pipe ile ayirarak yaz)
4. LinkedIn EN - Carousel/Dokuman (3 ile ayni konsept)
5. Twitter/X TR - Metin Postu
6. Twitter/X EN - 5 ile ayni konsept
7. Twitter/X TR - Thread (caption alaninda "1/ ... | 2/ ..." formatinda, pipe ile ayirarak yaz, farkli konu)
8. Twitter/X EN - 7 ile ayni konsept

FOUNDER PAYLASIMLARI (4 post, account_type="founder"):
9. LinkedIn TR - build-in-public tonunda
10. LinkedIn EN - 9 ile ayni konsept
11. Twitter/X TR - kisa gozlem
12. Twitter/X EN - 11 ile ayni konsept

INSTAGRAM (2 post, account_type="company"):
13. Instagram TR - kisa, carpici, gorsel agirlikli caption (design_template "A" veya "B" olsun)
14. Instagram EN - 13 ile ayni konsept

14 satir JSON ciktisi ver. Baska hicbir metin ekleme.
"""


def generate_week_content(week_label: str, used_themes: list[str] | None = None) -> list[dict]:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable tanimli degil.")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=config.CLAUDE_MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[
            {"role": "user", "content": build_user_prompt(week_label, used_themes or [])}
        ],
    )

    raw_text = "".join(block.text for block in message.content if block.type == "text")
    raw_text = raw_text.strip()

    # Olasi markdown code fence'leri temizle
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        raw_text = "\n".join(lines)

    results = []
    errors = []
    for i, line in enumerate(raw_text.split("\n"), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line, strict=False)
            results.append(obj)
        except json.JSONDecodeError as e:
            errors.append(f"  Satir {i}: {e} -- icerik: {line[:120]}")

    if not results:
        raise RuntimeError(
            "Claude'dan hicbir gecerli JSON satiri alinamadi.\n"
            "Hatalar:\n" + "\n".join(errors) + "\n\nHam cevap:\n" + raw_text[:1000]
        )

    if errors:
        print(f"UYARI: {len(errors)} satir parse edilemedi, {len(results)} icerik basariyla alindi.")
        for err in errors:
            print(err)

    return results


if __name__ == "__main__":
    week_label = sys.argv[1] if len(sys.argv) > 1 else f"Hafta - {datetime.now().strftime('%Y-%m-%d')}"

    used_themes_path = os.path.join(os.path.dirname(__file__), "..", "data", "used_themes.json")
    used_themes = []
    if os.path.exists(used_themes_path):
        with open(used_themes_path) as f:
            used_themes = json.load(f)

    content = generate_week_content(week_label, used_themes)

    out_path = os.path.join(os.path.dirname(__file__), "..", "data", f"content_{week_label.replace(' ', '_')}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    new_themes = [item.get("topic", "") for item in content]
    used_themes.extend(new_themes)
    with open(used_themes_path, "w", encoding="utf-8") as f:
        json.dump(used_themes, f, ensure_ascii=False, indent=2)

    print(f"Uretildi: {out_path}")
    print(f"{len(content)} icerik olusturuldu.")
