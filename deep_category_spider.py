#!/usr/bin/env python3
"""
Derin Kategori Örümceği - TÜM alt kategorileri recursive olarak bulur
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import re
import json
import time
from typing import List, Dict, Set, Optional
import cloudscraper
from collections import defaultdict


class DeepCategorySpider:
    """Sınırsız derinlikte kategori bulucu"""

    def __init__(self, max_depth: int = 2):
        self.scraper = cloudscraper.create_scraper()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        }
        self.visited_urls = set()
        self.all_categories = {}
        self.max_depth = max_depth
        self.max_categories_per_level = 20  # Her seviyede max kategori
        self.category_tree = {}

    def discover_all_categories_deep(self, site_url: str) -> Dict:
        """Siteyi DERIN tara ve TÜM kategorileri ağaç yapısında bul"""

        self.base_url = site_url
        self.domain = urlparse(site_url).netloc.lower()

        print(f"🕷️ Derin Kategori Taraması Başlıyor...")
        print(f"   Max Derinlik: {self.max_depth} seviye")

        # Site tipine göre strateji belirle
        if 'trendyol' in self.domain:
            categories = self._deep_crawl_trendyol()
        elif 'hepsiburada' in self.domain:
            categories = self._deep_crawl_hepsiburada()
        elif 'n11' in self.domain:
            categories = self._deep_crawl_n11()
        else:
            categories = self._deep_crawl_generic()

        # Sonuçları hazırla
        flat_categories = self._flatten_category_tree(self.category_tree)

        return {
            'site': self.domain,
            'base_url': site_url,
            'categories': flat_categories,
            'total': len(flat_categories),
            'tree': self.category_tree,
            'structure': self._analyze_structure(flat_categories)
        }

    def _deep_crawl_trendyol(self) -> Dict:
        """Trendyol'u derin tara"""

        # Ana kategoriler
        main_categories = [
            {'id': 'kadin', 'name': 'Kadın', 'url': '/butik/liste/2/kadin'},
            {'id': 'erkek', 'name': 'Erkek', 'url': '/butik/liste/1/erkek'},
            {'id': 'cocuk', 'name': 'Çocuk', 'url': '/butik/liste/9/cocuk'},
            {'id': 'ev-yasam', 'name': 'Ev & Yaşam', 'url': '/butik/liste/4/ev-yasam'},
            {'id': 'supermarket', 'name': 'Süpermarket', 'url': '/butik/liste/5/supermarket'},
            {'id': 'kozmetik', 'name': 'Kozmetik', 'url': '/butik/liste/6/kozmetik'},
            {'id': 'ayakkabi-canta', 'name': 'Ayakkabı & Çanta', 'url': '/butik/liste/7/ayakkabi-canta'},
            {'id': 'elektronik', 'name': 'Elektronik', 'url': '/butik/liste/8/elektronik'},
            {'id': 'spor', 'name': 'Spor & Outdoor', 'url': '/butik/liste/11/spor-outdoor'},
        ]

        for main_cat in main_categories:
            print(f"\n📂 {main_cat['name']} ana kategorisi işleniyor...")

            # Ana kategoriyi ekle
            category_node = {
                'id': main_cat['id'],
                'name': main_cat['name'],
                'url': f"{self.base_url}{main_cat['url']}",
                'level': 0,
                'children': {}
            }

            # Alt kategorileri recursive olarak bul
            self._crawl_category_recursive(
                category_url=f"{self.base_url}{main_cat['url']}",
                parent_node=category_node,
                current_depth=1,
                parent_name=main_cat['name']
            )

            # Ağaca ekle
            self.category_tree[main_cat['id']] = category_node

            time.sleep(1)  # Rate limiting

        return self.category_tree

    def _crawl_category_recursive(self, category_url: str, parent_node: Dict,
                                 current_depth: int, parent_name: str):
        """Bir kategoriyi ve alt kategorilerini recursive olarak tara"""

        if current_depth > self.max_depth:
            return

        if category_url in self.visited_urls:
            return

        self.visited_urls.add(category_url)

        try:
            print(f"   {'  ' * current_depth}↳ {parent_name} alt kategorileri aranıyor...")

            response = self.scraper.get(category_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Alt kategori linklerini bul
            subcategory_links = self._extract_subcategory_links(soup, category_url)

            # Limitli sayıda alt kategori işle
            max_subcats = min(self.max_categories_per_level, len(subcategory_links))
            for i, subcat in enumerate(subcategory_links[:max_subcats]):
                if subcat['url'] not in self.visited_urls:
                    # Alt kategori düğümü oluştur
                    subcat_node = {
                        'id': subcat['id'],
                        'name': subcat['name'],
                        'url': subcat['url'],
                        'level': current_depth,
                        'children': {}
                    }

                    # Parent'a ekle
                    parent_node['children'][subcat['id']] = subcat_node

                    print(f"   {'  ' * current_depth}  ✓ {subcat['name']}")

                    # Bu alt kategorinin alt kategorilerini bul (recursive) - sadece ilk 10 için
                    if current_depth < self.max_depth and i < 10:
                        self._crawl_category_recursive(
                            category_url=subcat['url'],
                            parent_node=subcat_node,
                            current_depth=current_depth + 1,
                            parent_name=subcat['name']
                        )

                    time.sleep(0.2)  # Rate limiting

        except Exception as e:
            print(f"   {'  ' * current_depth}  ⚠️ Hata: {str(e)[:50]}")

    def _extract_subcategory_links(self, soup: BeautifulSoup, parent_url: str) -> List[Dict]:
        """Sayfadan alt kategori linklerini çıkar"""

        subcategories = []
        found_urls = set()

        # Trendyol için özel selector'lar
        if 'trendyol' in self.domain:
            selectors = [
                'div.sub-category-list a',
                'div.campaign-list a',
                'a.child-category-item',
                'div.category-box a',
                'div.boutique-list a',
                'a[href*="/sr?"]',  # Search result links
                'a[href*="/x-c"]',  # Category pattern
                'div.sub-item a',
                '.filter-container a[href*="/"]'
            ]
        elif 'hepsiburada' in self.domain:
            selectors = [
                'ul.nav-categories a',
                'div.sub-categories a',
                'li.subcategory-item a'
            ]
        else:
            selectors = [
                'nav a',
                '.categories a',
                '[class*="category"] a',
                '[class*="sub"] a'
            ]

        for selector in selectors:
            links = soup.select(selector)

            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if href and text and len(text) > 2:
                    # Filtre metinlerini atla (cm, TL, renk adları vs.)
                    filter_texts = [
                        'cm', 'mm', 'TL', '₺', '%', 'İndirim',
                        'Kurumsal Faturaya Uygun', 'Ücretsiz Kargo',
                        'Hızlı Teslimat', 'Stokta var', 'Tükendi'
                    ]

                    # Sayısal aralıkları kontrol et (10-20, 0 TL - 100 TL gibi)
                    if any(x in text for x in filter_texts):
                        continue
                    if re.match(r'^\d+(-|\s*-\s*)\d+', text):
                        continue
                    if re.match(r'^\d+\s*(cm|mm|TL)', text):
                        continue

                    full_url = urljoin(parent_url, href)

                    # Filtreleme
                    if (full_url not in found_urls and
                        self._is_valid_subcategory(full_url, parent_url)):

                        found_urls.add(full_url)
                        subcategories.append({
                            'id': self._generate_category_id(full_url),
                            'name': text[:100],
                            'url': full_url
                        })

        return subcategories

    def _is_valid_subcategory(self, url: str, parent_url: str) -> bool:
        """Geçerli bir alt kategori URL'si mi kontrol et"""

        # Aynı URL değil
        if url == parent_url:
            return False

        # İstenmeyen pattern'ler
        invalid_patterns = [
            'login', 'register', 'sepet', 'cart', 'checkout',
            'account', 'yardim', 'help', 'iletisim', 'contact',
            'kampanya', 'deal', 'blog', 'magaza', 'satici',
            '.jpg', '.png', '.pdf', '.js', '.css', '#',
            'facebook', 'twitter', 'instagram', 'youtube',
            'sort=', 'order=', 'siralama=', 'sst=', 'price=',
            'min_price', 'max_price', 'fiyat=', 'beden=', 'size=',
            'color=', 'renk=', 'marka=', 'brand=', 'rating=',
            'discount=', 'indirim=', 'page=', 'sayfa='
        ]

        url_lower = url.lower()

        if any(pattern in url_lower for pattern in invalid_patterns):
            return False

        # Kategori belirteçleri
        category_indicators = [
            '/sr?', '/x-c', '/x-g',  # Trendyol
            '/c-', '/k-',  # Genel
            'kategori', 'category',
            '/butik/', '/liste/'
        ]

        # En az bir kategori belirteci içermeli
        if not any(indicator in url_lower for indicator in category_indicators):
            # Veya parent URL'ye benzer bir yapıda olmalı
            parent_path = urlparse(parent_url).path
            url_path = urlparse(url).path

            # Path benzerliği kontrolü
            if not url_path.startswith(parent_path[:10]):
                return False

        return True

    def _generate_category_id(self, url: str) -> str:
        """URL'den kategori ID oluştur"""

        # Trendyol ID pattern: x-c12345
        match = re.search(r'[xc]-c?(\d+)', url)
        if match:
            return f"cat_{match.group(1)}"

        # URL path'inden ID
        path = urlparse(url).path
        segments = [s for s in path.split('/') if s]

        if segments:
            # Son segment
            cat_id = segments[-1]
            # Temizle
            cat_id = re.sub(r'[^a-zA-Z0-9-]', '', cat_id)
            return cat_id[:50]

        # Fallback
        return f"cat_{abs(hash(url)) % 1000000}"

    def _deep_crawl_hepsiburada(self) -> Dict:
        """Hepsiburada'yı derin tara"""

        main_categories = [
            {'id': 'elektronik', 'name': 'Elektronik', 'code': '60001028'},
            {'id': 'moda', 'name': 'Moda', 'code': '60002028'},
            {'id': 'ev-yasam', 'name': 'Ev, Yaşam', 'code': '60008028'},
            {'id': 'anne-bebek', 'name': 'Anne, Bebek', 'code': '60003028'},
            {'id': 'kozmetik', 'name': 'Kozmetik', 'code': '60004028'},
            {'id': 'spor', 'name': 'Spor', 'code': '60006028'},
        ]

        for main_cat in main_categories:
            category_url = f"{self.base_url}/c-{main_cat['code']}"

            category_node = {
                'id': main_cat['id'],
                'name': main_cat['name'],
                'url': category_url,
                'level': 0,
                'children': {}
            }

            # Alt kategorileri bul
            self._crawl_category_recursive(
                category_url=category_url,
                parent_node=category_node,
                current_depth=1,
                parent_name=main_cat['name']
            )

            self.category_tree[main_cat['id']] = category_node

        return self.category_tree

    def _deep_crawl_n11(self) -> Dict:
        """N11'i derin tara"""

        main_paths = [
            {'id': 'elektronik', 'name': 'Elektronik', 'path': '/elektronik'},
            {'id': 'moda', 'name': 'Moda', 'path': '/moda'},
            {'id': 'ev-yasam', 'name': 'Ev & Yaşam', 'path': '/ev-yasam'},
            {'id': 'anne-bebek', 'name': 'Anne & Bebek', 'path': '/anne-bebek'},
            {'id': 'kozmetik', 'name': 'Kozmetik', 'path': '/kozmetik-kisisel-bakim'},
            {'id': 'spor', 'name': 'Spor', 'path': '/spor-outdoor'},
        ]

        for main_cat in main_paths:
            category_url = f"{self.base_url}{main_cat['path']}"

            category_node = {
                'id': main_cat['id'],
                'name': main_cat['name'],
                'url': category_url,
                'level': 0,
                'children': {}
            }

            self._crawl_category_recursive(
                category_url=category_url,
                parent_node=category_node,
                current_depth=1,
                parent_name=main_cat['name']
            )

            self.category_tree[main_cat['id']] = category_node

        return self.category_tree

    def _deep_crawl_generic(self) -> Dict:
        """Genel site için derin tarama"""

        try:
            response = self.scraper.get(self.base_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Ana kategorileri bul
            main_links = soup.select('nav a, .menu > li > a, .categories > a')

            for link in main_links[:10]:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if href and text and self._is_valid_subcategory(href, self.base_url):
                    cat_id = self._generate_category_id(href)
                    category_url = urljoin(self.base_url, href)

                    category_node = {
                        'id': cat_id,
                        'name': text,
                        'url': category_url,
                        'level': 0,
                        'children': {}
                    }

                    self._crawl_category_recursive(
                        category_url=category_url,
                        parent_node=category_node,
                        current_depth=1,
                        parent_name=text
                    )

                    self.category_tree[cat_id] = category_node

        except Exception as e:
            print(f"Genel tarama hatası: {e}")

        return self.category_tree

    def _flatten_category_tree(self, tree: Dict, parent_path: str = "") -> List[Dict]:
        """Ağaç yapısını düz listeye çevir"""

        flat_list = []

        for cat_id, node in tree.items():
            # Path oluştur
            current_path = f"{parent_path}/{node['name']}" if parent_path else node['name']

            # Kategori bilgisi
            category_info = {
                'id': node['id'],
                'name': node['name'],
                'url': node['url'],
                'level': node['level'],
                'path': current_path,
                'best_sellers_url': self._add_bestseller_param(node['url']),
                'has_children': len(node.get('children', {})) > 0,
                'child_count': len(node.get('children', {}))
            }

            flat_list.append(category_info)

            # Alt kategorileri de ekle (recursive)
            if node.get('children'):
                child_categories = self._flatten_category_tree(
                    node['children'],
                    current_path
                )
                flat_list.extend(child_categories)

        return flat_list

    def _add_bestseller_param(self, url: str) -> str:
        """URL'ye en çok satan parametresini ekle"""

        if 'trendyol' in self.domain:
            param = 'sst=BEST_SELLER'
        elif 'hepsiburada' in self.domain:
            param = 'siralama=coksatan'
        elif 'n11' in self.domain:
            param = 'srt=SALES'
        elif 'gittigidiyor' in self.domain:
            param = 'sira=satissayisi'
        else:
            param = 'sort=bestseller'

        if '?' in url:
            return f"{url}&{param}"
        else:
            return f"{url}?{param}"

    def _analyze_structure(self, categories: List[Dict]) -> Dict:
        """Kategori yapısını analiz et"""

        level_counts = defaultdict(int)
        has_children_count = 0

        for cat in categories:
            level_counts[cat['level']] += 1
            if cat['has_children']:
                has_children_count += 1

        return {
            'total_categories': len(categories),
            'max_depth': max(level_counts.keys()) if level_counts else 0,
            'categories_per_level': dict(level_counts),
            'categories_with_children': has_children_count,
            'leaf_categories': len(categories) - has_children_count
        }

    def save_to_database(self, site_id: int, categories: List[Dict]) -> int:
        """Kategorileri veritabanına kaydet"""

        from database import SessionLocal, SiteUrl
        session = SessionLocal()

        added = 0
        try:
            for cat in categories:
                # URL var mı kontrol et
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
                        description=f"{cat['path']} - En çok satanlar",
                        is_active=True,
                        priority=cat['level'] * 100 + added,  # Seviyeye göre öncelik
                        max_pages=3 if cat['level'] == 0 else 2,  # Ana kategorilerde daha fazla sayfa
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


    def save_categories(self, site_id: int, categories=None):
        """Kategorileri veritabanına kaydet"""
        from database import SessionLocal, SiteUrl

        session = SessionLocal()
        added = 0

        # Eğer categories parametresi verilmişse onu kullan
        categories_to_save = categories if categories else self._flatten_category_tree()

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
                        url_path=cat.get('best_sellers_url', cat['url'] + '?sort=best-selling'),
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


def test_deep_spider():
    """Test fonksiyonu"""

    print("🕷️ Derin Kategori Örümceği Test")
    print("=" * 60)

    spider = DeepCategorySpider(max_depth=3)  # 3 seviye derinlik

    result = spider.discover_all_categories_deep("https://www.trendyol.com")

    print(f"\n📊 SONUÇLAR:")
    print(f"✅ Toplam {result['total']} kategori bulundu!")

    # Yapı analizi
    if 'structure' in result:
        print(f"\n📈 Kategori Yapısı:")
        structure = result['structure']
        print(f"   Max Derinlik: {structure['max_depth']} seviye")
        print(f"   Alt Kategorisi Olanlar: {structure['categories_with_children']}")
        print(f"   Yaprak Kategoriler: {structure['leaf_categories']}")

        print(f"\n   Seviyeye Göre Dağılım:")
        for level, count in sorted(structure['categories_per_level'].items()):
            print(f"     Seviye {level}: {count} kategori")

    # İlk 15 kategoriyi göster
    print(f"\n🔍 Örnek Kategoriler:")
    for i, cat in enumerate(result['categories'][:15], 1):
        indent = "  " * cat['level']
        print(f"{indent}{i}. {cat['name']}")
        print(f"{indent}   Path: {cat['path']}")
        print(f"{indent}   Seviye: {cat['level']}")
        if cat['has_children']:
            print(f"{indent}   Alt Kategori: {cat['child_count']} adet")

    if result['total'] > 15:
        print(f"\n... ve {result['total'] - 15} kategori daha!")

    # Ağaç yapısını göster (ilk 2 ana kategori)
    print(f"\n🌳 Kategori Ağacı (İlk 2 Ana Kategori):")
    tree_items = list(result['tree'].items())[:2]
    for main_id, main_node in tree_items:
        print(f"\n📂 {main_node['name']}")
        for sub_id, sub_node in list(main_node['children'].items())[:3]:
            print(f"  ├─ {sub_node['name']}")
            for subsub_id, subsub_node in list(sub_node.get('children', {}).items())[:2]:
                print(f"  │  ├─ {subsub_node['name']}")


if __name__ == "__main__":
    test_deep_spider()