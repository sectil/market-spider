#!/usr/bin/env python3
"""
Akıllı Kategori Bulucu
Sitelerin kategori ve en çok satanlarını otomatik bulur
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse, parse_qs
import json
from typing import List, Dict
import cloudscraper


class SmartCategoryFinder:
    """Akıllı kategori bulucu"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def find_categories(self, site_url: str) -> Dict:
        """Site için kategorileri bul"""
        domain = urlparse(site_url).netloc.lower()

        if 'trendyol' in domain:
            return self._find_trendyol_categories(site_url)
        elif 'hepsiburada' in domain:
            return self._find_hepsiburada_categories(site_url)
        elif 'n11' in domain:
            return self._find_n11_categories(site_url)
        elif 'gittigidiyor' in domain:
            return self._find_gittigidiyor_categories(site_url)
        else:
            return self._find_generic_categories(site_url)

    def _find_trendyol_categories(self, base_url: str) -> Dict:
        """Trendyol kategorilerini bul"""
        categories = []

        # Trendyol'un gerçek kategori URL'leri (Güncel - 2024)
        known_categories = [
            {'name': 'Kadın', 'path': '/butik/liste/2/kadin', 'id': 'kadin'},
            {'name': 'Erkek', 'path': '/butik/liste/1/erkek', 'id': 'erkek'},
            {'name': 'Anne & Çocuk', 'path': '/butik/liste/3/anne-cocuk', 'id': 'anne-cocuk'},
            {'name': 'Ev & Yaşam', 'path': '/butik/liste/4/ev-yasam', 'id': 'ev-yasam'},
            {'name': 'Süpermarket', 'path': '/butik/liste/5/supermarket', 'id': 'supermarket'},
            {'name': 'Kozmetik', 'path': '/butik/liste/6/kozmetik', 'id': 'kozmetik'},
            {'name': 'Ayakkabı & Çanta', 'path': '/butik/liste/7/ayakkabi-canta', 'id': 'ayakkabi-canta'},
            {'name': 'Elektronik', 'path': '/butik/liste/8/elektronik', 'id': 'elektronik'},
            {'name': 'Çocuk', 'path': '/butik/liste/9/cocuk', 'id': 'cocuk'},
            {'name': 'Ev & Mobilya', 'path': '/butik/liste/10/ev-mobilya', 'id': 'ev-mobilya'},
            {'name': 'Spor & Outdoor', 'path': '/butik/liste/11/spor-outdoor', 'id': 'spor-outdoor'},
            {'name': 'Kitap & Kırtasiye & Oyuncak', 'path': '/butik/liste/12/kitap-kirtasiye-oyuncak', 'id': 'kitap-kirtasiye'},
        ]

        try:
            # Ana sayfayı çek ve dinamik kategorileri bul
            response = self.scraper.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Navigasyon linklerini bul
            nav_links = soup.select('a[href*="/x-"], a[href*="/c-"]')

            for link in nav_links[:20]:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if text and len(text) > 2:
                    # URL'yi temizle
                    if not href.startswith('http'):
                        href = urljoin(base_url, href)

                    # Kategori ID'sini çıkar
                    cat_id = self._extract_category_id(href)

                    # Duplicate kontrolü
                    if not any(c['id'] == cat_id for c in categories):
                        categories.append({
                            'id': cat_id,
                            'name': text,
                            'url': href,
                            'best_sellers_url': f"{href}?sst=BEST_SELLER",
                            'source': 'dynamic'
                        })

        except Exception as e:
            print(f"Dinamik kategori bulma hatası: {e}")

        # Bilinen kategorileri ekle
        for cat in known_categories:
            url = f"{base_url}{cat['path']}"
            categories.append({
                'id': cat['id'],
                'name': cat['name'],
                'url': url,
                'best_sellers_url': f"{url}?sst=BEST_SELLER",
                'source': 'known'
            })

        return {
            'site': 'trendyol',
            'base_url': base_url,
            'categories': categories,
            'total': len(categories),
            'sort_parameter': 'sst=BEST_SELLER'
        }

    def _find_hepsiburada_categories(self, base_url: str) -> Dict:
        """Hepsiburada kategorilerini bul"""
        categories = []

        known_categories = [
            {'name': 'Elektronik', 'path': '/elektronik-c-60001028', 'id': 'elektronik'},
            {'name': 'Moda', 'path': '/moda-c-60002028', 'id': 'moda'},
            {'name': 'Ev, Yaşam', 'path': '/ev-yasam-c-60008028', 'id': 'ev-yasam'},
            {'name': 'Oto, Bahçe, Yapı Market', 'path': '/oto-bahce-yapi-market-c-60009028', 'id': 'oto-bahce'},
            {'name': 'Anne, Bebek, Oyuncak', 'path': '/anne-bebek-oyuncak-c-60003028', 'id': 'anne-bebek'},
            {'name': 'Spor, Outdoor', 'path': '/spor-outdoor-c-60006028', 'id': 'spor'},
            {'name': 'Kozmetik, Kişisel Bakım', 'path': '/kozmetik-kisisel-bakim-c-60004028', 'id': 'kozmetik'},
            {'name': 'Süpermarket, Pet Shop', 'path': '/supermarket-petshop-c-60007028', 'id': 'supermarket'},
            {'name': 'Kitap, Müzik, Film, Hobi', 'path': '/kitap-muzik-film-hobi-c-60005028', 'id': 'kitap'},
        ]

        for cat in known_categories:
            url = f"{base_url}{cat['path']}"
            categories.append({
                'id': cat['id'],
                'name': cat['name'],
                'url': url,
                'best_sellers_url': f"{url}?siralama=coksatan",
                'source': 'known'
            })

        return {
            'site': 'hepsiburada',
            'base_url': base_url,
            'categories': categories,
            'total': len(categories),
            'sort_parameter': 'siralama=coksatan'
        }

    def _find_n11_categories(self, base_url: str) -> Dict:
        """N11 kategorilerini bul"""
        categories = []

        known_categories = [
            {'name': 'Elektronik', 'path': '/elektronik', 'id': 'elektronik'},
            {'name': 'Moda', 'path': '/moda', 'id': 'moda'},
            {'name': 'Ev & Yaşam', 'path': '/ev-yasam', 'id': 'ev-yasam'},
            {'name': 'Anne & Bebek', 'path': '/anne-bebek', 'id': 'anne-bebek'},
            {'name': 'Kozmetik & Kişisel Bakım', 'path': '/kozmetik-kisisel-bakim', 'id': 'kozmetik'},
            {'name': 'Spor & Outdoor', 'path': '/spor-outdoor', 'id': 'spor'},
            {'name': 'Kitap & Müzik & Film', 'path': '/kitap-muzik-film-oyun', 'id': 'kitap'},
            {'name': 'Otomotiv & Motosiklet', 'path': '/otomotiv-motosiklet', 'id': 'otomotiv'},
            {'name': 'Yapı Market & Bahçe', 'path': '/yapi-market-tamirat-bahce', 'id': 'yapi-market'},
            {'name': 'Süpermarket', 'path': '/supermarket', 'id': 'supermarket'},
        ]

        for cat in known_categories:
            url = f"{base_url}{cat['path']}"
            categories.append({
                'id': cat['id'],
                'name': cat['name'],
                'url': url,
                'best_sellers_url': f"{url}?srt=SALES",
                'source': 'known'
            })

        return {
            'site': 'n11',
            'base_url': base_url,
            'categories': categories,
            'total': len(categories),
            'sort_parameter': 'srt=SALES'
        }

    def _find_gittigidiyor_categories(self, base_url: str) -> Dict:
        """GittiGidiyor kategorilerini bul"""
        categories = []

        known_categories = [
            {'name': 'Elektronik', 'path': '/elektronik', 'id': 'elektronik'},
            {'name': 'Moda', 'path': '/giyim-aksesuar', 'id': 'moda'},
            {'name': 'Ev, Bahçe, Ofis', 'path': '/ev-bahce-ofis', 'id': 'ev-bahce'},
            {'name': 'Oto, Motosiklet', 'path': '/otomobil-motor-aksesuar', 'id': 'oto'},
            {'name': 'Kozmetik', 'path': '/kozmetik-kisisel-bakim', 'id': 'kozmetik'},
            {'name': 'Anne, Bebek, Oyuncak', 'path': '/anne-bebek', 'id': 'anne-bebek'},
            {'name': 'Spor', 'path': '/spor-outdoor', 'id': 'spor'},
            {'name': 'Kitap, Müzik, Film', 'path': '/kitap-dergi-muzik-film', 'id': 'kitap'},
        ]

        for cat in known_categories:
            url = f"{base_url}{cat['path']}"
            categories.append({
                'id': cat['id'],
                'name': cat['name'],
                'url': url,
                'best_sellers_url': f"{url}?sira=satissayisi",
                'source': 'known'
            })

        return {
            'site': 'gittigidiyor',
            'base_url': base_url,
            'categories': categories,
            'total': len(categories),
            'sort_parameter': 'sira=satissayisi'
        }

    def _find_generic_categories(self, base_url: str) -> Dict:
        """Genel site kategorilerini bul"""
        categories = []

        try:
            response = self.scraper.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Olası kategori linklerini bul
            patterns = [
                'kategori', 'category', 'categories',
                'koleksiyon', 'collection',
                '/c/', '/k/', '/cat/'
            ]

            links = soup.find_all('a', href=True)
            seen = set()

            for link in links[:100]:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                for pattern in patterns:
                    if pattern in href.lower() and text and len(text) > 2:
                        cat_id = self._extract_category_id(href)

                        if cat_id not in seen:
                            seen.add(cat_id)
                            full_url = urljoin(base_url, href)

                            categories.append({
                                'id': cat_id,
                                'name': text[:100],
                                'url': full_url,
                                'best_sellers_url': f"{full_url}{'&' if '?' in full_url else '?'}sort=bestseller",
                                'source': 'dynamic'
                            })

                            if len(categories) >= 20:
                                break

        except Exception as e:
            print(f"Genel kategori bulma hatası: {e}")

        return {
            'site': urlparse(base_url).netloc,
            'base_url': base_url,
            'categories': categories,
            'total': len(categories),
            'sort_parameter': 'sort=bestseller'
        }

    def _extract_category_id(self, url: str) -> str:
        """URL'den kategori ID'si çıkar"""
        # URL'den temiz ID çıkar
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        if segments:
            # Son segment'i al ve temizle
            cat_id = segments[-1]
            cat_id = re.sub(r'[^a-zA-Z0-9-_]', '', cat_id)
            return cat_id[:50]

        return 'general'

    def save_categories(self, site_id: int, categories_data: Dict):
        """Kategorileri veritabanına kaydet"""
        from database import SessionLocal, SiteUrl

        session = SessionLocal()
        added = 0

        try:
            for cat in categories_data['categories']:
                # Duplicate kontrolü
                existing = session.query(SiteUrl).filter_by(
                    site_id=site_id,
                    category=cat['id']
                ).first()

                if not existing:
                    new_url = SiteUrl(
                        site_id=site_id,
                        url_type='best_sellers',
                        url_path=cat['best_sellers_url'],
                        category=cat['id'],
                        description=f"En çok satan {cat['name']}",
                        is_active=True,
                        priority=added + 1,
                        max_pages=3,
                        max_products=100
                    )
                    session.add(new_url)
                    added += 1

            session.commit()
            return added

        except Exception as e:
            print(f"Kayıt hatası: {e}")
            session.rollback()
            return 0
        finally:
            session.close()


def test_category_finder():
    """Test fonksiyonu"""
    finder = SmartCategoryFinder()

    sites = [
        "https://www.trendyol.com",
        "https://www.hepsiburada.com",
        "https://www.n11.com",
        "https://www.gittigidiyor.com"
    ]

    for site_url in sites:
        print(f"\n{'='*60}")
        print(f"🔍 {site_url} analiz ediliyor...")

        result = finder.find_categories(site_url)

        print(f"✅ {result['total']} kategori bulundu")
        print(f"📊 Sıralama parametresi: {result['sort_parameter']}")

        # İlk 5 kategoriyi göster
        for i, cat in enumerate(result['categories'][:5], 1):
            print(f"   {i}. {cat['name']} ({cat['id']})")
            print(f"      URL: {cat['best_sellers_url'][:80]}...")

        if result['total'] > 5:
            print(f"   ... ve {result['total'] - 5} kategori daha")


if __name__ == "__main__":
    print("🚀 Akıllı Kategori Bulucu")
    print("-" * 60)
    test_category_finder()