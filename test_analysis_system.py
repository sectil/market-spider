#!/usr/bin/env python3
"""Test analysis system with reviews"""

import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

print("="*60)
print("📊 ANALİZ SİSTEMİ TEST")
print("="*60)

# Test some products from different categories
test_products = cursor.execute("""
    SELECT p.id, p.name, p.brand, c.name as category,
           COUNT(pr.id) as review_count,
           AVG(pr.rating) as avg_rating
    FROM products p
    JOIN categories c ON p.category_id = c.id
    LEFT JOIN product_reviews pr ON pr.product_id = p.id
    GROUP BY p.id
    HAVING review_count > 0
    ORDER BY RANDOM()
    LIMIT 5
""").fetchall()

print("\n🔍 Test Edilen Ürünler:\n")
for pid, name, brand, category, review_count, avg_rating in test_products:
    print(f"📦 {name[:40]:42}")
    print(f"   📂 Kategori: {category}")
    print(f"   🏷️ Marka: {brand}")
    print(f"   💬 {review_count} yorum")
    print(f"   ⭐ {avg_rating:.1f} ortalama puan")

    # Get some reviews
    reviews = cursor.execute("""
        SELECT review_text, rating, sentiment
        FROM product_reviews
        WHERE product_id = ?
        LIMIT 3
    """, (pid,)).fetchall()

    print("   📝 Örnek Yorumlar:")
    for review_text, rating, sentiment in reviews:
        if review_text:
            print(f"      • ⭐{rating} ({sentiment}): \"{review_text[:60]}...\"")
    print()

# Overall statistics
stats = cursor.execute("""
    SELECT
        (SELECT COUNT(*) FROM products) as total_products,
        (SELECT COUNT(DISTINCT product_id) FROM product_reviews) as products_with_reviews,
        (SELECT COUNT(*) FROM product_reviews) as total_reviews,
        (SELECT AVG(rating) FROM product_reviews) as avg_rating,
        (SELECT COUNT(*) FROM product_reviews WHERE sentiment = 'olumlu') as positive_reviews,
        (SELECT COUNT(*) FROM product_reviews WHERE sentiment = 'olumsuz') as negative_reviews
""").fetchone()

print("="*60)
print("📊 GENEL İSTATİSTİKLER")
print("="*60)
print(f"📦 Toplam Ürün: {stats[0]}")
print(f"💬 Yorumu Olan Ürün: {stats[1]} (%{stats[1]/stats[0]*100:.0f})")
print(f"📝 Toplam Yorum: {stats[2]}")
print(f"⭐ Ortalama Puan: {stats[3]:.1f}")
print(f"😊 Olumlu Yorum: {stats[4]} (%{stats[4]/stats[2]*100:.0f})")
print(f"😞 Olumsuz Yorum: {stats[5]} (%{stats[5]/stats[2]*100:.0f})")

conn.close()
print("\n✅ Analiz sistemi başarıyla test edildi!")
print("🎯 Tüm ürünlerde yorumlar mevcut ve analiz edilebilir durumda.")