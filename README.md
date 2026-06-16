# Commento İçerik Otomasyon Sistemi

Bu sistem her hafta otomatik olarak:
1. **Caption üretir** (LinkedIn TR/EN, Twitter/X TR/EN — şirket + founder hesapları)
2. **Tasarım görseli üretir** (3 şablon: A/B/C — markaya uygun)
3. **Google Sheets'e** "Commento_Icerik_Takip_Tablosu" dosyasına satır olarak ekler

---

## Klasör Yapısı

```
commento_design_system/
├── config.py                  # Genel ayarlar (saatler, ikon eşleştirmeleri vb.)
├── requirements.txt
├── templates/
│   ├── template_a.html        # Lavanta arka plan, kısa çarpıcı mesaj
│   ├── template_b.html         # Gradient + 3D illüstrasyon + balon (insan/duygu/fikir temalı)
│   └── template_c.html         # Koyu mavi, 3 ikonlu (karşılaştırma/liste)
├── assets/
│   ├── logo_blue.png / logo_white.png
│   ├── icons/                  # Lucide ikonları (beyaz, PNG) — Şablon C için
│   └── illustrations/          # 3D illüstrasyonlar — Şablon B için
├── scripts/
│   ├── generate_content.py     # Claude API ile caption üretimi
│   ├── generate_design.py      # HTML şablonları PNG'ye render eder
│   ├── sync_sheets.py           # Google Sheets'e satır ekler
│   └── run_weekly.py            # Hepsini sırayla çalıştırır (ana script)
├── data/                        # Üretilen content_*.json + used_themes.json
├── output/                      # Render edilmiş PNG'ler
└── .github/workflows/
    └── weekly_content.yml       # Her Pazar otomatik çalıştırma
```

---

## Kurulum (tek seferlik)

### 1. Bu klasörü bir GitHub repo'suna yükleyin
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <repo-url>
git push -u origin main
```

### 2. Anthropic API Key
- https://console.anthropic.com → API Keys → yeni key oluşturun
- GitHub repo → Settings → Secrets and variables → Actions → New repository secret
  - Name: `ANTHROPIC_API_KEY`
  - Value: `sk-ant-...`

### 3. Google Sheets Servis Hesabı
1. [Google Cloud Console](https://console.cloud.google.com) → yeni proje oluşturun
2. **Sheets API** ve **Drive API**'yi etkinleştirin
3. "IAM & Admin" → "Service Accounts" → yeni servis hesabı oluşturun
4. Bu hesap için bir **JSON key** indirin
5. "Commento_Icerik_Takip_Tablosu" Google Sheets dosyasını açın → **Paylaş** →
   servis hesabının e-posta adresini (örn. `commento-bot@proje.iam.gserviceaccount.com`)
   **Editor** olarak ekleyin
6. Sheet URL'sindeki ID'yi kopyalayın:
   `https://docs.google.com/spreadsheets/d/`**`BU_KISIM`**`/edit`

GitHub Secrets'a ekleyin:
  - `GOOGLE_SHEETS_CREDENTIALS_JSON`: indirdiğiniz JSON dosyasının **tüm içeriği** (tek satır, string olarak)
  - `GOOGLE_SHEET_ID`: yukarıdaki ID

---

## Otomatik Çalışma

`.github/workflows/weekly_content.yml` her **Pazar 18:00 UTC** (Türkiye saatiyle 21:00)
otomatik çalışır:
1. Yeni hafta için 12 içerik üretir (8 şirket + 4 founder)
2. Görselleri render eder
3. Google Sheets'e ekler
4. Üretilen JSON + PNG'leri repo'ya commit eder

## Manuel Çalıştırma

GitHub repo → **Actions** sekmesi → "Haftalık Commento İçerik Üretimi" →
**Run workflow** → istersen özel bir hafta etiketi yazıp çalıştırabilirsin.

Yerel makinede çalıştırmak için:
```bash
pip install -r requirements.txt
playwright install chromium

export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_SHEETS_CREDENTIALS_JSON='{"type": "service_account", ...}'
export GOOGLE_SHEET_ID="1mUfu3Gbaj..."

python scripts/run_weekly.py "Hafta 3"
```

---

## Haftalık İş Akışı (Deniz/Mina için)

1. Sistem Pazar akşamı otomatik çalışır
2. Pazartesi sabahı Google Sheets'i açın → "Şirket Hesapları" ve
   "Founder Paylaşımları" sekmelerinde "Üretildi" statüsünde yeni satırlar görürsünüz
3. `output/` klasöründeki PNG'leri (veya GitHub Actions çıktısından) indirin
4. Captionları gözden geçirin, gerekirse küçük düzenleme yapın
5. "Sorumlu" sütununu doldurun, paylaştıktan sonra "Durum"u "Paylaşıldı" yapın

---

## Şablonları Güncelleme

- Renkleri/fontları değiştirmek için `templates/template_*.html` içindeki
  `:root` CSS değişkenlerini düzenleyin
- Yeni ikon eklemek için `assets/icons/` klasörüne `*_white.png` ekleyin ve
  `config.py` → `ICON_LIBRARY` içine kaydedin
- İçerik üretim kurallarını (ton, yasaklı temalar vb.) değiştirmek için
  `scripts/generate_content.py` → `SYSTEM_PROMPT` düzenleyin
