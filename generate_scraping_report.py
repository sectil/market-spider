#!/usr/bin/env python3
"""
📊 Scraping Raporu Oluşturma
HTML formatında detaylı rapor
"""

import sqlite3
import json
from datetime import datetime
import pandas as pd

def generate_html_report():
    """HTML formatında rapor oluştur"""
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    # İstatistikleri topla
    stats = {}

    # Toplam ürün sayısı
    cursor.execute("SELECT COUNT(*) FROM products")
    stats['total_products'] = cursor.fetchone()[0]

    # Gerçek URL'li ürünler
    cursor.execute("""
        SELECT COUNT(*) FROM products
        WHERE url LIKE '%trendyol.com%'
        AND url NOT LIKE '%example.com%'
    """)
    stats['real_products'] = cursor.fetchone()[0]

    # Toplam yorum sayısı
    cursor.execute("SELECT COUNT(*) FROM product_reviews")
    stats['total_reviews'] = cursor.fetchone()[0]

    # Gerçek yorumlar
    cursor.execute("""
        SELECT COUNT(*) FROM product_reviews
        WHERE scraped_at IS NOT NULL
    """)
    stats['real_reviews'] = cursor.fetchone()[0]

    # Kategori dağılımı
    cursor.execute("""
        SELECT c.name, COUNT(p.id) as count
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        GROUP BY c.name
        ORDER BY count DESC
        LIMIT 10
    """)
    categories = cursor.fetchall()

    # En popüler markalar
    cursor.execute("""
        SELECT brand, COUNT(*) as count
        FROM products
        WHERE brand IS NOT NULL AND brand != ''
        GROUP BY brand
        ORDER BY count DESC
        LIMIT 10
    """)
    brands = cursor.fetchall()

    # En yüksek puanlı ürünler
    cursor.execute("""
        SELECT name, brand, price, rating, review_count
        FROM products
        WHERE rating > 0
        ORDER BY rating DESC, review_count DESC
        LIMIT 10
    """)
    top_rated = cursor.fetchall()

    # Son eklenen ürünler
    cursor.execute("""
        SELECT name, brand, price, created_at
        FROM products
        ORDER BY created_at DESC
        LIMIT 10
    """)
    recent_products = cursor.fetchall()

    # HTML rapor oluştur
    html = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Trendyol Scraping Raporu - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                padding: 40px;
                color: white;
                text-align: center;
            }}
            h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                padding: 30px;
            }}
            .stat-card {{
                background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                transition: transform 0.3s;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #333;
            }}
            .stat-label {{
                font-size: 1em;
                color: #666;
                margin-top: 5px;
            }}
            .section {{
                padding: 30px;
            }}
            .section-title {{
                font-size: 1.8em;
                color: #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #f093fb;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }}
            th {{
                background: #f7f7f7;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                color: #333;
                border-bottom: 2px solid #ddd;
            }}
            td {{
                padding: 10px 12px;
                border-bottom: 1px solid #eee;
            }}
            tr:hover {{
                background: #f9f9f9;
            }}
            .success {{
                color: #27ae60;
                font-weight: bold;
            }}
            .warning {{
                color: #f39c12;
                font-weight: bold;
            }}
            .danger {{
                color: #e74c3c;
                font-weight: bold;
            }}
            .chart {{
                margin-top: 20px;
                padding: 20px;
                background: #f9f9f9;
                border-radius: 10px;
            }}
            .footer {{
                background: #333;
                color: white;
                text-align: center;
                padding: 20px;
                font-size: 0.9em;
            }}
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 20px;
                background: #f093fb;
                color: white;
                font-size: 0.85em;
                margin: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛍️ Trendyol Scraping Raporu</h1>
                <div class="subtitle">{datetime.now().strftime('%d %B %Y, %H:%M')}</div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-number">{stats['total_products']}</div>
                    <div class="stat-label">Toplam Ürün</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['real_products']}</div>
                    <div class="stat-label">Gerçek Trendyol Ürünü</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['total_reviews']}</div>
                    <div class="stat-label">Toplam Yorum</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{stats['real_reviews']}</div>
                    <div class="stat-label">Gerçek Yorum</div>
                </div>
            </div>

            <div class="section">
                <h2 class="section-title">📊 Veri Kalite Analizi</h2>
                <table>
                    <tr>
                        <th>Metrik</th>
                        <th>Değer</th>
                        <th>Durum</th>
                    </tr>
                    <tr>
                        <td>Gerçek Ürün Oranı</td>
                        <td>{(stats['real_products']/stats['total_products']*100 if stats['total_products'] > 0 else 0):.1f}%</td>
                        <td class="{'success' if stats['real_products']/stats['total_products'] > 0.8 else 'warning' if stats['real_products']/stats['total_products'] > 0.5 else 'danger' if stats['total_products'] > 0 else 'danger'}">
                            {'✅ Mükemmel' if stats['real_products']/stats['total_products'] > 0.8 else '⚠️ Orta' if stats['real_products']/stats['total_products'] > 0.5 else '❌ Düşük' if stats['total_products'] > 0 else '❌ Veri Yok'}
                        </td>
                    </tr>
                    <tr>
                        <td>Gerçek Yorum Oranı</td>
                        <td>{(stats['real_reviews']/stats['total_reviews']*100 if stats['total_reviews'] > 0 else 0):.1f}%</td>
                        <td class="{'success' if stats['real_reviews']/stats['total_reviews'] > 0.8 else 'warning' if stats['real_reviews']/stats['total_reviews'] > 0.5 else 'danger' if stats['total_reviews'] > 0 else 'danger'}">
                            {'✅ Mükemmel' if stats['real_reviews']/stats['total_reviews'] > 0.8 else '⚠️ Orta' if stats['real_reviews']/stats['total_reviews'] > 0.5 else '❌ Düşük' if stats['total_reviews'] > 0 else '❌ Veri Yok'}
                        </td>
                    </tr>
                    <tr>
                        <td>Kategori Çeşitliliği</td>
                        <td>{len(categories)} kategori</td>
                        <td class="{'success' if len(categories) > 5 else 'warning' if len(categories) > 2 else 'danger'}">
                            {'✅ İyi' if len(categories) > 5 else '⚠️ Orta' if len(categories) > 2 else '❌ Az'}
                        </td>
                    </tr>
                    <tr>
                        <td>Marka Çeşitliliği</td>
                        <td>{len(brands)} marka</td>
                        <td class="{'success' if len(brands) > 5 else 'warning' if len(brands) > 2 else 'danger'}">
                            {'✅ İyi' if len(brands) > 5 else '⚠️ Orta' if len(brands) > 2 else '❌ Az'}
                        </td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2 class="section-title">🏷️ En Popüler Markalar</h2>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Marka</th>
                            <th>Ürün Sayısı</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td>{i+1}</td><td>{brand if brand else "Belirtilmemiş"}</td><td><span class="badge">{count}</span></td></tr>' for i, (brand, count) in enumerate(brands)])}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2 class="section-title">⭐ En Yüksek Puanlı Ürünler</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Ürün Adı</th>
                            <th>Marka</th>
                            <th>Fiyat</th>
                            <th>Puan</th>
                            <th>Yorum</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td>{name[:50]}...</td><td>{brand or "-"}</td><td>₺{price:.2f}</td><td>⭐ {rating:.1f}</td><td>{review_count}</td></tr>' for name, brand, price, rating, review_count in top_rated])}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2 class="section-title">📅 Son Eklenen Ürünler</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Ürün Adı</th>
                            <th>Marka</th>
                            <th>Fiyat</th>
                            <th>Eklenme Tarihi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'<tr><td>{name[:50]}...</td><td>{brand or "-"}</td><td>₺{price:.2f}</td><td>{created_at}</td></tr>' for name, brand, price, created_at in recent_products])}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p>🤖 GitHub Actions ile otomatik oluşturuldu</p>
                <p>Sonraki güncelleme: 4 saat sonra</p>
            </div>
        </div>
    </body>
    </html>
    """

    # HTML dosyasını kaydet
    with open('scraping_report.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✅ HTML rapor oluşturuldu: scraping_report.html")

    # JSON özet
    summary = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats,
        'top_brands': [{'brand': b[0] if b[0] else 'Belirtilmemiş', 'count': b[1]} for b in brands[:5]],
        'top_categories': [{'category': c[0] if c[0] else 'Kategorisiz', 'count': c[1]} for c in categories[:5]],
        'data_quality': {
            'real_product_ratio': stats['real_products'] / stats['total_products'] if stats['total_products'] > 0 else 0,
            'real_review_ratio': stats['real_reviews'] / stats['total_reviews'] if stats['total_reviews'] > 0 else 0,
            'status': 'SUCCESS' if stats['real_products'] > stats['total_products'] * 0.5 else 'NEEDS_IMPROVEMENT'
        }
    }

    with open('scraping_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("✅ JSON özet oluşturuldu: scraping_summary.json")

    conn.close()

if __name__ == "__main__":
    generate_html_report()