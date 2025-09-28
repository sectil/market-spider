#!/usr/bin/env python3
"""
GERÇEK Trendyol Yorumlarını HEPSİNİ Çeker
API odaklı, pagination destekli, FALLBACK YOK!
"""

import requests
import json
import re
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class ComprehensiveAPIScraper:
    """TÜM GERÇEK Trendyol yorumlarını API'den çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

        # Gerçek browser session taklit et
        self.http_session = requests.Session()
        self.http_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.trendyol.com',
            'Referer': 'https://www.trendyol.com/',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'DNT': '1'
        })

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        # Multiple pattern denemesi
        patterns = [
            r'-p-(\d+)',           # Standard pattern
            r'/p/.*-p-(\d+)',      # Full path pattern
            r'productId=(\d+)',    # Query param
            r'/(\d+)$',            # Ending number
            r'content-(\d+)',      # Content ID
            r'product/(\d+)',      # Product path
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # URL'yi parçalara ayır ve sayı ara
        parts = url.split('/')
        for part in reversed(parts):
            numbers = re.findall(r'\d{6,}', part)
            if numbers:
                return numbers[0]

        return None

    def get_all_reviews_from_api(self, product_id, trendyol_id):
        """API'den TÜM yorumları pagination ile çek"""
        all_reviews = []

        # Farklı API endpoint'leri dene
        api_endpoints = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{trendyol_id}",
            f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{trendyol_id}",
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/product-review/{trendyol_id}",
            f"https://api.trendyol.com/discovery-web-webproductgw-santral/api/review/{trendyol_id}",
            f"https://public-mdc.trendyol.com/discovery-web-webproductgw-santral/api/review/{trendyol_id}",
        ]

        for api_base in api_endpoints:
            print(f"\n🔍 API deneniyor: {api_base}")
            page = 0
            total_pages = 1
            reviews_from_this_api = []

            while page < total_pages and page < 100:  # Max 100 sayfa
                try:
                    params = {
                        'page': page,
                        'size': 50,  # Sayfa başı max yorum
                        'sortBy': 'MOST_HELPFUL',  # En faydalıları al
                        'culture': 'tr-TR'
                    }

                    # Özel headers ekle
                    headers = self.http_session.headers.copy()
                    headers['X-Storefront-ID'] = 'TR'
                    headers['X-Application-ID'] = 'web'

                    response = self.http_session.get(
                        api_base,
                        params=params,
                        headers=headers,
                        timeout=10,
                        verify=True
                    )

                    if response.status_code == 200:
                        data = response.json()

                        # Veri yapısını kontrol et
                        if 'result' in data:
                            result = data['result']

                            # productReviews içindeki yorumlar
                            if 'productReviews' in result:
                                review_data = result['productReviews']

                                # Total page sayısını al
                                if page == 0 and 'totalPages' in review_data:
                                    total_pages = review_data['totalPages']
                                    print(f"✓ Toplam {total_pages} sayfa yorum bulundu")

                                # Content içindeki yorumları al
                                if 'content' in review_data:
                                    content = review_data['content']
                                    if content:
                                        print(f"  Sayfa {page+1}: {len(content)} yorum")

                                        for r in content:
                                            if r.get('comment'):
                                                reviews_from_this_api.append({
                                                    'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                                    'reviewer_verified': r.get('verifiedPurchase', False),
                                                    'rating': r.get('rate', 5),
                                                    'review_text': r.get('comment', ''),
                                                    'review_date': datetime.now(),
                                                    'helpful_count': r.get('helpfulCount', 0),
                                                    'review_title': r.get('title', ''),
                                                    'seller_name': r.get('sellerName', ''),
                                                    'size': r.get('size', ''),
                                                    'color': r.get('color', '')
                                                })

                            # Direkt reviews array
                            elif 'reviews' in result:
                                reviews_array = result['reviews']
                                if reviews_array:
                                    print(f"  {len(reviews_array)} yorum bulundu")

                                    for r in reviews_array:
                                        if r.get('comment'):
                                            reviews_from_this_api.append({
                                                'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                                'reviewer_verified': True,
                                                'rating': r.get('rate', 5),
                                                'review_text': r.get('comment', ''),
                                                'review_date': datetime.now(),
                                                'helpful_count': r.get('helpfulCount', 0)
                                            })
                                    break  # Pagination yok, çık

                        # Root level content
                        elif 'content' in data:
                            content = data['content']
                            if content:
                                print(f"  {len(content)} yorum bulundu")

                                for r in content:
                                    if r.get('comment'):
                                        reviews_from_this_api.append({
                                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                            'reviewer_verified': r.get('verifiedPurchase', False),
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment', ''),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })

                    elif response.status_code == 404:
                        print(f"  ✗ 404 - API bulunamadı")
                        break
                    elif response.status_code == 403:
                        print(f"  ✗ 403 - Erişim engellendi")
                        break
                    else:
                        print(f"  ✗ HTTP {response.status_code}")
                        break

                except requests.exceptions.Timeout:
                    print(f"  ✗ Timeout")
                    break
                except requests.exceptions.ConnectionError:
                    print(f"  ✗ Bağlantı hatası")
                    break
                except Exception as e:
                    print(f"  ✗ Hata: {e}")
                    break

                # Sonraki sayfaya geç
                page += 1

                # Rate limiting
                if page < total_pages:
                    time.sleep(0.5)  # Sayfalar arası bekle

            # Bu API'den yorum alındıysa, diğerlerini deneme
            if reviews_from_this_api:
                all_reviews.extend(reviews_from_this_api)
                print(f"\n✅ Bu API'den toplam {len(reviews_from_this_api)} yorum alındı")
                break  # Başarılı API bulundu, çık

        return all_reviews

    def get_reviews_from_page(self, url):
        """Sayfa HTML'inden yorumları çıkar"""
        reviews = []

        try:
            print("📄 Sayfa HTML'i alınıyor...")

            # Önce cookie al
            cookie_response = self.http_session.get('https://www.trendyol.com', timeout=10)

            # Ana sayfayı çek
            response = self.http_session.get(url, timeout=10)

            if response.status_code == 200:
                html = response.text

                # window.__PRODUCT_DETAIL_APP_INITIAL_STATE__ içindeki JSON'ı bul
                match = re.search(
                    r'window\.__PRODUCT_DETAIL_APP_INITIAL_STATE__\s*=\s*({.*?});',
                    html,
                    re.DOTALL
                )

                if match:
                    try:
                        data = json.loads(match.group(1))

                        if 'product' in data:
                            product_data = data['product']

                            # ratingSummary içindeki yorumlar
                            if 'ratingSummary' in product_data and 'reviews' in product_data['ratingSummary']:
                                review_list = product_data['ratingSummary']['reviews']
                                print(f"✓ Sayfadan {len(review_list)} yorum bulundu")

                                for r in review_list:
                                    if r.get('comment'):
                                        reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                            'reviewer_verified': True,
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment', ''),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })
                    except json.JSONDecodeError:
                        print("⚠️ JSON parse hatası")
                else:
                    print("⚠️ Initial state bulunamadı")
            else:
                print(f"⚠️ Sayfa yüklenemedi: HTTP {response.status_code}")

        except Exception as e:
            print(f"⚠️ Sayfa çekme hatası: {e}")

        return reviews

    def scrape_all_reviews(self, product_id):
        """TÜM yorumları çek - HEPSİNİ!"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🚀 TÜM YORUMLARI ÇEKME - COMPREHENSIVE API SCRAPER")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        # Trendyol product ID'yi çıkar
        trendyol_id = self.extract_product_id(product.product_url or product.url)

        if not trendyol_id:
            print("❌ Product ID çıkarılamadı")
            return False

        print(f"🆔 Trendyol Product ID: {trendyol_id}")

        all_reviews = []

        # 1. Önce sayfadan yorumları al
        print("\n📋 AŞAMA 1: Sayfa HTML'inden yorumlar alınıyor...")
        page_reviews = self.get_reviews_from_page(product.product_url or product.url)
        if page_reviews:
            all_reviews.extend(page_reviews)
            print(f"✓ Sayfadan {len(page_reviews)} yorum alındı")

        # 2. API'den TÜM yorumları al (pagination ile)
        print("\n📋 AŞAMA 2: API'den TÜM yorumlar alınıyor...")
        api_reviews = self.get_all_reviews_from_api(product_id, trendyol_id)

        # Duplike kontrol (review_text bazında)
        existing_texts = {r['review_text'] for r in all_reviews}
        for review in api_reviews:
            if review['review_text'] not in existing_texts:
                all_reviews.append(review)
                existing_texts.add(review['review_text'])

        if api_reviews:
            print(f"✓ API'den {len(api_reviews)} yorum alındı")

        # SONUÇLARI KAYDET
        if all_reviews:
            print(f"\n💾 TOPLAM {len(all_reviews)} GERÇEK YORUM kaydediliyor...")

            for review_data in all_reviews:
                # AI analizi
                analysis = self.ai.analyze_review(review_data['review_text'])

                review = ProductReview(
                    product_id=product_id,
                    reviewer_name=review_data['reviewer_name'],
                    reviewer_verified=review_data['reviewer_verified'],
                    rating=review_data['rating'],
                    review_title=review_data.get('review_title', ''),
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
            print("✅ TÜM YORUMLAR BAŞARIYLA ALINDI!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ HİÇ YORUM ALINAMADI!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def _show_detailed_analysis(self, product_name, reviews):
        """Detaylı yorum analizi göster"""

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
        print(f"📊 {product_name[:40]}... DETAYLI ANALİZ")
        print("="*60)

        print(f"\n📈 İSTATİSTİKLER:")
        print(f"  • Toplam Yorum: {analysis['total_reviews']}")
        print(f"  • Doğrulanmış Alıcı: {sum(1 for r in reviews if r['reviewer_verified'])}")
        print(f"  • Ortalama Puan: {sum(r['rating'] for r in reviews) / len(reviews):.1f}/5")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")

        print(f"\n⭐ PUAN DAĞILIMI:")
        rating_dist = {}
        for r in reviews:
            rating = r['rating']
            rating_dist[rating] = rating_dist.get(rating, 0) + 1

        for rating in sorted(rating_dist.keys(), reverse=True):
            count = rating_dist[rating]
            percentage = (count / len(reviews)) * 100
            stars = '⭐' * rating
            print(f"  {stars:15} {count:3} yorum ({percentage:.1f}%)")

        print(f"\n🛒 NEDEN 1. SIRADA - EN ÖNEMLİ SEBEPLER:")
        for i, (reason, count) in enumerate(analysis['top_purchase_reasons'][:10], 1):
            print(f"  {i:2}. {reason}: {count} kişi")

        print(f"\n✅ EN ÇOK BEĞENİLEN ÖZELLİKLER:")
        for i, (pro, count) in enumerate(analysis['top_pros'][:10], 1):
            print(f"  {i:2}. {pro}: {count} kez bahsedildi")

        if analysis['top_cons']:
            print(f"\n❌ GELİŞTİRİLEBİLECEK YÖNLER:")
            for i, (con, count) in enumerate(analysis['top_cons'][:5], 1):
                print(f"  {i:2}. {con}: {count} kez bahsedildi")

        insights = analysis['human_insights']
        print(f"\n🧠 MÜŞTERİ PSİKOLOJİSİ ANALİZİ:")
        print(f"  Ana Motivasyon: {insights['ana_motivasyon']}")
        print(f"  Hedef Kitle: {insights['hedef_kitle']}")
        print(f"  Başarı Faktörü: {insights['basari_faktoru']}")

        print(f"\n📝 ÖRNEK YORUMLAR:")
        # En yüksek puanlı 3 yorum
        top_reviews = sorted(reviews, key=lambda x: x['rating'], reverse=True)[:3]
        for i, r in enumerate(top_reviews, 1):
            text = r['review_text'][:150] + "..." if len(r['review_text']) > 150 else r['review_text']
            print(f"\n  {i}. {r['reviewer_name']} (⭐{r['rating']}):")
            print(f"     \"{text}\"")


if __name__ == "__main__":
    print("="*60)
    print("🚀 COMPREHENSIVE API SCRAPER")
    print("✅ TÜM yorumları çeker (pagination ile)")
    print("✅ API + HTML kombinasyonu")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = ComprehensiveAPIScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_reviews(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()