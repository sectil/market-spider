#!/usr/bin/env python3
"""
🆓 GITHUB ACTIONS İLE ÜCRETSİZ SCRAPER
Tamamen ücretsiz ve kalıcı çözüm
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import pandas as pd
from datetime import datetime
import time
import random
import os

def github_action_scraper():
    """GitHub Actions ortamında çalışacak scraper"""

    # GitHub Actions için Chrome ayarları
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    # Undetected ChromeDriver - Cloudflare bypass
    driver = uc.Chrome(options=options, version_main=120)

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    # Tablo oluştur (yoksa)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            brand TEXT,
            price REAL,
            rating REAL,
            review_count INTEGER,
            url TEXT UNIQUE,
            site_name TEXT,
            category_id INTEGER,
            in_stock BOOLEAN,
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            reviewer_name TEXT,
            rating REAL,
            review_text TEXT,
            review_date TIMESTAMP,
            helpful_count INTEGER,
            sentiment_score REAL,
            scraped_at TIMESTAMP
        )
    """)

    conn.commit()

    products_data = []

    try:
        print("🌐 Trendyol'a bağlanılıyor...")
        driver.get("https://www.trendyol.com/cok-satanlar")

        # Cloudflare challenge'ı geçmesi için bekle
        time.sleep(10)

        # Sayfayı aşağı kaydır (lazy loading için)
        for i in range(5):
            driver.execute_script(f"window.scrollTo(0, {i * 1000});")
            time.sleep(2)

        # Ürünleri topla
        products = driver.find_elements(By.CSS_SELECTOR, "div.p-card-wrppr")
        print(f"✅ {len(products)} ürün bulundu")

        for idx, product in enumerate(products[:50], 1):  # İlk 50 ürün
            try:
                # JavaScript ile veri çek (daha güvenilir)
                product_data = driver.execute_script("""
                    var elem = arguments[0];
                    var link = elem.querySelector('a');
                    var name = elem.querySelector('.prdct-desc-cntnr-name');
                    var brand = elem.querySelector('.prdct-desc-cntnr-ttl');
                    var price = elem.querySelector('.prc-box-dscntd');
                    var rating = elem.querySelector('.rating-score');

                    return {
                        url: link ? link.href : '',
                        name: name ? name.innerText : '',
                        brand: brand ? brand.innerText : '',
                        price: price ? price.innerText : '',
                        rating: rating ? rating.innerText : ''
                    };
                """, product)

                if product_data['name']:
                    # Fiyatı temizle
                    price_str = product_data['price'].replace(' TL', '').replace('.', '').replace(',', '.')
                    try:
                        price = float(price_str)
                    except:
                        price = 0

                    # Veritabanına ekle
                    cursor.execute("""
                        INSERT OR REPLACE INTO products (
                            name, brand, price, url, site_name,
                            created_at, in_stock, rating
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_data['name'],
                        product_data['brand'],
                        price,
                        product_data['url'],
                        'Trendyol',
                        datetime.now(),
                        1,
                        float(product_data['rating']) if product_data['rating'] else 0
                    ))

                    products_data.append(product_data)
                    print(f"  {idx}. ✅ {product_data['name'][:40]}")

                    # Her 10 üründe bir commit
                    if idx % 10 == 0:
                        conn.commit()

            except Exception as e:
                print(f"  {idx}. ❌ Hata: {e}")
                continue

        conn.commit()

        # CSV'ye kaydet
        if products_data:
            df = pd.DataFrame(products_data)
            df.to_csv('scraped_products.csv', index=False)
            print(f"\n✅ {len(products_data)} ürün CSV'ye kaydedildi")

    except Exception as e:
        print(f"❌ Ana hata: {e}")

    finally:
        driver.quit()
        conn.close()

    print("\n🎉 Scraping tamamlandı!")
    return len(products_data)

if __name__ == "__main__":
    # GitHub Actions ortam değişkeni kontrolü
    if os.environ.get('GITHUB_ACTIONS'):
        print("🤖 GitHub Actions ortamında çalışıyor")

    result = github_action_scraper()
    print(f"\n📊 Toplam {result} ürün toplandı")