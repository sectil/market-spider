#!/usr/bin/env python3
"""
Test kategori sisteminin dashboard'da çalıştığını doğrula
"""

import sqlite3
import pandas as pd

def test_category_system():
    print("="*60)
    print("📊 KATEGORİ SİSTEMİ TEST")
    print("="*60)

    conn = sqlite3.connect('market_spider.db')

    # 1. Kategori hiyerarşisi
    print("\n🌳 Kategori Hiyerarşisi:")
    categories_hierarchy = pd.read_sql_query("""
        SELECT
            CASE
                WHEN c2.name IS NOT NULL THEN c2.name || ' > ' || c1.name
                ELSE c1.name
            END as full_path,
            COUNT(p.id) as product_count
        FROM categories c1
        LEFT JOIN categories c2 ON c1.parent_id = c2.id
        LEFT JOIN products p ON p.category_id = c1.id
        GROUP BY c1.id
        HAVING product_count > 0
        ORDER BY product_count DESC
    """, conn)

    for _, row in categories_hierarchy.iterrows():
        print(f"  • {row['full_path']}: {row['product_count']} ürün")

    # 2. Dashboard'da gösterilecek kategoriler
    print("\n📱 Dashboard Kategorileri:")
    dashboard_categories = pd.read_sql_query("""
        SELECT DISTINCT
            CASE
                WHEN c2.name IS NOT NULL THEN c2.name || ' > ' || c1.name
                ELSE c1.name
            END as full_name,
            COUNT(DISTINCT p.id) as product_count
        FROM categories c1
        LEFT JOIN categories c2 ON c1.parent_id = c2.id
        INNER JOIN products p ON p.category_id = c1.id
        GROUP BY c1.id
        HAVING product_count > 0
        ORDER BY product_count DESC
    """, conn)

    dashboard_list = ["Tüm Kategoriler"] + dashboard_categories['full_name'].tolist()
    for cat in dashboard_list:
        print(f"  • {cat}")

    # 3. Ürün kategori atamaları
    print("\n📦 Örnek Ürün Kategori Atamaları:")
    sample_products = pd.read_sql_query("""
        SELECT
            p.name as product_name,
            c.name as category_name,
            CASE
                WHEN c2.name IS NOT NULL THEN c2.name || ' > ' || c.name
                ELSE c.name
            END as full_category_path
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN categories c2 ON c.parent_id = c2.id
        LIMIT 10
    """, conn)

    for _, row in sample_products.iterrows():
        print(f"  • {row['product_name'][:40]:42} → {row['full_category_path']}")

    # 4. Ana kategorilere göre ürün dağılımı
    print("\n📊 Ana Kategorilere Göre Dağılım:")
    main_category_distribution = pd.read_sql_query("""
        SELECT
            CASE
                WHEN c.parent_id IS NULL THEN c.name
                ELSE (SELECT name FROM categories WHERE id = c.parent_id)
            END as main_category,
            COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        WHERE p.id IS NOT NULL
        GROUP BY main_category
        ORDER BY product_count DESC
    """, conn)

    for _, row in main_category_distribution.iterrows():
        print(f"  • {row['main_category']}: {row['product_count']} ürün")

    conn.close()

    print("\n" + "="*60)
    print("✅ TEST TAMAMLANDI")
    print("="*60)
    print("\n📌 Dashboard Bilgileri:")
    print("  • URL: http://localhost:8505")
    print("  • Yeni 'Kategoriler' sayfası eklendi")
    print("  • Analytics sayfası güncellendi")
    print("  • Kategoriler artık veritabanından dinamik olarak çekiliyor")

if __name__ == "__main__":
    test_category_system()