"""
Market Spider - Ana Kontrol Modülü
"""

import sys
import os
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import schedule
import threading

from sqlalchemy.orm import Session
from database import init_database, get_db, Product, PriceHistory, RankingHistory, ScrapeLog
from config import ECOMMERCE_SITES, SCRAPING, SCHEDULER
from base_scraper import ProductNormalizer

# Scraper'ları import et
from scrapers.trendyol_scraper import TrendyolScraper
# from scrapers.hepsiburada_scraper import HepsiburadaScraper  # TODO
# from scrapers.n11_scraper import N11Scraper  # TODO

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarketSpider:
    """Ana spider kontrol sınıfı"""

    def __init__(self):
        self.scrapers = {}
        self.init_scrapers()
        self.db = next(get_db())

    def init_scrapers(self):
        """Tüm scraper'ları başlat"""
        # Mevcut scraper'ları ekle
        self.scrapers['trendyol'] = TrendyolScraper

        # TODO: Diğer scraper'lar eklenecek
        # self.scrapers['hepsiburada'] = HepsiburadaScraper
        # self.scrapers['n11'] = N11Scraper

        logger.info(f"✅ {len(self.scrapers)} scraper yüklendi")

    def scrape_site(self, site_key: str) -> Dict:
        """Tek bir siteyi scrape et"""
        start_time = time.time()
        result = {
            'site': site_key,
            'products_found': 0,
            'products_updated': 0,
            'errors': [],
            'duration': 0
        }

        try:
            site_config = ECOMMERCE_SITES.get(site_key)
            if not site_config:
                raise ValueError(f"Site config bulunamadı: {site_key}")

            scraper_class = self.scrapers.get(site_key)
            if not scraper_class:
                raise ValueError(f"Scraper bulunamadı: {site_key}")

            logger.info(f"🔍 {site_key} scraping başladı...")
            scraper = scraper_class(site_config)

            all_products = []

            # En çok satanlar listelerini tara
            for url in site_config['best_sellers_urls']:
                try:
                    if 'api' in site_key:  # API destekli siteler
                        products = scraper.scrape_best_sellers_api()
                    else:
                        full_url = f"{site_config['base_url']}{url}" if not url.startswith('http') else url
                        products = scraper.scrape_best_sellers(full_url)

                    all_products.extend(products)
                    logger.info(f"  ✓ {len(products)} ürün bulundu: {url}")

                except Exception as e:
                    logger.error(f"  ✗ Hata {url}: {str(e)}")
                    result['errors'].append(str(e))

                time.sleep(site_config.get('rate_limit', 2))

            # Veritabanına kaydet
            for product_data in all_products:
                try:
                    normalized = ProductNormalizer.normalize_product(product_data, site_key)
                    self.save_product_to_db(normalized)
                    result['products_updated'] += 1
                except Exception as e:
                    logger.error(f"DB kayıt hatası: {e}")

            result['products_found'] = len(all_products)
            scraper.close()

        except Exception as e:
            logger.error(f"Site scraping hatası {site_key}: {str(e)}")
            result['errors'].append(str(e))

        result['duration'] = time.time() - start_time

        # Log kaydet
        self.save_scrape_log(site_key, result)

        logger.info(f"✅ {site_key} tamamlandı: {result['products_found']} ürün, "
                   f"{result['duration']:.2f} saniye")

        return result

    def save_product_to_db(self, product_data: Dict):
        """Ürünü veritabanına kaydet veya güncelle"""
        try:
            # Ürün var mı kontrol et
            product = self.db.query(Product).filter_by(
                product_id=product_data['product_id'],
                site_name=product_data['site_name']
            ).first()

            if not product:
                # Yeni ürün ekle
                product = Product(
                    product_id=product_data['product_id'],
                    name=product_data['name'],
                    brand=product_data['brand'],
                    category=product_data['category'],
                    sub_category=product_data['sub_category'],
                    site_name=product_data['site_name'],
                    product_url=product_data['product_url'],
                    image_url=product_data['image_url']
                )
                self.db.add(product)
                self.db.flush()

            # Fiyat geçmişi ekle
            price_history = PriceHistory(
                product_id=product.id,
                price=product_data['price'],
                original_price=product_data.get('original_price'),
                discount_percentage=product_data.get('discount_percentage'),
                currency=product_data['currency'],
                in_stock=product_data['in_stock'],
                seller_name=product_data.get('seller_name'),
                seller_rating=product_data.get('seller_rating')
            )
            self.db.add(price_history)

            # Ranking geçmişi ekle
            ranking_history = RankingHistory(
                product_id=product.id,
                rank_position=product_data['rank_position'],
                total_reviews=product_data.get('total_reviews'),
                average_rating=product_data.get('average_rating'),
                sales_count=product_data.get('sales_count'),
                list_type=product_data['list_type']
            )
            self.db.add(ranking_history)

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            raise e

    def save_scrape_log(self, site_name: str, result: Dict):
        """Scrape log'u kaydet"""
        try:
            log = ScrapeLog(
                site_name=site_name,
                status='success' if not result['errors'] else 'failed',
                products_found=result['products_found'],
                products_updated=result['products_updated'],
                error_message='; '.join(result['errors']) if result['errors'] else None,
                duration_seconds=result['duration']
            )
            self.db.add(log)
            self.db.commit()
        except:
            self.db.rollback()

    def scrape_all_sites(self):
        """Tüm siteleri paralel olarak scrape et"""
        logger.info("🚀 Tüm siteler için scraping başlıyor...")
        start_time = time.time()

        results = []
        with ThreadPoolExecutor(max_workers=SCRAPING['max_workers']) as executor:
            futures = {
                executor.submit(self.scrape_site, site_key): site_key
                for site_key in self.scrapers.keys()
            }

            for future in as_completed(futures):
                site_key = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Thread hatası {site_key}: {e}")

        total_duration = time.time() - start_time
        total_products = sum(r['products_found'] for r in results)

        logger.info(f"✅ Tüm scraping tamamlandı: {total_products} ürün, "
                   f"{total_duration:.2f} saniye")

        return results

    def get_statistics(self) -> Dict:
        """İstatistikleri al"""
        stats = {
            'total_products': self.db.query(Product).count(),
            'total_price_records': self.db.query(PriceHistory).count(),
            'sites_tracked': len(self.scrapers),
            'last_scrape': None
        }

        last_log = self.db.query(ScrapeLog).order_by(ScrapeLog.timestamp.desc()).first()
        if last_log:
            stats['last_scrape'] = last_log.timestamp.isoformat()

        return stats


