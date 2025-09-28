#!/usr/bin/env python3
"""
Add price history data for existing products
"""

from database import SessionLocal, Product, PriceHistory
from datetime import datetime, timedelta
import random

session = SessionLocal()

try:
    # Get all products
    products = session.query(Product).all()

    if not products:
        print("❌ Önce ürün eklenmesi gerekiyor!")
        exit(1)

    print(f"📦 {len(products)} ürün bulundu")

    # Add price history for each product
    price_count = 0

    for product in products:
        current_price = product.price or 100

        # Add current price
        price_entry = PriceHistory(
            product_id=product.id,
            price=current_price,
            original_price=product.original_price or current_price,
            discount_percentage=0 if current_price == product.original_price else ((product.original_price - current_price) / product.original_price * 100),
            currency='TRY',
            in_stock=True,
            seller_name=product.seller,
            seller_rating=random.uniform(4.0, 5.0),
            timestamp=datetime.now()
        )
        session.add(price_entry)
        price_count += 1

        # Add historical prices (last 30 days)
        for days_ago in range(1, 31):
            # Price fluctuation simulation
            price_change = random.uniform(-20, 30)  # -20 TL to +30 TL change
            historical_price = current_price + price_change

            # Occasional discounts
            is_discount_day = random.random() < 0.2  # 20% chance of discount
            if is_discount_day:
                discount_price = historical_price * 0.85  # 15% discount
                original = historical_price
            else:
                discount_price = historical_price
                original = historical_price

            historical_entry = PriceHistory(
                product_id=product.id,
                price=discount_price,
                original_price=original,
                discount_percentage=0 if discount_price == original else ((original - discount_price) / original * 100),
                currency='TRY',
                in_stock=random.random() > 0.1,  # 90% chance in stock
                seller_name=product.seller,
                seller_rating=random.uniform(4.0, 5.0),
                timestamp=datetime.now() - timedelta(days=days_ago)
            )
            session.add(historical_entry)
            price_count += 1

    session.commit()
    print(f"✅ {price_count} fiyat geçmişi kaydı eklendi")

    # Show price statistics
    from sqlalchemy import func

    # Products with biggest price drops today
    price_drops = session.query(
        Product.name,
        Product.brand,
        PriceHistory.price,
        PriceHistory.original_price,
        PriceHistory.discount_percentage
    ).join(
        PriceHistory
    ).filter(
        PriceHistory.timestamp >= datetime.now() - timedelta(hours=1),
        PriceHistory.discount_percentage > 0
    ).order_by(
        PriceHistory.discount_percentage.desc()
    ).limit(5).all()

    if price_drops:
        print("\n💰 En Büyük İndirimler:")
        for p in price_drops:
            print(f"  • {p.name[:40]}... - {p.price:.2f} TL (%%{p.discount_percentage:.1f} indirim)")

    # Price statistics
    stats = session.query(
        func.min(PriceHistory.price).label('min_price'),
        func.max(PriceHistory.price).label('max_price'),
        func.avg(PriceHistory.price).label('avg_price'),
        func.count(PriceHistory.id).label('total_prices')
    ).first()

    print(f"\n📊 Fiyat İstatistikleri:")
    print(f"  • Toplam fiyat kaydı: {stats.total_prices}")
    print(f"  • En düşük fiyat: {stats.min_price:.2f} TL")
    print(f"  • En yüksek fiyat: {stats.max_price:.2f} TL")
    print(f"  • Ortalama fiyat: {stats.avg_price:.2f} TL")

    # Average price by category
    category_prices = session.query(
        Product.category,
        func.avg(PriceHistory.price).label('avg_price'),
        func.count(Product.id).label('product_count')
    ).join(
        PriceHistory
    ).filter(
        PriceHistory.timestamp >= datetime.now() - timedelta(days=1)
    ).group_by(
        Product.category
    ).all()

    print(f"\n📦 Kategori Bazında Ortalama Fiyatlar:")
    for cat in category_prices:
        print(f"  • {cat.category or 'Diğer'}: {cat.avg_price:.2f} TL")

except Exception as e:
    print(f"❌ Hata: {e}")
    session.rollback()
finally:
    session.close()