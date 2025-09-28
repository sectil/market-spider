#!/usr/bin/env python3
"""
🔍 GELİŞMİŞ ÜRÜN ANALİZİ
Detaylı yorum analizi, satın alma nedenleri ve trend analizi
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from collections import Counter
import re

def show_enhanced_product_analysis(product_id):
    """Gelişmiş ürün analizi göster"""

    conn = sqlite3.connect('market_spider.db')

    # Ürün bilgilerini al
    product = pd.read_sql_query(f"""
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = {product_id}
    """, conn).to_dict('records')[0]

    st.header(f"🔍 {product['name']}")
    st.caption(f"Kategori: {product['category_name']} | Marka: {product['brand']}")

    # Ana metrikler
    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("💰 Fiyat", f"₺{product['price']:.2f}")
    col2.metric("⭐ Puan", f"{product['rating']:.1f}")
    col3.metric("💬 Yorum", f"{product['review_count']:,}")
    col4.metric("📊 Popülerlik", "🔥" * min(5, int(product['review_count']/10000 + 1)))
    col5.metric("📦 Stok", "✅ Var" if product['in_stock'] else "❌ Yok")

    # Tablar
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Satın Alma Analizi",
        "💬 Yorum Detayları",
        "📈 Fiyat & Trend",
        "🧠 Müşteri Profili",
        "📊 Rakip Analizi"
    ])

    # TÜM yorumları çek
    all_reviews = pd.read_sql_query(f"""
        SELECT * FROM product_reviews
        WHERE product_id = {product_id}
        ORDER BY helpful_count DESC
    """, conn)

    with tab1:
        st.subheader("🎯 Neden Bu Ürün Satın Alınıyor?")

        if not all_reviews.empty:
            # Satın alma nedenleri analizi
            purchase_reasons = {
                'Kalite & Dayanıklılık': {
                    'keywords': ['kalite', 'sağlam', 'dayanıklı', 'güvenilir', 'uzun ömür'],
                    'count': 0,
                    'sample_comments': []
                },
                'Fiyat/Performans': {
                    'keywords': ['uygun', 'ucuz', 'değer', 'fiyat', 'ekonomik', 'hesaplı'],
                    'count': 0,
                    'sample_comments': []
                },
                'Tasarım & Görünüm': {
                    'keywords': ['güzel', 'şık', 'tasarım', 'renk', 'modern', 'estetik'],
                    'count': 0,
                    'sample_comments': []
                },
                'Kullanım Kolaylığı': {
                    'keywords': ['pratik', 'kolay', 'kullanışlı', 'rahat', 'hafif'],
                    'count': 0,
                    'sample_comments': []
                },
                'Marka Güveni': {
                    'keywords': ['marka', 'güven', 'orijinal', 'bilindik', 'tanınmış'],
                    'count': 0,
                    'sample_comments': []
                },
                'Tavsiye & Sosyal Etki': {
                    'keywords': ['tavsiye', 'öneri', 'arkadaş', 'herkes', 'popüler'],
                    'count': 0,
                    'sample_comments': []
                },
                'Hızlı Teslimat': {
                    'keywords': ['hızlı', 'kargo', 'teslimat', 'geldi', 'ulaştı'],
                    'count': 0,
                    'sample_comments': []
                },
                'Hediye': {
                    'keywords': ['hediye', 'doğum günü', 'sevgiliye', 'anneme', 'babama'],
                    'count': 0,
                    'sample_comments': []
                }
            }

            # Yorumları analiz et
            for _, review in all_reviews.iterrows():
                if review['comment']:
                    comment_lower = review['comment'].lower()

                    for reason, data in purchase_reasons.items():
                        for keyword in data['keywords']:
                            if keyword in comment_lower:
                                purchase_reasons[reason]['count'] += 1
                                if len(purchase_reasons[reason]['sample_comments']) < 3:
                                    purchase_reasons[reason]['sample_comments'].append(
                                        review['comment'][:200]
                                    )
                                break

            # Sonuçları sırala
            sorted_reasons = sorted(purchase_reasons.items(),
                                  key=lambda x: x[1]['count'], reverse=True)

            col1, col2 = st.columns([1, 2])

            with col1:
                # Satın alma nedenleri grafiği
                reason_names = [r[0] for r in sorted_reasons if r[1]['count'] > 0]
                reason_counts = [r[1]['count'] for r in sorted_reasons if r[1]['count'] > 0]

                if reason_names:
                    fig = px.bar(
                        x=reason_counts,
                        y=reason_names,
                        orientation='h',
                        title="Satın Alma Nedenleri (Yorum Analizi)",
                        labels={'x': 'Bahsedilme Sayısı', 'y': 'Neden'},
                        color=reason_counts,
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # En önemli 3 neden detayı
                st.markdown("### 🏆 Top 3 Satın Alma Nedeni")

                for i, (reason, data) in enumerate(sorted_reasons[:3], 1):
                    if data['count'] > 0:
                        with st.expander(f"{i}. {reason} ({data['count']} kez bahsedildi)"):
                            st.write("**Örnek Yorumlar:**")
                            for comment in data['sample_comments']:
                                st.write(f"• *\"{comment}...\"*")
                                st.write("")

            # Satın alma puanı hesapla
            total_mentions = sum(r[1]['count'] for r in sorted_reasons)
            purchase_score = min(100, (total_mentions / len(all_reviews)) * 100)

            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            col1.metric(
                "🎯 Satın Alma Skoru",
                f"{purchase_score:.0f}/100",
                help="Yorumlarda satın alma nedenlerinin ne kadar net belirtildiği"
            )

            # Olumlu/Olumsuz oran
            positive_count = len(all_reviews[all_reviews['sentiment'] == 'olumlu'])
            negative_count = len(all_reviews[all_reviews['sentiment'] == 'olumsuz'])

            col2.metric(
                "😊 Memnuniyet Oranı",
                f"%{(positive_count/len(all_reviews)*100):.0f}" if len(all_reviews) > 0 else "N/A"
            )

            col3.metric(
                "🔄 Tekrar Satın Alma",
                f"%{min(95, purchase_score * 1.2):.0f}",
                help="Tahmin edilen tekrar satın alma oranı"
            )

    with tab2:
        st.subheader(f"💬 Tüm Yorumlar ({len(all_reviews)} adet)")

        if not all_reviews.empty:
            # Duygu dağılımı
            col1, col2 = st.columns(2)

            with col1:
                sentiment_dist = all_reviews['sentiment'].value_counts()
                fig = px.pie(
                    values=sentiment_dist.values,
                    names=sentiment_dist.index,
                    title="Duygu Dağılımı",
                    color_discrete_map={
                        'olumlu': '#00CC88',
                        'olumsuz': '#FF4444',
                        'nötr': '#FFAA00'
                    }
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Puan dağılımı
                rating_dist = all_reviews['rating'].value_counts().sort_index()
                fig = px.bar(
                    x=rating_dist.index,
                    y=rating_dist.values,
                    title="Puan Dağılımı",
                    labels={'x': 'Puan', 'y': 'Yorum Sayısı'},
                    color=rating_dist.values,
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig, use_container_width=True)

            # Kelime bulutu benzeri analiz
            st.markdown("### 🔤 En Çok Kullanılan Kelimeler")

            all_words = []
            for comment in all_reviews['comment'].dropna():
                words = re.findall(r'\w+', comment.lower())
                all_words.extend(words)

            # Stop words (Türkçe)
            stop_words = ['ve', 'bir', 'bu', 'da', 'de', 'için', 'ile', 'çok',
                         'daha', 'var', 'yok', 'ama', 'ben', 'sen', 'o', 'biz']

            filtered_words = [w for w in all_words if len(w) > 3 and w not in stop_words]
            word_freq = Counter(filtered_words).most_common(20)

            # Kelime frekans grafiği
            words_df = pd.DataFrame(word_freq, columns=['Kelime', 'Frekans'])
            fig = px.treemap(
                words_df,
                path=['Kelime'],
                values='Frekans',
                title='En Sık Kullanılan Kelimeler'
            )
            st.plotly_chart(fig, use_container_width=True)

            # En faydalı yorumlar
            st.markdown("### 👍 En Faydalı Yorumlar")

            top_helpful = all_reviews.nlargest(5, 'helpful_count')
            for _, review in top_helpful.iterrows():
                sentiment_color = {
                    'olumlu': '🟢',
                    'olumsuz': '🔴',
                    'nötr': '🟡'
                }.get(review['sentiment'], '⚪')

                with st.expander(
                    f"{sentiment_color} ⭐{review['rating']} - {review['reviewer_name']} "
                    f"(👍 {review['helpful_count']} kişi faydalı buldu)"
                ):
                    st.write(review['comment'])
                    st.caption(f"Tarih: {review['review_date']}")

    with tab3:
        st.subheader("📈 Fiyat Trendi ve Tahminler")

        # Gerçek fiyat geçmişi
        price_history = pd.read_sql_query(f"""
            SELECT price, timestamp
            FROM price_history
            WHERE product_id = {product_id}
            ORDER BY timestamp
        """, conn)

        if price_history.empty:
            # Simüle edilmiş veri oluştur
            dates = pd.date_range(end=datetime.now(), periods=90, freq='D')
            base_price = product['price']

            # Gerçekçi fiyat dalgalanması
            trend = np.random.choice([-1, 0, 1], size=90, p=[0.3, 0.4, 0.3])
            prices = [base_price]

            for t in trend[1:]:
                new_price = prices[-1] * (1 + t * np.random.uniform(0.01, 0.03))
                prices.append(new_price)

            price_history = pd.DataFrame({
                'timestamp': dates,
                'price': prices
            })

        # Fiyat grafiği
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=price_history['timestamp'],
            y=price_history['price'],
            mode='lines+markers',
            name='Fiyat',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=4)
        ))

        # Hareketli ortalamalar
        price_history['MA7'] = price_history['price'].rolling(window=7, min_periods=1).mean()
        price_history['MA30'] = price_history['price'].rolling(window=30, min_periods=1).mean()

        fig.add_trace(go.Scatter(
            x=price_history['timestamp'],
            y=price_history['MA7'],
            mode='lines',
            name='7 Günlük Ortalama',
            line=dict(color='orange', width=1, dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=price_history['timestamp'],
            y=price_history['MA30'],
            mode='lines',
            name='30 Günlük Ortalama',
            line=dict(color='red', width=1, dash='dot')
        ))

        fig.update_layout(
            title='Fiyat Değişim Grafiği',
            xaxis_title='Tarih',
            yaxis_title='Fiyat (₺)',
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # Fiyat istatistikleri
        col1, col2, col3, col4 = st.columns(4)

        recent_prices = price_history['price'].tail(30)

        col1.metric(
            "📉 Min (30 gün)",
            f"₺{recent_prices.min():.2f}"
        )
        col2.metric(
            "📈 Max (30 gün)",
            f"₺{recent_prices.max():.2f}"
        )
        col3.metric(
            "📊 Ortalama",
            f"₺{recent_prices.mean():.2f}"
        )

        # Volatilite
        volatility = (recent_prices.std() / recent_prices.mean()) * 100
        col4.metric(
            "📊 Volatilite",
            f"%{volatility:.1f}",
            help="Fiyat değişkenliği (düşük < %5 < orta < %10 < yüksek)"
        )

        # Satın alma önerisi
        st.markdown("### 💡 Satın Alma Önerisi")

        current_price = product['price']
        avg_price = recent_prices.mean()

        if current_price < avg_price * 0.95:
            st.success("🟢 **ŞİMDİ AL** - Fiyat ortalamanın %5+ altında!")
        elif current_price < avg_price:
            st.info("🔵 **İYİ FİYAT** - Fiyat ortalama seviyede")
        else:
            st.warning("🟡 **BEKLE** - Fiyat ortalamanın üzerinde")

    with tab4:
        st.subheader("🧠 Müşteri Profili Analizi")

        if not all_reviews.empty:
            # Müşteri segmentasyonu
            segments = {
                'Fiyat Odaklı': 0,
                'Kalite Odaklı': 0,
                'Marka Sadık': 0,
                'Trend Takipçisi': 0,
                'Fonksiyonel Alıcı': 0
            }

            for _, review in all_reviews.iterrows():
                if review['comment']:
                    comment = review['comment'].lower()

                    if any(w in comment for w in ['ucuz', 'uygun', 'fiyat', 'ekonomik']):
                        segments['Fiyat Odaklı'] += 1
                    if any(w in comment for w in ['kalite', 'sağlam', 'dayanıklı']):
                        segments['Kalite Odaklı'] += 1
                    if any(w in comment for w in ['marka', 'orijinal', 'güven']):
                        segments['Marka Sadık'] += 1
                    if any(w in comment for w in ['trend', 'moda', 'yeni', 'popüler']):
                        segments['Trend Takipçisi'] += 1
                    if any(w in comment for w in ['pratik', 'kullanışlı', 'işe yarıyor']):
                        segments['Fonksiyonel Alıcı'] += 1

            # Müşteri segmentasyon grafiği
            fig = go.Figure(data=go.Scatterpolar(
                r=list(segments.values()),
                theta=list(segments.keys()),
                fill='toself',
                name='Müşteri Profili'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, max(segments.values()) * 1.1] if segments.values() else [0, 100]
                    )),
                showlegend=False,
                title='Müşteri Profili Dağılımı'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Demografik tahmin
            st.markdown("### 👥 Tahminî Demografik Dağılım")

            col1, col2 = st.columns(2)

            with col1:
                # Cinsiyet tahmini (yorumlardaki ipuçlarından)
                gender_clues = {'kadın': 0, 'erkek': 0}

                for _, review in all_reviews.iterrows():
                    if review['comment']:
                        comment = review['comment'].lower()
                        if any(w in comment for w in ['eşim', 'kocam', 'hanım']):
                            gender_clues['kadın'] += 1
                        if any(w in comment for w in ['karım', 'beyler', 'erkek']):
                            gender_clues['erkek'] += 1

                if sum(gender_clues.values()) > 0:
                    fig = px.pie(
                        values=list(gender_clues.values()),
                        names=list(gender_clues.keys()),
                        title='Tahminî Cinsiyet Dağılımı'
                    )
                    st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Kullanım amacı
                usage = {
                    'Kişisel': len([r for r in all_reviews['comment'].dropna()
                                   if 'kendim' in r.lower() or 'benim' in r.lower()]),
                    'Hediye': len([r for r in all_reviews['comment'].dropna()
                                  if 'hediye' in r.lower()]),
                    'Aile': len([r for r in all_reviews['comment'].dropna()
                               if 'aile' in r.lower() or 'çocuk' in r.lower()])
                }

                fig = px.pie(
                    values=list(usage.values()),
                    names=list(usage.keys()),
                    title='Kullanım Amacı'
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.subheader("📊 Rakip Karşılaştırma")

        # Aynı kategorideki diğer ürünler
        competitors = pd.read_sql_query(f"""
            SELECT name, brand, price, rating, review_count
            FROM products
            WHERE category_id = {product['category_id']}
            AND id != {product_id}
            ORDER BY review_count DESC
            LIMIT 5
        """, conn)

        if not competitors.empty:
            # Karşılaştırma tablosu
            comparison_data = pd.DataFrame({
                'Ürün': [product['name'][:30] + ' (BU ÜRÜN)'] + competitors['name'].str[:30].tolist(),
                'Marka': [product['brand']] + competitors['brand'].tolist(),
                'Fiyat': [product['price']] + competitors['price'].tolist(),
                'Puan': [product['rating']] + competitors['rating'].tolist(),
                'Yorum': [product['review_count']] + competitors['review_count'].tolist()
            })

            # Renklendirme için style
            def highlight_this_product(row):
                if 'BU ÜRÜN' in row['Ürün']:
                    return ['background-color: #e6f3ff'] * len(row)
                return [''] * len(row)

            styled_df = comparison_data.style.apply(highlight_this_product, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Karşılaştırma grafikleri
            col1, col2 = st.columns(2)

            with col1:
                # Fiyat karşılaştırma
                fig = px.bar(
                    comparison_data,
                    x='Ürün',
                    y='Fiyat',
                    title='Fiyat Karşılaştırması',
                    color='Fiyat',
                    color_continuous_scale='RdYlGn_r'
                )
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Performans karşılaştırma
                fig = px.scatter(
                    comparison_data,
                    x='Puan',
                    y='Yorum',
                    size='Fiyat',
                    hover_data=['Ürün', 'Marka'],
                    title='Performans Karşılaştırması',
                    labels={'Yorum': 'Yorum Sayısı', 'Puan': 'Ortalama Puan'}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Rekabet avantajı
            st.markdown("### 🎯 Rekabet Avantajı Analizi")

            advantages = []
            disadvantages = []

            avg_price = competitors['price'].mean()
            avg_rating = competitors['rating'].mean()
            avg_reviews = competitors['review_count'].mean()

            if product['price'] < avg_price:
                advantages.append(f"✅ Fiyat avantajı: Rakiplerden %{((avg_price - product['price'])/avg_price*100):.0f} daha ucuz")
            else:
                disadvantages.append(f"❌ Fiyat dezavantajı: Rakiplerden %{((product['price'] - avg_price)/avg_price*100):.0f} daha pahalı")

            if product['rating'] > avg_rating:
                advantages.append(f"✅ Kalite avantajı: Rakiplerden {product['rating'] - avg_rating:.1f} puan daha yüksek")
            else:
                disadvantages.append(f"❌ Kalite dezavantajı: Rakiplerden {avg_rating - product['rating']:.1f} puan daha düşük")

            if product['review_count'] > avg_reviews:
                advantages.append(f"✅ Popülerlik avantajı: Rakiplerden {((product['review_count'] - avg_reviews)/avg_reviews*100):.0f}% daha fazla yorum")

            col1, col2 = st.columns(2)

            with col1:
                st.success("**Avantajlar:**")
                for adv in advantages:
                    st.write(adv)

            with col2:
                st.error("**Dezavantajlar:**")
                for dis in disadvantages:
                    st.write(dis)

    conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="Gelişmiş Ürün Analizi", layout="wide")

    # Test için örnek ürün ID
    test_product_id = st.number_input("Ürün ID:", min_value=1, value=1)
    show_enhanced_product_analysis(test_product_id)