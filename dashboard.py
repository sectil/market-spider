"""
Market Spider Dashboard - Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import sys
import os

# Database imports
from database import get_engine, Product, PriceHistory, RankingHistory, ScrapeLog
from config import DASHBOARD

# Sayfa ayarları
st.set_page_config(
    page_title="Market Spider Dashboard",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS stil
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem;
    }
    .price-up {
        color: #ff4444;
    }
    .price-down {
        color: #00c851;
    }
</style>
""", unsafe_allow_html=True)

# Database bağlantısı
from database import SessionLocal

@st.cache_resource
def get_db_session():
    return SessionLocal()

# Veri yükleme fonksiyonları
@st.cache_data(ttl=300)  # 5 dakika cache
def load_products():
    session = get_db_session()
    products = session.query(Product).all()
    return pd.DataFrame([p.to_dict() for p in products])

@st.cache_data(ttl=300)
def load_price_history(product_id=None, days=30):
    session = get_db_session()
    query = session.query(PriceHistory)

    if product_id:
        query = query.filter(PriceHistory.product_id == product_id)

    since_date = datetime.now() - timedelta(days=days)
    query = query.filter(PriceHistory.timestamp >= since_date)

    prices = query.all()
    return pd.DataFrame([p.to_dict() for p in prices])

@st.cache_data(ttl=300)
def load_rankings(days=7):
    session = get_db_session()
    since_date = datetime.now() - timedelta(days=days)
    rankings = session.query(RankingHistory).filter(
        RankingHistory.timestamp >= since_date
    ).all()
    return pd.DataFrame([r.to_dict() for r in rankings])

@st.cache_data(ttl=300)
def get_statistics():
    session = get_db_session()

    stats = {
        'total_products': session.query(Product).count(),
        'total_sites': session.query(Product.site_name).distinct().count(),
        'total_prices': session.query(PriceHistory).count(),
        'last_24h_updates': session.query(PriceHistory).filter(
            PriceHistory.timestamp >= datetime.now() - timedelta(days=1)
        ).count()
    }

    # Son tarama
    last_scrape = session.query(ScrapeLog).order_by(
        ScrapeLog.timestamp.desc()
    ).first()

    if last_scrape:
        stats['last_scrape'] = last_scrape.timestamp
        stats['last_scrape_status'] = last_scrape.status

    return stats

