#!/usr/bin/env python3
"""
Hepsiburada.com Scraper
"""

import requests
from bs4 import BeautifulSoup
import cloudscraper
import json
import time
from typing import List, Dict
from urllib.parse import urljoin


class HepsiburadaScraper:
    """Hepsiburada için özelleştirilmiş scraper"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://www.hepsiburada.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        }

    def scrape_products(self, url: str, max_pages: int = 1) -> List[Dict]:
        """Hepsiburada'dan ürünleri çek"""

        all_products = []

        for page in range(1, max_pages + 1):
            # Sayfa parametresini ekle
            page_url = url
            if '?' in page_url:
                page_url += f'&sayfa={page}'
            else:
                page_url += f'?sayfa={page}'

            try:
                # Sayfayı çek
                response = self.scraper.get(page_url, headers=self.headers, timeout=15)
                soup = BeautifulSoup(response.text, 'html.parser')

                products = self._parse_products(soup)
                all_products.extend(products)

                print(f"    Sayfa {page}: {len(products)} ürün bulundu")

                if len(products) == 0:
                    break  # Daha fazla ürün yok

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"    ⚠️ Sayfa {page} çekilemedi: {str(e)[:50]}")
                break

        return all_products

    def _parse_products(self, soup: BeautifulSoup) -> List[Dict]:
        """HTML'den ürünleri parse et"""
        products = []

        # Hepsiburada ürün kartlarını bul
        product_cards = soup.select('li[class*="productListContent"], div[class*="product-list-item"]')

        for card in product_cards:
            try:
                product = {}

                # İsim
                name_elem = card.select_one('h3, a[title]')
                product['name'] = name_elem.get('title', name_elem.get_text(strip=True)) if name_elem else ''

                # Marka
                brand_elem = card.select_one('span[class*="brand"]')
                product['brand'] = brand_elem.get_text(strip=True) if brand_elem else ''

                # Fiyat
                price_elem = card.select_one('[data-test-id*="price"], span[class*="price"]')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # TL ve virgülü temizle
                    price_text = price_text.replace('TL', '').replace('.', '').replace(',', '.').strip()
                    try:
                        product['price'] = float(price_text)
                    except:
                        product['price'] = 0
                else:
                    product['price'] = 0

                # URL
                link_elem = card.select_one('a[href]')
                if link_elem:
                    product['url'] = urljoin(self.base_url, link_elem.get('href', ''))
                else:
                    product['url'] = ''

                # Resim
                img_elem = card.select_one('img[src], img[data-src]')
                if img_elem:
                    product['image'] = img_elem.get('src') or img_elem.get('data-src', '')
                else:
                    product['image'] = ''

                # ID (URL'den çıkar)
                if product['url']:
                    import re
                    match = re.search(r'-([a-zA-Z0-9]+)$', product['url'].split('?')[0])
                    product['id'] = match.group(1) if match else ''
                else:
                    product['id'] = ''

                # Rating
                rating_elem = card.select_one('[class*="rating"], [class*="star"]')
                product['rating'] = 0  # Hepsiburada'da rating parse etmek zor

                # Satıcı
                seller_elem = card.select_one('[class*="merchant"], [class*="seller"]')
                product['seller'] = seller_elem.get_text(strip=True) if seller_elem else ''

                product['review_count'] = 0

                if product['name'] and product['price'] > 0:
                    products.append(product)

            except Exception as e:
                continue

        return products


def test_scraper():
    """Test fonksiyonu"""
    scraper = HepsiburadaScraper()

    # Test URL
    test_url = "https://www.hepsiburada.com/bilgisayarlar-c-2147483646?siralama=coksatan"

    print(f"🔍 Test URL: {test_url}")
    products = scraper.scrape_products(test_url, max_pages=1)

    print(f"\n✅ {len(products)} ürün bulundu!")

    # İlk 5 ürünü göster
    for i, product in enumerate(products[:5], 1):
        print(f"\n{i}. {product['name'][:60]}...")
        print(f"   Marka: {product['brand']}")
        print(f"   Fiyat: {product['price']} TL")
        print(f"   URL: {product['url'][:60]}...")

    return products


if __name__ == "__main__":
    test_scraper()