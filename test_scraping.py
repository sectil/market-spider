#!/usr/bin/env python3
"""
Test scraping script - Veritabanındaki sitelerden veri çek
"""

from database import SessionLocal, SiteConfig, SiteUrl, Product
from scrapers.trendyol_scraper import TrendyolScraper
from datetime import datetime
import json
import time

def test_site_scraping():
    """Veritabanındaki aktif siteleri test et"""
    print("🕷️ Market Spider Test Başlıyor...")

    session = SessionLocal()

    try:
        # Aktif siteleri al
        active_sites = session.query(SiteConfig).filter_by(is_active=True).all()
        print(f"\n✅ {len(active_sites)} aktif site bulundu")

        for site in active_sites:
            print(f"\n{'='*60}")
            print(f"🌐 {site.site_name} test ediliyor...")
            print(f"   Base URL: {site.base_url}")

            # Site URL'lerini al
            site_urls = session.query(SiteUrl).filter_by(
                site_id=site.id,
                is_active=True
            ).order_by(SiteUrl.priority).all()

            print(f"   {len(site_urls)} URL bulundu")

            if site.site_key == 'trendyol':
                # Trendyol scraper config
                config = {
                    'base_url': site.base_url,
                    'headers': site.headers or {},
                    'use_selenium': site.use_selenium,
                    'rate_limit': site.rate_limit
                }
                scraper = TrendyolScraper(config)

                for url_config in site_urls[:2]:  # İlk 2 URL'yi test et
                    print(f"\n   📍 {url_config.url_type}: {url_config.description}")

                    try:
                        # Full URL oluştur - URL zaten tam URL olarak geldiği için direkt kullan
                        full_url = url_config.url_path
                        print(f"      URL: {full_url}")

                        # Scraping yap - API metodunu kullan
                        products = scraper.scrape_best_sellers_api()

                        print(f"   ✅ {len(products)} ürün bulundu")

                        # İlk 3 ürünü göster
                        for i, product in enumerate(products[:3], 1):
                            print(f"      {i}. {product.get('title', 'N/A')[:50]}...")
                            print(f"         Fiyat: {product.get('price', 'N/A')} TL")

                        # URL istatistiklerini güncelle
                        url_config.last_scraped = datetime.utcnow()
                        url_config.last_product_count = len(products)
                        url_config.total_scrape_count += 1
                        session.commit()

                        # Rate limiting
                        time.sleep(site.rate_limit)

                    except Exception as e:
                        print(f"   ❌ Hata: {str(e)}")

            else:
                print(f"   ⚠️ {site.site_key} scraper'ı henüz hazır değil")

        print(f"\n{'='*60}")
        print("✅ Test tamamlandı!")
        print("\n💡 Dashboard'u görmek için: http://localhost:8501")
        print("   Admin Panel'den yeni siteler ve URL'ler ekleyebilirsiniz!")

    except Exception as e:
        print(f"❌ Test hatası: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    test_site_scraping()