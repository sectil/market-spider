#!/usr/bin/env python3
"""
📡 Trendyol API Endpoint Scraper
Direkt API çağrıları ile veri toplama
"""

import json
import time
import sqlite3
import requests
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
import cloudscraper

class TrendyolAPIScraper:
    def __init__(self):
        self.conn = sqlite3.connect('market_spider.db')
        self.cursor = self.conn.cursor()
        self.session = cloudscraper.create_scraper()

        # Bilinen Trendyol API endpoint'leri
        self.endpoints = [
            # Ana kategori endpoint'leri
            {
                'url': 'https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll/sr',
                'params': {'q': 'cok-satanlar', 'qt': 'cok-satanlar', 'st': 'cok-satanlar', 'os': '1', 'pi': '1'},
                'type': 'search'
            },
            {
                'url': 'https://public.trendyol.com/discovery-web-websfxaggregatorsfx-santral/api/v1/best-selling',
                'params': {'culture': 'tr-TR', 'storefrontId': '1'},
                'type': 'bestsellers'
            },
            {
                'url': 'https://public-mdc.trendyol.com/discovery-web-recogw-service/api/favorites/counts',
                'params': {},
                'type': 'favorites'
            },
            # Mobil API endpoint'leri (genelde daha az korumalı)
            {
                'url': 'https://api.trendyol.com/webapicontent/v2/best-seller-products',
                'params': {'channelId': '1', 'page': '0', 'size': '50'},
                'type': 'mobile_bestsellers'
            },
            {
                'url': 'https://gateway.trendyol.com/discovery-web-productgw-service/api/productDetail',
                'params': {},
                'type': 'product_detail'
            },
            # GraphQL endpoint
            {
                'url': 'https://gateway.trendyol.com/graphql',
                'type': 'graphql',
                'method': 'POST'
            }
        ]

        # Common headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Referer': 'https://www.trendyol.com/',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'x-application-id': 'web',
            'x-storefront-id': 'TR',
            'x-session-id': 'web-' + str(int(time.time() * 1000))
        }

    def fetch_from_endpoint(self, endpoint: Dict) -> List[Dict]:
        """Belirli bir endpoint'ten veri çek"""
        products = []

        try:
            print(f"\n🔌 Deneniyor: {endpoint['url']}")

            if endpoint.get('method') == 'POST':
                # GraphQL sorgusu
                if endpoint['type'] == 'graphql':
                    query = self.get_graphql_query()
                    response = self.session.post(
                        endpoint['url'],
                        json={'query': query, 'variables': {'first': 50}},
                        headers=self.headers,
                        timeout=10
                    )
                else:
                    response = self.session.post(
                        endpoint['url'],
                        json=endpoint.get('data', {}),
                        headers=self.headers,
                        timeout=10
                    )
            else:
                # GET request
                response = self.session.get(
                    endpoint['url'],
                    params=endpoint.get('params', {}),
                    headers=self.headers,
                    timeout=10
                )

            if response.status_code == 200:
                data = response.json()
                products = self.parse_response(data, endpoint['type'])
                print(f"   ✅ {len(products)} ürün bulundu")
            else:
                print(f"   ❌ Status: {response.status_code}")

        except Exception as e:
            print(f"   ❌ Hata: {e}")

        return products

    def parse_response(self, data: Dict, endpoint_type: str) -> List[Dict]:
        """API yanıtını parse et"""
        products = []

        try:
            if endpoint_type == 'search':
                # Arama sonuçları
                if 'result' in data and 'products' in data['result']:
                    items = data['result']['products']
                elif 'products' in data:
                    items = data['products']
                else:
                    items = []

                for item in items[:50]:
                    product = self.parse_product(item)
                    if product:
                        products.append(product)

            elif endpoint_type == 'bestsellers' or endpoint_type == 'mobile_bestsellers':
                # Çok satanlar
                if 'result' in data:
                    items = data['result'] if isinstance(data['result'], list) else []
                elif 'content' in data:
                    items = data['content']
                else:
                    items = []

                for item in items[:50]:
                    product = self.parse_product(item)
                    if product:
                        products.append(product)

            elif endpoint_type == 'graphql':
                # GraphQL yanıtı
                if 'data' in data and 'products' in data['data']:
                    edges = data['data']['products'].get('edges', [])
                    for edge in edges[:50]:
                        node = edge.get('node', {})
                        product = self.parse_product(node)
                        if product:
                            products.append(product)

        except Exception as e:
            print(f"Parse hatası: {e}")

        return products

    def parse_product(self, item: Dict) -> Dict:
        """Ürün verisini standart formata çevir"""
        try:
            # Farklı API formatlarını destekle
            name = item.get('name') or item.get('title') or item.get('productName', '')

            # Marka bilgisi
            brand = ''
            if 'brand' in item:
                if isinstance(item['brand'], dict):
                    brand = item['brand'].get('name', '')
                else:
                    brand = item['brand']
            elif 'brandName' in item:
                brand = item['brandName']

            # Fiyat bilgisi
            price = 0.0
            if 'price' in item:
                if isinstance(item['price'], dict):
                    price = float(item['price'].get('sellingPrice', 0))
                else:
                    price = float(item['price'])
            elif 'sellingPrice' in item:
                price = float(item['sellingPrice'])

            # Rating bilgisi
            rating = 0.0
            if 'ratingScore' in item:
                if isinstance(item['ratingScore'], dict):
                    rating = float(item['ratingScore'].get('averageRating', 0))
                else:
                    rating = float(item['ratingScore'])
            elif 'rating' in item:
                rating = float(item['rating'])

            # URL oluştur
            url = ''
            if 'url' in item:
                url = f"https://www.trendyol.com{item['url']}"
            elif 'id' in item:
                url = f"https://www.trendyol.com/p/{item['id']}"

            if name:
                return {
                    'name': name,
                    'brand': brand,
                    'price': price,
                    'rating': rating,
                    'review_count': int(item.get('reviewCount', 0)),
                    'url': url,
                    'image_url': item.get('imageUrl', ''),
                    'is_promoted': item.get('isPromoted', False),
                    'discount_rate': item.get('discountRate', 0)
                }
        except:
            pass
        return None

    def get_graphql_query(self) -> str:
        """GraphQL sorgusu"""
        return """
        query GetBestSellers($first: Int!, $category: String) {
            products(first: $first, orderBy: BEST_SELLER, category: $category) {
                edges {
                    node {
                        id
                        name
                        brand {
                            name
                        }
                        price {
                            sellingPrice
                            originalPrice
                            discountRate
                        }
                        rating {
                            averageRating
                            totalCount
                        }
                        url
                        imageUrl
                        isPromoted
                        isFavorite
                        hasStock
                    }
                }
                pageInfo {
                    hasNextPage
                    endCursor
                }
            }
        }
        """

    def fetch_product_reviews(self, product_id: str) -> List[Dict]:
        """Ürün yorumlarını çek"""
        reviews = []

        try:
            # Yorum API'si
            url = f"https://public-mdc.trendyol.com/discovery-web-socialgw-service/api/review/discussions/{product_id}"

            params = {
                'page': 0,
                'size': 20,
                'order': 'most_helpful'
            }

            response = self.session.get(url, params=params, headers=self.headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                discussions = data.get('result', {}).get('discussions', [])

                for discussion in discussions:
                    review = {
                        'reviewer_name': discussion.get('userFullName', 'Anonim'),
                        'rating': float(discussion.get('rate', 0)),
                        'review_text': discussion.get('comment', ''),
                        'review_date': discussion.get('commentDateISOType', ''),
                        'helpful_count': int(discussion.get('helpfulCount', 0))
                    }
                    reviews.append(review)

        except Exception as e:
            print(f"Yorum çekme hatası: {e}")

        return reviews

    def save_to_database(self, products: List[Dict]):
        """Ürünleri veritabanına kaydet"""
        saved_count = 0

        for product in products:
            try:
                # Ürünü kaydet
                self.cursor.execute("""
                    INSERT OR REPLACE INTO products (
                        name, brand, price, rating, review_count,
                        url, site_name, in_stock, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product['name'],
                    product['brand'],
                    product['price'],
                    product['rating'],
                    product['review_count'],
                    product['url'],
                    'Trendyol',
                    1,
                    datetime.now(),
                    datetime.now()
                ))

                saved_count += 1

                # URL'den ürün ID'sini çıkar ve yorumları çek
                if '-p-' in product['url']:
                    product_id = product['url'].split('-p-')[-1].split('?')[0]
                    reviews = self.fetch_product_reviews(product_id)

                    db_product_id = self.cursor.lastrowid
                    for review in reviews:
                        self.cursor.execute("""
                            INSERT OR REPLACE INTO product_reviews (
                                product_id, reviewer_name, rating, review_text,
                                review_date, helpful_count, sentiment_score, scraped_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            db_product_id,
                            review['reviewer_name'],
                            review['rating'],
                            review['review_text'],
                            review['review_date'],
                            review['helpful_count'],
                            self.calculate_sentiment(review['review_text']),
                            datetime.now()
                        ))

            except Exception as e:
                print(f"Kaydetme hatası: {e}")

        self.conn.commit()
        return saved_count

    def calculate_sentiment(self, text: str) -> float:
        """Basit sentiment analizi"""
        if not text:
            return 0.5

        positive_words = ['harika', 'mükemmel', 'güzel', 'kaliteli', 'memnun', 'tavsiye', 'beğendim', 'başarılı']
        negative_words = ['kötü', 'berbat', 'pişman', 'bozuk', 'kalitesiz', 'rezalet', 'beğenmedim', 'başarısız']

        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)

        if pos_count + neg_count == 0:
            return 0.5
        return pos_count / (pos_count + neg_count)

    def try_alternative_apis(self):
        """Alternatif API'leri dene"""
        alternative_apis = [
            # Trendyol partner/satıcı API'leri
            'https://sellercenter-api.trendyol.com/api/products/best-sellers',
            'https://partner-api.trendyol.com/integration/products/top-selling',

            # Analytics endpoint'leri
            'https://analytics.trendyol.com/api/trending-products',
            'https://data.trendyol.com/api/market-insights/best-sellers',

            # Mobil özel endpoint'ler
            'https://m-api.trendyol.com/mobile/v2/bestsellers',
            'https://app-api.trendyol.com/discover/trending',

            # Widget API'leri
            'https://widget.trendyol.com/api/recommendation/bestsellers',
            'https://cdn.trendyol.com/discovery/widget/best-selling.json'
        ]

        for api_url in alternative_apis:
            try:
                response = self.session.get(api_url, headers=self.headers, timeout=5)
                if response.status_code == 200:
                    print(f"✅ Çalışan API bulundu: {api_url}")
                    return response.json()
            except:
                continue

        return None

    def run(self):
        """Ana çalıştırma fonksiyonu"""
        print("="*60)
        print("📡 TRENDYOL API ENDPOINT SCRAPER")
        print("="*60)

        all_products = []

        # Ana endpoint'leri dene
        for endpoint in self.endpoints:
            products = self.fetch_from_endpoint(endpoint)
            all_products.extend(products)
            time.sleep(2)  # Rate limiting

        # Alternatif API'leri dene
        print("\n🔍 Alternatif API'ler deneniyor...")
        alt_data = self.try_alternative_apis()
        if alt_data:
            products = self.parse_response(alt_data, 'bestsellers')
            all_products.extend(products)

        # Unique ürünler
        unique_products = {p['name']: p for p in all_products}.values()

        if unique_products:
            # Veritabanına kaydet
            saved = self.save_to_database(list(unique_products))
            print(f"\n✅ {saved} ürün veritabanına kaydedildi")

            # CSV'ye kaydet
            df = pd.DataFrame(list(unique_products))
            df.to_csv('api_scraped_products.csv', index=False, encoding='utf-8')
            print(f"✅ CSV dosyası: api_scraped_products.csv")
        else:
            print("❌ Hiç ürün bulunamadı")

        # Özet
        total_products = self.cursor.execute("SELECT COUNT(*) FROM products WHERE site_name='Trendyol'").fetchone()[0]
        total_reviews = self.cursor.execute("SELECT COUNT(*) FROM product_reviews WHERE scraped_at IS NOT NULL").fetchone()[0]

        print("\n" + "="*60)
        print(f"📊 ÖZET:")
        print(f"   Toplam Trendyol ürünü: {total_products}")
        print(f"   Toplam gerçek yorum: {total_reviews}")
        print("="*60)

        self.conn.close()

if __name__ == "__main__":
    scraper = TrendyolAPIScraper()
    scraper.run()