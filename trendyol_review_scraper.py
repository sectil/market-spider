#!/usr/bin/env python3
"""
Trendyol Review Scraper - Ürün yorumlarını çeker
"""

import re
import json
import time
import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from database import SessionLocal, ProductReview, Product
from turkish_review_ai import TurkishReviewAI

class TrendyolReviewScraper:
    """Trendyol yorum scraper"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.ai = TurkishReviewAI()
        self.session = SessionLocal()

    def get_product_reviews(self, product_url: str, max_pages: int = 5) -> List[Dict]:
        """Ürün yorumlarını çek"""
        reviews = []

        # Product ID'yi URL'den çıkar
        product_id_match = re.search(r'-p-(\d+)', product_url)
        if not product_id_match:
            print(f"❌ Product ID bulunamadı: {product_url}")
            return reviews

        product_id = product_id_match.group(1)
        print(f"📦 Product ID: {product_id}")

        # Yorumları çek (sayfalama ile)
        for page in range(1, max_pages + 1):
            page_reviews = self._get_reviews_page(product_id, page)
            if not page_reviews:
                break

            reviews.extend(page_reviews)
            print(f"  ✓ Sayfa {page}: {len(page_reviews)} yorum bulundu")

            # Rate limiting
            time.sleep(1)

        print(f"✅ Toplam {len(reviews)} yorum çekildi")
        return reviews

    def _get_reviews_page(self, product_id: str, page: int) -> List[Dict]:
        """Belirli bir sayfa yorumları çek"""
        reviews = []

        # Trendyol API endpoint - Güncel URL
        url = f"https://api.trendyol.com/webproductgw/api/review/{product_id}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Referer': 'https://www.trendyol.com/'
        }

        params = {
            'page': page - 1,  # 0-indexed
            'size': 20,
            'sortBy': 'helpfulCount'  # En faydalı yorumlar
        }

        try:
            response = self.scraper.get(url, params=params, headers=headers)
            if response.status_code != 200:
                # Alternatif yöntem: Direkt ürün sayfasından çek
                return self._get_reviews_from_product_page(product_id, page)

            data = response.json()

            if 'result' in data and 'productReviews' in data['result']:
                review_data = data['result']['productReviews']

                for review_content in review_data.get('content', []):
                    # Yorum verilerini parse et
                    review = {
                        'reviewer_name': review_content.get('userFullName', 'Anonim'),
                        'reviewer_verified': review_content.get('verifiedPurchase', False),
                        'rating': review_content.get('rate', 0),
                        'review_title': review_content.get('reviewTitle', ''),
                        'review_text': review_content.get('comment', ''),
                        'review_date': self._parse_date(review_content.get('commentDateISOtype')),
                        'helpful_count': review_content.get('helpfulCount', 0),
                        'seller_name': review_content.get('sellerName', '')
                    }

                    # Boş yorumları atla
                    if review['review_text']:
                        reviews.append(review)

        except Exception as e:
            print(f"❌ API hatası: {e}")
            # Alternatif yöntem dene
            return self._get_reviews_from_product_page(product_id, page)

        return reviews

    def _get_reviews_from_product_page(self, product_id: str, page: int) -> List[Dict]:
        """Ürün sayfasından direkt yorum çek - Alternatif yöntem"""
        reviews = []

        try:
            # Ürün sayfasını bul
            product = self.session.query(Product).filter(
                Product.site_product_id == product_id
            ).first()

            if not product or not product.product_url:
                return reviews

            # Ürün sayfasını çek
            response = self.scraper.get(product.product_url)
            if response.status_code != 200:
                return reviews

            soup = BeautifulSoup(response.text, 'html.parser')

            # JavaScript içindeki yorumları bul
            for script in soup.find_all('script'):
                if script.string and 'window.__PRODUCT_DETAIL_APP_INITIAL_STATE__' in script.string:
                    match = re.search(r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});',
                                    script.string, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))

                        # Yorumları çıkar
                        if 'product' in data and 'reviews' in data['product']:
                            for review in data['product']['reviews']['content']:
                                reviews.append({
                                    'reviewer_name': review.get('userFullName', 'Anonim'),
                                    'reviewer_verified': review.get('verifiedPurchase', False),
                                    'rating': review.get('rate', 0),
                                    'review_title': review.get('reviewTitle', ''),
                                    'review_text': review.get('comment', ''),
                                    'review_date': self._parse_date(review.get('lastModifiedDate')),
                                    'helpful_count': review.get('helpfulCount', 0),
                                    'seller_name': review.get('sellerName', '')
                                })

        except Exception as e:
            print(f"⚠️ Sayfa parse hatası: {e}")

        return reviews

    def _parse_date(self, date_str: str) -> datetime:
        """Tarih string'ini parse et"""
        if not date_str:
            return datetime.now()

        try:
            # ISO format: "2024-03-15T10:30:00.000Z"
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()

    def scrape_and_analyze_product_reviews(self, product_id: int):
        """Veritabanındaki bir ürün için yorumları çek ve analiz et"""

        # Ürünü bul
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return

        print(f"\n🔍 Yorumlar çekiliyor: {product.name[:50]}...")

        # Yorumları çek
        reviews = self.get_product_reviews(product.product_url or product.url, max_pages=10)

        if not reviews:
            print("❌ Yorum bulunamadı")
            return

        print(f"📝 {len(reviews)} yorum analiz ediliyor...")

        # Her yorumu analiz et ve kaydet
        for review_data in reviews:
            # AI analizi
            analysis = self.ai.analyze_review(review_data['review_text'])

            # Veritabanına kaydet
            review = ProductReview(
                product_id=product_id,
                reviewer_name=review_data['reviewer_name'],
                reviewer_verified=review_data['reviewer_verified'],
                rating=review_data['rating'],
                review_title=review_data['review_title'],
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

        self.session.commit()
        print(f"✅ {len(reviews)} yorum kaydedildi ve analiz edildi")

        # Toplu analiz
        reviews_for_bulk = [{'text': r['review_text'], 'rating': r['rating'],
                            'verified': r['reviewer_verified'], 'helpful_count': r['helpful_count']}
                           for r in reviews]

        bulk_analysis = self.ai.analyze_bulk_reviews(reviews_for_bulk)

        # Analiz sonuçlarını göster
        self._display_analysis_results(product.name, bulk_analysis)

        return bulk_analysis

    def _display_analysis_results(self, product_name: str, analysis: Dict):
        """Analiz sonuçlarını görselleştir"""

        print("\n" + "="*60)
        print(f"📊 YORUM ANALİZ RAPORU: {product_name[:40]}...")
        print("="*60)

        # Genel istatistikler
        print(f"\n📈 GENEL İSTATİSTİKLER:")
        print(f"  • Toplam Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f} (-1 ile +1 arası)")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")
        print(f"  • Doğrulanmış Alıcı: %{analysis['verified_percentage']:.1f}")

        # Duygu dağılımı
        print(f"\n😊 DUYGU DAĞILIMI:")
        dist = analysis['sentiment_distribution']
        print(f"  • Pozitif: %{dist['pozitif']:.1f} 😊")
        print(f"  • Nötr: %{dist['nötr']:.1f} 😐")
        print(f"  • Negatif: %{dist['negatif']:.1f} 😞")

        # Satın alma nedenleri
        print(f"\n🛒 SATIN ALMA NEDENLERİ:")
        for reason, count in analysis['top_purchase_reasons']:
            print(f"  • {reason.title()}: {count} kişi")

        # Artılar
        print(f"\n✅ EN ÇOK BELİRTİLEN ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez bahsedildi")

        # Eksiler
        if analysis['top_cons']:
            print(f"\n❌ EN ÇOK BELİRTİLEN EKSİLER:")
            for con, count in analysis['top_cons'][:5]:
                print(f"  • {con}: {count} kez bahsedildi")

        # Müşteri davranış tipleri
        print(f"\n👥 MÜŞTERİ DAVRANIŞ TİPLERİ:")
        for behavior, count in analysis['behavior_distribution'].items():
            print(f"  • {behavior.replace('_', ' ').title()}: {count} kişi")

        # İnsan davranışı içgörüleri
        insights = analysis['human_insights']
        print(f"\n🧠 İNSAN DAVRANIŞI ANALİZİ:")
        print(f"\n📍 Ana Motivasyon:")
        print(f"  {insights['ana_motivasyon']}")

        print(f"\n👤 Müşteri Profili:")
        print(f"  {insights['müşteri_profili']}")

        print(f"\n🎯 Satın Alma Psikolojisi:")
        print(f"  {insights['satın_alma_psikolojisi']}")

        print(f"\n✨ Başarı Faktörleri:")
        for factor in insights['başarı_faktörleri']:
            print(f"  • {factor}")

        if insights['risk_faktörleri'] and insights['risk_faktörleri'][0] != 'Belirgin risk faktörü yok':
            print(f"\n⚠️ Risk Faktörleri:")
            for risk in insights['risk_faktörleri']:
                print(f"  • {risk}")

        print(f"\n📌 GENEL TAVSİYE:")
        print(f"  {insights['tavsiye']}")

        print("\n" + "="*60)

    def scrape_all_best_sellers(self):
        """En çok satanların hepsinin yorumlarını çek"""
        # Son 7 günün en çok satanlarını bul
        from sqlalchemy import func
        from database import RankingHistory

        seven_days_ago = datetime.now() - timedelta(days=7)

        best_sellers = self.session.query(
            Product
        ).join(
            RankingHistory
        ).filter(
            RankingHistory.timestamp >= seven_days_ago,
            RankingHistory.rank_position <= 10  # Top 10
        ).distinct().all()

        print(f"📦 {len(best_sellers)} en çok satan ürün bulundu")

        for product in best_sellers:
            print(f"\n{'='*60}")
            print(f"İşleniyor: {product.name[:50]}...")

            # Daha önce yorum çekilmiş mi kontrol et
            existing_reviews = self.session.query(ProductReview).filter_by(
                product_id=product.id
            ).count()

            if existing_reviews > 0:
                print(f"  ℹ️ {existing_reviews} yorum zaten mevcut, atlanıyor...")
                continue

            # Yorumları çek ve analiz et
            self.scrape_and_analyze_product_reviews(product.id)

            # Rate limiting
            time.sleep(2)

        print("\n✅ Tüm en çok satanların yorumları analiz edildi")


if __name__ == "__main__":
    scraper = TrendyolReviewScraper()

    # Test: İlk ürünün yorumlarını çek
    session = SessionLocal()
    first_product = session.query(Product).first()

    if first_product:
        print(f"Test ürün: {first_product.name}")
        scraper.scrape_and_analyze_product_reviews(first_product.id)
    else:
        print("❌ Test edilecek ürün bulunamadı")

    session.close()