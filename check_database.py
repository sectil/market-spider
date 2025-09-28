#!/usr/bin/env python3
"""Veritabanı durumunu kontrol et"""

import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

print("="*60)
print("📊 VERİTABANI DURUMU")
print("="*60)

# Toplam ürün sayısı
total = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
print(f"\n✅ Toplam ürün sayısı: {total}")

# Site bazında dağılım
print("\n📌 Site bazında dağılım:")
sites = cursor.execute("""
    SELECT site_name, COUNT(*) as count
    FROM products
    GROUP BY site_name
""").fetchall()

for site, count in sites:
    print(f"  • {site}: {count} ürün")

# Son eklenen 5 ürün
print("\n📦 Son eklenen 5 ürün:")
products = cursor.execute("""
    SELECT name, brand, price, site_name
    FROM products
    ORDER BY id DESC
    LIMIT 5
""").fetchall()

for name, brand, price, site in products:
    print(f"  • {name[:40]:42} | {brand:15} | ₺{price:8.2f} | {site}")

conn.close()