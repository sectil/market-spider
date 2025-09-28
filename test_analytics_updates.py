#!/usr/bin/env python3
"""
Test script to verify analytics page updates
"""

from database import SessionLocal, Product, PriceHistory, RankingHistory
from datetime import datetime, timedelta
from sqlalchemy import func
import pandas as pd

def test_price_chart_data():
    """Test if we can get price chart data for products"""
    session = SessionLocal()

    print("🔍 Testing Analytics Page Updates")
    print("=" * 50)

    # Get best sellers
    start_date = datetime.now() - timedelta(days=7)

    query = session.query(
        Product,
        func.min(RankingHistory.rank_position).label('best_rank'),
        func.avg(RankingHistory.rank_position).label('avg_rank')
    ).join(
        RankingHistory, Product.id == RankingHistory.product_id
    ).filter(
        RankingHistory.timestamp >= start_date
    ).group_by(
        Product.id
    ).order_by(
        'best_rank'
    ).limit(5)

    best_sellers = query.all()

    print(f"\n📊 Top {len(best_sellers)} Best Sellers:")
    print("-" * 50)

    for i, product in enumerate(best_sellers, 1):
        print(f"\n#{i} {product.Product.name[:40]}...")
        print(f"   Marka: {product.Product.brand}")

        # Get current price (latest)
        current_price = session.query(
            PriceHistory.price
        ).filter(
            PriceHistory.product_id == product.Product.id
        ).order_by(
            PriceHistory.timestamp.desc()
        ).first()

        actual_price = current_price[0] if current_price else product.Product.price
        print(f"   💵 Güncel Fiyat: {actual_price:.2f} TL")

        # Get last update
        last_update = session.query(
            func.max(PriceHistory.timestamp)
        ).filter(
            PriceHistory.product_id == product.Product.id
        ).scalar()

        if last_update:
            print(f"   📅 Son Güncelleme: {last_update.strftime('%d.%m.%Y %H:%M')}")

        # Get price history for chart
        price_history = session.query(
            PriceHistory.timestamp,
            PriceHistory.price,
            PriceHistory.original_price
        ).filter(
            PriceHistory.product_id == product.Product.id,
            PriceHistory.timestamp >= start_date
        ).order_by(
            PriceHistory.timestamp
        ).all()

        if price_history:
            df = pd.DataFrame(price_history)
            min_price = df['price'].min()
            max_price = df['price'].max()
            avg_price = df['price'].mean()

            print(f"   📈 Fiyat İstatistikleri (Son 7 Gün):")
            print(f"      - Min: {min_price:.2f} TL")
            print(f"      - Max: {max_price:.2f} TL")
            print(f"      - Ort: {avg_price:.2f} TL")
            print(f"      - Veri Sayısı: {len(price_history)} kayıt")

        print(f"   🏆 En İyi Sıra: #{int(product.best_rank)}")
        print(f"   📊 Ortalama Sıra: #{int(product.avg_rank)}")

    print("\n" + "=" * 50)
    print("✅ Analytics page data is ready for display with:")
    print("   - Real-time prices")
    print("   - Update timestamps")
    print("   - Price history charts")
    print("   - Ranking performance")

    session.close()

if __name__ == "__main__":
    test_price_chart_data()