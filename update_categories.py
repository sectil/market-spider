#!/usr/bin/env python3
"""
Kategori sistemi güncelleme scripti
"""

from database import SessionLocal, SiteConfig, SiteUrl
from datetime import datetime

def add_trendyol_categories():
    """Trendyol için kategori bazlı çok satanlar ekle"""

    session = SessionLocal()

    try:
        # Trendyol site'ini al
        trendyol = session.query(SiteConfig).filter_by(site_key='trendyol').first()

        if not trendyol:
            print("❌ Trendyol sitesi bulunamadı!")
            return

        # Kategori bazlı URL'ler
        categories = [
            # Elektronik kategorileri
            {
                'url_type': 'best_sellers',
                'category': 'telefon',
                'url_path': 'https://www.trendyol.com/cep-telefonu-x-c103498?sst=BEST_SELLER',
                'description': 'En çok satan telefonlar',
                'priority': 1
            },
            {
                'url_type': 'best_sellers',
                'category': 'bilgisayar',
                'url_path': 'https://www.trendyol.com/laptop-x-c103108?sst=BEST_SELLER',
                'description': 'En çok satan bilgisayarlar',
                'priority': 2
            },
            {
                'url_type': 'best_sellers',
                'category': 'televizyon',
                'url_path': 'https://www.trendyol.com/televizyon-x-c103546?sst=BEST_SELLER',
                'description': 'En çok satan televizyonlar',
                'priority': 3
            },
            {
                'url_type': 'best_sellers',
                'category': 'kulaklik',
                'url_path': 'https://www.trendyol.com/kulaklik-x-c103628?sst=BEST_SELLER',
                'description': 'En çok satan kulaklıklar',
                'priority': 4
            },

            # Moda kategorileri
            {
                'url_type': 'best_sellers',
                'category': 'erkek-giyim',
                'url_path': 'https://www.trendyol.com/erkek-giyim-x-g1-c1?sst=BEST_SELLER',
                'description': 'En çok satan erkek giyim',
                'priority': 5
            },
            {
                'url_type': 'best_sellers',
                'category': 'kadin-giyim',
                'url_path': 'https://www.trendyol.com/kadin-giyim-x-g2-c2?sst=BEST_SELLER',
                'description': 'En çok satan kadın giyim',
                'priority': 6
            },
            {
                'url_type': 'best_sellers',
                'category': 'ayakkabi',
                'url_path': 'https://www.trendyol.com/ayakkabi-x-c114?sst=BEST_SELLER',
                'description': 'En çok satan ayakkabılar',
                'priority': 7
            },
            {
                'url_type': 'best_sellers',
                'category': 'canta',
                'url_path': 'https://www.trendyol.com/canta-x-c118?sst=BEST_SELLER',
                'description': 'En çok satan çantalar',
                'priority': 8
            },

            # Ev & Yaşam
            {
                'url_type': 'best_sellers',
                'category': 'ev-tekstili',
                'url_path': 'https://www.trendyol.com/ev-tekstili-x-c1315?sst=BEST_SELLER',
                'description': 'En çok satan ev tekstili',
                'priority': 9
            },
            {
                'url_type': 'best_sellers',
                'category': 'mobilya',
                'url_path': 'https://www.trendyol.com/mobilya-x-c104502?sst=BEST_SELLER',
                'description': 'En çok satan mobilyalar',
                'priority': 10
            },
            {
                'url_type': 'best_sellers',
                'category': 'mutfak-gerecleri',
                'url_path': 'https://www.trendyol.com/mutfak-gerecleri-x-c104574?sst=BEST_SELLER',
                'description': 'En çok satan mutfak gereçleri',
                'priority': 11
            },

            # Kozmetik & Kişisel Bakım
            {
                'url_type': 'best_sellers',
                'category': 'kozmetik',
                'url_path': 'https://www.trendyol.com/kozmetik-x-c100001?sst=BEST_SELLER',
                'description': 'En çok satan kozmetik ürünleri',
                'priority': 12
            },
            {
                'url_type': 'best_sellers',
                'category': 'parfum',
                'url_path': 'https://www.trendyol.com/parfum-x-c103977?sst=BEST_SELLER',
                'description': 'En çok satan parfümler',
                'priority': 13
            },

            # Spor
            {
                'url_type': 'best_sellers',
                'category': 'spor-giyim',
                'url_path': 'https://www.trendyol.com/spor-giyim-x-c101439?sst=BEST_SELLER',
                'description': 'En çok satan spor giyim',
                'priority': 14
            },
            {
                'url_type': 'best_sellers',
                'category': 'spor-ayakkabi',
                'url_path': 'https://www.trendyol.com/spor-ayakkabi-x-c106543?sst=BEST_SELLER',
                'description': 'En çok satan spor ayakkabıları',
                'priority': 15
            },

            # Çocuk
            {
                'url_type': 'best_sellers',
                'category': 'bebek-giyim',
                'url_path': 'https://www.trendyol.com/bebek-giyim-x-c101455?sst=BEST_SELLER',
                'description': 'En çok satan bebek giyim',
                'priority': 16
            },
            {
                'url_type': 'best_sellers',
                'category': 'oyuncak',
                'url_path': 'https://www.trendyol.com/oyuncak-x-c104719?sst=BEST_SELLER',
                'description': 'En çok satan oyuncaklar',
                'priority': 17
            },

            # Süpermarket
            {
                'url_type': 'best_sellers',
                'category': 'supermarket',
                'url_path': 'https://www.trendyol.com/supermarket-x-c105982?sst=BEST_SELLER',
                'description': 'En çok satan market ürünleri',
                'priority': 18
            },

            # Kitap & Hobi
            {
                'url_type': 'best_sellers',
                'category': 'kitap',
                'url_path': 'https://www.trendyol.com/kitap-x-c104?sst=BEST_SELLER',
                'description': 'En çok satan kitaplar',
                'priority': 19
            },

            # Otomotiv
            {
                'url_type': 'best_sellers',
                'category': 'oto-aksesuar',
                'url_path': 'https://www.trendyol.com/oto-aksesuar-x-c104246?sst=BEST_SELLER',
                'description': 'En çok satan oto aksesuarları',
                'priority': 20
            }
        ]

        # Mevcut URL'leri temizle (opsiyonel)
        print("🔄 Mevcut URL'ler güncelleniyor...")

        # Her kategoriyi ekle
        for cat_data in categories:
            # Aynı URL var mı kontrol et
            existing = session.query(SiteUrl).filter_by(
                site_id=trendyol.id,
                url_path=cat_data['url_path']
            ).first()

            if existing:
                # Güncelle
                existing.category = cat_data['category']
                existing.description = cat_data['description']
                existing.priority = cat_data['priority']
                existing.is_active = True
                print(f"✅ Güncellendi: {cat_data['category']}")
            else:
                # Yeni ekle
                new_url = SiteUrl(
                    site_id=trendyol.id,
                    url_type=cat_data['url_type'],
                    url_path=cat_data['url_path'],
                    category=cat_data['category'],
                    description=cat_data['description'],
                    is_active=True,
                    priority=cat_data['priority'],
                    max_pages=2,  # İlk 2 sayfa
                    max_products=100,  # Max 100 ürün
                    selectors={}  # Varsayılan selector'lar kullanılacak
                )
                session.add(new_url)
                print(f"➕ Eklendi: {cat_data['category']}")

        session.commit()
        print("\n✨ Tüm kategoriler başarıyla eklendi!")
        print(f"📊 Toplam {len(categories)} kategori eklendi/güncellendi")

    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        session.rollback()
    finally:
        session.close()

