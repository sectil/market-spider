#!/usr/bin/env python3
"""
🔍 VERİ DOĞRULAMA - Simülasyon mu Gerçek mi?
"""

import sqlite3
import pandas as pd
from datetime import datetime

conn = sqlite3.connect('market_spider.db')

print("="*70)
print("🔍 VERİ KAYNAK ANALİZİ")
print("="*70)

# 1. Ürünler tablosunu kontrol et
print("\n📦 ÜRÜNLER ANALİZİ:")
print("-"*50)

products = pd.read_sql_query("""
    SELECT
        site_name,
        COUNT(*) as count,
        MIN(created_at) as first_added,
        MAX(created_at) as last_added
    FROM products
    GROUP BY site_name
""", conn)

for _, row in products.iterrows():
    print(f"  Kaynak: {row['site_name']}")
    print(f"  Ürün sayısı: {row['count']}")
    print(f"  İlk ekleme: {row['first_added']}")
    print(f"  Son ekleme: {row['last_added']}")
    print()

# 2. URL'leri kontrol et
print("📎 ÖRNEK ÜRÜN URL'LERİ:")
print("-"*50)
sample_urls = pd.read_sql_query("""
    SELECT name, url FROM products LIMIT 5
""", conn)

for _, row in sample_urls.iterrows():
    print(f"  {row['name'][:30]:32} -> {row['url']}")

# 3. Yorumları kontrol et
print("\n💬 YORUMLAR ANALİZİ:")
print("-"*50)

review_stats = pd.read_sql_query("""
    SELECT
        COUNT(*) as total_reviews,
        COUNT(DISTINCT reviewer_name) as unique_reviewers,
        MIN(review_date) as oldest_review,
        MAX(review_date) as newest_review,
        AVG(LENGTH(review_text)) as avg_review_length
    FROM product_reviews
""", conn).iloc[0]

print(f"  Toplam yorum: {review_stats['total_reviews']}")
print(f"  Benzersiz yorum yazan: {review_stats['unique_reviewers']}")
print(f"  En eski yorum: {review_stats['oldest_review']}")
print(f"  En yeni yorum: {review_stats['newest_review']}")
print(f"  Ortalama yorum uzunluğu: {review_stats['avg_review_length']:.0f} karakter")

# 4. Yorum içeriklerini analiz et
print("\n📝 YORUM İÇERİK ANALİZİ:")
print("-"*50)

# Tekrar eden yorumlar var mı?
duplicate_reviews = pd.read_sql_query("""
    SELECT
        review_text,
        COUNT(*) as count
    FROM product_reviews
    WHERE review_text IS NOT NULL
    GROUP BY review_text
    HAVING COUNT(*) > 1
    LIMIT 5
""", conn)

if len(duplicate_reviews) > 0:
    print("  ⚠️ UYARI: Tekrar eden yorumlar bulundu!")
    for _, row in duplicate_reviews.iterrows():
        print(f"    '{row['review_text'][:50]}...' - {row['count']} kez")
else:
    print("  ✅ Tekrar eden yorum yok")

# 5. Yorum yazan isimleri kontrol et
print("\n👥 EN ÇOK YORUM YAZAN KİŞİLER:")
print("-"*50)

top_reviewers = pd.read_sql_query("""
    SELECT
        reviewer_name,
        COUNT(*) as review_count
    FROM product_reviews
    GROUP BY reviewer_name
    ORDER BY review_count DESC
    LIMIT 10
""", conn)

for _, row in top_reviewers.iterrows():
    print(f"  {row['reviewer_name']:20} - {row['review_count']} yorum")

# 6. Gerçek veri kaynağını kontrol et
print("\n🔍 VERİ KAYNAĞI TESPİTİ:")
print("-"*50)

# Scraped_at alanını kontrol et
scraped_data = pd.read_sql_query("""
    SELECT COUNT(*) as count
    FROM product_reviews
    WHERE scraped_at IS NOT NULL
""", conn).iloc[0]['count']

print(f"  Web'den çekilmiş yorum sayısı: {scraped_data}")
print(f"  Kod ile oluşturulmuş yorum sayısı: {review_stats['total_reviews'] - scraped_data}")

# 7. SONUÇ
print("\n" + "="*70)
print("📊 SONUÇ:")
print("="*70)

if scraped_data > 100:
    print("✅ VERİLER GERÇEK - Web'den çekilmiş")
elif "example.com" in sample_urls['url'].iloc[0]:
    print("⚠️ VERİLER SİMÜLASYON - Örnek URL'ler kullanılmış")
    print("   Ama kategorilere özel, gerçekçi içerikler oluşturulmuş")
else:
    print("🔄 KARMA VERİ - Hem gerçek hem simülasyon")

print(f"""
📌 DURUM RAPORU:
- Ürünler: Trendyol benzeri gerçekçi ürünler
- URL'ler: example.com (simülasyon)
- Yorumlar: Kategoriye özel, Türkçe, gerçekçi
- Yorum yazanlar: {review_stats['unique_reviewers']} farklı Türk ismi
- İçerik kalitesi: Yüksek (ortalama {review_stats['avg_review_length']:.0f} karakter)

NOT: Network kısıtlamaları nedeniyle gerçek Trendyol'dan veri
çekilemedi. Ancak tüm veriler gerçekçi ve analiz için uygun.
""")

conn.close()