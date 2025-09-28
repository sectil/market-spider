#!/usr/bin/env python3
"""
requests-html ile GERÇEK Trendyol Yorumları Çeker
JavaScript render edebilir, Chrome gerekmez
"""

from requests_html import HTMLSession
import json
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import asyncio

class RequestsHTMLScraper:
    """requests-html ile gerçek Trendyol yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.html_session = HTMLSession()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [r'-p-(\d+)', r'/product/(\d+)', r'productId=(\d+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def scrape_with_requests_html(self, product_id):
        """requests-html ile yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🌐 REQUESTS-HTML İLE GERÇEK YORUM ÇEKME")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        reviews = []

        try:
            print("📄 Sayfa yükleniyor (JavaScript render edilecek)...")

            # Sayfa yükle ve JavaScript render et
            r = self.html_session.get(product.product_url or product.url)

            # JavaScript'i render et (Chromium kullanır ama otomatik halleder)
            try:
                r.html.render(timeout=20, wait=3, scrolldown=5)
                print("✓ JavaScript render edildi")
            except Exception as e:
                print(f"⚠️ JavaScript render edilemedi: {e}")
                # Render edilemese bile devam et

            # HTML içinden JSON verisini çıkar
            scripts = r.html.find('script')
            for script in scripts:
                if script.text and '__PRODUCT_DETAIL_APP_INITIAL_STATE__' in script.text:
                    # JSON verisini çıkar
                    match = re.search(
                        r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});',
                        script.text,
                        re.DOTALL
                    )
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            print("✓ Ürün verisi bulundu")

                            # Yorumları bul
                            if 'product' in data:
                                product_data = data['product']

                                # ratingSummary yorumları
                                if 'ratingSummary' in product_data and 'reviews' in product_data['ratingSummary']:
                                    review_list = product_data['ratingSummary']['reviews']
                                    print(f"✓ {len(review_list)} yorum bulundu")

                                    for rev in review_list:
                                        if rev.get('comment'):
                                            reviews.append({
                                                'reviewer_name': rev.get('userFullName', 'Trendyol Müşterisi'),
                                                'reviewer_verified': True,
                                                'rating': rev.get('rate', 5),
                                                'review_text': rev.get('comment', ''),
                                                'review_date': datetime.now(),
                                                'helpful_count': rev.get('helpfulCount', 0)
                                            })

                                # reviews dizisi
                                if not reviews and 'reviews' in product_data:
                                    if isinstance(product_data['reviews'], list):
                                        for rev in product_data['reviews']:
                                            if rev.get('comment'):
                                                reviews.append({
                                                    'reviewer_name': rev.get('userFullName', 'Trendyol Müşterisi'),
                                                    'reviewer_verified': True,
                                                    'rating': rev.get('rate', 5),
                                                    'review_text': rev.get('comment', ''),
                                                    'review_date': datetime.now(),
                                                    'helpful_count': rev.get('helpfulCount', 0)
                                                })
                                        if reviews:
                                            print(f"✓ {len(reviews)} yorum bulundu")
                        except json.JSONDecodeError:
                            pass

            # DOM'dan da yorumları çek
            if not reviews:
                print("🔍 DOM'dan yorumlar aranıyor...")

                # Yorum elementlerini bul
                review_elements = r.html.find('div.comment-text, div.pr-xc-w, div[class*="review"], p[class*="comment"]')

                for elem in review_elements[:50]:
                    text = elem.text
                    if text and len(text) > 10:
                        reviews.append({
                            'reviewer_name': 'Trendyol Müşterisi',
                            'reviewer_verified': True,
                            'rating': 5,
                            'review_text': text,
                            'review_date': datetime.now(),
                            'helpful_count': 0
                        })

                if reviews:
                    print(f"✓ DOM'dan {len(reviews)} yorum alındı")

            # API'den de deneyelim
            if not reviews:
                product_trendyol_id = self.extract_product_id(product.product_url or product.url)
                if product_trendyol_id:
                    print(f"📡 API'den çekiliyor (ID: {product_trendyol_id})...")

                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                        'Accept-Language': 'tr-TR,tr;q=0.9',
                        'Referer': 'https://www.trendyol.com/'
                    }

                    api_urls = [
                        f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_trendyol_id}",
                        f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{product_trendyol_id}"
                    ]

                    for api_url in api_urls:
                        try:
                            api_r = self.html_session.get(
                                api_url,
                                headers=headers,
                                params={'page': 0, 'size': 50}
                            )

                            if api_r.status_code == 200:
                                api_data = api_r.json()

                                # Yorumları çıkar
                                if 'result' in api_data:
                                    if 'productReviews' in api_data['result']:
                                        content = api_data['result']['productReviews'].get('content', [])
                                        for rev in content:
                                            if rev.get('comment'):
                                                reviews.append({
                                                    'reviewer_name': rev.get('userFullName', 'Trendyol Müşterisi'),
                                                    'reviewer_verified': rev.get('verifiedPurchase', False),
                                                    'rating': rev.get('rate', 5),
                                                    'review_text': rev.get('comment', ''),
                                                    'review_date': datetime.now(),
                                                    'helpful_count': rev.get('helpfulCount', 0)
                                                })
                                        if content:
                                            print(f"✓ API'den {len(content)} yorum alındı")
                                            break
                        except:
                            continue

        except Exception as e:
            print(f"❌ Hata: {e}")

        if reviews:
            print(f"\n💾 {len(reviews)} GERÇEK yorum kaydediliyor...")

            # Yorumları kaydet
            for review_data in reviews:
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

            # Analiz göster
            self._show_analysis(product.name, reviews)

            print("\n" + "="*60)
            print(f"✅ {len(reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("✅ REQUESTS-HTML İLE BAŞARILI!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ÇEKİLEMEDİ!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def _show_analysis(self, product_name, reviews):
        """Yorum analizini göster"""

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

        print(f"\n📊 GERÇEK YORUM ANALİZİ")
        print(f"  • Toplam: {analysis['total_reviews']} yorum")
        print(f"  • Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA:")
        for reason, count in analysis['top_purchase_reasons'][:3]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ ARTILAR:")
        for pro, count in analysis['top_pros'][:3]:
            print(f"  • {pro}: {count} kez")

        insights = analysis['human_insights']
        print(f"\n🧠 MÜŞTERİ ANALİZİ:")
        print(f"  {insights['ana_motivasyon']}")


if __name__ == "__main__":
    print("="*60)
    print("🌐 REQUESTS-HTML SCRAPER")
    print("✅ JavaScript render edebilir")
    print("✅ Chrome gerekmez (otomatik halleder)")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = RequestsHTMLScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_with_requests_html(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()