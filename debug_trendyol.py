#!/usr/bin/env python3
"""
Debug script to check actual Trendyol HTML structure
"""

import cloudscraper
from bs4 import BeautifulSoup
import json

def debug_trendyol():
    scraper = cloudscraper.create_scraper()

    # Test URL
    url = "https://www.trendyol.com/kadin-giyim-x-g1-c82?sst=BEST_SELLER"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }

    print(f"🔍 Fetching: {url}")
    response = scraper.get(url, headers=headers, timeout=15)

    print(f"📋 Response status: {response.status_code}")
    print(f"📋 Content-Type: {response.headers.get('content-type', 'N/A')}")

    # Save response to file for analysis
    with open('trendyol_response.html', 'w', encoding='utf-8') as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    print("\n🔍 Looking for product cards...")

    # Try different selectors
    selectors_to_try = [
        'div.p-card-wrppr',
        'div.p-card-chldrn-cntnr',
        'div[class*="product"]',
        'div[class*="p-card"]',
        'article',
        'div[data-id]',
        '[class*="product-card"]'
    ]

    for selector in selectors_to_try:
        cards = soup.select(selector)
        if cards:
            print(f"✅ Found {len(cards)} elements with selector: {selector}")

            # Analyze first card
            if cards:
                first_card = cards[0]
                print(f"\n📦 First card analysis:")
                print(f"  - Tag: {first_card.name}")
                print(f"  - Classes: {first_card.get('class', [])}")
                print(f"  - data-id: {first_card.get('data-id', 'N/A')}")

                # Look for price elements
                price_selectors = [
                    '.prc-box-dscntd',
                    '.prc-box-sllng',
                    '.prc-box',
                    '[class*="prc"]',
                    '[class*="price"]',
                    'span[class*="prc"]',
                    'div[class*="prc"]'
                ]

                print("\n  💰 Price elements:")
                for ps in price_selectors:
                    price_elem = first_card.select_one(ps)
                    if price_elem:
                        print(f"    - Found with {ps}: {price_elem.get_text(strip=True)[:50]}")
                        print(f"      Classes: {price_elem.get('class', [])}")

                # Look for brand elements
                brand_selectors = [
                    '.prdct-desc-cntnr-brand',
                    '[class*="brand"]',
                    'span[class*="brand"]',
                    '.product-brand'
                ]

                print("\n  🏷️ Brand elements:")
                for bs in brand_selectors:
                    brand_elem = first_card.select_one(bs)
                    if brand_elem:
                        print(f"    - Found with {bs}: {brand_elem.get_text(strip=True)[:50]}")

                # Look for name elements
                name_selectors = [
                    '.prdct-desc-cntnr-name',
                    '[class*="name"]',
                    '[class*="title"]',
                    '[class*="ttl"]',
                    'span[class*="prdct"]',
                    '.product-name'
                ]

                print("\n  📝 Name elements:")
                for ns in name_selectors:
                    name_elem = first_card.select_one(ns)
                    if name_elem:
                        print(f"    - Found with {ns}: {name_elem.get_text(strip=True)[:50]}")

                # Print full first card HTML for inspection
                print("\n📄 First card HTML (first 1000 chars):")
                print(str(first_card)[:1000])

            break

    # Check if there's script data with products
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if 'itemListElement' in data:
                print(f"\n✨ Found JSON-LD data with {len(data['itemListElement'])} items")
                break
        except:
            pass

    # Check for __SEARCH_APP_INITIAL_STATE__
    for script in soup.find_all('script'):
        if script.string and '__SEARCH_APP_INITIAL_STATE__' in script.string:
            print("\n✨ Found __SEARCH_APP_INITIAL_STATE__ data")
            # Extract the JSON
            import re
            match = re.search(r'window.__SEARCH_APP_INITIAL_STATE__\s*=\s*({.*?});', script.string, re.DOTALL)
            if match:
                try:
                    state_data = json.loads(match.group(1))
                    if 'products' in str(state_data):
                        print("  - Contains product data!")
                        # Find products in the state
                        def find_products(obj, depth=0):
                            if depth > 5:
                                return
                            if isinstance(obj, dict):
                                if 'products' in obj:
                                    products = obj['products']
                                    if isinstance(products, list) and products:
                                        print(f"  - Found {len(products)} products in state")
                                        # Show first product
                                        first = products[0]
                                        print(f"\n  First product from state:")
                                        print(f"    - id: {first.get('id')}")
                                        print(f"    - name: {first.get('name', '')[:50]}")
                                        print(f"    - price: {first.get('price')}")
                                        print(f"    - brand: {first.get('brand')}")
                                        return products
                                for key, value in obj.items():
                                    result = find_products(value, depth+1)
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = find_products(item, depth+1)
                                    if result:
                                        return result

                        products = find_products(state_data)
                        if products:
                            # Save for analysis
                            with open('trendyol_products.json', 'w', encoding='utf-8') as f:
                                json.dump(products[:5], f, indent=2, ensure_ascii=False)
                            print(f"\n  Saved first 5 products to trendyol_products.json")
                except Exception as e:
                    print(f"  Error parsing state: {e}")
            break

    print("\n✅ Debug complete! Check trendyol_response.html for full HTML")

if __name__ == "__main__":
    debug_trendyol()