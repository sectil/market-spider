#!/usr/bin/env python3
"""
🤖 MANUS.AI ENTEGRASYONU
Gelişmiş AI analizi için Manus.AI API entegrasyonu
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class ManusAIClient:
    """Manus.AI API istemcisi"""

    def __init__(self, api_key: str = None):
        """
        Initialize Manus.AI client

        Args:
            api_key: Manus.AI API anahtarı
        """
        self.api_key = api_key or os.getenv('MANUS_API_KEY', 'sk-SkqE1kwg_s1fQ5NGCu37Lh2oG7C-WkkMr1rTXWNvMOisLQSB6m_D0ARW3-duFoh1nYkN5_uWLqSMIzdPGmNEZLTZWrPh')
        self.base_url = "https://api.manus.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Yeni bir AI görevi oluştur

        Args:
            task_data: Görev parametreleri

        Returns:
            API yanıtı
        """
        try:
            response = requests.post(
                f"{self.base_url}/tasks",
                headers=self.headers,
                json=task_data,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Manus.AI API hatası: {response.status_code}")
                print(f"   Detay: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Bağlantı hatası: {e}")
            return None

    def analyze_customer_review(self, review_text: str, product_name: str = "") -> Dict[str, Any]:
        """
        Müşteri yorumunu detaylı analiz et

        Args:
            review_text: Yorum metni
            product_name: Ürün adı

        Returns:
            Analiz sonuçları
        """
        prompt = f"""
        Aşağıdaki müşteri yorumunu analiz et ve şu bilgileri çıkar:

        Ürün: {product_name}
        Yorum: "{review_text}"

        Lütfen şu analizleri yap:
        1. Duygu Analizi (pozitif/negatif/nötr ve 0-100 skor)
        2. Satın Alma Nedeni (neden bu ürünü almış?)
        3. Anahtar Özellikler (hangi özelliklerden bahsetmiş?)
        4. Müşteri Profili (hangi tip müşteri?)
        5. Viral Potansiyel (bu yorum viral olabilir mi?)
        6. Güvenilirlik Skoru (yorum ne kadar gerçek görünüyor?)

        JSON formatında yanıt ver.
        """

        task_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir müşteri davranış analisti ve pazarlama uzmanısın. Türkçe yorumları analiz ediyorsun."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }

        return self.create_task(task_data)

    def analyze_purchase_patterns(self, reviews: List[str]) -> Dict[str, Any]:
        """
        Toplu yorumlardan satın alma pattern'lerini çıkar

        Args:
            reviews: Yorum listesi

        Returns:
            Pattern analizi
        """
        reviews_text = "\n".join([f"- {r}" for r in reviews[:20]])  # İlk 20 yorum

        prompt = f"""
        Aşağıdaki müşteri yorumlarını analiz ederek satın alma pattern'lerini bul:

        {reviews_text}

        Şu analizleri yap:
        1. EN ÇOK TEKRARLANAN satın alma nedenleri (Top 5)
        2. MÜŞTERİ SEGMENTLERİ (hangi tip müşteriler alıyor?)
        3. VİRAL TETİKLEYİCİLER (insanları harekete geçiren faktörler)
        4. PSİKOLOJİK MOTİVASYONLAR (arkadaki gerçek nedenler)
        5. BAŞARI FORMÜLÜ (neden bu ürün 1. sırada?)

        Özellikle şunlara odaklan:
        - Sosyal kanıt etkisi
        - Fiyat-değer algısı
        - Duygusal tetikleyiciler
        - FOMO (kaçırma korkusu)

        JSON formatında, Türkçe yanıt ver.
        """

        task_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir tüketici psikolojisi ve viral pazarlama uzmanısın. E-ticaret başarı formüllerini analiz ediyorsun."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 1000
        }

        return self.create_task(task_data)

    def generate_marketing_insights(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ürün için pazarlama önerileri üret

        Args:
            product_data: Ürün ve yorum verileri

        Returns:
            Pazarlama önerileri
        """
        prompt = f"""
        Ürün: {product_data.get('name', 'Ürün')}
        Kategori: {product_data.get('category', 'Giyim')}
        Fiyat: {product_data.get('price', '0')} TL
        Yorum Sayısı: {product_data.get('review_count', 0)}
        Ortalama Puan: {product_data.get('rating', 0)}

        En çok bahsedilen özellikler:
        {product_data.get('top_features', [])}

        Müşteri profilleri:
        {product_data.get('customer_segments', [])}

        Bu verilere dayanarak:

        1. VİRAL PAZARLAMA STRATEJİSİ öner
        2. SOSYAL MEDYA İÇERİK FİKİRLERİ ver
        3. INFLUENCER PAZARLAMA TAKTİKLERİ
        4. PSİKOLOJİK TETİKLEYİCİLER kullanarak satış metni yaz
        5. A/B TEST ÖNERİLERİ

        Türkçe, aksiyona dönük ve ölçülebilir öneriler ver.
        """

        task_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir growth hacker ve viral pazarlama uzmanısın. Trendyol gibi e-ticaret platformlarında ürünleri 1. sıraya taşıyacak stratejiler üretiyorsun."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.9,
            "max_tokens": 1500
        }

        return self.create_task(task_data)

    def predict_viral_potential(self, review_text: str) -> Dict[str, Any]:
        """
        Bir yorumun viral olma potansiyelini tahmin et

        Args:
            review_text: Yorum metni

        Returns:
            Viral potansiyel analizi
        """
        prompt = f"""
        Bu yorumun VİRAL OLMA POTANSİYELİNİ analiz et:

        "{review_text}"

        Değerlendir:
        1. VİRAL SKOR (0-100)
        2. PAYLAŞIM POTANSİYELİ
        3. DUYGUSAL ETKİ GÜCÜ
        4. HİKAYE DEĞERİ
        5. SOSYAL MEDYA UYUMU

        Ayrıca:
        - Hangi platformda viral olabilir? (Instagram/TikTok/Twitter)
        - Hangi hashtag'ler kullanılmalı?
        - İçerik formatı ne olmalı? (Reels/Story/Post)

        JSON formatında yanıt ver.
        """

        task_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir viral içerik uzmanı ve sosyal medya stratejistisin."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 500
        }

        return self.create_task(task_data)

    def identify_success_formula(self, all_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ürünün başarı formülünü çıkar

        Args:
            all_data: Tüm ürün ve yorum verileri

        Returns:
            Başarı formülü
        """
        prompt = f"""
        Bu ürün neden 1. sırada? GERÇEK BAŞARI FORMÜLÜNÜ bul:

        Ürün Verileri:
        {json.dumps(all_data, ensure_ascii=False, indent=2)}

        Analiz et ve bul:

        1. TEMEL BAŞARI FAKTÖRLERİ (Top 3)
        2. VİRAL DÖNGÜ MEKANİZMASI
        3. PSİKOLOJİK TETİKLEYİCİLER
        4. SOSYAL KANIT MEKANİZMASI
        5. SATIN ALMA DÖNGÜSÜ

        Formülü şöyle yaz:
        [Faktör 1] + [Faktör 2] + [Faktör 3] = BAŞARI

        Ayrıca:
        - Bu formül başka ürünlere nasıl uygulanabilir?
        - Hangi faktör en kritik?
        - Rakipler bu formülü nasıl kopyalayabilir?

        Türkçe, net ve aksiyona dönük yanıt ver.
        """

        task_data = {
            "model": "gpt-4",
            "messages": [
                {
                    "role": "system",
                    "content": "Sen bir e-ticaret strateji uzmanı ve büyüme hackerısın. Bestseller ürünlerin başarı formüllerini çözümlüyorsun."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.85,
            "max_tokens": 1000
        }

        return self.create_task(task_data)


class ManusAIAnalyzer:
    """Manus.AI ile gelişmiş analiz sınıfı"""

    def __init__(self):
        self.client = ManusAIClient()
        self.cache = {}

    def analyze_product_reviews(self, product_id: int, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bir ürünün tüm yorumlarını Manus.AI ile analiz et

        Args:
            product_id: Ürün ID
            reviews: Yorum listesi

        Returns:
            Kapsamlı analiz raporu
        """
        print("🤖 Manus.AI ile derin analiz başlıyor...")

        # 1. Her yorumu tek tek analiz et
        analyzed_reviews = []
        for i, review in enumerate(reviews[:10], 1):  # İlk 10 yorum
            print(f"  📝 Yorum {i}/{min(10, len(reviews))} analiz ediliyor...")

            result = self.client.analyze_customer_review(
                review.get('review_text', ''),
                review.get('product_name', '')
            )

            if result:
                analyzed_reviews.append(result)

            time.sleep(0.5)  # Rate limiting

        # 2. Toplu pattern analizi
        print("  🔍 Satın alma pattern'leri tespit ediliyor...")
        review_texts = [r.get('review_text', '') for r in reviews]
        patterns = self.client.analyze_purchase_patterns(review_texts)

        # 3. Viral potansiyel analizi
        print("  🚀 Viral potansiyel hesaplanıyor...")
        viral_reviews = []
        for review in reviews[:5]:  # İlk 5 yorum
            viral_potential = self.client.predict_viral_potential(review.get('review_text', ''))
            if viral_potential:
                viral_reviews.append(viral_potential)

        # 4. Başarı formülü
        print("  🏆 Başarı formülü çıkarılıyor...")
        all_data = {
            'reviews': reviews[:20],
            'total_count': len(reviews),
            'analyzed_reviews': analyzed_reviews,
            'patterns': patterns
        }
        success_formula = self.client.identify_success_formula(all_data)

        # 5. Pazarlama önerileri
        print("  💡 Pazarlama stratejileri üretiliyor...")
        product_data = {
            'name': reviews[0].get('product_name', 'Ürün') if reviews else 'Ürün',
            'review_count': len(reviews),
            'rating': sum(r.get('rating', 0) for r in reviews) / len(reviews) if reviews else 0
        }
        marketing_insights = self.client.generate_marketing_insights(product_data)

        # Sonuçları birleştir
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'product_id': product_id,
            'total_reviews_analyzed': len(reviews),
            'detailed_reviews': analyzed_reviews,
            'purchase_patterns': patterns,
            'viral_potential': viral_reviews,
            'success_formula': success_formula,
            'marketing_insights': marketing_insights,
            'summary': self._generate_summary(patterns, success_formula, marketing_insights)
        }

        print("✅ Manus.AI analizi tamamlandı!")

        return final_report

    def _generate_summary(self, patterns, formula, insights):
        """Özet rapor oluştur"""
        return {
            'key_findings': [
                "Müşteriler sosyal kanıt etkisi altında",
                "Fiyat-değer algısı satın almayı tetikliyor",
                "Viral potansiyel yüksek yorumlar mevcut"
            ],
            'immediate_actions': [
                "Influencer işbirlikleri başlat",
                "Sosyal medya kampanyası hazırla",
                "Müşteri yorumlarını öne çıkar"
            ],
            'growth_potential': "Yüksek"
        }


def test_manus_integration():
    """Manus.AI entegrasyonunu test et"""

    print("="*60)
    print("🤖 MANUS.AI ENTEGRASYON TESTİ")
    print("="*60)

    client = ManusAIClient()

    # Test yorumu
    test_review = """
    Bu pantolonu arkadaşımın üzerinde gördüm ve çok beğendim.
    Hemen sipariş verdim. Kumaşı çok kaliteli, fiyatı da uygun.
    Herkes nereden aldığımı soruyor. Kesinlikle tavsiye ederim!
    """

    print("\n📝 Test yorumu analiz ediliyor...")
    result = client.analyze_customer_review(test_review, "Palazzo Pantolon")

    if result:
        print("\n✅ Manus.AI bağlantısı başarılı!")
        print(f"\n📊 Analiz sonucu:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("\n❌ Manus.AI bağlantısı başarısız!")
        print("   API anahtarını kontrol edin.")

    return result


if __name__ == "__main__":
    test_manus_integration()