"""
Database Models ve ORM Yapısı
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, Index, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json
from config import DATABASE

Base = declarative_base()


class SiteConfig(Base):
    """E-ticaret site konfigürasyonları"""
    __tablename__ = 'site_configs'

    id = Column(Integer, primary_key=True)
    site_key = Column(String(50), unique=True, nullable=False)  # trendyol, hepsiburada vs.
    site_name = Column(String(100), nullable=False)  # Görünen isim
    base_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)

    # Scraper ayarları
    scraper_type = Column(String(50), default='generic')  # generic, trendyol, hepsiburada vs.
    use_selenium = Column(Boolean, default=False)
    rate_limit = Column(Float, default=2.0)  # Saniye cinsinden bekleme

    # Headers (JSON olarak saklanır)
    headers = Column(JSON, default={})

    # Proxy ayarları
    proxy_url = Column(String(200))

    # Zaman damgaları
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    urls = relationship("SiteUrl", back_populates="site", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'site_key': self.site_key,
            'site_name': self.site_name,
            'base_url': self.base_url,
            'is_active': self.is_active,
            'scraper_type': self.scraper_type,
            'use_selenium': self.use_selenium,
            'rate_limit': self.rate_limit,
            'headers': self.headers,
            'proxy_url': self.proxy_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class SiteUrl(Base):
    """Site URL'leri - En çok satanlar, kategoriler vs."""
    __tablename__ = 'site_urls'

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('site_configs.id', ondelete='CASCADE'))
    url_type = Column(String(50), nullable=False)  # best_sellers, category, search vs.
    url_path = Column(Text, nullable=False)  # URL veya path
    category = Column(String(100))  # Kategori adı (elektronik, giyim vs.)
    description = Column(String(500))  # Açıklama
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Öncelik sırası

    # Scraping parametreleri
    max_pages = Column(Integer, default=1)  # Kaç sayfa taransın
    max_products = Column(Integer, default=100)  # Max kaç ürün alınsın

    # Selector'lar (CSS/XPath)
    selectors = Column(JSON, default={})  # Özel selector'lar

    # İstatistikler
    last_scraped = Column(DateTime)
    last_product_count = Column(Integer, default=0)
    total_scrape_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişki
    site = relationship("SiteConfig", back_populates="urls")

    def to_dict(self):
        return {
            'id': self.id,
            'site_id': self.site_id,
            'url_type': self.url_type,
            'url_path': self.url_path,
            'category': self.category,
            'description': self.description,
            'is_active': self.is_active,
            'priority': self.priority,
            'max_pages': self.max_pages,
            'max_products': self.max_products,
            'selectors': self.selectors,
            'last_scraped': self.last_scraped.isoformat() if self.last_scraped else None,
            'last_product_count': self.last_product_count,
            'total_scrape_count': self.total_scrape_count
        }


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey("site_configs.id", ondelete="CASCADE"))  # Site ID
    site_product_id = Column(String(100), index=True)  # Site'nin kendi ID'si
    product_id = Column(String(100), unique=True, index=True)  # Eski uyumluluk için
    name = Column(String(500), nullable=False)
    brand = Column(String(200))
    category = Column(String(100))
    sub_category = Column(String(100))
    site_name = Column(String(50), nullable=False)
    product_url = Column(Text)
    url = Column(Text)  # Eski uyumluluk için
    image_url = Column(Text)
    price = Column(Float)
    original_price = Column(Float)
    seller = Column(String(200))
    rating = Column(Float)
    review_count = Column(Integer, default=0)
    in_stock = Column(Boolean, default=True)
    description = Column(Text)
    scraped_at = Column(DateTime, default=datetime.now)

    # İlişkiler
    prices = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    rankings = relationship("RankingHistory", back_populates="product", cascade="all, delete-orphan")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")

    # İndeksler
    __table_args__ = (
        Index('idx_product_site', 'product_id', 'site_name'),
        Index('idx_category', 'category'),
    )

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'brand': self.brand,
            'category': self.category,
            'sub_category': self.sub_category,
            'site_name': self.site_name,
            'product_url': self.product_url,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    price = Column(Float, nullable=False)
    original_price = Column(Float)  # İndirimden önceki fiyat
    discount_percentage = Column(Float)
    currency = Column(String(10), default='TRY')
    in_stock = Column(Boolean, default=True)
    seller_name = Column(String(200))
    seller_rating = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # İlişki
    product = relationship("Product", back_populates="prices")

    # İndeks
    __table_args__ = (
        Index('idx_price_timestamp', 'product_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'original_price': self.original_price,
            'discount_percentage': self.discount_percentage,
            'currency': self.currency,
            'in_stock': self.in_stock,
            'seller_name': self.seller_name,
            'seller_rating': self.seller_rating,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class RankingHistory(Base):
    __tablename__ = 'ranking_history'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    rank_position = Column(Integer, nullable=False)
    category_rank = Column(Integer)
    total_reviews = Column(Integer)
    average_rating = Column(Float)
    sales_count = Column(Integer)  # Eğer site bu bilgiyi veriyorsa
    list_type = Column(String(50))  # "best_sellers", "most_viewed", "trending" vs
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # İlişki
    product = relationship("Product", back_populates="rankings")

    # İndeks
    __table_args__ = (
        Index('idx_ranking_timestamp', 'product_id', 'timestamp'),
        Index('idx_rank_position', 'rank_position', 'timestamp'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'rank_position': self.rank_position,
            'category_rank': self.category_rank,
            'total_reviews': self.total_reviews,
            'average_rating': self.average_rating,
            'sales_count': self.sales_count,
            'list_type': self.list_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class ProductReview(Base):
    """Ürün yorumları"""
    __tablename__ = 'product_reviews'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id', ondelete='CASCADE'))
    reviewer_name = Column(String(200))
    reviewer_verified = Column(Boolean, default=False)  # Doğrulanmış alıcı
    rating = Column(Float)
    review_title = Column(String(500))
    review_text = Column(Text)
    review_date = Column(DateTime)
    helpful_count = Column(Integer, default=0)  # Faydalı bulma sayısı

    # Yorum analizi sonuçları
    sentiment_score = Column(Float)  # -1 (negatif) ile 1 (pozitif) arası
    key_phrases = Column(JSON)  # Anahtar kelimeler ve özellikler
    purchase_reasons = Column(JSON)  # Satın alma nedenleri
    pros = Column(JSON)  # Artılar listesi
    cons = Column(JSON)  # Eksiler listesi

    # Metadata
    language = Column(String(10), default='tr')
    scraped_at = Column(DateTime, default=datetime.utcnow)

    # İlişki
    product = relationship("Product", back_populates="reviews")

    # İndeks
    __table_args__ = (
        Index('idx_review_product', 'product_id', 'review_date'),
        Index('idx_review_sentiment', 'sentiment_score'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'reviewer_name': self.reviewer_name,
            'reviewer_verified': self.reviewer_verified,
            'rating': self.rating,
            'review_title': self.review_title,
            'review_text': self.review_text,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'helpful_count': self.helpful_count,
            'sentiment_score': self.sentiment_score,
            'key_phrases': self.key_phrases,
            'purchase_reasons': self.purchase_reasons,
            'pros': self.pros,
            'cons': self.cons
        }


class ScrapeLog(Base):
    __tablename__ = 'scrape_logs'

    id = Column(Integer, primary_key=True)
    site_name = Column(String(50), nullable=False)
    url = Column(Text)
    status = Column(String(20))  # 'success', 'failed', 'partial'
    products_found = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'site_name': self.site_name,
            'url': self.url,
            'status': self.status,
            'products_found': self.products_found,
            'products_updated': self.products_updated,
            'error_message': self.error_message,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    alert_type = Column(String(50))  # 'price_drop', 'back_in_stock', 'rank_change'
    threshold_value = Column(Float)
    current_value = Column(Float)
    message = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    triggered_at = Column(DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'alert_type': self.alert_type,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'message': self.message,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None
        }


# Database bağlantısı kurma
def get_engine():
    if DATABASE['type'] == 'sqlite':
        return create_engine(f"sqlite:///{DATABASE['sqlite_path']}",
                           connect_args={'check_same_thread': False})
    elif DATABASE['type'] == 'postgresql':
        pg = DATABASE['postgresql']
        return create_engine(
            f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['database']}"
        )
    else:
        raise ValueError(f"Unsupported database type: {DATABASE['type']}")

# SiteConfig'e products ilişkisini ekle (Product sınıfı zaten yukarıda tanımlı)
# SiteConfig.products = relationship("Product", back_populates="site", cascade="all, delete-orphan")

# Session oluşturma
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_database():
    """Database tablolarını oluştur"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tabloları oluşturuldu")

def get_db():
    """Database session'ı al"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_database()