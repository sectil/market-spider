#!/usr/bin/env python3
"""
🌳 İNTERAKTİF KATEGORİ AĞACI
Tıklanabilir kategoriler ve detaylı ürün analizi
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def show_interactive_category_tree():
    """İnteraktif kategori ağacı ve ürün detayları"""

    st.title("🌳 İnteraktif Kategori Ağacı")

    conn = sqlite3.connect('market_spider.db')

    # Session state için seçili kategori
    if 'selected_category' not in st.session_state:
        st.session_state.selected_category = None
    if 'selected_subcategory' not in st.session_state:
        st.session_state.selected_subcategory = None
    if 'selected_product' not in st.session_state:
        st.session_state.selected_product = None

    # Ana kategoriler
    main_categories = pd.read_sql_query("""
        SELECT id, name, icon
        FROM categories
        WHERE parent_id IS NULL
        ORDER BY order_index
    """, conn)

    # 3 sütunlu layout
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.subheader("📂 Ana Kategoriler")

        # Ana kategori seçimi
        for _, cat in main_categories.iterrows():
            # Her kategori için ürün sayısı
            product_count = pd.read_sql_query(f"""
                SELECT COUNT(p.id) as count
                FROM products p
                JOIN categories c ON p.category_id = c.id
                WHERE c.id = {cat['id']} OR c.parent_id = {cat['id']}
            """, conn).iloc[0]['count']

            if product_count > 0:
                if st.button(f"{cat['icon']} {cat['name']} ({product_count})",
                           key=f"main_{cat['id']}",
                           use_container_width=True):
                    st.session_state.selected_category = cat['id']
                    st.session_state.selected_subcategory = None
                    st.session_state.selected_product = None

    with col2:
        st.subheader("📁 Alt Kategoriler")

        if st.session_state.selected_category:
            # Seçili ana kategorinin alt kategorileri
            subcategories = pd.read_sql_query(f"""
                SELECT id, name
                FROM categories
                WHERE parent_id = {st.session_state.selected_category}
                ORDER BY order_index
            """, conn)

            for _, subcat in subcategories.iterrows():
                # Alt kategori ürün sayısı
                subcat_product_count = pd.read_sql_query(f"""
                    SELECT COUNT(*) as count
                    FROM products
                    WHERE category_id = {subcat['id']}
                """, conn).iloc[0]['count']

                if subcat_product_count > 0:
                    if st.button(f"└─ {subcat['name']} ({subcat_product_count})",
                               key=f"sub_{subcat['id']}",
                               use_container_width=True):
                        st.session_state.selected_subcategory = subcat['id']
                        st.session_state.selected_product = None

    with col3:
        st.subheader("📦 Ürünler")

        # Hangi kategorinin ürünlerini gösterelim?
        category_to_show = st.session_state.selected_subcategory or st.session_state.selected_category

        if category_to_show:
            # Kategorideki ürünler - En çok satanlar önce
            products = pd.read_sql_query(f"""
                SELECT
                    id, name, brand, price, rating,
                    review_count, in_stock
                FROM products
                WHERE category_id = {category_to_show}
                ORDER BY review_count DESC, rating DESC
            """, conn)

            if not products.empty:
                # Ürün listesi
                for _, product in products.iterrows():
                    col_prod1, col_prod2 = st.columns([3, 1])

                    with col_prod1:
                        # Ürün bilgileri
                        st.markdown(f"""
                        **{product['name'][:50]}**
                        {product['brand']} | ⭐ {product['rating']:.1f} | 💬 {product['review_count']} yorum
                        """)

                    with col_prod2:
                        st.markdown(f"**₺{product['price']:.2f}**")
                        if st.button("🔍 Detay", key=f"prod_{product['id']}", use_container_width=True):
                            st.session_state.selected_product = product['id']

    # Ürün detay bölümü
    if st.session_state.selected_product:
        st.markdown("---")
        st.header("📊 Ürün Detaylı Analizi")

        # Ürün bilgilerini çek
        product_detail = pd.read_sql_query(f"""
            SELECT * FROM products WHERE id = {st.session_state.selected_product}
        """, conn).to_dict('records')[0]

        # 3 tab: Genel Bilgi, Yorumlar & Analiz, Fiyat Geçmişi
        tab1, tab2, tab3 = st.tabs(["📋 Genel Bilgi", "💬 Yorumlar & Analiz", "📈 Fiyat Geçmişi"])

        with tab1:
            col1, col2, col3, col4 = st.columns(4)

            col1.metric("Marka", product_detail['brand'])
            col2.metric("Fiyat", f"₺{product_detail['price']:.2f}")
            col3.metric("Puan", f"⭐ {product_detail['rating']:.1f}")
            col4.metric("Yorum", f"💬 {product_detail['review_count']}")

            st.markdown(f"""
            ### {product_detail['name']}

            - **Stok Durumu:** {'✅ Stokta' if product_detail['in_stock'] else '❌ Stok Yok'}
            - **Kategori ID:** {product_detail['category_id']}
            - **Ürün URL:** {product_detail['url']}
            """)

        with tab2:
            # Yorumları çek
            reviews = pd.read_sql_query(f"""
                SELECT * FROM product_reviews
                WHERE product_id = {st.session_state.selected_product}
                ORDER BY helpful_count DESC
                LIMIT 10
            """, conn)

            if not reviews.empty:
                # Duygu analizi özeti
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("😊 Duygu Analizi")
                    sentiment_counts = reviews['sentiment'].value_counts()

                    # Pie chart
                    fig = px.pie(
                        values=sentiment_counts.values,
                        names=sentiment_counts.index,
                        title="Yorum Duygu Dağılımı",
                        color_discrete_map={
                            'olumlu': '#00CC88',
                            'olumsuz': '#FF4444',
                            'nötr': '#FFAA00'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("🎯 Neden Satın Alınıyor?")

                    # Satın alma nedenleri (yorumlardan çıkarım)
                    reasons = {
                        'Kalite': 0,
                        'Fiyat': 0,
                        'Tasarım': 0,
                        'Kullanışlı': 0,
                        'Tavsiye': 0
                    }

                    for _, review in reviews.iterrows():
                        comment_lower = review['comment'].lower() if review['comment'] else ''
                        if 'kalite' in comment_lower or 'sağlam' in comment_lower:
                            reasons['Kalite'] += 1
                        if 'uygun' in comment_lower or 'ucuz' in comment_lower or 'fiyat' in comment_lower:
                            reasons['Fiyat'] += 1
                        if 'güzel' in comment_lower or 'şık' in comment_lower or 'tasarım' in comment_lower:
                            reasons['Tasarım'] += 1
                        if 'pratik' in comment_lower or 'kullanışlı' in comment_lower:
                            reasons['Kullanışlı'] += 1
                        if 'tavsiye' in comment_lower or 'öneri' in comment_lower:
                            reasons['Tavsiye'] += 1

                    # Bar chart
                    fig = px.bar(
                        x=list(reasons.values()),
                        y=list(reasons.keys()),
                        orientation='h',
                        title="Satın Alma Nedenleri",
                        labels={'x': 'Bahsedilme Sayısı', 'y': 'Neden'}
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # En faydalı yorumlar
                st.subheader("💭 En Faydalı Yorumlar")
                for idx, review in reviews.head(5).iterrows():
                    with st.expander(f"⭐ {review['rating']:.0f} - {review['reviewer_name']}"):
                        st.write(review['comment'])
                        st.caption(f"👍 {review['helpful_count']} kişi faydalı buldu")
            else:
                st.info("Bu ürün için henüz yorum bulunmuyor.")

        with tab3:
            st.subheader("📈 Fiyat Geçmişi")

            # Fiyat geçmişi verisi
            price_history = pd.read_sql_query(f"""
                SELECT price, timestamp
                FROM price_history
                WHERE product_id = {st.session_state.selected_product}
                ORDER BY timestamp
            """, conn)

            if not price_history.empty:
                # Zaman serisi grafiği
                fig = px.line(
                    price_history,
                    x='timestamp',
                    y='price',
                    title='Fiyat Değişim Grafiği',
                    labels={'price': 'Fiyat (₺)', 'timestamp': 'Tarih'}
                )
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig, use_container_width=True)

                # Fiyat istatistikleri
                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Min Fiyat",
                    f"₺{price_history['price'].min():.2f}"
                )
                col2.metric(
                    "Max Fiyat",
                    f"₺{price_history['price'].max():.2f}"
                )
                col3.metric(
                    "Ortalama",
                    f"₺{price_history['price'].mean():.2f}"
                )

                # Son değişim
                if len(price_history) > 1:
                    last_change = price_history.iloc[-1]['price'] - price_history.iloc[-2]['price']
                    col4.metric(
                        "Son Değişim",
                        f"₺{abs(last_change):.2f}",
                        delta=f"{'↑' if last_change > 0 else '↓'} {abs(last_change/price_history.iloc[-2]['price']*100):.1f}%"
                    )
            else:
                # Simüle edilmiş fiyat geçmişi oluştur
                st.info("Gerçek fiyat geçmişi henüz mevcut değil. Örnek veri gösteriliyor...")

                # Son 30 gün için örnek veri
                import numpy as np
                dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
                base_price = product_detail['price']
                prices = base_price + np.random.normal(0, base_price * 0.05, 30)

                price_history = pd.DataFrame({
                    'timestamp': dates,
                    'price': prices
                })

                fig = px.line(
                    price_history,
                    x='timestamp',
                    y='price',
                    title='Örnek Fiyat Değişim Grafiği (Son 30 Gün)',
                    labels={'price': 'Fiyat (₺)', 'timestamp': 'Tarih'}
                )
                fig.update_traces(mode='lines+markers')
                st.plotly_chart(fig, use_container_width=True)

    conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="İnteraktif Kategori Ağacı", layout="wide")
    show_interactive_category_tree()