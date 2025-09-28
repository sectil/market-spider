#!/usr/bin/env python3
"""
ULTIMATE Trendyol Yorum Scraper
TÜM yorumları çeker - Çoklu strateji kullanır
"""

import requests
import json
import re
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import cloudscraper

class UltimateReviewScraper:
    """Ultimate scraper - TÜM yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.scraper = cloudscraper.create_scraper()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [
            r'-p-(\d+)',
            r'/product/(\d+)',
            r'productId=(\d+)',
            r'/(\d+)\?',
            r'/(\d+)$'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def scrape_all_reviews(self, product_id):
        """TÜM yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🚀 ULTIMATE SCRAPER - TÜM YORUMLAR")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        all_reviews = []
        product_trendyol_id = self.extract_product_id(product.product_url or product.url)

        if not product_trendyol_id and product.site_product_id:
            product_trendyol_id = product.site_product_id

        print(f"🔍 Product ID: {product_trendyol_id}")

        # STRATEJI 1: Sayfa HTML'inden çek
        print("\n📄 STRATEJI 1: HTML'den yorumları çekiyor...")
        html_reviews = self.get_reviews_from_html(product.product_url or product.url)
        if html_reviews:
            all_reviews.extend(html_reviews)
            print(f"  ✓ HTML'den {len(html_reviews)} yorum alındı")

        # STRATEJI 2: API'lerden çek (TÜM sayfalar)
        if product_trendyol_id:
            print("\n📡 STRATEJI 2: API'den TÜM sayfalar çekiliyor...")
            api_reviews = self.get_all_reviews_from_api(product_trendyol_id)
            if api_reviews:
                all_reviews.extend(api_reviews)
                print(f"  ✓ API'den {len(api_reviews)} yorum alındı")

        # STRATEJI 3: Widget API'yi dene
        if product_trendyol_id:
            print("\n🔧 STRATEJI 3: Widget API deneniyor...")
            widget_reviews = self.get_reviews_from_widget(product_trendyol_id)
            if widget_reviews:
                all_reviews.extend(widget_reviews)
                print(f"  ✓ Widget'tan {len(widget_reviews)} yorum alındı")

        # Duplicate'leri kaldır
        unique_reviews = []
        seen_texts = set()
        for review in all_reviews:
            review_text = review.get('review_text', '')
            if review_text and review_text not in seen_texts:
                unique_reviews.append(review)
                seen_texts.add(review_text)

        if unique_reviews:
            print(f"\n💾 {len(unique_reviews)} benzersiz yorum kaydediliyor...")

            for review_data in unique_reviews:
                # AI analizi
                analysis = self.ai.analyze_review(review_data['review_text'])

                review = ProductReview(
                    product_id=product_id,
                    reviewer_name=review_data.get('reviewer_name', 'Trendyol Müşterisi'),
                    reviewer_verified=review_data.get('reviewer_verified', False),
                    rating=review_data.get('rating', 5),
                    review_title='',
                    review_text=review_data['review_text'],
                    review_date=review_data.get('review_date', datetime.now()),
                    helpful_count=review_data.get('helpful_count', 0),
                    sentiment_score=analysis['sentiment_score'],
                    key_phrases=analysis['key_phrases'],
                    purchase_reasons=analysis['purchase_reasons'],
                    pros=analysis['pros'],
                    cons=analysis['cons']
                )
                self.session.add(review)

            self.session.commit()

            # Analiz göster
            self._show_analysis(product.name, unique_reviews)

            print("\n" + "="*60)
            print(f"✅ {len(unique_reviews)} YORUM BAŞARIYLA KAYDEDİLDİ!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ HİÇ YORUM ÇEKİLEMEDİ!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def get_reviews_from_html(self, url):
        """HTML sayfasından yorumları çek"""
        reviews = []

        try:
            response = self.scraper.get(url, timeout=15)
            if response.status_code != 200:
                return reviews

            html = response.text

            # window.__PRODUCT_DETAIL_APP_INITIAL_STATE__ içindeki veriyi bul
            pattern = r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(1))

                    # Farklı yollardan yorumları bul
                    paths = [
                        lambda d: d.get('product', {}).get('ratingSummary', {}).get('reviews', []),
                        lambda d: d.get('product', {}).get('reviews', {}).get('content', []),
                        lambda d: d.get('product', {}).get('reviews', []),
                        lambda d: d.get('product', {}).get('review', {}).get('productReviews', {}).get('content', [])
                    ]

                    for path_func in paths:
                        review_list = path_func(data)
                        if review_list and isinstance(review_list, list):
                            for r in review_list:
                                if r.get('comment'):
                                    reviews.append({
                                        'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                        'reviewer_verified': r.get('verifiedPurchase', True),
                                        'rating': r.get('rate', 5),
                                        'review_text': r.get('comment', ''),
                                        'review_date': self._parse_date(r.get('commentDateISOtype')),
                                        'helpful_count': r.get('helpfulCount', 0)
                                    })
                            if reviews:
                                break

                except json.JSONDecodeError:
                    pass

            # Alternatif pattern
            pattern2 = r'<script type="application/ld\+json">(.*?)</script>'
            matches = re.findall(pattern2, html, re.DOTALL)
            for match_text in matches:
                try:
                    ld_data = json.loads(match_text)
                    if ld_data.get('@type') == 'Product' and 'review' in ld_data:
                        for review in ld_data['review']:
                            if review.get('reviewBody'):
                                reviews.append({
                                    'reviewer_name': review.get('author', {}).get('name', 'Trendyol Müşterisi'),
                                    'reviewer_verified': True,
                                    'rating': review.get('reviewRating', {}).get('ratingValue', 5),
                                    'review_text': review.get('reviewBody', ''),
                                    'review_date': self._parse_date(review.get('datePublished')),
                                    'helpful_count': 0
                                })
                except:
                    pass

        except Exception as e:
            print(f"  ❌ HTML hatası: {e}")

        return reviews

    def get_all_reviews_from_api(self, product_id):
        """API'den TÜM yorumları çek (tüm sayfalar)"""
        all_reviews = []

        # Farklı API endpoint'leri
        api_endpoints = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/review/{product_id}",
            f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{product_id}",
            f"https://public-mdc.trendyol.com/discovery-web-productgw-service/reviews/{product_id}",
            f"https://api.trendyol.com/webproductgw/api/review/{product_id}",
            f"https://public.trendyol.com/reviews-service/api/product/{product_id}/reviews",
            f"https://public.trendyol.com/discovery-web-recogw-service/api/rnr/products/{product_id}/reviews"
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.trendyol.com',
            'Referer': 'https://www.trendyol.com/'
        }

        for endpoint in api_endpoints:
            print(f"  📡 Deneniyor: {endpoint[:50]}...")

            page = 0
            page_reviews = []

            while page < 50:  # Max 50 sayfa
                params = {
                    'page': page,
                    'size': 50,
                    'sortBy': 'helpfulCount',
                    'culture': 'tr-TR',
                    'storefrontId': '1',
                    'culturetype': '0'
                }

                try:
                    response = self.scraper.get(
                        endpoint,
                        headers=headers,
                        params=params,
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Yorumları çıkar
                        review_list = self._extract_reviews_from_json(data)

                        if review_list:
                            page_reviews.extend(review_list)
                            print(f"    ✓ Sayfa {page+1}: {len(review_list)} yorum")

                            if len(review_list) < 50:  # Son sayfa
                                break

                            page += 1
                            time.sleep(0.5)  # Rate limiting
                        else:
                            break

                    elif response.status_code == 404:
                        break
                    else:
                        break

                except Exception as e:
                    break

            if page_reviews:
                all_reviews.extend(page_reviews)
                print(f"  ✅ Bu API'den toplam {len(page_reviews)} yorum alındı")
                break  # Başarılı olduysa diğer API'leri deneme

        return all_reviews

    def get_reviews_from_widget(self, product_id):
        """Widget API'den yorumları çek"""
        reviews = []

        widget_url = f"https://public.trendyol.com/discovery-web-webproductgw-santral/widget/product/{product_id}/reviews"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'X-Storefront-Id': '1',
            'X-Application-Id': '1'
        }

        try:
            response = self.scraper.get(widget_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                review_list = self._extract_reviews_from_json(data)
                if review_list:
                    reviews.extend(review_list)

        except:
            pass

        return reviews

    def _extract_reviews_from_json(self, data):
        """JSON'dan yorumları çıkar"""
        reviews = []

        # Farklı JSON yapılarını dene
        paths = [
            lambda d: d.get('result', {}).get('productReviews', {}).get('content', []),
            lambda d: d.get('result', {}).get('content', []),
            lambda d: d.get('content', []),
            lambda d: d.get('reviews', {}).get('content', []),
            lambda d: d.get('reviews', []),
            lambda d: d.get('productReviews', {}).get('content', []),
            lambda d: d if isinstance(d, list) else []
        ]

        for path_func in paths:
            try:
                review_list = path_func(data)
                if review_list and isinstance(review_list, list):
                    for r in review_list:
                        comment = r.get('comment', '') or r.get('text', '') or r.get('reviewText', '')
                        if comment and len(comment) > 5:
                            reviews.append({
                                'reviewer_name': r.get('userFullName', '') or r.get('userName', '') or 'Trendyol Müşterisi',
                                'reviewer_verified': r.get('verifiedPurchase', False) or r.get('isVerified', False),
                                'rating': r.get('rate', 5) or r.get('rating', 5) or r.get('score', 5),
                                'review_text': comment,
                                'review_date': self._parse_date(r.get('commentDateISOtype') or r.get('date')),
                                'helpful_count': r.get('helpfulCount', 0) or r.get('helpfulVotes', 0)
                            })
                    if reviews:
                        return reviews
            except:
                continue

        return reviews

    def _parse_date(self, date_str):
        """Tarih parse et"""
        if not date_str:
            return datetime.now()

        try:
            if 'T' in str(date_str):
                return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
            elif isinstance(date_str, (int, float)):
                timestamp = int(date_str)
                if timestamp > 1000000000000:
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
        except:
            pass

        return datetime.now()

    def _show_analysis(self, product_name, reviews):
        """Detaylı yorum analizi göster"""

        reviews_for_ai = [
            {
                'text': r['review_text'],
                'rating': r.get('rating', 5),
                'verified': r.get('reviewer_verified', False),
                'helpful_count': r.get('helpful_count', 0)
            }
            for r in reviews
        ]

        analysis = self.ai.analyze_bulk_reviews(reviews_for_ai)

        print("\n" + "="*60)
        print(f"📊 {product_name[:40]}... YORUM ANALİZİ")
        print("="*60)

        print(f"\n📈 İSTATİSTİKLER:")
        print(f"  • Toplam Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")

        if 'verified_percentage' in analysis:
            print(f"  • Doğrulanmış: %{analysis['verified_percentage']:.1f}")

        print(f"\n🛒 NEDEN 1. SIRADA? (MÜŞTERİ GÖRÜŞLERİ):")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez belirtilmiş")

        if analysis['top_cons']:
            print(f"\n❌ EKSİLER:")
            for con, count in analysis['top_cons'][:3]:
                print(f"  • {con}: {count} kez belirtilmiş")

        insights = analysis['human_insights']
        print(f"\n🧠 MÜŞTERİ DAVRANIŞI ANALİZİ:")
        print(f"  {insights['ana_motivasyon']}")

        if 'satın_alma_psikolojisi' in insights:
            print(f"\n🎯 NEDEN BU ÜRÜN 1. SIRADA:")
            print(f"  {insights['satın_alma_psikolojisi']}")

        print("\n" + "="*60)


if __name__ == "__main__":
    print("="*60)
    print("⚡ ULTIMATE REVIEW SCRAPER")
    print("✅ TÜM yorumları çeker")
    print("✅ Çoklu strateji kullanır")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = UltimateReviewScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_reviews(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()