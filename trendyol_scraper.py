#!/usr/bin/env python3
"""
Trendyol.com Scraper
"""

import requests
from bs4 import BeautifulSoup
import cloudscraper
import json
import time
import re
from typing import List, Dict
from urllib.parse import urljoin


class TrendyolScraper:
    """Trendyol için özelleştirilmiş scraper"""

    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        self.base_url = "https://www.trendyol.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept': 'application/json, text/plain, */*',
        }

    def scrape_products(self, url: str, max_pages: int = 1) -> List[Dict]:
        """Trendyol'dan ürünleri çek"""

        all_products = []

        for page in range(1, max_pages + 1):
            # Sayfa parametresini ekle
            page_url = url
            if '?' in page_url:
                page_url += f'&pi={page}'
            else:
                page_url += f'?pi={page}'

            try:
                # Sayfayı çek
                response = self.scraper.get(page_url, headers=self.headers, timeout=15)

                # JSON data var mı kontrol et (Trendyol genelde JSON döner)
                if 'application/json' in response.headers.get('content-type', ''):
                    data = response.json()
                    products = self._parse_json_products(data)
                else:
                    # HTML parse et
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Önce __SEARCH_APP_INITIAL_STATE__ içinde ürün ara
                    products = self._extract_products_from_state(soup)

                    # Bulamazsan HTML'den parse et
                    if not products:
                        products = self._parse_html_products(soup, page_url)

                all_products.extend(products)

                print(f"    Sayfa {page}: {len(products)} ürün bulundu")

                if len(products) == 0:
                    break  # Daha fazla ürün yok

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"    ⚠️ Sayfa {page} çekilemedi: {str(e)[:50]}")
                break

        return all_products

    def _parse_json_products(self, data: Dict) -> List[Dict]:
        """JSON response'dan ürünleri parse et"""
        products = []

        # Farklı JSON yapıları olabilir
        product_list = []

        if 'result' in data:
            if 'products' in data['result']:
                product_list = data['result']['products']
            elif 'slicingAttributes' in data['result']:
                # Alternatif yapı
                if 'products' in data['result'].get('slicingAttributes', {}):
                    product_list = data['result']['slicingAttributes']['products']
        elif 'products' in data:
            product_list = data['products']

        for item in product_list:
            try:
                # Fiyat bilgisini al
                price = 0
                if 'price' in item:
                    if isinstance(item['price'], dict):
                        price = item['price'].get('sellingPrice', 0)
                    else:
                        price = item['price']
                elif 'sellingPrice' in item:
                    price = item['sellingPrice']
                elif 'discountedPrice' in item:
                    price = item['discountedPrice']

                product = {
                    'id': str(item.get('id', '')),
                    'name': item.get('name', ''),
                    'brand': item.get('brand', {}).get('name', '') if isinstance(item.get('brand'), dict) else item.get('brand', ''),
                    'price': price,
                    'url': urljoin(self.base_url, item.get('url', '')),
                    'image': item.get('images', [{}])[0].get('url', '') if item.get('images') else '',
                    'rating': item.get('ratingScore', {}).get('averageRating', 0) if isinstance(item.get('ratingScore'), dict) else 0,
                    'review_count': item.get('ratingScore', {}).get('totalCount', 0) if isinstance(item.get('ratingScore'), dict) else 0,
                    'seller': item.get('merchant', {}).get('name', '') if isinstance(item.get('merchant'), dict) else ''
                }

                products.append(product)

            except Exception as e:
                continue

        return products

    def _extract_products_from_state(self, soup: BeautifulSoup) -> List[Dict]:
        """__SEARCH_APP_INITIAL_STATE__ JavaScript değişkeninden ürünleri çıkar"""
        products = []

        # Script tagları içinde state data'yı ara
        for script in soup.find_all('script'):
            if script.string and '__SEARCH_APP_INITIAL_STATE__' in script.string:
                import re
                # State JSON'ı çıkar
                match = re.search(r'window.__SEARCH_APP_INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        state_data = json.loads(match.group(1))
                        # Ürünleri bul
                        products = self._find_products_in_state(state_data)
                        if products:
                            return products
                    except Exception as e:
                        print(f"    ⚠️ State parse hatası: {str(e)[:50]}")
                break

        return products

    def _find_products_in_state(self, obj, depth=0) -> List[Dict]:
        """State objesi içinde ürünleri recursive olarak ara"""
        if depth > 5:
            return []

        if isinstance(obj, dict):
            # products anahtarını ara
            if 'products' in obj:
                product_list = obj['products']
                if isinstance(product_list, list) and product_list:
                    # Ürünleri parse et
                    return self._parse_state_products(product_list)

            # Diğer anahtarlarda ara
            for key, value in obj.items():
                result = self._find_products_in_state(value, depth + 1)
                if result:
                    return result

        elif isinstance(obj, list):
            for item in obj:
                result = self._find_products_in_state(item, depth + 1)
                if result:
                    return result

        return []

    def _parse_state_products(self, product_list: List) -> List[Dict]:
        """State'ten gelen ürün listesini parse et"""
        products = []

        for item in product_list:
            try:
                # Fiyat bilgisini al
                price = 0
                if 'price' in item and isinstance(item['price'], dict):
                    price_data = item['price']
                    # İndirimli fiyat varsa onu kullan, yoksa normal fiyat
                    price = price_data.get('discountedPrice', price_data.get('sellingPrice', 0))

                product = {
                    'id': str(item.get('id', '')),
                    'name': item.get('name', ''),
                    'brand': item.get('brand', {}).get('name', '') if isinstance(item.get('brand'), dict) else '',
                    'price': float(price) if price else 0,
                    'url': urljoin(self.base_url, item.get('url', '')),
                    'image': f"https://cdn.dsmcdn.com/{item.get('images', [''])[0]}" if item.get('images') else '',
                    'rating': item.get('ratingScore', {}).get('averageRating', 0) if isinstance(item.get('ratingScore'), dict) else 0,
                    'review_count': item.get('ratingScore', {}).get('totalCount', 0) if isinstance(item.get('ratingScore'), dict) else 0,
                    'seller': item.get('merchantId', '')  # Merchant ID'yi kullan
                }

                # En azından ismi ve fiyatı olan ürünleri ekle
                if product['name'] and product['price'] > 0:
                    products.append(product)

            except Exception as e:
                continue

        return products

    def _parse_html_products(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """HTML'den ürünleri parse et"""
        products = []

        # Trendyol ürün kartlarını bul
        selectors = [
            'div.p-card-wrppr',
            'div.product-card',
            'div.prdct-cntnr-wrppr',
            'article.product-card',
            'div[data-id]'
        ]

        product_cards = []
        for selector in selectors:
            product_cards = soup.select(selector)
            if product_cards:
                break

        for card in product_cards:
            try:
                # Ürün bilgilerini çıkar
                product = {}

                # ID
                product['id'] = card.get('data-id', '')

                # İsim
                name_elem = card.select_one('.prdct-desc-cntnr-name, .product-name, span.prdct-desc-cntnr-ttl, span.prdct-desc-cntnr-ttl-w, .product-desc-name')
                if not name_elem:
                    # Title attribute'ından al
                    product['name'] = card.get('title', '')
                else:
                    product['name'] = name_elem.get_text(strip=True)

                # Marka
                brand_elem = card.select_one('.prdct-desc-cntnr-brand, .product-brand')
                product['brand'] = brand_elem.get_text(strip=True) if brand_elem else ''

                # Fiyat
                price_elem = card.select_one('.prc-box-dscntd, .price-value, .prc-box-sllng')
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

                # Rating
                rating_elem = card.select_one('.ratings, .rating-score')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    try:
                        product['rating'] = float(rating_text.replace(',', '.'))
                    except:
                        product['rating'] = 0
                else:
                    product['rating'] = 0

                # Satıcı
                seller_elem = card.select_one('.merchant-name, .seller-name')
                product['seller'] = seller_elem.get_text(strip=True) if seller_elem else ''

                # Review count
                review_elem = card.select_one('.rating-count, .review-count')
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    # Parantez içindeki sayıyı al
                    match = re.search(r'\d+', review_text)
                    product['review_count'] = int(match.group()) if match else 0
                else:
                    product['review_count'] = 0

                # En azından ismi olan ürünleri ekle
                if product['name']:
                    products.append(product)

            except Exception as e:
                continue

        return products


def test_scraper():
    """Test fonksiyonu"""
    scraper = TrendyolScraper()

    # Test URL - Kadın giyim en çok satanlar
    test_url = "https://www.trendyol.com/kadin-giyim-x-g1-c82?sst=BEST_SELLER"

    print(f"🔍 Test URL: {test_url}")
    products = scraper.scrape_products(test_url, max_pages=1)

    print(f"\n✅ {len(products)} ürün bulundu!")

    # İlk 5 ürünü göster
    for i, product in enumerate(products[:5], 1):
        print(f"\n{i}. {product['name'][:60]}...")
        print(f"   Marka: {product['brand']}")
        print(f"   Fiyat: {product['price']} TL")
        print(f"   Rating: {product['rating']} ({product['review_count']} yorum)")
        print(f"   URL: {product['url'][:60]}...")

    return products


if __name__ == "__main__":
    test_scraper()