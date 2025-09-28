#!/usr/bin/env python3
"""
Otomatik Örümcek - Siteyi gezer ve kategorileri kendisi bulur
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import time
from typing import List, Dict, Set
import cloudscraper
from collections import defaultdict


class AutoSpider:
    """Otomatik kategori ve ürün bulucu örümcek"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.visited_urls = set()
        self.discovered_categories = []
        self.best_seller_patterns = []
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        }

    def crawl_site(self, base_url: str, max_depth: int = 2) -> Dict:
        """Siteyi gez ve kategorileri otomatik bul"""

        self.base_url = base_url
        self.domain = urlparse(base_url).netloc

        print(f"🕷️ Örümcek {base_url} sitesini tarıyor...")

        # 1. Ana sayfayı ziyaret et
        main_categories = self._crawl_page(base_url, depth=0, max_depth=max_depth)

        # 2. En çok satan pattern'leri bul
        self.best_seller_patterns = self._find_best_seller_patterns(base_url)

        # 3. Kategori sayfalarını tespit et
        category_urls = self._identify_category_pages(base_url)

        # 4. Her kategori için en çok satanlar URL'sini oluştur
        categories_with_bestsellers = []

        for cat_url in category_urls[:30]:  # İlk 30 kategori
            cat_info = self._analyze_category_page(cat_url)
            if cat_info:
                categories_with_bestsellers.append(cat_info)

        return {
            'site': self.domain,
            'base_url': base_url,
            'categories': categories_with_bestsellers,
            'total': len(categories_with_bestsellers),
            'best_seller_patterns': self.best_seller_patterns
        }

    def _crawl_page(self, url: str, depth: int = 0, max_depth: int = 2) -> List[str]:
        """Bir sayfayı ziyaret et ve linkleri topla"""

        if depth > max_depth or url in self.visited_urls:
            return []

        self.visited_urls.add(url)
        found_urls = []

        try:
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Tüm linkleri bul
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                full_url = urljoin(url, href)

                # Aynı domain'de mi?
                if urlparse(full_url).netloc == self.domain:
                    found_urls.append(full_url)

                    # Kategori pattern'leri ara
                    if self._is_category_url(full_url):
                        self.discovered_categories.append({
                            'url': full_url,
                            'text': link.get_text(strip=True),
                            'depth': depth
                        })

        except Exception as e:
            print(f"❌ Sayfa ziyaret edilemedi {url}: {e}")

        return found_urls

    def _find_best_seller_patterns(self, base_url: str) -> List[Dict]:
        """En çok satan ürünler için URL pattern'lerini bul"""

        patterns = []

        # Bilinen pattern'ler
        common_patterns = [
            {'param': 'sort', 'values': ['best-selling', 'bestseller', 'most-sold', 'popular']},
            {'param': 'siralama', 'values': ['coksatan', 'cok-satan', 'ensatan']},
            {'param': 'srt', 'values': ['SALES', 'BESTSELLER', 'POPULAR']},
            {'param': 'sst', 'values': ['BEST_SELLER', 'MOST_SOLD']},
            {'param': 'orderby', 'values': ['sales', 'popularity', 'bestsellers']},
            {'param': 'filter', 'values': ['bestseller', 'topselling', 'popular']}
        ]

        # Site spesifik pattern'leri tespit et
        try:
            response = self.scraper.get(base_url, headers=self.headers, timeout=10)
            text = response.text.lower()

            # URL'lerde pattern ara
            for pattern in common_patterns:
                for value in pattern['values']:
                    if f"{pattern['param']}={value}" in text or f"{pattern['param']}:{value}" in text:
                        patterns.append({
                            'param': pattern['param'],
                            'value': value,
                            'found': True
                        })

            # Link metinlerinde ipucu ara
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                link_text = link.get_text(strip=True).lower()
                link_href = link.get('href', '').lower()

                if any(word in link_text for word in ['çok satan', 'best seller', 'popular', 'top']):
                    # URL'den parametreyi çıkar
                    if '?' in link_href:
                        params = link_href.split('?')[1]
                        patterns.append({
                            'url_sample': link_href,
                            'text': link_text,
                            'params': params
                        })

        except Exception as e:
            print(f"Pattern bulunamadı: {e}")

        return patterns

    def _identify_category_pages(self, base_url: str) -> List[str]:
        """Kategori sayfalarını tespit et"""

        category_urls = set()

        try:
            response = self.scraper.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Menü ve navigasyon elemanlarını bul
            nav_elements = soup.select('nav a, .menu a, .categories a, .category-list a, [class*="menu"] a, [class*="category"] a')

            for elem in nav_elements:
                href = elem.get('href', '')
                if href and not href.startswith('#'):
                    full_url = urljoin(base_url, href)

                    # Kategori URL pattern'leri
                    category_patterns = [
                        r'/kategori/',
                        r'/category/',
                        r'/c/',
                        r'/k/',
                        r'/butik/',
                        r'/liste/',
                        r'/shop/',
                        r'/collections/',
                        r'/departments/'
                    ]

                    # Pattern kontrolü
                    if any(pattern in full_url.lower() for pattern in category_patterns):
                        category_urls.add(full_url)

                    # Veya link metninde kategori belirteci var mı?
                    link_text = elem.get_text(strip=True).lower()
                    if len(link_text) > 2 and not any(skip in link_text for skip in ['giriş', 'login', 'sepet', 'cart']):
                        # Muhtemelen bir kategori
                        category_urls.add(full_url)

        except Exception as e:
            print(f"Kategori tespiti hatası: {e}")

        return list(category_urls)

    def _analyze_category_page(self, url: str) -> Dict:
        """Kategori sayfasını analiz et"""

        try:
            response = self.scraper.get(url, headers=self.headers, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Sayfa başlığını al
            title = soup.find('title')
            category_name = title.text.strip() if title else self._extract_name_from_url(url)

            # Ürün var mı kontrol et
            product_indicators = soup.select('.product, .item, .product-card, [class*="product"], [class*="item"]')

            if len(product_indicators) > 0:
                # Bu bir kategori sayfası

                # En çok satan URL'sini oluştur
                best_seller_url = self._create_best_seller_url(url)

                return {
                    'id': self._create_category_id(url),
                    'name': category_name[:100],
                    'url': url,
                    'best_sellers_url': best_seller_url,
                    'product_count': len(product_indicators),
                    'source': 'auto_discovered'
                }

        except Exception as e:
            pass

        return None

    def _create_best_seller_url(self, category_url: str) -> str:
        """Kategori için en çok satanlar URL'sini oluştur"""

        # Site spesifik pattern'ler
        if 'trendyol' in self.domain:
            if '?' in category_url:
                return f"{category_url}&sst=BEST_SELLER"
            return f"{category_url}?sst=BEST_SELLER"

        elif 'hepsiburada' in self.domain:
            if '?' in category_url:
                return f"{category_url}&siralama=coksatan"
            return f"{category_url}?siralama=coksatan"

        elif 'n11' in self.domain:
            if '?' in category_url:
                return f"{category_url}&srt=SALES"
            return f"{category_url}?srt=SALES"

        elif 'gittigidiyor' in self.domain:
            if '?' in category_url:
                return f"{category_url}&sira=satissayisi"
            return f"{category_url}?sira=satissayisi"

        else:
            # Genel pattern
            if '?' in category_url:
                return f"{category_url}&sort=bestseller"
            return f"{category_url}?sort=bestseller"

    def _is_category_url(self, url: str) -> bool:
        """URL'nin kategori sayfası olup olmadığını kontrol et"""

        # Kategori belirteçleri
        category_indicators = [
            '/kategori/', '/category/', '/c/', '/k/',
            '/shop/', '/collections/', '/departments/',
            '/liste/', '/butik/'
        ]

        # İstenmeyen URL'ler
        skip_patterns = [
            'login', 'register', 'cart', 'checkout',
            'account', 'wishlist', 'compare', 'help',
            '.jpg', '.png', '.css', '.js', '#',
            'iletisim', 'contact', 'about', 'meet-us',
            'yardim', 'support', 'faq', 'kampanya',
            'campaign', 'deal', 'privacy', 'terms',
            'blog', 'press', 'career', 'seller',
            'satici', 'magaza-ac', 'hediye-rehberi'
        ]

        url_lower = url.lower()

        # İstenmeyen mi?
        if any(skip in url_lower for skip in skip_patterns):
            return False

        # Kategori belirteci var mı?
        if any(indicator in url_lower for indicator in category_indicators):
            return True

        return False

    def _extract_name_from_url(self, url: str) -> str:
        """URL'den kategori adını çıkar"""

        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        if segments:
            # Son segment'i al ve temizle
            name = segments[-1]
            name = name.replace('-', ' ').replace('_', ' ')
            return name.title()

        return "Kategori"

    def _create_category_id(self, url: str) -> str:
        """URL'den kategori ID oluştur"""

        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        if segments:
            # Son segment'i ID olarak kullan
            cat_id = segments[-1]
            cat_id = re.sub(r'[^a-zA-Z0-9-]', '', cat_id)
            return cat_id[:50]

        return f"cat_{hash(url) % 10000}"

    def save_discovered_categories(self, site_id: int, categories: List[Dict]):
        """Bulunan kategorileri veritabanına kaydet"""

        from database import SessionLocal, SiteUrl
        session = SessionLocal()

        added = 0
        try:
            for cat in categories:
                existing = session.query(SiteUrl).filter_by(
                    site_id=site_id,
                    url_path=cat['best_sellers_url']
                ).first()

                if not existing:
                    new_url = SiteUrl(
                        site_id=site_id,
                        url_type='best_sellers',
                        url_path=cat['best_sellers_url'],
                        category=cat['id'],
                        description=f"En çok satan - {cat['name']}",
                        is_active=True,
                        priority=added + 1,
                        max_pages=3,
                        max_products=100
                    )
                    session.add(new_url)
                    added += 1

            session.commit()
            print(f"✅ {added} kategori veritabanına eklendi")

        except Exception as e:
            print(f"❌ Kayıt hatası: {e}")
            session.rollback()
        finally:
            session.close()

        return added


def test_auto_spider():
    """Test fonksiyonu"""

    spider = AutoSpider()

    # Test URL'leri
    test_sites = [
        "https://www.trendyol.com",
        # "https://www.hepsiburada.com",
        # "https://www.n11.com"
    ]

    for site_url in test_sites:
        print(f"\n{'='*60}")
        print(f"🌐 {site_url} analiz ediliyor...")

        result = spider.crawl_site(site_url, max_depth=1)

        print(f"\n📊 Sonuçlar:")
        print(f"✅ {result['total']} kategori bulundu")

        # İlk 5 kategoriyi göster
        for i, cat in enumerate(result['categories'][:5], 1):
            print(f"\n{i}. {cat['name']}")
            print(f"   ID: {cat['id']}")
            print(f"   URL: {cat['url'][:80]}...")
            print(f"   En Çok Satanlar: {cat['best_sellers_url'][:80]}...")
            if 'product_count' in cat:
                print(f"   Ürün Sayısı: {cat['product_count']}")

        if result['total'] > 5:
            print(f"\n... ve {result['total'] - 5} kategori daha")

        # Pattern'leri göster
        if result['best_seller_patterns']:
            print(f"\n🔍 Bulunan en çok satan pattern'leri:")
            for pattern in result['best_seller_patterns'][:3]:
                print(f"   - {pattern}")


if __name__ == "__main__":
    print("🕷️ Otomatik Örümcek Başlıyor...")
    print("-" * 60)
    test_auto_spider()