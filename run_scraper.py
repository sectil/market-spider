#!/usr/bin/env python3
"""
Web scraper'ı çalıştır ve ürünleri veritabanına kaydet
"""

import time
from database import SessionLocal, SiteConfig, SiteUrl, Product
from trendyol_scraper import TrendyolScraper
from hepsiburada_scraper import HepsiburadaScraper
from datetime import datetime

def run_scraper(site_key: str = None, max_pages: int = 1):
    """Belirtilen site için scraper'ı çalıştır"""

    session = SessionLocal()

    try:
        # Site seç
        if site_key:
            sites = session.query(SiteConfig).filter_by(site_key=site_key, is_active=True).all()
        else:
            sites = session.query(SiteConfig).filter_by(is_active=True).all()

        if not sites:
            print("❌ Aktif site bulunamadı!")
            return

        total_products = 0

        for site in sites:
            print(f"\n{'='*60}")
            print(f"🌐 {site.site_name} scraping başlıyor...")

            # Site'ye göre scraper seç
            if site.site_key == 'trendyol':
                scraper = TrendyolScraper()
            elif site.site_key == 'hepsiburada':
                scraper = HepsiburadaScraper()
            else:
                print(f"⚠️ {site.site_key} için scraper bulunamadı, geçiliyor...")
                continue

            # Bu site için URL'leri al
            urls = session.query(SiteUrl).filter_by(
                site_id=site.id,
                is_active=True
            ).all()

            if not urls:
                print(f"  ⚠️ {site.site_name} için aktif URL bulunamadı")
                continue

            site_product_count = 0

            for url in urls[:3]:  # İlk 3 URL'yi çek
                print(f"\n  📍 Kategori: {url.category or 'Genel'}")
                print(f"  🔗 URL: {url.url_path[:80]}...")

                try:
                    # Ürünleri çek
                    products = scraper.scrape_products(
                        url=url.url_path,
                        max_pages=max_pages
                    )

                    if products:
                        print(f"  ✅ {len(products)} ürün bulundu")

                        # Veritabanına kaydet
                        for product_data in products[:50]:  # İlk 50 ürünü kaydet
                            # Var olan ürünü kontrol et
                            existing = session.query(Product).filter_by(
                                site_id=site.id,
                                site_product_id=product_data.get('id', '')
                            ).first()

                            if not existing:
                                product = Product(
                                    site_id=site.id,
                                    site_product_id=product_data.get('id', ''),
                                    product_id=f"{site.site_key}_{product_data.get('id', '')}",  # Eski uyumluluk için
                                    name=product_data.get('name', '')[:500],
                                    price=float(product_data.get('price', 0)),
                                    product_url=product_data.get('url', ''),
                                    url=product_data.get('url', ''),  # Eski uyumluluk için
                                    image_url=product_data.get('image', ''),
                                    brand=product_data.get('brand', ''),
                                    category=url.category,
                                    site_name=site.site_key,  # Site adı ekle
                                    seller=product_data.get('seller', ''),
                                    rating=product_data.get('rating'),
                                    review_count=product_data.get('review_count', 0),
                                    in_stock=True,
                                    scraped_at=datetime.now()
                                )
                                session.add(product)
                                site_product_count += 1

                        session.commit()

                        # İlk 3 ürünü göster
                        for i, p in enumerate(products[:3], 1):
                            print(f"    {i}. {p.get('name', '')[:50]}... - {p.get('price', 0)} TL")
                    else:
                        print(f"  ⚠️ Ürün bulunamadı")

                except Exception as e:
                    print(f"  ❌ Hata: {str(e)}")
                    session.rollback()

                time.sleep(2)  # Rate limiting

            print(f"\n✅ {site.site_name} için {site_product_count} yeni ürün eklendi")
            total_products += site_product_count

        print(f"\n{'='*60}")
        print(f"🎉 TOPLAM {total_products} yeni ürün veritabanına eklendi!")

        # Toplam ürün sayısını göster
        total_in_db = session.query(Product).count()
        print(f"📦 Veritabanında toplam {total_in_db} ürün var")

    except Exception as e:
        print(f"❌ Genel hata: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    import sys

    # Komut satırı parametreleri
    site_key = sys.argv[1] if len(sys.argv) > 1 else None
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print("🚀 Market Spider Scraper")
    print("-" * 60)

    if site_key:
        print(f"Site: {site_key}")
    else:
        print("Tüm aktif siteler çekilecek")
    print(f"Max sayfa: {max_pages}")

    run_scraper(site_key, max_pages)