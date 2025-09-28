#!/usr/bin/env python3
"""
Database'i başlat ve örnek veriler ekle
"""

from database import init_database, SessionLocal, SiteConfig, SiteUrl
from datetime import datetime
import json

def add_sample_sites():
    """Örnek site konfigürasyonları ekle"""
    session = SessionLocal()

    # Trendyol
    trendyol = session.query(SiteConfig).filter_by(site_key='trendyol').first()
    if not trendyol:
        trendyol = SiteConfig(
            site_key='trendyol',
            site_name='Trendyol',
            base_url='https://www.trendyol.com',
            scraper_type='trendyol',
            use_selenium=False,
            rate_limit=2.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8"
            },
            is_active=True
        )
        session.add(trendyol)
        session.flush()

        # Trendyol URL'leri
        urls = [
            {
                'url_type': 'best_sellers',
                'url_path': 'https://www.trendyol.com/sr?wc=103108&os=1&sk=1&sst=BEST_SELLER',
                'category': 'elektronik',
                'description': 'En çok satan elektronik ürünler',
                'max_products': 100
            },
            {
                'url_type': 'best_sellers',
                'url_path': 'https://www.trendyol.com/sr?wc=82&os=1&sk=1&sst=BEST_SELLER',
                'category': 'giyim',
                'description': 'En çok satan giyim ürünleri',
                'max_products': 100
            },
            {
                'url_type': 'api',
                'url_path': 'https://public.trendyol.com/discovery-web-searchgw-service/v2/api/infinite-scroll',
                'category': 'genel',
                'description': 'Trendyol API endpoint',
                'max_products': 200
            }
        ]

        for url_data in urls:
            url = SiteUrl(
                site_id=trendyol.id,
                url_type=url_data['url_type'],
                url_path=url_data['url_path'],
                category=url_data.get('category'),
                description=url_data.get('description'),
                max_products=url_data.get('max_products', 100),
                is_active=True,
                priority=1
            )
            session.add(url)

    # Hepsiburada
    hepsiburada = session.query(SiteConfig).filter_by(site_key='hepsiburada').first()
    if not hepsiburada:
        hepsiburada = SiteConfig(
            site_key='hepsiburada',
            site_name='Hepsiburada',
            base_url='https://www.hepsiburada.com',
            scraper_type='generic',
            use_selenium=True,  # JavaScript yoğun site
            rate_limit=3.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9"
            },
            is_active=True
        )
        session.add(hepsiburada)
        session.flush()

        # Hepsiburada URL'leri
        urls = [
            {
                'url_type': 'best_sellers',
                'url_path': '/cok-satanlar',
                'category': 'genel',
                'description': 'Genel en çok satanlar',
                'max_products': 100
            },
            {
                'url_type': 'category',
                'url_path': '/bilgisayarlar-c-2147483646?siralama=coksatan',
                'category': 'bilgisayar',
                'description': 'En çok satan bilgisayarlar',
                'max_products': 50
            }
        ]

        for url_data in urls:
            url = SiteUrl(
                site_id=hepsiburada.id,
                url_type=url_data['url_type'],
                url_path=url_data['url_path'],
                category=url_data.get('category'),
                description=url_data.get('description'),
                max_products=url_data.get('max_products', 100),
                is_active=True,
                priority=2
            )
            session.add(url)

    # N11
    n11 = session.query(SiteConfig).filter_by(site_key='n11').first()
    if not n11:
        n11 = SiteConfig(
            site_key='n11',
            site_name='N11',
            base_url='https://www.n11.com',
            scraper_type='generic',
            use_selenium=False,
            rate_limit=3.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            is_active=True
        )
        session.add(n11)
        session.flush()

        # N11 URL'leri
        urls = [
            {
                'url_type': 'best_sellers',
                'url_path': '/bilgisayar?srt=SELLING',
                'category': 'bilgisayar',
                'description': 'En çok satan bilgisayar ürünleri',
                'max_products': 100
            },
            {
                'url_type': 'best_sellers',
                'url_path': '/telefon-ve-aksesuarlari?srt=SELLING',
                'category': 'telefon',
                'description': 'En çok satan telefon ve aksesuarlar',
                'max_products': 100
            }
        ]

        for url_data in urls:
            url = SiteUrl(
                site_id=n11.id,
                url_type=url_data['url_type'],
                url_path=url_data['url_path'],
                category=url_data.get('category'),
                description=url_data.get('description'),
                max_products=url_data.get('max_products', 100),
                is_active=True,
                priority=3
            )
            session.add(url)

    # Amazon TR
    amazon = session.query(SiteConfig).filter_by(site_key='amazon_tr').first()
    if not amazon:
        amazon = SiteConfig(
            site_key='amazon_tr',
            site_name='Amazon TR',
            base_url='https://www.amazon.com.tr',
            scraper_type='generic',
            use_selenium=False,
            rate_limit=2.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept-Language": "tr-TR,tr;q=0.9"
            },
            is_active=True
        )
        session.add(amazon)
        session.flush()

        # Amazon URL'leri
        urls = [
            {
                'url_type': 'best_sellers',
                'url_path': '/gp/bestsellers',
                'category': 'genel',
                'description': 'Amazon en çok satanlar',
                'max_products': 100
            },
            {
                'url_type': 'best_sellers',
                'url_path': '/gp/bestsellers/electronics',
                'category': 'elektronik',
                'description': 'En çok satan elektronik',
                'max_products': 100
            }
        ]

        for url_data in urls:
            url = SiteUrl(
                site_id=amazon.id,
                url_type=url_data['url_type'],
                url_path=url_data['url_path'],
                category=url_data.get('category'),
                description=url_data.get('description'),
                max_products=url_data.get('max_products', 100),
                is_active=True,
                priority=2
            )
            session.add(url)

    session.commit()
    print("✅ Örnek site konfigürasyonları eklendi!")


if __name__ == "__main__":
    print("🔄 Database başlatılıyor...")
    init_database()
    print("✅ Database tabloları oluşturuldu!")

    print("\n📝 Örnek veriler ekleniyor...")
    add_sample_sites()

    print("\n✨ Database hazır!")
    print("\nSistem şimdi admin panelden yönetilebilir:")
    print("1. Dashboard'u açın: streamlit run dashboard.py")
    print("2. Sol menüden 'Admin Panel' seçin")
    print("3. Siteleri ve URL'leri yönetin")