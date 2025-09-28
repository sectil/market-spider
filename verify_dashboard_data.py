#!/usr/bin/env python3
"""
Dashboard'un gösterdiği veriyi doğrula
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Product, get_engine
import sqlite3

print("="*60)
print("📊 DASHBOARD VERİ DOĞRULAMA")
print("="*60)

# SQLAlchemy ile kontrol
engine = get_engine()
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# SQLAlchemy üzerinden ürün sayısı
product_count_sqlalchemy = session.query(Product).count()
print(f"\n✅ SQLAlchemy ile ürün sayısı: {product_count_sqlalchemy}")

# İlk 5 ürün
products = session.query(Product).limit(5).all()
print("\nİlk 5 ürün (SQLAlchemy):")
for p in products:
    print(f"  • {p.name[:40]:42} - ₺{p.price}")

# Son 5 ürün
latest_products = session.query(Product).order_by(Product.id.desc()).limit(5).all()
print("\nSon eklenen 5 ürün (SQLAlchemy):")
for p in latest_products:
    print(f"  • {p.name[:40]:42} - ₺{p.price}")

session.close()

# SQLite direkt kontrol
conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()
product_count_sqlite = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
print(f"\n✅ SQLite direkt ürün sayısı: {product_count_sqlite}")

# Kategorili ürünler
categorized = cursor.execute("""
    SELECT COUNT(*) FROM products WHERE category_id IS NOT NULL
""").fetchone()[0]
print(f"✅ Kategorili ürün sayısı: {categorized}")

# En popüler ürünler (en çok yorum alan)
print("\n🏆 En Popüler 10 Ürün (Yorum sayısına göre):")
popular = cursor.execute("""
    SELECT name, brand, price, review_count, rating
    FROM products
    ORDER BY review_count DESC
    LIMIT 10
""").fetchall()

for name, brand, price, reviews, rating in popular:
    print(f"  • {name[:30]:32} | {brand:15} | ₺{price:8.2f} | {reviews:5} yorum | ⭐{rating}")

conn.close()

print("\n" + "="*60)
print("✅ VERİ DOĞRULAMA TAMAMLANDI")
print(f"🎯 Dashboard'da {product_count_sqlalchemy} ürün görünmeli")
print("="*60)