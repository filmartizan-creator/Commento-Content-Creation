"""
run_weekly.py
=============
Tüm haftalık akışı çalıştırır:
1. Claude API ile yeni hafta içeriklerini üret (caption + tasarım talimatları)
2. Her içerik için tasarım görselini render et (Şablon A/B/C)
3. Google Sheets'e yeni satırlar olarak ekle

Kullanım:
    python scripts/run_weekly.py "Hafta 2"

GitHub Actions üzerinden haftalık otomatik çalıştırma için
.github/workflows/weekly_content.yml dosyasına bakın.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_content import generate_week_content
from scripts.generate_design import render_post, OUTPUT_DIR
from scripts.sync_sheets import sync_to_sheets
import json
import config


def main(week_label: str):
    print(f"=== {week_label} için içerik üretimi başlıyor ===")

    # 1. Önceki temaları yükle
    used_themes_path = os.path.join(os.path.dirname(__file__), "..", "data", "used_themes.json")
    used_themes = []
    if os.path.exists(used_themes_path):
        with open(used_themes_path) as f:
            used_themes = json.load(f)

    # 2. Caption + tasarım talimatlarını üret
    content = generate_week_content(week_label, used_themes)
    print(f"{len(content)} içerik üretildi.")

    # 3. Tasarımları render et
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for i, post in enumerate(content, start=1):
        out_path = render_post(post, i, week_label.replace(" ", "_"))
        if out_path:
            post["design_image_path"] = out_path
            print(f"[{i}] Görsel render edildi: {os.path.basename(out_path)}")

    # 4. content_*.json'ı kaydet
    content_path = os.path.join(
        os.path.dirname(__file__), "..", "data", f"content_{week_label.replace(' ', '_')}.json"
    )
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    # 5. Kullanılan temaları güncelle
    used_themes.extend([item["topic"] for item in content])
    with open(used_themes_path, "w", encoding="utf-8") as f:
        json.dump(used_themes, f, ensure_ascii=False, indent=2)

    # 6. Google Sheets'e senkronize et
    try:
        sync_to_sheets(content_path, week_label)
    except RuntimeError as e:
        print(f"UYARI: Sheets senkronizasyonu yapılamadı: {e}")
        print("İçerikler ve görseller yine de oluşturuldu, manuel olarak ekleyebilirsiniz.")

    print("=== Tamamlandı ===")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        week_label = sys.argv[1]
    else:
        # Otomatik hafta numarası: data/used_themes.json'daki kayıt sayısına göre
        week_label = f"Hafta {datetime.now().isocalendar()[1]}"

    main(week_label)
