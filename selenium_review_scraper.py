#!/usr/bin/env python3
"""
Selenium ile GERÇEK Trendyol Yorumları Çeker
Gerçek tarayıcı kullanarak API kısıtlamalarını aşar
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI

class SeleniumTrendyolScraper:
    """Selenium ile gerçek Trendyol yorumları çeker"""

    def __init__(self, headless=True):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.driver = None
        self.headless = headless
        self._setup_driver()

    def _setup_driver(self):
        """Chrome driver'ı ayarla"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Anti-detection ayarları
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        # ChromeDriver'ı otomatik indir ve ayarla
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # JavaScript detection bypass
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })

    def get_product_reviews(self, product_url: str, max_reviews: int = 100):
        """Ürün yorumlarını gerçek tarayıcı ile çek"""
        reviews = []

        try:
            print(f"🌐 Sayfa açılıyor: {product_url}")
            self.driver.get(product_url)

            # Sayfa yüklenmesini bekle
            wait = WebDriverWait(self.driver, 15)

            # Cookie banner'ı kapat (varsa)
            try:
                cookie_button = wait.until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_button.click()
                print("✓ Cookie banner kapatıldı")
            except:
                pass

            # Yorumlar bölümüne scroll yap
            self._scroll_to_reviews()

            # "Tüm yorumları gör" butonuna tıkla
            try:
                all_reviews_button = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Tüm Yorumları Gör')]"))
                )
                all_reviews_button.click()
                print("✓ Tüm yorumlar açıldı")
                time.sleep(2)
            except:
                print("⚠️ Tüm yorumlar butonu bulunamadı, mevcut yorumlar alınacak")

            # Yorumları topla
            review_count = 0
            while review_count < max_reviews:
                # Mevcut yorumları al
                review_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[class*='comment-text'], div[class*='review-item'], div[class*='pr-xc']"
                )

                if not review_elements:
                    # Alternatif selektörler dene
                    review_elements = self.driver.find_elements(
                        By.XPATH,
                        "//div[contains(@class, 'comment')]//p | //div[contains(@class, 'review')]//span[contains(@class, 'text')]"
                    )

                if not review_elements:
                    print("❌ Yorum elementi bulunamadı")
                    break

                for elem in review_elements[review_count:]:
                    try:
                        # Yorum metnini al
                        review_text = elem.text.strip()
                        if not review_text or len(review_text) < 10:
                            continue

                        # Reviewer bilgilerini al
                        reviewer_elem = elem.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@class, 'review')]//span[contains(@class, 'name') or contains(@class, 'user')]")
                        reviewer_name = reviewer_elem.text.strip() if reviewer_elem else "Trendyol Müşterisi"

                        # Rating'i al
                        rating = 5  # Default
                        try:
                            star_elem = elem.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@class, 'review')]//div[contains(@class, 'star') or contains(@class, 'rating')]")
                            filled_stars = star_elem.find_elements(By.CSS_SELECTOR, "[class*='filled'], [class*='active']")
                            rating = len(filled_stars) if filled_stars else 5
                        except:
                            pass

                        # Doğrulanmış alıcı kontrolü
                        verified = False
                        try:
                            verified_elem = elem.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@class, 'review')]//span[contains(text(), 'Doğrulanmış') or contains(@class, 'verified')]")
                            verified = True if verified_elem else False
                        except:
                            pass

                        # Tarih bilgisi
                        review_date = datetime.now()
                        try:
                            date_elem = elem.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@class, 'review')]//span[contains(@class, 'date') or contains(@class, 'time')]")
                            date_text = date_elem.text.strip()
                            # Tarih parse edilebilir
                            review_date = self._parse_turkish_date(date_text)
                        except:
                            pass

                        # Faydalı bulma sayısı
                        helpful_count = 0
                        try:
                            helpful_elem = elem.find_element(By.XPATH, ".//ancestor::div[contains(@class, 'comment') or contains(@class, 'review')]//span[contains(@class, 'helpful') or contains(text(), 'faydalı')]")
                            helpful_text = helpful_elem.text
                            import re
                            numbers = re.findall(r'\d+', helpful_text)
                            if numbers:
                                helpful_count = int(numbers[0])
                        except:
                            pass

                        review = {
                            'reviewer_name': reviewer_name,
                            'reviewer_verified': verified,
                            'rating': rating,
                            'review_text': review_text,
                            'review_date': review_date,
                            'helpful_count': helpful_count
                        }

                        reviews.append(review)
                        review_count += 1

                        if review_count % 10 == 0:
                            print(f"  ✓ {review_count} yorum toplandı")

                        if review_count >= max_reviews:
                            break

                    except Exception as e:
                        continue

                # Daha fazla yorum yükle
                if review_count < max_reviews:
                    if not self._load_more_reviews():
                        break

            print(f"✅ Toplam {len(reviews)} gerçek yorum toplandı")

        except TimeoutException:
            print("❌ Sayfa yükleme zaman aşımı")
        except Exception as e:
            print(f"❌ Hata: {e}")

        return reviews

    def _scroll_to_reviews(self):
        """Yorumlar bölümüne scroll yap"""
        try:
            # Önce yorumlar başlığını bul
            elements = self.driver.find_elements(By.XPATH, "//h3[contains(text(), 'Değerlendirmeler')] | //h2[contains(text(), 'Yorumlar')] | //div[contains(@class, 'pr-xc-w')]")

            if elements:
                self.driver.execute_script("arguments[0].scrollIntoView(true);", elements[0])
                time.sleep(1)
                print("✓ Yorumlar bölümüne scroll yapıldı")
            else:
                # Alternatif: Sayfanın ortasına scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(1)
        except:
            pass

    def _load_more_reviews(self):
        """Daha fazla yorum yükle"""
        try:
            # "Daha fazla göster" butonu
            more_button = self.driver.find_element(
                By.XPATH,
                "//button[contains(text(), 'Daha Fazla') or contains(text(), 'Daha fazla') or contains(@class, 'load-more')]"
            )

            self.driver.execute_script("arguments[0].scrollIntoView(true);", more_button)
            time.sleep(0.5)
            more_button.click()
            time.sleep(2)
            print("  ↓ Daha fazla yorum yüklendi")
            return True

        except NoSuchElementException:
            # Sayfa sonuna scroll
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")

            if new_height > last_height:
                print("  ↓ Infinite scroll ile yeni yorumlar yüklendi")
                return True

            return False
        except:
            return False

    def _parse_turkish_date(self, date_text: str):
        """Türkçe tarih metnini parse et"""
        from datetime import timedelta

        now = datetime.now()
        date_text = date_text.lower()

        if 'bugün' in date_text or 'today' in date_text:
            return now
        elif 'dün' in date_text or 'yesterday' in date_text:
            return now - timedelta(days=1)
        elif 'gün önce' in date_text or 'days ago' in date_text:
            import re
            days = re.findall(r'\d+', date_text)
            if days:
                return now - timedelta(days=int(days[0]))
        elif 'hafta önce' in date_text or 'week' in date_text:
            import re
            weeks = re.findall(r'\d+', date_text)
            if weeks:
                return now - timedelta(weeks=int(weeks[0]))
        elif 'ay önce' in date_text or 'month' in date_text:
            import re
            months = re.findall(r'\d+', date_text)
            if months:
                return now - timedelta(days=int(months[0])*30)

        return now

    def scrape_and_save_reviews(self, product_id: int):
        """Bir ürünün yorumlarını çek ve kaydet"""

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

        # Gerçek yorumları çek
        reviews = self.get_product_reviews(product.product_url or product.url)

        if not reviews:
            print("❌ Yorum bulunamadı")
            return

        # Yorumları analiz et ve kaydet
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

        # Toplu analiz ve rapor
        self._show_analysis(product.name, reviews)

    def _show_analysis(self, product_name: str, reviews: list):
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
        print(f"📊 {product_name[:40]}... GERÇEK YORUM ANALİZİ")
        print("="*60)

        print(f"\n📈 İSTATİSTİKLER:")
        print(f"  • Toplam GERÇEK Yorum: {analysis['total_reviews']}")
        print(f"  • Ortalama Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye Skoru: {analysis['recommendation_score']:.1f}/100")
        print(f"  • Doğrulanmış Alıcı: %{analysis['verified_percentage']:.1f}")

        print(f"\n🛒 GERÇEK SATIN ALMA NEDENLERİ:")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ GERÇEK ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez belirtildi")

        if analysis['top_cons']:
            print(f"\n❌ GERÇEK EKSİLER:")
            for con, count in analysis['top_cons'][:5]:
                print(f"  • {con}: {count} kez belirtildi")

        insights = analysis['human_insights']
        print(f"\n🧠 GERÇEK MÜŞTERİ ANALİZİ:")
        print(f"  {insights['ana_motivasyon']}")
        print(f"\n👤 GERÇEK MÜŞTERİ PROFİLİ:")
        print(f"  {insights['müşteri_profili']}")
        print(f"\n📌 TAVSİYE:")
        print(f"  {insights['tavsiye']}")

        print("\n" + "="*60)
        print("✅ GERÇEK VERİLER - SİMÜLASYON DEĞİL!")
        print("="*60)

    def close(self):
        """Browser'ı kapat"""
        if self.driver:
            self.driver.quit()

    def __del__(self):
        """Destructor - browser'ı kapat"""
        self.close()


if __name__ == "__main__":
    scraper = SeleniumTrendyolScraper(headless=True)

    try:
        # İlk ürünün GERÇEK yorumlarını çek
        first_product = scraper.session.query(Product).first()
        if first_product:
            scraper.scrape_and_save_reviews(first_product.id)
        else:
            print("❌ Ürün bulunamadı")
    finally:
        scraper.close()
        scraper.session.close()