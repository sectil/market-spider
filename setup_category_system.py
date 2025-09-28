#!/usr/bin/env python3
"""
🏪 E-TİCARET KATEGORİ SİSTEMİ
Gerçek e-ticaret sitesi gibi kategori yapısı oluştur
"""

from database import SessionLocal, Product
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import random
from datetime import datetime

Base = declarative_base()

class Category(Base):
    """Kategori modeli"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True)
    parent_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    description = Column(Text)
    icon = Column(String(50))
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

    # İlişkiler
    parent = relationship("Category", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category_rel")

def setup_category_system():
    """Kategori sistemini kur"""

    session = SessionLocal()

    # Önce categories tablosunu oluştur
    engine = create_engine('sqlite:///market_spider.db')
    Base.metadata.create_all(engine)

    print("="*80)
    print("🏪 E-TİCARET KATEGORİ SİSTEMİ KURULUMU")
    print("="*80)

    # Ana kategoriler ve alt kategorileri
    category_structure = {
        "👗 Giyim & Aksesuar": {
            "icon": "👗",
            "slug": "giyim-aksesuar",
            "subcategories": {
                "Kadın Giyim": ["Elbise", "Pantolon", "Gömlek", "T-shirt", "Trençkot", "Sweatshirt", "Atlet"],
                "Erkek Giyim": ["Pantolon", "Gömlek", "T-shirt", "Sweatshirt", "Ceket", "Takım Elbise"],
                "Çocuk Giyim": ["Bebek Giyim", "Kız Çocuk", "Erkek Çocuk", "Okul Kıyafetleri"],
                "İç Giyim": ["Kadın İç Giyim", "Erkek İç Giyim", "Pijama & Gecelik", "Çorap"],
                "Ayakkabı": ["Kadın Ayakkabı", "Erkek Ayakkabı", "Çocuk Ayakkabı", "Spor Ayakkabı"],
                "Çanta": ["Kadın Çanta", "Erkek Çanta", "Sırt Çantası", "Valiz"],
                "Aksesuar": ["Takı", "Saat", "Gözlük", "Şapka", "Kemer", "Cüzdan"]
            }
        },
        "🏠 Ev & Yaşam": {
            "icon": "🏠",
            "slug": "ev-yasam",
            "subcategories": {
                "Ev Tekstili": ["Nevresim Takımı", "Havlu", "Halı & Kilim", "Perde", "Yastık", "Battaniye"],
                "Mobilya": ["Koltuk Takımı", "Yatak Odası", "Yemek Odası", "Çalışma Masası", "TV Ünitesi"],
                "Ev Dekorasyon": ["Tablo", "Ayna", "Vazo", "Mumluk", "Çerçeve", "Biblo"],
                "Mutfak": ["Tencere Seti", "Bardak Takımı", "Çatal Bıçak", "Mutfak Robotu", "Kahve Makinesi"],
                "Banyo": ["Banyo Tekstili", "Banyo Aksesuarı", "Duş Sistemleri"],
                "Bahçe": ["Bahçe Mobilyası", "Mangal", "Çim Biçme", "Bahçe Dekorasyon"],
                "Yapı Market": ["El Aletleri", "Elektrikli Aletler", "Boya", "Aydınlatma"]
            }
        },
        "📱 Elektronik": {
            "icon": "📱",
            "slug": "elektronik",
            "subcategories": {
                "Telefon": ["Cep Telefonu", "Telefon Kılıfı", "Şarj Aleti", "Kulaklık", "Powerbank"],
                "Bilgisayar": ["Laptop", "Masaüstü PC", "Tablet", "Monitör", "Klavye Mouse"],
                "TV & Ses Sistemleri": ["Televizyon", "Soundbar", "Hoparlör", "Kulaklık", "Mikrofon"],
                "Oyun & Konsol": ["PlayStation", "Xbox", "Nintendo", "Oyun", "Gaming Aksesuar"],
                "Fotoğraf & Kamera": ["DSLR", "Aksiyon Kamera", "Drone", "Objektif"],
                "Beyaz Eşya": ["Buzdolabı", "Çamaşır Makinesi", "Bulaşık Makinesi", "Fırın"],
                "Küçük Ev Aletleri": ["Ütü", "Süpürge", "Blender", "Tost Makinesi", "Kettle"]
            }
        },
        "💄 Kozmetik & Kişisel Bakım": {
            "icon": "💄",
            "slug": "kozmetik",
            "subcategories": {
                "Makyaj": ["Fondöten", "Ruj", "Maskara", "Far Paleti", "Allık"],
                "Cilt Bakım": ["Yüz Kremi", "Serum", "Tonik", "Temizleyici", "Maske"],
                "Parfüm": ["Kadın Parfüm", "Erkek Parfüm", "Unisex Parfüm", "Deodorant"],
                "Saç Bakım": ["Şampuan", "Saç Kremi", "Saç Serumu", "Saç Boyası"],
                "Vücut Bakım": ["Duş Jeli", "Vücut Losyonu", "El Kremi", "Güneş Kremi"],
                "Tıraş & Epilasyon": ["Tıraş Makinesi", "Epilatör", "Ağda", "Tıraş Köpüğü"],
                "Sağlık": ["Vitamin", "Takviye", "Medikal Ürünler", "Bebek Bakım"]
            }
        },
        "🏪 Süpermarket": {
            "icon": "🏪",
            "slug": "supermarket",
            "subcategories": {
                "Temel Gıda": ["Un", "Şeker", "Yağ", "Makarna", "Pirinç", "Bakliyat"],
                "Atıştırmalık": ["Bisküvi", "Çikolata", "Cips", "Kuruyemiş"],
                "İçecek": ["Su", "Meyve Suyu", "Gazlı İçecek", "Çay", "Kahve"],
                "Süt Ürünleri": ["Süt", "Yoğurt", "Peynir", "Tereyağı"],
                "Et & Tavuk": ["Kırmızı Et", "Tavuk", "Balık", "Şarküteri"],
                "Meyve & Sebze": ["Meyve", "Sebze", "Organik Ürünler"],
                "Temizlik": ["Deterjan", "Temizlik Malzemesi", "Kağıt Ürünleri"]
            }
        },
        "🏃 Spor & Outdoor": {
            "icon": "🏃",
            "slug": "spor-outdoor",
            "subcategories": {
                "Fitness": ["Fitness Aletleri", "Yoga", "Pilates", "Ağırlık"],
                "Spor Giyim": ["Eşofman", "Tayt", "Spor Ayakkabı", "Forma"],
                "Bisiklet": ["Bisiklet", "Bisiklet Aksesuarı", "Kask", "Eldiven"],
                "Kamp & Doğa": ["Çadır", "Uyku Tulumu", "Kamp Sandalyesi", "Termos"],
                "Su Sporları": ["Mayo", "Deniz Gözlüğü", "Şnorkel", "Sörf"],
                "Takım Sporları": ["Futbol", "Basketbol", "Voleybol", "Tenis"],
                "Kış Sporları": ["Kayak", "Snowboard", "Paten", "Kış Giyim"]
            }
        },
        "📚 Kitap & Hobi": {
            "icon": "📚",
            "slug": "kitap-hobi",
            "subcategories": {
                "Kitap": ["Roman", "Bilim", "Tarih", "Çocuk Kitabı", "Ders Kitabı"],
                "Dergi": ["Moda", "Teknoloji", "Sağlık", "Dekorasyon"],
                "Kırtasiye": ["Defter", "Kalem", "Okul Malzemesi", "Ofis Malzemesi"],
                "Müzik": ["Müzik Aleti", "Plak", "CD", "Aksesuar"],
                "Oyuncak": ["Bebek", "Lego", "Puzzle", "Eğitici Oyuncak"],
                "Hobi": ["Resim Malzemesi", "El İşi", "Koleksiyon", "Model"],
                "Oyun": ["Kutu Oyunu", "Kart Oyunu", "Strateji Oyunu"]
            }
        },
        "🚗 Otomotiv": {
            "icon": "🚗",
            "slug": "otomotiv",
            "subcategories": {
                "Araç Aksesuarı": ["Koltuk Kılıfı", "Paspas", "Direksiyon Kılıfı"],
                "Yedek Parça": ["Filtre", "Yağ", "Akü", "Lastik"],
                "Araç Bakım": ["Temizlik", "Cila", "Parfüm", "Bakım Seti"],
                "Elektronik": ["Navigasyon", "Kamera", "Müzik Sistemi"],
                "Motosiklet": ["Kask", "Mont", "Eldiven", "Aksesuar"],
                "Bisiklet": ["Yol Bisikleti", "Dağ Bisikleti", "Aksesuar"]
            }
        },
        "🐕 Petshop": {
            "icon": "🐕",
            "slug": "petshop",
            "subcategories": {
                "Kedi": ["Kedi Maması", "Kedi Kumu", "Oyuncak", "Taşıma"],
                "Köpek": ["Köpek Maması", "Tasma", "Oyuncak", "Yatak"],
                "Kuş": ["Kuş Yemi", "Kafes", "Aksesuar"],
                "Akvaryum": ["Balık Yemi", "Akvaryum", "Filtre", "Dekor"],
                "Kemirgen": ["Hamster", "Tavşan", "Kobay", "Kafes"],
                "Sağlık": ["Vitamin", "Şampuan", "Veteriner", "İlaç"]
            }
        }
    }

    # Kategorileri oluştur
    print("\n📂 Kategoriler oluşturuluyor...")

    category_map = {}
    order = 0

    for main_cat_name, main_cat_data in category_structure.items():
        # Ana kategori
        main_cat = Category(
            name=main_cat_name.replace(main_cat_data["icon"], "").strip(),
            slug=main_cat_data["slug"],
            icon=main_cat_data["icon"],
            order_index=order,
            parent_id=None
        )
        session.add(main_cat)
        session.commit()
        category_map[main_cat_name] = main_cat
        order += 1

        print(f"\n{main_cat_data['icon']} {main_cat.name}")

        # Alt kategoriler
        sub_order = 0
        for sub_cat_name, sub_sub_categories in main_cat_data["subcategories"].items():
            sub_cat = Category(
                name=sub_cat_name,
                slug=f"{main_cat_data['slug']}-{sub_cat_name.lower().replace(' ', '-')}",
                parent_id=main_cat.id,
                order_index=sub_order
            )
            session.add(sub_cat)
            session.commit()
            category_map[sub_cat_name] = sub_cat
            sub_order += 1

            print(f"  └─ {sub_cat_name}")

            # Alt alt kategoriler
            sub_sub_order = 0
            for sub_sub_cat_name in sub_sub_categories:
                sub_sub_cat = Category(
                    name=sub_sub_cat_name,
                    slug=f"{main_cat_data['slug']}-{sub_cat_name.lower().replace(' ', '-')}-{sub_sub_cat_name.lower().replace(' ', '-')}",
                    parent_id=sub_cat.id,
                    order_index=sub_sub_order
                )
                session.add(sub_sub_cat)
                session.commit()
                category_map[sub_sub_cat_name] = sub_sub_cat
                sub_sub_order += 1

                print(f"      └─ {sub_sub_cat_name}")

    # Mevcut ürünleri kategorilere ata
    print("\n\n📦 Mevcut ürünler kategorilere atanıyor...")

    products = session.query(Product).all()

    for product in products:
        # Ürün adına göre kategori tahmin et
        product_name = product.name.lower()

        if "pantolon" in product_name or "palazzo" in product_name:
            category = category_map.get("Pantolon")
        elif "atlet" in product_name:
            category = category_map.get("Atlet")
        elif "trençkot" in product_name or "trenç" in product_name:
            category = category_map.get("Trençkot")
        elif "sweatshirt" in product_name:
            category = category_map.get("Sweatshirt")
        elif "pijama" in product_name:
            category = category_map.get("Pijama & Gecelik")
        elif "külot" in product_name or "bikini" in product_name:
            category = category_map.get("Kadın İç Giyim")
        elif "çorap" in product_name or "külotlu" in product_name or "patik" in product_name:
            category = category_map.get("Çorap")
        elif "ceket" in product_name or "bomber" in product_name:
            category = category_map.get("Ceket")
        elif "bluz" in product_name:
            category = category_map.get("Gömlek")
        elif "sütyen" in product_name:
            category = category_map.get("Kadın İç Giyim")
        else:
            # Default kategori
            category = category_map.get("Kadın Giyim")

        if category:
            # Product tablosunda category_id alanı varsa güncelle
            # (Önce database.py'de Product modeline category_id eklenmeli)
            print(f"  {product.name[:40]:42} → {category.name}")

    session.commit()

    # Özet rapor
    print("\n" + "="*80)
    print("📊 KATEGORİ SİSTEMİ ÖZET")
    print("="*80)

    total_categories = session.query(Category).count()
    main_categories = session.query(Category).filter_by(parent_id=None).count()

    print(f"✅ Toplam {total_categories} kategori oluşturuldu")
    print(f"   • {main_categories} ana kategori")
    print(f"   • {total_categories - main_categories} alt kategori")

    print("\n📂 Ana Kategoriler:")
    main_cats = session.query(Category).filter_by(parent_id=None).order_by(Category.order_index).all()
    for cat in main_cats:
        sub_count = session.query(Category).filter_by(parent_id=cat.id).count()
        print(f"   {cat.icon} {cat.name}: {sub_count} alt kategori")

    session.close()


def display_category_tree():
    """Kategori ağacını göster"""

    session = SessionLocal()

    print("\n" + "="*80)
    print("🌳 KATEGORİ AĞACI")
    print("="*80)

    # Ana kategoriler
    main_categories = session.query(Category).filter_by(parent_id=None).order_by(Category.order_index).all()

    for main_cat in main_categories:
        print(f"\n{main_cat.icon} {main_cat.name}")

        # Alt kategoriler
        sub_categories = session.query(Category).filter_by(parent_id=main_cat.id).order_by(Category.order_index).all()

        for i, sub_cat in enumerate(sub_categories):
            is_last_sub = (i == len(sub_categories) - 1)
            prefix = "└─" if is_last_sub else "├─"
            print(f"  {prefix} {sub_cat.name}")

            # Alt alt kategoriler
            sub_sub_categories = session.query(Category).filter_by(parent_id=sub_cat.id).order_by(Category.order_index).all()

            for j, sub_sub_cat in enumerate(sub_sub_categories):
                is_last_sub_sub = (j == len(sub_sub_categories) - 1)
                sub_prefix = "   " if is_last_sub else "│  "
                sub_sub_prefix = "└─" if is_last_sub_sub else "├─"
                print(f"  {sub_prefix}{sub_sub_prefix} {sub_sub_cat.name}")

    session.close()


if __name__ == "__main__":
    setup_category_system()
    display_category_tree()