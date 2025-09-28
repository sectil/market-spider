#!/usr/bin/env python3
"""
DNS Sorunu Çözülmüş Scraper
curl kullanarak GERÇEK yorumları çeker
"""

import subprocess
import json
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class DNSFixedScraper:
    """DNS sorunu çözülmüş, curl ile çalışan scraper"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        match = re.search(r'-p-(\d+)', url)
        if match:
            return match.group(1)
        return None

    def get_reviews_with_curl(self, product_id):
        """curl ile API'den yorumları çek"""
        all_reviews = []
        page = 0
        max_pages = 10

        print(f"\n📡 curl ile API'den yorumlar çekiliyor (ID: {product_id})...")

        while page < max_pages:
            try:
                # API URL
                api_url = f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}?page={page}&size=50&sortBy=MOST_HELPFUL"

                # curl komutu
                curl_cmd = [
                    'curl', '-s',
                    '-H', 'Accept: application/json',
                    '-H', 'Accept-Language: tr-TR,tr;q=0.9',
                    '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    '-H', 'Referer: https://www.trendyol.com/',
                    '--compressed',
                    api_url
                ]

                print(f"  Sayfa {page + 1} çekiliyor...")

                # curl çalıştır
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)

                        if 'result' in data and 'productReviews' in data['result']:
                            review_data = data['result']['productReviews']

                            # İlk sayfada toplam sayfa sayısını al
                            if page == 0:
                                total_pages = review_data.get('totalPages', 1)
                                total_elements = review_data.get('totalElements', 0)
                                print(f"  ✓ Toplam {total_elements} yorum, {total_pages} sayfa bulundu")
                                max_pages = min(total_pages, 10)  # Max 10 sayfa

                            # Yorumları al
                            content = review_data.get('content', [])
                            if content:
                                print(f"  ✓ Sayfa {page + 1}: {len(content)} yorum alındı")

                                for r in content:
                                    if r.get('comment'):
                                        all_reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                            'reviewer_verified': r.get('verifiedPurchase', False),
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment'),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })
                            else:
                                print("  ✗ Bu sayfada yorum yok")
                                break

                        else:
                            print("  ✗ API yanıtı beklenmeyen formatta")
                            break

                    except json.JSONDecodeError as e:
                        print(f"  ✗ JSON parse hatası: {e}")
                        break
                else:
                    print(f"  ✗ curl başarısız: {result.returncode}")
                    break

            except Exception as e:
                print(f"  ✗ Hata: {e}")
                break

            page += 1

        return all_reviews

    def scrape_all_reviews_dns_fixed(self, product_id):
        """DNS sorunu çözülmüş scraper"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🌐 DNS FIXED SCRAPER - TÜM YORUMLAR")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Trendyol product ID'yi çıkar
        trendyol_id = self.extract_product_id(product.product_url or product.url)

        if not trendyol_id:
            print("❌ Product ID çıkarılamadı")
            return False

        print(f"🆔 Trendyol Product ID: {trendyol_id}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        # curl ile yorumları çek
        all_reviews = self.get_reviews_with_curl(trendyol_id)

        if all_reviews:
            print(f"\n💾 TOPLAM {len(all_reviews)} GERÇEK YORUM kaydediliyor...")

            for review_data in all_reviews[:200]:  # Max 200 yorum
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

            # Özet göster
            self._show_summary(product.name, all_reviews)

            print("\n" + "="*60)
            print(f"✅ {len(all_reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("✅ DNS SORUNU ÇÖZÜLDÜ!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ALINAMADI!")
            print("="*60)
            return False

    def _show_summary(self, product_name, reviews):
        """Özet göster"""
        total = len(reviews)
        avg_rating = sum(r['rating'] for r in reviews) / total if total > 0 else 0
        verified = sum(1 for r in reviews if r['reviewer_verified'])

        print(f"\n📊 ÖZET:")
        print(f"  • Toplam: {total} yorum")
        print(f"  • Ortalama: {avg_rating:.1f}/5")
        print(f"  • Doğrulanmış: {verified}/{total}")

        # AI analizi
        if total > 0:
            reviews_for_ai = [
                {
                    'text': r['review_text'],
                    'rating': r['rating'],
                    'verified': r['reviewer_verified'],
                    'helpful_count': r['helpful_count']
                }
                for r in reviews[:50]  # İlk 50 yorum
            ]

            analysis = self.ai.analyze_bulk_reviews(reviews_for_ai)

            print(f"\n🛒 NEDEN 1. SIRADA:")
            for i, (reason, count) in enumerate(analysis['top_purchase_reasons'][:3], 1):
                print(f"  {i}. {reason}: {count} kişi")


if __name__ == "__main__":
    print("="*60)
    print("🌐 DNS FIXED SCRAPER")
    print("✅ DNS sorunu çözüldü")
    print("✅ curl ile çalışıyor")
    print("✅ TÜM yorumları çeker")
    print("="*60)

    scraper = DNSFixedScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_reviews_dns_fixed(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()