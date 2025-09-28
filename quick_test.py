#!/usr/bin/env python3
"""
Quick test to populate database with products
"""

from database import SessionLocal, SiteConfig, SiteUrl, Product, init_database
from trendyol_scraper import TrendyolScraper
from datetime import datetime

# Initialize database
init_database()

session = SessionLocal()

try:
    # Add Trendyol site if not exists
    site = session.query(SiteConfig).filter_by(site_key='trendyol').first()

    if not site:
        site = SiteConfig(
            site_key='trendyol',
            site_name='Trendyol',
            base_url='https://www.trendyol.com',
            is_active=True,
            scraper_type='trendyol',
            use_selenium=False,
            rate_limit=1.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'
            }
        )
        session.add(site)
        session.commit()
        print(f"✅ Trendyol site eklendi")

    # Add URL for women's clothing best sellers
    url = session.query(SiteUrl).filter_by(
        site_id=site.id,
        url_type='best_sellers'
    ).first()

    if not url:
        url = SiteUrl(
            site_id=site.id,
            url_type='best_sellers',
            url_path='https://www.trendyol.com/kadin-giyim-x-g1-c82?sst=BEST_SELLER',
            category='Kadın Giyim',
            description='Kadın giyim en çok satanlar',
            is_active=True,
            priority=1,
            max_pages=1,
            max_products=50
        )
        session.add(url)
        session.commit()
        print(f"✅ URL eklendi: Kadın Giyim")

    # Scrape products
    print(f"\n🔍 Ürünler çekiliyor...")
    scraper = TrendyolScraper()
    products = scraper.scrape_products(url.url_path, max_pages=1)

    print(f"✅ {len(products)} ürün bulundu")

    # Save products to database
    saved_count = 0
    for product_data in products[:50]:  # Save first 50
        # Check if product exists
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
                category='Kadın Giyim',
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
    print(f"✅ {saved_count} yeni ürün veritabanına eklendi")

    # Show total products
    total = session.query(Product).count()
    print(f"📦 Veritabanında toplam {total} ürün var")

    # Show first 3 products
    products_in_db = session.query(Product).limit(3).all()

    print(f"\n📦 İlk 3 ürün:")
    for i, p in enumerate(products_in_db, 1):
        print(f"{i}. {p.name[:50]}... - {p.price} TL ({p.brand})")

except Exception as e:
    print(f"❌ Hata: {e}")
    session.rollback()
finally:
    session.close()