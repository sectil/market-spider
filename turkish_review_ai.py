#!/usr/bin/env python3
"""
Turkish Review AI - Müşteri yorumlarını analiz eden özel yapay zeka
NO FALLBACK - Tamamen özel geliştirilen Türkçe doğal dil işleme motoru
"""

import re
import math
from typing import List, Dict, Tuple
from collections import Counter, defaultdict
import statistics

class TurkishReviewAI:
    """Türkçe yorum analizi için özel geliştirilmiş yapay zeka"""

    def __init__(self):
        # Türkçe sentiment kelimeleri ve ağırlıkları
        self.positive_words = {
            # Kalite
            'kaliteli': 0.9, 'sağlam': 0.8, 'dayanıklı': 0.8, 'güzel': 0.7,
            'harika': 0.9, 'mükemmel': 1.0, 'muhteşem': 0.95, 'süper': 0.85,
            'güvenilir': 0.8, 'başarılı': 0.7, 'efsane': 0.9, 'şahane': 0.85,

            # Fiyat/Performans
            'uygun': 0.6, 'ucuz': 0.5, 'hesaplı': 0.6, 'değer': 0.7,
            'kazandırıyor': 0.8, 'ekonomik': 0.6, 'avantajlı': 0.7,

            # Hizmet
            'hızlı': 0.7, 'sorunsuz': 0.8, 'düzgün': 0.6, 'titiz': 0.7,
            'özenli': 0.7, 'dikkatli': 0.6, 'profesyonel': 0.8,

            # Memnuniyet
            'memnun': 0.8, 'mutlu': 0.7, 'beğendim': 0.7, 'sevdim': 0.7,
            'tavsiye': 0.85, 'öneririm': 0.85, 'pişman değilim': 0.7,
            'teşekkür': 0.6, 'teşekkürler': 0.6, 'başarılı': 0.7,

            # Konforbuna
            'rahat': 0.7, 'konforlu': 0.7, 'yumuşak': 0.6, 'hafif': 0.6,
            'pratik': 0.6, 'kullanışlı': 0.7, 'ferah': 0.6,

            # Görünüm
            'zarif': 0.7, 'şık': 0.7, 'güzel duruyor': 0.8, 'yakışmış': 0.7,
            'modern': 0.6, 'estetik': 0.7, 'hoş': 0.6, 'kibar': 0.6
        }

        self.negative_words = {
            # Kalite Sorunları
            'kötü': -0.8, 'kalitesiz': -0.9, 'berbat': -1.0, 'rezalet': -0.95,
            'dandik': -0.85, 'çöp': -0.9, 'sahte': -0.9, 'bozuk': -0.85,
            'kırık': -0.8, 'defolu': -0.8, 'hatalı': -0.7, 'çakma': -0.8,

            # Hayal Kırıklığı
            'pişman': -0.8, 'hayal kırıklığı': -0.9, 'aldatıldım': -0.9,
            'kandırıldım': -0.9, 'yanıltıcı': -0.8, 'aldanmayın': -0.85,
            'sakın': -0.7, 'almayın': -0.8, 'uzak durun': -0.85,

            # Hizmet Sorunları
            'yavaş': -0.6, 'geç': -0.6, 'ulaşmadı': -0.8, 'gecikti': -0.6,
            'ilgisiz': -0.7, 'kaba': -0.7, 'saygısız': -0.8, 'özensiz': -0.7,

            # Uyumsuzluk
            'farklı': -0.5, 'uymuyor': -0.7, 'büyük': -0.5, 'küçük': -0.5,
            'dar': -0.6, 'bol': -0.5, 'kısa': -0.5, 'uzun': -0.4,

            # İade/Değişim
            'iade': -0.7, 'değişim': -0.6, 'geri gönderdim': -0.8,
            'iade ettim': -0.8, 'geri yolladım': -0.8, 'iade edeceğim': -0.7
        }

        # Satın alma nedeni kalıpları
        self.purchase_patterns = {
            'fiyat': ['fiyat', 'ucuz', 'uygun', 'indirim', 'kampanya', 'taksit', 'ekonomik'],
            'kalite': ['kalite', 'sağlam', 'dayanıklı', 'güvenilir', 'orijinal'],
            'marka': ['marka', 'güvenilir marka', 'tanınmış', 'bilindik'],
            'ihtiyaç': ['ihtiyaç', 'lazım', 'gerekli', 'mecbur', 'zorunlu'],
            'önerildi': ['tavsiye', 'önerdi', 'söyledi', 'duydum', 'arkadaş'],
            'beğeni': ['beğendim', 'hoşuma gitti', 'güzel', 'sevdim', 'güzel durdu'],
            'hediye': ['hediye', 'doğum günü', 'yıldönümü', 'sevgiliye', 'anneme'],
            'promosyon': ['kargo bedava', 'ücretsiz kargo', 'hızlı kargo', '2 al 1 öde']
        }

        # Davranış kalıpları
        self.behavior_patterns = {
            'dürtüsel_alıcı': ['hemen aldım', 'düşünmeden', 'anında', 'direkt'],
            'araştırmacı_alıcı': ['araştırdım', 'karşılaştırdım', 'inceledim', 'yorumları okudum'],
            'fiyat_odaklı': ['en ucuz', 'fiyat performans', 'bütçeme uygun', 'kampanya'],
            'kalite_odaklı': ['kaliteli', 'orijinal', 'güvenilir', 'sağlam'],
            'marka_sadık': ['her zaman', 'yıllardır', 'güveniyorum', 'vazgeçmem'],
            'yenilikçi': ['yeni çıktı', 'trend', 'moda', 'son model'],
            'güven_arayan': ['yorumlara güvendim', 'tavsiye edildi', 'herkes almış']
        }

        # Türkçe dil özellikleri için yardımcı fonksiyonlar
        self.turkish_lower = str.maketrans('İIĞÜŞÖÇ', 'iığüşöç')

    def analyze_review(self, review_text: str) -> Dict:
        """Tek bir yorumu analiz et"""
        if not review_text:
            return self._empty_analysis()

        # Metni normalize et
        normalized_text = self._normalize_text(review_text)

        # Analizler
        sentiment = self._calculate_sentiment(normalized_text)
        key_phrases = self._extract_key_phrases(normalized_text)
        purchase_reasons = self._detect_purchase_reasons(normalized_text)
        pros_cons = self._extract_pros_cons(normalized_text)
        behavior_type = self._detect_behavior_type(normalized_text)

        return {
            'sentiment_score': sentiment['score'],
            'sentiment_label': sentiment['label'],
            'confidence': sentiment['confidence'],
            'key_phrases': key_phrases,
            'purchase_reasons': purchase_reasons,
            'pros': pros_cons['pros'],
            'cons': pros_cons['cons'],
            'behavior_type': behavior_type,
            'word_count': len(normalized_text.split()),
            'exclamation_count': review_text.count('!'),
            'question_count': review_text.count('?')
        }

    def analyze_bulk_reviews(self, reviews: List[Dict]) -> Dict:
        """Toplu yorum analizi - İnsan davranışlarını çıkar"""
        if not reviews:
            return self._empty_bulk_analysis()

        all_analyses = []
        for review in reviews:
            analysis = self.analyze_review(review.get('text', ''))
            analysis['rating'] = review.get('rating', 0)
            analysis['verified'] = review.get('verified', False)
            analysis['helpful'] = review.get('helpful_count', 0)
            all_analyses.append(analysis)

        # Toplu istatistikler
        sentiment_scores = [a['sentiment_score'] for a in all_analyses]
        avg_sentiment = statistics.mean(sentiment_scores) if sentiment_scores else 0

        # En sık satın alma nedenleri
        all_reasons = []
        for a in all_analyses:
            all_reasons.extend(a['purchase_reasons'])
        reason_counts = Counter(all_reasons)

        # Davranış tipleri dağılımı
        behavior_types = [a['behavior_type'] for a in all_analyses if a['behavior_type']]
        behavior_dist = Counter(behavior_types)

        # Artı ve eksiler
        all_pros = []
        all_cons = []
        for a in all_analyses:
            all_pros.extend(a['pros'])
            all_cons.extend(a['cons'])

        pros_counts = Counter(all_pros).most_common(10)
        cons_counts = Counter(all_cons).most_common(10)

        # İnsan davranışı analizi
        human_insights = self._generate_human_insights(
            all_analyses, reason_counts, behavior_dist, avg_sentiment
        )

        return {
            'total_reviews': len(reviews),
            'average_sentiment': avg_sentiment,
            'sentiment_distribution': self._calculate_sentiment_distribution(sentiment_scores),
            'top_purchase_reasons': reason_counts.most_common(5),
            'behavior_distribution': dict(behavior_dist),
            'top_pros': pros_counts,
            'top_cons': cons_counts,
            'human_insights': human_insights,
            'verified_percentage': sum(1 for a in all_analyses if a['verified']) / len(all_analyses) * 100,
            'recommendation_score': self._calculate_recommendation_score(all_analyses)
        }

    def _normalize_text(self, text: str) -> str:
        """Türkçe metni normalize et"""
        # Küçük harfe çevir (Türkçe karakterler dahil)
        text = text.translate(self.turkish_lower).lower()

        # Gereksiz boşlukları temizle
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _calculate_sentiment(self, text: str) -> Dict:
        """Sentiment analizi yap"""
        words = text.split()
        positive_score = 0
        negative_score = 0
        word_matches = 0

        for word in words:
            # Pozitif kelimeler
            for pos_word, weight in self.positive_words.items():
                if pos_word in word:
                    positive_score += weight
                    word_matches += 1

            # Negatif kelimeler
            for neg_word, weight in self.negative_words.items():
                if neg_word in word:
                    negative_score += abs(weight)
                    word_matches += 1

        # Net skor hesapla
        if positive_score + negative_score == 0:
            net_score = 0
        else:
            net_score = (positive_score - negative_score) / (positive_score + negative_score)

        # Güven skoru
        confidence = min(word_matches / max(len(words) / 10, 1), 1.0)

        # Etiket belirle
        if net_score >= 0.3:
            label = 'pozitif'
        elif net_score <= -0.3:
            label = 'negatif'
        else:
            label = 'nötr'

        return {
            'score': net_score,
            'label': label,
            'confidence': confidence
        }

    def _extract_key_phrases(self, text: str) -> List[str]:
        """Anahtar kelimeleri çıkar"""
        # Basit n-gram analizi
        words = text.split()
        phrases = []

        # Tek kelimeler
        word_freq = Counter(words)
        for word, count in word_freq.most_common(5):
            if len(word) > 3 and count > 1:
                phrases.append(word)

        # İki kelimelik gruplar
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if any(key in bigram for key in ['çok güzel', 'çok kötü', 'tavsiye ederim',
                                             'almayın', 'harika ürün', 'berbat ürün']):
                phrases.append(bigram)

        return phrases[:8]  # En fazla 8 anahtar kelime

    def _detect_purchase_reasons(self, text: str) -> List[str]:
        """Satın alma nedenlerini tespit et"""
        reasons = []

        for reason_type, keywords in self.purchase_patterns.items():
            for keyword in keywords:
                if keyword in text:
                    reasons.append(reason_type)
                    break

        return list(set(reasons))  # Tekrarları kaldır

    def _extract_pros_cons(self, text: str) -> Dict:
        """Artı ve eksileri çıkar"""
        pros = []
        cons = []

        # Pozitif özellikler
        for word, weight in self.positive_words.items():
            if word in text and weight >= 0.7:
                pros.append(word)

        # Negatif özellikler
        for word, weight in self.negative_words.items():
            if word in text and abs(weight) >= 0.7:
                cons.append(word)

        return {
            'pros': pros[:5],  # En fazla 5 artı
            'cons': cons[:5]   # En fazla 5 eksi
        }

    def _detect_behavior_type(self, text: str) -> str:
        """Müşteri davranış tipini tespit et"""
        behavior_scores = {}

        for behavior_type, keywords in self.behavior_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                behavior_scores[behavior_type] = score

        if behavior_scores:
            return max(behavior_scores, key=behavior_scores.get)
        return 'belirsiz'

    def _generate_human_insights(self, analyses: List[Dict], reasons: Counter,
                                behaviors: Counter, avg_sentiment: float) -> Dict:
        """İnsan davranışları hakkında içgörüler üret"""

        insights = {
            'ana_motivasyon': '',
            'müşteri_profili': '',
            'satın_alma_psikolojisi': '',
            'başarı_faktörleri': [],
            'risk_faktörleri': [],
            'tavsiye': ''
        }

        # Ana motivasyon
        if reasons:
            top_reason = reasons.most_common(1)[0][0]
            motivations = {
                'fiyat': 'Müşteriler bu ürünü özellikle uygun fiyatı nedeniyle tercih ediyor. Fiyat-performans dengesi satın alma kararında kritik rol oynuyor.',
                'kalite': 'Ürün kalitesi müşterilerin ana motivasyonu. Dayanıklılık ve güvenilirlik beklentileri satın alma kararını şekillendiriyor.',
                'ihtiyaç': 'Zorunlu ihtiyaç nedeniyle satın alınıyor. Müşteriler alternatif aramadan hızlı karar veriyor.',
                'önerildi': 'Sosyal etki ve tavsiyeler satın almada belirleyici. Müşteriler başkalarının deneyimlerine güveniyor.',
                'beğeni': 'Görsel beğeni ve ilk izlenim satın almayı tetikliyor. Estetik ve stil önemli faktörler.',
                'hediye': 'Hediye amaçlı alımlar yoğunlukta. Özel günler için tercih ediliyor.',
            }
            insights['ana_motivasyon'] = motivations.get(top_reason, 'Çeşitli faktörler satın almayı etkiliyor.')

        # Müşteri profili
        if behaviors:
            top_behavior = behaviors.most_common(1)[0][0]
            profiles = {
                'fiyat_odaklı': 'Fiyata duyarlı, kampanya takipçisi müşteri grubu. İndirim ve promosyonlardan etkileniyor.',
                'kalite_odaklı': 'Kaliteye önem veren, uzun vadeli düşünen müşteri profili. Premium segmente hitap ediyor.',
                'araştırmacı_alıcı': 'Detaylı araştırma yapan, bilinçli tüketici grubu. Yorumları ve özellikleri detaylıca inceliyor.',
                'dürtüsel_alıcı': 'Hızlı karar veren, anlık tatmin arayan müşteri tipi. Görsel etki ve ilk izlenimle hareket ediyor.',
                'marka_sadık': 'Markaya güvenen, sadık müşteri kitlesi. Yeniden satın alma oranı yüksek.',
                'güven_arayan': 'Sosyal onay arayan, güven odaklı müşteri grubu. Yorumlar ve tavsiyelerden yoğun etkileniyor.'
            }
            insights['müşteri_profili'] = profiles.get(top_behavior, 'Karma müşteri profili mevcut.')

        # Satın alma psikolojisi
        if avg_sentiment > 0.5:
            insights['satın_alma_psikolojisi'] = """Müşteriler bu üründen yüksek tatmin sağlıyor.
            Beklentilerin üzerinde performans, pozitif duygusal bağ yaratmış.
            Sosyal kanıt etkisi güçlü - başarılı deneyimler yeni alıcıları teşvik ediyor."""
        elif avg_sentiment < -0.3:
            insights['satın_alma_psikolojisi'] = """Hayal kırıklığı ve pişmanlık duyguları hakim.
            Beklenti-gerçeklik uyumsuzluğu memnuniyetsizlik yaratmış.
            Olumsuz deneyimler potansiyel alıcıları uzaklaştırıyor."""
        else:
            insights['satın_alma_psikolojisi'] = """Karma duygular mevcut.
            Ürün bazı beklentileri karşılarken bazı alanlarda yetersiz kalmış.
            Müşteri segmentine göre tatmin değişkenlik gösteriyor."""

        # Başarı faktörleri
        success_factors = []
        if 'kalite' in reasons and reasons['kalite'] > 2:
            success_factors.append('Kalite algısı güçlü')
        if 'fiyat' in reasons and reasons['fiyat'] > 2:
            success_factors.append('Fiyat avantajı çekici')
        if avg_sentiment > 0.3:
            success_factors.append('Müşteri memnuniyeti yüksek')
        if 'tavsiye' in [word for analysis in analyses for word in analysis['key_phrases']]:
            success_factors.append('Ağızdan ağıza pazarlama etkili')

        insights['başarı_faktörleri'] = success_factors if success_factors else ['Belirgin başarı faktörü yok']

        # Risk faktörleri
        risk_factors = []
        if any(c in ['iade', 'değişim', 'bozuk', 'hatalı'] for analysis in analyses for c in analysis['cons']):
            risk_factors.append('Kalite kontrol sorunları')
        if avg_sentiment < 0:
            risk_factors.append('Genel memnuniyetsizlik riski')
        if 'kargo' in [word for analysis in analyses for word in analysis['cons']]:
            risk_factors.append('Teslimat sorunları')

        insights['risk_faktörleri'] = risk_factors if risk_factors else ['Belirgin risk faktörü yok']

        # Tavsiye
        if avg_sentiment > 0.5 and len(success_factors) > 2:
            insights['tavsiye'] = "✅ Güçlü Tavsiye: Müşteri deneyimi ve geri bildirimler son derece olumlu. Güvenle satın alınabilir."
        elif avg_sentiment > 0:
            insights['tavsiye'] = "👍 Tavsiye Edilir: Genel olarak olumlu deneyimler mevcut. Beklentilerinizi karşılayabilir."
        elif avg_sentiment < -0.3:
            insights['tavsiye'] = "⚠️ Dikkatli Olun: Olumsuz deneyimler yoğunlukta. Alternatiflerini değerlendirin."
        else:
            insights['tavsiye'] = "🤔 Araştırın: Karma yorumlar mevcut. İhtiyacınıza uygunluğunu detaylıca değerlendirin."

        return insights

    def _calculate_sentiment_distribution(self, scores: List[float]) -> Dict:
        """Sentiment dağılımını hesapla"""
        positive = sum(1 for s in scores if s > 0.3)
        negative = sum(1 for s in scores if s < -0.3)
        neutral = len(scores) - positive - negative

        return {
            'pozitif': (positive / len(scores)) * 100 if scores else 0,
            'negatif': (negative / len(scores)) * 100 if scores else 0,
            'nötr': (neutral / len(scores)) * 100 if scores else 0
        }

    def _calculate_recommendation_score(self, analyses: List[Dict]) -> float:
        """Tavsiye skorunu hesapla (0-100)"""
        if not analyses:
            return 0

        # Faktörler ve ağırlıkları
        avg_sentiment = statistics.mean([a['sentiment_score'] for a in analyses])
        avg_rating = statistics.mean([a['rating'] for a in analyses if a['rating']])
        verified_ratio = sum(1 for a in analyses if a['verified']) / len(analyses)

        # Ağırlıklı skor
        score = (
            (avg_sentiment + 1) * 25 +  # -1 to 1 -> 0 to 50
            (avg_rating / 5) * 40 +      # 0 to 5 -> 0 to 40
            verified_ratio * 10          # 0 to 1 -> 0 to 10
        )

        return min(max(score, 0), 100)

    def _empty_analysis(self) -> Dict:
        """Boş analiz sonucu"""
        return {
            'sentiment_score': 0,
            'sentiment_label': 'belirsiz',
            'confidence': 0,
            'key_phrases': [],
            'purchase_reasons': [],
            'pros': [],
            'cons': [],
            'behavior_type': 'belirsiz'
        }

    def _empty_bulk_analysis(self) -> Dict:
        """Boş toplu analiz sonucu"""
        return {
            'total_reviews': 0,
            'average_sentiment': 0,
            'sentiment_distribution': {'pozitif': 0, 'negatif': 0, 'nötr': 0},
            'top_purchase_reasons': [],
            'behavior_distribution': {},
            'top_pros': [],
            'top_cons': [],
            'human_insights': {},
            'verified_percentage': 0,
            'recommendation_score': 0
        }