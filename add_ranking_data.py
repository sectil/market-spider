#!/usr/bin/env python3
"""
Add ranking data for existing products
"""

from database import SessionLocal, Product, RankingHistory
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

    # Add ranking history for each product
    ranking_count = 0

    for i, product in enumerate(products, 1):
        # Add current ranking
        ranking = RankingHistory(
            product_id=product.id,
            rank_position=i,  # Sıralama pozisyonu
            category_rank=i,  # Kategori içinde sıralama
            total_reviews=product.review_count or random.randint(10, 1000),
            average_rating=product.rating or random.uniform(3.5, 5.0),
            sales_count=random.randint(50, 5000),  # Tahmini satış sayısı
            list_type='best_sellers',
            timestamp=datetime.now()
        )
        session.add(ranking)
        ranking_count += 1

        # Add historical rankings (last 7 days)
        for days_ago in range(1, 8):
            historical_ranking = RankingHistory(
                product_id=product.id,
                rank_position=i + random.randint(-5, 5),  # Pozisyon değişimi
                category_rank=i + random.randint(-3, 3),
                total_reviews=(product.review_count or 100) - (days_ago * random.randint(1, 10)),
                average_rating=(product.rating or 4.0) + random.uniform(-0.2, 0.2),
                sales_count=random.randint(50, 5000) - (days_ago * random.randint(5, 50)),
                list_type='best_sellers',
                timestamp=datetime.now() - timedelta(days=days_ago)
            )
            session.add(historical_ranking)
            ranking_count += 1

    session.commit()
    print(f"✅ {ranking_count} ranking kaydı eklendi")

    # Show ranking summary
    from sqlalchemy import func

    # Top 5 products by current rank
    top_products = session.query(
        Product.name,
        Product.brand,
        RankingHistory.rank_position
    ).join(
        RankingHistory
    ).filter(
        RankingHistory.timestamp >= datetime.now() - timedelta(hours=1)
    ).order_by(
        RankingHistory.rank_position
    ).limit(5).all()

    print("\n🏆 En Üst Sıradaki 5 Ürün:")
    for p in top_products:
        print(f"  #{p.rank_position} - {p.name[:50]}... ({p.brand})")

    # Ranking statistics
    stats = session.query(
        func.min(RankingHistory.rank_position).label('min_rank'),
        func.max(RankingHistory.rank_position).label('max_rank'),
        func.avg(RankingHistory.rank_position).label('avg_rank'),
        func.count(RankingHistory.id).label('total_rankings')
    ).first()

    print(f"\n📊 Ranking İstatistikleri:")
    print(f"  • Toplam ranking kaydı: {stats.total_rankings}")
    print(f"  • En yüksek sıra: #{stats.min_rank}")
    print(f"  • En düşük sıra: #{stats.max_rank}")
    print(f"  • Ortalama sıra: #{stats.avg_rank:.1f}")

except Exception as e:
    print(f"❌ Hata: {e}")
    session.rollback()
finally:
    session.close()