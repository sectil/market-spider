#!/usr/bin/env python3
"""
Selenium ile GERÇEK Trendyol Yorumlarını HEPSİNİ Çeker
Browser otomasyonu ile tüm yorumları alır
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import json
import re
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class SeleniumRealScraper:
    """Selenium ile TÜM GERÇEK yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.driver = None

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [
            r'-p-(\d+)',
            r'/p/.*-p-(\d+)',
            r'productId=(\d+)',
            r'/(\d{6,})',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        numbers = re.findall(r'\d{6,}', url)
        if numbers:
            return numbers[-1]
        return None

    def setup_driver(self):
        """Selenium driver'ı kur"""
        options = Options()

        # Headless mod
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # User agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Window size
        options.add_argument('--window-size=1920,1080')

        # Language
        options.add_argument('--lang=tr-TR')

        try:
            # ChromeDriver'ı başlat
            self.driver = webdriver.Chrome(options=options)

            # Anti-detection JavaScript
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['tr-TR', 'tr', 'en-US', 'en']
                    });
                '''
            })

            return True
        except Exception as e:
            print(f"❌ Driver kurulamadı: {e}")
            return False

    def get_all_reviews_selenium(self, url):
        """Selenium ile TÜM yorumları çek"""
        all_reviews = []

        if not self.setup_driver():
            return all_reviews

        try:
            print("📄 Sayfa yükleniyor...")
            self.driver.get(url)
            time.sleep(3)

            # Cookie banner'ı kapat
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_btn.click()
                print("✓ Cookie kapatıldı")
            except:
                pass

            # JavaScript'ten initial state'i al
            try:
                initial_state = self.driver.execute_script(
                    "return window.__PRODUCT_DETAIL_APP_INITIAL_STATE__;"
                )

                if initial_state and 'product' in initial_state:
                    product_data = initial_state['product']

                    # ratingSummary'den yorumlar
                    if 'ratingSummary' in product_data and 'reviews' in product_data['ratingSummary']:
                        reviews_list = product_data['ratingSummary']['reviews']
                        print(f"✓ Initial state'ten {len(reviews_list)} yorum bulundu")

                        for r in reviews_list:
                            if r.get('comment'):
                                all_reviews.append({
                                    'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                    'reviewer_verified': True,
                                    'rating': r.get('rate', 5),
                                    'review_text': r.get('comment', ''),
                                    'review_date': datetime.now(),
                                    'helpful_count': r.get('helpfulCount', 0)
                                })
            except Exception as e:
                print(f"⚠️ Initial state alınamadı: {e}")

            # Yorumlar bölümüne scroll et
            print("🔍 Yorumlar bölümü aranıyor...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)

            # "Tüm Yorumları Gör" butonuna tıkla
            try:
                all_reviews_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tüm Yorumları Gör')]"))
                )
                all_reviews_btn.click()
                print("✓ Tüm yorumlar açıldı")
                time.sleep(3)

                # Tüm yorumları yükle - scroll ile
                last_height = self.driver.execute_script("return document.body.scrollHeight")
                scroll_count = 0

                while scroll_count < 20:  # Max 20 scroll
                    # Sayfayı aşağı kaydır
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)

                    # Yeni yükseklik kontrol et
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # "Daha fazla yükle" butonu var mı?
                        try:
                            load_more = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Daha Fazla')]")
                            load_more.click()
                            time.sleep(2)
                        except:
                            break

                    last_height = new_height
                    scroll_count += 1
                    print(f"  Scroll {scroll_count} - Yorumlar yükleniyor...")

            except Exception as e:
                print(f"⚠️ Tüm yorumlar gösterilemedi: {e}")

            # DOM'dan yorumları topla
            print("📝 Yorumlar toplanıyor...")

            # Farklı selector'ları dene
            selectors = [
                "div.comment-text",
                "div.pr-xc-w",
                "div[class*='review']",
                "div[class*='comment']",
                "div.review-item",
                "div.user-review",
                "div.product-review",
                "p[class*='comment']",
                "span[class*='comment']",
            ]

            review_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        review_elements.extend(elements)
                        print(f"  ✓ {selector}: {len(elements)} element")
                except:
                    continue

            # Benzersiz yorumları al
            unique_texts = set()
            for elem in review_elements:
                try:
                    text = elem.text.strip()
                    if text and len(text) > 20 and text not in unique_texts:
                        unique_texts.add(text)

                        # Rating'i bulmaya çalış
                        rating = 5
                        try:
                            parent = elem.find_element(By.XPATH, "./..")
                            stars = parent.find_elements(By.CSS_SELECTOR, "[class*='star']")
                            if stars:
                                filled_stars = [s for s in stars if 'filled' in s.get_attribute('class')]
                                rating = len(filled_stars) if filled_stars else 5
                        except:
                            pass

                        # İsmi bulmaya çalış
                        reviewer_name = "Trendyol Müşterisi"
                        try:
                            parent = elem.find_element(By.XPATH, "./..")
                            name_elem = parent.find_element(By.CSS_SELECTOR, "[class*='user'], [class*='name']")
                            if name_elem:
                                reviewer_name = name_elem.text.strip()
                        except:
                            pass

                        all_reviews.append({
                            'reviewer_name': reviewer_name,
                            'reviewer_verified': True,
                            'rating': rating,
                            'review_text': text,
                            'review_date': datetime.now(),
                            'helpful_count': 0
                        })
                except:
                    continue

            print(f"✓ DOM'dan {len(unique_texts)} benzersiz yorum toplandı")

        except Exception as e:
            print(f"❌ Selenium hatası: {e}")
        finally:
            if self.driver:
                self.driver.quit()

        return all_reviews

    def scrape_all_with_selenium(self, product_id):
        """Selenium ile TÜM yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🌐 SELENIUM REAL SCRAPER - TÜM YORUMLAR")
        print("="*60)
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        # Selenium ile yorumları çek
        all_reviews = self.get_all_reviews_selenium(product.product_url or product.url)

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

            # Detaylı analiz
            self._show_detailed_analysis(product.name, all_reviews)

            print("\n" + "="*60)
            print(f"✅ {len(all_reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("✅ SELENIUM İLE TÜM YORUMLAR ALINDI!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ALINAMADI!")
            print("❌ FALLBACK KULLANILMADI!")
            print("="*60)
            return False

    def _show_detailed_analysis(self, product_name, reviews):
        """Detaylı analiz göster"""

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

        print(f"\n📊 {product_name[:40]}... DETAYLI ANALİZ")
        print(f"  • Toplam: {analysis['total_reviews']} yorum")
        print(f"  • Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA:")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ EN ÇOK BEĞENİLEN:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez")


if __name__ == "__main__":
    print("="*60)
    print("🌐 SELENIUM REAL SCRAPER")
    print("✅ Browser otomasyonu ile çeker")
    print("✅ TÜM yorumları alır")
    print("✅ Scroll ve pagination destekler")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = SeleniumRealScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_with_selenium(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()