def main():
    # Session state'te sayfa kontrolü
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "📊 Özet"

    # Başlık
    st.markdown('<h1 class="main-header">🕷️ Market Spider Dashboard</h1>',
                unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        # Logo yerine emoji ve başlık kullan
        st.markdown("# 🕷️ Market Spider")
        st.markdown("**E-Ticaret Veri Analizi**")
        st.markdown("---")

        # Radio button ile sayfa seçimi
        pages = ["📊 Özet", "📈 Fiyat Takibi", "🏆 En Çok Satanlar",
                 "🏪 Kategoriler", "🔍 Ürün Arama", "🛠️ Admin Panel", "⚙️ Ayarlar"]

        # Session state'ten mevcut sayfayı al
        current_index = pages.index(st.session_state.current_page) if st.session_state.current_page in pages else 0

        page = st.radio(
            "📍 Sayfa Seçimi",
            pages,
            index=current_index,
            key="page_selector"
        )

        # Sayfa değişimini session state'e kaydet
        st.session_state.current_page = page

        st.markdown("---")
        st.markdown("### 🔄 Otomatik Yenileme")
        auto_refresh = st.checkbox("Aktif", value=False)
        if auto_refresh:
            st.info(f"Her {DASHBOARD['refresh_interval']} saniyede yenileniyor")

    # Ana içerik - session state'ten sayfa seç
    page = st.session_state.current_page

    if page == "📊 Özet":
        show_overview_page()
    elif page == "📈 Fiyat Takibi":
        show_price_tracking_page()
    elif page == "🏆 En Çok Satanlar":
        show_best_sellers_page()
    elif page == "🏪 Kategoriler":
        from category_view import display_category_view
        display_category_view()
    elif page == "🔍 Ürün Arama":
        show_product_search_page()
    elif page == "🛠️ Admin Panel":
        from admin_panel import show_admin_panel
        show_admin_panel()
    elif page == "⚙️ Ayarlar":
        show_settings_page()

def show_overview_page():
    """Özet sayfası"""
    st.header("📊 Genel Özet")

    # İstatistikler
    stats = get_statistics()

    # Tıklanabilir metrik kartlar için CSS
    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 10px;
            color: white;
            cursor: pointer;
            transition: transform 0.2s;
            text-align: center;
            margin: 10px 0;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }
        .metric-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .metric-delta {
            font-size: 12px;
            opacity: 0.8;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        container = st.container()
        with container:
            st.markdown(
                f"""<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px; border-radius: 10px; text-align: center; cursor: pointer;'
                onclick="window.location.hash='product'">
                <div style='color: white; font-size: 24px;'>📦</div>
                <div style='color: white; font-size: 28px; font-weight: bold;'>{stats['total_products']:,}</div>
                <div style='color: white; font-size: 14px;'>Toplam Ürün</div>
                <div style='color: white; font-size: 12px; opacity: 0.8;'>Aktif</div>
                </div>""",
                unsafe_allow_html=True
            )
        if st.button("Ürün Arama →", key="go_product", use_container_width=True):
            st.session_state.current_page = "🔍 Ürün Arama"
            st.rerun()

    with col2:
        container = st.container()
        with container:
            st.markdown(
                f"""<div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 20px; border-radius: 10px; text-align: center; cursor: pointer;'>
                <div style='color: white; font-size: 24px;'>🏪</div>
                <div style='color: white; font-size: 28px; font-weight: bold;'>{stats['total_sites']}</div>
                <div style='color: white; font-size: 14px;'>Takip Edilen Site</div>
                <div style='color: white; font-size: 12px; opacity: 0.8;'>{stats['total_sites']} site</div>
                </div>""",
                unsafe_allow_html=True
            )
        if st.button("Admin Panel →", key="go_admin", use_container_width=True):
            st.session_state.current_page = "🛠️ Admin Panel"
            st.rerun()

    with col3:
        container = st.container()
        with container:
            st.markdown(
                f"""<div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                padding: 20px; border-radius: 10px; text-align: center; cursor: pointer;'>
                <div style='color: white; font-size: 24px;'>💰</div>
                <div style='color: white; font-size: 28px; font-weight: bold;'>{stats['total_prices']:,}</div>
                <div style='color: white; font-size: 14px;'>Toplam Fiyat Kaydı</div>
                <div style='color: white; font-size: 12px; opacity: 0.8;'>+{stats['last_24h_updates']} (24 saat)</div>
                </div>""",
                unsafe_allow_html=True
            )
        if st.button("Fiyat Takibi →", key="go_price", use_container_width=True):
            st.session_state.current_page = "📈 Fiyat Takibi"
            st.rerun()

    with col4:
        container = st.container()
        with container:
            if 'last_scrape' in stats:
                time_diff = datetime.now() - stats['last_scrape']
                hours_ago = time_diff.total_seconds() / 3600
                last_update_text = f"{hours_ago:.1f} saat önce"
                delta_text = stats['last_scrape_status']
            else:
                last_update_text = "Henüz yok"
                delta_text = "Bekliyor"

            st.markdown(
                f"""<div style='background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                padding: 20px; border-radius: 10px; text-align: center; cursor: pointer;'>
                <div style='color: white; font-size: 24px;'>📊</div>
                <div style='color: white; font-size: 28px; font-weight: bold;'>{last_update_text}</div>
                <div style='color: white; font-size: 14px;'>Son Güncelleme</div>
                <div style='color: white; font-size: 12px; opacity: 0.8;'>{delta_text}</div>
                </div>""",
                unsafe_allow_html=True
            )
        if st.button("En Çok Satanlar →", key="go_ranking", use_container_width=True):
            st.session_state.current_page = "🏆 En Çok Satanlar"
            st.rerun()


    st.markdown("---")

    # Grafikler
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 Kategori Dağılımı")
        products_df = load_products()
        if not products_df.empty:
            category_counts = products_df['category'].value_counts()
            fig = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title="Ürün Kategorileri"
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🏪 Site Bazında Ürün Sayısı")
        if not products_df.empty:
            site_counts = products_df['site_name'].value_counts()
            fig = px.bar(
                x=site_counts.values,
                y=site_counts.index,
                orientation='h',
                title="Site Bazında Ürün Dağılımı"
            )
            st.plotly_chart(fig, use_container_width=True)

    # Son Güncellenen Ürünler
    st.subheader("🔄 Son Güncellenen Ürünler")

    price_history_df = load_price_history(days=1)
    if not price_history_df.empty:
        # timestamp'i datetime'a çevir
        price_history_df['timestamp'] = pd.to_datetime(price_history_df['timestamp'])
        # Son 10 güncelleme
        recent_prices = price_history_df.nlargest(10, 'timestamp')

        # Product bilgilerini ekle
        products_df = load_products()
        recent_products = recent_prices.merge(
            products_df[['id', 'name', 'site_name', 'image_url']],
            left_on='product_id',
            right_on='id',
            how='left'
        )

        for _, row in recent_products.iterrows():
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                if row.get('image_url'):
                    st.image(row['image_url'], width=80)

            with col2:
                st.write(f"**{row.get('name', 'Ürün')}**")
                st.caption(f"{row.get('site_name', '')}")

            with col3:
                price_change = ""
                if row.get('original_price') and row.get('price'):
                    discount = ((row['original_price'] - row['price']) /
                               row['original_price'] * 100)
                    if discount > 0:
                        price_change = f"🔻 %{discount:.0f} indirim"

                st.write(f"💰 **{row.get('price', 0):.2f} TL** {price_change}")
                st.caption(f"{row.get('timestamp', '')}")

def show_price_tracking_page():
    """Fiyat takip sayfası"""
    st.header("📈 Fiyat Takibi")

    products_df = load_products()

    if products_df.empty:
        st.warning("Henüz ürün verisi yok")
        return

    # Ürün seçimi
    selected_product_name = st.selectbox(
        "Ürün Seçin",
        products_df['name'].unique()
    )

    selected_product = products_df[products_df['name'] == selected_product_name].iloc[0]

    # Ürün detayları
    col1, col2 = st.columns([1, 3])

    with col1:
        if selected_product.get('image_url'):
            st.image(selected_product['image_url'], width=200)

    with col2:
        st.subheader(selected_product['name'])
        st.write(f"**Marka:** {selected_product.get('brand', 'Belirtilmemiş')}")
        st.write(f"**Kategori:** {selected_product.get('category', 'Diğer')}")
        st.write(f"**Site:** {selected_product['site_name']}")
        if selected_product.get('product_url'):
            st.markdown(f"[🔗 Ürüne Git]({selected_product['product_url']})")

    st.markdown("---")

    # Fiyat geçmişi
    days = st.slider("Kaç günlük veri?", 1, 90, 30)
    price_history = load_price_history(selected_product['id'], days)

    if not price_history.empty:
        # Fiyat grafiği
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=price_history['timestamp'],
            y=price_history['price'],
            mode='lines+markers',
            name='Fiyat',
            line=dict(color='#667eea', width=2)
        ))

        if 'original_price' in price_history.columns:
            fig.add_trace(go.Scatter(
                x=price_history['timestamp'],
                y=price_history['original_price'],
                mode='lines',
                name='Liste Fiyatı',
                line=dict(color='#ff4444', width=1, dash='dash')
            ))

        fig.update_layout(
            title="Fiyat Değişimi",
            xaxis_title="Tarih",
            yaxis_title="Fiyat (TL)",
            hovermode='x unified'
        )

        st.plotly_chart(fig, use_container_width=True)

        # İstatistikler
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "En Düşük Fiyat",
                f"{price_history['price'].min():.2f} TL"
            )

        with col2:
            st.metric(
                "En Yüksek Fiyat",
                f"{price_history['price'].max():.2f} TL"
            )

        with col3:
            st.metric(
                "Ortalama Fiyat",
                f"{price_history['price'].mean():.2f} TL"
            )

        with col4:
            current_price = price_history.iloc[-1]['price']
            prev_price = price_history.iloc[-2]['price'] if len(price_history) > 1 else current_price
            change = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0

            st.metric(
                "Güncel Fiyat",
                f"{current_price:.2f} TL",
                delta=f"{change:+.1f}%"
            )

