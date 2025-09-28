"""
Admin Panel - Site ve URL Yönetimi
"""

import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from database import SessionLocal, SiteConfig, SiteUrl

def get_db_session():
    return SessionLocal()
from base_scraper import BaseScraper
import json
import time

def show_admin_panel():
    """Admin paneli ana fonksiyonu"""
    st.header("🛠️ Admin Panel - Site Yönetimi")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Site Ekle/Düzenle", "🔗 URL Yönetimi", "🔍 Otomatik Keşif", "🧪 URL Test", "📊 Site Listesi"])

    with tab1:
        show_site_management()

    with tab2:
        show_url_management()

    with tab3:
        show_auto_discovery()

    with tab4:
        show_url_tester()

    with tab5:
        show_site_list()


def show_site_management():
    """Site ekleme/düzenleme formu"""
    st.subheader("📝 Site Ekle/Düzenle")

    session = get_db_session()

    # Mevcut siteleri listele
    sites = session.query(SiteConfig).all()
    site_options = ["Yeni Site Ekle"] + [f"{s.site_name} ({s.site_key})" for s in sites]

    selected_site = st.selectbox("Site Seçin", site_options, key="site_manage_select")

    # Form değişkenleri
    if selected_site == "Yeni Site Ekle":
        site_data = {
            'site_key': '',
            'site_name': '',
            'base_url': '',
            'scraper_type': 'generic',
            'use_selenium': False,
            'rate_limit': 2.0,
            'headers': {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            'proxy_url': '',
            'is_active': True
        }
    else:
        # Mevcut site verilerini yükle
        site_key = selected_site.split('(')[1].split(')')[0]
        site = session.query(SiteConfig).filter_by(site_key=site_key).first()
        site_data = site.to_dict() if site else {}

    # Form
    with st.form("site_form"):
        col1, col2 = st.columns(2)

        with col1:
            site_key = st.text_input("Site Kodu (Kısa İsim)*",
                                     value=site_data.get('site_key', ''),
                                     placeholder="trendyol, hepsiburada",
                                     help="Sistem içinde kullanılacak benzersiz kod")

            site_name = st.text_input("Site Adı*",
                                      value=site_data.get('site_name', ''),
                                      placeholder="Trendyol")

            base_url = st.text_input("Ana URL*",
                                     value=site_data.get('base_url', ''),
                                     placeholder="https://www.trendyol.com")

            scraper_type = st.selectbox("Scraper Tipi",
                                       options=['generic', 'trendyol', 'hepsiburada', 'n11', 'amazon'],
                                       index=['generic', 'trendyol', 'hepsiburada', 'n11', 'amazon'].index(
                                           site_data.get('scraper_type', 'generic')))

        with col2:
            use_selenium = st.checkbox("Selenium Kullan",
                                      value=site_data.get('use_selenium', False),
                                      help="JavaScript render gerektiren siteler için")

            rate_limit = st.number_input("Rate Limit (saniye)",
                                        min_value=0.5, max_value=10.0,
                                        value=float(site_data.get('rate_limit', 2.0)),
                                        step=0.5)

            proxy_url = st.text_input("Proxy URL (Opsiyonel)",
                                     value=site_data.get('proxy_url', ''),
                                     placeholder="http://proxy:port")

            is_active = st.checkbox("Aktif", value=site_data.get('is_active', True))

        # Headers
        st.subheader("Headers")
        headers_text = st.text_area("Headers (JSON formatında)",
                                   value=json.dumps(site_data.get('headers', {}), indent=2),
                                   height=150)

        # Submit button
        submitted = st.form_submit_button("💾 Kaydet", type="primary")

        if submitted:
            if not site_key or not site_name or not base_url:
                st.error("Zorunlu alanları doldurun!")
            else:
                try:
                    headers = json.loads(headers_text)

                    if selected_site == "Yeni Site Ekle":
                        # Site key'in benzersiz olduğunu kontrol et
                        existing_site = session.query(SiteConfig).filter_by(site_key=site_key).first()
                        if existing_site:
                            st.error(f"❌ '{site_key}' site anahtarı zaten kullanımda! Lütfen farklı bir anahtar seçin.")
                            return

                        # Yeni site ekle
                        new_site = SiteConfig(
                            site_key=site_key,
                            site_name=site_name,
                            base_url=base_url,
                            scraper_type=scraper_type,
                            use_selenium=use_selenium,
                            rate_limit=rate_limit,
                            headers=headers,
                            proxy_url=proxy_url if proxy_url else None,
                            is_active=is_active
                        )
                        session.add(new_site)
                    else:
                        # Mevcut siteyi güncelle
                        site = session.query(SiteConfig).filter_by(site_key=site_data['site_key']).first()
                        if site:
                            site.site_key = site_key
                            site.site_name = site_name
                            site.base_url = base_url
                            site.scraper_type = scraper_type
                            site.use_selenium = use_selenium
                            site.rate_limit = rate_limit
                            site.headers = headers
                            site.proxy_url = proxy_url if proxy_url else None
                            site.is_active = is_active
                            site.updated_at = datetime.utcnow()

                    session.commit()
                    st.success(f"✅ {site_name} başarıyla kaydedildi!")
                    st.rerun()

                except json.JSONDecodeError:
                    st.error("Headers JSON formatı hatalı!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Hata: {str(e)}")


def show_url_management():
    """URL ekleme/düzenleme"""
    st.subheader("🔗 URL Yönetimi")

    session = get_db_session()

    # Site seçimi
    sites = session.query(SiteConfig).filter_by(is_active=True).all()
    if not sites:
        st.warning("Önce site ekleyin!")
        return

    site_options = {s.site_name: s.id for s in sites}
    selected_site_name = st.selectbox("Site Seçin", list(site_options.keys()), key="url_manage_site_select")
    selected_site_id = site_options[selected_site_name]

    # Mevcut URL'leri göster
    urls = session.query(SiteUrl).filter_by(site_id=selected_site_id).order_by(SiteUrl.priority).all()

    if urls:
        st.write("**Mevcut URL'ler:**")
        for url in urls:
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            with col1:
                st.text(url.url_path[:50] + "..." if len(url.url_path) > 50 else url.url_path)
            with col2:
                st.text(f"{url.url_type} - {url.category or 'Genel'}")
            with col3:
                st.text("✅ Aktif" if url.is_active else "❌ Pasif")
            with col4:
                if st.button("🗑️", key=f"delete_url_{url.id}"):
                    session.delete(url)
                    session.commit()
                    st.rerun()

    st.markdown("---")

    # Yeni URL ekleme formu
    st.write("**Yeni URL Ekle:**")
    with st.form("url_form"):
        col1, col2 = st.columns(2)

        with col1:
            url_type = st.selectbox("URL Tipi",
                                   options=['best_sellers', 'category', 'search', 'deals', 'new_products'])

            url_path = st.text_input("URL*",
                                    placeholder="/en-cok-satanlar veya tam URL")

            category = st.text_input("Kategori",
                                    placeholder="elektronik, giyim vs.")

            max_pages = st.number_input("Max Sayfa", min_value=1, max_value=100, value=1)

        with col2:
            description = st.text_input("Açıklama",
                                      placeholder="En çok satan elektronik ürünler")

            priority = st.number_input("Öncelik", min_value=1, max_value=10, value=1,
                                     help="Düşük sayı = yüksek öncelik")

            max_products = st.number_input("Max Ürün", min_value=10, max_value=1000, value=100)

            is_active = st.checkbox("Aktif", value=True)

        # Özel selector'lar (opsiyonel)
        show_selectors = st.checkbox("Özel Selector Ekle")
        selectors = {}

        if show_selectors:
            st.write("CSS Selector'lar (Opsiyonel):")
            selectors['product_container'] = st.text_input("Ürün Container",
                                                          placeholder="div.product-card")
            selectors['title'] = st.text_input("Başlık",
                                              placeholder="h3.product-title")
            selectors['price'] = st.text_input("Fiyat",
                                              placeholder="span.price")

        submitted = st.form_submit_button("➕ URL Ekle", type="primary")

        if submitted:
            if not url_path:
                st.error("URL zorunludur!")
            else:
                try:
                    new_url = SiteUrl(
                        site_id=selected_site_id,
                        url_type=url_type,
                        url_path=url_path,
                        category=category if category else None,
                        description=description if description else None,
                        is_active=is_active,
                        priority=priority,
                        max_pages=max_pages,
                        max_products=max_products,
                        selectors=selectors if selectors else {}
                    )
                    session.add(new_url)
                    session.commit()
                    st.success(f"✅ URL başarıyla eklendi!")
                    st.rerun()

                except Exception as e:
                    session.rollback()
                    st.error(f"Hata: {str(e)}")


def show_auto_discovery():
    """Otomatik kategori keşfi"""
    st.subheader("🔍 Otomatik Kategori Keşfi")
    st.write("Site URL'si girin, sistem otomatik olarak tüm kategorileri ve en çok satanları bulacak!")

    session = get_db_session()

    # Site seçimi veya URL girişi
    col1, col2 = st.columns([1, 2])

    with col1:
        discovery_mode = st.radio(
            "Keşif Modu",
            ["Mevcut Site", "Yeni URL"],
            key="discovery_mode"
        )

    with col2:
        if discovery_mode == "Mevcut Site":
            # Mevcut sitelerden seç
            sites = session.query(SiteConfig).filter_by(is_active=True).all()
            if not sites:
                st.warning("Önce site ekleyin!")
                return

            site_options = {s.site_name: s for s in sites}
            selected_site_name = st.selectbox(
                "Site Seçin",
                list(site_options.keys()),
                key="discovery_site_select"
            )
            selected_site = site_options[selected_site_name]
            discovery_url = selected_site.base_url
            site_id = selected_site.id
        else:
            # Manuel URL gir
            discovery_url = st.text_input(
                "Site URL'si",
                placeholder="https://www.example.com",
                key="discovery_url_input"
            )
            site_id = None

    # Gelişmiş ayarlar
    with st.expander("⚙️ Gelişmiş Ayarlar"):
        use_selenium = st.checkbox("Selenium Kullan (JavaScript siteleri için)", value=False)
        max_categories = st.number_input("Max Kategori Sayısı", min_value=5, max_value=100, value=20)
        spider_depth = st.number_input("Örümcek Derinliği", min_value=1, max_value=3, value=1,
                                      help="1: Sadece ana sayfa, 2: Ana sayfa + 1 seviye, 3: Derin tarama")
        st.session_state['spider_depth'] = spider_depth
        auto_save = st.checkbox("Otomatik Veritabanına Kaydet", value=True)

    # Keşif butonu
    if st.button("🚀 Keşfi Başlat", type="primary", key="start_discovery"):
        if not discovery_url:
            st.error("Lütfen bir URL girin!")
            return

        with st.spinner("🔍 Kategoriler keşfediliyor... Bu birkaç dakika sürebilir."):
            try:
                # Site'ye özel spider seç
                domain = urlparse(discovery_url).netloc.lower()

                if 'trendyol' in domain:
                    # Trendyol için özel spider
                    from trendyol_spider import TrendyolSpider
                    spider = TrendyolSpider()
                    st.info(f"🕷️ Trendyol özel örümceği kategorileri buluyor...")
                    result = spider.discover_all_categories()
                else:
                    # Diğer siteler için deep spider
                    from deep_category_spider import DeepCategorySpider
                    spider = DeepCategorySpider(max_depth=spider_depth)
                    st.info(f"🕷️ Örümcek {discovery_url} sitesinin TÜM kategorilerini {spider_depth} seviye derinlikte buluyor...")
                    result = spider.discover_all_categories_deep(discovery_url)

                if result['total'] > 0:
                    st.success(f"✅ {result['total']} kategori bulundu!")

                    # Sonuçları göster
                    st.write("### 📊 Bulunan Kategoriler:")

                    # Kategorileri seviyelerine göre göster
                    categories = result['categories']

                    # HTML tablo oluştur - tıklanabilir linklerle
                    html_content = """
                    <style>
                        .category-table {
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                        }
                        .category-table th {
                            background-color: #f0f2f6;
                            padding: 12px;
                            text-align: left;
                            border-bottom: 2px solid #ddd;
                        }
                        .category-table td {
                            padding: 10px 12px;
                            border-bottom: 1px solid #eee;
                        }
                        .category-table tr:hover {
                            background-color: #f8f9fa;
                        }
                        .category-link {
                            color: #0066cc;
                            text-decoration: none;
                        }
                        .category-link:hover {
                            text-decoration: underline;
                            color: #0052a3;
                        }
                        .level-0 { padding-left: 12px; font-weight: bold; }
                        .level-1 { padding-left: 32px; }
                        .level-2 { padding-left: 52px; }
                        .level-3 { padding-left: 72px; }
                        .category-url {
                            font-size: 12px;
                            color: #666;
                            word-break: break-all;
                        }
                        .copy-btn {
                            background: #e0e0e0;
                            border: none;
                            padding: 2px 8px;
                            border-radius: 3px;
                            cursor: pointer;
                            font-size: 11px;
                        }
                        .copy-btn:hover {
                            background: #d0d0d0;
                        }
                    </style>
                    <table class="category-table">
                        <thead>
                            <tr>
                                <th style="width: 40px;">#</th>
                                <th>Kategori Adı</th>
                                <th>URL</th>
                                <th style="width: 80px;">Seviye</th>
                            </tr>
                        </thead>
                        <tbody>
                    """

                    # Kategorileri göster
                    for i, cat in enumerate(categories[:max_categories], 1):
                        level = cat.get('level', cat.get('depth', 0))
                        name = cat.get('name', 'İsimsiz')
                        url = cat.get('url', '#')
                        best_url = cat.get('best_sellers_url', url)

                        # Seviyeye göre girintili göster
                        indent_class = f"level-{level}"

                        html_content += f"""
                        <tr>
                            <td>{i}</td>
                            <td class="{indent_class}">
                                {'&nbsp;&nbsp;&nbsp;&nbsp;' * level}{'└─ ' if level > 0 else ''}{name}
                            </td>
                            <td class="category-url">
                                <a href="{best_url}" target="_blank" class="category-link"
                                   title="En çok satanları görüntüle">
                                    {best_url[:80]}{'...' if len(best_url) > 80 else ''}
                                </a>
                            </td>
                            <td style="text-align: center;">{level}</td>
                        </tr>
                        """

                    html_content += """
                        </tbody>
                    </table>
                    """

                    if len(categories) > max_categories:
                        html_content += f"""
                        <div style="text-align: center; margin-top: 10px; color: #666;">
                            ... ve {len(categories) - max_categories} kategori daha
                        </div>
                        """

                    # HTML'i göster
                    st.markdown(html_content, unsafe_allow_html=True)

                    # İstatistikler
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Toplam Kategori", result['total'])
                    with col2:
                        st.metric("Site", result.get('site', 'Bilinmiyor'))
                    with col3:
                        st.metric("Keşif Tipi", "Otomatik")

                    # Veritabanına kaydet
                    if auto_save and site_id:
                        if st.button("💾 Veritabanına Kaydet", key="save_discovered"):
                            with st.spinner("Kaydediliyor..."):
                                added = spider.save_categories(site_id, result['categories'])
                                if added > 0:
                                    st.success(f"✅ {added} yeni kategori veritabanına eklendi!")
                                    st.rerun()
                                else:
                                    st.info("Tüm kategoriler zaten mevcut.")

                        # JSON olarak indir
                        json_str = json.dumps(result, ensure_ascii=False, indent=2)
                        st.download_button(
                            label="📥 JSON Olarak İndir",
                            data=json_str,
                            file_name=f"{result['site']}_categories.json",
                            mime="application/json"
                        )

                    else:
                        st.warning("DataFrame boş!")

                else:
                    st.warning("😔 Kategori bulunamadı. Site yapısı farklı olabilir.")

            except ImportError:
                st.error("❌ auto_category_discovery modülü bulunamadı!")
            except Exception as e:
                st.error(f"❌ Keşif hatası: {str(e)}")

    # Mevcut kategorileri göster
    if discovery_mode == "Mevcut Site" and site_id:
        st.markdown("---")
        st.write("### 📋 Mevcut Kategoriler:")

        existing_urls = session.query(SiteUrl).filter_by(
            site_id=site_id,
            url_type='best_sellers'
        ).order_by(SiteUrl.priority).all()

        if existing_urls:
            st.write(f"**{len(existing_urls)}** kategori mevcut:")
            for url in existing_urls[:10]:
                st.text(f"• {url.category or 'Genel'}: {url.description or url.url_path[:50]}")

            if len(existing_urls) > 10:
                st.text(f"... ve {len(existing_urls) - 10} kategori daha")
        else:
            st.info("Bu site için henüz kategori eklenmemiş.")

def show_url_tester():
    """URL test aracı"""
    st.subheader("🧪 URL Test")

    session = get_db_session()

    # Site ve URL seçimi
    sites = session.query(SiteConfig).filter_by(is_active=True).all()
    if not sites:
        st.warning("Site bulunamadı!")
        return

    site_options = {s.site_name: s for s in sites}
    selected_site_name = st.selectbox("Site Seçin", list(site_options.keys()), key="test_site_select")
    selected_site = site_options[selected_site_name]

    urls = session.query(SiteUrl).filter_by(
        site_id=selected_site.id,
        is_active=True
    ).all()

    if not urls:
        st.warning("Bu site için URL bulunamadı!")
        return

    url_options = [f"{u.url_type}: {u.url_path[:50]}..." for u in urls]
    selected_url_idx = st.selectbox("URL Seçin", range(len(urls)),
                                   format_func=lambda x: url_options[x])
    selected_url = urls[selected_url_idx]

    # Test butonu
    if st.button("🔍 URL'yi Test Et", type="primary"):
        with st.spinner("URL test ediliyor..."):
            test_url = selected_url.url_path
            if not test_url.startswith('http'):
                test_url = selected_site.base_url + test_url

            st.info(f"Test edilen URL: {test_url}")

            # Bağlantı testi
            try:
                start_time = time.time()
                headers = selected_site.headers if selected_site.headers else {}

                response = requests.get(test_url, headers=headers, timeout=10)
                elapsed_time = time.time() - start_time

                col1, col2, col3 = st.columns(3)

                with col1:
                    if response.status_code == 200:
                        st.success(f"✅ Status: {response.status_code}")
                    else:
                        st.warning(f"⚠️ Status: {response.status_code}")

                with col2:
                    st.metric("Yanıt Süresi", f"{elapsed_time:.2f} sn")

                with col3:
                    st.metric("İçerik Boyutu", f"{len(response.text) / 1024:.1f} KB")

                # HTML analizi
                if response.status_code == 200:
                    st.write("**HTML İçerik Analizi:**")

                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'lxml')

                    # Ürün kartlarını bul
                    possible_products = []

                    # Yaygın ürün selector'ları
                    common_selectors = [
                        'div[class*="product"]',
                        'div[class*="item"]',
                        'article[class*="product"]',
                        'div[data-testid*="product"]',
                        'div[class*="card"]'
                    ]

                    for selector in common_selectors:
                        elements = soup.select(selector)
                        if elements:
                            possible_products.append((selector, len(elements)))

                    if possible_products:
                        st.write("**Bulunan Muhtemel Ürün Elementleri:**")
                        for selector, count in possible_products:
                            st.write(f"• `{selector}`: {count} adet")

                    # İlk ürünün detaylarını göster
                    if possible_products:
                        best_selector = possible_products[0][0]
                        first_product = soup.select_one(best_selector)

                        if first_product:
                            st.write("**İlk Ürün HTML Örneği:**")
                            # HTML'i güzelleştir ve göster
                            pretty_html = first_product.prettify()[:1000]
                            st.code(pretty_html, language='html')

                            # Fiyat ve başlık tahminleri
                            st.write("**Tespit Edilen Bilgiler:**")

                            # Başlık ara
                            title_tags = first_product.find_all(['h1', 'h2', 'h3', 'h4', 'span', 'div'])
                            for tag in title_tags[:5]:
                                text = tag.get_text(strip=True)
                                if len(text) > 10 and len(text) < 200:
                                    st.write(f"Muhtemel başlık: `{text[:100]}`")
                                    break

                            # Fiyat ara
                            price_pattern = r'[\d.,]+\s*(TL|₺|TRY)'
                            import re
                            prices = re.findall(price_pattern, first_product.get_text())
                            if prices:
                                st.write(f"Muhtemel fiyat: `{prices[0]}`")

            except requests.RequestException as e:
                st.error(f"❌ Bağlantı hatası: {str(e)}")
            except Exception as e:
                st.error(f"❌ Test hatası: {str(e)}")


