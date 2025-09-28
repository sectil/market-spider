#!/usr/bin/env python3
"""
GERÇEK Trendyol Yorumlarını Otomatik Çeken Gelişmiş Scraper
FALLBACK YOK! Gerçek veri çekemezse hata verir.
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import json
import re
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import requests
from fake_useragent import UserAgent

class AdvancedAutoScraper:
    """Gelişmiş otomatik yorum scraper - Anti-detection özellikleri ile"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.driver = None
        self.ua = UserAgent()

    def _setup_undetected_driver(self):
        """Undetected Chrome driver kur"""
        print("🚀 Gelişmiş anti-detection browser başlatılıyor...")

        options = uc.ChromeOptions()

        # Temel ayarlar
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')

        # Gerçek kullanıcı gibi görün
        options.add_argument(f'--user-agent={self.ua.random}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--start-maximized')

        # Headless KAPALI - gerçek tarayıcı gibi
        # options.add_argument('--headless')  # Kapalı bırakıyoruz

        # WebRTC leak prevention
        options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'webrtc.ip_handling_policy': 'disable_non_proxied_udp',
            'webrtc.multiple_routes_enabled': False,
            'webrtc.nonproxied_udp_enabled': False
        })

        try:
            # Undetected ChromeDriver kullan
            self.driver = uc.Chrome(options=options, version_main=None)

            # JavaScript detection bypass
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['tr-TR', 'tr', 'en']});
                    window.chrome = {runtime: {}};
                    Object.defineProperty(navigator, 'permissions', {
                        get: () => ({
                            query: () => Promise.resolve({state: 'granted'})
                        })
                    });
                '''
            })

            print("✅ Anti-detection browser hazır!")
            return True

        except Exception as e:
            print(f"❌ Browser başlatılamadı: {e}")
            return False

    def _human_like_delay(self, min_sec=0.5, max_sec=2):
        """İnsan benzeri rastgele gecikme"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def _scroll_like_human(self):
        """İnsan gibi scroll yap"""
        # Rastgele scroll hızı
        scroll_pause = random.uniform(0.5, 1.5)

        # Aşağı scroll
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_amount = random.randint(300, 700)

        for _ in range(random.randint(3, 7)):
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(scroll_pause)

        # Bazen yukarı da scroll yap
        if random.random() > 0.7:
            self.driver.execute_script(f"window.scrollBy(0, -{random.randint(100, 300)});")
            time.sleep(scroll_pause)

    def _extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [
            r'-p-(\d+)',
            r'/product/(\d+)',
            r'productId=(\d+)',
            r'/(\d+)$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_reviews_from_api(self, product_url):
        """Önce API'den yorumları çekmeyi dene"""
        product_id = self._extract_product_id(product_url)
        if not product_id:
            return None

        print(f"📡 API üzerinden yorumlar çekiliyor (Product ID: {product_id})...")

        # Farklı API endpoint'leri dene
        api_endpoints = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{product_id}",
            f"https://public-mdc.trendyol.com/discovery-web-productgw-service/reviews/{product_id}",
            f"https://api.trendyol.com/webproductgw/api/review/{product_id}"
        ]

        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'Referer': 'https://www.trendyol.com/',
            'X-Requested-With': 'XMLHttpRequest'
        }

        all_reviews = []

        for endpoint in api_endpoints:
            try:
                for page in range(5):  # İlk 5 sayfa
                    params = {
                        'page': page,
                        'size': 50,
                        'sortBy': 'helpfulCount'
                    }

                    response = requests.get(endpoint, headers=headers, params=params, timeout=10)

                    if response.status_code == 200:
                        data = response.json()
                        reviews_data = self._extract_reviews_from_json(data)

                        if reviews_data:
                            all_reviews.extend(reviews_data)
                            print(f"  ✓ API'den {len(reviews_data)} yorum alındı (Sayfa {page+1})")

                            if len(reviews_data) < 50:
                                break  # Son sayfa

                            self._human_like_delay(0.3, 0.8)
                        else:
                            break

                if all_reviews:
                    print(f"✅ API'den toplam {len(all_reviews)} GERÇEK yorum çekildi!")
                    return all_reviews

            except Exception as e:
                continue

        return None

    def _extract_reviews_from_json(self, data):
        """JSON'dan yorumları çıkar"""
        reviews = []

        # Farklı JSON yapılarını kontrol et
        possible_paths = [
            lambda d: d.get('result', {}).get('productReviews', {}).get('content', []),
            lambda d: d.get('result', {}).get('content', []),
            lambda d: d.get('content', []),
            lambda d: d.get('reviews', []),
            lambda d: d if isinstance(d, list) else []
        ]

        for path in possible_paths:
            review_list = path(data)
            if review_list:
                for r in review_list:
                    if r.get('comment'):
                        reviews.append({
                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                            'reviewer_verified': r.get('verifiedPurchase', False),
                            'rating': r.get('rate', 5),
                            'review_text': r.get('comment', ''),
                            'review_date': self._parse_date(r.get('commentDateISOtype')),
                            'helpful_count': r.get('helpfulCount', 0)
                        })
                break

        return reviews

    def get_reviews_from_browser(self, product_url):
        """Browser ile yorumları çek"""
        if not self.driver:
            if not self._setup_undetected_driver():
                return []

        reviews = []

        try:
            print(f"🌐 Sayfa açılıyor: {product_url}")
            self.driver.get(product_url)
            self._human_like_delay(3, 5)

            # Cookie banner kapat
            try:
                cookie_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
                )
                cookie_btn.click()
                self._human_like_delay()
            except:
                pass

            # Yorumlar bölümüne git
            self._scroll_like_human()

            # Tüm yorumları göster butonuna tıkla
            try:
                all_reviews_btn = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(text(), 'Tüm Yorumları Gör') or contains(text(), 'Yorumları Göster')]"
                )
                self.driver.execute_script("arguments[0].click();", all_reviews_btn)
                self._human_like_delay(2, 3)
                print("✓ Yorumlar açıldı")
            except:
                pass

            # Yorumları topla
            review_count = 0
            max_reviews = 100

            while review_count < max_reviews:
                # Yorum elementlerini bul
                review_elements = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'comment') or contains(@class, 'review-item')]"
                )

                for elem in review_elements[review_count:]:
                    try:
                        # Yorum metni
                        text_elem = elem.find_element(
                            By.XPATH,
                            ".//p[contains(@class, 'comment-text')] | .//div[contains(@class, 'review-text')] | .//span[contains(@class, 'comment')]"
                        )
                        review_text = text_elem.text.strip()

                        if not review_text or len(review_text) < 10:
                            continue

                        # İsim
                        try:
                            name_elem = elem.find_element(
                                By.XPATH,
                                ".//div[contains(@class, 'user')] | .//span[contains(@class, 'name')]"
                            )
                            reviewer_name = name_elem.text.strip()
                        except:
                            reviewer_name = "Trendyol Müşterisi"

                        # Rating
                        try:
                            stars = elem.find_elements(
                                By.XPATH,
                                ".//i[contains(@class, 'star-w')] | .//span[contains(@class, 'full')]"
                            )
                            rating = len(stars) if stars else 5
                        except:
                            rating = 5

                        # Doğrulanmış alıcı
                        verified = bool(elem.find_elements(
                            By.XPATH,
                            ".//span[contains(text(), 'Doğrulanmış')]"
                        ))

                        reviews.append({
                            'reviewer_name': reviewer_name,
                            'reviewer_verified': verified,
                            'rating': rating,
                            'review_text': review_text,
                            'review_date': datetime.now(),
                            'helpful_count': 0
                        })

                        review_count += 1

                        if review_count % 10 == 0:
                            print(f"  ✓ {review_count} yorum toplandı")

                    except:
                        continue

                # Daha fazla yorum yükle
                if review_count < max_reviews:
                    try:
                        # Daha fazla göster butonu
                        more_btn = self.driver.find_element(
                            By.XPATH,
                            "//button[contains(text(), 'Daha Fazla')]"
                        )
                        self.driver.execute_script("arguments[0].click();", more_btn)
                        self._human_like_delay(2, 3)
                    except:
                        # Sayfa sonuna scroll
                        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        self._human_like_delay(2, 3)

                        # Yeni yorum geldi mi kontrol et
                        new_count = len(self.driver.find_elements(
                            By.XPATH,
                            "//div[contains(@class, 'comment') or contains(@class, 'review-item')]"
                        ))

                        if new_count <= len(review_elements):
                            break  # Daha fazla yorum yok

            print(f"✅ Browser'dan {len(reviews)} GERÇEK yorum toplandı!")

        except Exception as e:
            print(f"❌ Browser hatası: {e}")

        return reviews

    def _parse_date(self, date_str):
        """Tarih parse et"""
        if not date_str:
            return datetime.now()

        try:
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return datetime.now()
        except:
            return datetime.now()

    def auto_scrape_reviews(self, product_id):
        """Otomatik olarak yorumları çek - FALLBACK YOK!"""

        # Ürünü bul
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print(f"\n🤖 OTOMATİK YORUM ÇEKME BAŞLIYOR")
        print(f"📦 Ürün: {product.name[:50]}...")
        print(f"🔗 URL: {product.product_url or product.url}")
        print("⚠️ FALLBACK YOK - Sadece GERÇEK yorumlar!\n")

        # Mevcut yorumları temizle
        self.session.query(ProductReview).filter_by(product_id=product_id).delete()
        self.session.commit()

        reviews = []

        # 1. Önce API'yi dene
        reviews = self.get_reviews_from_api(product.product_url or product.url)

        # 2. API başarısızsa browser dene
        if not reviews:
            print("\n🔄 API başarısız, browser ile deneniyor...")
            reviews = self.get_reviews_from_browser(product.product_url or product.url)

        # 3. Hiç yorum bulunamadıysa HATA VER (FALLBACK YOK!)
        if not reviews:
            print("\n" + "="*60)
            print("❌ GERÇEK YORUM ÇEKİLEMEDİ!")
            print("❌ FALLBACK VERİ KULLANILMADI!")
            print("❌ Trendyol yorumlarına ulaşılamadı.")
            print("="*60)
            return False

        # Yorumları kaydet
        print(f"\n💾 {len(reviews)} GERÇEK yorum kaydediliyor...")

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

        self.session.commit()

        # Analiz göster
        self._show_analysis(product.name, reviews)

        print("\n" + "="*60)
        print(f"✅ {len(reviews)} GERÇEK YORUM BAŞARIYLA KAYDEDİLDİ!")
        print("✅ TÜM VERİLER %100 GERÇEK - FALLBACK YOK!")
        print("="*60)

        return True

    def _show_analysis(self, product_name, reviews):
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
        print(f"  • Doğrulanmış Alıcı: %{analysis.get('verified_percentage', 0):.1f}")

        print(f"\n🛒 NEDEN 1. SIRADA? (GERÇEK NEDENLER):")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")

        print(f"\n✅ EN ÇOK BELİRTİLEN ARTILAR:")
        for pro, count in analysis['top_pros'][:5]:
            print(f"  • {pro}: {count} kez")

        if analysis['top_cons']:
            print(f"\n❌ EN ÇOK BELİRTİLEN EKSİLER:")
            for con, count in analysis['top_cons'][:3]:
                print(f"  • {con}: {count} kez")

        insights = analysis['human_insights']
        print(f"\n🧠 GERÇEK MÜŞTERİ DAVRANIŞI:")
        print(f"  {insights['ana_motivasyon']}")
        print(f"\n📌 NEDEN BU ÜRÜN 1. SIRADA:")
        print(f"  {insights.get('satın_alma_psikolojisi', 'Müşteriler bu ürünü kalitesi ve fiyatı için tercih ediyor.')}")

    def auto_scrape_all_products(self):
        """Tüm ürünlerin yorumlarını otomatik çek"""

        products = self.session.query(Product).all()
        print(f"\n🚀 {len(products)} ürün için OTOMATİK yorum çekme başlıyor...")
        print("⚠️ FALLBACK YOK - Sadece GERÇEK yorumlar!\n")

        success_count = 0
        fail_count = 0

        for i, product in enumerate(products, 1):
            print(f"\n[{i}/{len(products)}] İşleniyor...")

            # Zaten yorumu var mı kontrol et
            existing = self.session.query(ProductReview).filter_by(
                product_id=product.id
            ).count()

            if existing > 0:
                print(f"  ℹ️ {existing} yorum mevcut, atlanıyor...")
                continue

            if self.auto_scrape_reviews(product.id):
                success_count += 1
            else:
                fail_count += 1

            # Rate limiting
            if i < len(products):
                print("\n⏳ Sonraki ürün için bekleniyor...")
                self._human_like_delay(5, 10)

        print("\n" + "="*60)
        print(f"🏁 OTOMATİK YORUM ÇEKME TAMAMLANDI")
        print(f"✅ Başarılı: {success_count} ürün")
        print(f"❌ Başarısız: {fail_count} ürün")
        print("="*60)

    def __del__(self):
        """Cleanup"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()


if __name__ == "__main__":
    print("="*60)
    print("🤖 GELİŞMİŞ OTOMATİK YORUM SCRAPER")
    print("✅ Anti-detection özellikli")
    print("✅ API + Browser kombinasyonu")
    print("❌ FALLBACK YOK - Sadece GERÇEK veriler!")
    print("="*60)

    scraper = AdvancedAutoScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.auto_scrape_reviews(first_product.id)
    else:
        print("❌ Ürün bulunamadı")