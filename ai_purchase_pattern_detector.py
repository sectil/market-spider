#!/usr/bin/env python3
"""
🧠 AI SATIN ALMA PATTERN TESPİT SİSTEMİ
Müşteri davranışlarındaki pattern'leri tespit eder
Neden satın aldıklarını derin öğrenir
"""

from database import SessionLocal, Product, ProductReview
from collections import defaultdict, Counter
import numpy as np
from datetime import datetime, timedelta
import json
import re

class AIPurchasePatternDetector:
    """AI destekli satın alma pattern tespit sistemi"""

    def __init__(self):
        self.session = SessionLocal()
        self.patterns = defaultdict(list)
        self.learned_behaviors = {}

    def detect_behavioral_patterns(self, product_id):
        """Davranışsal pattern'leri tespit et"""

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        patterns = {
            'impulse_buying': [],        # Dürtüsel satın alma
            'research_based': [],         # Araştırma bazlı
            'social_influenced': [],      # Sosyal etki
            'price_sensitive': [],        # Fiyat hassasiyeti
            'quality_focused': [],        # Kalite odaklı
            'trend_follower': [],         # Trend takipçisi
            'brand_loyal': [],            # Marka sadakati
            'problem_solver': [],         # Problem çözücü
            'gift_buyer': [],             # Hediye alıcısı
            'repeat_customer': []         # Tekrar eden müşteri
        }

        # Pattern tespiti için anahtar kelimeler
        pattern_keywords = {
            'impulse_buying': ['görünce', 'hemen', 'anında', 'bayıldım', 'dayanamadım',
                              'düşünmeden', 'direk', 'o an', 'acele'],

            'research_based': ['araştırdım', 'karşılaştırdım', 'inceledim', 'yorumları okudum',
                              'baktım', 'kontrol ettim', 'emin olmak', 'detaylı'],

            'social_influenced': ['arkadaş', 'tavsiye', 'önerdi', 'instagram', 'influencer',
                                 'herkes', 'sosyal medya', 'gördüm', 'paylaşım'],

            'price_sensitive': ['fiyat', 'ucuz', 'indirim', 'kampanya', 'bütçe',
                               'ekonomik', 'hesaplı', 'pahalı değil', 'uygun'],

            'quality_focused': ['kalite', 'sağlam', 'dayanıklı', 'orijinal', 'premium',
                               'uzun ömür', 'bozulmaz', 'güvenilir', 'marka'],

            'trend_follower': ['trend', 'moda', 'yeni', 'popüler', 'güncel',
                              'sezon', 'herkes alıyor', 'çok satan', 'viral'],

            'brand_loyal': ['marka', 'güven', 'her zaman', 'yıllardır', 'sürekli',
                           'sadık', 'tercih', 'başka almam', 'tek'],

            'problem_solver': ['ihtiyaç', 'lazım', 'gerek', 'çözüm', 'sorun',
                              'yerine', 'eksik', 'tamamlamak', 'doldurmak'],

            'gift_buyer': ['hediye', 'doğum günü', 'sevgiliye', 'anneye', 'arkadaşa',
                          'sürpriz', 'özel gün', 'yıldönümü', 'armağan'],

            'repeat_customer': ['tekrar', 'yine', 'bir daha', 'ikinci', 'üçüncü',
                               'her seferinde', 'devamlı', 'yeniden', 'aynısından']
        }

        # Her yorumu analiz et
        for review in reviews:
            text = review.review_text.lower()
            reviewer = review.reviewer_name

            # Pattern tespiti
            for pattern_type, keywords in pattern_keywords.items():
                if any(keyword in text for keyword in keywords):
                    patterns[pattern_type].append({
                        'reviewer': reviewer,
                        'text': review.review_text[:100],
                        'rating': review.rating,
                        'confidence': self._calculate_pattern_confidence(text, keywords)
                    })

        return patterns

    def _calculate_pattern_confidence(self, text, keywords):
        """Pattern güven skorunu hesapla"""
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(matches / len(keywords), 1.0)

    def analyze_purchase_journey(self, product_id):
        """Satın alma yolculuğunu analiz et"""

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        journey_stages = {
            'awareness': [],      # Farkındalık
            'interest': [],       # İlgi
            'consideration': [],  # Değerlendirme
            'purchase': [],       # Satın alma
            'satisfaction': [],   # Memnuniyet
            'advocacy': []        # Savunuculuk
        }

        # Aşama tespiti
        for review in reviews:
            text = review.review_text.lower()

            # Farkındalık aşaması
            if any(word in text for word in ['gördüm', 'rastladım', 'denk geldim', 'karşılaştım']):
                journey_stages['awareness'].append(review.reviewer_name)

            # İlgi aşaması
            if any(word in text for word in ['ilgimi çekti', 'merak ettim', 'bakmak istedim']):
                journey_stages['interest'].append(review.reviewer_name)

            # Değerlendirme aşaması
            if any(word in text for word in ['karşılaştırdım', 'yorumları okudum', 'araştırdım']):
                journey_stages['consideration'].append(review.reviewer_name)

            # Satın alma aşaması
            if any(word in text for word in ['aldım', 'sipariş verdim', 'satın aldım']):
                journey_stages['purchase'].append(review.reviewer_name)

            # Memnuniyet aşaması
            if review.rating >= 4 and any(word in text for word in ['memnun', 'mutlu', 'beğendim']):
                journey_stages['satisfaction'].append(review.reviewer_name)

            # Savunuculuk aşaması
            if any(word in text for word in ['tavsiye', 'öneririm', 'kesinlikle alın']):
                journey_stages['advocacy'].append(review.reviewer_name)

        return journey_stages

    def find_conversion_triggers(self, product_id):
        """Satın almaya dönüştüren tetikleyicileri bul"""

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        triggers = {
            'scarcity': 0,          # Kıtlık
            'social_proof': 0,      # Sosyal kanıt
            'authority': 0,         # Otorite
            'reciprocity': 0,       # Karşılıklılık
            'commitment': 0,        # Bağlılık
            'liking': 0,           # Beğeni
            'urgency': 0,          # Aciliyet
            'fear_of_missing': 0,   # Kaçırma korkusu
            'exclusivity': 0,       # Özellik
            'simplicity': 0         # Basitlik
        }

        # Cialdini'nin ikna prensipleri
        trigger_indicators = {
            'scarcity': ['son', 'kalmadı', 'tükeniyor', 'stok', 'sınırlı', 'az kaldı'],
            'social_proof': ['herkes', 'çok satan', '1 numara', 'popüler', 'beğenilen'],
            'authority': ['uzman', 'doktor', 'önerdi', 'tavsiye etti', 'onayladı'],
            'reciprocity': ['hediye', 'ücretsiz', 'bonus', 'ekstra', 'dahil'],
            'commitment': ['denedim', 'kullanıyorum', 'yıllardır', 'sürekli', 'her zaman'],
            'liking': ['bayıldım', 'harika', 'mükemmel', 'muhteşem', 'süper'],
            'urgency': ['acele', 'hemen', 'şimdi', 'bugün', 'yarın'],
            'fear_of_missing': ['kaçırmak', 'fırsat', 'kampanya', 'indirim', 'son gün'],
            'exclusivity': ['özel', 'VIP', 'premium', 'limited', 'sadece'],
            'simplicity': ['kolay', 'basit', 'pratik', 'hızlı', 'rahat']
        }

        # Tetikleyicileri say
        for review in reviews:
            text = review.review_text.lower()

            for trigger_type, indicators in trigger_indicators.items():
                if any(indicator in text for indicator in indicators):
                    triggers[trigger_type] += 1

        # Yüzdelere çevir
        total_reviews = len(reviews) if reviews else 1
        for trigger in triggers:
            triggers[trigger] = (triggers[trigger] / total_reviews) * 100

        return triggers

    def predict_customer_lifetime_value(self, product_id):
        """Müşteri yaşam boyu değerini tahmin et"""

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        clv_indicators = {
            'high_value': [],      # Yüksek değerli müşteriler
            'medium_value': [],    # Orta değerli müşteriler
            'low_value': [],       # Düşük değerli müşteriler
            'churn_risk': []       # Kayıp riski olanlar
        }

        for review in reviews:
            text = review.review_text.lower()
            rating = review.rating

            # Yüksek değerli müşteri göstergeleri
            if rating >= 4 and any(word in text for word in
                ['tekrar alacağım', 'başka renk', 'diğer model', 'arkadaşlara önerdim']):
                clv_indicators['high_value'].append(review.reviewer_name)

            # Orta değerli müşteri
            elif rating >= 3 and rating < 4:
                clv_indicators['medium_value'].append(review.reviewer_name)

            # Düşük değerli müşteri
            elif rating < 3:
                clv_indicators['low_value'].append(review.reviewer_name)

            # Kayıp riski
            if any(word in text for word in ['pişman', 'iade', 'değişim', 'beğenmedim']):
                clv_indicators['churn_risk'].append(review.reviewer_name)

        return clv_indicators

    def generate_ai_insights(self, product_id):
        """AI destekli içgörüler üret"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        # Tüm analizleri topla
        behavioral_patterns = self.detect_behavioral_patterns(product_id)
        purchase_journey = self.analyze_purchase_journey(product_id)
        conversion_triggers = self.find_conversion_triggers(product_id)
        clv_prediction = self.predict_customer_lifetime_value(product_id)

        # En güçlü pattern'leri bul
        strongest_patterns = []
        for pattern_type, customers in behavioral_patterns.items():
            if customers:
                strongest_patterns.append({
                    'type': pattern_type,
                    'count': len(customers),
                    'percentage': (len(customers) / 100) * 100  # 100 yorumdan yüzde
                })

        strongest_patterns.sort(key=lambda x: x['count'], reverse=True)

        # En etkili tetikleyiciler
        top_triggers = sorted(conversion_triggers.items(), key=lambda x: x[1], reverse=True)[:3]

        # AI İçgörüleri
        insights = {
            'product_name': product.name,
            'analysis_date': datetime.now().isoformat(),

            'customer_segments': {
                'primary_segment': strongest_patterns[0]['type'] if strongest_patterns else 'unknown',
                'segment_distribution': strongest_patterns[:3]
            },

            'purchase_motivations': {
                'top_trigger': top_triggers[0] if top_triggers else None,
                'trigger_effectiveness': dict(top_triggers[:5])
            },

            'customer_journey': {
                'advocacy_rate': len(purchase_journey['advocacy']),
                'satisfaction_rate': len(purchase_journey['satisfaction']),
                'consideration_depth': len(purchase_journey['consideration'])
            },

            'revenue_potential': {
                'high_value_customers': len(clv_prediction['high_value']),
                'churn_risk_customers': len(clv_prediction['churn_risk']),
                'retention_opportunity': len(clv_prediction['medium_value'])
            },

            'recommendations': self._generate_recommendations(
                strongest_patterns, top_triggers, clv_prediction
            )
        }

        return insights

    def _generate_recommendations(self, patterns, triggers, clv):
        """Öneriler üret"""

        recommendations = []

        # Pattern bazlı öneriler
        if patterns and patterns[0]['type'] == 'impulse_buying':
            recommendations.append("🎯 Görsel odaklı pazarlama yapın, 'Sınırlı Stok' vurgusu ekleyin")
        elif patterns and patterns[0]['type'] == 'research_based':
            recommendations.append("📊 Detaylı ürün bilgisi ve karşılaştırma tabloları ekleyin")
        elif patterns and patterns[0]['type'] == 'social_influenced':
            recommendations.append("📱 Influencer işbirlikleri ve kullanıcı içerikleri artırın")

        # Tetikleyici bazlı öneriler
        if triggers and triggers[0][0] == 'social_proof':
            recommendations.append("⭐ 'En Çok Satan' ve 'Müşteri Favorisi' etiketlerini kullanın")
        elif triggers and triggers[0][0] == 'scarcity':
            recommendations.append("⏰ Stok sayısı gösterimi ve zamanlı kampanyalar düzenleyin")

        # CLV bazlı öneriler
        if len(clv['high_value']) > 20:
            recommendations.append("💎 Sadakat programı başlatın, VIP müşteri avantajları sunun")
        if len(clv['churn_risk']) > 10:
            recommendations.append("🔄 İade/değişim politikasını iyileştirin, müşteri desteğini güçlendirin")

        return recommendations


def main():
    """Ana fonksiyon"""

    detector = AIPurchasePatternDetector()

    print("="*80)
    print("🧠 AI SATIN ALMA PATTERN TESPİT SİSTEMİ")
    print("="*80)

    # İlk ürünü analiz et
    first_product = detector.session.query(Product).first()

    if first_product:
        print(f"\n📦 Analiz edilen ürün: {first_product.name}")
        print("-"*60)

        # Davranışsal pattern'ler
        print("\n🎭 DAVRANIŞSAL PATTERN'LER:")
        patterns = detector.detect_behavioral_patterns(first_product.id)

        for pattern_type, customers in patterns.items():
            if customers:
                print(f"\n{pattern_type.replace('_', ' ').upper()}: {len(customers)} müşteri")
                if customers:
                    sample = customers[0]
                    print(f"  Örnek: {sample['reviewer']} - \"{sample['text']}...\"")
                    print(f"  Güven: %{sample['confidence']*100:.0f}")

        # Satın alma tetikleyicileri
        print("\n🎯 SATIN ALMA TETİKLEYİCİLERİ:")
        triggers = detector.find_conversion_triggers(first_product.id)

        for trigger, percentage in sorted(triggers.items(), key=lambda x: x[1], reverse=True)[:5]:
            if percentage > 0:
                print(f"  {trigger.replace('_', ' ').title()}: %{percentage:.1f}")

        # Müşteri segmentleri
        print("\n👥 MÜŞTERİ YAŞAM BOYU DEĞERİ:")
        clv = detector.predict_customer_lifetime_value(first_product.id)

        print(f"  Yüksek Değerli: {len(clv['high_value'])} müşteri")
        print(f"  Orta Değerli: {len(clv['medium_value'])} müşteri")
        print(f"  Düşük Değerli: {len(clv['low_value'])} müşteri")
        print(f"  Kayıp Riski: {len(clv['churn_risk'])} müşteri")

        # AI İçgörüleri
        print("\n🤖 AI İÇGÖRÜLERİ:")
        insights = detector.generate_ai_insights(first_product.id)

        if insights['recommendations']:
            print("\n📌 ÖNERİLER:")
            for rec in insights['recommendations']:
                print(f"  {rec}")

        # JSON olarak kaydet
        with open('ai_insights.json', 'w', encoding='utf-8') as f:
            json.dump(insights, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Detaylı rapor kaydedildi: ai_insights.json")


if __name__ == "__main__":
    main()