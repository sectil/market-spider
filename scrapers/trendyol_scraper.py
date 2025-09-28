"""
Trendyol Scraper
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_scraper import BaseScraper
import re
import json


class TrendyolScraper(BaseScraper):
    """Trendyol.com scraper"""

    def find_product_elements(self, soup: BeautifulSoup) -> List:
        """Trendyol'da ürün elementlerini bul"""
        # Farklı container'ları dene
        selectors = [
            'div[class*="p-card-wrppr"]',
            'div[class*="product-card"]',
            'div[class*="prdct-cntnr-wrppr"]',
            'article[class*="product"]',
            'div[data-id]'  # Ürün ID'si olan divler
        ]

        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements

        return []

    def extract_product_data(self, element, rank: int) -> Optional[Dict]:
        """Trendyol'dan ürün verilerini çıkar"""
        try:
            product_data = {}

            # Ürün ID
            product_id = element.get('data-id', '')
            if not product_id:
                # ID'yi link'ten çıkarmaya çalış
                link = element.select_one('a')
                if link and link.get('href'):
                    product_id = self.extract_product_id(link['href'])

            product_data['id'] = product_id

            # Ürün başlığı ve linki
            title_elem = element.select_one('span[class*="prdct-desc-cntnr-name"], '
                                           'span[class*="product-name"], '
                                           'div[class*="product-title"]')
            if title_elem:
                product_data['title'] = self.clean_text(title_elem.text)

            # Marka
            brand_elem = element.select_one('span[class*="prdct-desc-cntnr-ttl"], '
                                           'span[class*="product-brand"]')
            if brand_elem:
                product_data['brand'] = self.clean_text(brand_elem.text)

            # URL
            link_elem = element.select_one('a')
            if link_elem and link_elem.get('href'):
                product_data['url'] = self.make_absolute_url(link_elem['href'])

            # Resim
            img_elem = element.select_one('img')
            if img_elem:
                product_data['image'] = img_elem.get('src') or img_elem.get('data-src')

            # Fiyat
            price_elem = element.select_one('div[class*="price-value"], '
                                           'span[class*="prc-box-dscntd"], '
                                           'div[class*="product-price"]')
            if price_elem:
                product_data['price'] = self.parse_price(price_elem.text)

            # Orijinal fiyat
            original_price_elem = element.select_one('span[class*="prc-box-orgnl"], '
                                                    'del[class*="price"]')
            if original_price_elem:
                product_data['original_price'] = self.parse_price(original_price_elem.text)

            # Rating ve yorumlar
            rating_elem = element.select_one('div[class*="rating-score"], '
                                            'span[class*="rating"]')
            if rating_elem:
                rating_text = self.clean_text(rating_elem.text)
                try:
                    product_data['rating'] = float(rating_text.replace(',', '.'))
                except:
                    pass

            # Yorum sayısı
            review_elem = element.select_one('span[class*="rating-count"], '
                                            'span[class*="review-count"]')
            if review_elem:
                review_text = re.findall(r'\d+', review_elem.text)
                if review_text:
                    product_data['review_count'] = int(review_text[0])

            # Satıcı bilgisi
            seller_elem = element.select_one('span[class*="seller-name"], '
                                            'div[class*="merchant-name"]')
            if seller_elem:
                product_data['seller'] = self.clean_text(seller_elem.text)

            # Kargo bilgisi
            shipping_elem = element.select_one('div[class*="shipment"], '
                                              'span[class*="free-shipping"]')
            if shipping_elem:
                product_data['free_shipping'] = True

            # Kategori
            product_data['category'] = self.categorize_product(
                product_data.get('title', ''),
                product_data.get('brand', '')
            )

            # Rank
            product_data['rank'] = rank

            return product_data

        except Exception as e:
            print(f"Ürün verisi çıkarılamadı: {e}")
            return None

    def scrape_best_sellers_api(self, category_id: str = None) -> List[Dict]:
        """Trendyol API üzerinden en çok satan ürünleri al"""
        products = []

        # Trendyol'un internal API'si
        api_url = "https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll"

        params = {
            'sst': 'BEST_SELLER',  # En çok satanlar
            'pi': 1,  # Sayfa
            'culture': 'tr-TR',
            'userGenderId': '',
            'pId': '',
            'scoringAlgorithmId': '',
            'categoryRelevancyEnabled': 'false',
            'isLegalRequirementConfirmed': 'false',
            'searchStrategyType': 'DEFAULT',
            'productStampType': 'TypeA',
            'offset': 0,
            'channelId': 1
        }

        if category_id:
            params['wb'] = category_id  # Kategori ID

        try:
            response = self.scraper.get(api_url, params=params, headers=self.headers)
            data = response.json()

            if 'result' in data and 'products' in data['result']:
                for rank, product in enumerate(data['result']['products'][:100], 1):
                    product_data = {
                        'id': product.get('id'),
                        'title': product.get('name'),
                        'brand': product.get('brand', {}).get('name'),
                        'url': f"https://www.trendyol.com{product.get('url')}",
                        'image': f"https://cdn.dsmcdn.com{product.get('images', [{}])[0].get('url', '')}",
                        'price': product.get('price', {}).get('sellingPrice'),
                        'original_price': product.get('price', {}).get('originalPrice'),
                        'rating': product.get('ratingScore', {}).get('averageRating'),
                        'review_count': product.get('ratingScore', {}).get('totalRatingCount'),
                        'seller': product.get('merchant', {}).get('name'),
                        'category': product.get('categoryName'),
                        'rank': rank,
                        'in_stock': not product.get('hasStock', True)
                    }
                    products.append(product_data)

        except Exception as e:
            print(f"API hatası: {e}")
            # Fallback to web scraping
            return self.scrape_best_sellers("https://www.trendyol.com/en-cok-satanlar")

        return products


if __name__ == "__main__":
    # Test
    from config import ECOMMERCE_SITES

    scraper = TrendyolScraper(ECOMMERCE_SITES['trendyol'])
    products = scraper.scrape_best_sellers_api()

    print(f"Toplam {len(products)} ürün bulundu")
    if products:
        print("\nİlk 5 ürün:")
        for p in products[:5]:
            print(f"#{p['rank']}: {p['title']} - {p['price']} TL")

    scraper.close()