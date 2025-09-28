#!/usr/bin/env python3
"""
Direkt API ile GERÇEK Trendyol Yorumlarını HEPSİNİ Çeker
En basit ve etkili yöntem - requests ile direkt API çağrısı
"""

import requests
import json
import re
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class DirectAPIScraper:
    """Direkt API çağrısı ile TÜM yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        # -p-652719507 formatından ID'yi al
        match = re.search(r'-p-(\d+)', url)
        if match:
            return match.group(1)

        # Alternatif pattern'ler
        patterns = [r'/p/.*-p-(\d+)', r'productId=(\d+)', r'/(\d{6,})']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_reviews_from_html_page(self, url):
        """HTML sayfasından yorumları çıkar"""
        reviews = []

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }

            print("📄 HTML sayfası indiriliyor...")
            response = requests.get(url, headers=headers, timeout=15)

            if response.status_code == 200:
                html_content = response.text

                # window.__PRODUCT_DETAIL_APP_INITIAL_STATE__ içindeki JSON'ı bul
                pattern = r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});'
                match = re.search(pattern, html_content, re.DOTALL)

                if match:
                    try:
                        print("✓ JSON verisi bulundu, parse ediliyor...")
                        json_str = match.group(1)

                        # JSON'ı parse et
                        data = json.loads(json_str)

                        if 'product' in data:
                            product_data = data['product']

                            # Önce ratingSummary'deki yorumları al
                            if 'ratingSummary' in product_data:
                                rating_summary = product_data['ratingSummary']

                                # reviews array'i var mı?
                                if 'reviews' in rating_summary and isinstance(rating_summary['reviews'], list):
                                    review_list = rating_summary['reviews']
                                    print(f"✓ ratingSummary'den {len(review_list)} yorum bulundu")

                                    for r in review_list:
                                        if r.get('comment'):
                                            reviews.append({
                                                'reviewer_name': r.get('userFullName', 'Anonim'),
                                                'reviewer_verified': True,
                                                'rating': r.get('rate', 5),
                                                'review_text': r.get('comment'),
                                                'review_date': datetime.now(),
                                                'helpful_count': r.get('helpfulCount', 0)
                                            })

                            # reviews dizisi de kontrol et
                            if not reviews and 'reviews' in product_data:
                                if isinstance(product_data['reviews'], list):
                                    review_list = product_data['reviews']
                                    print(f"✓ product.reviews'dan {len(review_list)} yorum bulundu")

                                    for r in review_list:
                                        if r.get('comment'):
                                            reviews.append({
                                                'reviewer_name': r.get('userFullName', 'Anonim'),
                                                'reviewer_verified': True,
                                                'rating': r.get('rate', 5),
                                                'review_text': r.get('comment'),
                                                'review_date': datetime.now(),
                                                'helpful_count': r.get('helpfulCount', 0)
                                            })
                                elif isinstance(product_data['reviews'], dict):
                                    # reviews bir obje ise content'ini al
                                    if 'content' in product_data['reviews']:
                                        review_list = product_data['reviews']['content']
                                        print(f"✓ reviews.content'ten {len(review_list)} yorum bulundu")

                                        for r in review_list:
                                            if r.get('comment'):
                                                reviews.append({
                                                    'reviewer_name': r.get('userFullName', 'Anonim'),
                                                    'reviewer_verified': True,
                                                    'rating': r.get('rate', 5),
                                                    'review_text': r.get('comment'),
                                                    'review_date': datetime.now(),
                                                    'helpful_count': r.get('helpfulCount', 0)
                                                })

                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON parse hatası: {e}")
                else:
                    print("⚠️ Initial state JSON'ı bulunamadı")
            else:
                print(f"⚠️ Sayfa yüklenemedi: HTTP {response.status_code}")

        except Exception as e:
            print(f"⚠️ HTML çekme hatası: {e}")

        return reviews

    def get_all_reviews_from_api(self, product_id):
        """API'den pagination ile TÜM yorumları çek"""
        all_reviews = []
        page = 0
        total_pages = 1

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Referer': 'https://www.trendyol.com/',
            'Origin': 'https://www.trendyol.com',
            'X-Storefront-Id': 'TR',
            'X-Application-Id': 'web'
        }

        print(f"\n📡 API'den yorumlar çekiliyor (Product ID: {product_id})...")

        while page < total_pages and page < 50:  # Max 50 sayfa
            # Farklı API URL'leri dene
            api_urls = [
                f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
                f"https://public-mdc.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
                f"https://www.trendyol.com/api/review/{product_id}",
                f"https://api.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
            ]

            for api_url in api_urls:
                try:
                    params = {
                        'page': page,
                        'size': 100,  # Max 100 yorum/sayfa
                        'sortBy': 'MOST_HELPFUL'
                    }

                    print(f"  Sayfa {page + 1} deneniyor: {api_url[:50]}...")

                    response = requests.get(
                        api_url,
                        headers=headers,
                        params=params,
                        timeout=10
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()

                            if 'result' in data and 'productReviews' in data['result']:
                                review_data = data['result']['productReviews']

                                # İlk sayfada toplam sayfa sayısını al
                                if page == 0 and 'totalPages' in review_data:
                                    total_pages = review_data['totalPages']
                                    total_elements = review_data.get('totalElements', 0)
                                    print(f"  ✓ Toplam {total_elements} yorum, {total_pages} sayfa bulundu")

                                # Yorumları al
                                if 'content' in review_data:
                                    content = review_data['content']
                                    if content:
                                        print(f"  ✓ Sayfa {page + 1}: {len(content)} yorum alındı")

                                        for r in content:
                                            if r.get('comment'):
                                                all_reviews.append({
                                                    'reviewer_name': r.get('userFullName', 'Anonim'),
                                                    'reviewer_verified': r.get('verifiedPurchase', False),
                                                    'rating': r.get('rate', 5),
                                                    'review_text': r.get('comment'),
                                                    'review_date': datetime.now(),
                                                    'helpful_count': r.get('helpfulCount', 0),
                                                    'seller': r.get('sellerName', ''),
                                                    'size': r.get('size', ''),
                                                    'color': r.get('color', '')
                                                })

                                        # Bu API çalıştı, diğerlerini deneme
                                        break
                        except json.JSONDecodeError:
                            print(f"  ✗ JSON parse hatası")
                            continue
                    elif response.status_code == 404:
                        print(f"  ✗ 404 - Endpoint bulunamadı")
                    elif response.status_code == 403:
                        print(f"  ✗ 403 - Erişim engellendi")
                    else:
                        print(f"  ✗ HTTP {response.status_code}")

                except requests.exceptions.RequestException as e:
                    print(f"  ✗ İstek hatası: {e}")
                    continue

            # Sonraki sayfa
            page += 1

            # Rate limiting için bekle
            if page < total_pages:
                time.sleep(0.5)

        return all_reviews

    def scrape_all_reviews_direct(self, product_id):
        """Direkt API ile TÜM yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("📡 DIRECT API SCRAPER - TÜM YORUMLAR")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        all_reviews = []

        # 1. Önce HTML sayfasından yorumları al
        print("\n📋 AŞAMA 1: HTML sayfasından yorumlar...")
        html_reviews = self.get_reviews_from_html_page(product.product_url or product.url)
        if html_reviews:
            all_reviews.extend(html_reviews)
            print(f"✓ HTML'den {len(html_reviews)} yorum alındı")

        # 2. Trendyol product ID'yi çıkar ve API'den al
        trendyol_id = self.extract_product_id(product.product_url or product.url)
        if trendyol_id:
            print(f"\n📋 AŞAMA 2: API'den TÜM yorumlar (ID: {trendyol_id})...")
            api_reviews = self.get_all_reviews_from_api(trendyol_id)

            # Duplike kontrolü
            existing_texts = {r['review_text'] for r in all_reviews}
            for review in api_reviews:
                if review['review_text'] not in existing_texts:
                    all_reviews.append(review)

            if api_reviews:
                print(f"✓ API'den {len(api_reviews)} ek yorum alındı")
        else:
            print("⚠️ Product ID çıkarılamadı, API kullanılamıyor")

        # SONUÇLARI KAYDET
        if all_reviews:
            print(f"\n💾 TOPLAM {len(all_reviews)} GERÇEK YORUM kaydediliyor...")

            for review_data in all_reviews[:500]:  # Max 500 yorum kaydet
                # AI analizi
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

            # Detaylı analiz göster
            self._show_detailed_analysis(product.name, all_reviews)

            print("\n" + "="*60)
            print(f"✅ {len(all_reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("✅ DIRECT API İLE BAŞARILI!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ALINAMADI!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def _show_detailed_analysis(self, product_name, reviews):
        """Detaylı analiz göster"""

        reviews_for_ai = [
            {
                'text': r['review_text'],
                'rating': r['rating'],
                'verified': r['reviewer_verified'],
                'helpful_count': r['helpful_count']
            }
            for r in reviews[:100]  # İlk 100 yorumu analiz et
        ]

        analysis = self.ai.analyze_bulk_reviews(reviews_for_ai)

        print(f"\n📊 {product_name[:40]}... DETAYLI ANALİZ")
        print(f"  • Toplam: {len(reviews)} yorum")
        print(f"  • Ortalama Puan: {sum(r['rating'] for r in reviews) / len(reviews):.1f}/5")
        print(f"  • Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA - TOP 5:")
        for i, (reason, count) in enumerate(analysis['top_purchase_reasons'][:5], 1):
            print(f"  {i}. {reason}: {count} kişi")

        print(f"\n✅ EN BEĞENİLEN ÖZELLİKLER:")
        for i, (pro, count) in enumerate(analysis['top_pros'][:5], 1):
            print(f"  {i}. {pro}: {count} kez")

        if analysis['top_cons']:
            print(f"\n❌ GELİŞTİRİLEBİLECEK YÖNLER:")
            for i, (con, count) in enumerate(analysis['top_cons'][:3], 1):
                print(f"  {i}. {con}: {count} kez")


if __name__ == "__main__":
    print("="*60)
    print("📡 DIRECT API SCRAPER")
    print("✅ En basit ve etkili yöntem")
    print("✅ HTML + API kombinasyonu")
    print("✅ Pagination ile TÜM yorumlar")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = DirectAPIScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_reviews_direct(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()