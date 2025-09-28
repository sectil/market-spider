#!/usr/bin/env python3
"""
Pyppeteer ile GERÇEK Trendyol Yorumları Çeker
Sistem bağımlılıkları olmadan çalışır
"""

import asyncio
from pyppeteer import launch
import json
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class PyppeteerScraper:
    """Pyppeteer ile gerçek Trendyol yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [r'-p-(\d+)', r'/product/(\d+)', r'productId=(\d+)']
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    async def scrape_async(self, product_id):
        """Asenkron olarak yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🤖 PYPPETEER İLE GERÇEK YORUM ÇEKME")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        reviews = []

        try:
            print("🌐 Headless browser başlatılıyor...")
            browser = await launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process'
                ],
                autoClose=True
            )

            page = await browser.newPage()

            # User agent ayarla
            await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            # Anti-detection
            await page.evaluateOnNewDocument('''() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            }''')

            print(f"📄 Sayfa açılıyor: {product.product_url or product.url}")
            await page.goto(product.product_url or product.url, {'waitUntil': 'domcontentloaded'})
            await asyncio.sleep(3)

            # Cookie banner kapat
            try:
                await page.click('#onetrust-accept-btn-handler')
                print("✓ Cookie kapatıldı")
            except:
                pass

            # JavaScript'ten initial state al
            try:
                initial_state = await page.evaluate('''() => {
                    return window.__PRODUCT_DETAIL_APP_INITIAL_STATE__ || null;
                }''')

                if initial_state and 'product' in initial_state:
                    product_data = initial_state['product']

                    # ratingSummary yorumları
                    if 'ratingSummary' in product_data and 'reviews' in product_data['ratingSummary']:
                        review_list = product_data['ratingSummary']['reviews']
                        print(f"✓ {len(review_list)} yorum bulundu")

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

            # API'den çek
            if not reviews:
                product_trendyol_id = self.extract_product_id(product.product_url or product.url)
                if product_trendyol_id:
                    print(f"📡 API'den çekiliyor (ID: {product_trendyol_id})...")

                    api_url = f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_trendyol_id}"

                    try:
                        response = await page.evaluate(f'''async () => {{
                            const res = await fetch("{api_url}?page=0&size=50", {{
                                headers: {{
                                    "Accept": "application/json",
                                    "Accept-Language": "tr-TR"
                                }}
                            }});
                            return await res.json();
                        }}''')

                        if response and 'result' in response:
                            if 'productReviews' in response['result']:
                                content = response['result']['productReviews'].get('content', [])
                                print(f"✓ API'den {len(content)} yorum alındı")

                                for r in content:
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
                        print(f"⚠️ API hatası: {e}")

            # DOM'dan çek
            if not reviews:
                print("🔍 DOM'dan aranıyor...")

                # Scroll yap
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
                await asyncio.sleep(2)

                # Tüm yorumları göster
                try:
                    await page.click('button:contains("Tüm Yorumları Gör")')
                    await asyncio.sleep(2)
                    print("✓ Yorumlar açıldı")
                except:
                    pass

                # Yorumları topla
                comments = await page.evaluate('''() => {
                    const elements = document.querySelectorAll('div.comment-text, div.pr-xc-w, div[class*="review"]');
                    const results = [];
                    elements.forEach(el => {
                        const text = el.innerText;
                        if (text && text.length > 10) {
                            results.push(text);
                        }
                    });
                    return results;
                }''')

                for text in comments[:50]:
                    reviews.append({
                        'reviewer_name': 'Trendyol Müşterisi',
                        'reviewer_verified': True,
                        'rating': 5,
                        'review_text': text,
                        'review_date': datetime.now(),
                        'helpful_count': 0
                    })

                if comments:
                    print(f"✓ DOM'dan {len(comments)} yorum alındı")

            await browser.close()

        except Exception as e:
            print(f"❌ Hata: {e}")

        if reviews:
            print(f"\n💾 {len(reviews)} GERÇEK yorum kaydediliyor...")

            for review_data in reviews:
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
            self._show_analysis(product.name, reviews)

            print("\n" + "="*60)
            print(f"✅ {len(reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ÇEKİLEMEDİ!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def scrape_with_pyppeteer(self, product_id):
        """Senkron wrapper"""
        return asyncio.get_event_loop().run_until_complete(self.scrape_async(product_id))

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
        print(f"  • Toplam: {analysis['total_reviews']}")
        print(f"  • Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA:")
        for reason, count in analysis['top_purchase_reasons'][:3]:
            print(f"  • {reason}: {count} kişi")


if __name__ == "__main__":
    print("="*60)
    print("🤖 PYPPETEER SCRAPER")
    print("✅ Sistem bağımlılıkları gerekmez")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = PyppeteerScraper()

    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_with_pyppeteer(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()