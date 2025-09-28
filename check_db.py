#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(products)")
columns = cursor.fetchall()

print("Products table columns:")
for col in columns:
    print(f"  {col[1]} - {col[2]}")

conn.close()