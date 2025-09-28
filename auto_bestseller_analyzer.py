#!/usr/bin/env python3
"""
🚀 OTOMATİK BESTSELLER ANALİZ SİSTEMİ
Her gün çalışır, en çok satan ürünleri analiz eder
Neden 1. sırada olduklarını otomatik tespit eder
"""

import schedule
import time
from datetime import datetime
from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
from collections import Counter, defaultdict
import json

class AutoBestsellerAnalyzer:
    """Otomatik bestseller analiz sistemi"""

    def __init__(self):
        self.session = SessionLocal()
        self.ai = TurkishReviewAI()
        self.analysis_history = []

    def analyze_success_formula(self, product_id):
        """Bir ürünün başarı formülünü analiz et"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        if not reviews:
            return None

        # BAŞARI FAKTÖRLERİ
        success_factors = {
            'viral_effect': 0,
            'social_proof': 0,
            'value_perception': 0,
            'quality_trust': 0,
            'trend_following': 0,
            'emotional_connection': 0,
            'functional_need': 0,
            'price_advantage': 0
        }

        # Viral etkiyi ölç
        viral_keywords = ['herkes', 'soruyor', 'nereden', 'aldın', 'instagram',
                         'arkadaş', 'tavsiye', 'önerdi', 'gördüm', 'beğenildi']

        # Değer algısını ölç
        value_keywords = ['fiyat', 'değer', 'ucuz', 'uygun', 'mağaza',
                         'katı', 'bu paraya', 'fırsat', 'kaçmaz']

        # Kalite güvenini ölç
        quality_keywords = ['kalite', 'sağlam', 'dayanıklı', 'orijinal',
                          'marka', 'güvenilir', 'dikiş', 'kumaş', 'malzeme']

        # Trend takibini ölç
        trend_keywords = ['trend', 'moda', 'yeni sezon', 'popüler',
                         'fenomen', 'viral', 'gündem']

        # Duygusal bağı ölç
        emotion_keywords = ['bayıldım', 'aşık', 'harika', 'mükemmel',
                          'muhteşem', 'güzel', 'şık', 'tarz']

        # Her yorumu analiz et
        for review in reviews:
            text = review.review_text.lower()

            # Viral etki
            if any(word in text for word in viral_keywords):
                success_factors['viral_effect'] += 1

            # Sosyal kanıt
            if review.helpful_count > 5:
                success_factors['social_proof'] += 1

            # Değer algısı
            if any(word in text for word in value_keywords):
                success_factors['value_perception'] += 1

            # Kalite güveni
            if any(word in text for word in quality_keywords):
                success_factors['quality_trust'] += 1

            # Trend takibi
            if any(word in text for word in trend_keywords):
                success_factors['trend_following'] += 1

            # Duygusal bağ
            if any(word in text for word in emotion_keywords):
                success_factors['emotional_connection'] += 1

            # Fonksiyonel ihtiyaç
            if 'ihtiyaç' in text or 'lazım' in text or 'gerek' in text:
                success_factors['functional_need'] += 1

            # Fiyat avantajı
            if 'ucuz' in text or 'hesaplı' in text or 'ekonomik' in text:
                success_factors['price_advantage'] += 1

        # Yüzdeleri hesapla
        total_reviews = len(reviews)
        for factor in success_factors:
            success_factors[factor] = (success_factors[factor] / total_reviews) * 100

        # En güçlü faktörleri bul
        top_factors = sorted(success_factors.items(), key=lambda x: x[1], reverse=True)[:3]

        # BAŞARI FORMÜLÜ
        formula = {
            'product_name': product.name,
            'total_reviews': total_reviews,
            'average_rating': sum(r.rating for r in reviews) / total_reviews,
            'success_factors': success_factors,
            'top_3_factors': top_factors,
            'viral_score': success_factors['viral_effect'] + success_factors['social_proof'],
            'value_score': success_factors['value_perception'] + success_factors['price_advantage'],
            'trust_score': success_factors['quality_trust'] + success_factors['social_proof'],
            'formula': self._generate_formula(top_factors)
        }

        return formula

    def _generate_formula(self, top_factors):
        """Başarı formülü oluştur"""

        formulas = {
            'viral_effect': "Viral Döngü: Çok satan → Daha çok yorum → Daha çok güven → Daha çok satış",
            'social_proof': "Sosyal Onay: Herkes alıyor → Ben de almalıyım → FOMO etkisi",
            'value_perception': "Değer Algısı: Gerçek fiyat < Algılanan değer = Kazanç hissi",
            'quality_trust': "Kalite Güveni: Kaliteli görünüm + Olumlu yorumlar = Güven",
            'trend_following': "Trend Takibi: Moda olan → Sosyal medyada paylaşılan → Daha çok aranan",
            'emotional_connection': "Duygusal Bağ: Görsel çekicilik + Kişisel stil = Satın alma dürtüsü",
            'functional_need': "Fonksiyonel İhtiyaç: Gerçek ihtiyaç + Uygun çözüm = Hızlı karar",
            'price_advantage': "Fiyat Avantajı: Düşük fiyat + Yüksek kalite algısı = Fırsat"
        }

        # En güçlü 3 faktörün formülünü birleştir
        formula_parts = []
        for factor, score in top_factors:
            if factor in formulas:
                formula_parts.append(f"({score:.1f}%) {formulas[factor]}")

        return " + ".join(formula_parts)

    def find_viral_patterns(self, product_id):
        """Viral olma pattern'lerini tespit et"""

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        patterns = {
            'organic_marketing': [],
            'word_of_mouth': [],
            'social_media_effect': [],
            'influencer_impact': [],
            'bandwagon_effect': []
        }

        for review in reviews:
            text = review.review_text.lower()

            # Organik pazarlama
            if 'nereden aldın' in text or 'soruyor' in text:
                patterns['organic_marketing'].append(review.reviewer_name)

            # Ağızdan ağıza
            if 'arkadaş' in text and ('önerdi' in text or 'tavsiye' in text):
                patterns['word_of_mouth'].append(review.reviewer_name)

            # Sosyal medya etkisi
            if 'instagram' in text or 'tiktok' in text or 'youtube' in text:
                patterns['social_media_effect'].append(review.reviewer_name)

            # Influencer etkisi
            if 'influencer' in text or 'fenomen' in text or 'ünlü' in text:
                patterns['influencer_impact'].append(review.reviewer_name)

            # Çoğunluk etkisi
            if 'herkes' in text and ('alıyor' in text or 'kullanıyor' in text):
                patterns['bandwagon_effect'].append(review.reviewer_name)

        return patterns

    def generate_daily_report(self):
        """Günlük otomatik rapor oluştur"""

        print("\n" + "="*80)
        print(f"📊 OTOMATİK BESTSELLER ANALİZ RAPORU - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80)

        # Tüm ürünleri analiz et
        products = self.session.query(Product).all()

        results = []
        for product in products:
            formula = self.analyze_success_formula(product.id)
            if formula:
                viral_patterns = self.find_viral_patterns(product.id)

                results.append({
                    'product': product.name,
                    'formula': formula,
                    'viral_patterns': viral_patterns
                })

        # En başarılı ürünü bul
        if results:
            best_product = max(results, key=lambda x: x['formula']['viral_score'])

            print(f"\n🏆 EN BAŞARILI ÜRÜN: {best_product['product']}")
            print(f"   Viral Skor: {best_product['formula']['viral_score']:.1f}%")
            print(f"   Değer Skoru: {best_product['formula']['value_score']:.1f}%")
            print(f"   Güven Skoru: {best_product['formula']['trust_score']:.1f}%")

            print(f"\n📈 BAŞARI FORMÜLÜ:")
            print(f"   {best_product['formula']['formula']}")

            print(f"\n🔥 VİRAL PATTERN'LER:")
            for pattern_type, users in best_product['viral_patterns'].items():
                if users:
                    print(f"   • {pattern_type}: {len(users)} kişi")

            # Raporu kaydet
            report = {
                'date': datetime.now().isoformat(),
                'best_product': best_product,
                'all_results': results
            }

            with open(f'reports/daily_report_{datetime.now().strftime("%Y%m%d")}.json', 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)

            print(f"\n✅ Rapor kaydedildi: reports/daily_report_{datetime.now().strftime('%Y%m%d')}.json")

        return results

    def continuous_monitoring(self):
        """Sürekli izleme ve analiz"""

        print("\n🚀 OTOMATİK BESTSELLER ANALİZ SİSTEMİ BAŞLATILDI")
        print("⏰ Her 6 saatte bir analiz yapılacak")
        print("📊 Günlük raporlar otomatik oluşturulacak")

        # İlk analizi hemen yap
        self.generate_daily_report()

        # Zamanlama ayarla
        schedule.every(6).hours.do(self.generate_daily_report)
        schedule.every().day.at("09:00").do(self.send_morning_insights)
        schedule.every().day.at("18:00").do(self.send_evening_summary)

        # Sürekli çalış
        while True:
            schedule.run_pending()
            time.sleep(60)  # Her dakika kontrol et

    def send_morning_insights(self):
        """Sabah içgörü raporu"""
        print("\n☀️ SABAH İÇGÖRÜ RAPORU")
        print("="*60)

        # En çok yorum alan ürünler
        products = self.session.query(Product).all()
        for product in products:
            review_count = self.session.query(ProductReview).filter_by(product_id=product.id).count()
            if review_count > 0:
                print(f"📦 {product.name}: {review_count} yorum")

                # Son 24 saatte eklenen yorumlar
                recent = self.session.query(ProductReview).filter_by(product_id=product.id).limit(5).all()
                for r in recent[:2]:
                    print(f"   • {r.reviewer_name}: \"{r.review_text[:50]}...\"")

    def send_evening_summary(self):
        """Akşam özet raporu"""
        print("\n🌙 AKŞAM ÖZET RAPORU")
        print("="*60)

        # Günün en çok bahsedilen özellikleri
        all_reviews = self.session.query(ProductReview).all()
        all_keywords = []

        for review in all_reviews:
            if review.key_phrases:
                all_keywords.extend(review.key_phrases)

        top_keywords = Counter(all_keywords).most_common(10)

        print("🔥 Günün Trend Kelimeleri:")
        for keyword, count in top_keywords:
            print(f"   • {keyword}: {count} kez")

    def detect_emerging_trends(self):
        """Yükselen trendleri tespit et"""

        reviews = self.session.query(ProductReview).order_by(ProductReview.review_date.desc()).limit(100).all()

        # Son yorumlarda geçen kelimeler
        recent_words = []
        for review in reviews:
            words = review.review_text.lower().split()
            recent_words.extend(words)

        # En çok tekrarlanan kelimeler
        word_freq = Counter(recent_words)

        # Trend olabilecek kelimeler
        trends = []
        trend_keywords = ['yeni', 'trend', 'moda', 'sezon', 'popüler', 'viral', 'herkes']

        for word, count in word_freq.most_common(50):
            if any(trend in word for trend in trend_keywords):
                trends.append((word, count))

        return trends


def main():
    """Ana fonksiyon"""

    analyzer = AutoBestsellerAnalyzer()

    print("="*80)
    print("🚀 OTOMATİK BESTSELLER ANALİZ SİSTEMİ")
    print("="*80)
    print("\n1. Tek seferlik analiz")
    print("2. Sürekli izleme modu")
    print("3. Trend analizi")
    print("4. Viral pattern analizi")

    # Direkt analiz yap
    print("\n📊 Analiz başlatılıyor...")
    analyzer.generate_daily_report()

    # Trend analizi
    print("\n🔥 YÜKSELEN TRENDLER:")
    trends = analyzer.detect_emerging_trends()
    for word, count in trends[:5]:
        print(f"   • {word}: {count} kez")

    # Viral pattern'ler
    first_product = analyzer.session.query(Product).first()
    if first_product:
        patterns = analyzer.find_viral_patterns(first_product.id)
        print(f"\n🌟 {first_product.name} VİRAL ANALİZİ:")
        for pattern_type, users in patterns.items():
            if users:
                print(f"   • {pattern_type.replace('_', ' ').title()}: {len(users)} kişi")


if __name__ == "__main__":
    main()