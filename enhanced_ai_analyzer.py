#!/usr/bin/env python3
"""
🚀 GELİŞMİŞ AI ANALİZ SİSTEMİ
Manus.AI + Mevcut sistem entegrasyonu
"""

from database import SessionLocal, Product, ProductReview
from turkish_review_ai import TurkishReviewAI
from manus_ai_integration import ManusAIClient, ManusAIAnalyzer
from collections import Counter, defaultdict
import json
from datetime import datetime
import os

class EnhancedAIAnalyzer:
    """Gelişmiş AI analiz sistemi - Manus.AI destekli"""

    def __init__(self, use_manus=True):
        self.session = SessionLocal()
        self.local_ai = TurkishReviewAI()
        self.use_manus = use_manus

        # Manus.AI'yi başlat (eğer API key varsa)
        self.manus_ai = None
        if use_manus:
            api_key = os.getenv('MANUS_API_KEY')
            if api_key:
                self.manus_ai = ManusAIAnalyzer()
                print("✅ Manus.AI entegrasyonu aktif")
            else:
                print("⚠️ Manus.AI API anahtarı bulunamadı, lokal analiz kullanılacak")
                self.use_manus = False

    def analyze_product_comprehensive(self, product_id):
        """
        Ürünü kapsamlı analiz et - Hem lokal hem Manus.AI

        Args:
            product_id: Ürün ID

        Returns:
            Kapsamlı analiz raporu
        """
        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        print("\n" + "="*80)
        print(f"🚀 GELİŞMİŞ AI ANALİZİ: {product.name}")
        print("="*80)

        # 1. LOKAL ANALİZ (her zaman çalışır)
        print("\n📊 AŞAMA 1: Lokal AI Analizi...")
        local_analysis = self._perform_local_analysis(product, reviews)

        # 2. MANUS.AI ANALİZİ (eğer aktifse)
        manus_analysis = None
        if self.use_manus and self.manus_ai:
            print("\n🤖 AŞAMA 2: Manus.AI Derin Analizi...")
            try:
                review_data = [
                    {
                        'review_text': r.review_text,
                        'rating': r.rating,
                        'reviewer_name': r.reviewer_name,
                        'product_name': product.name
                    }
                    for r in reviews
                ]
                manus_analysis = self.manus_ai.analyze_product_reviews(product_id, review_data)
            except Exception as e:
                print(f"⚠️ Manus.AI analizi başarısız: {e}")

        # 3. SONUÇLARI BİRLEŞTİR
        print("\n🔄 AŞAMA 3: Sonuçları Birleştirme...")
        final_analysis = self._merge_analyses(local_analysis, manus_analysis)

        # 4. RAPOR OLUŞTUR
        print("\n📝 AŞAMA 4: Rapor Hazırlama...")
        report = self._generate_comprehensive_report(product, final_analysis)

        # Raporu kaydet
        report_filename = f"reports/ai_analysis_{product_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("reports", exist_ok=True)

        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Analiz tamamlandı! Rapor: {report_filename}")

        return report

    def _perform_local_analysis(self, product, reviews):
        """Lokal AI ile analiz yap"""

        analysis = {
            'total_reviews': len(reviews),
            'average_rating': sum(r.rating for r in reviews) / len(reviews) if reviews else 0,
            'sentiment_distribution': defaultdict(int),
            'purchase_reasons': [],
            'key_features': [],
            'customer_segments': defaultdict(list)
        }

        # Her yorumu analiz et
        for review in reviews:
            # Sentiment
            if review.sentiment_score > 0.7:
                analysis['sentiment_distribution']['positive'] += 1
            elif review.sentiment_score < 0.3:
                analysis['sentiment_distribution']['negative'] += 1
            else:
                analysis['sentiment_distribution']['neutral'] += 1

            # Satın alma nedenleri
            if review.purchase_reasons:
                analysis['purchase_reasons'].extend(review.purchase_reasons)

            # Anahtar özellikler
            if review.key_phrases:
                analysis['key_features'].extend(review.key_phrases)

        # En çok tekrarlanan öğeler
        analysis['top_purchase_reasons'] = Counter(analysis['purchase_reasons']).most_common(5)
        analysis['top_features'] = Counter(analysis['key_features']).most_common(10)

        # Müşteri segmentasyonu
        for review in reviews:
            text = review.review_text.lower()

            if 'kalite' in text or 'sağlam' in text:
                analysis['customer_segments']['quality_focused'].append(review.reviewer_name)
            if 'fiyat' in text or 'ucuz' in text:
                analysis['customer_segments']['price_sensitive'].append(review.reviewer_name)
            if 'arkadaş' in text or 'tavsiye' in text:
                analysis['customer_segments']['social_influenced'].append(review.reviewer_name)
            if 'trend' in text or 'moda' in text:
                analysis['customer_segments']['trend_follower'].append(review.reviewer_name)

        return analysis

    def _merge_analyses(self, local, manus):
        """Lokal ve Manus.AI analizlerini birleştir"""

        merged = {
            'local_analysis': local,
            'manus_analysis': manus,
            'combined_insights': {}
        }

        # Eğer Manus.AI analizi varsa, içgörüleri birleştir
        if manus:
            merged['combined_insights'] = {
                'confidence_level': 'high',
                'data_sources': ['local_ai', 'manus_ai'],
                'key_findings': self._extract_key_findings(local, manus)
            }
        else:
            merged['combined_insights'] = {
                'confidence_level': 'medium',
                'data_sources': ['local_ai'],
                'key_findings': self._extract_key_findings(local, None)
            }

        return merged

    def _extract_key_findings(self, local, manus):
        """Ana bulguları çıkar"""

        findings = []

        # Lokal bulgular
        if local['top_purchase_reasons']:
            top_reason = local['top_purchase_reasons'][0]
            findings.append(f"En önemli satın alma nedeni: {top_reason[0]} ({top_reason[1]} kez)")

        if local['average_rating'] >= 4.0:
            findings.append(f"Yüksek müşteri memnuniyeti: {local['average_rating']:.1f}/5")

        # Manus.AI bulguları
        if manus and 'success_formula' in manus:
            findings.append("Başarı formülü tespit edildi")

        if manus and 'viral_potential' in manus:
            findings.append("Viral potansiyel analizi mevcut")

        return findings

    def _generate_comprehensive_report(self, product, analysis):
        """Kapsamlı rapor oluştur"""

        report = {
            'report_date': datetime.now().isoformat(),
            'product': {
                'id': product.id,
                'name': product.name,
                'category': product.category,
                'price': float(product.price) if product.price else 0,
                'url': product.url
            },
            'analysis': analysis,
            'executive_summary': self._create_executive_summary(product, analysis),
            'recommendations': self._generate_recommendations(analysis),
            'action_items': self._create_action_items(analysis)
        }

        return report

    def _create_executive_summary(self, product, analysis):
        """Yönetici özeti oluştur"""

        local = analysis.get('local_analysis', {})

        summary = {
            'product_name': product.name,
            'total_reviews_analyzed': local.get('total_reviews', 0),
            'average_rating': local.get('average_rating', 0),
            'sentiment': {
                'positive': local['sentiment_distribution'].get('positive', 0),
                'neutral': local['sentiment_distribution'].get('neutral', 0),
                'negative': local['sentiment_distribution'].get('negative', 0)
            },
            'key_success_factors': [],
            'viral_potential': 'Unknown',
            'market_position': self._determine_market_position(local)
        }

        # Başarı faktörleri
        if local['top_purchase_reasons']:
            summary['key_success_factors'] = [reason[0] for reason in local['top_purchase_reasons'][:3]]

        # Manus.AI özeti ekle
        if analysis.get('manus_analysis'):
            summary['enhanced_insights_available'] = True
            summary['viral_potential'] = 'High'  # Manus.AI'den gelecek

        return summary

    def _determine_market_position(self, analysis):
        """Pazar pozisyonunu belirle"""

        rating = analysis.get('average_rating', 0)
        reviews = analysis.get('total_reviews', 0)

        if rating >= 4.5 and reviews >= 50:
            return "Market Leader"
        elif rating >= 4.0 and reviews >= 20:
            return "Strong Competitor"
        elif rating >= 3.5:
            return "Average Performer"
        else:
            return "Needs Improvement"

    def _generate_recommendations(self, analysis):
        """Öneriler oluştur"""

        recommendations = []
        local = analysis.get('local_analysis', {})

        # Sentiment bazlı öneriler
        sentiment_dist = local.get('sentiment_distribution', {})
        if sentiment_dist.get('positive', 0) > sentiment_dist.get('negative', 0) * 3:
            recommendations.append({
                'type': 'marketing',
                'priority': 'high',
                'action': 'Olumlu yorumları pazarlama materyallerinde kullanın',
                'reason': 'Yüksek pozitif sentiment oranı'
            })

        # Müşteri segmenti bazlı öneriler
        segments = local.get('customer_segments', {})
        if len(segments.get('price_sensitive', [])) > 10:
            recommendations.append({
                'type': 'pricing',
                'priority': 'medium',
                'action': 'Fiyat odaklı kampanyalar düzenleyin',
                'reason': 'Fiyat hassasiyeti yüksek müşteri segmenti'
            })

        if len(segments.get('social_influenced', [])) > 5:
            recommendations.append({
                'type': 'social_media',
                'priority': 'high',
                'action': 'Influencer işbirlikleri ve referans programları başlatın',
                'reason': 'Sosyal etki altında satın alma eğilimi'
            })

        # Manus.AI önerileri
        if analysis.get('manus_analysis') and 'marketing_insights' in analysis['manus_analysis']:
            recommendations.append({
                'type': 'ai_powered',
                'priority': 'high',
                'action': 'Manus.AI önerilerini uygulayın',
                'reason': 'Gelişmiş AI analizi mevcut'
            })

        return recommendations

    def _create_action_items(self, analysis):
        """Aksiyona dönük maddeler oluştur"""

        action_items = [
            {
                'id': 1,
                'task': 'En çok bahsedilen özellikleri ön plana çıkarın',
                'deadline': '1 hafta',
                'responsible': 'Pazarlama',
                'status': 'pending'
            },
            {
                'id': 2,
                'task': 'Negatif yorumları analiz edin ve iyileştirme planı hazırlayın',
                'deadline': '2 hafta',
                'responsible': 'Ürün Geliştirme',
                'status': 'pending'
            },
            {
                'id': 3,
                'task': 'Viral potansiyeli yüksek yorumları sosyal medyada paylaşın',
                'deadline': '3 gün',
                'responsible': 'Sosyal Medya',
                'status': 'pending'
            }
        ]

        return action_items

    def quick_analysis(self, product_id):
        """Hızlı analiz - sadece özet bilgi"""

        product = self.session.query(Product).filter_by(id=product_id).first()
        if not product:
            return None

        reviews = self.session.query(ProductReview).filter_by(product_id=product_id).all()

        # Hızlı metrikleri hesapla
        total = len(reviews)
        avg_rating = sum(r.rating for r in reviews) / total if total > 0 else 0
        positive = sum(1 for r in reviews if r.sentiment_score > 0.7)

        # En çok tekrarlanan satın alma nedenleri
        all_reasons = []
        for r in reviews:
            if r.purchase_reasons:
                all_reasons.extend(r.purchase_reasons)

        top_reasons = Counter(all_reasons).most_common(3)

        return {
            'product_name': product.name,
            'total_reviews': total,
            'average_rating': avg_rating,
            'positive_percentage': (positive / total * 100) if total > 0 else 0,
            'top_purchase_reasons': top_reasons,
            'quick_verdict': self._get_quick_verdict(avg_rating, total, positive)
        }

    def _get_quick_verdict(self, rating, total, positive):
        """Hızlı karar ver"""

        if rating >= 4.5 and total >= 50 and positive >= 40:
            return "⭐ BESTSELLER POTANSİYELİ"
        elif rating >= 4.0 and total >= 20:
            return "✅ BAŞARILI ÜRÜN"
        elif rating >= 3.5:
            return "📊 ORTALAMA PERFORMANS"
        else:
            return "⚠️ İYİLEŞTİRME GEREKLİ"


