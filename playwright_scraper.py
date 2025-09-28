#!/usr/bin/env python3
"""
Playwright ile GERÇEK Trendyol Yorumları Çeker
Chrome kurulu olmasa bile çalışır!
"""

from playwright.sync_api import sync_playwright
import json
import re
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class PlaywrightScraper:
    """Playwright ile gerçek Trendyol yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [
            r'-p-(\d+)',
            r'/product/(\d+)',
            r'productId=(\d+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def scrape_with_playwright(self, product_id):
        """Playwright ile yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🎭 PLAYWRIGHT İLE GERÇEK YORUM ÇEKME")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        with sync_playwright() as p:
            # Browser başlat (headless modda)
            print("🌐 Browser başlatılıyor...")
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )

            # Yeni sayfa aç
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='tr-TR'
            )

            page = context.new_page()

            # Anti-detection JavaScript ekle
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            reviews = []

            try:
                print(f"📄 Sayfa açılıyor: {product.product_url or product.url}")
                page.goto(product.product_url or product.url, wait_until='domcontentloaded')

                # Sayfa yüklenmesini bekle
                page.wait_for_timeout(3000)

                # Cookie banner'ı kapat
                try:
                    page.click('#onetrust-accept-btn-handler', timeout=3000)
                    print("✓ Cookie banner kapatıldı")
                except:
                    pass

                # Önce sayfadaki initial state'ten yorumları al
                try:
                    # JavaScript'ten veri çek
                    initial_state = page.evaluate("""
                        () => {
                            if (window.__PRODUCT_DETAIL_APP_INITIAL_STATE__) {
                                return window.__PRODUCT_DETAIL_APP_INITIAL_STATE__;
                            }
                            return null;
                        }
                    """)

                    if initial_state:
                        # Yorumları bul
                        if 'product' in initial_state:
                            product_data = initial_state['product']

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
                except Exception as e:
                    print(f"⚠️ Initial state okunamadı: {e}")

                # Eğer initial state'ten yorum bulunamadıysa DOM'dan çek
                if not reviews:
                    print("🔍 DOM'dan yorum aranıyor...")

                    # Yorumlar bölümüne scroll
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                    page.wait_for_timeout(2000)

                    # Tüm yorumları göster butonuna tıkla
                    try:
                        page.click("button:has-text('Tüm Yorumları Gör')", timeout=3000)
                        page.wait_for_timeout(2000)
                        print("✓ Tüm yorumlar açıldı")
                    except:
                        pass

                    # Yorumları topla
                    review_elements = page.query_selector_all("div.comment-text, div.pr-xc-w, div[class*='review']")

                    for elem in review_elements[:50]:  # Max 50 yorum
                        try:
                            text = elem.inner_text()
                            if text and len(text) > 10:
                                reviews.append({
                                    'reviewer_name': 'Trendyol Müşterisi',
                                    'reviewer_verified': True,
                                    'rating': 5,
                                    'review_text': text,
                                    'review_date': datetime.now(),
                                    'helpful_count': 0
                                })
                        except:
                            continue

                # API'den de deneyelim
                if not reviews:
                    product_trendyol_id = self.extract_product_id(product.product_url or product.url)
                    if product_trendyol_id:
                        print(f"📡 API'den yorumlar çekiliyor (ID: {product_trendyol_id})...")

                        api_url = f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_trendyol_id}?page=0&size=50"

                        response = page.evaluate(f"""
                            async () => {{
                                try {{
                                    const response = await fetch('{api_url}', {{
                                        headers: {{
                                            'Accept': 'application/json',
                                            'Accept-Language': 'tr-TR,tr;q=0.9'
                                        }}
                                    }});
                                    return await response.json();
                                }} catch (e) {{
                                    return null;
                                }}
                            }}
                        """)

                        if response and 'result' in response:
                            if 'productReviews' in response['result'] and 'content' in response['result']['productReviews']:
                                api_reviews = response['result']['productReviews']['content']
                                print(f"✓ API'den {len(api_reviews)} yorum alındı")

                                for r in api_reviews:
                                    if r.get('comment'):
                                        reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                            'reviewer_verified': r.get('verifiedPurchase', False),
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment', ''),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })

            except Exception as e:
                print(f"❌ Hata: {e}")
            finally:
                browser.close()

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
                print("✅ PLAYWRIGHT İLE BAŞARILI!")
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

        print("\n" + "="*60)
        print(f"📊 {product_name[:40]}... GERÇEK YORUM ANALİZİ")
        print("="*60)

        print(f"\n📈 İSTATİSTİKLER:")
        print(f"  • Toplam Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA:")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez")

        if analysis['top_cons']:
            print(f"\n❌ EKSİLER:")
            for con, count in analysis['top_cons'][:3]:
                print(f"  • {con}: {count} kez")


if __name__ == "__main__":
    print("="*60)
    print("🎭 PLAYWRIGHT SCRAPER")
    print("✅ Chrome gerekmez - Chromium kullanır")
    print("✅ Headless modda çalışır")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = PlaywrightScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_with_playwright(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()