#!/usr/bin/env python3
"""
🔍 Gerçek veri durumu kontrolü
"""

import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

print("="*60)
print("📊 GERÇEK VERİ DURUMU KONTROLÜ")
print("="*60)

# URL kontrolü
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN url IS NOT NULL AND url != '' THEN 1 ELSE 0 END) as with_url,
           SUM(CASE WHEN url LIKE '%trendyol.com%' THEN 1 ELSE 0 END) as real_trendyol_url
    FROM products
""")
result = cursor.fetchone()
total, with_url, real_url = result

print(f"\n🛍️ ÜRÜN DURUMU:")
print(f"   Toplam ürün: {total}")
print(f"   URL'si olan: {with_url}")
print(f"   Gerçek Trendyol URL'si: {real_url}")

if real_url == 0:
    print("   ❌ HİÇ GERÇEK TRENDYOL URL'Sİ YOK - SİMÜLASYON VERİ!")
else:
    print(f"   ✅ {real_url} gerçek Trendyol ürünü var")

# Örnek URL'ler
print("\n📌 Örnek URL'ler:")
cursor.execute("SELECT name, url FROM products LIMIT 5")
for name, url in cursor.fetchall():
    if url:
        print(f"   • {name[:30]:32} → {url}")
    else:
        print(f"   • {name[:30]:32} → URL YOK ❌")

# Yorumlar kontrolü
cursor.execute("""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN scraped_at IS NOT NULL THEN 1 ELSE 0 END) as real_reviews
    FROM product_reviews
""")
total_reviews, real_reviews = cursor.fetchone()

print(f"\n💬 YORUM DURUMU:")
print(f"   Toplam yorum: {total_reviews}")
print(f"   Gerçek yorum (scraped_at var): {real_reviews}")
print(f"   Simülasyon yorum: {total_reviews - real_reviews}")

# SONUÇ
print("\n" + "="*60)
print("🎯 SONUÇ:")

if real_url == 0:
    print("❌ ŞU AN SİMÜLASYON VERİ KULLANIYOR!")
    print("   - Hiç gerçek Trendyol URL'si yok")
    print("   - Bu veriler test amaçlı oluşturulmuş")
    print("\n✅ ÇÖZÜM:")
    print("   1. GitHub Actions kurulumunu yap")
    print("   2. Otomatik scraping başlayacak")
    print("   3. Her 4 saatte gerçek veri eklenecek")
else:
    gerçek_oran = (real_url / total) * 100
    print(f"✅ %{gerçek_oran:.1f} GERÇEK VERİ")

print("\n📈 GITHUB ACTIONS İLE:")
print("   • İlk çalıştırmada +50-100 gerçek ürün")
print("   • Her 4 saatte +20-50 yeni ürün")
print("   • 1 haftada 500+ gerçek ürün")
print("   • Tamamen ücretsiz ve otomatik")
print("="*60)

conn.close()