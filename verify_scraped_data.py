#!/usr/bin/env python3
"""
✅ Scraped Data Doğrulama Scripti
Gerçek veri mi simülasyon mu kontrol eder
"""

import sqlite3
import json
from datetime import datetime
import sys

def verify_data_quality():
    """Veri kalitesini doğrula"""
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*60)
    print("🔍 VERİ KALİTE KONTROLÜ")
    print("="*60)

    # Test kriterleri
    tests = {
        'passed': [],
        'failed': []
    }

    # 1. Gerçek URL kontrolü
    print("\n1️⃣ URL Kontrolü:")
    cursor.execute("""
        SELECT COUNT(*) FROM products
        WHERE url IS NOT NULL
        AND url != ''
        AND url LIKE '%trendyol.com%'
        AND url NOT LIKE '%example.com%'
    """)
    real_urls = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    if total_products > 0:
        url_ratio = (real_urls / total_products) * 100
        print(f"   Gerçek URL oranı: {url_ratio:.1f}% ({real_urls}/{total_products})")
        if url_ratio > 80:
            tests['passed'].append("URL kontrolü")
        else:
            tests['failed'].append(f"URL kontrolü ({url_ratio:.1f}%)")
    else:
        print("   ❌ Hiç ürün yok!")
        tests['failed'].append("Ürün kontrolü")

    # 2. Fiyat kontrolü
    print("\n2️⃣ Fiyat Kontrolü:")
    cursor.execute("""
        SELECT COUNT(*) FROM products
        WHERE price > 0 AND price < 1000000
    """)
    valid_prices = cursor.fetchone()[0]

    if total_products > 0:
        price_ratio = (valid_prices / total_products) * 100
        print(f"   Geçerli fiyat oranı: {price_ratio:.1f}% ({valid_prices}/{total_products})")
        if price_ratio > 90:
            tests['passed'].append("Fiyat kontrolü")
        else:
            tests['failed'].append(f"Fiyat kontrolü ({price_ratio:.1f}%)")

    # 3. Marka kontrolü
    print("\n3️⃣ Marka Kontrolü:")
    cursor.execute("""
        SELECT brand, COUNT(*) as count
        FROM products
        WHERE brand IS NOT NULL AND brand != ''
        GROUP BY brand
        ORDER BY count DESC
        LIMIT 10
    """)
    brands = cursor.fetchall()

    if brands:
        print("   En çok bulunan markalar:")
        for brand, count in brands[:5]:
            print(f"      • {brand}: {count} ürün")

        # Bilinen Trendyol markaları
        known_brands = ['Samsung', 'Apple', 'Adidas', 'Nike', 'LCWaikiki', 'Koton', 'Mavi', 'Philips', 'Bosch', 'Arçelik']
        found_known = sum(1 for b, _ in brands if any(k.lower() in b.lower() for k in known_brands))

        if found_known > 0:
            tests['passed'].append("Marka kontrolü")
            print(f"   ✅ {found_known} bilinen marka bulundu")
        else:
            tests['failed'].append("Marka kontrolü")
            print("   ❌ Bilinen marka bulunamadı")

    # 4. Yorum kontrolü
    print("\n4️⃣ Yorum Kontrolü:")
    cursor.execute("""
        SELECT COUNT(*) FROM product_reviews
        WHERE scraped_at IS NOT NULL
    """)
    real_reviews = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM product_reviews")
    total_reviews = cursor.fetchone()[0]

    if total_reviews > 0:
        review_ratio = (real_reviews / total_reviews) * 100
        print(f"   Gerçek yorum oranı: {review_ratio:.1f}% ({real_reviews}/{total_reviews})")
        if review_ratio > 50:
            tests['passed'].append("Yorum kontrolü")
        else:
            tests['failed'].append(f"Yorum kontrolü ({review_ratio:.1f}%)")

        # Yorum içerik analizi
        cursor.execute("""
            SELECT review_text FROM product_reviews
            WHERE scraped_at IS NOT NULL
            LIMIT 100
        """)
        reviews = cursor.fetchall()

        # Simülasyon pattern'leri
        sim_patterns = ['harika ürün', 'süper kalite', 'çok memnunum', 'tavsiye ederim']
        sim_count = sum(1 for r in reviews if any(p in r[0].lower() for p in sim_patterns))

        if reviews:
            sim_ratio = (sim_count / len(reviews)) * 100
            print(f"   Şablon yorum oranı: {sim_ratio:.1f}%")
            if sim_ratio < 30:
                tests['passed'].append("Yorum özgünlük kontrolü")
            else:
                tests['failed'].append(f"Yorum özgünlük kontrolü ({sim_ratio:.1f}%)")

    # 5. Tarih kontrolü
    print("\n5️⃣ Tarih Kontrolü:")
    cursor.execute("""
        SELECT MIN(created_at), MAX(created_at)
        FROM products
        WHERE created_at IS NOT NULL
    """)
    date_range = cursor.fetchone()

    if date_range[0] and date_range[1]:
        print(f"   İlk ürün: {date_range[0]}")
        print(f"   Son ürün: {date_range[1]}")
        tests['passed'].append("Tarih kontrolü")
    else:
        tests['failed'].append("Tarih kontrolü")

    # 6. Kategori dağılımı
    print("\n6️⃣ Kategori Dağılımı:")
    cursor.execute("""
        SELECT c.name, COUNT(p.id) as product_count
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        GROUP BY c.name
        ORDER BY product_count DESC
        LIMIT 10
    """)
    categories = cursor.fetchall()

    if categories:
        print("   Kategori dağılımı:")
        for cat, count in categories[:5]:
            cat_name = cat if cat else "Kategorisiz"
            print(f"      • {cat_name}: {count} ürün")

    # ÖZET
    print("\n" + "="*60)
    print("📊 TEST SONUÇLARI")
    print("="*60)

    total_tests = len(tests['passed']) + len(tests['failed'])
    success_rate = (len(tests['passed']) / total_tests * 100) if total_tests > 0 else 0

    print(f"\n✅ Başarılı: {len(tests['passed'])} test")
    for test in tests['passed']:
        print(f"   • {test}")

    print(f"\n❌ Başarısız: {len(tests['failed'])} test")
    for test in tests['failed']:
        print(f"   • {test}")

    print(f"\n📈 Başarı Oranı: %{success_rate:.1f}")

    # Karar
    if success_rate >= 70:
        print("\n✅ VERİ KALİTESİ: KABUL EDİLEBİLİR")
        quality = "ACCEPTED"
    elif success_rate >= 50:
        print("\n⚠️ VERİ KALİTESİ: ORTA")
        quality = "MEDIUM"
    else:
        print("\n❌ VERİ KALİTESİ: DÜŞÜK - YENİDEN SCRAPING GEREKLİ")
        quality = "LOW"

    # Rapor oluştur
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_products': total_products,
        'total_reviews': total_reviews,
        'real_urls': real_urls,
        'real_reviews': real_reviews,
        'tests_passed': tests['passed'],
        'tests_failed': tests['failed'],
        'success_rate': success_rate,
        'quality': quality
    }

    with open('data_quality_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n📄 Detaylı rapor: data_quality_report.json")

    conn.close()

    # Exit kodu (GitHub Actions için)
    if quality == "LOW":
        return 1  # Başarısız
    return 0  # Başarılı

if __name__ == "__main__":
    exit_code = verify_data_quality()
    sys.exit(exit_code)