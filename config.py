"""
Market Spider - Türkiye E-ticaret Fiyat Takip Sistemi
Konfigurasyon Dosyası
"""

# E-ticaret Siteleri
ECOMMERCE_SITES = {
    "trendyol": {
        "name": "Trendyol",
        "base_url": "https://www.trendyol.com",
        "best_sellers_urls": [
            "/en-cok-satanlar",
            "/sr?wb=101470&wg=1&sst=BEST_SELLER",  # Elektronik
            "/sr?wb=103108&wg=2&sst=BEST_SELLER",  # Giyim
            "/sr?wb=103665&wg=3&sst=BEST_SELLER",  # Ev & Yaşam
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 2  # saniye
    },
    "hepsiburada": {
        "name": "Hepsiburada",
        "base_url": "https://www.hepsiburada.com",
        "best_sellers_urls": [
            "/cok-satanlar",
            "/elektronik-c-2147483633?siralama=coksatan",
            "/moda-c-12087822?siralama=coksatan",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 2
    },
    "n11": {
        "name": "N11",
        "base_url": "https://www.n11.com",
        "best_sellers_urls": [
            "/bilgisayar?srt=SELLING",
            "/telefon-ve-aksesuarlari?srt=SELLING",
            "/elektronik?srt=SELLING",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "gittigidiyor": {
        "name": "GittiGidiyor",
        "base_url": "https://www.gittigidiyor.com",
        "best_sellers_urls": [
            "/cok-satanlar",
            "/elektronik?srt=most_selling",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "amazon_tr": {
        "name": "Amazon TR",
        "base_url": "https://www.amazon.com.tr",
        "best_sellers_urls": [
            "/gp/bestsellers",
            "/gp/bestsellers/electronics",
            "/gp/bestsellers/computers",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 2
    },
    "ciceksepeti": {
        "name": "ÇiçekSepeti",
        "base_url": "https://www.ciceksepeti.com",
        "best_sellers_urls": [
            "/cok-satanlar",
            "/elektronik-cok-satanlar",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "morhipo": {
        "name": "Morhipo",
        "base_url": "https://www.morhipo.com",
        "best_sellers_urls": [
            "/kampanya/en-cok-satanlar",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "teknosa": {
        "name": "Teknosa",
        "base_url": "https://www.teknosa.com",
        "best_sellers_urls": [
            "/cok-satanlar-c-100001",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "mediamarkt": {
        "name": "MediaMarkt",
        "base_url": "https://www.mediamarkt.com.tr",
        "best_sellers_urls": [
            "/tr/category/_cok-satanlar-701213.html",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    },
    "vatan": {
        "name": "Vatan Bilgisayar",
        "base_url": "https://www.vatanbilgisayar.com",
        "best_sellers_urls": [
            "/cok-satanlar",
        ],
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "rate_limit": 3
    }
}

# Ürün Kategorileri
PRODUCT_CATEGORIES = {
    "elektronik": ["telefon", "laptop", "tablet", "televizyon", "kulaklık", "kamera"],
    "bilgisayar": ["laptop", "masaüstü", "monitör", "klavye", "mouse", "ram", "ssd"],
    "giyim": ["elbise", "pantolon", "tişört", "gömlek", "ayakkabı", "çanta"],
    "ev_yasam": ["mobilya", "dekorasyon", "mutfak", "banyo", "aydınlatma"],
    "kozmetik": ["parfüm", "makyaj", "cilt bakım", "saç bakım"],
    "kitap": ["roman", "bilim", "tarih", "çocuk", "sınav"],
    "spor": ["fitness", "koşu", "futbol", "basketbol", "yoga"],
    "bebek": ["bebek bezi", "mama", "bebek arabası", "bebek güvenlik"],
    "gida": ["atıştırmalık", "içecek", "kahve", "çay", "vitamin"],
    "oyuncak": ["lego", "bebek oyuncak", "eğitici oyuncak", "puzzle"]
}

# Database Ayarları
DATABASE = {
    "type": "sqlite",  # "postgresql" olarak değiştirilebilir
    "sqlite_path": "market_spider.db",
    "postgresql": {
        "host": "localhost",
        "port": 5432,
        "database": "market_spider",
        "user": "spider_user",
        "password": "spider_pass"
    }
}

# Scraping Ayarları
SCRAPING = {
    "max_workers": 5,  # Paralel worker sayısı
    "retry_attempts": 3,
    "timeout": 30,  # saniye
    "use_selenium": False,  # JavaScript render gereken siteler için
    "selenium_headless": True,
    "proxy": None  # Proxy kullanmak için: "http://proxy:port"
}

# Scheduler Ayarları
SCHEDULER = {
    "enabled": True,
    "interval_hours": 6,  # Her 6 saatte bir çalıştır
    "start_time": "09:00",  # Günlük başlangıç saati
    "end_time": "23:00"  # Günlük bitiş saati
}

# Dashboard Ayarları
DASHBOARD = {
    "host": "0.0.0.0",
    "port": 8501,  # Streamlit port
    "api_port": 8000,  # FastAPI port
    "refresh_interval": 60  # saniye
}

# Logging
LOGGING = {
    "level": "INFO",
    "file": "market_spider.log",
    "max_size": "10MB",
    "backup_count": 5
}