def main():
    """Test ve demo"""

    print("="*80)
    print("🚀 GELİŞMİŞ AI ANALİZ SİSTEMİ")
    print("="*80)

    analyzer = EnhancedAIAnalyzer(use_manus=False)  # Şimdilik Manus.AI'sız

    # İlk ürünü analiz et
    first_product = analyzer.session.query(Product).first()

    if first_product:
        # Hızlı analiz
        print("\n⚡ HIZLI ANALİZ:")
        quick = analyzer.quick_analysis(first_product.id)

        if quick:
            print(f"\n📦 Ürün: {quick['product_name']}")
            print(f"⭐ Ortalama: {quick['average_rating']:.1f}/5")
            print(f"📊 Toplam: {quick['total_reviews']} yorum")
            print(f"😊 Pozitif: %{quick['positive_percentage']:.1f}")
            print(f"\n🎯 En Önemli Satın Alma Nedenleri:")
            for reason, count in quick['top_purchase_reasons']:
                print(f"   • {reason}: {count} kez")
            print(f"\n🏆 SONUÇ: {quick['quick_verdict']}")

        # Tam analiz
        print("\n" + "-"*60)
        print("📊 KAPSAMLI ANALİZ BAŞLIYOR...")
        full_report = analyzer.analyze_product_comprehensive(first_product.id)

        if full_report:
            print("\n📈 YÖNETİCİ ÖZETİ:")
            summary = full_report['executive_summary']
            print(f"   Pazar Pozisyonu: {summary['market_position']}")
            print(f"   Başarı Faktörleri: {', '.join(summary['key_success_factors'][:3])}")

            print("\n💡 ÖNERİLER:")
            for rec in full_report['recommendations'][:3]:
                print(f"   [{rec['priority'].upper()}] {rec['action']}")

    analyzer.session.close()


if __name__ == "__main__":
    main()