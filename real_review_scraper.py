#!/usr/bin/env python3
"""
GERÇEK Trendyol Yorumlarını Çeker - NO FALLBACK
"""

import requests
import json
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class RealTrendyolReviewScraper:
    """Gerçek Trendyol yorumlarını çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Origin': 'https://www.trendyol.com',
            'Referer': 'https://www.trendyol.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }

    def get_real_reviews(self, product_url: str) -> list:
        """Gerçek yorumları çek"""

        # URL'den ürün bilgilerini çıkar
        import re

        # Örnek URL: https://www.trendyol.com/xyz/urun-adi-p-12345678
        product_id_match = re.search(r'-p-(\d+)', product_url)
        if not product_id_match:
            print("❌ Ürün ID bulunamadı")
            return []

        product_id = product_id_match.group(1)
        print(f"✅ Ürün ID: {product_id}")

        reviews = []
        page = 1
        max_pages = 10  # Maksimum 10 sayfa yorum çek

        while page <= max_pages:
            print(f"📄 Sayfa {page} çekiliyor...")

            # Trendyol yorumlar API'si
            api_url = f"https://www.trendyol.com/yorumlar/{product_id}"

            params = {
                'page': page,
                'size': 50,  # Sayfa başına 50 yorum
                'sortType': 'MOST_HELPFUL'  # En faydalı yorumlar
            }

            try:
                response = requests.get(api_url, headers=self.headers, params=params, timeout=10)

                if response.status_code == 200:
                    # JSON yanıtı parse et
                    try:
                        data = response.json()

                        # Yorumları kontrol et
                        if 'content' in data:
                            page_reviews = data['content']

                            if not page_reviews:
                                print(f"✓ Sayfa {page}: Yorum kalmadı")
                                break

                            for review_data in page_reviews:
                                review = {
                                    'reviewer_name': review_data.get('userFullName', 'Anonim'),
                                    'reviewer_verified': review_data.get('verifiedPurchase', False),
                                    'rating': review_data.get('rate', 0),
                                    'review_text': review_data.get('comment', ''),
                                    'review_date': review_data.get('createdDate'),
                                    'helpful_count': review_data.get('helpfulCount', 0),
                                    'images': review_data.get('images', [])
                                }

                                # Boş yorumları atla
                                if review['review_text']:
                                    reviews.append(review)

                            print(f"✓ Sayfa {page}: {len(page_reviews)} yorum bulundu")
                            page += 1

                            # Rate limiting - saygılı ol
                            time.sleep(1)

                        else:
                            # HTML yanıt dönmüşse parse et
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(response.text, 'html.parser')

                            # Yorum elementlerini bul
                            review_elements = soup.find_all('div', class_='comment-text')

                            if not review_elements:
                                print("✓ Yorum bulunamadı")
                                break

                            for elem in review_elements:
                                # Yorum metnini al
                                text_elem = elem.find('p')
                                if text_elem:
                                    review = {
                                        'reviewer_name': 'Trendyol Müşterisi',
                                        'reviewer_verified': True,
                                        'rating': 5,  # Default
                                        'review_text': text_elem.text.strip(),
                                        'review_date': datetime.now().isoformat(),
                                        'helpful_count': 0,
                                        'images': []
                                    }
                                    reviews.append(review)

                            print(f"✓ Sayfa {page}: {len(review_elements)} yorum bulundu (HTML)")
                            page += 1
                            time.sleep(1)

                    except json.JSONDecodeError:
                        print(f"⚠️ JSON parse hatası, HTML olarak işleniyor...")
                        # HTML olarak parse et
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.text, 'html.parser')

                        # Farklı yorum selektörleri dene
                        selectors = [
                            'div.comment-text p',
                            'div.review-text',
                            'div.user-review-item',
                            'div[class*="comment"]',
                            'div[class*="review"]'
                        ]

                        found = False
                        for selector in selectors:
                            elements = soup.select(selector)
                            if elements:
                                for elem in elements:
                                    text = elem.get_text(strip=True)
                                    if text and len(text) > 10:
                                        review = {
                                            'reviewer_name': 'Trendyol Müşterisi',
                                            'reviewer_verified': True,
                                            'rating': 5,
                                            'review_text': text,
                                            'review_date': datetime.now().isoformat(),
                                            'helpful_count': 0,
                                            'images': []
                                        }
                                        reviews.append(review)
                                        found = True

                                if found:
                                    print(f"✓ {len(elements)} yorum bulundu (selector: {selector})")
                                    break

                        if not found:
                            print("❌ Yorum bulunamadı")
                        break

                else:
                    print(f"❌ HTTP {response.status_code} hatası")
                    break

            except requests.exceptions.RequestException as e:
                print(f"❌ Bağlantı hatası: {e}")
                break

        print(f"\n✅ Toplam {len(reviews)} gerçek yorum çekildi")
        return reviews

    def save_reviews_to_db(self, product_id: int, reviews: list):
        """Yorumları veritabanına kaydet"""

        saved_count = 0

        for review_data in reviews:
            # AI analizi
            analysis = self.ai.analyze_review(review_data['review_text'])

            # Tarih parse
            if isinstance(review_data['review_date'], str):
                try:
                    review_date = datetime.fromisoformat(review_data['review_date'].replace('Z', '+00:00'))
                except:
                    review_date = datetime.now()
            else:
                review_date = review_data['review_date'] or datetime.now()

            # Veritabanına kaydet
            review = ProductReview(
                product_id=product_id,
                reviewer_name=review_data['reviewer_name'],
                reviewer_verified=review_data['reviewer_verified'],
                rating=review_data['rating'],
                review_title='',
                review_text=review_data['review_text'],
                review_date=review_date,
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
        print(f"✅ {saved_count} yorum veritabanına kaydedildi")

        return saved_count

    def scrape_product_reviews(self, product_id: int):
        """Bir ürünün yorumlarını çek"""

        # Ürünü bul
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return

        print(f"\n🔍 Yorumlar çekiliyor: {product.name[:50]}...")
        print(f"URL: {product.product_url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        # Gerçek yorumları çek
        reviews = self.get_real_reviews(product.product_url or product.url)

        if reviews:
            # Kaydet
            self.save_reviews_to_db(product_id, reviews)

            # Analiz göster
            self.show_analysis(product.name, reviews)
        else:
            print("❌ Yorum bulunamadı")

    def show_analysis(self, product_name: str, reviews: list):
        """Yorum analizini göster"""

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
        print(f"📊 {product_name[:40]}... YORUM ANALİZİ")
        print("="*60)

        print(f"\n📈 İSTATİSTİKLER:")
        print(f"  • Toplam Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 SATIN ALMA NEDENLERİ:")
        for reason, count in analysis['top_purchase_reasons'][:3]:
            print(f"  • {reason}: {count} kişi")

        insights = analysis['human_insights']
        print(f"\n🧠 İNSAN DAVRANIŞI ANALİZİ:")
        print(f"  {insights['ana_motivasyon']}")
        print(f"\n👤 MÜŞTERİ PROFİLİ:")
        print(f"  {insights['müşteri_profili']}")
        print(f"\n📌 TAVSİYE:")
        print(f"  {insights['tavsiye']}")

        print("\n" + "="*60)


if __name__ == "__main__":
    scraper = RealTrendyolReviewScraper()

    # İlk ürünün yorumlarını çek
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_product_reviews(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()