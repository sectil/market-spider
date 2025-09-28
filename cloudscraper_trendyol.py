#!/usr/bin/env python3
"""
🔥 CLOUDSCRAPER İLE GERÇEK TRENDYOL VERİLERİ
Cloudflare bypass için cloudscraper kullanımı
"""

import cloudscraper
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random
import json

def scrape_with_cloudscraper():
    """Cloudscraper ile Trendyol'dan gerçek veri çek"""

    # Cloudscraper instance oluştur (Cloudflare bypass)
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*60)
    print("🔥 GERÇEK TRENDYOL VERİLERİ ÇEKİLİYOR")
    print("="*60)

    # Önce mevcut simülasyon verilerini temizle
    print("\n🧹 Simülasyon veriler temizleniyor...")
    cursor.execute("DELETE FROM product_reviews WHERE scraped_at IS NULL")
    cursor.execute("DELETE FROM products WHERE site_name != 'Trendyol'")
    conn.commit()

    try:
        # Çok satanlar sayfası
        url = "https://www.trendyol.com/cok-satanlar"
        print(f"\n📌 Bağlanılıyor: {url}")

        response = scraper.get(url)

        if response.status_code == 200:
            print("✅ Cloudflare bypass başarılı!")

            soup = BeautifulSoup(response.text, 'html.parser')

            # Sayfa içindeki window.__SEARCH_APP_INITIAL_STATE__ değişkenini bul
            script_tags = soup.find_all('script')

            for script in script_tags:
                if '__SEARCH_APP_INITIAL_STATE__' in str(script):
                    # JSON verilerini çıkar
                    script_text = str(script.string)
                    start = script_text.find('{')
                    end = script_text.rfind('}') + 1
                    json_str = script_text[start:end]

                    try:
                        data = json.loads(json_str)
                        products = data.get('products', [])

                        print(f"\n📦 {len(products)} ürün bulundu!")

                        for idx, product in enumerate(products[:30], 1):
                            try:
                                # Ürün bilgileri
                                name = product.get('name', '')
                                brand = product.get('brand', {}).get('name', '')
                                price = product.get('price', {}).get('sellingPrice', 0)
                                rating = product.get('ratingScore', {}).get('averageRating', 0)
                                review_count = product.get('ratingScore', {}).get('totalRatingCount', 0)
                                product_id = product.get('id')
                                merchant_id = product.get('merchant', {}).get('id')
                                url = f"https://www.trendyol.com{product.get('url', '')}"

                                # Veritabanına ekle
                                cursor.execute("""
                                    INSERT OR REPLACE INTO products (
                                        name, brand, price, rating, review_count,
                                        url, site_name, in_stock, created_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                                    name, brand, price, rating, review_count,
                                    url, 'Trendyol', 1, datetime.now()
                                ))

                                db_product_id = cursor.lastrowid
                                print(f"  {idx}. ✅ {name[:40]}")

                                # Yorumları çek
                                if product_id and merchant_id:
                                    time.sleep(random.uniform(1, 2))

                                    review_url = f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/rating/review?merchantId={merchant_id}&productId={product_id}&page=0&size=20"

                                    review_response = scraper.get(review_url)

                                    if review_response.status_code == 200:
                                        review_data = review_response.json()
                                        reviews = review_data.get('result', {}).get('productReviews', {}).get('content', [])

                                        for review in reviews[:10]:
                                            reviewer = review.get('userFullName', 'Anonim')
                                            rating = review.get('rate', 0)
                                            comment = review.get('comment', '')
                                            review_date = review.get('lastModifiedDate')

                                            if review_date:
                                                review_date = datetime.fromtimestamp(review_date / 1000)
                                            else:
                                                review_date = datetime.now()

                                            cursor.execute("""
                                                INSERT INTO product_reviews (
                                                    product_id, reviewer_name, rating,
                                                    review_text, review_date, scraped_at,
                                                    sentiment_score, helpful_count
                                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                            """, (
                                                db_product_id, reviewer, rating, comment,
                                                review_date, datetime.now(),
                                                1.0 if rating >= 4 else -1.0 if rating <= 2 else 0.0,
                                                review.get('helpfulCount', 0)
                                            ))

                                        print(f"     💬 {len(reviews)} yorum eklendi")

                                conn.commit()

                            except Exception as e:
                                print(f"  ❌ Ürün hatası: {e}")
                                continue

                    except json.JSONDecodeError as e:
                        print(f"JSON parse hatası: {e}")

            # Alternatif: HTML parse et
            if not products:
                print("\n📋 HTML parse deneniyor...")

                product_cards = soup.find_all('div', class_='p-card-wrppr')[:20]

                for idx, card in enumerate(product_cards, 1):
                    try:
                        name_elem = card.find('span', class_='prdct-desc-cntnr-name')
                        brand_elem = card.find('span', class_='prdct-desc-cntnr-ttl')
                        price_elem = card.find('div', class_='prc-box-dscntd')
                        link_elem = card.find('a')

                        if name_elem and price_elem:
                            name = name_elem.text.strip()
                            brand = brand_elem.text.strip() if brand_elem else 'Bilinmiyor'
                            price = float(price_elem.text.replace(' TL', '').replace(',', '.'))
                            url = 'https://www.trendyol.com' + link_elem['href'] if link_elem else ''

                            cursor.execute("""
                                INSERT INTO products (
                                    name, brand, price, url, site_name,
                                    in_stock, created_at
                                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (name, brand, price, url, 'Trendyol', 1, datetime.now()))

                            print(f"  {idx}. ✅ {name[:40]}")

                    except Exception as e:
                        continue

                conn.commit()

        else:
            print(f"❌ HTTP {response.status_code} hatası")

    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")

    finally:
        # Sonuç raporu
        cursor.execute("SELECT COUNT(*) FROM products WHERE site_name='Trendyol'")
        product_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM product_reviews WHERE scraped_at IS NOT NULL")
        review_count = cursor.fetchone()[0]

        print("\n" + "="*60)
        print("📊 SONUÇ")
        print("="*60)
        print(f"✅ Toplam ürün: {product_count}")
        print(f"💬 Toplam yorum: {review_count}")
        print("="*60)

        conn.close()

if __name__ == "__main__":
    # Cloudscraper kurulumu kontrol et
    try:
        import cloudscraper
        print("✅ Cloudscraper kurulu")
    except ImportError:
        print("📦 Cloudscraper kuruluyor...")
        import subprocess
        subprocess.run(["pip", "install", "cloudscraper"], check=True)
        import cloudscraper

    scrape_with_cloudscraper()