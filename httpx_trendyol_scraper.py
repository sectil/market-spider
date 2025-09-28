#!/usr/bin/env python3
"""
🔥 HTTPX ile Trendyol Scraper - HTTP/2 desteği ile
"""

import httpx
from fake_useragent import UserAgent
import sqlite3
from datetime import datetime
import json
import time
import random

def scrape_with_httpx():
    """HTTPX ile HTTP/2 kullanarak Trendyol'dan veri çek"""

    ua = UserAgent()

    # HTTP/2 destekli client
    client = httpx.Client(
        http2=True,
        follow_redirects=True,
        timeout=30.0,
        headers={
            'User-Agent': ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
        }
    )

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*60)
    print("🔥 HTTPX İLE GERÇEK VERİ ÇEKME")
    print("="*60)

    # Simülasyon verileri temizle
    cursor.execute("DELETE FROM product_reviews WHERE scraped_at IS NULL")
    cursor.execute("DELETE FROM products WHERE url LIKE '%example.com%'")
    conn.commit()

    urls_to_try = [
        "https://www.trendyol.com/cok-satanlar",
        "https://www.trendyol.com/sr?q=laptop",
        "https://www.trendyol.com/kadin",
        "https://public.trendyol.com/discovery-web-websfxproductrecommendation-santral/api/best-selling"
    ]

    for url in urls_to_try:
        print(f"\n🔍 Deneniyor: {url}")
        time.sleep(random.uniform(2, 4))

        try:
            response = client.get(url)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                # JSON endpoint mi kontrol et
                if 'api' in url:
                    try:
                        data = response.json()
                        if 'result' in data or 'products' in data:
                            products = data.get('result', data.get('products', []))

                            for product in products[:10]:
                                name = product.get('name', '')
                                brand = product.get('brand', '')
                                price = product.get('price', 0)

                                cursor.execute("""
                                    INSERT INTO products (name, brand, price, url, site_name, created_at, in_stock)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """, (name, brand, price, url, "Trendyol", datetime.now(), 1))

                                print(f"   ✅ Eklendi: {name[:30]}")

                            conn.commit()
                            print(f"   ✅ API'den {len(products)} ürün alındı")
                    except:
                        pass

                # HTML içeriği
                else:
                    # Sayfa içinde JavaScript verisi ara
                    content = response.text
                    if 'window.__SEARCH_APP_INITIAL_STATE__' in content:
                        start = content.find('window.__SEARCH_APP_INITIAL_STATE__ = ') + 39
                        end = content.find('};', start) + 1

                        if start > 39 and end > start:
                            try:
                                json_str = content[start:end]
                                data = json.loads(json_str)

                                if 'products' in data:
                                    products = data['products']
                                    for product in products[:10]:
                                        name = product.get('name', '')
                                        brand = product.get('brand', {}).get('name', '')
                                        price = product.get('price', {}).get('sellingPrice', 0)

                                        cursor.execute("""
                                            INSERT INTO products (name, brand, price, url, site_name, created_at, in_stock)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (name, brand, price, url, "Trendyol", datetime.now(), 1))

                                    conn.commit()
                                    print(f"   ✅ HTML'den {len(products)} ürün parse edildi")
                            except:
                                pass

        except httpx.HTTPError as e:
            print(f"   ❌ Hata: {e}")

    # Sonuç
    cursor.execute("SELECT COUNT(*) FROM products WHERE site_name='Trendyol'")
    total = cursor.fetchone()[0]

    print("\n" + "="*60)
    print(f"✅ Toplam {total} Trendyol ürünü veritabanında")
    print("="*60)

    conn.close()
    client.close()

if __name__ == "__main__":
    scrape_with_httpx()