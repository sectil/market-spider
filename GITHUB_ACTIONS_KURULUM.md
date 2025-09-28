# 🚀 GitHub Actions ile Ücretsiz ve Kalıcı Trendyol Veri Toplama

## 🎯 Amaç
Simülasyon değil, **GERÇEK** Trendyol verilerini otomatik olarak toplamak için ücretsiz ve kalıcı bir sistem.

## ✨ Özellikler
- ✅ **Tamamen Ücretsiz** - GitHub Actions free tier kullanır
- ✅ **Otomatik** - Her 4 saatte bir çalışır
- ✅ **Gerçek Veri** - Simülasyon YOK, sadece Trendyol'dan gerçek veri
- ✅ **Cloudflare Bypass** - Undetected ChromeDriver kullanır
- ✅ **Yedekli** - Birden fazla scraping yöntemi
- ✅ **Raporlama** - HTML ve JSON formatında detaylı raporlar

## 📋 Kurulum Adımları

### 1️⃣ GitHub Repository Oluşturma
```bash
# Yeni bir public repository oluştur (Private repo'da Actions limiti var)
# Repository adı: market-spider-automation
```

### 2️⃣ Dosyaları Yükleme
```bash
# Bu projideki tüm dosyaları GitHub'a yükle
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/[KULLANICI_ADINIZ]/market-spider-automation.git
git push -u origin main
```

### 3️⃣ GitHub Actions'ı Aktifleştirme
1. GitHub repository sayfasına git
2. "Settings" → "Actions" → "General" sekmesine git
3. "Actions permissions" bölümünde "Allow all actions" seç
4. Kaydet

### 4️⃣ İlk Çalıştırma
```bash
# Manuel tetikleme (test için)
# GitHub repository'de:
# Actions → Advanced Trendyol Data Scraper → Run workflow
```

## 🔄 Otomatik Çalışma Zamanları
```yaml
schedule:
  - cron: '0 */4 * * *'  # Her 4 saatte bir
```

Değiştirmek için:
- `0 */6 * * *` - Her 6 saatte bir
- `0 0,12 * * *` - Günde 2 kez (00:00 ve 12:00)
- `0 0 * * *` - Günde 1 kez (gece yarısı)

## 📊 Veri Erişimi

### Otomatik Güncellenen Dosyalar
- `market_spider.db` - SQLite veritabanı
- `scraped_products.csv` - Excel'de açılabilir CSV
- `scraping_report.html` - Görsel rapor
- `data_quality_report.json` - Veri kalite metrikleri

### Verileri İndirme
1. GitHub Actions → Son workflow çalışması
2. "Artifacts" bölümü
3. `trendyol-data-XX.zip` dosyasını indir

## 🛠️ Özelleştirme

### Kategori Ekleme
`.github/workflows/advanced_trendyol_scraper.yml` dosyasında:
```yaml
categories:
  default: 'cok-satanlar,elektronik,moda,kozmetik,spor,oyuncak'
```

### Ürün Sayısı Artırma
`github_advanced_scraper.py` dosyasında:
```python
for p in product_data[:100]:  # 50'den 100'e çıkar
```

## 🔍 Veri Doğrulama
```bash
# Lokal test
python3 verify_scraped_data.py

# Beklenen sonuç:
# ✅ Gerçek URL oranı: >80%
# ✅ Gerçek yorum oranı: >50%
# ✅ Veri kalitesi: KABUL EDİLEBİLİR
```

## 🚨 Sorun Giderme

### "403 Forbidden" Hatası
- Normal, Cloudflare koruması
- Sistem otomatik olarak alternatif yöntemleri dener

### "No products found" Hatası
- API endpoint'leri değişmiş olabilir
- `api_endpoint_scraper.py` dosyasındaki URL'leri güncelle

### Actions Çalışmıyor
- Repository public mi kontrol et
- Actions permissions kontrol et
- GitHub Free limit (2000 dakika/ay) aşılmamış mı kontrol et

## 📈 Başarı Metrikleri
- ✅ En az 50 gerçek ürün
- ✅ En az 100 gerçek yorum
- ✅ %80+ gerçek veri oranı
- ✅ 5+ farklı kategori
- ✅ 10+ farklı marka

## 🆓 Alternatif Ücretsiz Yöntemler

### 1. Render.com (Scheduled Jobs)
```python
# render.yaml
services:
  - type: cron
    name: trendyol-scraper
    schedule: "0 */6 * * *"
    buildCommand: pip install -r requirements.txt
    startCommand: python github_advanced_scraper.py
```

### 2. Railway.app (Free Tier)
```bash
railway login
railway init
railway add
railway up
```

### 3. Google Colab (Notebook)
```python
# Colab'da zamanlı çalıştırma
!pip install selenium undetected-chromedriver
!python github_advanced_scraper.py
```

### 4. Replit (Scheduled Repls)
- Replit.com'da hesap aç
- Python repl oluştur
- Always On özelliğini aktifle (ücretsiz)

## ✅ Kontrol Listesi
- [ ] GitHub repository oluşturuldu
- [ ] Dosyalar yüklendi
- [ ] Actions aktifleştirildi
- [ ] İlk workflow çalıştı
- [ ] Veri kalitesi doğrulandı
- [ ] Otomatik schedule ayarlandı

## 📞 Destek
Sorun yaşarsanız:
1. Actions loglarını kontrol et
2. `logs/` klasöründeki log dosyalarını incele
3. `verify_scraped_data.py` çalıştır
4. Issue aç: github.com/[username]/market-spider-automation/issues

---

**NOT:** Bu sistem tamamen yasal web scraping yöntemleri kullanır. Trendyol'un robots.txt kurallarına uyar ve rate limiting uygular.