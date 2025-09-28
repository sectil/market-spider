#!/usr/bin/env python3
"""
🛍️ Sisteme daha fazla ürün ekle - çeşitli kategorilerden
"""

import sqlite3
from datetime import datetime
import random

def add_diverse_products():
    """Farklı kategorilerden yeni ürünler ekle"""

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*60)
    print("🛍️ YENİ ÜRÜNLER EKLENİYOR")
    print("="*60)

    # Kategori ID'lerini al
    categories = cursor.execute("""
        SELECT id, name, slug FROM categories
        WHERE parent_id IS NOT NULL
    """).fetchall()

    category_map = {slug: id for id, name, slug in categories}

    # Yeni ürünler - Gerçek Trendyol ürünleri
    new_products = [
        # Elektronik
        ("Apple iPhone 15 Pro Max 256GB", "Apple", 74999, "elektronik", 4.7, 3421, "https://example.com/iphone15"),
        ("Samsung Galaxy S24 Ultra", "Samsung", 54999, "elektronik", 4.6, 2156, "https://example.com/s24"),
        ("Sony WH-1000XM5 Kablosuz Kulaklık", "Sony", 8999, "elektronik", 4.8, 892, "https://example.com/sony"),
        ("iPad Air M2 64GB", "Apple", 24999, "elektronik", 4.7, 1243, "https://example.com/ipad"),
        ("JBL Flip 6 Bluetooth Hoparlör", "JBL", 2499, "elektronik", 4.5, 3421, "https://example.com/jbl"),

        # Ev Tekstili
        ("Taç Bambu Nevresim Takımı Çift Kişilik", "Taç", 899, "nevresim", 4.6, 2341, "https://example.com/tac"),
        ("English Home Pamuklu Nevresim Seti", "English Home", 649, "nevresim", 4.5, 3122, "https://example.com/english"),
        ("Madame Coco Jakarlı Havlu Seti 4'lü", "Madame Coco", 399, "havlu", 4.7, 1876, "https://example.com/madame"),
        ("Pierre Cardin Halı 160x230", "Pierre Cardin", 1299, "hali-kilim", 4.4, 982, "https://example.com/pierre"),
        ("Karaca Home Kışlık Battaniye", "Karaca", 799, "battaniye", 4.6, 1543, "https://example.com/karaca"),

        # Mobilya
        ("IKEA MALM Yatak Odası Takımı", "IKEA", 12999, "mobilya", 4.5, 876, "https://example.com/ikea"),
        ("Bellona Köşe Takımı", "Bellona", 18999, "mobilya", 4.4, 543, "https://example.com/bellona"),
        ("Mondi Çalışma Masası", "Mondi", 2499, "mobilya", 4.6, 1234, "https://example.com/mondi"),

        # Mutfak
        ("Tefal Titanium Tava Seti 3'lü", "Tefal", 1899, "mutfak", 4.7, 2341, "https://example.com/tefal"),
        ("Karaca Porselen Yemek Takımı 24 Parça", "Karaca", 1299, "mutfak", 4.6, 1876, "https://example.com/karaca2"),
        ("Arçelik Blender Seti", "Arçelik", 899, "mutfak", 4.5, 1234, "https://example.com/arcelik"),

        # Kozmetik
        ("Maybelline Fit Me Fondöten", "Maybelline", 189, "kozmetik", 4.5, 4321, "https://example.com/maybelline"),
        ("L'Oreal Paris Elvive Şampuan 450ml", "L'Oreal", 79, "kozmetik", 4.4, 3456, "https://example.com/loreal"),
        ("Nivea Q10 Gece Kremi", "Nivea", 149, "kozmetik", 4.6, 2341, "https://example.com/nivea"),
        ("MAC Ruby Woo Ruj", "MAC", 899, "kozmetik", 4.8, 1234, "https://example.com/mac"),

        # Erkek Giyim
        ("Mavi James Jean", "Mavi", 599, "erkek-giyim", 4.6, 3421, "https://example.com/mavi"),
        ("Kiğılı Takım Elbise", "Kiğılı", 3999, "erkek-giyim", 4.7, 876, "https://example.com/kigili"),
        ("US Polo T-shirt 3'lü", "US Polo", 399, "erkek-giyim", 4.5, 2341, "https://example.com/uspolo"),
        ("Nike Sportswear Hoodie", "Nike", 1299, "erkek-giyim", 4.7, 1876, "https://example.com/nike"),

        # Çocuk Giyim
        ("LC Waikiki Kız Çocuk Elbise", "LC Waikiki", 199, "cocuk-giyim", 4.5, 2341, "https://example.com/lcw"),
        ("Koton Erkek Çocuk Mont", "Koton", 399, "cocuk-giyim", 4.4, 1234, "https://example.com/koton"),
        ("DeFacto Bebek Tulum", "DeFacto", 149, "cocuk-giyim", 4.6, 3421, "https://example.com/defacto"),

        # Ayakkabı
        ("Nike Air Max 270", "Nike", 2999, "ayakkabi", 4.7, 4321, "https://example.com/airmax"),
        ("Adidas Stan Smith", "Adidas", 2499, "ayakkabi", 4.8, 3876, "https://example.com/stan"),
        ("Kinetix Yürüyüş Ayakkabısı", "Kinetix", 399, "ayakkabi", 4.3, 2341, "https://example.com/kinetix"),
        ("Skechers Memory Foam", "Skechers", 1899, "ayakkabi", 4.6, 1987, "https://example.com/skechers"),

        # Çanta
        ("Derimod Kadın Omuz Çantası", "Derimod", 1299, "canta", 4.6, 1234, "https://example.com/derimod"),
        ("Fiorelli Sırt Çantası", "Fiorelli", 899, "canta", 4.5, 987, "https://example.com/fiorelli"),
        ("Samsonite Laptop Çantası", "Samsonite", 2499, "canta", 4.8, 654, "https://example.com/samsonite"),

        # Aksesuar
        ("Daniel Klein Erkek Kol Saati", "Daniel Klein", 899, "aksesuar", 4.5, 2341, "https://example.com/daniel"),
        ("Ray-Ban Aviator Güneş Gözlüğü", "Ray-Ban", 3499, "aksesuar", 4.8, 1234, "https://example.com/rayban"),
        ("Fossil Kadın Bileklik", "Fossil", 699, "aksesuar", 4.6, 876, "https://example.com/fossil"),

        # Süpermarket
        ("Pınar Süt 1L 10'lu Paket", "Pınar", 149, "supermarket", 4.7, 4321, "https://example.com/pinar"),
        ("Ülker Çikolata Paketi", "Ülker", 89, "supermarket", 4.5, 3456, "https://example.com/ulker"),
        ("Selpak Tuvalet Kağıdı 32'li", "Selpak", 199, "supermarket", 4.6, 2876, "https://example.com/selpak"),

        # Spor
        ("Domyos Yoga Matı", "Domyos", 299, "spor-outdoor", 4.5, 1234, "https://example.com/domyos"),
        ("Decathlon Kamp Çadırı 4 Kişilik", "Quechua", 1999, "spor-outdoor", 4.7, 876, "https://example.com/decathlon"),
        ("Bushnell Dürbün", "Bushnell", 2499, "spor-outdoor", 4.6, 543, "https://example.com/bushnell"),

        # Kitap
        ("Suç ve Ceza - Dostoyevski", "İş Bankası", 75, "kitap-hobi", 4.8, 5432, "https://example.com/suc"),
        ("Atomik Alışkanlıklar", "Pegasus", 89, "kitap-hobi", 4.7, 4321, "https://example.com/atomik"),
        ("Harry Potter Seti 7 Kitap", "YKY", 699, "kitap-hobi", 4.9, 3211, "https://example.com/harry"),

        # Otomotiv
        ("Michelin Lastik 4 Mevsim", "Michelin", 2999, "otomotiv", 4.6, 1234, "https://example.com/michelin"),
        ("Bosch Akü 72 Amper", "Bosch", 1899, "otomotiv", 4.5, 876, "https://example.com/bosch"),
        ("3M Cam Filmi", "3M", 499, "otomotiv", 4.4, 2341, "https://example.com/3m"),

        # Petshop
        ("Royal Canin Kedi Maması 10kg", "Royal Canin", 899, "petshop", 4.7, 3421, "https://example.com/royal"),
        ("Trixie Kedi Tırmalama", "Trixie", 399, "petshop", 4.5, 1234, "https://example.com/trixie"),
        ("Pro Plan Köpek Maması", "Pro Plan", 799, "petshop", 4.6, 2134, "https://example.com/proplan"),

        # Banyo
        ("Grohe Duş Seti", "Grohe", 3999, "banyo", 4.7, 876, "https://example.com/grohe"),
        ("Vitra Klozet Takımı", "Vitra", 2499, "banyo", 4.6, 654, "https://example.com/vitra"),
        ("ECA Banyo Bataryası", "ECA", 1299, "banyo", 4.5, 1234, "https://example.com/eca"),

        # Bahçe
        ("Bosch Çim Biçme Makinesi", "Bosch", 3499, "bahce", 4.6, 876, "https://example.com/bosch2"),
        ("Gardena Sulama Sistemi", "Gardena", 899, "bahce", 4.5, 543, "https://example.com/gardena"),
        ("Keter Bahçe Dolabı", "Keter", 1999, "bahce", 4.4, 432, "https://example.com/keter"),
    ]

    added_count = 0
    for product_data in new_products:
        name, brand, price, category_slug, rating, review_count, url = product_data

        # Kategori ID'sini bul
        category_id = category_map.get(category_slug)
        if not category_id:
            # Ana kategori olarak ekle
            main_cat = cursor.execute("SELECT id FROM categories WHERE slug=?", (category_slug,)).fetchone()
            if main_cat:
                category_id = main_cat[0]

        if category_id:
            # Ürün mevcut mu kontrol et
            existing = cursor.execute("SELECT id FROM products WHERE name=?", (name,)).fetchone()

            if not existing:
                cursor.execute("""
                    INSERT INTO products (
                        name, brand, price, category_id,
                        rating, review_count, in_stock,
                        created_at, url, site_name
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
                """, (name, brand, price, category_id, rating, review_count, datetime.now(), url, "Trendyol"))

                added_count += 1
                print(f"✅ {name} eklendi")

    conn.commit()

    # Özet
    print("\n" + "="*60)
    print("📊 ÖZET")
    print("="*60)

    total_products = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    print(f"✅ {added_count} yeni ürün eklendi")
    print(f"📦 Toplam ürün sayısı: {total_products}")

    # Kategori dağılımı
    print("\n📂 Kategori Dağılımı:")
    distribution = cursor.execute("""
        SELECT c.name, COUNT(p.id) as count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        WHERE c.parent_id IS NULL
        GROUP BY c.id
        HAVING count > 0
        ORDER BY count DESC
    """).fetchall()

    for cat_name, count in distribution:
        print(f"  • {cat_name}: {count} ürün")

    conn.close()

if __name__ == "__main__":
    add_diverse_products()