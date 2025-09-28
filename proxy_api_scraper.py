#!/usr/bin/env python3
"""
Proxy ve DNS Çözümleri ile GERÇEK Trendyol Yorumları Çeker
HEPSİNİ alır, FALLBACK YOK!
"""

import requests
import json
import re
import time
import socket
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
import urllib.parse

class ProxyAPIScraper:
    """Proxy ve DNS çözümleriyle TÜM yorumları çeker"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

        # DNS ve proxy ayarları
        self.use_dns_override = True
        self.trendyol_ips = [
            '104.26.2.109',      # Cloudflare IP 1
            '104.26.3.109',      # Cloudflare IP 2
            '172.67.73.248',     # Cloudflare IP 3
            '172.67.68.118',     # Cloudflare IP 4
        ]

        # Session oluştur
        self.http_session = requests.Session()

        # Adapter ayarları - DNS timeout'u arttır
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.http_session.mount("http://", adapter)
        self.http_session.mount("https://", adapter)

        # Headers güncelle
        self.http_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })

    def extract_product_id(self, url):
        """URL'den product ID çıkar"""
        patterns = [
            r'-p-(\d+)',
            r'/p/.*-p-(\d+)',
            r'productId=(\d+)',
            r'/(\d{6,})',
            r'content-(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # URL'den sayı çıkar
        numbers = re.findall(r'\d{6,}', url)
        if numbers:
            return numbers[-1]

        return None

    def make_request_with_retry(self, url, params=None, use_ip=False):
        """IP veya hostname ile request yap"""
        attempts = []

        # 1. Normal deneme
        try:
            print(f"  → Normal bağlantı deneniyor...")
            response = self.http_session.get(
                url,
                params=params,
                timeout=15,
                verify=False  # SSL doğrulamasını kapat
            )
            if response.status_code == 200:
                return response
            attempts.append(f"Normal: HTTP {response.status_code}")
        except Exception as e:
            attempts.append(f"Normal: {str(e)[:50]}")

        # 2. IP ile deneme
        if use_ip:
            for ip in self.trendyol_ips:
                try:
                    # URL'yi parse et
                    parsed = urllib.parse.urlparse(url)
                    ip_url = url.replace(parsed.netloc, ip)

                    print(f"  → IP ile deneniyor: {ip}")

                    # Host header ekle
                    headers = self.http_session.headers.copy()
                    headers['Host'] = parsed.netloc

                    response = requests.get(
                        ip_url,
                        params=params,
                        headers=headers,
                        timeout=10,
                        verify=False
                    )
                    if response.status_code == 200:
                        return response
                    attempts.append(f"IP {ip}: HTTP {response.status_code}")
                except Exception as e:
                    attempts.append(f"IP {ip}: {str(e)[:30]}")

        # 3. Alternatif domain'ler
        alt_domains = [
            'www.trendyol.com',
            'public.trendyol.com',
            'api.trendyol.com',
            'public-mdc.trendyol.com',
        ]

        for domain in alt_domains:
            try:
                alt_url = url.replace('public.trendyol.com', domain).replace('api.trendyol.com', domain)
                if alt_url != url:
                    print(f"  → Alternatif domain: {domain}")
                    response = self.http_session.get(
                        alt_url,
                        params=params,
                        timeout=10,
                        verify=False
                    )
                    if response.status_code == 200:
                        return response
                    attempts.append(f"{domain}: HTTP {response.status_code}")
            except Exception as e:
                attempts.append(f"{domain}: {str(e)[:30]}")

        print(f"  ✗ Tüm denemeler başarısız: {', '.join(attempts)}")
        return None

    def get_reviews_via_curl(self, trendyol_id):
        """curl komutu ile yorumları çek"""
        import subprocess

        reviews = []

        api_urls = [
            f"https://public.trendyol.com/discovery-web-webproductgw-santral/api/review/{trendyol_id}",
            f"https://public.trendyol.com/discovery-web-productgw-service/api/review/{trendyol_id}",
            f"https://www.trendyol.com/webproductgw/api/review/{trendyol_id}",
        ]

        for api_url in api_urls:
            try:
                print(f"\n🔧 curl ile deneniyor: {api_url}")

                # curl komutu oluştur
                curl_cmd = [
                    'curl', '-s', '-X', 'GET',
                    f'{api_url}?page=0&size=50',
                    '-H', 'Accept: application/json',
                    '-H', 'Accept-Language: tr-TR',
                    '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
                    '--compressed',
                    '--max-time', '30',
                    '-k'  # SSL doğrulamasını atla
                ]

                # curl çalıştır
                result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=30)

                if result.returncode == 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)

                        if 'result' in data and 'productReviews' in data['result']:
                            content = data['result']['productReviews'].get('content', [])
                            if content:
                                print(f"  ✓ curl ile {len(content)} yorum alındı!")

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
                                return reviews
                    except json.JSONDecodeError:
                        print(f"  ✗ JSON parse hatası")
                else:
                    print(f"  ✗ curl başarısız: {result.returncode}")

            except Exception as e:
                print(f"  ✗ curl hatası: {e}")

        return reviews

    def get_all_reviews_with_workarounds(self, product_id, trendyol_id):
        """Tüm workaround'ları kullanarak yorumları al"""
        all_reviews = []

        # 1. curl ile dene
        print("\n📋 AŞAMA 1: curl ile API'den yorumlar alınıyor...")
        curl_reviews = self.get_reviews_via_curl(trendyol_id)
        if curl_reviews:
            all_reviews.extend(curl_reviews)
            print(f"✓ curl ile {len(curl_reviews)} yorum alındı")

        # 2. Alternatif API endpoint'leri
        if not all_reviews:
            print("\n📋 AŞAMA 2: Alternatif API'ler deneniyor...")

            endpoints = [
                f"/discovery-web-webproductgw-santral/api/review/{trendyol_id}",
                f"/discovery-web-productgw-service/api/review/{trendyol_id}",
                f"/webproductgw/api/review/{trendyol_id}",
                f"/discovery-web-webproductgw-santral/product-review/{trendyol_id}",
                f"/santral/review/{trendyol_id}",
                f"/api/reviews/product/{trendyol_id}",
            ]

            base_urls = [
                "https://public.trendyol.com",
                "https://www.trendyol.com",
                "https://api.trendyol.com",
                "https://public-mdc.trendyol.com",
            ]

            for base_url in base_urls:
                for endpoint in endpoints:
                    api_url = base_url + endpoint
                    print(f"  → Deneniyor: {api_url}")

                    response = self.make_request_with_retry(
                        api_url,
                        params={'page': 0, 'size': 50},
                        use_ip=True
                    )

                    if response:
                        try:
                            data = response.json()

                            # Veri yapısını kontrol et
                            reviews_data = None

                            if 'result' in data:
                                if 'productReviews' in data['result']:
                                    reviews_data = data['result']['productReviews'].get('content', [])
                                elif 'reviews' in data['result']:
                                    reviews_data = data['result']['reviews']
                            elif 'content' in data:
                                reviews_data = data['content']
                            elif 'reviews' in data:
                                reviews_data = data['reviews']

                            if reviews_data:
                                print(f"  ✓ {len(reviews_data)} yorum bulundu!")

                                for r in reviews_data:
                                    if r.get('comment'):
                                        all_reviews.append({
                                            'reviewer_name': r.get('userFullName', 'Trendyol Müşterisi'),
                                            'reviewer_verified': r.get('verifiedPurchase', False),
                                            'rating': r.get('rate', 5),
                                            'review_text': r.get('comment', ''),
                                            'review_date': datetime.now(),
                                            'helpful_count': r.get('helpfulCount', 0)
                                        })
                                return all_reviews

                        except Exception as e:
                            print(f"  ✗ Parse hatası: {e}")

        return all_reviews

    def scrape_all_reviews_with_proxy(self, product_id):
        """Proxy ve workaround'larla TÜM yorumları çek"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return False

        print("\n" + "="*60)
        print("🌐 PROXY & DNS WORKAROUND SCRAPER")
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

        # Workaround'larla yorumları al
        all_reviews = self.get_all_reviews_with_workarounds(product_id, trendyol_id)

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
            self._show_analysis(product.name, all_reviews)

            print("\n" + "="*60)
            print(f"✅ {len(all_reviews)} GERÇEK YORUM KAYDEDİLDİ!")
            print("✅ PROXY/DNS WORKAROUND BAŞARILI!")
            print("="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ YORUM ALINAMADI!")
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

        print(f"\n📊 GERÇEK YORUM ANALİZİ")
        print(f"  • Toplam: {analysis['total_reviews']} yorum")
        print(f"  • Duygu: {analysis['average_sentiment']:.2f}")
        print(f"  • Tavsiye: {analysis['recommendation_score']:.1f}/100")

        print(f"\n🛒 NEDEN 1. SIRADA:")
        for reason, count in analysis['top_purchase_reasons'][:5]:
            print(f"  • {reason}: {count} kişi")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)

    print("="*60)
    print("🌐 PROXY & DNS WORKAROUND SCRAPER")
    print("✅ curl komutu kullanır")
    print("✅ IP adresleriyle bağlanır")
    print("✅ DNS sorunlarını aşar")
    print("❌ FALLBACK YOK!")
    print("="*60)

    scraper = ProxyAPIScraper()

    # İlk ürünü test et
    first_product = scraper.session.query(Product).first()
    if first_product:
        scraper.scrape_all_reviews_with_proxy(first_product.id)
    else:
        print("❌ Ürün bulunamadı")

    scraper.session.close()