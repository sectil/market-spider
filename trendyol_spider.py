#!/usr/bin/env python3
"""
Trendyol Özel Kategori Örümceği
Trendyol'un yapısına özel derin kategori bulucu
"""

import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import time
import json
from typing import List, Dict

class TrendyolSpider:
    """Trendyol için özelleştirilmiş kategori örümceği"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        }
        self.base_url = "https://www.trendyol.com"
        self.visited_urls = set()
        self.all_categories = []

    def discover_all_categories(self) -> Dict:
        """Trendyol'daki tüm kategorileri bul"""

        print("🕷️ Trendyol Kategori Taraması Başlıyor...")

        # 1. Ana kategorileri bul
        main_categories = self._get_main_categories()

        # 2. Her ana kategori için alt kategorileri bul
        for main_cat in main_categories:
            print(f"\n📂 {main_cat['name']} kategorisi işleniyor...")

            # Ana kategoriyi ekle
            self.all_categories.append({
                'id': main_cat['id'],
                'name': main_cat['name'],
                'url': main_cat['url'],
                'best_sellers_url': f"{main_cat['url']}?sst=BEST_SELLER",
                'level': 0,
                'parent': None
            })

            # Alt kategorileri bul
            self._discover_subcategories(main_cat['url'], main_cat['id'], main_cat['name'], level=1)

            time.sleep(1)  # Rate limiting

        print(f"\n✅ Toplam {len(self.all_categories)} kategori bulundu!")

        return {
            'site': 'trendyol',
            'base_url': self.base_url,
            'categories': self.all_categories,
            'total': len(self.all_categories)
        }

    def _get_main_categories(self) -> List[Dict]:
        """Trendyol ana kategorileri"""
        return [
            {'id': 'kadin', 'name': 'Kadın', 'url': f'{self.base_url}/butik/liste/2/kadin'},
            {'id': 'erkek', 'name': 'Erkek', 'url': f'{self.base_url}/butik/liste/1/erkek'},
            {'id': 'cocuk', 'name': 'Çocuk', 'url': f'{self.base_url}/butik/liste/9/cocuk'},
            {'id': 'ev-yasam', 'name': 'Ev & Yaşam', 'url': f'{self.base_url}/butik/liste/4/ev-yasam'},
            {'id': 'supermarket', 'name': 'Süpermarket', 'url': f'{self.base_url}/butik/liste/5/supermarket'},
            {'id': 'kozmetik', 'name': 'Kozmetik', 'url': f'{self.base_url}/butik/liste/6/kozmetik'},
            {'id': 'ayakkabi-canta', 'name': 'Ayakkabı & Çanta', 'url': f'{self.base_url}/butik/liste/7/ayakkabi-canta'},
            {'id': 'elektronik', 'name': 'Elektronik', 'url': f'{self.base_url}/butik/liste/8/elektronik'},
            {'id': 'spor', 'name': 'Spor & Outdoor', 'url': f'{self.base_url}/butik/liste/11/spor-outdoor'},
        ]

    def _discover_subcategories(self, parent_url: str, parent_id: str, parent_name: str, level: int):
        """Alt kategorileri recursive olarak bul"""

        if level > 2 or parent_url in self.visited_urls:  # Max 2 seviye derinlik
            return

        self.visited_urls.add(parent_url)

        try:
            # Trendyol için özel kategori URL'leri
            if 'butik/liste' in parent_url:
                # Butik listesi sayfasından kategori linkleri çıkar
                subcategory_urls = self._get_butik_categories(parent_url)
            else:
                # Normal kategori sayfasından alt kategorileri çıkar
                subcategory_urls = self._get_category_subcategories(parent_url)

            for subcat in subcategory_urls[:30]:  # Her seviyede max 30 alt kategori
                if subcat['url'] not in self.visited_urls:
                    # Alt kategoriyi ekle
                    self.all_categories.append({
                        'id': subcat['id'],
                        'name': subcat['name'],
                        'url': subcat['url'],
                        'best_sellers_url': f"{subcat['url']}?sst=BEST_SELLER",
                        'level': level,
                        'parent': parent_id,
                        'parent_name': parent_name
                    })

                    print(f"  {'  ' * level}✓ {subcat['name']}")

                    # Bu alt kategorinin alt kategorilerini bul
                    if level < 2:  # Max 2 seviye
                        self._discover_subcategories(
                            subcat['url'],
                            subcat['id'],
                            subcat['name'],
                            level + 1
                        )

                    time.sleep(0.2)

        except Exception as e:
            print(f"  {'  ' * level}⚠️ Hata: {str(e)[:50]}")

    def _get_butik_categories(self, butik_url: str) -> List[Dict]:
        """Butik sayfasından kategori linklerini çıkar"""
        categories = []

        try:
            response = self.scraper.get(butik_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Trendyol'un farklı kategori link yapıları
            selectors = [
                'a[href*="/x-"]',  # /x-kategori-adi şeklinde
                'a[href*="/-c"]',  # /kategori-adi-c şeklinde
                'a[href*="/sr?"]', # Arama sonuçları
                'a.category-box',  # Kategori kutucukları
                'a.campaign-product-item',  # Kampanya ürünleri
            ]

            for selector in selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if href and text and len(text) > 2:
                        # URL'yi temizle ve kontrol et
                        full_url = urljoin(self.base_url, href)
                        if self._is_valid_category_url(full_url, text):
                            categories.append({
                                'id': self._generate_id(full_url),
                                'name': text[:100],
                                'url': full_url
                            })

            # Trendyol için bilinen alt kategoriler
            if 'kadin' in butik_url:
                categories.extend([
                    {'id': 'kadin-giyim', 'name': 'Giyim', 'url': f'{self.base_url}/kadin-giyim-x-g1-c82'},
                    {'id': 'kadin-ayakkabi', 'name': 'Ayakkabı', 'url': f'{self.base_url}/kadin-ayakkabi-x-g1-c114'},
                    {'id': 'kadin-canta', 'name': 'Çanta', 'url': f'{self.base_url}/kadin-canta-x-g1-c115'},
                    {'id': 'kadin-aksesuar', 'name': 'Aksesuar', 'url': f'{self.base_url}/kadin-aksesuar-x-g1-c116'},
                ])
            elif 'erkek' in butik_url:
                categories.extend([
                    {'id': 'erkek-giyim', 'name': 'Giyim', 'url': f'{self.base_url}/erkek-giyim-x-g2-c82'},
                    {'id': 'erkek-ayakkabi', 'name': 'Ayakkabı', 'url': f'{self.base_url}/erkek-ayakkabi-x-g2-c114'},
                    {'id': 'erkek-saat', 'name': 'Saat', 'url': f'{self.base_url}/erkek-saat-x-g2-c34'},
                ])
            elif 'cocuk' in butik_url:
                categories.extend([
                    {'id': 'bebek-giyim', 'name': 'Bebek Giyim', 'url': f'{self.base_url}/bebek-giyim-x-c83'},
                    {'id': 'cocuk-giyim', 'name': 'Çocuk Giyim', 'url': f'{self.base_url}/cocuk-giyim-x-c55'},
                    {'id': 'oyuncak', 'name': 'Oyuncak', 'url': f'{self.base_url}/oyuncak-x-c56'},
                ])

        except Exception as e:
            print(f"    ⚠️ Butik kategorileri alınamadı: {e}")

        return categories

    def _get_category_subcategories(self, category_url: str) -> List[Dict]:
        """Kategori sayfasından alt kategorileri çıkar"""
        subcategories = []

        try:
            response = self.scraper.get(category_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Alt kategori filtreleri
            filter_sections = soup.select('.fltr-cntnr-ttl, .filter-container')

            for section in filter_sections:
                # Kategori filtresini bul
                if 'kategori' in section.get_text(strip=True).lower():
                    links = section.find_all('a')
                    for link in links[:20]:
                        href = link.get('href', '')
                        text = link.get_text(strip=True)

                        if href and text:
                            full_url = urljoin(self.base_url, href)
                            subcategories.append({
                                'id': self._generate_id(full_url),
                                'name': text[:100],
                                'url': full_url
                            })

        except Exception as e:
            pass

        return subcategories

    def _is_valid_category_url(self, url: str, text: str) -> bool:
        """Geçerli kategori URL'si mi kontrol et"""

        # İstenmeyen kelimeler
        invalid_words = [
            'giriş', 'login', 'sepet', 'cart', 'yardım', 'help',
            'kampanya', 'indirim', '%', 'TL', '₺', 'Kargo',
            'Stokta', 'Tükendi', 'Hediye', 'Kupon'
        ]

        # URL veya metinde istenmeyen kelime varsa atla
        url_lower = url.lower()
        text_lower = text.lower()

        for word in invalid_words:
            if word.lower() in url_lower or word.lower() in text_lower:
                return False

        # Sayı ile başlayan metinleri atla (fiyat, beden vs.)
        if re.match(r'^\d+', text):
            return False

        # Tek harf veya sayı olanları atla
        if len(text) <= 1:
            return False

        return True

    def _generate_id(self, url: str) -> str:
        """URL'den kategori ID'si oluştur"""
        path = urlparse(url).path
        # URL'den temiz ID çıkar
        id_match = re.search(r'/([^/]+)(?:-x-|-c)(\w+)', path)
        if id_match:
            return f"{id_match.group(1)}_{id_match.group(2)}"

        # Fallback: path'in son parçası
        segments = [s for s in path.split('/') if s]
        if segments:
            return re.sub(r'[^a-zA-Z0-9-_]', '', segments[-1])[:50]

        return f"cat_{hash(url) % 100000}"

    def save_categories(self, site_id: int, categories=None):
        """Kategorileri veritabanına kaydet"""
        from database import SessionLocal, SiteUrl

        session = SessionLocal()
        added = 0

        # Eğer categories parametresi verilmişse onu kullan, yoksa self.all_categories
        categories_to_save = categories if categories else self.all_categories

        try:
            for cat in categories_to_save:
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
                        description=f"En çok satan - {cat['name']}",
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
            print(f"❌ Kayıt hatası: {e}")
            session.rollback()
            return 0
        finally:
            session.close()


def test_trendyol_spider():
    """Test fonksiyonu"""
    spider = TrendyolSpider()
    result = spider.discover_all_categories()

    # Sonuçları göster
    print(f"\n📊 Kategori Seviyeleri:")
    levels = {}
    for cat in result['categories']:
        level = cat.get('level', 0)
        levels[level] = levels.get(level, 0) + 1

    for level, count in sorted(levels.items()):
        print(f"  Seviye {level}: {count} kategori")

    # Örnek kategorileri göster
    print(f"\n🌳 Örnek Kategoriler:")
    for i, cat in enumerate(result['categories'][:30], 1):
        indent = "  " * cat.get('level', 0)
        parent_info = f" (← {cat.get('parent_name', '')})" if cat.get('parent') else ""
        print(f"{indent}{i}. {cat['name']}{parent_info}")

    if result['total'] > 30:
        print(f"\n... ve {result['total'] - 30} kategori daha")

    return result


if __name__ == "__main__":
    print("🚀 Trendyol Kategori Örümceği")
    print("-" * 60)
    test_trendyol_spider()