def run_scheduled_scraping():
    """Zamanlanmış scraping görevi"""
    spider = MarketSpider()
    spider.scrape_all_sites()


def start_scheduler():
    """Scheduler'ı başlat"""
    if not SCHEDULER['enabled']:
        logger.info("Scheduler devre dışı")
        return

    # Her X saatte bir çalıştır
    schedule.every(SCHEDULER['interval_hours']).hours.do(run_scheduled_scraping)

    logger.info(f"📅 Scheduler başlatıldı: Her {SCHEDULER['interval_hours']} saatte bir çalışacak")

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et

    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()


def main():
    """Ana fonksiyon"""
    print("""
    ╔══════════════════════════════════════╗
    ║     🕷️  MARKET SPIDER v1.0  🕷️        ║
    ║   Türkiye E-Ticaret Fiyat Takibi    ║
    ╚══════════════════════════════════════╝
    """)

    # Database'i başlat
    init_database()

    spider = MarketSpider()

    while True:
        print("\n📋 MENÜ:")
        print("1. Tüm siteleri tara")
        print("2. Tek site tara")
        print("3. İstatistikleri göster")
        print("4. Scheduler'ı başlat")
        print("5. Çıkış")

        choice = input("\nSeçiminiz: ")

        if choice == '1':
            spider.scrape_all_sites()

        elif choice == '2':
            print("\nMevcut siteler:")
            for i, site in enumerate(spider.scrapers.keys(), 1):
                print(f"{i}. {site}")
            site_idx = int(input("Site numarası: ")) - 1
            site_key = list(spider.scrapers.keys())[site_idx]
            spider.scrape_site(site_key)

        elif choice == '3':
            stats = spider.get_statistics()
            print("\n📊 İSTATİSTİKLER:")
            print(f"Toplam Ürün: {stats['total_products']}")
            print(f"Toplam Fiyat Kaydı: {stats['total_price_records']}")
            print(f"Takip Edilen Site: {stats['sites_tracked']}")
            print(f"Son Tarama: {stats['last_scrape']}")

        elif choice == '4':
            start_scheduler()
            print("Scheduler başlatıldı. Ana menü aktif...")

        elif choice == '5':
            print("Çıkış yapılıyor...")
            break


if __name__ == "__main__":
    main()