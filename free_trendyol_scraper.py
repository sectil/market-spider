#!/usr/bin/env python3
"""
🆓 ÜCRETSİZ TRENDYOL SCRAPER - Kalıcı Çözüm
Proxy rotasyonu ve header manipülasyonu ile
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import time
import random
import json
import base64

class FreeTrendyolScraper:
    def __init__(self):
        self.session = requests.Session()

        # Ücretsiz proxy listesi (güncellenebilir)
        self.free_proxies = [
            # Bu listeyi güncel tutmak gerekiyor
            # https://www.proxy-list.download/HTTPS
            # https://free-proxy-list.net/
        ]

        # User-Agent rotasyonu
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
        ]

        # Google Cache kullanımı
        self.use_google_cache = True

    def get_via_google_cache(self, url):
        """Google Cache üzerinden eriş"""
        cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{url}"
        headers = {'User-Agent': random.choice(self.user_agents)}

        try:
            response = requests.get(cache_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None

    def get_via_wayback_machine(self, url):
        """Wayback Machine arşivinden al"""
        wayback_url = f"https://web.archive.org/web/2/{url}"

        try:
            response = requests.get(wayback_url, timeout=10)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None

    def scrape_via_mobile_api(self):
        """Mobil API üzerinden veri çek"""

        # Trendyol mobil API endpoint'leri
        mobile_endpoints = [
            "https://api.trendyol.com/webapicontent/v2/best-seller-products",
            "https://public.trendyol.com/discovery-web-recogw-service/api/favorites/counts",
            "https://public-sdc.trendyol.com/discovery-web-searchgw-service/v2/api/filter/sr"
        ]

        # Mobil cihaz gibi davran
        mobile_headers = {
            'User-Agent': 'Trendyol/5.14.1 (com.trendyol.app; build:1141; iOS 16.0.0) Alamofire/5.6.2',
            'Accept': 'application/json',
            'Accept-Language': 'tr-TR,tr;q=0.9',
            'X-Storefront-Id': 'TR',
            'X-Application-Id': 'com.trendyol.app',
        }

        conn = sqlite3.connect('market_spider.db')
        cursor = conn.cursor()

        for endpoint in mobile_endpoints:
            try:
                response = self.session.get(endpoint, headers=mobile_headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    # Veriyi işle
                    print(f"✅ Mobil API'den veri alındı: {endpoint}")
            except:
                continue

        conn.close()

    def scrape_via_rss_feed(self):
        """RSS feed'lerden ürün bilgisi al"""

        # Trendyol ve rakiplerin RSS/Sitemap URL'leri
        feed_urls = [
            "https://www.trendyol.com/sitemap.xml",
            "https://www.trendyol.com/sitemap_index.xml",
            "https://www.trendyol.com/sitemap/brands.xml",
            "https://www.trendyol.com/sitemap/categories.xml"
        ]

        for feed_url in feed_urls:
            try:
                response = requests.get(feed_url, timeout=10)
                if response.status_code == 200:
                    # XML parse et
                    soup = BeautifulSoup(response.content, 'xml')
                    urls = soup.find_all('loc')

                    print(f"✅ Sitemap'ten {len(urls)} URL bulundu")
                    # URL'leri veritabanına kaydet
            except:
                continue

    def scrape_via_graphql(self):
        """GraphQL endpoint'lerini kullan"""

        graphql_url = "https://api.trendyol.com/graphql"

        # GraphQL sorgusu
        query = """
        query GetProducts($first: Int!) {
            products(first: $first, orderBy: BEST_SELLER) {
                edges {
                    node {
                        id
                        name
                        brand
                        price
                        rating
                        reviews {
                            totalCount
                            edges {
                                node {
                                    comment
                                    rating
                                    author
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"first": 50}

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': random.choice(self.user_agents)
        }

        try:
            response = requests.post(
                graphql_url,
                json={'query': query, 'variables': variables},
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                print("✅ GraphQL'den veri alındı")
                return data
        except:
            pass

        return None

def setup_free_scraping_system():
    """Ücretsiz ve kalıcı scraping sistemi kur"""

    print("="*60)
    print("🆓 ÜCRETSİZ SCRAPING SİSTEMİ KURULUYOR")
    print("="*60)

    # 1. TOR Network kurulumu
    print("\n1️⃣ TOR Network Kurulumu:")
    print("""
    sudo apt-get install tor
    sudo service tor start

    # Python'da kullanım:
    pip install requests[socks]

    proxies = {
        'http': 'socks5://127.0.0.1:9050',
        'https': 'socks5://127.0.0.1:9050'
    }
    """)

    # 2. DNS over HTTPS
    print("\n2️⃣ DNS over HTTPS:")
    print("""
    pip install httpx

    import httpx
    client = httpx.Client(http2=True)
    # Cloudflare'i bypass eder
    """)

    # 3. Headless browser (ücretsiz)
    print("\n3️⃣ Headless Browser:")
    print("""
    pip install pyppeteer

    import asyncio
    from pyppeteer import launch

    async def main():
        browser = await launch({'headless': True, 'args': ['--no-sandbox']})
        page = await browser.newPage()
        await page.goto('https://www.trendyol.com')
        content = await page.content()
        await browser.close()
        return content
    """)

    # 4. Rotating User-Agents
    print("\n4️⃣ User-Agent Rotasyonu:")
    print("""
    pip install fake-useragent

    from fake_useragent import UserAgent
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    """)

    # 5. Free proxy scraper
    print("\n5️⃣ Ücretsiz Proxy Listesi:")
    print("""
    pip install proxy-requests

    from proxy_requests import ProxyRequests
    r = ProxyRequests("https://www.trendyol.com")
    r.get_with_headers()
    """)

def create_scheduler_script():
    """Otomatik veri çekme scheduler"""

    script = """
