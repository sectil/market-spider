#!/usr/bin/env python3
"""
GERÇEK TRENDYOL VERİ ÇEKME - Selenium ile
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import sqlite3
from datetime import datetime
import time
import random

def setup_driver():
    """Selenium driver kurulumu"""
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver
    except:
        print("Chrome driver bulunamadı. Firefox deneyelim...")
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        firefox_options = FirefoxOptions()
        firefox_options.add_argument('--disable-blink-features=AutomationControlled')
        return webdriver.Firefox(options=firefox_options)

def scrape_trendyol_real():
    """Gerçek Trendyol verilerini çek"""

    driver = setup_driver()
    conn = sqlite3.connect('market_spider.db')
    cursor = conn.cursor()

    # Simülasyon verileri temizle
    print("🧹 Simülasyon verileri temizleniyor...")
    cursor.execute("DELETE FROM product_reviews WHERE scraped_at IS NULL")
    cursor.execute("DELETE FROM products WHERE url LIKE '%example.com%'")
    conn.commit()

    try:
        print("🌐 Trendyol'a bağlanılıyor...")
        driver.get("https://www.trendyol.com/cok-satanlar")
        time.sleep(5)  # Sayfa yüklensin

        # Cookie kabul et (varsa)
        try:
            cookie_btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_btn.click()
            time.sleep(2)
        except:
            pass

        print("📦 Ürünler toplanıyor...")

        # Ürün kartlarını bul
        products = driver.find_elements(By.CSS_SELECTOR, "div.p-card-wrppr")[:20]
        print(f"✅ {len(products)} ürün bulundu")

        for idx, product in enumerate(products, 1):
            try:
                # Ürün bilgileri
                name = product.find_element(By.CSS_SELECTOR, ".prdct-desc-cntnr-name").text
                brand = product.find_element(By.CSS_SELECTOR, ".prdct-desc-cntnr-ttl").text
                price = product.find_element(By.CSS_SELECTOR, ".prc-box-dscntd").text.replace(" TL", "").replace(",", ".")
                link = product.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                # Veritabanına ekle
                cursor.execute("""
                    INSERT INTO products (name, brand, price, url, site_name, created_at, in_stock)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, brand, float(price), link, "Trendyol", datetime.now(), 1))

                product_id = cursor.lastrowid
                print(f"  {idx}. {name[:30]} eklendi")

                # Ürün detay sayfasına git
                driver.execute_script(f"window.open('{link}', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                time.sleep(random.uniform(3, 5))

                # Yorumları bul
                try:
                    # Yorumlar bölümüne kaydır
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(2)

                    reviews = driver.find_elements(By.CSS_SELECTOR, "div.comment")[:10]

                    for review in reviews:
                        try:
                            reviewer = review.find_element(By.CSS_SELECTOR, ".comment-owner").text
                            rating = len(review.find_elements(By.CSS_SELECTOR, ".full"))
                            comment = review.find_element(By.CSS_SELECTOR, ".comment-text").text

                            cursor.execute("""
                                INSERT INTO product_reviews
                                (product_id, reviewer_name, rating, review_text, review_date, scraped_at, sentiment_score)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            """, (
                                product_id, reviewer, rating, comment,
                                datetime.now(), datetime.now(),
                                1.0 if rating >= 4 else -1.0 if rating <= 2 else 0.0
                            ))

                        except Exception as e:
                            continue

                except Exception as e:
                    print(f"    Yorum bulunamadı: {e}")

                # Sekmeyi kapat ve ana sayfaya dön
                driver.close()
                driver.switch_to.window(driver.window_handles[0])

                conn.commit()

            except Exception as e:
                print(f"  Hata: {e}")
                continue

    except Exception as e:
        print(f"❌ Ana hata: {e}")

    finally:
        driver.quit()
        conn.close()

    print("\n✅ Gerçek veri çekme tamamlandı!")

if __name__ == "__main__":
    scrape_trendyol_real()