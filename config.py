"""
Commento İçerik Otomasyon Sistemi — Konfigürasyon
====================================================
Bu dosya, sistemin genel ayarlarını içerir.
Hassas bilgiler (API key'ler) buraya YAZILMAZ — environment variable
olarak (.env dosyası veya GitHub Actions Secrets) sağlanır.
"""

import os

# ------------------------------------------------------------------
# API KEYS (environment variable'dan okunur — buraya asla yazmayın)
# ------------------------------------------------------------------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
GOOGLE_SHEETS_CREDENTIALS_JSON = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")  # service account JSON (string)
GOOGLE_SHEET_ID = os.environ.get("GOOGLE_SHEET_ID")  # Commento_Icerik_Takip_Tablosu sheet ID

# ------------------------------------------------------------------
# CLAUDE API
# ------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 4000

# ------------------------------------------------------------------
# PLATFORM AYARLARI
# ------------------------------------------------------------------
PLATFORMS = ["LinkedIn TR", "LinkedIn EN", "Twitter/X TR", "Twitter/X EN", "Instagram TR", "Instagram EN"]

# Her platform için kurumsal hesap paylaşım zamanları (gün, saat)
SCHEDULE = {
    "LinkedIn TR": [("Pazartesi", "10:00"), ("Çarşamba", "10:00")],
    "LinkedIn EN": [("Pazartesi", "16:00"), ("Çarşamba", "16:00")],
    "Twitter/X TR": [("Cuma", "12:30")],
    "Twitter/X EN": [("Cuma", "16:30")],
    "Instagram TR": [("Salı", "20:00")],
    "Instagram EN": [("Çarşamba", "16:00")],
}

# Founder kişisel hesap paylaşım zamanları
FOUNDER_SCHEDULE = {
    "LinkedIn TR": [("Salı", "09:00")],
    "LinkedIn EN": [("Salı", "15:00")],
    "Twitter/X TR": [("Perşembe", "11:00")],
    "Twitter/X EN": [("Perşembe", "17:00")],
}

# ------------------------------------------------------------------
# GOOGLE SHEETS SEKME ADLARI
# ------------------------------------------------------------------
SHEET_COMPANY = "Şirket Hesapları"
SHEET_FOUNDER = "Founder Paylaşımları"
SHEET_IDEAS = "İçerik Fikir Havuzu"

# ------------------------------------------------------------------
# TASARIM SİSTEMİ
# ------------------------------------------------------------------
DESIGN_OUTPUT_DIR = "output"
TEMPLATES_DIR = "templates"
ASSETS_DIR = "assets"

# Render boyutu (Instagram/LinkedIn 4:5 dikey post için)
RENDER_WIDTH = 1080
RENDER_HEIGHT = 1350
DEVICE_SCALE_FACTOR = 2  # retina kalite

# Şablon C için kullanılabilir ikon havuzu (assets/icons/*_white.png)
ICON_LIBRARY = {
    "kriz_yonetimi": ["radar_white.png", "siren_white.png", "shield-check_white.png"],
    "ai_moderasyon": ["brain-circuit_white.png", "shield-check_white.png", "activity_white.png"],
    "yorum_analizi": ["message-square-text_white.png", "scan-search_white.png", "trending-up_white.png"],
    "sentiment": ["message-circle-heart_white.png", "scan-search_white.png", "trending-up_white.png"],
    "multi_platform": ["layers_white.png", "users_white.png", "trending-up_white.png"],
    "genel": ["target_white.png", "clipboard-list_white.png", "trending-up_white.png"],
}

# Şablon B için 3D illüstrasyon havuzu (assets/illustrations/*.png)
# design_icon_category alanı bu anahtarlarla eşleşir (Şablon B seçildiğinde de kullanılır)
ILLUSTRATION_LIBRARY = {
    "kriz_yonetimi": "thinking_face.png",
    "ai_moderasyon": "light_bulb.png",
    "yorum_analizi": "magnifying_glass.png",
    "sentiment": "speech_balloon.png",
    "multi_platform": "bar_chart.png",
    "genel": "speech_balloon.png",
}
DEFAULT_ILLUSTRATION = "speech_balloon.png"
