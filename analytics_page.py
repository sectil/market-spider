#!/usr/bin/env python3
"""
Detaylı Analiz Sayfası - Kategori bazlı en çok satanlar ve trend analizi
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from database import SessionLocal, Product, PriceHistory, RankingHistory, SiteConfig, ProductReview
from sqlalchemy import or_
import sqlite3
from sqlalchemy import or_
import sqlite3
from sqlalchemy import func, and_, desc
import numpy as np

def show_product_detail(product_id):
    """Ürün detay modalı"""
    session = SessionLocal()

    # Ürünü getir
    product = session.query(Product).filter_by(id=product_id).first()
    if not product:
        st.error("Ürün bulunamadı!")
        return

    # Modal benzeri görünüm için expander kullan
    with st.expander(f"📦 {product.name} - Detaylı Analiz", expanded=True):

        # Ürün bilgileri
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("💵 Güncel Fiyat", f"{product.price:.2f} TL")

        with col2:
            st.metric("⭐ Rating", f"{product.rating:.1f}")

        with col3:
            st.metric("💬 Yorum", f"{product.review_count:,}")

        # Fiyat geçmişi grafiği
        st.subheader("📈 Fiyat Geçmişi")

        price_history = session.query(
            PriceHistory.timestamp,
            PriceHistory.price,
            PriceHistory.original_price,
            PriceHistory.discount_percentage
        ).filter(
            PriceHistory.product_id == product_id
        ).order_by(
            PriceHistory.timestamp
        ).all()

        if price_history:
            df_price = pd.DataFrame(price_history)

            fig = go.Figure()

            # Ana fiyat çizgisi
            fig.add_trace(go.Scatter(
                x=df_price['timestamp'],
                y=df_price['price'],
                mode='lines+markers',
                name='Satış Fiyatı',
                line=dict(color='#2ecc71', width=3),
                marker=dict(size=8)
            ))

            # İndirim öncesi fiyat
            if df_price['original_price'].notna().any():
                fig.add_trace(go.Scatter(
                    x=df_price['timestamp'],
                    y=df_price['original_price'],
                    mode='lines',
                    name='Liste Fiyatı',
                    line=dict(color='#e74c3c', dash='dash', width=2)
                ))

            # İndirim yüzdesi (ikinci y ekseni)
            fig.add_trace(go.Scatter(
                x=df_price['timestamp'],
                y=df_price['discount_percentage'],
                mode='lines',
                name='İndirim %',
                line=dict(color='#f39c12', width=2),
                yaxis='y2'
            ))

            fig.update_layout(
                title=f"{product.name[:50]}... Fiyat Trendi",
                xaxis_title="Tarih",
                yaxis_title="Fiyat (TL)",
                yaxis2=dict(
                    title='İndirim %',
                    overlaying='y',
                    side='right',
                    range=[0, 100]
                ),
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

            # Fiyat istatistikleri
            st.subheader("📊 Fiyat İstatistikleri")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                min_price = df_price['price'].min()
                st.metric("📉 En Düşük", f"{min_price:.2f} TL")

            with col2:
                max_price = df_price['price'].max()
                st.metric("📈 En Yüksek", f"{max_price:.2f} TL")

            with col3:
                avg_price = df_price['price'].mean()
                st.metric("📊 Ortalama", f"{avg_price:.2f} TL")

            with col4:
                price_change = df_price['price'].iloc[-1] - df_price['price'].iloc[0]
                change_pct = (price_change / df_price['price'].iloc[0]) * 100
                st.metric("📈 Değişim", f"%{change_pct:.1f}", f"{price_change:+.2f} TL")

        # Sıralama geçmişi
        st.subheader("🏆 Sıralama Performansı")

        ranking_history = session.query(
            RankingHistory.timestamp,
            RankingHistory.rank_position,
            RankingHistory.category_rank
        ).filter(
            RankingHistory.product_id == product_id
        ).order_by(
            RankingHistory.timestamp
        ).all()

        if ranking_history:
            df_rank = pd.DataFrame(ranking_history)

            fig2 = go.Figure()

            fig2.add_trace(go.Scatter(
                x=df_rank['timestamp'],
                y=df_rank['rank_position'],
                mode='lines+markers',
                name='Genel Sıralama',
                line=dict(color='#3498db', width=2)
            ))

            fig2.add_trace(go.Scatter(
                x=df_rank['timestamp'],
                y=df_rank['category_rank'],
                mode='lines+markers',
                name='Kategori Sıralaması',
                line=dict(color='#9b59b6', width=2)
            ))

            fig2.update_layout(
                title="Sıralama Değişimi",
                xaxis_title="Tarih",
                yaxis_title="Sıralama",
                yaxis=dict(autorange='reversed'),  # Düşük sıra yukarıda
                hovermode='x unified',
                height=300
            )

            st.plotly_chart(fig2, use_container_width=True)

    session.close()

def show_detailed_analytics():
    """Detaylı analiz sayfası"""
    st.header("📊 Detaylı Ürün Analizi")

    session = SessionLocal()

    # Sidebar'da filtreler
    with st.sidebar:
        st.subheader("🔍 Filtreler")

        # Kategori seçimi
        categories = session.query(Product.category).distinct().all()
        categories = [cat[0] for cat in categories if cat[0]]
        categories.insert(0, "Tüm Kategoriler")

        selected_category = st.selectbox(
            "📦 Kategori",
            categories,
            help="Analiz edilecek kategoriyi seçin"
        )

        # Zaman aralığı seçimi
        time_range = st.selectbox(
            "📅 Zaman Aralığı",
            ["Son 24 Saat", "Son 7 Gün", "Son 30 Gün", "Son 6 Ay", "Son 1 Yıl"],
            index=1
        )

        # Site seçimi
        sites = session.query(SiteConfig).filter_by(is_active=True).all()
        site_names = ["Tüm Siteler"] + [site.site_name for site in sites]
        selected_site = st.selectbox("🏪 Site", site_names)

        # Top N ürün sayısı
        top_n = st.slider("🏆 Top N Ürün", 5, 50, 10, 5)

    # Zaman aralığını hesapla
    time_ranges = {
        "Son 24 Saat": timedelta(days=1),
        "Son 7 Gün": timedelta(days=7),
        "Son 30 Gün": timedelta(days=30),
        "Son 6 Ay": timedelta(days=180),
        "Son 1 Yıl": timedelta(days=365)
    }
    time_delta = time_ranges[time_range]
    start_date = datetime.now() - time_delta

    # Ana metrikler
    st.markdown("### 📈 Özet Metrikler")
    col1, col2, col3, col4 = st.columns(4)

    # Kategori filtresi uygula
    query = session.query(Product)
    if selected_category != "Tüm Kategoriler":
        query = query.filter(Product.category == selected_category)
    if selected_site != "Tüm Siteler":
        query = query.filter(Product.site_name == selected_site.lower())

    products = query.all()
    total_products = len(products)

    with col1:
        st.metric("📦 Toplam Ürün", f"{total_products:,}")

    # Ortalama fiyat
    avg_price = session.query(func.avg(Product.price)).scalar() or 0
    with col2:
        st.metric("💰 Ort. Fiyat", f"{avg_price:.2f} TL")

    # En çok satan marka
    top_brand = session.query(
        Product.brand,
        func.count(Product.id).label('count')
    )
    if selected_category != "Tüm Kategoriler":
        top_brand = top_brand.filter(Product.category == selected_category)
    top_brand = top_brand.group_by(Product.brand).order_by(desc('count')).first()

    with col3:
        st.metric("🏷️ En Popüler Marka", top_brand[0] if top_brand else "N/A")

    # Fiyat değişimi
    price_change = session.query(
        func.avg(PriceHistory.discount_percentage)
    ).filter(
        PriceHistory.timestamp >= start_date
    ).scalar() or 0

    with col4:
        st.metric("📉 Ort. İndirim", f"%{abs(price_change):.1f}")

    st.markdown("---")

    # Tab'lar
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 En Çok Satanlar",
        "📈 Fiyat Trendleri",
        "📊 Kategori Analizi",
        "🏷️ Marka Analizi",
        "🔄 Değişim Analizi",
        "🧠 Yorum Analizi"
    ])

    with tab1:
        show_best_sellers_tab(session, selected_category, selected_site, top_n, start_date)

    with tab2:
        show_price_trends_tab(session, selected_category, selected_site, start_date)

    with tab3:
        show_category_analysis_tab(session, selected_site)

    with tab4:
        show_brand_analysis_tab(session, selected_category, selected_site)

    with tab5:
        show_change_analysis_tab(session, selected_category, time_range)

    with tab6:
        show_review_analysis_tab(session, selected_category, selected_site, top_n)

    session.close()

def show_best_sellers_tab(session, category, site, top_n, start_date):
    """En çok satanlar tab'ı"""
    st.subheader("🏆 En Çok Satan Ürünler")

    # En çok satan ürünleri getir
    query = session.query(
        Product.id,
        Product.name,
        Product.brand,
        Product.price,
        Product.rating,
        Product.review_count,
        Product.image_url,
        Product.product_url,
        func.min(RankingHistory.rank_position).label('best_rank'),
        func.avg(RankingHistory.rank_position).label('avg_rank')
    ).join(
        RankingHistory, Product.id == RankingHistory.product_id
    ).filter(
        RankingHistory.timestamp >= start_date
    )

    if category != "Tüm Kategoriler":
        query = query.filter(Product.category == category)
    if site != "Tüm Siteler":
        query = query.filter(Product.site_name == site.lower())

    best_sellers = query.group_by(
        Product.id
    ).order_by(
        'best_rank'
    ).limit(top_n).all()

    # İki sütunlu layout
    for i in range(0, len(best_sellers), 2):
        cols = st.columns(2)

        for j, col in enumerate(cols):
            if i + j < len(best_sellers):
                product = best_sellers[i + j]
                with col:
                    # Son güncelleme tarihi al
                    last_update = session.query(
                        func.max(PriceHistory.timestamp)
                    ).filter(
                        PriceHistory.product_id == product.id
                    ).scalar()

                    # Gerçek anlık fiyat
                    current_price = session.query(
                        PriceHistory.price
                    ).filter(
                        PriceHistory.product_id == product.id
                    ).order_by(
                        PriceHistory.timestamp.desc()
                    ).first()

                    actual_price = current_price[0] if current_price else product.price

                    # Ürün kartı
                    st.markdown(f"""
                        <div style='background: white; padding: 15px; border-radius: 10px;
                                    box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px;'>
                            <div style='display: flex; align-items: center;'>
                                <div style='flex: 1;'>
                                    <h4 style='margin: 0; color: #333;'>#{i+j+1} {product.name[:50]}...</h4>
                                    <p style='margin: 5px 0; color: #666;'>
                                        <b>Marka:</b> {product.brand}<br>
                                        <b>Güncel Fiyat:</b> <span style='color: #e74c3c; font-weight: bold; font-size: 18px;'>{actual_price:.2f} TL</span><br>
                                        <b>Rating:</b> ⭐ {product.rating:.1f} ({product.review_count:,} yorum)<br>
                                        <b>En İyi Sıra:</b> #{int(product.best_rank)}<br>
                                        <b>Ort. Sıra:</b> #{int(product.avg_rank)}<br>
                                        <b>Son Güncelleme:</b> {last_update.strftime('%d.%m.%Y %H:%M') if last_update else 'Bilinmiyor'}
                                    </p>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Fiyat grafiği
                    price_history = session.query(
                        PriceHistory.timestamp,
                        PriceHistory.price,
                        PriceHistory.original_price
                    ).filter(
                        PriceHistory.product_id == product.id,
                        PriceHistory.timestamp >= start_date
                    ).order_by(
                        PriceHistory.timestamp
                    ).all()

                    if price_history and len(price_history) > 1:
                        df_price = pd.DataFrame(price_history)

                        # Mini fiyat grafiği
                        fig = go.Figure()

                        fig.add_trace(go.Scatter(
                            x=df_price['timestamp'],
                            y=df_price['price'],
                            mode='lines+markers',
                            name='Fiyat',
                            line=dict(color='#3498db', width=2),
                            marker=dict(size=6)
                        ))

                        if df_price['original_price'].notna().any():
                            fig.add_trace(go.Scatter(
                                x=df_price['timestamp'],
                                y=df_price['original_price'],
                                mode='lines',
                                name='İndirimli Fiyat',
                                line=dict(color='#e74c3c', dash='dash')
                            ))

                        fig.update_layout(
                            height=200,
                            margin=dict(l=0, r=0, t=20, b=0),
                            showlegend=True,
                            legend=dict(
                                orientation="h",
                                yanchor="bottom",
                                y=1.02,
                                xanchor="right",
                                x=1
                            ),
                            xaxis_title="",
                            yaxis_title="Fiyat (TL)",
                            hovermode='x unified'
                        )

                        st.plotly_chart(fig, use_container_width=True, key=f"price_chart_{product.id}")

                    # Detay butonu
                    if st.button(f"📊 Detaylı Analiz", key=f"detail_{product.id}"):
                        show_product_detail(product.id)

def show_price_trends_tab(session, category, site, start_date):
    """Fiyat trendleri tab'ı"""
    st.subheader("📈 Fiyat Trendleri")

    # Fiyat verilerini getir
    query = session.query(
        PriceHistory.timestamp,
        func.avg(PriceHistory.price).label('avg_price'),
        func.min(PriceHistory.price).label('min_price'),
        func.max(PriceHistory.price).label('max_price')
    ).join(
        Product, PriceHistory.product_id == Product.id
    ).filter(
        PriceHistory.timestamp >= start_date
    )

    if category != "Tüm Kategoriler":
        query = query.filter(Product.category == category)
    if site != "Tüm Siteler":
        query = query.filter(Product.site_name == site.lower())

    price_data = query.group_by(
        func.date(PriceHistory.timestamp)
    ).order_by(
        PriceHistory.timestamp
    ).all()

    if price_data:
        # DataFrame oluştur
        df = pd.DataFrame(price_data)

        # Grafik oluştur
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['avg_price'],
            mode='lines+markers',
            name='Ortalama Fiyat',
            line=dict(color='blue', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['min_price'],
            mode='lines',
            name='Min Fiyat',
            line=dict(color='green', dash='dash')
        ))

        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['max_price'],
            mode='lines',
            name='Max Fiyat',
            line=dict(color='red', dash='dash')
        ))

        fig.update_layout(
            title="Fiyat Trend Analizi",
            xaxis_title="Tarih",
            yaxis_title="Fiyat (TL)",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # İstatistikler
        col1, col2, col3 = st.columns(3)

        with col1:
            price_change = ((df['avg_price'].iloc[-1] - df['avg_price'].iloc[0]) / df['avg_price'].iloc[0]) * 100
            st.metric(
                "Fiyat Değişimi",
                f"%{price_change:+.2f}",
                delta=f"{df['avg_price'].iloc[-1] - df['avg_price'].iloc[0]:.2f} TL"
            )

        with col2:
            st.metric(
                "En Düşük Fiyat",
                f"{df['min_price'].min():.2f} TL",
                delta=f"Tarih: {df.loc[df['min_price'].idxmin(), 'timestamp'].strftime('%d.%m.%Y')}"
            )

        with col3:
            st.metric(
                "En Yüksek Fiyat",
                f"{df['max_price'].max():.2f} TL",
                delta=f"Tarih: {df.loc[df['max_price'].idxmax(), 'timestamp'].strftime('%d.%m.%Y')}"
            )
    else:
        st.info("Bu zaman aralığında fiyat verisi bulunamadı.")

def show_category_analysis_tab(session, site):
    """Kategori analizi tab'ı"""
    st.subheader("📊 Kategori Analizi")

    # Kategori istatistikleri
    query = session.query(
        Product.category,
        func.count(Product.id).label('product_count'),
        func.avg(Product.price).label('avg_price'),
        func.avg(Product.rating).label('avg_rating')
    )

    if site != "Tüm Siteler":
        query = query.filter(Product.site_name == site.lower())

    category_stats = query.group_by(Product.category).all()

    if category_stats:
        df = pd.DataFrame(category_stats)

        # Pasta grafik - Ürün dağılımı
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                df,
                values='product_count',
                names='category',
                title='Kategori Bazında Ürün Dağılımı'
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Bar chart - Ortalama fiyatlar
            fig = px.bar(
                df.sort_values('avg_price', ascending=False),
                x='category',
                y='avg_price',
                title='Kategori Bazında Ortalama Fiyatlar',
                color='avg_price',
                color_continuous_scale='viridis'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        # Detaylı tablo
        st.markdown("### 📋 Kategori Detayları")
        df_display = df.copy()
        df_display['avg_price'] = df_display['avg_price'].round(2)
        df_display['avg_rating'] = df_display['avg_rating'].round(2)
        df_display.columns = ['Kategori', 'Ürün Sayısı', 'Ort. Fiyat (TL)', 'Ort. Rating']
        st.dataframe(df_display, use_container_width=True)

def show_brand_analysis_tab(session, category, site):
    """Marka analizi tab'ı"""
    st.subheader("🏷️ Marka Analizi")

    # Marka istatistikleri
    query = session.query(
        Product.brand,
        func.count(Product.id).label('product_count'),
        func.avg(Product.price).label('avg_price'),
        func.avg(Product.rating).label('avg_rating'),
        func.sum(Product.review_count).label('total_reviews')
    )

    if category != "Tüm Kategoriler":
        query = query.filter(Product.category == category)
    if site != "Tüm Siteler":
        query = query.filter(Product.site_name == site.lower())

    brand_stats = query.group_by(Product.brand).having(
        Product.brand != None
    ).order_by(desc('product_count')).limit(20).all()

    if brand_stats:
        df = pd.DataFrame(brand_stats)

        # Treemap - Marka büyüklükleri
        fig = px.treemap(
            df,
            path=['brand'],
            values='product_count',
            color='avg_rating',
            hover_data=['avg_price', 'total_reviews'],
            color_continuous_scale='RdYlGn',
            title='Marka Büyüklükleri ve Performansı'
        )
        st.plotly_chart(fig, use_container_width=True)

        # Top 10 Marka tablosu
        st.markdown("### 🏆 Top 10 Marka")
        df_top = df.head(10).copy()
        df_top['avg_price'] = df_top['avg_price'].round(2)
        df_top['avg_rating'] = df_top['avg_rating'].round(2)
        df_top.columns = ['Marka', 'Ürün Sayısı', 'Ort. Fiyat', 'Ort. Rating', 'Toplam Yorum']
        st.dataframe(df_top, use_container_width=True)

def show_change_analysis_tab(session, category, time_range):
    """Değişim analizi tab'ı"""
    st.subheader("🔄 Zaman Bazlı Değişim Analizi")

    # Periyodik karşılaştırma
    periods = {
        "Son 24 Saat": (timedelta(days=1), "Günlük"),
        "Son 7 Gün": (timedelta(days=7), "Haftalık"),
        "Son 30 Gün": (timedelta(days=30), "Aylık"),
        "Son 6 Ay": (timedelta(days=180), "6 Aylık"),
        "Son 1 Yıl": (timedelta(days=365), "Yıllık")
    }

    st.markdown("### 📊 Periyodik Değişimler")

    cols = st.columns(len(periods))

    for i, (period_name, (delta, label)) in enumerate(periods.items()):
        with cols[i]:
            start = datetime.now() - delta

            # Ürün sayısı değişimi
            new_products = session.query(Product).filter(
                Product.created_at >= start
            )
            if category != "Tüm Kategoriler":
                new_products = new_products.filter(Product.category == category)
            new_count = new_products.count()

            # Fiyat değişimi
            price_change = session.query(
                func.avg(PriceHistory.discount_percentage)
            ).filter(
                PriceHistory.timestamp >= start
            ).scalar() or 0

            st.markdown(f"""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 15px; border-radius: 10px; text-align: center; color: white;'>
                    <h4 style='margin: 0;'>{label}</h4>
                    <div style='font-size: 24px; font-weight: bold; margin: 10px 0;'>
                        +{new_count}
                    </div>
                    <div style='font-size: 14px;'>Yeni Ürün</div>
                    <div style='font-size: 18px; margin-top: 10px;'>
                        %{abs(price_change):.1f} {' ↓' if price_change < 0 else ' ↑'}
                    </div>
                    <div style='font-size: 14px;'>Fiyat Değişimi</div>
                </div>
            """, unsafe_allow_html=True)

    # Trend grafiği
    st.markdown("### 📈 Uzun Dönem Trend")

    # Son 30 günlük veri
    thirty_days_ago = datetime.now() - timedelta(days=30)
    daily_stats = []

    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        next_date = date + timedelta(days=1)

        # O güne ait istatistikler
        products_count = session.query(Product).filter(
            and_(Product.created_at >= date, Product.created_at < next_date)
        )
        if category != "Tüm Kategoriler":
            products_count = products_count.filter(Product.category == category)

        avg_price = session.query(func.avg(PriceHistory.price)).filter(
            and_(PriceHistory.timestamp >= date, PriceHistory.timestamp < next_date)
        ).scalar() or 0

        daily_stats.append({
            'date': date,
            'new_products': products_count.count(),
            'avg_price': avg_price
        })

    if daily_stats:
        df = pd.DataFrame(daily_stats)

        # Çift eksenli grafik için subplots kullan
        from plotly.subplots import make_subplots

        fig = make_subplots(
            specs=[[{"secondary_y": True}]]
        )

        # Bar chart - yeni ürünler
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['new_products'],
                name='Yeni Ürünler',
                marker_color='lightblue'
            ),
            secondary_y=False,
        )

        # Line chart - ortalama fiyat
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['avg_price'],
                mode='lines',
                name='Ort. Fiyat',
                line=dict(color='red', width=2)
            ),
            secondary_y=True,
        )

        # Eksen başlıkları
        fig.update_xaxes(title_text="Tarih")
        fig.update_yaxes(title_text="Yeni Ürün Sayısı", secondary_y=False)
        fig.update_yaxes(title_text="Ortalama Fiyat (TL)", secondary_y=True)

        fig.update_layout(
            title="30 Günlük Trend Analizi",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

def show_product_detail(product_id):
    """Ürün detay modalı"""
    session = SessionLocal()
    product = session.query(Product).filter_by(id=product_id).first()

    if product:
        # Modal benzeri bir görünüm için expander kullan
        with st.expander(f"📦 {product.name}", expanded=True):
            col1, col2 = st.columns([1, 2])

            with col1:
                if product.image_url:
                    st.image(product.image_url, use_container_width=True)

            with col2:
                st.markdown(f"""
                    **Marka:** {product.brand}
                    **Kategori:** {product.category}
                    **Fiyat:** {product.price:.2f} TL
                    **Rating:** ⭐ {product.rating:.1f} ({product.review_count:,} yorum)
                    **Satıcı:** {product.seller}
                    **Site:** {product.site_name}
                """)

                if st.button("🔗 Ürüne Git", key=f"go_{product_id}"):
                    st.markdown(f"[Ürün Sayfası]({product.product_url})")

    session.close()

def show_review_analysis_tab(session, category, site, top_n):
    """Yorum analizi tab'ı - İnsan davranışlarını analiz eder"""
    st.subheader("🧠 Müşteri Yorum Analizi ve İnsan Davranışları")

    # Analiz seçenekleri
    col1, col2 = st.columns(2)

    with col1:
        analysis_type = st.radio(
            "📊 Analiz Tipi",
            ["Tekil Ürün Analizi", "Kategori Toplu Analizi", "En Çok Satanlar Analizi"]
        )

    with col2:
        if st.button("🔄 Yorumları Güncelle", help="Trendyol'dan güncel yorumları çek"):
            with st.spinner("Yorumlar çekiliyor..."):
                from trendyol_review_scraper import TrendyolReviewScraper
                scraper = TrendyolReviewScraper()
                scraper.scrape_all_best_sellers()
                st.success("✅ Yorumlar güncellendi!")

    # İlgili ürünleri getir
    if analysis_type == "Tekil Ürün Analizi":
        # Ürün seçimi
        products = session.query(Product).filter(
            Product.category == category if category != "Tüm Kategoriler" else True
        ).all()

        if products:
            product_names = [f"{p.name[:50]}... ({p.brand})" for p in products]
            selected_idx = st.selectbox("Ürün Seçin", range(len(products)),
                                       format_func=lambda x: product_names[x])
            selected_product = products[selected_idx]

            # Ürün yorumlarını getir
            reviews = session.query(ProductReview).filter_by(
                product_id=selected_product.id
            ).all()

            if reviews:
                show_product_review_analysis(selected_product, reviews, session)
            else:
                st.info("📝 Bu ürün için henüz yorum yok.")

                # Manuel yorum ekleme seçenekleri
                st.markdown("### 📥 Yorum Ekleme Seçenekleri")

                tab1, tab2, tab3 = st.tabs(["🖊️ Manuel Giriş", "📋 Toplu Yapıştır", "🔄 Otomatik Çek"])

                with tab1:
                    st.subheader("Manuel Yorum Girişi")
                    with st.form(key="manual_review_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            reviewer_name = st.text_input("Yorumcu Adı", "Trendyol Müşterisi")
                            rating = st.slider("Puan", 1, 5, 5)
                            verified = st.checkbox("Doğrulanmış Alıcı", value=True)

                        with col2:
                            helpful_count = st.number_input("Faydalı Bulma", 0, 1000, 0)
                            import random
                            from datetime import timedelta
                            days_ago = st.number_input("Kaç gün önce", 0, 365, random.randint(1, 30))

                        review_text = st.text_area("Yorum Metni (Gerçek Trendyol yorumu)",
                                                  height=150,
                                                  placeholder="Ürün gerçekten çok güzel...")

                        if st.form_submit_button("💾 Yorumu Kaydet", type="primary"):
                            if review_text and len(review_text) > 10:
                                from turkish_review_ai import TurkishReviewAI
                                ai = TurkishReviewAI()
                                analysis = ai.analyze_review(review_text)

                                new_review = ProductReview(
                                    product_id=selected_product.id,
                                    reviewer_name=reviewer_name,
                                    reviewer_verified=verified,
                                    rating=rating,
                                    review_title='',
                                    review_text=review_text,
                                    review_date=datetime.now() - timedelta(days=days_ago),
                                    helpful_count=helpful_count,
                                    sentiment_score=analysis['sentiment_score'],
                                    key_phrases=analysis['key_phrases'],
                                    purchase_reasons=analysis['purchase_reasons'],
                                    pros=analysis['pros'],
                                    cons=analysis['cons']
                                )

                                session.add(new_review)
                                session.commit()
                                st.success("✅ Yorum kaydedildi!")
                                st.rerun()
                            else:
                                st.error("❌ Geçerli bir yorum girin!")

                with tab2:
                    st.subheader("Toplu Yorum Yapıştır")
                    bulk_reviews = st.text_area(
                        "Trendyol'dan kopyalanan yorumları yapıştır (her satır bir yorum)",
                        height=300,
                        placeholder="Ürün çok kaliteli geldi...\nHızlı kargo teşekkürler...\nTam beden uyumlu..."
                    )

                    if st.button("📥 Toplu Kaydet", key="bulk_save"):
                        if bulk_reviews:
                            from turkish_review_ai import TurkishReviewAI
                            ai = TurkishReviewAI()
                            import random
                            from datetime import timedelta

                            lines = [l.strip() for l in bulk_reviews.strip().split('\n') if l.strip()]
                            added = 0

                            progress = st.progress(0)
                            for i, line in enumerate(lines):
                                if len(line) > 10:
                                    analysis = ai.analyze_review(line)

                                    # Rating tahmin et
                                    sentiment = analysis['sentiment_score']
                                    if sentiment > 0.3:
                                        rating = 5 if sentiment > 0.6 else 4
                                    elif sentiment > -0.3:
                                        rating = 3
                                    else:
                                        rating = 2 if sentiment > -0.6 else 1

                                    new_review = ProductReview(
                                        product_id=selected_product.id,
                                        reviewer_name=f"Müşteri_{random.randint(100, 999)}",
                                        reviewer_verified=True,
                                        rating=rating,
                                        review_title='',
                                        review_text=line,
                                        review_date=datetime.now() - timedelta(days=random.randint(1, 60)),
                                        helpful_count=random.randint(0, 100),
                                        sentiment_score=analysis['sentiment_score'],
                                        key_phrases=analysis['key_phrases'],
                                        purchase_reasons=analysis['purchase_reasons'],
                                        pros=analysis['pros'],
                                        cons=analysis['cons']
                                    )

                                    session.add(new_review)
                                    added += 1

                                progress.progress((i + 1) / len(lines))

                            session.commit()
                            st.success(f"✅ {added} yorum kaydedildi!")
                            st.rerun()
                        else:
                            st.error("❌ Yorum metni girin!")

                with tab3:
                    st.subheader("⚡ ULTRA Otomatik Yorum Çekme")
                    st.info("✅ Akıllı API kullanımı - Chrome gerekmez")
                    st.error("❌ FALLBACK YOK - %100 GERÇEK VERİ!")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("📡 Direct API", type="primary", use_container_width=True, help="En basit ve etkili yöntem"):
                            with st.spinner("📡 Direct API ile TÜM yorumlar çekiliyor..."):
                                from direct_api_scraper import DirectAPIScraper
                                scraper = DirectAPIScraper()
                                success = scraper.scrape_all_reviews_direct(selected_product.id)
                                if success:
                                    st.success("✅ TÜM yorumlar çekildi!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ API erişilemez!")
                                scraper.session.close()

                    with col2:
                        if st.button("🌐 Proxy/DNS", use_container_width=True, help="curl ve DNS workaround kullanır"):
                            with st.spinner("🌐 curl ile çekiliyor..."):
                                from proxy_api_scraper import ProxyAPIScraper
                                scraper = ProxyAPIScraper()
                                success = scraper.scrape_all_reviews_with_proxy(selected_product.id)
                                if success:
                                    st.success("✅ Yorumlar çekildi!")
                                    st.balloons()
                                    st.rerun()
                                else:
                                    st.error("❌ Çekilemedi!")
                                scraper.session.close()

                    with col3:
                        if st.button("🎭 Playwright", use_container_width=True, help="Browser ile çeker"):
                            with st.spinner("🎭 Playwright çalışıyor..."):
                                from playwright_scraper import PlaywrightScraper
                                scraper = PlaywrightScraper()
                                success = scraper.scrape_with_playwright(selected_product.id)
                                if success:
                                    st.success("✅ Yorumlar çekildi!")
                                    st.rerun()
                                else:
                                    st.error("❌ Sistem bağımlılıkları eksik!")
                                scraper.session.close()

                    with col4:
                        if st.button("⚡ Ultimate", use_container_width=True, help="3 strateji ile çeker"):
                            with st.spinner("⚡ Ultimate scraper çalışıyor..."):
                                from ultimate_review_scraper import UltimateReviewScraper
                                scraper = UltimateReviewScraper()
                                success = scraper.scrape_all_reviews(selected_product.id)
                                if success:
                                    st.success("✅ Yorumlar çekildi!")
                                    st.rerun()
                                else:
                                    st.error("❌ API erişilemez!")
                                scraper.session.close()

    elif analysis_type == "Kategori Toplu Analizi":
        # Kategorideki tüm yorumları analiz et
        show_category_review_analysis(session, category, site)

    else:  # En Çok Satanlar Analizi
        show_best_sellers_review_analysis(session, category, top_n)


def show_product_review_analysis(product, reviews, session):
    """Tek ürün için yorum analizi göster"""
    from turkish_review_ai import TurkishReviewAI

    st.markdown(f"### 📦 {product.name}")

    # Yorum istatistikleri
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("💬 Toplam Yorum", len(reviews))

    with col2:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)
        st.metric("⭐ Ortalama Puan", f"{avg_rating:.1f}")

    with col3:
        verified_count = sum(1 for r in reviews if r.reviewer_verified)
        st.metric("✅ Doğrulanmış Alıcı", f"%{verified_count/len(reviews)*100:.0f}")

    with col4:
        avg_sentiment = sum(r.sentiment_score for r in reviews if r.sentiment_score) / len(reviews)
        st.metric("😊 Duygu Skoru", f"{avg_sentiment:.2f}")

    # AI ile toplu analiz
    ai = TurkishReviewAI()
    reviews_data = [{
        'text': r.review_text,
        'rating': r.rating,
        'verified': r.reviewer_verified,
        'helpful_count': r.helpful_count
    } for r in reviews]

    analysis = ai.analyze_bulk_reviews(reviews_data)

    # İnsan Davranışı Analizi
    st.markdown("### 🧠 İnsan Davranışı Analizi")

    insights = analysis['human_insights']

    # Ana bulgular
    st.info(f"**📍 Ana Motivasyon:** {insights['ana_motivasyon']}")
    st.success(f"**👤 Müşteri Profili:** {insights['müşteri_profili']}")

    # Satın alma psikolojisi
    with st.expander("🎯 Satın Alma Psikolojisi", expanded=True):
        st.write(insights['satın_alma_psikolojisi'])

    # İki sütunlu layout
    col1, col2 = st.columns(2)

    with col1:
        # Başarı faktörleri
        st.markdown("### ✨ Başarı Faktörleri")
        for factor in insights['başarı_faktörleri']:
            st.success(f"✓ {factor}")

        # Satın alma nedenleri
        st.markdown("### 🛒 Satın Alma Nedenleri")
        reasons_df = pd.DataFrame(
            analysis['top_purchase_reasons'],
            columns=['Neden', 'Sayı']
        )
        if not reasons_df.empty:
            fig = px.bar(reasons_df, x='Sayı', y='Neden', orientation='h',
                        color='Sayı', color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Risk faktörleri
        if insights['risk_faktörleri'] and insights['risk_faktörleri'][0] != 'Belirgin risk faktörü yok':
            st.markdown("### ⚠️ Risk Faktörleri")
            for risk in insights['risk_faktörleri']:
                st.error(f"⚠ {risk}")

        # Müşteri davranış dağılımı
        st.markdown("### 👥 Müşteri Tipleri")
        if analysis['behavior_distribution']:
            behavior_df = pd.DataFrame.from_dict(
                analysis['behavior_distribution'],
                orient='index',
                columns=['Sayı']
            ).reset_index()
            behavior_df.columns = ['Tip', 'Sayı']

            fig = px.pie(behavior_df, values='Sayı', names='Tip',
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)

    # Duygu dağılımı
    st.markdown("### 😊 Duygu Dağılımı")
    sentiment_data = analysis['sentiment_distribution']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("😊 Pozitif", f"%{sentiment_data['pozitif']:.1f}")
    with col2:
        st.metric("😐 Nötr", f"%{sentiment_data['nötr']:.1f}")
    with col3:
        st.metric("😞 Negatif", f"%{sentiment_data['negatif']:.1f}")

    # Artı ve eksiler
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ En Çok Belirtilen Artılar")
        for pro, count in analysis['top_pros'][:5]:
            st.write(f"• **{pro}** ({count} kez)")

    with col2:
        st.markdown("### ❌ En Çok Belirtilen Eksiler")
        for con, count in analysis['top_cons'][:5]:
            st.write(f"• **{con}** ({count} kez)")

    # Genel tavsiye
    st.markdown("### 📌 Genel Değerlendirme")
    st.markdown(f"<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; font-size: 18px;'>{insights['tavsiye']}</div>", unsafe_allow_html=True)

    # Örnek yorumlar
    with st.expander("📝 Örnek Yorumlar"):
        # En pozitif 3 yorum
        st.markdown("**😊 En Olumlu Yorumlar:**")
        positive_reviews = sorted(reviews, key=lambda x: x.sentiment_score or 0, reverse=True)[:3]
        for r in positive_reviews:
            st.success(f"⭐ {r.rating} - {r.reviewer_name}: {r.review_text[:200]}...")

        # En negatif 3 yorum
        st.markdown("**😞 En Olumsuz Yorumlar:**")
        negative_reviews = sorted(reviews, key=lambda x: x.sentiment_score or 0)[:3]
        for r in negative_reviews:
            st.error(f"⭐ {r.rating} - {r.reviewer_name}: {r.review_text[:200]}...")


def show_category_review_analysis(session, category, site):
    """Kategori bazlı toplu yorum analizi"""
    st.markdown("### 📊 Kategori Bazlı Yorum Analizi")

    # Kategorideki ürünleri al
    query = session.query(Product)
    if category != "Tüm Kategoriler":
        query = query.filter(Product.category == category)
    if site != "Tüm Siteler":
        query = query.filter(Product.site_name == site.lower())

    products = query.all()

    if not products:
        st.warning("Bu kategoride ürün bulunamadı.")
        return

    # Her ürün için yorum sayılarını al
    product_reviews = []
    for product in products:
        review_count = session.query(ProductReview).filter_by(product_id=product.id).count()
        if review_count > 0:
            avg_sentiment = session.query(func.avg(ProductReview.sentiment_score)).filter_by(
                product_id=product.id
            ).scalar() or 0

            product_reviews.append({
                'name': product.name[:40] + '...',
                'brand': product.brand,
                'review_count': review_count,
                'avg_sentiment': avg_sentiment,
                'rating': product.rating
            })

    if product_reviews:
        df = pd.DataFrame(product_reviews)

        # Yorum sayısına göre sırala
        df = df.sort_values('review_count', ascending=False)

        # Grafik
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['name'],
            y=df['review_count'],
            name='Yorum Sayısı',
            marker_color='lightblue'
        ))

        fig.add_trace(go.Scatter(
            x=df['name'],
            y=df['avg_sentiment'],
            name='Duygu Skoru',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='red', width=2)
        ))

        fig.update_layout(
            title=f"{category} Kategorisi Yorum Analizi",
            xaxis_title="Ürünler",
            yaxis_title="Yorum Sayısı",
            yaxis2=dict(
                title='Duygu Skoru',
                overlaying='y',
                side='right',
                range=[-1, 1]
            ),
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

        # Özet tablo
        st.dataframe(df.sort_values('avg_sentiment', ascending=False))

    else:
        st.info("Bu kategoride henüz yorum analizi yapılmamış.")


def show_best_sellers_review_analysis(session, category, top_n):
    """En çok satanların yorum analizi karşılaştırması"""
    from turkish_review_ai import TurkishReviewAI

    st.markdown("### 🏆 En Çok Satanlar Yorum Karşılaştırması")

    # En çok satanları getir
    from datetime import timedelta
    start_date = datetime.now() - timedelta(days=7)

    query = session.query(
        Product,
        func.min(RankingHistory.rank_position).label('best_rank')
    ).join(
        RankingHistory
    ).filter(
        RankingHistory.timestamp >= start_date
    )

    if category != "Tüm Kategoriler":
        query = query.filter(Product.category == category)

    best_sellers = query.group_by(Product.id).order_by('best_rank').limit(top_n).all()

    if not best_sellers:
        st.warning("En çok satan ürün bulunamadı.")
        return

    # Her ürün için analiz sonuçlarını topla
    comparison_data = []

    for product, best_rank in best_sellers:
        reviews = session.query(ProductReview).filter_by(product_id=product.id).all()

        if reviews:
            ai = TurkishReviewAI()
            reviews_data = [{
                'text': r.review_text,
                'rating': r.rating,
                'verified': r.reviewer_verified,
                'helpful_count': r.helpful_count
            } for r in reviews]

            analysis = ai.analyze_bulk_reviews(reviews_data)

            comparison_data.append({
                'name': product.name[:30] + '...',
                'rank': int(best_rank),
                'review_count': len(reviews),
                'avg_sentiment': analysis['average_sentiment'],
                'recommendation_score': analysis['recommendation_score'],
                'verified_pct': analysis['verified_percentage'],
                'top_reason': analysis['top_purchase_reasons'][0][0] if analysis['top_purchase_reasons'] else 'Belirsiz'
            })

    if comparison_data:
        df = pd.DataFrame(comparison_data)

        # Karşılaştırma grafiği
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Tavsiye Skoru', 'Duygu Skoru',
                          'Yorum Sayısı', 'Ana Satın Alma Nedeni')
        )

        # Tavsiye skoru
        fig.add_trace(
            go.Bar(x=df['name'], y=df['recommendation_score'],
                  marker_color='green'),
            row=1, col=1
        )

        # Duygu skoru
        fig.add_trace(
            go.Bar(x=df['name'], y=df['avg_sentiment'],
                  marker_color='blue'),
            row=1, col=2
        )

        # Yorum sayısı
        fig.add_trace(
            go.Bar(x=df['name'], y=df['review_count'],
                  marker_color='orange'),
            row=2, col=1
        )

        # Ana neden dağılımı
        reason_counts = df['top_reason'].value_counts()
        fig.add_trace(
            go.Pie(labels=reason_counts.index, values=reason_counts.values),
            row=2, col=2
        )

        fig.update_layout(height=700, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        # Detaylı tablo
        st.markdown("### 📊 Detaylı Karşılaştırma")
        styled_df = df.style.background_gradient(subset=['recommendation_score', 'avg_sentiment'])
        st.dataframe(styled_df)

        # En iyi performans gösteren
        best_performer = df.loc[df['recommendation_score'].idxmax()]
        st.success(f"🏆 **En İyi Performans:** {best_performer['name']} - Tavsiye Skoru: {best_performer['recommendation_score']:.1f}/100")

    else:
        st.info("Yorum verisi bulunamadı. Önce yorumları çekmeniz gerekiyor.")


if __name__ == "__main__":
    st.set_page_config(page_title="Detaylı Analiz", layout="wide")
    show_detailed_analytics()