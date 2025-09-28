#!/usr/bin/env python3
"""Fix column names in review queries"""

import sqlite3

conn = sqlite3.connect('market_spider.db')
cursor = conn.cursor()

# Add sentiment column if not exists
try:
    cursor.execute("ALTER TABLE product_reviews ADD COLUMN sentiment VARCHAR(20)")
    conn.commit()
    print("✅ Added sentiment column")
except:
    print("ℹ️ Sentiment column already exists")

# Update sentiment based on sentiment_score
cursor.execute("""
    UPDATE product_reviews
    SET sentiment = CASE
        WHEN sentiment_score > 0 THEN 'olumlu'
        WHEN sentiment_score < 0 THEN 'olumsuz'
        ELSE 'nötr'
    END
    WHERE sentiment IS NULL
""")
conn.commit()
print(f"✅ Updated {cursor.rowcount} sentiment values")

# Create comment column as alias to review_text
try:
    cursor.execute("ALTER TABLE product_reviews ADD COLUMN comment TEXT")
    cursor.execute("UPDATE product_reviews SET comment = review_text WHERE comment IS NULL")
    conn.commit()
    print("✅ Added comment column as alias")
except:
    print("ℹ️ Comment column already exists")

conn.close()
print("✅ Database schema fixed!")