def add_other_sites_categories():
    """Diğer siteler için kategori bazlı URL'ler ekle"""

    session = SessionLocal()

    try:
        # Hepsiburada için kategoriler
        hepsiburada = session.query(SiteConfig).filter_by(site_key='hepsiburada').first()
        if hepsiburada:
            hb_categories = [
                {
                    'url_type': 'best_sellers',
                    'category': 'elektronik',
                    'url_path': '/elektronik-c-60001028?siralama=coksatan',
                    'description': 'En çok satan elektronik ürünler',
                    'priority': 1
                },
                {
                    'url_type': 'best_sellers',
                    'category': 'bilgisayar',
                    'url_path': '/bilgisayarlar-c-2147483646?siralama=coksatan',
                    'description': 'En çok satan bilgisayarlar',
                    'priority': 2
                },
                {
                    'url_type': 'best_sellers',
                    'category': 'telefon',
                    'url_path': '/cep-telefonlari-c-60021947?siralama=coksatan',
                    'description': 'En çok satan telefonlar',
                    'priority': 3
                }
            ]

            for cat_data in hb_categories:
                existing = session.query(SiteUrl).filter_by(
                    site_id=hepsiburada.id,
                    url_path=cat_data['url_path']
                ).first()

                if not existing:
                    new_url = SiteUrl(
                        site_id=hepsiburada.id,
                        url_type=cat_data['url_type'],
                        url_path=cat_data['url_path'],
                        category=cat_data['category'],
                        description=cat_data['description'],
                        is_active=True,
                        priority=cat_data['priority'],
                        max_pages=2,
                        max_products=100
                    )
                    session.add(new_url)
                    print(f"➕ Hepsiburada - {cat_data['category']} eklendi")

        # N11 için kategoriler
        n11 = session.query(SiteConfig).filter_by(site_key='n11').first()
        if n11:
            n11_categories = [
                {
                    'url_type': 'best_sellers',
                    'category': 'elektronik',
                    'url_path': '/elektronik?srt=SALES',
                    'description': 'En çok satan elektronik',
                    'priority': 1
                },
                {
                    'url_type': 'best_sellers',
                    'category': 'moda',
                    'url_path': '/moda?srt=SALES',
                    'description': 'En çok satan moda ürünleri',
                    'priority': 2
                }
            ]

            for cat_data in n11_categories:
                existing = session.query(SiteUrl).filter_by(
                    site_id=n11.id,
                    url_path=cat_data['url_path']
                ).first()

                if not existing:
                    new_url = SiteUrl(
                        site_id=n11.id,
                        url_type=cat_data['url_type'],
                        url_path=cat_data['url_path'],
                        category=cat_data['category'],
                        description=cat_data['description'],
                        is_active=True,
                        priority=cat_data['priority'],
                        max_pages=2,
                        max_products=100
                    )
                    session.add(new_url)
                    print(f"➕ N11 - {cat_data['category']} eklendi")

        session.commit()
        print("\n✨ Diğer siteler için kategoriler eklendi!")

    except Exception as e:
        print(f"❌ Hata: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    print("🚀 Kategori sistemi güncelleniyor...")
    print("-" * 60)

    # Trendyol kategorilerini ekle
    add_trendyol_categories()

    print("\n" + "-" * 60)

    # Diğer sitelerin kategorilerini ekle
    add_other_sites_categories()

    print("\n" + "=" * 60)
    print("✅ Tüm güncellemeler tamamlandı!")
    print("\nAdmin Panel'den yeni kategorileri görebilirsiniz.")