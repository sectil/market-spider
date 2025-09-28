#!/usr/bin/env python3
"""
🔄 TÜM ÜRÜNLERE YORUM EKLE
Her ürün için gerçekçi yorumlar oluştur
"""

from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
from datetime import datetime, timedelta
import random

class AllProductsReviewGenerator:
    """Tüm ürünler için yorum üretici"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()

    def generate_category_specific_reviews(self, product_name, category, count=50):
        """Kategoriye özel yorumlar üret"""

        reviews = []

        # Kategori bazlı yorum şablonları
        templates = {
            'giyim': {
                'positive': [
                    "Kumaş kalitesi çok güzel, {product} tam aradığım gibiydi",
                    "Beden uyumu mükemmel, {product} üzerimde harika duruyor",
                    "{product} için verdiğim paraya değdi, kalitesi çok iyi",
                    "Arkadaşlarım {product} çok beğendi, nereden aldın diye sordular",
                    "Kargo hızlıydı, {product} tam beklediğim gibi geldi",
                    "{product} rengi canlı, hiç solmuyor",
                    "Günlük kullanım için ideal, {product} çok rahat",
                    "Ofiste giyiyorum, {product} şık duruyor",
                    "{product} dikişleri sağlam, uzun ömürlü görünüyor",
                    "Bu fiyata {product} bulmak zor, kesinlikle alın"
                ],
                'neutral': [
                    "{product} fena değil ama biraz ince kumaş",
                    "Beden tablosu doğru, {product} idare eder",
                    "{product} normal, ne çok iyi ne çok kötü",
                    "Fiyatına göre {product} uygun",
                    "{product} beklentimi tam karşılamadı ama kullanılır"
                ],
                'negative': [
                    "{product} resimden farklı geldi",
                    "Kumaş kalitesi düşük, {product} pişman oldum",
                    "{product} ilk yıkamada soldu",
                    "Beden uyumsuz, {product} iade ettim",
                    "{product} dikişleri bozuk geldi"
                ]
            },
            'elektronik': {
                'positive': [
                    "{product} performansı harika, çok hızlı çalışıyor",
                    "Batarya ömrü uzun, {product} tüm gün dayanıyor",
                    "{product} ses kalitesi mükemmel",
                    "Kurulumu kolay, {product} hemen çalıştı",
                    "{product} için ödediğim paraya değdi",
                    "Marka güvenilir, {product} kaliteli",
                    "{product} tasarımı çok şık",
                    "Garantili geldi, {product} güven veriyor",
                    "{product} hızlı kargo ile geldi, sağlam paketlenmişti",
                    "Arkadaşıma da aldım, {product} çok beğendi"
                ],
                'neutral': [
                    "{product} normal performans gösteriyor",
                    "Fiyatına göre {product} idare eder",
                    "{product} beklentimi karşıladı sayılır",
                    "Ortalama bir ürün, {product} kullanılır",
                    "{product} bazı özellikleri eksik ama işimi görüyor"
                ],
                'negative': [
                    "{product} çabuk bozuldu",
                    "Ses kalitesi kötü, {product} pişmanım",
                    "{product} şarjı çabuk bitiyor",
                    "Kutuda eksik parça vardı, {product} çalışmıyor",
                    "{product} ısınma sorunu var"
                ]
            },
            'kozmetik': {
                'positive': [
                    "{product} cildime çok iyi geldi",
                    "Kokusu harika, {product} bayıldım",
                    "{product} alerjik reaksiyon yapmadı",
                    "Uzun süre kalıcı, {product} tavsiye ederim",
                    "{product} doğal içerikli, güvenle kullanıyorum",
                    "Ambalajı çok şık, {product} hediye için ideal",
                    "{product} sonuçları hemen görünüyor",
                    "Hassas cildim var, {product} hiç tahriş etmedi",
                    "{product} ekonomik, uzun süre yetiyor",
                    "Makyajımın üzerinde {product} mükemmel duruyor"
                ],
                'neutral': [
                    "{product} normal bir ürün",
                    "Fiyatına göre {product} idare eder",
                    "{product} çok fark yaratmadı ama kötü değil",
                    "Ortalama kalite, {product} kullanılır",
                    "{product} beklediğim etkiyi yapmadı"
                ],
                'negative': [
                    "{product} cildimi kuruttu",
                    "Alerjik reaksiyon yaptı, {product} kullanamadım",
                    "{product} çok yapay kokuyor",
                    "Pahalıya geldi, {product} etkisi yok",
                    "{product} ambalajı hasarlı geldi"
                ]
            },
            'ev': {
                'positive': [
                    "{product} evime çok yakıştı",
                    "Kalitesi görünüyor, {product} sağlam",
                    "{product} montajı kolaydı",
                    "Boyutları tam uydu, {product} mükemmel",
                    "{product} temizliği kolay",
                    "Misafirler {product} çok beğendi",
                    "{product} uzun ömürlü görünüyor",
                    "Rengi canlı, {product} dekorasyonuma uydu",
                    "{product} fonksiyonel ve şık",
                    "Bu fiyata {product} harika"
                ],
                'neutral': [
                    "{product} idare eder",
                    "Normal kalite, {product} fena değil",
                    "{product} beklentimi tam karşılamadı",
                    "Fiyatına göre {product} uygun",
                    "{product} ortalama bir ürün"
                ],
                'negative': [
                    "{product} kırık geldi",
                    "Montaj zordu, {product} parçaları eksik",
                    "{product} görselden farklı",
                    "Kalitesiz malzeme, {product} pişmanım",
                    "{product} boyutları yanlış"
                ]
            }
        }

        # Default template
        default = templates.get('giyim')
        category_templates = templates.get(category.lower(), default)

        # Türk isimleri listesi
        names = [
            "Ayşe Y.", "Mehmet K.", "Fatma S.", "Ali D.", "Zeynep A.",
            "Mustafa B.", "Emine T.", "Hasan Ö.", "Hatice M.", "Ahmet G.",
            "Hülya R.", "İbrahim Ç.", "Elif K.", "Hüseyin Y.", "Sultan N.",
            "Ömer F.", "Merve D.", "Burak S.", "Selin A.", "Emre T.",
            "Esra K.", "Cem B.", "Gamze Y.", "Serkan M.", "Dilek Ö.",
            "Onur Ş.", "Burcu A.", "Oğuz T.", "Pınar K.", "Barış D.",
            "Ceren S.", "Tolga Y.", "Deniz A.", "Kaan B.", "İrem Ç.",
            "Umut K.", "Beste S.", "Efe D.", "Seda Y.", "Mert A.",
            "Aslı T.", "Can B.", "Gizem K.", "Furkan S.", "Ebru Ö.",
            "Volkan D.", "Melis A.", "Yunus K.", "Nihan S.", "Berkay T."
        ]

        for i in range(count):
            # Rastgele rating belirle (çoğunluk pozitif)
            rating_choice = random.random()
            if rating_choice < 0.70:  # %70 pozitif
                rating = random.choice([4, 5])
                template_list = category_templates['positive']
            elif rating_choice < 0.90:  # %20 nötr
                rating = 3
                template_list = category_templates['neutral']
            else:  # %10 negatif
                rating = random.choice([1, 2])
                template_list = category_templates['negative']

            # Template seç ve ürün adını yerleştir
            template = random.choice(template_list)
            review_text = template.format(product=product_name)

            # Ekstra detaylar ekle
            extras = [
                " Kargo hızlıydı.",
                " Satıcı ilgiliydi.",
                " Tekrar alırım.",
                " Tavsiye ederim.",
                " Fiyat performans ürünü.",
                " Herkese öneririm.",
                " Çok memnun kaldım.",
                " Beklentilerimi karşıladı.",
                " Güzel paketlenmişti.",
                " Teşekkürler."
            ]

            if rating >= 4 and random.random() > 0.5:
                review_text += random.choice(extras)

            reviews.append({
                'reviewer_name': random.choice(names),
                'reviewer_verified': random.random() > 0.2,  # %80 doğrulanmış
                'rating': rating,
                'review_text': review_text,
                'review_date': datetime.now() - timedelta(days=random.randint(1, 180)),
                'helpful_count': random.randint(0, 50) if random.random() > 0.7 else 0
            })

        return reviews

    def add_reviews_to_all_products(self):
        """Tüm ürünlere yorum ekle"""

        products = self.session.query(Product).all()

        print("="*60)
        print("🔄 TÜM ÜRÜNLERE YORUM EKLEME")
        print("="*60)

        for product in products:
            # Mevcut yorumları kontrol et
            existing = self.session.query(ProductReview).filter_by(product_id=product.id).count()

            if existing > 0:
                print(f"✓ {product.name}: Zaten {existing} yorum var")
                continue

            print(f"\n📦 {product.name} için yorum ekleniyor...")

            # Kategori bazlı yorum sayısı
            if "palazzo" in product.name.lower() or "pantolon" in product.name.lower():
                review_count = 100  # Ana ürüne daha çok
            else:
                review_count = random.randint(20, 50)

            # Yorumları oluştur
            reviews = self.generate_category_specific_reviews(
                product.name,
                product.category or 'giyim',
                review_count
            )

            # Veritabanına kaydet
            added = 0
            for review_data in reviews:
                # AI analizi
                analysis = self.ai.analyze_review(review_data['review_text'])

                review = ProductReview(
                    product_id=product.id,
                    reviewer_name=review_data['reviewer_name'],
                    reviewer_verified=review_data['reviewer_verified'],
                    rating=review_data['rating'],
                    review_title='',
                    review_text=review_data['review_text'],
                    review_date=review_data['review_date'],
                    helpful_count=review_data['helpful_count'],
                    sentiment_score=analysis['sentiment_score'],
                    key_phrases=analysis['key_phrases'],
                    purchase_reasons=analysis['purchase_reasons'],
                    pros=analysis['pros'],
                    cons=analysis['cons']
                )
                self.session.add(review)
                added += 1

            self.session.commit()
            print(f"✅ {added} yorum eklendi")

            # Özet göster
            avg_rating = sum(r['rating'] for r in reviews) / len(reviews)
            positive = sum(1 for r in reviews if r['rating'] >= 4)
            print(f"   Ortalama: {avg_rating:.1f}/5")
            print(f"   Pozitif: {positive}/{len(reviews)} (%{positive/len(reviews)*100:.0f})")

        # Genel özet
        print("\n" + "="*60)
        print("📊 GENEL ÖZET")
        print("="*60)

        total_products = self.session.query(Product).count()
        total_reviews = self.session.query(ProductReview).count()

        print(f"✅ Toplam {total_products} ürün")
        print(f"✅ Toplam {total_reviews} yorum")

        # Her ürün için özet
        print("\n📋 Ürün Bazında Yorum Dağılımı:")
        for product in products:
            review_count = self.session.query(ProductReview).filter_by(product_id=product.id).count()
            avg = self.session.query(ProductReview).filter_by(product_id=product.id).first()
            if avg:
                ratings = self.session.query(ProductReview).filter_by(product_id=product.id).all()
                avg_rating = sum(r.rating for r in ratings) / len(ratings)
                print(f"   • {product.name[:40]:40} → {review_count:3} yorum (⭐{avg_rating:.1f})")

    def quick_add_sample_reviews(self, product_id, count=25):
        """Belirli bir ürüne hızlıca yorum ekle"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            print(f"❌ Ürün bulunamadı: {product_id}")
            return

        reviews = self.generate_category_specific_reviews(
            product.name,
            product.category or 'giyim',
            count
        )

        for review_data in reviews:
            analysis = self.ai.analyze_review(review_data['review_text'])

            review = ProductReview(
                product_id=product.id,
                reviewer_name=review_data['reviewer_name'],
                reviewer_verified=review_data['reviewer_verified'],
                rating=review_data['rating'],
                review_title='',
                review_text=review_data['review_text'],
                review_date=review_data['review_date'],
                helpful_count=review_data['helpful_count'],
                sentiment_score=analysis['sentiment_score'],
                key_phrases=analysis['key_phrases'],
                purchase_reasons=analysis['purchase_reasons'],
                pros=analysis['pros'],
                cons=analysis['cons']
            )
            self.session.add(review)

        self.session.commit()
        print(f"✅ {count} yorum eklendi: {product.name}")


def main():
    """Ana fonksiyon"""

    generator = AllProductsReviewGenerator()

    print("🚀 TÜM ÜRÜNLERE YORUM EKLEME SİSTEMİ")
    print("\n1. Tüm ürünlere yorum ekle")
    print("2. Belirli bir ürüne yorum ekle")

    # Otomatik olarak tüm ürünlere ekle
    generator.add_reviews_to_all_products()

    generator.session.close()


if __name__ == "__main__":
    main()