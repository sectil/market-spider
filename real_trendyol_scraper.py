#!/usr/bin/env python3
"""
🔧 GERÇEK TRENDYOL SCRAPER - Kalıcı Çözüm
Proxy desteği, rate limiting ve hata yönetimi ile
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TrendyolScraper:
    def __init__(self, use_proxy=False):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(self.headers)

        # Proxy ayarları (opsiyonel)
        if use_proxy:
            self.proxies = {
                'http': 'http://your_proxy:port',
                'https': 'http://your_proxy:port'
            }
        else:
            self.proxies = None

        # Rate limiting
        self.min_delay = 2
        self.max_delay = 5

    def get_product_reviews_api(self, product_id: str, merchant_id: str, page: int = 1) -> Optional[Dict]:
        """Trendyol API'sinden yorumları çek"""

        # Trendyol'un gerçek API endpoint'i
        api_url = f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/rating/review"

        params = {
            'merchantId': merchant_id,
            'productId': product_id,
            'page': page,
            'size': 50,
            'order': 'most_helpful'
        }

        try:
            time.sleep(random.uniform(self.min_delay, self.max_delay))

            response = self.session.get(
                api_url,
                params=params,
                proxies=self.proxies,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API yanıt kodu: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"API hatası: {e}")
            return None

    def scrape_product_page(self, url: str) -> Optional[Dict]:
        """Ürün sayfasından bilgileri çek"""

        try:
            time.sleep(random.uniform(self.min_delay, self.max_delay))

            response = self.session.get(url, proxies=self.proxies, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Sayfa içindeki JSON-LD verilerini bul
            json_ld = soup.find('script', {'type': 'application/ld+json'})
            if json_ld:
                product_data = json.loads(json_ld.string)

                # Ürün bilgilerini çıkar
                result = {
                    'name': product_data.get('name'),
                    'brand': product_data.get('brand', {}).get('name'),
                    'price': float(product_data.get('offers', {}).get('price', 0)),
                    'rating': float(product_data.get('aggregateRating', {}).get('ratingValue', 0)),
                    'review_count': int(product_data.get('aggregateRating', {}).get('reviewCount', 0)),
                    'url': url,
                    'image': product_data.get('image'),
                    'description': product_data.get('description'),
                }

                # Product ID'yi URL'den çıkar
                if '/p-' in url:
                    product_id = url.split('/p-')[-1].split('?')[0]
                    result['product_id'] = product_id

                    # Merchant ID'yi bul
                    merchant_match = url.split('merchantId=')
                    if len(merchant_match) > 1:
                        result['merchant_id'] = merchant_match[1].split('&')[0]

                return result

        except Exception as e:
            logger.error(f"Sayfa scraping hatası: {e}")
            return None

    def scrape_category_products(self, category_url: str, max_pages: int = 5) -> List[Dict]:
        """Kategori sayfasından ürünleri topla"""

        products = []

        for page in range(1, max_pages + 1):
            try:
                url = f"{category_url}?pi={page}"
                time.sleep(random.uniform(self.min_delay, self.max_delay))

                response = self.session.get(url, proxies=self.proxies, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Ürün kartlarını bul
                product_cards = soup.find_all('div', {'class': 'p-card-wrppr'})

                for card in product_cards:
                    try:
                        link = card.find('a')
                        if link and link.get('href'):
                            product_url = 'https://www.trendyol.com' + link['href']

                            # Ürün bilgilerini çek
                            product = {
                                'url': product_url,
                                'name': card.find('span', {'class': 'prdct-desc-cntnr-name'}).text.strip(),
                                'brand': card.find('span', {'class': 'prdct-desc-cntnr-ttl'}).text.strip(),
                                'price': float(card.find('div', {'class': 'prc-box-dscntd'}).text.replace('TL', '').replace(',', '.')),
                            }

                            # Rating varsa ekle
                            rating_elem = card.find('div', {'class': 'ratings-container'})
                            if rating_elem:
                                product['rating'] = float(rating_elem.get('data-rating', 0))

                            products.append(product)

                    except Exception as e:
                        logger.warning(f"Ürün kartı parse hatası: {e}")
                        continue

                logger.info(f"Sayfa {page}: {len(product_cards)} ürün bulundu")

            except Exception as e:
                logger.error(f"Kategori sayfa {page} hatası: {e}")
                break

        return products

def update_database_with_real_data():
    """Veritabanını gerçek verilerle güncelle"""

    scraper = TrendyolScraper(use_proxy=False)
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    # Popüler kategorileri tara
    categories = [
        'https://www.trendyol.com/cok-satanlar',
        'https://www.trendyol.com/kadin-giyim',
        'https://www.trendyol.com/erkek-giyim',
        'https://www.trendyol.com/elektronik',
        'https://www.trendyol.com/ev-yasam'
    ]

    total_products = 0
    total_reviews = 0

    for category_url in categories:
        logger.info(f"Kategori taranıyor: {category_url}")
        products = scraper.scrape_category_products(category_url, max_pages=2)

        for product in products:
            try:
                # Detaylı ürün bilgilerini al
                detailed = scraper.scrape_product_page(product['url'])
                if detailed:
                    # Veritabanına ekle
                    cursor.execute("""
                        INSERT OR REPLACE INTO products (
                            name, brand, price, rating, review_count,
                            url, site_name, in_stock, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        detailed['name'],
                        detailed['brand'],
                        detailed['price'],
                        detailed['rating'],
                        detailed['review_count'],
                        detailed['url'],
                        'Trendyol',
                        1,
                        datetime.now()
                    ))

                    product_id = cursor.lastrowid
                    total_products += 1

                    # Yorumları çek (eğer product_id ve merchant_id varsa)
                    if 'product_id' in detailed and 'merchant_id' in detailed:
                        reviews_data = scraper.get_product_reviews_api(
                            detailed['product_id'],
                            detailed['merchant_id']
                        )

                        if reviews_data and 'result' in reviews_data:
                            for review in reviews_data['result'].get('productReviews', {}).get('content', []):
                                try:
                                    cursor.execute("""
                                        INSERT INTO product_reviews (
                                            product_id, reviewer_name, rating,
                                            review_text, review_date, helpful_count,
                                            sentiment_score, scraped_at
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        product_id,
                                        review.get('userFullName', 'Anonim'),
                                        review.get('rate', 0),
                                        review.get('comment', ''),
                                        datetime.fromtimestamp(review.get('lastModifiedDate', 0) / 1000),
                                        review.get('helpfulCount', 0),
                                        1.0 if review.get('rate', 0) >= 4 else -1.0 if review.get('rate', 0) <= 2 else 0.0,
                                        datetime.now()
                                    ))
                                    total_reviews += 1
                                except Exception as e:
                                    logger.warning(f"Yorum ekleme hatası: {e}")

            except Exception as e:
                logger.error(f"Ürün işleme hatası: {e}")
                continue

        conn.commit()

    conn.close()

    logger.info(f"""
    ==========================================
    SCRAPING TAMAMLANDI
    ==========================================
    Toplam ürün: {total_products}
    Toplam yorum: {total_reviews}
    ==========================================
    """)

def setup_alternative_solution():
    """Alternatif veri kaynakları ve çözümler"""

    print("""
    ==========================================
    🔧 ALTERNATİF ÇÖZÜMLER
    ==========================================

    1. PROXY KULLANIMI:
       - ProxyMesh, Bright Data gibi servisler
       - Residential proxy'ler daha etkili
       - Rotating proxy listesi kullan

    2. API ENTEGRASYONU:
       - Trendyol API ortaklığı başvurusu
       - RapidAPI üzerinden alternatifler
       - Web scraping servisleri (ScraperAPI, Scrapfly)

    3. BROWSER AUTOMATION:
       - Selenium Grid kurulumu
       - Playwright Cloud servisleri
       - Browserless.io gibi headless servisler

    4. VERİ SATIN ALMA:
       - Bright Data, Oxylabs veri marketleri
       - Hazır e-ticaret veri setleri

    5. CLOUDFLARE BYPASS:
       - Cloudflare Workers kullanımı
       - FlareSolverr proxy kurulumu
       - Undetected-chromedriver kullanımı

    6. RATE LIMITING ÇÖZÜMÜ:
       - İstekler arası 5-10 saniye bekle
       - Rastgele User-Agent rotasyonu
       - Session cookie'leri sakla ve kullan

    7. DOCKER CONTAINER:
       - Tüm bağımlılıklar ile hazır imaj
       - VPN entegrasyonu
       - Tor network üzerinden
    ==========================================
    """)

if __name__ == "__main__":
    print("Gerçek veri çekme işlemi başlatılıyor...")

    try:
        # Önce basit test
        scraper = TrendyolScraper()
        test_url = "https://www.trendyol.com/sr?q=laptop&qt=laptop&st=laptop&os=1"

        response = scraper.session.get(test_url, timeout=5)
        if response.status_code == 200:
            print("✅ Trendyol'a bağlantı başarılı!")
            update_database_with_real_data()
        else:
            print(f"⚠️ Bağlantı sorunu: {response.status_code}")
            setup_alternative_solution()

    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")
        setup_alternative_solution()