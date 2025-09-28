#!/usr/bin/env python3
"""
🚀 GITHUB ACTIONS İÇİN GELİŞMİŞ TRENDYOL SCRAPER
Gerçek veri toplama - Simülasyon YOK!
"""

import os
import sys
import json
import time
import random
import sqlite3
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any

# Selenium imports
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    USE_UNDETECTED = True
except ImportError:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    USE_UNDETECTED = False

# HTTP imports
import requests
from bs4 import BeautifulSoup
import cloudscraper
from fake_useragent import UserAgent

class TrendyolRealDataScraper:
    def __init__(self):
        self.conn = sqlite3.connect('market_spider.db')
        self.cursor = self.conn.cursor()
        self.ua = UserAgent()
        self.products_scraped = 0
        self.reviews_scraped = 0

        # GitHub Actions ortamında mıyız?
        self.is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

        # Log dosyası
        os.makedirs('logs', exist_ok=True)
        self.log_file = open(f'logs/scraping_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 'w', encoding='utf-8')

        self._log("🚀 Trendyol Gerçek Veri Scraper başlatıldı")
        self._log(f"GitHub Actions: {self.is_github_actions}")
        self._log(f"Undetected ChromeDriver: {USE_UNDETECTED}")

    def _log(self, message):
        """Log mesajı yaz"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        self.log_file.write(log_msg + "\n")
        self.log_file.flush()

    def setup_driver(self):
        """Selenium driver kurulumu"""
        options = webdriver.ChromeOptions() if not USE_UNDETECTED else uc.ChromeOptions()

        # Headless mod (GitHub Actions için zorunlu)
        if self.is_github_actions:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

        # Genel ayarlar
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(f'user-agent={self.ua.chrome}')

        # Anti-detection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        if USE_UNDETECTED:
            driver = uc.Chrome(options=options, version_main=120)
        else:
            driver = webdriver.Chrome(options=options)

        # JavaScript anti-detection
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": self.ua.chrome
        })

        return driver

    def scrape_with_selenium(self):
        """Selenium ile veri çek"""
        self._log("🌐 Selenium ile scraping başlıyor...")

        try:
            driver = self.setup_driver()

            # Ana sayfa
            self._log("Trendyol ana sayfasına gidiliyor...")
            driver.get("https://www.trendyol.com")
            time.sleep(random.uniform(3, 5))

            # Çok satanlar sayfası
            self._log("Çok satanlar sayfasına gidiliyor...")
            driver.get("https://www.trendyol.com/cok-satanlar")
            time.sleep(random.uniform(5, 8))

            # Sayfayı scroll et (lazy loading için)
            self._log("Sayfa scroll ediliyor...")
            for i in range(5):
                driver.execute_script(f"window.scrollTo(0, {i * 1000});")
                time.sleep(random.uniform(1, 2))

            # Ürünleri topla
            products = self._extract_products_selenium(driver)

            # Kategori sayfaları
            categories = [
                "elektronik", "moda", "kozmetik", "ev-yasam",
                "supermarket", "anne-cocuk", "spor-outdoor"
            ]

            for category in categories:
                try:
                    self._log(f"📂 {category} kategorisi taranıyor...")
                    driver.get(f"https://www.trendyol.com/{category}")
                    time.sleep(random.uniform(3, 5))

                    # Scroll
                    for i in range(3):
                        driver.execute_script(f"window.scrollTo(0, {i * 1000});")
                        time.sleep(1)

                    # Ürünleri çek
                    cat_products = self._extract_products_selenium(driver)
                    products.extend(cat_products)

                except Exception as e:
                    self._log(f"❌ {category} kategorisi hata: {e}")

            driver.quit()
            return products

        except Exception as e:
            self._log(f"❌ Selenium hata: {e}")
            if 'driver' in locals():
                driver.quit()
            return []

    def _extract_products_selenium(self, driver) -> List[Dict]:
        """Selenium ile ürün verilerini çıkar"""
        products = []

        try:
            # JavaScript ile veri çek
            product_data = driver.execute_script("""
                var products = [];
                var items = document.querySelectorAll('.p-card-wrppr, .product-card, [data-id]');

                items.forEach(function(item) {
                    var product = {};

                    // Ürün adı
                    var nameEl = item.querySelector('.prdct-desc-cntnr-name, .product-name, h3');
                    product.name = nameEl ? nameEl.innerText : '';

                    // Marka
                    var brandEl = item.querySelector('.prdct-desc-cntnr-ttl, .product-brand, .brand');
                    product.brand = brandEl ? brandEl.innerText : '';

                    // Fiyat
                    var priceEl = item.querySelector('.prc-box-dscntd, .price, [class*="price"]');
                    product.price = priceEl ? priceEl.innerText : '';

                    // Rating
                    var ratingEl = item.querySelector('.rating-score, .star-rating, [class*="rating"]');
                    product.rating = ratingEl ? ratingEl.innerText : '';

                    // Yorum sayısı
                    var reviewEl = item.querySelector('.rating-count, .review-count, [class*="review"]');
                    product.reviewCount = reviewEl ? reviewEl.innerText : '';

                    // URL
                    var linkEl = item.querySelector('a');
                    product.url = linkEl ? linkEl.href : '';

                    // Resim
                    var imgEl = item.querySelector('img');
                    product.image = imgEl ? imgEl.src : '';

                    if (product.name) {
                        products.push(product);
                    }
                });

                return products;
            """)

            for p in product_data[:50]:  # İlk 50 ürün
                if p.get('name'):
                    # Fiyatı temizle
                    price_str = p.get('price', '0')
                    price = self._clean_price(price_str)

                    # Rating'i temizle
                    rating = self._clean_rating(p.get('rating', '0'))

                    # Review count'u temizle
                    review_count = self._clean_review_count(p.get('reviewCount', '0'))

                    products.append({
                        'name': p['name'],
                        'brand': p.get('brand', ''),
                        'price': price,
                        'rating': rating,
                        'review_count': review_count,
                        'url': p.get('url', ''),
                        'image_url': p.get('image', '')
                    })

            self._log(f"✅ {len(products)} ürün bulundu")

        except Exception as e:
            self._log(f"❌ Ürün çıkarma hatası: {e}")

        return products

    def scrape_with_api(self):
        """API endpoint'lerinden veri çek"""
        self._log("🔌 API endpoint'leri deneniyor...")

        endpoints = [
            {
                'url': 'https://public.trendyol.com/discovery-web-websfxproductrecommendation-santral/api/best-selling',
                'method': 'GET'
            },
            {
                'url': 'https://api.trendyol.com/webapicontent/v2/best-seller-products',
                'method': 'GET'
            },
            {
                'url': 'https://public-mdc.trendyol.com/discovery-web-recogw-service/api/favorites/counts',
                'method': 'GET'
            }
        ]

        products = []
        session = cloudscraper.create_scraper()

        for endpoint in endpoints:
            try:
                self._log(f"API deneniyor: {endpoint['url']}")

                headers = {
                    'User-Agent': self.ua.chrome,
                    'Accept': 'application/json',
                    'Accept-Language': 'tr-TR,tr;q=0.9',
                    'Referer': 'https://www.trendyol.com/',
                    'X-Storefront-Id': 'TR',
                    'X-Application-Id': 'web'
                }

                response = session.get(endpoint['url'], headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    self._log(f"✅ API başarılı: {endpoint['url']}")

                    # Veriyi parse et
                    if 'result' in data:
                        items = data['result']
                    elif 'products' in data:
                        items = data['products']
                    elif 'content' in data:
                        items = data['content']
                    else:
                        items = []

                    for item in items[:20]:
                        product = self._parse_api_product(item)
                        if product:
                            products.append(product)

                else:
                    self._log(f"❌ API {response.status_code}: {endpoint['url']}")

            except Exception as e:
                self._log(f"❌ API hatası: {e}")

        return products

    def _parse_api_product(self, item: Dict) -> Dict:
        """API verisinden ürün bilgisi çıkar"""
        try:
            return {
                'name': item.get('name', item.get('title', '')),
                'brand': item.get('brand', {}).get('name', item.get('brandName', '')),
                'price': float(item.get('price', {}).get('sellingPrice', item.get('sellingPrice', 0))),
                'rating': float(item.get('ratingScore', {}).get('averageRating', item.get('rating', 0))),
                'review_count': int(item.get('ratingScore', {}).get('totalCount', item.get('reviewCount', 0))),
                'url': f"https://www.trendyol.com{item.get('url', '')}",
                'image_url': item.get('images', [{}])[0].get('url', '') if item.get('images') else ''
            }
        except:
            return None

    def scrape_reviews(self, product_id: int, product_url: str):
        """Ürün yorumlarını çek"""
        if not product_url:
            return

        try:
            # URL'den ürün ID'sini çıkar
            trendyol_product_id = product_url.split('-p-')[-1].split('?')[0] if '-p-' in product_url else None

            if not trendyol_product_id:
                return

            # Yorum API'si
            review_url = f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/review/discussions/{trendyol_product_id}"

            headers = {
                'User-Agent': self.ua.chrome,
                'Accept': 'application/json',
                'Referer': product_url
            }

            session = cloudscraper.create_scraper()
            response = session.get(review_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                reviews = data.get('result', {}).get('discussions', [])

                for review in reviews[:10]:  # İlk 10 yorum
                    self._save_review(product_id, review)
                    self.reviews_scraped += 1

                self._log(f"✅ {len(reviews)} yorum eklendi")

        except Exception as e:
            self._log(f"❌ Yorum çekme hatası: {e}")

    def _save_review(self, product_id: int, review_data: Dict):
        """Yorumu veritabanına kaydet"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO product_reviews (
                    product_id, reviewer_name, rating, review_text,
                    review_date, helpful_count, sentiment_score, scraped_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id,
                review_data.get('userFullName', 'Anonim'),
                float(review_data.get('rate', 0)),
                review_data.get('comment', ''),
                datetime.fromisoformat(review_data.get('commentDateISOType', datetime.now().isoformat())),
                int(review_data.get('helpfulCount', 0)),
                self._calculate_sentiment(review_data.get('comment', '')),
                datetime.now()
            ))
        except Exception as e:
            self._log(f"Yorum kaydetme hatası: {e}")

    def _calculate_sentiment(self, text: str) -> float:
        """Basit sentiment analizi"""
        if not text:
            return 0.5

        positive_words = ['harika', 'mükemmel', 'güzel', 'kaliteli', 'memnun', 'tavsiye', 'beğendim']
        negative_words = ['kötü', 'berbat', 'pişman', 'bozuk', 'kalitesiz', 'rezalet', 'beğenmedim']

        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count + neg_count == 0:
            return 0.5
        return pos_count / (pos_count + neg_count)

    def _clean_price(self, price_str: str) -> float:
        """Fiyat string'ini temizle"""
        try:
            cleaned = price_str.replace('TL', '').replace('₺', '').replace('.', '').replace(',', '.').strip()
            return float(cleaned)
        except:
            return 0.0

    def _clean_rating(self, rating_str: str) -> float:
        """Rating string'ini temizle"""
        try:
            cleaned = rating_str.replace(',', '.').strip()
            return float(cleaned)
        except:
            return 0.0

    def _clean_review_count(self, count_str: str) -> int:
        """Yorum sayısını temizle"""
        try:
            # Parantez içindeki sayıyı al
            if '(' in count_str:
                count_str = count_str.split('(')[1].split(')')[0]
            cleaned = count_str.replace('.', '').replace(',', '').strip()
            return int(cleaned)
        except:
            return 0

    def save_products(self, products: List[Dict]):
        """Ürünleri veritabanına kaydet"""
        for product in products:
            try:
                # Önce ürünü kaydet
                self.cursor.execute("""
                    INSERT OR REPLACE INTO products (
                        name, brand, price, rating, review_count,
                        url, site_name, in_stock, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product['name'],
                    product['brand'],
                    product['price'],
                    product['rating'],
                    product['review_count'],
                    product['url'],
                    'Trendyol',
                    1,
                    datetime.now(),
                    datetime.now()
                ))

                product_id = self.cursor.lastrowid
                self.products_scraped += 1

                # Yorumları çek
                if product['url']:
                    self.scrape_reviews(product_id, product['url'])

            except Exception as e:
                self._log(f"Ürün kaydetme hatası: {e}")

        self.conn.commit()

    def clean_simulation_data(self):
        """Simülasyon verilerini temizle"""
        self._log("🧹 Simülasyon verileri temizleniyor...")

        # Simülasyon yorumlarını sil
        self.cursor.execute("""
            DELETE FROM product_reviews
            WHERE scraped_at IS NULL
            OR review_text LIKE '%harika%ürün%'
            OR review_text LIKE '%süper%kalite%'
        """)

        # URL'si olmayan ürünleri sil
        self.cursor.execute("""
            DELETE FROM products
            WHERE url IS NULL
            OR url = ''
            OR url LIKE '%example.com%'
        """)

        self.conn.commit()
        self._log("✅ Simülasyon verileri temizlendi")

    def run(self):
        """Ana scraping işlemi"""
        self._log("="*60)
        self._log("🚀 GERÇEK VERİ TOPLAMA BAŞLIYOR")
        self._log("="*60)

        # Önce simülasyon verilerini temizle
        self.clean_simulation_data()

        all_products = []

        # 1. Selenium ile dene
        selenium_products = self.scrape_with_selenium()
        all_products.extend(selenium_products)

        # 2. API ile dene
        api_products = self.scrape_with_api()
        all_products.extend(api_products)

        # 3. Ürünleri kaydet
        if all_products:
            self._log(f"\n📊 Toplam {len(all_products)} ürün bulundu")
            self.save_products(all_products)

            # CSV'ye kaydet
            df = pd.DataFrame(all_products)
            df.to_csv('scraped_products.csv', index=False, encoding='utf-8')
            self._log(f"✅ CSV dosyası oluşturuldu: scraped_products.csv")
        else:
            self._log("❌ Hiç ürün bulunamadı")

        # Özet
        self._log("\n" + "="*60)
        self._log("📊 SCRAPING ÖZET")
        self._log(f"✅ Toplam ürün: {self.products_scraped}")
        self._log(f"✅ Toplam yorum: {self.reviews_scraped}")

        # Veritabanı istatistikleri
        total_products = self.cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        total_reviews = self.cursor.execute("SELECT COUNT(*) FROM product_reviews").fetchone()[0]

        self._log(f"📦 Veritabanında toplam ürün: {total_products}")
        self._log(f"💬 Veritabanında toplam yorum: {total_reviews}")
        self._log("="*60)

        # Temizlik
        self.conn.close()
        self.log_file.close()

        return self.products_scraped > 0

if __name__ == "__main__":
    scraper = TrendyolRealDataScraper()
    success = scraper.run()

    # GitHub Actions için çıkış kodu
    sys.exit(0 if success else 1)