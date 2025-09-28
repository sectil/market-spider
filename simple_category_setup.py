#!/usr/bin/env python3
"""
🏪 BASİT KATEGORİ SİSTEMİ KURULUMU
E-ticaret kategorilerini veritabanına ekle
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import sqlite3

# Doğrudan SQLite ile çalış
def setup_categories_simple():
    """Basit kategori sistemi kur"""

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*80)
    print("🏪 KATEGORİ SİSTEMİ KURULUMU")
    print("="*80)

    # Categories tablosunu oluştur
    print("\n📂 Kategori tablosu oluşturuluyor...")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE,
            parent_id INTEGER,
            icon TEXT,
            description TEXT,
            order_index INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )
    ''')

    # Product tablosuna category_id ekle
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN category_id INTEGER')
        print("✓ Product tablosuna category_id eklendi")
    except:
        print("ℹ️ category_id zaten var")

    # Kategori yapısı
    categories = [
        # Ana Kategoriler
        ("👗 Giyim & Aksesuar", "giyim-aksesuar", None, "👗", 1),
        ("🏠 Ev & Yaşam", "ev-yasam", None, "🏠", 2),
        ("📱 Elektronik", "elektronik", None, "📱", 3),
        ("💄 Kozmetik", "kozmetik", None, "💄", 4),
        ("🏪 Süpermarket", "supermarket", None, "🏪", 5),
        ("🏃 Spor & Outdoor", "spor-outdoor", None, "🏃", 6),
        ("📚 Kitap & Hobi", "kitap-hobi", None, "📚", 7),
        ("🚗 Otomotiv", "otomotiv", None, "🚗", 8),
        ("🐕 Petshop", "petshop", None, "🐕", 9),
    ]

    # Ana kategorileri ekle
    print("\n📁 Ana kategoriler ekleniyor...")
    for cat in categories:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', cat)
        print(f"  {cat[3]} {cat[0]}")

    conn.commit()

    # Giyim alt kategorileri
    giyim_id = cursor.execute("SELECT id FROM categories WHERE slug='giyim-aksesuar'").fetchone()[0]

    giyim_subcats = [
        ("Kadın Giyim", "kadin-giyim", giyim_id, None, 1),
        ("Erkek Giyim", "erkek-giyim", giyim_id, None, 2),
        ("Çocuk Giyim", "cocuk-giyim", giyim_id, None, 3),
        ("İç Giyim", "ic-giyim", giyim_id, None, 4),
        ("Ayakkabı", "ayakkabi", giyim_id, None, 5),
        ("Çanta", "canta", giyim_id, None, 6),
        ("Aksesuar", "aksesuar", giyim_id, None, 7),
    ]

    print(f"\n  └─ Alt kategoriler ekleniyor...")
    for subcat in giyim_subcats:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', subcat)
        print(f"      • {subcat[0]}")

    # Kadın Giyim alt kategorileri
    kadin_id = cursor.execute("SELECT id FROM categories WHERE slug='kadin-giyim'").fetchone()[0]

    kadin_subcats = [
        ("Elbise", "elbise", kadin_id, None, 1),
        ("Pantolon", "pantolon", kadin_id, None, 2),
        ("Gömlek", "gomlek", kadin_id, None, 3),
        ("T-shirt", "tshirt", kadin_id, None, 4),
        ("Trençkot", "trenckok", kadin_id, None, 5),
        ("Sweatshirt", "sweatshirt", kadin_id, None, 6),
        ("Atlet", "atlet", kadin_id, None, 7),
        ("Bluz", "bluz", kadin_id, None, 8),
        ("Ceket", "ceket", kadin_id, None, 9),
    ]

    for subcat in kadin_subcats:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', subcat)

    # İç Giyim alt kategorileri
    ic_giyim_id = cursor.execute("SELECT id FROM categories WHERE slug='ic-giyim'").fetchone()[0]

    ic_giyim_subcats = [
        ("Kadın İç Giyim", "kadin-ic-giyim", ic_giyim_id, None, 1),
        ("Erkek İç Giyim", "erkek-ic-giyim", ic_giyim_id, None, 2),
        ("Pijama & Gecelik", "pijama", ic_giyim_id, None, 3),
        ("Çorap", "corap", ic_giyim_id, None, 4),
    ]

    for subcat in ic_giyim_subcats:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', subcat)

    # Ev & Yaşam alt kategorileri
    ev_id = cursor.execute("SELECT id FROM categories WHERE slug='ev-yasam'").fetchone()[0]

    ev_subcats = [
        ("Ev Tekstili", "ev-tekstili", ev_id, None, 1),
        ("Mobilya", "mobilya", ev_id, None, 2),
        ("Ev Dekorasyon", "ev-dekorasyon", ev_id, None, 3),
        ("Mutfak", "mutfak", ev_id, None, 4),
        ("Banyo", "banyo", ev_id, None, 5),
        ("Bahçe", "bahce", ev_id, None, 6),
    ]

    for subcat in ev_subcats:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', subcat)

    # Ev Tekstili alt kategorileri
    ev_tekstil_id = cursor.execute("SELECT id FROM categories WHERE slug='ev-tekstili'").fetchone()[0]

    tekstil_subcats = [
        ("Nevresim Takımı", "nevresim", ev_tekstil_id, None, 1),
        ("Havlu", "havlu", ev_tekstil_id, None, 2),
        ("Halı & Kilim", "hali-kilim", ev_tekstil_id, None, 3),
        ("Perde", "perde", ev_tekstil_id, None, 4),
        ("Yastık", "yastik", ev_tekstil_id, None, 5),
        ("Battaniye", "battaniye", ev_tekstil_id, None, 6),
    ]

    for subcat in tekstil_subcats:
        cursor.execute('''
            INSERT OR IGNORE INTO categories (name, slug, parent_id, icon, order_index)
            VALUES (?, ?, ?, ?, ?)
        ''', subcat)

    conn.commit()

    # Mevcut ürünleri kategorilere ata
    print("\n\n📦 Mevcut ürünleri kategorilere atama...")

    product_categories = {
        'palazzo': 'pantolon',
        'pantolon': 'pantolon',
        'atlet': 'atlet',
        'trençkot': 'trenckok',
        'trenç': 'trenckok',
        'sweatshirt': 'sweatshirt',
        'pijama': 'pijama',
        'külot': 'kadin-ic-giyim',
        'bikini': 'kadin-ic-giyim',
        'çorap': 'corap',
        'külotlu': 'corap',
        'patik': 'corap',
        'ceket': 'ceket',
        'bomber': 'ceket',
        'bluz': 'bluz',
        'sütyen': 'kadin-ic-giyim'
    }

    # Tüm ürünleri al
    products = cursor.execute("SELECT id, name FROM products").fetchall()

    for product_id, product_name in products:
        product_lower = product_name.lower()
        category_slug = None

        # Kategori bul
        for keyword, slug in product_categories.items():
            if keyword in product_lower:
                category_slug = slug
                break

        # Default kategori
        if not category_slug:
            category_slug = 'kadin-giyim'

        # Kategori ID'yi bul
        cat_result = cursor.execute("SELECT id FROM categories WHERE slug=?", (category_slug,)).fetchone()
        if cat_result:
            category_id = cat_result[0]
            cursor.execute("UPDATE products SET category_id=? WHERE id=?", (category_id, product_id))
            print(f"  {product_name[:40]:42} → {category_slug}")

    conn.commit()

    # Özet rapor
    print("\n" + "="*80)
    print("📊 KATEGORİ SİSTEMİ ÖZET")
    print("="*80)

    total_categories = cursor.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    main_categories = cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id IS NULL").fetchone()[0]

    print(f"✅ Toplam {total_categories} kategori oluşturuldu")
    print(f"   • {main_categories} ana kategori")
    print(f"   • {total_categories - main_categories} alt kategori")

    print("\n📂 Kategori Ağacı:")

    # Ana kategorileri göster
    main_cats = cursor.execute("""
        SELECT id, name, icon
        FROM categories
        WHERE parent_id IS NULL
        ORDER BY order_index
    """).fetchall()

    for cat_id, cat_name, icon in main_cats:
        # Alt kategori sayısı
        sub_count = cursor.execute("""
            SELECT COUNT(*)
            FROM categories
            WHERE parent_id=?
        """, (cat_id,)).fetchone()[0]

        print(f"   {icon} {cat_name}: {sub_count} alt kategori")

        # Alt kategorileri göster
        sub_cats = cursor.execute("""
            SELECT name
            FROM categories
            WHERE parent_id=?
            ORDER BY order_index
        """, (cat_id,)).fetchall()

        for sub_cat in sub_cats[:3]:  # İlk 3'ü göster
            print(f"      └─ {sub_cat[0]}")

        if len(sub_cats) > 3:
            print(f"      └─ ... ve {len(sub_cats) - 3} diğer")

    # Ürün dağılımı
    print("\n📦 Kategorilere göre ürün dağılımı:")

    category_products = cursor.execute("""
        SELECT c.name, c.icon, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        GROUP BY c.id
        HAVING product_count > 0
        ORDER BY product_count DESC
        LIMIT 10
    """).fetchall()

    for cat_name, icon, count in category_products:
        print(f"   {icon if icon else '•'} {cat_name}: {count} ürün")

    conn.close()


if __name__ == "__main__":
    setup_categories_simple()