def show_best_sellers_page():
    """En çok satanlar sayfası - Detaylı analiz"""
    from analytics_page import show_detailed_analytics
    show_detailed_analytics()

def show_product_search_page():
    """Ürün arama sayfası"""
    st.header("🔍 Ürün Arama")

    # Arama kutusu
    search_term = st.text_input("Ürün adı, marka veya kategori girin", "")

    if search_term:
        products_df = load_products()

        # Arama
        mask = (
            products_df['name'].str.contains(search_term, case=False, na=False) |
            products_df['brand'].str.contains(search_term, case=False, na=False) |
            products_df['category'].str.contains(search_term, case=False, na=False)
        )

        results = products_df[mask]

        st.write(f"**{len(results)} sonuç bulundu**")

        # Sonuçları göster
        for _, product in results.iterrows():
            col1, col2, col3 = st.columns([1, 3, 2])

            with col1:
                if product.get('image_url'):
                    st.image(product['image_url'], width=100)

            with col2:
                st.write(f"**{product['name']}**")
                st.caption(f"{product.get('brand', '')} | {product['category']}")
                st.caption(f"Site: {product['site_name']}")

            with col3:
                # Son fiyatı al
                price_history = load_price_history(product['id'], 1)
                if not price_history.empty:
                    last_price = price_history.iloc[-1]
                    st.write(f"💰 **{last_price['price']:.2f} TL**")

                    if last_price.get('discount_percentage'):
                        st.write(f"🏷️ %{last_price['discount_percentage']:.0f} indirim")

                if product.get('product_url'):
                    st.markdown(f"[Ürüne Git →]({product['product_url']})")

            st.markdown("---")

