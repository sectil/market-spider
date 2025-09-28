#!/usr/bin/env python3
"""
Otomatik Kategori Keşif Sistemi
Site URL'sinden otomatik olarak tüm kategorileri ve en çok satanları bulur
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import json
import time
from typing import List, Dict, Set, Optional
import cloudscraper
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from database import SessionLocal, SiteConfig, SiteUrl
from datetime import datetime


class AutoCategoryDiscovery:
    """Otomatik kategori ve en çok satanlar keşfi"""

    def __init__(self, use_selenium: bool = False):
        self.scraper = cloudscraper.create_scraper()
        self.use_selenium = use_selenium
        self.driver = None
        self.discovered_categories = []
        self.discovered_best_sellers = []

    def setup_selenium(self):
        """Selenium driver kurulumu"""
        if not self.driver and self.use_selenium:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            self.driver = webdriver.Chrome(options=options)

    def close(self):
        """Driver'ı kapat"""
        if self.driver:
            self.driver.quit()

    def discover_trendyol(self, base_url: str) -> Dict:
        """Trendyol için otomatik keşif"""
        categories = []

        try:
            # Ana sayfayı al
            response = self.scraper.get(base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # 1. Üst menüdeki ana kategorileri bul
            main_menu = soup.select('nav a[href*="/"], .category-header a, .main-nav a')

            category_patterns = {
                'kadin': 'Kadın',
                'erkek': 'Erkek',
                'cocuk': 'Çocuk',
                'ayakkabi': 'Ayakkabı',
                'canta': 'Çanta',
                'saat': 'Saat & Aksesuar',
                'kozmetik': 'Kozmetik',
                'elektronik': 'Elektronik',
                'spor': 'Spor',
                'kitap': 'Kitap',
                'oyuncak': 'Oyuncak',
                'mobilya': 'Ev & Mobilya',
                'supermarket': 'Süpermarket',
                'otomobil': 'Otomobil',
                'yapı-market': 'Yapı Market',
                'pet-shop': 'Pet Shop',
                'oyun-konsol': 'Oyun & Konsol',
                'tv-ses': 'TV & Ses Sistemleri',
                'telefon': 'Telefon',
                'bilgisayar': 'Bilgisayar'
            }

            # 2. Kategori linklerini topla
            for link in main_menu:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # URL'den kategori çıkar
                for pattern, name in category_patterns.items():
                    if pattern in href.lower() or pattern in text.lower():
                        # En çok satanlar URL'sini oluştur
                        if href.startswith('http'):
                            category_url = href
                        else:
                            category_url = urljoin(base_url, href)

                        # Trendyol'da en çok satanlar parametresi
                        if '?' in category_url:
                            best_seller_url = f"{category_url}&sst=BEST_SELLER"
                        else:
                            best_seller_url = f"{category_url}?sst=BEST_SELLER"

                        categories.append({
                            'category': pattern,
                            'name': name,
                            'url': category_url,
                            'best_sellers_url': best_seller_url,
                            'type': 'auto_discovered'
                        })
                        break

            # 3. Sitemap'ten ek kategoriler bul (opsiyonel)
            sitemap_urls = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/robots.txt"
            ]

            for sitemap_url in sitemap_urls:
                try:
                    resp = self.scraper.get(sitemap_url, timeout=5)
                    if resp.status_code == 200:
                        # robots.txt'den sitemap'leri çıkar
                        if 'robots.txt' in sitemap_url:
                            sitemap_matches = re.findall(r'Sitemap:\s*(.*)', resp.text)
                            for sitemap in sitemap_matches[:3]:  # İlk 3 sitemap
                                self._parse_sitemap_for_categories(sitemap, categories, category_patterns)
                except:
                    continue

        except Exception as e:
            print(f"Trendyol keşif hatası: {e}")

        return {
            'site': 'trendyol',
            'categories': categories,
            'total': len(categories)
        }

    def discover_hepsiburada(self, base_url: str) -> Dict:
        """Hepsiburada için otomatik keşif"""
        categories = []

        try:
            response = self.scraper.get(base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Hepsiburada kategori yapısı
            category_links = soup.select('a[href*="/c-"], .categories a, nav a[href*="kategori"]')

            for link in category_links[:30]:  # İlk 30 kategori
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if '/c-' in href and text:
                    category_url = urljoin(base_url, href)
                    # Hepsiburada'da sıralama parametresi
                    best_seller_url = f"{category_url}?siralama=coksatan"

                    categories.append({
                        'category': self._extract_category_key(href),
                        'name': text,
                        'url': category_url,
                        'best_sellers_url': best_seller_url,
                        'type': 'auto_discovered'
                    })

        except Exception as e:
            print(f"Hepsiburada keşif hatası: {e}")

        return {
            'site': 'hepsiburada',
            'categories': categories,
            'total': len(categories)
        }

    def discover_n11(self, base_url: str) -> Dict:
        """N11 için otomatik keşif"""
        categories = []

        try:
            response = self.scraper.get(base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # N11 kategori yapısı
            category_links = soup.select('.catMenu a, .categories a, nav a')

            for link in category_links[:30]:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                if href and text and not href.startswith('#'):
                    category_url = urljoin(base_url, href)
                    # N11'de sıralama parametresi
                    if '?' in category_url:
                        best_seller_url = f"{category_url}&srt=SALES"
                    else:
                        best_seller_url = f"{category_url}?srt=SALES"

                    categories.append({
                        'category': self._extract_category_key(href),
                        'name': text,
                        'url': category_url,
                        'best_sellers_url': best_seller_url,
                        'type': 'auto_discovered'
                    })

        except Exception as e:
            print(f"N11 keşif hatası: {e}")

        return {
            'site': 'n11',
            'categories': categories,
            'total': len(categories)
        }

    def discover_amazon_tr(self, base_url: str) -> Dict:
        """Amazon TR için otomatik keşif"""
        categories = []

        try:
            # Amazon için Selenium kullanmak daha iyi
            if self.use_selenium:
                self.setup_selenium()
                self.driver.get(base_url)
                time.sleep(2)

                # Kategori menüsünü aç
                try:
                    menu_btn = self.driver.find_element(By.ID, "nav-hamburger-menu")
                    menu_btn.click()
                    time.sleep(1)

                    # Kategorileri bul
                    category_elements = self.driver.find_elements(By.CSS_SELECTOR, ".hmenu-item")

                    for elem in category_elements[:20]:
                        text = elem.text.strip()
                        href = elem.get_attribute('href')

                        if href and text:
                            # Amazon'da best seller URL'si
                            category_key = self._extract_category_key(href)
                            best_seller_url = f"{base_url}/gp/bestsellers/{category_key}"

                            categories.append({
                                'category': category_key,
                                'name': text,
                                'url': href,
                                'best_sellers_url': best_seller_url,
                                'type': 'auto_discovered'
                            })
                except:
                    pass
            else:
                # Selenium yoksa basit scraping
                response = self.scraper.get(f"{base_url}/gp/bestsellers", timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                category_links = soup.select('a[href*="/bestsellers/"]')

                for link in category_links[:20]:
                    href = link.get('href', '')
                    text = link.get_text(strip=True)

                    if href and text:
                        categories.append({
                            'category': self._extract_category_key(href),
                            'name': text,
                            'url': urljoin(base_url, href),
                            'best_sellers_url': urljoin(base_url, href),
                            'type': 'auto_discovered'
                        })

        except Exception as e:
            print(f"Amazon TR keşif hatası: {e}")

        return {
            'site': 'amazon_tr',
            'categories': categories,
            'total': len(categories)
        }

    def discover_site(self, site_url: str) -> Dict:
        """Verilen site için otomatik kategori keşfi"""

        domain = urlparse(site_url).netloc.lower()

        # Site özel keşif metodları
        if 'trendyol' in domain:
            return self.discover_trendyol(site_url)
        elif 'hepsiburada' in domain:
            return self.discover_hepsiburada(site_url)
        elif 'n11' in domain:
            return self.discover_n11(site_url)
        elif 'amazon' in domain:
            return self.discover_amazon_tr(site_url)
        else:
            # Genel keşif metodu
            return self.discover_generic(site_url)

    def discover_generic(self, base_url: str) -> Dict:
        """Genel siteler için otomatik keşif"""
        categories = []

        try:
            response = self.scraper.get(base_url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Genel kategori pattern'leri
            patterns = [
                r'kategori|category|categories',
                r'urunler|products|items',
                r'koleksiyon|collection',
                r'marka|brand|brands',
                r'/c-|/k-|/cat-'
            ]

            # Olası en çok satanlar parametreleri
            sort_params = [
                'sort=best-selling',
                'order=popular',
                'siralama=coksatan',
                'srt=SALES',
                'sortBy=sales',
                'filter=bestseller'
            ]

            # Tüm linkleri kontrol et
            all_links = soup.find_all('a', href=True)
            seen_categories = set()

            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Pattern kontrolü
                for pattern in patterns:
                    if re.search(pattern, href, re.IGNORECASE):
                        category_key = self._extract_category_key(href)

                        if category_key not in seen_categories and text:
                            seen_categories.add(category_key)

                            full_url = urljoin(base_url, href)

                            # En çok satanlar URL'sini tahmin et
                            best_seller_url = full_url
                            if '?' in full_url:
                                best_seller_url = f"{full_url}&{sort_params[0]}"
                            else:
                                best_seller_url = f"{full_url}?{sort_params[0]}"

                            categories.append({
                                'category': category_key,
                                'name': text[:100],  # Max 100 karakter
                                'url': full_url,
                                'best_sellers_url': best_seller_url,
                                'type': 'auto_discovered'
                            })

                            if len(categories) >= 20:  # Max 20 kategori
                                break

        except Exception as e:
            print(f"Genel keşif hatası: {e}")

        return {
            'site': urlparse(base_url).netloc,
            'categories': categories,
            'total': len(categories)
        }

    def _extract_category_key(self, url: str) -> str:
        """URL'den kategori anahtarını çıkar"""
        # URL'den temiz kategori ismi çıkar
        path = urlparse(url).path

        # Son segment'i al
        segments = [s for s in path.split('/') if s]
        if segments:
            category = segments[-1]
            # Özel karakterleri temizle
            category = re.sub(r'[^a-zA-Z0-9-_]', '', category)
            return category[:50]  # Max 50 karakter

        return 'general'

    def _parse_sitemap_for_categories(self, sitemap_url: str, categories: List, patterns: Dict):
        """Sitemap'ten kategori URL'leri çıkar"""
        try:
            resp = self.scraper.get(sitemap_url, timeout=5)
            if resp.status_code == 200:
                # URL'leri çıkar
                urls = re.findall(r'<loc>(.*?)</loc>', resp.text)

                for url in urls[:50]:  # İlk 50 URL
                    for pattern, name in patterns.items():
                        if pattern in url.lower():
                            # Zaten eklenmemiş mi kontrol et
                            if not any(c['category'] == pattern for c in categories):
                                categories.append({
                                    'category': pattern,
                                    'name': name,
                                    'url': url,
                                    'best_sellers_url': f"{url}?sst=BEST_SELLER",
                                    'type': 'sitemap'
                                })
                            break
        except:
            pass

    def save_to_database(self, site_id: int, discovered_data: Dict):
        """Keşfedilen kategorileri veritabanına kaydet"""
        session = SessionLocal()

        try:
            added_count = 0

            for category in discovered_data['categories']:
                # Aynı URL var mı kontrol et
                existing = session.query(SiteUrl).filter_by(
                    site_id=site_id,
                    url_path=category['best_sellers_url']
                ).first()

                if not existing:
                    new_url = SiteUrl(
                        site_id=site_id,
                        url_type='best_sellers',
                        url_path=category['best_sellers_url'],
                        category=category['category'],
                        description=f"En çok satan {category['name']}",
                        is_active=True,
                        priority=added_count + 1,
                        max_pages=2,
                        max_products=100,
                        selectors={}
                    )
                    session.add(new_url)
                    added_count += 1

            session.commit()
            print(f"✅ {added_count} yeni kategori eklendi")
            return added_count

        except Exception as e:
            print(f"❌ Veritabanı hatası: {e}")
            session.rollback()
            return 0
        finally:
            session.close()


def discover_and_save(site_url: str, site_id: int = None, use_selenium: bool = False):
    """Site için kategorileri keşfet ve kaydet"""

    discoverer = AutoCategoryDiscovery(use_selenium=use_selenium)

    try:
        print(f"\n🔍 {site_url} için kategori keşfi başlıyor...")

        # Kategorileri keşfet
        result = discoverer.discover_site(site_url)

        print(f"📊 {result['total']} kategori bulundu")

        # İlk 5 kategoriyi göster
        for i, cat in enumerate(result['categories'][:5], 1):
            print(f"   {i}. {cat['name']} ({cat['category']})")

        if result['total'] > 5:
            print(f"   ... ve {result['total'] - 5} kategori daha")

        # Veritabanına kaydet
        if site_id:
            added = discoverer.save_to_database(site_id, result)
            print(f"\n💾 {added} yeni kategori veritabanına eklendi")

        return result

    finally:
        discoverer.close()


if __name__ == "__main__":
    # Test
    print("🚀 Otomatik Kategori Keşif Sistemi")
    print("-" * 60)

    # Trendyol için test
    result = discover_and_save("https://www.trendyol.com", use_selenium=False)

    print("\n" + "=" * 60)
    print(f"✨ Keşif tamamlandı!")
    print(f"   Toplam kategori: {result['total']}")