def show_site_list():
    """Tüm siteleri listele"""
    st.subheader("📊 Site Listesi")

    session = get_db_session()

    sites = session.query(SiteConfig).all()

    if not sites:
        st.info("Henüz site eklenmemiş")
        return

    # Site tablosu
    site_data = []
    for site in sites:
        url_count = session.query(SiteUrl).filter_by(site_id=site.id).count()
        active_url_count = session.query(SiteUrl).filter_by(
            site_id=site.id,
            is_active=True
        ).count()

        site_data.append({
            'Site': site.site_name,
            'Kod': site.site_key,
            'URL': site.base_url,
            'Scraper': site.scraper_type,
            'Selenium': '✅' if site.use_selenium else '❌',
            'URL Sayısı': f"{active_url_count}/{url_count}",
            'Durum': '✅ Aktif' if site.is_active else '❌ Pasif',
            'Rate Limit': f"{site.rate_limit}s"
        })

    df = pd.DataFrame(site_data)
    st.dataframe(df, use_container_width=True)

    # Site silme
    st.markdown("---")
    st.write("**Site Sil:**")

    col1, col2 = st.columns([3, 1])
    with col1:
        site_to_delete = st.selectbox("Silinecek Site",
                                     ["Seçin"] + [s.site_name for s in sites])
    with col2:
        if st.button("🗑️ Siteyi Sil", type="secondary"):
            if site_to_delete != "Seçin":
                site = session.query(SiteConfig).filter_by(site_name=site_to_delete).first()
                if site:
                    session.delete(site)
                    session.commit()
                    st.success(f"✅ {site_to_delete} silindi!")
                    st.rerun()


if __name__ == "__main__":
    # Test için
    st.set_page_config(page_title="Market Spider Admin", page_icon="🛠️", layout="wide")
    show_admin_panel()