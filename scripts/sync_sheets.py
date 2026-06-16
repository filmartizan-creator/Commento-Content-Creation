"""
sync_sheets.py
===============
content_*.json içeriğini Google Sheets'teki "Commento_Icerik_Takip_Tablosu"
dosyasının ilgili sekmelerine yeni satırlar olarak ekler.

Gereksinim: bir Google Cloud servis hesabı (Sheets API + Drive API açık),
JSON credentials, ve sheet'in bu servis hesabıyla "Editor" olarak paylaşılmış olması.
"""

import json
import os
import sys

import gspread
from google.oauth2.service_account import Credentials

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def get_client() -> gspread.Client:
    if not config.GOOGLE_SHEETS_CREDENTIALS_JSON:
        raise RuntimeError("GOOGLE_SHEETS_CREDENTIALS_JSON environment variable tanımlı değil.")

    print(f"DEBUG: credentials uzunluk = {len(config.GOOGLE_SHEETS_CREDENTIALS_JSON or '')}")
    creds_dict = json.loads(config.GOOGLE_SHEETS_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def find_schedule(platform: str, account_type: str, slot_index: int) -> tuple[str, str]:
    schedule_map = config.SCHEDULE if account_type == "company" else config.FOUNDER_SCHEDULE
    slots = schedule_map.get(platform, [("", "")])
    return slots[slot_index % len(slots)]


def sync_to_sheets(content_path: str, week_label: str):
    client = get_client()
    sheet = client.open_by_key(config.GOOGLE_SHEET_ID)

    with open(content_path, encoding="utf-8") as f:
        posts = json.load(f)

    company_ws = sheet.worksheet(config.SHEET_COMPANY)
    founder_ws = sheet.worksheet(config.SHEET_FOUNDER)

    company_rows = []
    founder_rows = []

    slot_counters = {}

    for idx, post in enumerate(posts, start=1):
        platform = post.get("platform", "")
        account_type = post.get("account_type", "company")

        key = (platform, account_type)
        slot_idx = slot_counters.get(key, 0)
        slot_counters[key] = slot_idx + 1
        day, time = find_schedule(platform, account_type, slot_idx)

        caption_full = post.get("caption", "")
        hashtags = post.get("hashtags", "")
        if isinstance(hashtags, list):
            hashtags = " ".join(hashtags)
        design_path = post.get("design_image_path", "")
        note = f"Otomatik üretildi ({week_label})"
        if design_path:
            note += f" | Görsel: {os.path.basename(design_path)}"

        if account_type == "company":
            row = [
                str(len(company_rows) + 1),  # No
                week_label,                   # Hafta
                platform,
                post.get("format", ""),
                post.get("topic", ""),
                caption_full,
                hashtags,
                day,
                time,
                "",          # Sorumlu - manuel atanacak
                "Üretildi",  # Durum
                note,
            ]
            company_rows.append(row)
        else:
            row = [
                str(len(founder_rows) + 1),
                week_label,
                platform,
                post.get("format", ""),
                post.get("topic", ""),
                caption_full,
                hashtags,
                day,
                time,
                "Üretildi",
                note,
            ]
            founder_rows.append(row)

    if company_rows:
        company_ws.append_rows(company_rows, value_input_option="USER_ENTERED")
        print(f"{len(company_rows)} satır 'Şirket Hesapları' sekmesine eklendi.")

    if founder_rows:
        founder_ws.append_rows(founder_rows, value_input_option="USER_ENTERED")
        print(f"{len(founder_rows)} satır 'Founder Paylaşımları' sekmesine eklendi.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Kullanım: python sync_sheets.py data/content_<hafta>.json")
        sys.exit(1)

    content_path = sys.argv[1]
    week_label = os.path.basename(content_path).replace("content_", "").replace(".json", "")
    sync_to_sheets(content_path, week_label)
