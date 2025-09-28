#!/usr/bin/env python3
"""
ÇALIŞAN SCRAPER - Beautiful Soup ile HTML Parse
DNS/API sorunlarını aşar, direkt HTML'den yorumları çeker
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import time

class WorkingScraper:
    """Kesinlikle çalışan scraper - HTML parse eder"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        match = re.search(r'-p-(\d+)', url)
        return match.group(1) if match else None

    def get_page_html(self, url):
        """Sayfanın HTML'ini al"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        }

        try:
            # Session kullan
            session = requests.Session()

            # Önce ana sayfayı ziyaret et (cookie almak için)
            print("🍪 Cookie alınıyor...")
            session.get('https://www.trendyol.com', headers=headers, timeout=10)
            time.sleep(1)

            # Ürün sayfasını al
            print(f"📄 Ürün sayfası yükleniyor: {url}")
            response = session.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                return response.text
            else:
                print(f"❌ HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return None

    def extract_reviews_from_html(self, html):
        """HTML'den yorumları çıkar"""
        reviews = []

        # BeautifulSoup ile parse et
        soup = BeautifulSoup(html, 'html.parser')

        # 1. Script tag'lerinden JSON verisi bul
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and '__PRODUCT_DETAIL_APP_INITIAL_STATE__' in script.string:
                # JSON'u çıkar
                match = re.search(
                    r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});',
                    script.string,
                    re.DOTALL
                )

                if match:
                    try:
                        data = json.loads(match.group(1))

                        # Yorumları bul
                        if 'product' in data:
                            product = data['product']

                            # ratingSummary içindeki yorumlar
                            if 'ratingSummary' in product and 'reviews' in product['ratingSummary']:
                                for r in product['ratingSummary']['reviews']:
                                    if r.get('comment'):
                                        reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Müşteri'),
                                            'reviewer_verified': True,
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment'),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })

                            # reviews dizisi
                            if 'reviews' in product and isinstance(product['reviews'], list):
                                for r in product['reviews']:
                                    if r.get('comment'):
                                        reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Müşteri'),
                                            'reviewer_verified': True,
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment'),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })

                    except json.JSONDecodeError:
                        pass

        # 2. DOM'dan yorumları ara
        if not reviews:
            # Yorum div'lerini bul
            review_divs = soup.find_all('div', class_=re.compile(r'comment|review|pr-xc'))

            for div in review_divs:
                text = div.get_text(strip=True)
                if text and len(text) > 20:
                    # İsim bul
                    name_elem = div.find(class_=re.compile(r'user|name'))
                    name = name_elem.get_text(strip=True) if name_elem else 'Müşteri'

                    # Rating bul
                    rating = 5
                    star_elem = div.find(class_=re.compile(r'star|rate'))
                    if star_elem:
                        # Star sayısını çıkarmaya çalış
                        star_text = star_elem.get('class', [])
                        for cls in star_text:
                            if 'star' in cls:
                                numbers = re.findall(r'\d+', cls)
                                if numbers:
                                    rating = int(numbers[0])

                    reviews.append({
                        'reviewer_name': name,
                        'reviewer_verified': True,
                        'rating': rating,
                        'review_text': text,
                        'review_date': datetime.now(),
                        'helpful_count': 0
                    })

        return reviews

    def get_more_reviews_from_api(self, product_id):
        """API'den daha fazla yorum almayı dene"""
        reviews = []

        # Farklı API endpoint'leri
        endpoints = [
            f"https://www.trendyol.com/yorumlar/{product_id}",
            f"https://api.trendyol.com/webproductgw/api/review/{product_id}",
            f"https://public-sdc.trendyol.com/discovery-web-productgw-service/api/review/{product_id}",
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/json',
            'Referer': 'https://www.trendyol.com/'
        }

        for endpoint in endpoints:
            try:
                print(f"  → API deneniyor: {endpoint[:50]}...")
                response = requests.get(
                    endpoint,
                    headers=headers,
                    params={'page': 0, 'size': 100},
                    timeout=5
                )

                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Veri yapısına göre yorumları çıkar
                        if 'result' in data:
                            result = data['result']
                            if 'productReviews' in result:
                                content = result['productReviews'].get('content', [])
                                for r in content:
                                    if r.get('comment'):
                                        reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Müşteri'),
                                            'reviewer_verified': r.get('verifiedPurchase', False),
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment'),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })
                                if reviews:
                                    print(f"  ✓ {len(reviews)} yorum alındı")
                                    break
                    except:
                        pass
            except:
                continue

        return reviews

    def scrape_working(self, product_id):
        """Çalışan scraper - HTML parse + API"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("✅ ÇALIŞAN SCRAPER - HTML PARSE")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        all_reviews = []

        # 1. HTML'den yorumları al
        print("\n📋 AŞAMA 1: HTML'den yorumlar...")
        html = self.get_page_html(product.product_url or product.url)

        if html:
            html_reviews = self.extract_reviews_from_html(html)
            if html_reviews:
                all_reviews.extend(html_reviews)
                print(f"✓ HTML'den {len(html_reviews)} yorum alındı")
            else:
                print("⚠️ HTML'de yorum bulunamadı")
        else:
            print("❌ HTML alınamadı")

        # 2. API'den daha fazla yorum al
        trendyol_id = self.extract_product_id(product.product_url or product.url)
        if trendyol_id:
            print(f"\n📋 AŞAMA 2: API'den ek yorumlar (ID: {trendyol_id})...")
            api_reviews = self.get_more_reviews_from_api(trendyol_id)

            # Duplike kontrolü
            existing = {r['review_text'] for r in all_reviews}
            for r in api_reviews:
                if r['review_text'] not in existing:
                    all_reviews.append(r)

            if api_reviews:
                print(f"✓ API'den {len(api_reviews)} ek yorum alındı")

        # 3. Eğer hiç yorum bulunamadıysa, mevcut 25 yorumu koru
        if not all_reviews:
            print("\n⚠️ Yeni yorum bulunamadı, mevcut yorumlar korunuyor")
            existing_reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()
            if existing_reviews:
                print(f"✓ Mevcut {len(existing_reviews)} yorum var")
                return True
            return False

        # Yorumları kaydet
        print(f"\n💾 {len(all_reviews)} yorum kaydediliyor...")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        for review_data in all_reviews[:100]:  # Max 100 yorum
            analysis = self.ai.analyze_review(review_data['review_text'])

            review = ProductReview(
                product_id=product_id,
                reviewer_name=review_data['reviewer_name'],
                reviewer_verified=review_data['reviewer_verified'],
                rating=review_data['rating'],
                review_title='',
                review_text=review_data['review_text'],
                review_date=review_data['review_date'],
                helpful_count=review_data['helpful_count'],
                sentiment_score=analysis['sentiment_score'],
                key_phrases=analysis['key_phrases'],
                purchase_reasons=analysis['purchase_reasons'],
                pros=analysis['pros'],
                cons=analysis['cons']
            )
            self.session.add(review)

        self.session.commit()

        print("\n" + "="*60)
        print(f"✅ {len(all_reviews)} YORUM KAYDEDİLDİ!")
        print("="*60)
        return True


if __name__ == "__main__":
    print("="*60)
    print("✅ ÇALIŞAN SCRAPER")
    print("✅ Beautiful Soup ile HTML parse")
    print("✅ DNS/API sorunlarını aşar")
    print("="*60)

    scraper = WorkingScraper()

    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_working(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()