#!/bin/bash

# GitHub Actions için otomatik kurulum scripti

echo "🚀 GitHub Actions Otomasyonu Kuruluyor..."
echo "="*60

# 1. Git repository oluştur
if [ ! -d .git ]; then
    git init
    echo "✅ Git repository oluşturuldu"
fi

# 2. .gitignore oluştur
cat > .gitignore << EOF
__pycache__/
*.pyc
.env
venv/
*.log
.DS_Store
EOF
echo "✅ .gitignore oluşturuldu"

# 3. requirements.txt oluştur
cat > requirements.txt << EOF
selenium==4.15.0
undetected-chromedriver==3.5.3
beautifulsoup4==4.12.2
requests==2.31.0
pandas==2.1.3
cloudscraper==1.2.71
httpx[http2]==0.25.1
fake-useragent==1.4.0
streamlit==1.28.2
plotly==5.18.0
EOF
echo "✅ requirements.txt oluşturuldu"

# 4. README oluştur
cat > README.md << EOF
# 🛍️ Trendyol Market Spider

Otomatik Trendyol veri toplama sistemi. GitHub Actions ile her 4 saatte bir çalışır.

## 🚀 Özellikler
- ✅ Gerçek Trendyol verisi
- ✅ Otomatik güncelleme
- ✅ Tamamen ücretsiz
- ✅ Cloudflare bypass

## 📊 Veri Görüntüleme
\`\`\`bash
python3 -m streamlit run dashboard.py
\`\`\`

## 📈 İstatistikler
Sistem her çalıştığında yeni ürünler ekler.
EOF
echo "✅ README.md oluşturuldu"

# 5. İlk commit
git add .
git commit -m "🎉 Initial commit - Trendyol scraping system"
echo "✅ İlk commit yapıldı"

echo ""
echo "="*60
echo "📋 ŞİMDİ YAPMAN GEREKENLER:"
echo "="*60
echo ""
echo "1️⃣ GitHub.com'a giriş yap"
echo "2️⃣ 'New repository' butonuna tıkla"
echo "3️⃣ Repository adı: market-spider"
echo "4️⃣ PUBLIC seç (önemli!)"
echo "5️⃣ Create repository tıkla"
echo ""
echo "6️⃣ Sonra bu komutları çalıştır:"
echo ""
echo "git remote add origin https://github.com/[KULLANICI_ADIN]/market-spider.git"
echo "git branch -M main"
echo "git push -u origin main"
echo ""
echo "7️⃣ GitHub'da Actions sekmesine git"
echo "8️⃣ 'Run workflow' butonuna tıkla"
echo ""
echo "🎯 SİSTEM OTOMATİK ÇALIŞMAYA BAŞLAYACAK!"
echo "   Her 4 saatte Trendyol'dan veri çekecek"
echo "   Hiç müdahale gerekmez!"
echo "="*60