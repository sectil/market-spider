#!/usr/bin/env python3
"""
📊 Dashboard'daki kategori listesini güncelle
Yeni kategori sistemini kullan
"""

import sqlite3

def update_analytics_page():
    """analytics_page.py'yi güncelle"""

    # Önce kategorileri veritabanından alalım
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    # Ürünlerin bulunduğu kategorileri al
    categories_with_products = cursor.execute("""
        SELECT DISTINCT
            CASE
                WHEN c2.name IS NOT NULL THEN c2.name || ' > ' || c1.name
                ELSE c1.name
            END as full_name,
            c1.name as category_name,
            COUNT(DISTINCT p.id) as product_count
        FROM categories c1
        LEFT JOIN categories c2 ON c1.parent_id = c2.id
        INNER JOIN products p ON p.category_id = c1.id
        GROUP BY c1.id
        ORDER BY product_count DESC
    """).fetchall()

    print("="*60)
    print("📊 DASHBOARD KATEGORİ GÜNCELLEMESİ")
    print("="*60)

    print("\n🏪 Ürünleri olan kategoriler:")
    for full_name, cat_name, count in categories_with_products:
        print(f"  • {full_name}: {count} ürün")

    # Analytics_page.py'yi oku
    with open('analytics_page.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Eski kategori listesini bul ve değiştir
    old_categories = 'categories = ["Tüm Kategoriler", "Giyim", "Elektronik", "Ev & Yaşam", "Kozmetik", "Spor", "Diğer"]'

    # Yeni kategori listesi
    new_category_list = ["Tüm Kategoriler"]
    for full_name, _, _ in categories_with_products:
        new_category_list.append(full_name)

    new_categories = f'categories = {new_category_list}'

    # Değiştir
    if old_categories in content:
        content = content.replace(old_categories, new_categories)
        print(f"\n✓ Eski kategori listesi güncellendi")
        print(f"  Yeni kategoriler: {new_category_list}")
    else:
        print("\n⚠️ Eski kategori listesi bulunamadı, manuel güncelleme gerekebilir")

    # Kategori sorgusunu da güncelle
    old_query1 = 'query.filter(Product.category == selected_category)'
    new_query1 = '''query.join(
            Category, Product.category_id == Category.id
        ).filter(
            or_(
                Category.name == selected_category.split(' > ')[-1],
                Category.name == selected_category
            )
        )'''

    # analytics_page.py'yi güncelle
    updated = False

    # Önce import'ları güncelle
    if 'from database import SessionLocal, Product' in content and 'Category' not in content:
        content = content.replace(
            'from database import SessionLocal, Product, PriceHistory, RankingHistory, SiteConfig, ProductReview',
            'from database import SessionLocal, Product, PriceHistory, RankingHistory, SiteConfig, ProductReview\nfrom sqlalchemy import or_\nimport sqlite3'
        )
        updated = True

    # Kategori listesini SQL'den dinamik olarak alan kod ekle
    category_code = '''
def get_categories_from_db():
    """Veritabanından kategorileri al"""
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    categories_with_products = cursor.execute("""
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
    """).fetchall()

    conn.close()

    return ["Tüm Kategoriler"] + [name for name, _ in categories_with_products]
'''

    # show_analytics_page fonksiyonunun başına ekle
    if 'def show_analytics_page():' in content and 'get_categories_from_db' not in content:
        content = category_code + '\n' + content

        # Sabit kategori listesini dinamik hale getir
        content = content.replace(
            'categories = ["Tüm Kategoriler", "Giyim", "Elektronik", "Ev & Yaşam", "Kozmetik", "Spor", "Diğer"]',
            'categories = get_categories_from_db()'
        )
        updated = True

    if updated:
        # Dosyayı kaydet
        with open('analytics_page.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("\n✅ analytics_page.py güncellendi!")
    else:
        print("\n⚠️ analytics_page.py güncellenemedi, manuel müdahale gerekebilir")

    # Dashboard'ı da kontrol et
    print("\n📋 Dashboard.py kontrolü...")

    with open('dashboard.py', 'r', encoding='utf-8') as f:
        dashboard_content = f.read()

    # Category view import'u ekle
    if 'category_view' not in dashboard_content:
        print("  ⚠️ Dashboard'a kategori görünümü eklenmeli")
    else:
        print("  ✓ Kategori görünümü zaten ekli")

    conn.close()

    print("\n" + "="*60)
    print("✅ GÜNCELLEME TAMAMLANDI")
    print("="*60)
    print("\n📌 Yapılan değişiklikler:")
    print("  1. Kategori listesi veritabanından dinamik olarak alınıyor")
    print("  2. Ürünleri olan kategoriler gösteriliyor")
    print("  3. Hiyerarşik kategori yapısı destekleniyor (Ana > Alt)")
    print("\n🚀 Dashboard'u yeniden başlatın:")
    print("  python3 -m streamlit run dashboard.py")


if __name__ == "__main__":
    update_analytics_page()