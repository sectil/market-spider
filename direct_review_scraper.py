#!/usr/bin/env python3
"""
Trendyol API'den direkt GERÇEK yorumları çeker
"""

import requests
import json
import time
import re
from datetime import datetime, timedelta
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class DirectTrendyolReviewScraper:
    """Trendyol API'den direkt gerçek yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': 'https://www.trendyol.com/',
            'Origin': 'https://www.trendyol.com'
        }

    def extract_product_id_from_url(self, url: str):
        """URL'den product ID'yi çıkar"""
        # Pattern: -p-12345678
        match = re.search(r'-p-(\d+)', url)
        if match:
            return match.group(1)

        # Pattern: /product/12345678
        match = re.search(r'/product/(\d+)', url)
        if match:
            return match.group(1)

        # Pattern: productId=12345678
        match = re.search(r'productId=(\d+)', url)
        if match:
            return match.group(1)

        return None

    def get_real_reviews(self, product_url: str, max_pages: int = 10):
        """Gerçek yorumları Trendyol API'den çek"""

        product_id = self.extract_product_id_from_url(product_url)
        if not product_id:
            print(f"❌ Product ID çıkarılamadı: {product_url}")
            return []

        print(f"✅ Product ID: {product_id}")

        all_reviews = []

        # Farklı API endpoint'lerini dene
        api_urls = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/review/{product_id}",
            f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{product_id}",
            f"https://api.trendyol.com/webproductgw/api/review/{product_id}",
            f"https://public-mdc.trendyol.com/discovery-web-productgw-service/reviews/{product_id}"
        ]

        for api_base in api_urls:
            print(f"  Deneniyor: {api_base[:50]}...")

            for page in range(max_pages):
                params = {
                    'page': page,
                    'size': 20,
                    'sortBy': 'helpfulCount',
                    'culture': 'tr-TR'
                }

                try:
                    response = requests.get(
                        api_base,
                        headers=self.headers,
                        params=params,
                        timeout=10
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Farklı JSON yapılarını kontrol et
                        reviews_data = None

                        # Format 1: result.productReviews.content
                        if 'result' in data and 'productReviews' in data['result']:
                            reviews_data = data['result']['productReviews'].get('content', [])

                        # Format 2: result.content
                        elif 'result' in data and 'content' in data['result']:
                            reviews_data = data['result']['content']

                        # Format 3: content direkt
                        elif 'content' in data:
                            reviews_data = data['content']

                        # Format 4: reviews.content
                        elif 'reviews' in data and 'content' in data['reviews']:
                            reviews_data = data['reviews']['content']

                        # Format 5: data direkt array
                        elif isinstance(data, list):
                            reviews_data = data

                        if reviews_data:
                            print(f"    ✓ Sayfa {page+1}: {len(reviews_data)} GERÇEK yorum bulundu")

                            for review in reviews_data:
                                processed_review = self._process_review(review)
                                if processed_review:
                                    all_reviews.append(processed_review)

                            # Eğer daha az yorum geldiyse, son sayfadayız
                            if len(reviews_data) < 20:
                                break

                            time.sleep(0.5)  # Rate limiting
                        else:
                            # Bu sayfada yorum yok, bir sonraki API'yi dene
                            break

                    elif response.status_code == 404:
                        # Bu API endpoint'i çalışmıyor, bir sonrakini dene
                        break

                except requests.exceptions.RequestException as e:
                    print(f"    ❌ Bağlantı hatası: {e}")
                    break

            # Eğer yorum bulduysan, diğer API'leri deneme
            if all_reviews:
                break

        print(f"\n✅ Toplam {len(all_reviews)} GERÇEK yorum çekildi")
        return all_reviews

    def _process_review(self, review_data: dict):
        """Yorum verisini işle"""

        # Boş yorum kontrolü
        comment_text = review_data.get('comment', '') or review_data.get('text', '') or review_data.get('reviewText', '')
        if not comment_text or len(comment_text) < 5:
            return None

        # Tarih parse
        date_str = review_data.get('commentDateISOtype') or review_data.get('lastModifiedDate') or review_data.get('createdDate')
        review_date = self._parse_date(date_str)

        return {
            'reviewer_name': review_data.get('userFullName', '') or review_data.get('userName', '') or 'Trendyol Müşterisi',
            'reviewer_verified': review_data.get('verifiedPurchase', False) or review_data.get('isVerified', False),
            'rating': review_data.get('rate', 0) or review_data.get('rating', 0) or review_data.get('score', 0),
            'review_text': comment_text,
            'review_date': review_date,
            'helpful_count': review_data.get('helpfulCount', 0) or review_data.get('helpfulVotes', 0),
            'seller_name': review_data.get('sellerName', '') or review_data.get('seller', '')
        }

    def _parse_date(self, date_str: str):
        """Tarih string'ini parse et"""
        if not date_str:
            return datetime.now()

        try:
            # ISO format
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))

            # Unix timestamp
            if date_str.isdigit() and len(date_str) > 10:
                return datetime.fromtimestamp(int(date_str) / 1000)

            # Başka formatlar için
            return datetime.now()
        except:
            return datetime.now()

    def scrape_product_reviews(self, product_id: int):
        """Bir ürün için gerçek yorumları çek ve kaydet"""

        # Ürünü bul
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return

        print(f"\n🔍 GERÇEK yorumlar çekiliyor: {product.name[:50]}...")
        print(f"URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        # GERÇEK yorumları çek
        reviews = self.get_real_reviews(product.product_url or product.url)

        if not reviews:
            print("❌ GERÇEK yorum bulunamadı")
            # Alternatif: site_product_id kullan
            if product.site_product_id:
                print(f"  Site Product ID ile tekrar deneniyor: {product.site_product_id}")
                fake_url = f"https://www.trendyol.com/x/y-p-{product.site_product_id}"
                reviews = self.get_real_reviews(fake_url)

        if reviews:
            # Yorumları kaydet
            saved_count = 0
            for review_data in reviews:
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

                    # AI analiz sonuçları
                    sentiment_score=analysis['sentiment_score'],
                    key_phrases=analysis['key_phrases'],
                    purchase_reasons=analysis['purchase_reasons'],
                    pros=analysis['pros'],
                    cons=analysis['cons']
                )

                self.session.add(review)
                saved_count += 1

            self.session.commit()
            print(f"✅ {saved_count} GERÇEK yorum kaydedildi")

            # Analiz göster
            self.show_analysis(product.name, reviews)
        else:
            print("❌ Hiç GERÇEK yorum çekilemedi")

    def show_analysis(self, product_name: str, reviews: list):
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
        print(f"  • Doğrulanmış Alıcı: %{analysis['verified_percentage']:.1f}")

        print(f"\n🛒 NEDEN 1. SIRADA? (GERÇEK NEDENLER):")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi belirtmiş")

        print(f"\n✅ EN ÇOK BELİRTİLEN ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez bahsedilmiş")

        if analysis['top_cons']:
            print(f"\n❌ EN ÇOK BELİRTİLEN EKSİLER:")
            for con, count in analysis['top_cons'][:3]:
                print(f"  • {con}: {count} kez bahsedilmiş")

        insights = analysis['human_insights']
        print(f"\n🧠 GERÇEK MÜŞTERİ DAVRANIŞI ANALİZİ:")
        print(f"\n📍 Ana Motivasyon:")
        print(f"  {insights['ana_motivasyon']}")
        print(f"\n👤 Müşteri Profili:")
        print(f"  {insights['müşteri_profili']}")
        print(f"\n🎯 Neden Bu Ürün 1. Sırada:")
        print(f"  {insights['satın_alma_psikolojisi']}")
        print(f"\n📌 Özet Tavsiye:")
        print(f"  {insights['tavsiye']}")

        print("\n" + "="*60)
        print("✅ %100 GERÇEK VERİ - SİMÜLASYON DEĞİL!")
        print("="*60)

    def scrape_all_products(self):
        """Tüm ürünler için gerçek yorumları çek"""

        products = self.session.query(Product).all()
        print(f"📦 {len(products)} ürün bulundu")

        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] İşleniyor...")

            # Zaten yorumu var mı kontrol et
            existing_reviews = self.session.query(ProductReview).filter_by(
                product_id=product.id
            ).count()

            if existing_reviews > 0:
                print(f"  ℹ️ {existing_reviews} yorum zaten mevcut, atlanıyor...")
                continue

            self.scrape_product_reviews(product.id)

            # Rate limiting
            time.sleep(2)

        print("\n✅ Tüm ürünlerin GERÇEK yorumları çekildi")


if __name__ == "__main__":
    scraper = DirectTrendyolReviewScraper()

    # İlk ürünün gerçek yorumlarını çek
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_product_reviews(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()