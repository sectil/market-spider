#!/usr/bin/env python3
"""
Gerçek Akıllı Örümcek - Tüm kategorileri bulur
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
import json
import time
from typing import List, Dict, Set
import cloudscraper
from collections import defaultdict


class RealSpider:
    """Gerçek kategori bulucu örümcek"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        }
        self.categories = {}
        self.visited = set()

    def discover_all_categories(self, site_url: str) -> Dict:
        """Sitenin TÜM kategorilerini bul"""

        domain = urlparse(site_url).netloc.lower()

        if 'trendyol' in domain:
            return self._discover_trendyol_all(site_url)
        elif 'hepsiburada' in domain:
            return self._discover_hepsiburada_all(site_url)
        elif 'n11' in domain:
            return self._discover_n11_all(site_url)
        else:
            return self._discover_generic_all(site_url)

    def _discover_trendyol_all(self, base_url: str) -> Dict:
        """Trendyol'un TÜM kategorilerini bul"""

        all_categories = []

        # 1. Ana kategoriler - Butik listesi
        main_categories = [
            {'id': 1, 'name': 'Erkek', 'path': '/butik/liste/1/erkek'},
            {'id': 2, 'name': 'Kadın', 'path': '/butik/liste/2/kadin'},
            {'id': 3, 'name': 'Anne & Çocuk', 'path': '/butik/liste/3/anne-cocuk'},
            {'id': 4, 'name': 'Ev & Yaşam', 'path': '/butik/liste/4/ev-yasam'},
            {'id': 5, 'name': 'Süpermarket', 'path': '/butik/liste/5/supermarket'},
            {'id': 6, 'name': 'Kozmetik', 'path': '/butik/liste/6/kozmetik'},
            {'id': 7, 'name': 'Ayakkabı & Çanta', 'path': '/butik/liste/7/ayakkabi-canta'},
            {'id': 8, 'name': 'Elektronik', 'path': '/butik/liste/8/elektronik'},
            {'id': 9, 'name': 'Çocuk', 'path': '/butik/liste/9/cocuk'},
            {'id': 10, 'name': 'Ev & Mobilya', 'path': '/butik/liste/10/ev-mobilya'},
            {'id': 11, 'name': 'Spor & Outdoor', 'path': '/butik/liste/11/spor-outdoor'},
        ]

        print("🔍 Ana kategoriler taranıyor...")

        # Her ana kategoriyi ziyaret et
        for main_cat in main_categories:
            cat_url = f"{base_url}{main_cat['path']}"

            # Ana kategoriyi ekle
            all_categories.append({
                'id': f"main_{main_cat['id']}",
                'name': main_cat['name'],
                'url': cat_url,
                'best_sellers_url': f"{cat_url}?sst=BEST_SELLER",
                'level': 'main',
                'parent': None
            })

            # Alt kategorileri bul
            print(f"   📂 {main_cat['name']} kategorisi taranıyor...")
            subcategories = self._get_trendyol_subcategories(base_url, main_cat['path'])
            all_categories.extend(subcategories)

            time.sleep(0.5)  # Rate limiting

        # 2. Direkt kategori URL'leri (x-c pattern)
        direct_categories = self._find_trendyol_direct_categories(base_url)
        all_categories.extend(direct_categories)

        # 3. API'den kategoriler
        api_categories = self._get_trendyol_api_categories()
        all_categories.extend(api_categories)

        # Duplicate'leri temizle
        unique_categories = {}
        for cat in all_categories:
            key = cat.get('id') or cat.get('url')
            if key and key not in unique_categories:
                unique_categories[key] = cat

        return {
            'site': 'trendyol',
            'base_url': base_url,
            'categories': list(unique_categories.values()),
            'total': len(unique_categories),
            'structure': {
                'main_categories': len(main_categories),
                'total_with_subcategories': len(unique_categories)
            }
        }

    def _get_trendyol_subcategories(self, base_url: str, main_path: str) -> List[Dict]:
        """Ana kategorinin alt kategorilerini bul"""

        subcategories = []

        try:
            url = f"{base_url}{main_path}"
            response = self.scraper.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Alt kategori linklerini bul
            # Trendyol'da farklı pattern'ler olabilir
            patterns = [
                'a[href*="/sr?"]',  # Search result links
                'a[href*="/x-c"]',  # Category links with x-c pattern
                'a[href*="/x-g"]',  # Gender specific categories
                '.category-box a',
                '.sub-category a',
                '[class*="category"] a[href*="/"]'
            ]

            for pattern in patterns:
                links = soup.select(pattern)

                for link in links[:50]:  # İlk 50 alt kategori
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if href and text and len(text) > 2:
                        # URL'yi temizle
                        if not href.startswith('http'):
                            full_url = urljoin(base_url, href)
                        else:
                            full_url = href

                        # Filtreleme
                        if self._is_valid_category_url(full_url):
                            subcategories.append({
                                'id': self._extract_id_from_url(full_url),
                                'name': text,
                                'url': full_url,
                                'best_sellers_url': self._add_bestseller_param(full_url, 'trendyol'),
                                'level': 'sub',
                                'parent': main_path
                            })

        except Exception as e:
            print(f"      ⚠️ Alt kategori bulunamadı: {e}")

        return subcategories

    def _find_trendyol_direct_categories(self, base_url: str) -> List[Dict]:
        """Trendyol'un direkt kategori URL'lerini bul"""

        categories = []

        # Bilinen popüler kategoriler
        popular_categories = [
            # Elektronik
            {'name': 'Cep Telefonu', 'url': '/cep-telefonu-x-c103498'},
            {'name': 'Bilgisayar', 'url': '/bilgisayar-x-c103108'},
            {'name': 'Televizyon', 'url': '/televizyon-x-c103546'},
            {'name': 'Kulaklık', 'url': '/kulaklik-x-c103628'},
            {'name': 'Tablet', 'url': '/tablet-x-c103665'},
            {'name': 'Oyun Konsolu', 'url': '/oyun-konsollari-x-c106535'},

            # Moda
            {'name': 'Elbise', 'url': '/elbise-x-c56'},
            {'name': 'T-shirt', 'url': '/tisort-x-c73'},
            {'name': 'Pantolon', 'url': '/pantolon-x-c70'},
            {'name': 'Ayakkabı', 'url': '/ayakkabi-x-c114'},
            {'name': 'Mont', 'url': '/mont-x-c118'},
            {'name': 'Çanta', 'url': '/canta-x-c118'},

            # Kozmetik
            {'name': 'Parfüm', 'url': '/parfum-x-c103977'},
            {'name': 'Makyaj', 'url': '/makyaj-x-c100257'},
            {'name': 'Cilt Bakım', 'url': '/cilt-bakim-x-c100318'},
            {'name': 'Saç Bakım', 'url': '/sac-bakim-x-c100104'},

            # Ev
            {'name': 'Mobilya', 'url': '/mobilya-x-c104502'},
            {'name': 'Ev Tekstili', 'url': '/ev-tekstili-x-c1315'},
            {'name': 'Mutfak', 'url': '/mutfak-gerecleri-x-c104574'},
            {'name': 'Banyo', 'url': '/banyo-x-c105101'},
            {'name': 'Dekorasyon', 'url': '/ev-dekorasyon-x-c103668'},

            # Bebek
            {'name': 'Bebek Giyim', 'url': '/bebek-giyim-x-c101455'},
            {'name': 'Bebek Bezi', 'url': '/bebek-bezi-x-c101462'},
            {'name': 'Oyuncak', 'url': '/oyuncak-x-c104719'},

            # Spor
            {'name': 'Spor Giyim', 'url': '/spor-giyim-x-c101439'},
            {'name': 'Spor Ayakkabı', 'url': '/spor-ayakkabi-x-c106543'},
            {'name': 'Fitness', 'url': '/fitness-kondisyon-x-c100584'},

            # Süpermarket
            {'name': 'Gıda', 'url': '/gida-x-c103893'},
            {'name': 'Temizlik', 'url': '/temizlik-x-c103928'},
            {'name': 'Kişisel Bakım', 'url': '/kisisel-bakim-x-c103996'},
        ]

        for cat in popular_categories:
            full_url = f"{base_url}{cat['url']}"
            categories.append({
                'id': self._extract_id_from_url(full_url),
                'name': cat['name'],
                'url': full_url,
                'best_sellers_url': f"{full_url}?sst=BEST_SELLER",
                'level': 'direct',
                'parent': None
            })

        return categories

    def _get_trendyol_api_categories(self) -> List[Dict]:
        """Trendyol API'den kategorileri al (opsiyonel)"""

        categories = []

        # Trendyol'un public API endpoint'leri
        api_endpoints = [
            'https://public-mdc.trendyol.com/discovery-web-websfxcategoriesv2-santral/api/categories',
            'https://public.trendyol.com/discovery-web-searchgw-service/v2/api/filter/tabs'
        ]

        for endpoint in api_endpoints[:1]:  # İlk endpoint'i dene
            try:
                response = requests.get(endpoint, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    # API response'u parse et
                    # (Trendyol API yapısına göre düzenlenecek)
                    pass
            except:
                pass

        return categories

    def _discover_hepsiburada_all(self, base_url: str) -> Dict:
        """Hepsiburada'nın tüm kategorilerini bul"""

        all_categories = []

        # Ana kategoriler
        main_categories = [
            {'name': 'Elektronik', 'id': '60001028'},
            {'name': 'Moda', 'id': '60002028'},
            {'name': 'Ev, Yaşam', 'id': '60008028'},
            {'name': 'Oto, Bahçe', 'id': '60009028'},
            {'name': 'Anne, Bebek', 'id': '60003028'},
            {'name': 'Spor', 'id': '60006028'},
            {'name': 'Kozmetik', 'id': '60004028'},
            {'name': 'Süpermarket', 'id': '60007028'},
            {'name': 'Kitap', 'id': '60005028'},
        ]

        for main_cat in main_categories:
            cat_url = f"{base_url}/c-{main_cat['id']}"
            all_categories.append({
                'id': main_cat['id'],
                'name': main_cat['name'],
                'url': cat_url,
                'best_sellers_url': f"{cat_url}?siralama=coksatan",
                'level': 'main',
                'parent': None
            })

        return {
            'site': 'hepsiburada',
            'base_url': base_url,
            'categories': all_categories,
            'total': len(all_categories),
            'structure': {
                'main_categories': len(main_categories)
            }
        }

    def _discover_n11_all(self, base_url: str) -> Dict:
        """N11'in tüm kategorilerini bul"""

        all_categories = []

        # N11 ana kategorileri
        main_paths = [
            '/elektronik',
            '/moda',
            '/ev-yasam',
            '/anne-bebek',
            '/kozmetik-kisisel-bakim',
            '/mucevher-saat',
            '/spor-outdoor',
            '/kitap-muzik-film-oyun',
            '/otomotiv-motosiklet',
            '/supermarket'
        ]

        for path in main_paths:
            cat_name = path.replace('/', '').replace('-', ' ').title()
            cat_url = f"{base_url}{path}"

            all_categories.append({
                'id': path.replace('/', ''),
                'name': cat_name,
                'url': cat_url,
                'best_sellers_url': f"{cat_url}?srt=SALES",
                'level': 'main',
                'parent': None
            })

        return {
            'site': 'n11',
            'base_url': base_url,
            'categories': all_categories,
            'total': len(all_categories),
            'structure': {
                'main_categories': len(main_paths)
            }
        }

    def _discover_generic_all(self, base_url: str) -> Dict:
        """Genel site kategorilerini bul"""

        all_categories = []

        try:
            response = self.scraper.get(base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Kategori linklerini bul
            category_selectors = [
                'nav a',
                '.menu a',
                '.categories a',
                '[class*="category"] a',
                '[class*="menu"] a'
            ]

            for selector in category_selectors:
                links = soup.select(selector)

                for link in links[:100]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if href and text and self._is_valid_category_url(href):
                        full_url = urljoin(base_url, href)

                        all_categories.append({
                            'id': self._extract_id_from_url(full_url),
                            'name': text,
                            'url': full_url,
                            'best_sellers_url': self._add_bestseller_param(full_url, 'generic'),
                            'level': 'main',
                            'parent': None
                        })

        except Exception as e:
            print(f"Genel kategori keşfi hatası: {e}")

        return {
            'site': urlparse(base_url).netloc,
            'base_url': base_url,
            'categories': all_categories,
            'total': len(all_categories)
        }

    def _is_valid_category_url(self, url: str) -> bool:
        """Geçerli kategori URL'si mi kontrol et"""

        # İstenmeyen pattern'ler
        invalid_patterns = [
            'login', 'register', 'sepet', 'cart', 'checkout',
            'hesap', 'account', 'yardim', 'help', 'iletisim',
            'contact', 'about', 'hakkimizda', 'kampanya',
            'blog', 'magazalar', 'satici'
        ]

        url_lower = url.lower()

        # İstenmeyen mi?
        if any(pattern in url_lower for pattern in invalid_patterns):
            return False

        # Dosya uzantısı var mı?
        if any(ext in url_lower for ext in ['.jpg', '.png', '.pdf', '.css', '.js']):
            return False

        return True

    def _extract_id_from_url(self, url: str) -> str:
        """URL'den kategori ID çıkar"""

        # Trendyol pattern: x-c103498
        match = re.search(r'[xc]-c?(\d+)', url)
        if match:
            return f"cat_{match.group(1)}"

        # Path'ten ID oluştur
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        if segments:
            # Son segment'i ID olarak kullan
            cat_id = segments[-1]
            cat_id = re.sub(r'[^a-zA-Z0-9-]', '', cat_id)
            return cat_id[:50]

        return f"cat_{abs(hash(url)) % 100000}"

    def _add_bestseller_param(self, url: str, site_type: str) -> str:
        """URL'ye en çok satan parametresini ekle"""

        params = {
            'trendyol': 'sst=BEST_SELLER',
            'hepsiburada': 'siralama=coksatan',
            'n11': 'srt=SALES',
            'gittigidiyor': 'sira=satissayisi',
            'generic': 'sort=bestseller'
        }

        param = params.get(site_type, 'sort=bestseller')

        if '?' in url:
            return f"{url}&{param}"
        else:
            return f"{url}?{param}"

    def save_categories(self, site_id: int, categories: List[Dict]) -> int:
        """Kategorileri veritabanına kaydet"""

        from database import SessionLocal, SiteUrl
        session = SessionLocal()

        added = 0
        try:
            for cat in categories:
                # Duplicate kontrolü
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
                        description=f"{cat['name']} - En çok satanlar",
                        is_active=True,
                        priority=added + 1,
                        max_pages=2,
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


def test_real_spider():
    """Test fonksiyonu"""

    spider = RealSpider()

    # Trendyol'u test et
    print("🕷️ Gerçek Örümcek Çalışıyor...")
    print("-" * 60)

    result = spider.discover_all_categories("https://www.trendyol.com")

    print(f"\n📊 SONUÇLAR:")
    print(f"✅ Toplam {result['total']} kategori bulundu!")

    if 'structure' in result:
        print(f"\n📈 Kategori Yapısı:")
        for key, value in result['structure'].items():
            print(f"   {key}: {value}")

    # Kategorileri seviyelerine göre grupla
    by_level = defaultdict(list)
    for cat in result['categories']:
        by_level[cat.get('level', 'unknown')].append(cat)

    print(f"\n📂 Seviyeye Göre Dağılım:")
    for level, cats in by_level.items():
        print(f"   {level}: {len(cats)} kategori")

    # İlk 10 kategoriyi göster
    print(f"\n🔍 İlk 10 Kategori:")
    for i, cat in enumerate(result['categories'][:10], 1):
        print(f"\n{i}. {cat['name']}")
        print(f"   ID: {cat['id']}")
        print(f"   URL: {cat['url'][:60]}...")
        print(f"   Seviye: {cat.get('level', 'unknown')}")

    if result['total'] > 10:
        print(f"\n... ve {result['total'] - 10} kategori daha!")


if __name__ == "__main__":
    test_real_spider()