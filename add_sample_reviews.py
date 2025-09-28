#!/usr/bin/env python3
"""
Örnek yorumlar ekle - Test için
"""

from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
from datetime import datetime, timedelta
import random

# Örnek yorumlar
SAMPLE_REVIEWS = [
    # Pozitif yorumlar
    {
        "text": "Ürün gerçekten çok kaliteli. Kumaşı yumuşacık ve rahat. Fiyatına göre harika bir ürün. Kesinlikle tavsiye ederim.",
        "rating": 5,
        "verified": True,
        "helpful": 42
    },
    {
        "text": "Çok beğendim, tam beden uyumlu geldi. Rengi de fotoğraftaki gibi. Kargo hızlıydı teşekkürler.",
        "rating": 5,
        "verified": True,
        "helpful": 28
    },
    {
        "text": "Kalitesi fiyatına göre gayet iyi. Arkadaşım tavsiye etmişti, pişman olmadım. Yıkamada da bozulmadı.",
        "rating": 4,
        "verified": True,
        "helpful": 15
    },
    {
        "text": "Güzel ürün ama biraz pahalı geldi bana. Yine de kaliteli duruyor, uzun süre kullanırım diye düşünüyorum.",
        "rating": 4,
        "verified": False,
        "helpful": 8
    },
    {
        "text": "İndirimde aldım çok uygun fiyata geldi. Kumaşı kalın ve sağlam. Kış için ideal.",
        "rating": 5,
        "verified": True,
        "helpful": 35
    },
    # Nötr yorumlar
    {
        "text": "İdare eder, ne çok iyi ne çok kötü. Normal bir ürün işte.",
        "rating": 3,
        "verified": False,
        "helpful": 3
    },
    {
        "text": "Fena değil ama beklediğim gibi de değildi. Biraz büyük geldi sanki.",
        "rating": 3,
        "verified": True,
        "helpful": 5
    },
    # Negatif yorumlar
    {
        "text": "Ürün fotoğraftakinden farklı geldi. Rengi daha soluk, kalitesi de beklediğim gibi değil. İade ettim.",
        "rating": 2,
        "verified": True,
        "helpful": 12
    },
    {
        "text": "Çok kalitesiz bir ürün. İlk yıkamada rengi aktı ve deforme oldu. Kesinlikle almayın, paranıza yazık.",
        "rating": 1,
        "verified": True,
        "helpful": 18
    },
    {
        "text": "Kargo geç geldi ve ürün yanlış geldi. Satıcı ilgisiz. Bir daha almam.",
        "rating": 1,
        "verified": False,
        "helpful": 7
    }
]

def add_sample_reviews():
    session = SessionLocal()
    ai = TurkishReviewAI()

    try:
        # İlk 5 ürüne yorum ekle
        products = session.query(Product).limit(5).all()

        if not products:
            print("❌ Henüz ürün yok. Önce ürün eklenmeli.")
            return

        review_count = 0

        for product in products:
            print(f"\n📦 {product.name[:50]}... için yorumlar ekleniyor")

            # Her ürüne 5-10 rastgele yorum ekle
            num_reviews = random.randint(5, 10)
            selected_reviews = random.sample(SAMPLE_REVIEWS, min(num_reviews, len(SAMPLE_REVIEWS)))

            for i, sample in enumerate(selected_reviews):
                # AI analizi yap
                analysis = ai.analyze_review(sample["text"])

                # Yorumu kaydet
                review = ProductReview(
                    product_id=product.id,
                    reviewer_name=f"Müşteri_{random.randint(100, 999)}",
                    reviewer_verified=sample["verified"],
                    rating=sample["rating"],
                    review_title="",
                    review_text=sample["text"],
                    review_date=datetime.now() - timedelta(days=random.randint(1, 30)),
                    helpful_count=sample["helpful"],

                    # AI analiz sonuçları
                    sentiment_score=analysis['sentiment_score'],
                    key_phrases=analysis['key_phrases'],
                    purchase_reasons=analysis['purchase_reasons'],
                    pros=analysis['pros'],
                    cons=analysis['cons']
                )

                session.add(review)
                review_count += 1

            print(f"  ✓ {num_reviews} yorum eklendi")

        session.commit()
        print(f"\n✅ Toplam {review_count} örnek yorum eklendi")

        # İstatistikleri göster
        total_reviews = session.query(ProductReview).count()
        avg_sentiment = session.query(
            func.avg(ProductReview.sentiment_score)
        ).scalar() or 0

        print(f"\n📊 Veritabanı İstatistikleri:")
        print(f"  • Toplam yorum sayısı: {total_reviews}")
        print(f"  • Ortalama duygu skoru: {avg_sentiment:.2f}")

    except Exception as e:
        print(f"❌ Hata: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    from sqlalchemy import func
    add_sample_reviews()