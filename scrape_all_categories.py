#!/usr/bin/env python3
"""
Scrape products from all discovered categories
"""

from database import SessionLocal, SiteConfig, SiteUrl, Product
from trendyol_scraper import TrendyolScraper
from datetime import datetime

session = SessionLocal()

try:
    # Get Trendyol site
    site = session.query(SiteConfig).filter_by(site_key='trendyol').first()

    if not site:
        print("❌ Trendyol site bulunamadı!")
        exit(1)

    # Get all active URLs for this site
    urls = session.query(SiteUrl).filter_by(
        site_id=site.id,
        is_active=True
    ).order_by(SiteUrl.priority).all()

    print(f"📦 {len(urls)} kategori bulundu")

    scraper = TrendyolScraper()
    total_products_saved = 0

    for url in urls[:10]:  # Process first 10 categories
        print(f"\n📍 Kategori: {url.category or 'Genel'}")
        print(f"  🔗 {url.url_path[:80]}...")

        try:
            # Scrape products
            products = scraper.scrape_products(url.url_path, max_pages=1)

            if products:
                print(f"  ✅ {len(products)} ürün bulundu")

                # Save to database
                saved_count = 0
                for product_data in products[:20]:  # Save first 20 from each category
                    # Check if exists
                    existing = session.query(Product).filter_by(
                        site_product_id=product_data.get('id', ''),
                        site_name='trendyol'
                    ).first()

                    if not existing:
                        product = Product(
                            site_id=site.id,
                            site_product_id=product_data.get('id', ''),
                            product_id=f"trendyol_{product_data.get('id', '')}",
                            name=product_data.get('name', '')[:500],
                            price=float(product_data.get('price', 0)),
                            original_price=float(product_data.get('price', 0)),
                            product_url=product_data.get('url', ''),
                            url=product_data.get('url', ''),
                            image_url=product_data.get('image', ''),
                            brand=product_data.get('brand', ''),
                            category=url.category,
                            site_name='trendyol',
                            seller=str(product_data.get('seller', '')),
                            rating=float(product_data.get('rating', 0)),
                            review_count=int(product_data.get('review_count', 0)),
                            in_stock=True,
                            scraped_at=datetime.now()
                        )
                        session.add(product)
                        saved_count += 1

                session.commit()
                print(f"  💾 {saved_count} yeni ürün kaydedildi")
                total_products_saved += saved_count

                # Update URL stats
                url.last_scraped = datetime.now()
                url.last_product_count = len(products)
                url.total_scrape_count = (url.total_scrape_count or 0) + 1
                session.commit()
            else:
                print(f"  ⚠️ Ürün bulunamadı")

        except Exception as e:
            print(f"  ❌ Hata: {str(e)[:100]}")
            session.rollback()
            continue

    print(f"\n{'='*60}")
    print(f"🎉 TOPLAM {total_products_saved} yeni ürün eklendi!")

    # Show total in database
    total = session.query(Product).count()
    print(f"📦 Veritabanında toplam {total} ürün var")

    # Show product distribution by category
    from sqlalchemy import func
    category_stats = session.query(
        Product.category,
        func.count(Product.id).label('count'),
        func.avg(Product.price).label('avg_price')
    ).group_by(Product.category).all()

    print(f"\n📊 Kategori Dağılımı:")
    for cat in category_stats:
        print(f"  • {cat.category or 'Diğer'}: {cat.count} ürün (Ort. {cat.avg_price:.2f} TL)")

except Exception as e:
    print(f"❌ Genel hata: {e}")
    session.rollback()
finally:
    session.close()