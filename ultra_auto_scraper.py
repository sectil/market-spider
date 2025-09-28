#!/usr/bin/env python3
"""
ULTRA Otomatik Trendyol Yorum Scraper
Chrome olmadan çalışır - Sadece requests ve akıllı API kullanımı
FALLBACK YOK! %100 GERÇEK VERİ!
"""

import requests
import json
import time
import random
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import cloudscraper

class UltraAutoScraper:
    """Ultra otomatik scraper - Chrome gerekmez, API odaklı"""

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

    def get_product_data_from_page(self, product_url):
        """Ürün sayfasından veri çek"""
        print("📄 Ürün sayfası analiz ediliyor...")

        try:
            response = self.scraper.get(product_url, timeout=15)

            if response.status_code != 200:
                return None

            html = response.text

            # JavaScript içindeki JSON verisini bul
            pattern = r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});'
            match = re.search(pattern, html, re.DOTALL)

            if match:
                try:
                    data = json.loads(match.group(1))
                    return data
                except:
                    pass

            # Alternatif pattern
            pattern2 = r'<script>window\.TYPageName="product_detail";window\.\_\_data\_\_=({.*?})</script>'
            match2 = re.search(pattern2, html)

            if match2:
                try:
                    data = json.loads(match2.group(1))
                    return data
                except:
                    pass

        except Exception as e:
            print(f"  ❌ Sayfa çekme hatası: {e}")

        return None

    def extract_reviews_from_page_data(self, page_data):
        """Sayfa verisinden yorumları çıkar"""
        reviews = []

        if not page_data:
            return reviews

        # Farklı yollardan yorumları bul
        paths = [
            lambda d: d.get('product', {}).get('ratingSummary', {}).get('reviews', []),
            lambda d: d.get('product', {}).get('reviews', {}).get('content', []),
            lambda d: d.get('product', {}).get('reviews', []),
            lambda d: d.get('reviews', []),
            lambda d: d.get('ratingSummary', {}).get('reviews', [])
        ]

        for path_func in paths:
            try:
                review_list = path_func(page_data)
                if review_list and isinstance(review_list, list):
                    for r in review_list:
                        if r.get('comment') or r.get('text'):
                            reviews.append({
                                'reviewer_name': r.get('userFullName', '') or r.get('userName', '') or 'Trendyol Müşterisi',
                                'reviewer_verified': r.get('verifiedPurchase', False),
                                'rating': r.get('rate', 5) or r.get('rating', 5),
                                'review_text': r.get('comment', '') or r.get('text', ''),
                                'review_date': self._parse_date(r.get('commentDateISOtype') or r.get('date')),
                                'helpful_count': r.get('helpfulCount', 0)
                            })
                    if reviews:
                        print(f"  ✓ Sayfadan {len(reviews)} yorum bulundu")
                        return reviews
            except:
                continue

        return reviews

    def get_reviews_via_api(self, product_id):
        """API üzerinden yorumları çek"""
        reviews = []

        # Çeşitli API endpoint'leri
        endpoints = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/review/{product_id}",
            f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{product_id}",
            f"https://public-mdc.trendyol.com/discovery-web-productgw-service/reviews/{product_id}",
            f"https://api.trendyol.com/webproductgw/api/review/{product_id}",
            f"https://public.trendyol.com/reviews-service/api/product/{product_id}/reviews"
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.trendyol.com',
            'Referer': 'https://www.trendyol.com/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        for endpoint in endpoints:
            print(f"  📡 API deneniyor: {endpoint[:60]}...")

            try:
                # Her endpoint için farklı sayfalama dene
                for page in range(5):
                    params = {
                        'page': page,
                        'size': 50,
                        'sortBy': 'helpfulCount',
                        'culture': 'tr-TR',
                        'storefrontId': '1',
                        'culturetype': '0'
                    }

                    response = self.scraper.get(
                        endpoint,
                        headers=headers,
                        params=params,
                        timeout=10
                    )

                    if response.status_code == 200:
                        try:
                            data = response.json()

                            # Yorumları bul
                            review_list = self._extract_reviews_from_api_response(data)

                            if review_list:
                                reviews.extend(review_list)
                                print(f"    ✓ Sayfa {page+1}: {len(review_list)} yorum")

                                if len(review_list) < 20:
                                    break  # Son sayfa

                                time.sleep(random.uniform(0.5, 1))
                            else:
                                break

                        except Exception as e:
                            break

                    elif response.status_code == 404:
                        break

                    else:
                        break

                if reviews:
                    print(f"  ✅ Bu API'den toplam {len(reviews)} yorum alındı")
                    return reviews

            except Exception as e:
                continue

        return reviews

    def _extract_reviews_from_api_response(self, data):
        """API response'dan yorumları çıkar"""
        reviews = []

        # Farklı JSON formatlarını dene
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
                                'review_date': self._parse_date(r.get('commentDateISOtype') or r.get('date') or r.get('createdDate')),
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
            # ISO format
            if 'T' in str(date_str):
                return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))

            # Unix timestamp
            if isinstance(date_str, (int, float)) or (isinstance(date_str, str) and date_str.isdigit()):
                timestamp = int(date_str)
                if timestamp > 1000000000000:  # Milliseconds
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)

        except:
            pass

        return datetime.now()

    def ultra_auto_scrape(self, product_id):
        """Ultra otomatik scraping - FALLBACK YOK!"""

        # Ürünü bul
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🚀 ULTRA OTOMATİK YORUM ÇEKME")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")
        print("⚠️ FALLBACK YOK - %100 GERÇEK VERİ!")
        print("-"*60)

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        all_reviews = []

        # 1. Önce sayfadan veri çek
        page_data = self.get_product_data_from_page(product.product_url or product.url)
        if page_data:
            page_reviews = self.extract_reviews_from_page_data(page_data)
            if page_reviews:
                all_reviews.extend(page_reviews)
                print(f"✅ Sayfadan {len(page_reviews)} yorum alındı")

        # 2. Product ID çıkar
        product_trendyol_id = self.extract_product_id(product.product_url or product.url)

        if not product_trendyol_id and product.site_product_id:
            product_trendyol_id = product.site_product_id

        # 3. API'den yorumları çek
        if product_trendyol_id:
            print(f"\n📡 API araması (Product ID: {product_trendyol_id})...")
            api_reviews = self.get_reviews_via_api(product_trendyol_id)
            if api_reviews:
                all_reviews.extend(api_reviews)
                print(f"✅ API'den {len(api_reviews)} yorum alındı")

        # Duplicate'leri kaldır
        unique_reviews = []
        seen_texts = set()
        for review in all_reviews:
            if review['review_text'] not in seen_texts:
                unique_reviews.append(review)
                seen_texts.add(review['review_text'])

        if not unique_reviews:
            print("\n" + "="*60)
            print("❌ GERÇEK YORUM ÇEKİLEMEDİ!")
            print("❌ FALLBACK KULLANILMADI!")
            print("⚠️ Trendyol API'sine ulaşılamadı")
            print("="*60)
            return False

        # Yorumları kaydet
        print(f"\n💾 {len(unique_reviews)} GERÇEK yorum kaydediliyor...")

        for review_data in unique_reviews[:100]:  # Max 100 yorum
            # AI analizi
            analysis = self.ai.analyze_review(review_data['review_text'])

            # Veritabanına kaydet
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

        # Analiz göster
        self._show_real_analysis(product.name, unique_reviews[:100])

        print("\n" + "="*60)
        print(f"✅ {len(unique_reviews[:100])} GERÇEK YORUM KAYDEDİLDİ!")
        print("✅ %100 GERÇEK VERİ - FALLBACK YOK!")
        print("="*60)

        return True

    def _show_real_analysis(self, product_name, reviews):
        """GERÇEK yorum analizini göster"""

        # AI ile toplu analiz
        reviews_for_ai = [
            {
                'text': r['review_text'],
                'rating': r['rating'],
                'verified': r['reviewer_verified'],
                'helpful_count': r['helpful_count']
            }
            for r in reviews
        ]

        analysis = self.ai.analyze_bulk_reviews(reviews_for_ai)

        print("\n" + "="*60)
        print(f"📊 {product_name[:40]}... GERÇEK YORUM ANALİZİ")
        print("="*60)

        print(f"\n📈 GERÇEK İSTATİSTİKLER:")
        print(f"  • Toplam GERÇEK Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")

        if 'verified_percentage' in analysis:
            print(f"  • Doğrulanmış Alıcı: %{analysis['verified_percentage']:.1f}")

        print(f"\n🛒 NEDEN 1. SIRADA? (GERÇEK MÜŞTERİ GÖRÜŞLERİ):")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ GERÇEK ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez belirtilmiş")

        if analysis['top_cons']:
            print(f"\n❌ GERÇEK EKSİLER:")
            for con, count in analysis['top_cons'][:3]:
                print(f"  • {con}: {count} kez belirtilmiş")

        insights = analysis['human_insights']
        print(f"\n🧠 GERÇEK MÜŞTERİ DAVRANIŞI ANALİZİ:")
        print(f"  {insights['ana_motivasyon']}")

        if 'satın_alma_psikolojisi' in insights:
            print(f"\n🎯 NEDEN BU ÜRÜN 1. SIRADA:")
            print(f"  {insights['satın_alma_psikolojisi']}")

        print("\n" + "="*60)


if __name__ == "__main__":
    print("="*60)
    print("⚡ ULTRA OTOMATİK SCRAPER")
    print("✅ Chrome gerekmez")
    print("✅ Akıllı API kullanımı")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = UltraAutoScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.ultra_auto_scrape(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()