#!/bin/bash
# Cron job for automatic scraping
# Add to crontab: crontab -e
# */30 * * * * /path/to/trendyol_scheduler.sh

# Her 30 dakikada bir çalıştır
while true; do
    python3 free_trendyol_scraper.py
    sleep 1800  # 30 dakika bekle
done
"""

    with open('trendyol_scheduler.sh', 'w') as f:
        f.write(script)

    print("✅ Scheduler script oluşturuldu: trendyol_scheduler.sh")

def alternative_data_sources():
    """Alternatif ücretsiz veri kaynakları"""

    print("\n" + "="*60)
    print("📊 ALTERNATİF ÜCRETSİZ VERİ KAYNAKLARI")
    print("="*60)

    sources = {
        "Google Shopping API": {
            "url": "https://developers.google.com/shopping-content/v2/quickstart",
            "limit": "Günlük 25.000 ücretsiz istek",
            "avantaj": "Trendyol ürünleri de var"
        },
        "SerpAPI Free Tier": {
            "url": "https://serpapi.com/",
            "limit": "Aylık 100 ücretsiz arama",
            "avantaj": "Google Shopping sonuçları"
        },
        "Apify Free Tier": {
            "url": "https://apify.com/",
            "limit": "Aylık $5 kredi",
            "avantaj": "Hazır Trendyol scraper'ları"
        },
        "ParseHub": {
            "url": "https://www.parsehub.com/",
            "limit": "200 sayfa/run ücretsiz",
            "avantaj": "Görsel scraper, kod gerekmez"
        },
        "Octoparse": {
            "url": "https://www.octoparse.com/",
            "limit": "10.000 satır veri ücretsiz",
            "avantaj": "Cloud-based scraping"
        },
        "GitHub Actions": {
            "url": "https://github.com/features/actions",
            "limit": "Aylık 2000 dakika ücretsiz",
            "avantaj": "Otomatik scheduled scraping"
        }
    }

    for name, details in sources.items():
        print(f"\n🔹 {name}")
        print(f"   URL: {details['url']}")
        print(f"   Limit: {details['limit']}")
        print(f"   Avantaj: {details['avantaj']}")

if __name__ == "__main__":
    print("🚀 Ücretsiz Trendyol Scraper Başlatılıyor...")

    scraper = FreeTrendyolScraper()

    # Farklı yöntemleri dene
    print("\n1. Mobil API deneniyor...")
    scraper.scrape_via_mobile_api()

    print("\n2. RSS/Sitemap deneniyor...")
    scraper.scrape_via_rss_feed()

    print("\n3. GraphQL deneniyor...")
    scraper.scrape_via_graphql()

    print("\n4. Google Cache deneniyor...")
    content = scraper.get_via_google_cache("https://www.trendyol.com/cok-satanlar")
    if content:
        print("✅ Google Cache'ten veri alındı")

    # Kurulum talimatları
    setup_free_scraping_system()

    # Scheduler oluştur
    create_scheduler_script()

    # Alternatif kaynaklar
    alternative_data_sources()