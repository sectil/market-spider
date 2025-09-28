#!/usr/bin/env python3
"""
📂 KATEGORİ GÖRÜNÜMÜ
Dashboard için kategori bazlı analiz
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def display_category_view():
    """Kategori görünümünü göster"""

    st.title("🏪 Kategori Analizi")

    # Tab'lar ekle
    tab1, tab2 = st.tabs(["📊 İstatistikler", "🌳 İnteraktif Ağaç"])

    with tab1:
        display_category_statistics()

    with tab2:
        display_interactive_tree()


def display_category_statistics():
    """Kategori istatistikleri - eski görünüm"""

    conn = sqlite3.connect('market_spider.db')

    # Kategori istatistikleri
    st.header("📊 Kategori İstatistikleri")

    col1, col2, col3, col4 = st.columns(4)

    # Toplam kategori sayısı
    total_categories = pd.read_sql_query("""
        SELECT COUNT(*) as total
        FROM categories
    """, conn).iloc[0]['total']

    # Toplam ürün sayısı
    total_products = pd.read_sql_query("""
        SELECT COUNT(*) as total
        FROM products
    """, conn).iloc[0]['total']

    # Kategorili ürün sayısı
    categorized = pd.read_sql_query("""
        SELECT COUNT(*) as total
        FROM products
        WHERE category_id IS NOT NULL
    """, conn).iloc[0]['total']

    # En popüler kategori
    popular_category = pd.read_sql_query("""
        SELECT c.name, c.icon, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        GROUP BY c.id
        ORDER BY product_count DESC
        LIMIT 1
    """, conn).to_dict('records')[0] if categorized > 0 else {'name': 'N/A', 'icon': '', 'product_count': 0}

    col1.metric("📂 Toplam Kategori", total_categories)
    col2.metric("📦 Toplam Ürün", total_products)
    col3.metric("✅ Kategorize Edilmiş", f"{categorized}/{total_products}")
    col4.metric("🏆 En Popüler", f"{popular_category['icon']} {popular_category['name'][:15]}")

    # Kategori Ağacı
    st.header("🌳 Kategori Ağacı")

    # Ana kategoriler
    main_categories = pd.read_sql_query("""
        SELECT id, name, icon
        FROM categories
        WHERE parent_id IS NULL
        ORDER BY order_index
    """, conn)

    # Ağaç görünümü oluştur
    category_tree = []
    for _, main_cat in main_categories.iterrows():
        # Alt kategoriler
        sub_categories = pd.read_sql_query(f"""
            SELECT id, name
            FROM categories
            WHERE parent_id = {main_cat['id']}
            ORDER BY order_index
        """, conn)

        # Ürün sayısı
        product_count = pd.read_sql_query(f"""
            SELECT COUNT(p.id) as count
            FROM products p
            JOIN categories c ON p.category_id = c.id
            WHERE c.id = {main_cat['id']} OR c.parent_id = {main_cat['id']}
        """, conn).iloc[0]['count']

        category_tree.append({
            'Ana Kategori': f"{main_cat['icon']} {main_cat['name']}",
            'Alt Kategori Sayısı': len(sub_categories),
            'Ürün Sayısı': product_count,
            'Alt Kategoriler': ', '.join(sub_categories['name'].tolist()[:5])
        })

    df_tree = pd.DataFrame(category_tree)
    st.dataframe(df_tree, use_container_width=True)

    # Kategori bazlı ürün dağılımı
    st.header("📊 Ürün Dağılımı")

    # Pie chart için veri
    category_distribution = pd.read_sql_query("""
        SELECT
            CASE
                WHEN c.parent_id IS NULL THEN c.name
                ELSE (SELECT name FROM categories WHERE id = c.parent_id)
            END as main_category,
            c.icon,
            COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON p.category_id = c.id
        WHERE p.id IS NOT NULL
        GROUP BY main_category
        HAVING product_count > 0
    """, conn)

    if not category_distribution.empty:
        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig = px.pie(
                category_distribution,
                values='product_count',
                names='main_category',
                title='Ana Kategorilere Göre Dağılım'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Bar chart - Alt kategoriler
            subcategory_distribution = pd.read_sql_query("""
                SELECT c.name as category, c.icon, COUNT(p.id) as product_count
                FROM categories c
                LEFT JOIN products p ON p.category_id = c.id
                WHERE p.id IS NOT NULL AND c.parent_id IS NOT NULL
                GROUP BY c.id
                HAVING product_count > 0
                ORDER BY product_count DESC
                LIMIT 10
            """, conn)

            if not subcategory_distribution.empty:
                fig = px.bar(
                    subcategory_distribution,
                    x='product_count',
                    y='category',
                    orientation='h',
                    title='Top 10 Alt Kategori'
                )
                fig.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig, use_container_width=True)

    # Kategori Performansı
    st.header("📈 Kategori Performansı")

    # Her kategorinin ortalama puanı ve yorum sayısı
    category_performance = pd.read_sql_query("""
        SELECT
            c.name as category,
            c.icon,
            COUNT(DISTINCT p.id) as product_count,
            AVG(p.rating) as avg_rating,
            SUM(p.review_count) as total_reviews,
            AVG(p.price) as avg_price
        FROM categories c
        JOIN products p ON p.category_id = c.id
        WHERE c.parent_id IS NOT NULL
        GROUP BY c.id
        HAVING product_count > 0
        ORDER BY avg_rating DESC
    """, conn)

    if not category_performance.empty:
        # Metrikler
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("⭐ En Yüksek Puanlı Kategoriler")
            top_rated = category_performance.nlargest(5, 'avg_rating')[['category', 'avg_rating', 'product_count']]
            top_rated['avg_rating'] = top_rated['avg_rating'].round(1)
            st.dataframe(top_rated, use_container_width=True)

        with col2:
            st.subheader("💬 En Çok Yorum Alan Kategoriler")
            most_reviewed = category_performance.nlargest(5, 'total_reviews')[['category', 'total_reviews', 'product_count']]
            st.dataframe(most_reviewed, use_container_width=True)

        # Scatter plot - Rating vs Reviews
        fig = px.scatter(
            category_performance,
            x='avg_rating',
            y='total_reviews',
            size='product_count',
            hover_data=['category', 'avg_price'],
            title='Kategori Performans Matrisi',
            labels={
                'avg_rating': 'Ortalama Puan',
                'total_reviews': 'Toplam Yorum',
                'product_count': 'Ürün Sayısı'
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    # Kategori Detayları
    st.header("🔍 Kategori Detayları")

    # Kategori seçimi
    all_categories = pd.read_sql_query("""
        SELECT id, name,
               CASE
                   WHEN parent_id IS NULL THEN name
                   ELSE (SELECT name || ' > ' FROM categories WHERE id = c.parent_id) || name
               END as full_path
        FROM categories c
        ORDER BY full_path
    """, conn)

    selected_category = st.selectbox(
        "Kategori Seç:",
        options=all_categories['id'].tolist(),
        format_func=lambda x: all_categories[all_categories['id'] == x]['full_path'].iloc[0]
    )

    if selected_category:
        # Seçilen kategorideki ürünler
        products_in_category = pd.read_sql_query(f"""
            SELECT
                p.name,
                p.brand,
                p.price,
                p.rating,
                p.review_count,
                p.in_stock
            FROM products p
            WHERE p.category_id = {selected_category}
            ORDER BY p.review_count DESC
        """, conn)

        if not products_in_category.empty:
            st.subheader(f"📦 {all_categories[all_categories['id'] == selected_category]['full_path'].iloc[0]} Ürünleri")

            # Özet metrikler
            col1, col2, col3 = st.columns(3)
            col1.metric("Ürün Sayısı", len(products_in_category))
            col2.metric("Ortalama Fiyat", f"₺{products_in_category['price'].mean():.2f}")
            col3.metric("Ortalama Puan", f"{products_in_category['rating'].mean():.1f}⭐")

            # Ürün listesi
            st.dataframe(
                products_in_category,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "name": "Ürün",
                    "brand": "Marka",
                    "price": st.column_config.NumberColumn("Fiyat", format="₺%.2f"),
                    "rating": st.column_config.NumberColumn("Puan", format="%.1f⭐"),
                    "review_count": "Yorum",
                    "in_stock": st.column_config.CheckboxColumn("Stok")
                }
            )

            # En çok satan ürünler
            st.subheader("🏆 Bu Kategoride En Çok Satan")
            top_products = products_in_category.nlargest(3, 'review_count')[['name', 'rating', 'review_count', 'price']]

            for idx, product in top_products.iterrows():
                st.write(f"**{idx+1}. {product['name'][:50]}**")
                col1, col2, col3 = st.columns(3)
                col1.write(f"⭐ {product['rating']:.1f}")
                col2.write(f"💬 {product['review_count']} yorum")
                col3.write(f"💰 ₺{product['price']:.2f}")
        else:
            st.info("Bu kategoride henüz ürün bulunmuyor.")

    conn.close()


def display_interactive_tree():
    """İnteraktif kategori ağacı"""
    from datetime import datetime, timedelta
    import numpy as np

    conn = sqlite3.connect('market_spider.db')

    # Session state
    if 'selected_main_cat' not in st.session_state:
        st.session_state.selected_main_cat = None
    if 'selected_sub_cat' not in st.session_state:
        st.session_state.selected_sub_cat = None
    if 'selected_product_id' not in st.session_state:
        st.session_state.selected_product_id = None

    # 3 sütunlu layout
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        st.subheader("📂 Ana Kategoriler")

        main_cats = pd.read_sql_query("""
            SELECT c.id, c.name, c.icon, COUNT(DISTINCT p.id) as product_count
            FROM categories c
            LEFT JOIN categories sub ON sub.parent_id = c.id
            LEFT JOIN products p ON (p.category_id = c.id OR p.category_id = sub.id)
            WHERE c.parent_id IS NULL
            GROUP BY c.id
            HAVING product_count > 0
            ORDER BY c.order_index
        """, conn)

        for _, cat in main_cats.iterrows():
            if st.button(
                f"{cat['icon']} {cat['name']} ({cat['product_count']})",
                key=f"tree_main_{cat['id']}",
                use_container_width=True
            ):
                st.session_state.selected_main_cat = cat['id']
                st.session_state.selected_sub_cat = None
                st.session_state.selected_product_id = None

    with col2:
        st.subheader("📁 Alt Kategoriler")

        if st.session_state.selected_main_cat:
            # 2. seviye kategoriler ve altındaki ürün sayıları
            sub_cats = pd.read_sql_query(f"""
                SELECT
                    c.id,
                    c.name,
                    (
                        SELECT COUNT(*)
                        FROM products p
                        WHERE p.category_id = c.id
                           OR p.category_id IN (
                               SELECT id FROM categories
                               WHERE parent_id = c.id
                           )
                    ) as total_products,
                    (
                        SELECT COUNT(*)
                        FROM categories
                        WHERE parent_id = c.id
                    ) as child_count
                FROM categories c
                WHERE c.parent_id = {st.session_state.selected_main_cat}
                ORDER BY c.order_index
            """, conn)

            for _, subcat in sub_cats.iterrows():
                if subcat['total_products'] > 0:
                    # Alt kategori varsa yanında + işareti koy
                    icon = "📂" if subcat['child_count'] > 0 else "📄"

                    if st.button(
                        f"{icon} {subcat['name']} ({subcat['total_products']})",
                        key=f"tree_sub_{subcat['id']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_sub_cat = subcat['id']
                        st.session_state.selected_product_id = None

            # Eğer 2. seviye kategori seçiliyse, onun alt kategorilerini göster
            if st.session_state.selected_sub_cat:
                st.markdown("---")
                st.markdown("**📁 Alt Kategoriler:**")

                third_level = pd.read_sql_query(f"""
                    SELECT c.id, c.name, COUNT(p.id) as product_count
                    FROM categories c
                    LEFT JOIN products p ON p.category_id = c.id
                    WHERE c.parent_id = {st.session_state.selected_sub_cat}
                    GROUP BY c.id
                    HAVING product_count > 0
                    ORDER BY c.order_index
                """, conn)

                if not third_level.empty:
                    for _, thirdcat in third_level.iterrows():
                        if st.button(
                            f"  └─ {thirdcat['name']} ({thirdcat['product_count']})",
                            key=f"tree_third_{thirdcat['id']}",
                            use_container_width=True
                        ):
                            # 3. seviye kategori seçildiğinde onu sub_cat olarak ayarla
                            st.session_state.selected_sub_cat = thirdcat['id']
                            st.session_state.selected_product_id = None

    with col3:
        st.subheader("📦 Ürünler")

        category_id = st.session_state.selected_sub_cat or st.session_state.selected_main_cat

        if category_id:
            products = pd.read_sql_query(f"""
                SELECT id, name, brand, price, rating, review_count
                FROM products
                WHERE category_id = {category_id}
                ORDER BY review_count DESC, rating DESC
            """, conn)

            if not products.empty:
                for _, product in products.iterrows():
                    col_p1, col_p2 = st.columns([3, 1])

                    with col_p1:
                        st.markdown(f"""
                        **{product['name'][:45]}**
                        {product['brand']} | ⭐ {product['rating']:.1f} | 💬 {product['review_count']}
                        """)

                    with col_p2:
                        st.markdown(f"**₺{product['price']:.2f}**")
                        if st.button("📊", key=f"tree_detail_{product['id']}"):
                            st.session_state.selected_product_id = product['id']

    # Ürün detay bölümü
    if st.session_state.selected_product_id:
        st.markdown("---")

        # Gelişmiş analiz modülünü kullan
        from enhanced_product_analysis import show_enhanced_product_analysis
        show_enhanced_product_analysis(st.session_state.selected_product_id)

        # Eski kod yerine gelişmiş analiz kullanılıyor
        conn.close()
        return

        with tab1:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Marka", product['brand'])
            col2.metric("Fiyat", f"₺{product['price']:.2f}")
            col3.metric("Puan", f"⭐ {product['rating']:.1f}")
            col4.metric("Yorum", f"{product['review_count']:,}")

            st.markdown(f"### {product['name']}")
            st.write(f"**Stok:** {'✅ Var' if product['in_stock'] else '❌ Yok'}")

        with tab2:
            reviews = pd.read_sql_query(f"""
                SELECT * FROM product_reviews
                WHERE product_id = {st.session_state.selected_product_id}
                ORDER BY helpful_count DESC
                LIMIT 10
            """, conn)

            if not reviews.empty:
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("😊 Duygu Analizi")
                    sentiment = reviews['sentiment'].value_counts()

                    fig = px.pie(
                        values=sentiment.values,
                        names=sentiment.index,
                        title="Duygu Dağılımı",
                        color_discrete_map={
                            'olumlu': '#00CC88',
                            'olumsuz': '#FF4444',
                            'nötr': '#FFAA00'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("🎯 Satın Alma Nedenleri")

                    reasons = {
                        'Kalite': len([r for r in reviews['comment'] if r and ('kalite' in r.lower() or 'sağlam' in r.lower())]),
                        'Fiyat': len([r for r in reviews['comment'] if r and ('uygun' in r.lower() or 'ucuz' in r.lower())]),
                        'Tasarım': len([r for r in reviews['comment'] if r and ('güzel' in r.lower() or 'şık' in r.lower())]),
                        'Kullanışlı': len([r for r in reviews['comment'] if r and ('pratik' in r.lower() or 'kullanışlı' in r.lower())])
                    }

                    fig = px.bar(
                        x=list(reasons.values()),
                        y=list(reasons.keys()),
                        orientation='h',
                        title="Neden Tercih Ediliyor?"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.subheader("💭 En Faydalı Yorumlar")
                for _, review in reviews.head(3).iterrows():
                    with st.expander(f"⭐ {review['rating']:.0f} - {review['reviewer_name']}"):
                        st.write(review['comment'])
                        st.caption(f"👍 {review['helpful_count']} kişi faydalı buldu")

        with tab3:
            st.subheader("📈 Fiyat Değişimi")

            # Örnek fiyat geçmişi oluştur
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            base = product['price']
            prices = base + np.random.normal(0, base * 0.03, 30).cumsum()

            price_df = pd.DataFrame({
                'Tarih': dates,
                'Fiyat': prices
            })

            fig = px.line(
                price_df, x='Tarih', y='Fiyat',
                title='Son 30 Gün Fiyat Grafiği'
            )
            fig.update_traces(mode='lines+markers')
            st.plotly_chart(fig, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Min", f"₺{prices.min():.2f}")
            col2.metric("Max", f"₺{prices.max():.2f}")
            col3.metric("Ortalama", f"₺{prices.mean():.2f}")

    conn.close()


if __name__ == "__main__":
    st.set_page_config(page_title="Kategori Analizi", layout="wide")
    display_category_view()