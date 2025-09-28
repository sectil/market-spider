#!/usr/bin/env python3
"""Check product_reviews table schema"""
import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(product_reviews)")
columns = cursor.fetchall()

print("product_reviews table columns:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()