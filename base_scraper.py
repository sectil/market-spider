"""
Base Scraper - Tüm site scraper'larının temel sınıfı
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cloudscraper
from urllib.parse import urljoin, urlparse
import re
import json

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """Tüm e-ticaret site scraper'larının ana sınıfı"""

    def __init__(self, site_config: Dict[str, Any], use_selenium: bool = False):
        self.site_config = site_config
        self.site_name = site_config.get('name')
        self.base_url = site_config.get('base_url')
        self.headers = site_config.get('headers', {})
        self.rate_limit = site_config.get('rate_limit', 2)
        self.use_selenium = use_selenium
        self.driver = None
        self.session = None

        # CloudScraper for Cloudflare protected sites
        self.scraper = cloudscraper.create_scraper()

    def setup_selenium(self) -> webdriver.Chrome:
        """Selenium WebDriver kurulumu"""
        options = Options()
        options.add_argument('--headless')  # Arka planda çalış
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument(f'user-agent={self.headers.get("User-Agent")}')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        return self.driver

    def get_page_content(self, url: str) -> Optional[str]:
        """Sayfa içeriğini al (requests veya selenium ile)"""
        try:
            if self.use_selenium:
                if not self.driver:
                    self.setup_selenium()

                self.driver.get(url)
                # Sayfanın yüklenmesini bekle
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                time.sleep(2)  # JavaScript render için ek süre
                return self.driver.page_source
            else:
                # CloudScraper kullan (Cloudflare koruması için)
                response = self.scraper.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                return response.text

        except Exception as e:
            logger.error(f"Sayfa alınamadı {url}: {str(e)}")
            return None

    def parse_price(self, price_text: str) -> Optional[float]:
        """Fiyat metnini float'a çevir"""
        try:
            # Türkçe para birimi ve ayraçları temizle
            price_text = price_text.replace('TL', '').replace('₺', '')
            price_text = price_text.replace('.', '').replace(',', '.')
            price_text = re.sub(r'[^\d.,]', '', price_text)
            return float(price_text)
        except:
            return None

    def extract_product_id(self, url: str) -> str:
        """URL'den ürün ID'sini çıkar"""
        # Her site için override edilmeli
        return url.split('/')[-1].split('?')[0]

    def categorize_product(self, title: str, category_text: str = "") -> str:
        """Ürünü kategorize et"""
        text = (title + " " + category_text).lower()

        # Basit keyword matching
        categories = {
            "elektronik": ["telefon", "laptop", "tablet", "bilgisayar", "televizyon",
                          "kulaklık", "hoparlör", "kamera", "playstation", "xbox"],
            "giyim": ["elbise", "pantolon", "tişört", "gömlek", "mont", "ceket",
                     "ayakkabı", "çanta", "etek", "kazak", "sweatshirt"],
            "ev_yasam": ["mobilya", "halı", "perde", "yatak", "yastık", "battaniye",
                        "masa", "sandalye", "dolap", "koltuk"],
            "kozmetik": ["parfüm", "ruj", "makyaj", "krem", "şampuan", "saç",
                        "cilt", "göz", "fondöten", "maskara"],
            "kitap": ["kitap", "roman", "hikaye", "şiir", "dergi", "ansiklopedi"],
            "bebek": ["bebek", "bezi", "mama", "emzik", "biberon", "bebek arabası"],
            "spor": ["spor", "fitness", "yoga", "pilates", "koşu", "futbol", "basketbol"],
            "gida": ["gıda", "yemek", "içecek", "kahve", "çay", "atıştırmalık", "vitamin"]
        }

        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category

        return "diger"

    def scrape_best_sellers(self, url: str) -> List[Dict]:
        """En çok satan ürünleri topla"""
        products = []
        content = self.get_page_content(url)

        if not content:
            return products

        soup = BeautifulSoup(content, 'lxml')

        # Bu method her site için override edilmeli
        product_elements = self.find_product_elements(soup)

        for rank, element in enumerate(product_elements[:100], 1):  # İlk 100 ürün
            product_data = self.extract_product_data(element, rank)
            if product_data:
                products.append(product_data)

            # Rate limiting
            time.sleep(random.uniform(0.5, self.rate_limit))

        return products

    def find_product_elements(self, soup: BeautifulSoup) -> List:
        """Ürün elementlerini bul - Override edilmeli"""
        raise NotImplementedError("Bu method her site için özelleştirilmeli")

    def extract_product_data(self, element, rank: int) -> Optional[Dict]:
        """Ürün verilerini çıkar - Override edilmeli"""
        raise NotImplementedError("Bu method her site için özelleştirilmeli")

    def clean_text(self, text: str) -> str:
        """Metni temizle"""
        if not text:
            return ""
        return ' '.join(text.split()).strip()

    def make_absolute_url(self, url: str) -> str:
        """Relative URL'yi absolute yap"""
        if not url:
            return ""
        return urljoin(self.base_url, url)

    def close(self):
        """Kaynakları temizle"""
        if self.driver:
            self.driver.quit()
            self.driver = None


class ProductNormalizer:
    """Farklı sitelerden gelen ürün verilerini normalize et"""

    @staticmethod
    def normalize_product(product_data: Dict, site_name: str) -> Dict:
        """Ürün verisini standart formata çevir"""

        normalized = {
            'site_name': site_name,
            'product_id': f"{site_name}_{product_data.get('id', '')}",
            'name': product_data.get('title', ''),
            'brand': ProductNormalizer.extract_brand(product_data.get('title', '')),
            'category': product_data.get('category', 'diger'),
            'sub_category': product_data.get('sub_category', ''),
            'product_url': product_data.get('url', ''),
            'image_url': product_data.get('image', ''),
            'price': product_data.get('price', 0),
            'original_price': product_data.get('original_price'),
            'discount_percentage': ProductNormalizer.calculate_discount(
                product_data.get('price'),
                product_data.get('original_price')
            ),
            'currency': 'TRY',
            'in_stock': product_data.get('in_stock', True),
            'seller_name': product_data.get('seller', ''),
            'seller_rating': product_data.get('seller_rating'),
            'rank_position': product_data.get('rank', 0),
            'total_reviews': product_data.get('review_count', 0),
            'average_rating': product_data.get('rating', 0),
            'sales_count': product_data.get('sales_count'),
            'list_type': 'best_sellers'
        }

        return normalized

    @staticmethod
    def extract_brand(title: str) -> str:
        """Başlıktan marka adını çıkar"""
        # Bilinen markalar listesi
        known_brands = [
            'Samsung', 'Apple', 'iPhone', 'Xiaomi', 'Huawei', 'LG', 'Sony',
            'Lenovo', 'HP', 'Dell', 'Asus', 'MSI', 'Acer', 'Toshiba',
            'Nike', 'Adidas', 'Puma', 'Reebok', 'New Balance', 'Converse',
            'Zara', 'H&M', 'Mango', 'LC Waikiki', 'Koton', 'DeFacto',
            'Philips', 'Bosch', 'Arçelik', 'Beko', 'Vestel', 'Siemens',
            'L\'Oreal', 'Maybelline', 'MAC', 'Nivea', 'Dove', 'Gillette'
        ]

        title_lower = title.lower()
        for brand in known_brands:
            if brand.lower() in title_lower:
                return brand

        # İlk kelimeyi marka olarak al
        first_word = title.split()[0] if title else ""
        return first_word

    @staticmethod
    def calculate_discount(price: float, original_price: float) -> float:
        """İndirim yüzdesini hesapla"""
        if not original_price or not price or original_price <= price:
            return 0
        return round(((original_price - price) / original_price) * 100, 2)