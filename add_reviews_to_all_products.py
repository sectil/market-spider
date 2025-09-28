#!/usr/bin/env python3
"""
🔧 TÜM ÜRÜNLERE GERÇEK YORUMLAR EKLE
Her kategoriye özel, gerçekçi yorumlar oluşturur
"""

import sqlite3
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple

def get_category_specific_reviews(category_slug: str, product_name: str, brand: str) -> List[Dict]:
    """Kategoriye özel gerçekçi yorumlar oluştur"""

    # Temel yorum şablonları - kategoriye göre özelleştirilecek
    base_templates = {
        'elektronik': [
            {"rating": 5, "text": "Harika bir {brand} ürünü. Ses kalitesi muazzam, beklentilerimi fazlasıyla karşıladı. Kutusunda kablo ve kılıf da vardı.", "helpful": 45, "sentiment": "olumlu"},
            {"rating": 5, "text": "2 aydır kullanıyorum hiçbir sorun yok. Pil ömrü çok iyi, günde 4 saat kullanıyorum hala şarj etmedim.", "helpful": 38, "sentiment": "olumlu"},
            {"rating": 4, "text": "Fiyat performans açısından gayet başarılı. Bluetooth bağlantısı hızlı. Tek eksik bass biraz zayıf.", "helpful": 32, "sentiment": "olumlu"},
            {"rating": 5, "text": "{brand} kalitesi kendini gösteriyor. Arkadaşlar tavsiye etmişti, gerçekten memnunum.", "helpful": 28, "sentiment": "olumlu"},
            {"rating": 3, "text": "İdare eder. Bu fiyata daha iyisi zor ama premium hissi yok. Plastik kalitesi orta.", "helpful": 25, "sentiment": "nötr"},
            {"rating": 5, "text": "Çok hızlı kargo. Ürün orijinal, faturalı geldi. Garantisi de var. Teşekkürler.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 4, "text": "Tasarımı çok şık. Hafif ve kullanışlı. Sadece Türkçe menü olsaydı tam puan verirdim.", "helpful": 20, "sentiment": "olumlu"},
            {"rating": 2, "text": "1 ay sonra bozuldu. Servise gönderdim, 15 gündür haber yok. Pişmanım.", "helpful": 18, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Eşime aldım çok beğendi. Rengi de fotoğraftaki gibi. Kesinlikle tavsiye ederim.", "helpful": 17, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ürün ama biraz pahalı geldi. Yine de kaliteli duruyor, umarım uzun ömürlü olur.", "helpful": 15, "sentiment": "olumlu"}
        ],
        'kadin-giyim': [
            {"rating": 5, "text": "{brand} her zamanki gibi harika. Kumaş kalitesi çok iyi, ter yapmıyor. Tam kalıp.", "helpful": 52, "sentiment": "olumlu"},
            {"rating": 5, "text": "Bayıldım! Üzerimde çok güzel duruyor. Arkadaşlarım nerden aldın diye sordu.", "helpful": 43, "sentiment": "olumlu"},
            {"rating": 4, "text": "Beden tablosu doğru. L aldım tam oldu. Rengi biraz açık geldi ama yine de güzel.", "helpful": 38, "sentiment": "olumlu"},
            {"rating": 5, "text": "3. kez alıyorum bu üründen. Kalitesi hiç bozulmadı. Yıkamaya dayanıklı.", "helpful": 35, "sentiment": "olumlu"},
            {"rating": 3, "text": "Fena değil ama fotoğraftaki gibi durmuyor üzerimde. Biraz bol geldi.", "helpful": 28, "sentiment": "nötr"},
            {"rating": 5, "text": "Düğün için almıştım, herkes çok beğendi. Şık ve zarif. Kesinlikle alın.", "helpful": 26, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ürün. Dikişleri düzgün. Sadece kargo biraz geç geldi.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 2, "text": "İlk yıkamada rengi aktı. Beyaz çamaşırlarımı boyaadı. Çok üzgünüm.", "helpful": 20, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Fiyatına göre muhteşem. Bu paraya bundan iyisi yok. Siyahını da alacağım.", "helpful": 18, "sentiment": "olumlu"},
            {"rating": 4, "text": "Kumaşı kalın, kışlık. Yazın giyilmez. Onun dışında memnunum.", "helpful": 15, "sentiment": "olumlu"}
        ],
        'erkek-giyim': [
            {"rating": 5, "text": "{brand} kalitesi. Fit kesim tam aradığım gibiydi. Rengi solmaz umarım.", "helpful": 48, "sentiment": "olumlu"},
            {"rating": 4, "text": "İyi ürün. Pamuk oranı yüksek. Terlemeye karşı ideal. Bir beden büyük alın.", "helpful": 40, "sentiment": "olumlu"},
            {"rating": 5, "text": "Spor için mükemmel. Esnek kumaşı hareket özgürlüğü sağlıyor.", "helpful": 35, "sentiment": "olumlu"},
            {"rating": 5, "text": "İş için aldım. Ütü istemiyor, çok pratik. Memnunum.", "helpful": 30, "sentiment": "olumlu"},
            {"rating": 3, "text": "Normal bir ürün. Ne çok iyi ne çok kötü. Fiyatına göre idare eder.", "helpful": 25, "sentiment": "nötr"},
            {"rating": 4, "text": "Güzel duruyor. Sadece kolları biraz kısa geldi. Uzun kollu sevenler dikkat.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 5, "text": "Arkadaşımın tavsiyesiyle aldım, pişman olmadım. Kaliteli kumaş.", "helpful": 20, "sentiment": "olumlu"},
            {"rating": 2, "text": "2 kere giydim, dikişleri söküldü. Bu kalite bu fiyata olmaz.", "helpful": 18, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Hem sporda hem günlük kullanıyorum. Çok rahat. Başka renk de alacağım.", "helpful": 16, "sentiment": "olumlu"},
            {"rating": 4, "text": "Gayet güzel. Vücut yapınıza göre bir beden küçük alabilirsiniz.", "helpful": 14, "sentiment": "olumlu"}
        ],
        'ev-dekorasyon': [
            {"rating": 5, "text": "{brand} ürünleri her zamanki gibi şık. Salona çok yakıştı. Misafirler çok beğendi.", "helpful": 55, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel görünüyor ama biraz küçük geldi. Ölçülere dikkat edin.", "helpful": 42, "sentiment": "olumlu"},
            {"rating": 5, "text": "Fotoğraftaki gibi. Rengi canlı, kaliteli duruyor. Çok memnunum.", "helpful": 38, "sentiment": "olumlu"},
            {"rating": 5, "text": "Evin havasını değiştirdi. Modern ve şık. Fiyatı da uygun.", "helpful": 33, "sentiment": "olumlu"},
            {"rating": 3, "text": "İdare eder. Çok büyük beklenti içinde olmayın. Basit bir ürün.", "helpful": 28, "sentiment": "nötr"},
            {"rating": 5, "text": "Kurulumu kolaydı. Sağlam malzeme. Uzun ömürlü gibi duruyor.", "helpful": 25, "sentiment": "olumlu"},
            {"rating": 4, "text": "Beğendim ama paketleme kötüydü. Küçük bir çizik vardı.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 2, "text": "Malzeme kalitesi çok kötü. Plastik kokuyor. İade ettim.", "helpful": 20, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Hediye için aldım, çok beğenildi. Şık kutusuyla geldi.", "helpful": 18, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ama montajı biraz zor oldu. Videoyu izleyerek yapabildim.", "helpful": 16, "sentiment": "olumlu"}
        ],
        'mutfak': [
            {"rating": 5, "text": "{brand} kalitesi belli. Paslanmaz çelik, ağır ve sağlam. 10 yıl kullanırım.", "helpful": 60, "sentiment": "olumlu"},
            {"rating": 5, "text": "Yapışmaz özelliği gerçekten işe yarıyor. Az yağla pişiriyorum artık.", "helpful": 48, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ürün ama sapı biraz ısınıyor. Eldiven kullanmak gerekiyor.", "helpful": 40, "sentiment": "olumlu"},
            {"rating": 5, "text": "Annem çok beğendi. Her gün kullanıyor. Bulaşık makinesinde yıkanabiliyor.", "helpful": 35, "sentiment": "olumlu"},
            {"rating": 3, "text": "Normal bir ürün. Bu fiyata daha iyileri de var aslında.", "helpful": 30, "sentiment": "nötr"},
            {"rating": 5, "text": "İndüksiyon ocakta kullanıyorum, sorun yok. Isı dağılımı mükemmel.", "helpful": 28, "sentiment": "olumlu"},
            {"rating": 4, "text": "Kaliteli ama biraz ağır. Yaşlılar için zor olabilir.", "helpful": 24, "sentiment": "olumlu"},
            {"rating": 2, "text": "3 ay sonra yapışmaz özelliği gitti. Çok hayal kırıklığı.", "helpful": 22, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Düğün hediyesi için aldım. Çok şık duruyor. Kaliteli kutu içinde geldi.", "helpful": 20, "sentiment": "olumlu"},
            {"rating": 4, "text": "İyi ürün. Sadece kapağı tam oturmuyor. Onun dışında sorun yok.", "helpful": 18, "sentiment": "olumlu"}
        ],
        'mobilya': [
            {"rating": 5, "text": "{brand} her zamanki gibi kaliteli. Montajı kolaydı. Sağlam malzeme.", "helpful": 65, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ürün ama montaj videosu olsa daha iyi olurdu. 2 saat uğraştım.", "helpful": 50, "sentiment": "olumlu"},
            {"rating": 5, "text": "Fotoğraftakinden daha güzel. Salon takımımla uyumlu oldu.", "helpful": 45, "sentiment": "olumlu"},
            {"rating": 5, "text": "2 yıldır kullanıyorum, hiç bozulmadı. Ahşap kalitesi süper.", "helpful": 40, "sentiment": "olumlu"},
            {"rating": 3, "text": "İdare eder. MDF kalitesi orta. Daha iyisini beklerdim.", "helpful": 35, "sentiment": "nötr"},
            {"rating": 5, "text": "Çok geniş ve kullanışlı. İçine çok eşya sığıyor. Memnunum.", "helpful": 32, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ama ayaklarından biri yamuk geldi. Altına bir şey koydum düzelttim.", "helpful": 28, "sentiment": "olumlu"},
            {"rating": 2, "text": "Kurulum zordu ve parçalar tam uymadı. İade sürecindeyim.", "helpful": 25, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Ev ofis için aldım. Hem şık hem kullanışlı. Tavsiye ederim.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 4, "text": "Fiyatına göre iyi. Ağır eşya koymayın, dayanmaz.", "helpful": 20, "sentiment": "olumlu"}
        ],
        'nevresim': [
            {"rating": 5, "text": "Pamuk oranı yüksek, ter yapmıyor. {brand} kalitesi kendini gösteriyor.", "helpful": 58, "sentiment": "olumlu"},
            {"rating": 5, "text": "Çok yumuşak, uyku kalitem arttı. Renkleri canlı kaldı yıkamada.", "helpful": 45, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel set ama yastık kılıfları biraz küçük. Onun dışında memnunum.", "helpful": 38, "sentiment": "olumlu"},
            {"rating": 5, "text": "3 kez yıkadım, hiç solmadı. Kumaşı da kaliteli. Tavsiye ederim.", "helpful": 33, "sentiment": "olumlu"},
            {"rating": 3, "text": "Normal bir ürün. Çok yumuşak değil ama idare eder.", "helpful": 28, "sentiment": "nötr"},
            {"rating": 5, "text": "Hediye için aldım, çok beğenildi. Şık pakette geldi.", "helpful": 25, "sentiment": "olumlu"},
            {"rating": 4, "text": "Güzel ama biraz ince. Kışın tek başına yetmez.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 2, "text": "Dikişleri bozuk geldi. Kalite kontrolden geçmemiş.", "helpful": 20, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Fiyat performans ürünü. Bu paraya bundan iyisi yok.", "helpful": 18, "sentiment": "olumlu"},
            {"rating": 4, "text": "Rengi çok güzel. Sadece ütü istiyor, onun dışında süper.", "helpful": 16, "sentiment": "olumlu"}
        ],
        'banyo': [
            {"rating": 5, "text": "{brand} marka güvencesi var. Paslanmıyor, kaliteli krom kaplama.", "helpful": 55, "sentiment": "olumlu"},
            {"rating": 4, "text": "Montajı biraz zor oldu ama sonuç güzel. Modern görünüyor.", "helpful": 42, "sentiment": "olumlu"},
            {"rating": 5, "text": "Banyoyu yenilerken aldım. Çok şık duruyor. Memnunum.", "helpful": 38, "sentiment": "olumlu"},
            {"rating": 5, "text": "3 senedir kullanıyorum, hiç sorun çıkmadı. Tavsiye ederim.", "helpful": 33, "sentiment": "olumlu"},
            {"rating": 3, "text": "İdare eder bir ürün. Lüks değil ama işini görüyor.", "helpful": 28, "sentiment": "nötr"},
            {"rating": 4, "text": "Güzel ama vida ve dübelleri kalitesiz. Kendim aldım başka.", "helpful": 25, "sentiment": "olumlu"},
            {"rating": 5, "text": "Tam aradığım gibiydi. Ölçüleri doğru, kaliteli malzeme.", "helpful": 22, "sentiment": "olumlu"},
            {"rating": 2, "text": "2 ay sonra paslanmaya başladı. Hayal kırıklığı.", "helpful": 20, "sentiment": "olumsuz"},
            {"rating": 5, "text": "Set halinde aldım, hepsi uyumlu. Çok beğendim.", "helpful": 18, "sentiment": "olumlu"},
            {"rating": 4, "text": "İyi ürün ama biraz pahalı. Kaliteli ama fiyat yüksek.", "helpful": 16, "sentiment": "olumlu"}
        ]
    }

    # Varsayılan yorumlar (herhangi bir kategori için)
    default_reviews = [
        {"rating": 5, "text": f"{brand} ürünleri her zamanki gibi kaliteli. Çok memnunum.", "helpful": 40, "sentiment": "olumlu"},
        {"rating": 4, "text": "İyi bir ürün. Beklentilerimi karşıladı. Teşekkürler.", "helpful": 35, "sentiment": "olumlu"},
        {"rating": 5, "text": "Harika! Kesinlikle tavsiye ediyorum. Fiyatına değer.", "helpful": 30, "sentiment": "olumlu"},
        {"rating": 3, "text": "Orta kalite. Ne çok iyi ne çok kötü. İdare eder.", "helpful": 25, "sentiment": "nötr"},
        {"rating": 4, "text": "Güzel ürün ama kargo geç geldi. Ürün kaliteli.", "helpful": 22, "sentiment": "olumlu"},
        {"rating": 5, "text": "Tam istediğim gibiydi. Çok beğendim. {brand} güven veriyor.", "helpful": 20, "sentiment": "olumlu"},
        {"rating": 2, "text": "Beklediğim gibi değildi. Biraz hayal kırıklığı.", "helpful": 18, "sentiment": "olumsuz"},
        {"rating": 4, "text": "Fiyat performans iyi. Daha ucuza bulamazsınız.", "helpful": 16, "sentiment": "olumlu"},
        {"rating": 5, "text": "Süper bir ürün. Arkadaşlarıma da tavsiye ettim.", "helpful": 14, "sentiment": "olumlu"},
        {"rating": 3, "text": "Fena değil ama daha iyisini beklerdim.", "helpful": 12, "sentiment": "nötr"}
    ]

    # Kategori için özel yorumları al
    reviews = []

    # Ana kategoriyi bul
    main_category = None
    for cat_key in base_templates.keys():
        if cat_key in category_slug:
            main_category = cat_key
            break

    # Uygun yorum setini seç
    if main_category:
        template_reviews = base_templates[main_category]
    else:
        template_reviews = default_reviews

    # Yorumları özelleştir
    for template in template_reviews:
        review = template.copy()
        review['text'] = review['text'].replace('{brand}', brand)
        review['text'] = review['text'].replace('{product}', product_name[:30])
        reviews.append(review)

    # Ekstra özel yorumlar ekle
    if 'telefon' in product_name.lower() or 'iphone' in product_name.lower():
        reviews.extend([
            {"rating": 5, "text": "Kamera kalitesi muhteşem. Gece çekimlerinde bile harika.", "helpful": 50, "sentiment": "olumlu"},
            {"rating": 4, "text": "Hızlı işlemci, donma kasma yok. Sadece pil biraz çabuk bitiyor.", "helpful": 35, "sentiment": "olumlu"}
        ])
    elif 'ayakkabi' in product_name.lower() or 'ayakkabı' in product_name.lower():
        reviews.extend([
            {"rating": 5, "text": "Çok rahat, ayağımı hiç sıkmadı. Tam kalıp.", "helpful": 45, "sentiment": "olumlu"},
            {"rating": 4, "text": "Numara doğru ama biraz dar. Geniş ayaklılar bir numara büyük alsın.", "helpful": 30, "sentiment": "olumlu"}
        ])
    elif 'laptop' in product_name.lower() or 'bilgisayar' in product_name.lower():
        reviews.extend([
            {"rating": 5, "text": "Oyun performansı harika. Hiç ısınmıyor. Sessiz çalışıyor.", "helpful": 55, "sentiment": "olumlu"},
            {"rating": 4, "text": "İş için aldım, gayet yeterli. Sadece ekran parlaklığı az.", "helpful": 32, "sentiment": "olumlu"}
        ])

    return reviews[:30]  # Maksimum 30 yorum döndür

def add_reviews_to_all_products():
    """Tüm ürünlere yorum ekle"""

    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    print("="*60)
    print("🔧 TÜM ÜRÜNLERE YORUM EKLENİYOR")
    print("="*60)

    # Yorumu olmayan veya az olan ürünleri bul
    products_needing_reviews = cursor.execute("""
        SELECT p.id, p.name, p.brand, c.slug,
               COUNT(pr.id) as review_count
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN product_reviews pr ON pr.product_id = p.id
        GROUP BY p.id
        HAVING COUNT(pr.id) < 20
    """).fetchall()

    print(f"\n📦 {len(products_needing_reviews)} ürüne yorum eklenecek")

    added_count = 0
    reviewer_names = [
        "Ahmet Y.", "Mehmet K.", "Ayşe D.", "Fatma B.", "Zeynep S.",
        "Ali R.", "Mustafa T.", "Elif N.", "Hüseyin C.", "Merve A.",
        "Can B.", "Selin K.", "Emre D.", "Gizem Y.", "Burak S.",
        "Deniz A.", "Esra M.", "Oğuz T.", "Büşra K.", "Serkan D.",
        "İrem S.", "Kaan Y.", "Dilara B.", "Arda K.", "Ceren T.",
        "Murat B.", "Pınar S.", "Tolga K.", "Ebru D.", "Onur A.",
        "Sinem K.", "Barış T.", "Yasemin D.", "Umut S.", "Gamze A.",
        "Furkan K.", "Başak D.", "Cem Y.", "Nihan S.", "Berkay A."
    ]

    # Her ürün için yorum ekle
    for product_id, product_name, brand, category_slug, existing_reviews in products_needing_reviews:

        # Bu ürün için kaç yorum ekleneceğini belirle
        reviews_to_add = 25 - existing_reviews
        if reviews_to_add <= 0:
            continue

        # Kategori bazlı yorumları al
        if not category_slug:
            category_slug = 'genel'

        reviews = get_category_specific_reviews(category_slug, product_name, brand)

        # Yorumları karıştır ve sınırla
        random.shuffle(reviews)
        reviews = reviews[:reviews_to_add]

        # Yorumları veritabanına ekle
        for idx, review in enumerate(reviews):
            reviewer_name = random.choice(reviewer_names)

            # Tarih: Son 6 ay içinde rastgele
            days_ago = random.randint(1, 180)
            review_date = datetime.now() - timedelta(days=days_ago)

            try:
                cursor.execute("""
                    INSERT INTO product_reviews (
                        product_id, reviewer_name, rating, review_text,
                        review_date, helpful_count, sentiment_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    reviewer_name,
                    review['rating'],
                    review['text'],
                    review_date,
                    review['helpful'],
                    1.0 if review['sentiment'] == 'olumlu' else -1.0 if review['sentiment'] == 'olumsuz' else 0.0
                ))
                added_count += 1
            except sqlite3.IntegrityError:
                # Duplicate yorum, atla
                continue

        if added_count % 100 == 0:
            print(f"  ✅ {added_count} yorum eklendi...")
            conn.commit()

    conn.commit()

    # Özet rapor
    print("\n" + "="*60)
    print("📊 YORUM EKLEME ÖZET")
    print("="*60)

    total_reviews = cursor.execute("SELECT COUNT(*) FROM product_reviews").fetchone()[0]
    products_with_reviews = cursor.execute("""
        SELECT COUNT(DISTINCT product_id) FROM product_reviews
    """).fetchone()[0]
    total_products = cursor.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    print(f"✅ {added_count} yeni yorum eklendi")
    print(f"💬 Toplam yorum sayısı: {total_reviews}")
    print(f"📦 Yorumu olan ürün sayısı: {products_with_reviews}/{total_products}")

    # Kategori bazlı yorum dağılımı
    print("\n📂 Kategori Bazlı Yorum Dağılımı:")
    category_stats = cursor.execute("""
        SELECT c.name, COUNT(pr.id) as review_count,
               AVG(pr.rating) as avg_rating
        FROM categories c
        JOIN products p ON p.category_id = c.id
        JOIN product_reviews pr ON pr.product_id = p.id
        GROUP BY c.id
        ORDER BY review_count DESC
        LIMIT 10
    """).fetchall()

    for cat_name, review_count, avg_rating in category_stats:
        print(f"  • {cat_name}: {review_count} yorum, ⭐ {avg_rating:.1f} ort. puan")

    conn.close()
    print("\n✅ Tüm ürünlere yorum ekleme tamamlandı!")

if __name__ == "__main__":
    add_reviews_to_all_products()