def show_settings_page():
    """Ayarlar sayfası"""
    st.header("⚙️ Ayarlar")

    st.subheader("🔄 Veri Güncelleme")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Manuel Güncelleme Başlat", type="primary"):
            with st.spinner("Veriler güncelleniyor..."):
                # TODO: Scraping işlemini başlat
                st.success("Güncelleme başlatıldı!")

    with col2:
        st.info("Otomatik güncelleme her 6 saatte bir yapılmaktadır.")

    st.markdown("---")

    st.subheader("📊 Database İstatistikleri")

    stats = get_statistics()

    st.json({
        "Toplam Ürün": stats['total_products'],
        "Toplam Site": stats['total_sites'],
        "Toplam Fiyat Kaydı": stats['total_prices'],
        "Son 24 Saat Güncelleme": stats['last_24h_updates']
    })

    st.markdown("---")

    st.subheader("🗑️ Veri Temizleme")

    days_to_keep = st.number_input(
        "Kaç günlük veri saklanacak?",
        min_value=7,
        max_value=365,
        value=90
    )

    if st.button("🗑️ Eski Verileri Temizle", type="secondary"):
        # TODO: Eski verileri temizle
        st.warning(f"{days_to_keep} günden eski veriler silinecek!")


if __name__ == "__main__":
    main()