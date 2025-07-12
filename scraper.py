"""
MatchaRush - Expanded Multi-Product Monitoring System
Monitors multiple Ippodo matcha products for stock status changes
"""

import time
import random
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import os

class ProductMonitor:
    """
    A comprehensive web scraper for monitoring multiple Ippodo Tea matcha products.
    
    This class manages a list of products and can check stock status for all of them,
    with proper rate limiting and respectful scraping practices.
    """
    
    def __init__(self, headless=True, delay_range=(3, 6)):
        """
        Initialize the product monitor with configuration options.
        
        Args:
            headless (bool): Whether to run browser in headless mode (no GUI)
            delay_range (tuple): Min and max seconds to wait between requests
        """
        self.headless = headless
        self.delay_range = delay_range
        self.user_agents = [
            # Modern browser user agents for 2025
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]
        
        # Product catalog - COMPLETE Ippodo monitoring list
        self.products = {
            # === IKUYO SERIES ===
            'ikuyo_30g': {
                'name': 'Ikuyo Matcha 30g',
                'url': 'https://ippodotea.com/products/ikuyo',
                'category': 'Medium & Snappy',
                'expected_price': '$19',
                'priority': 'high'
            },
            'ikuyo_100g': {
                'name': 'Ikuyo Matcha 100g',
                'url': 'https://ippodotea.com/products/ikuyo-100',
                'category': 'Medium & Snappy',
                'expected_price': '$55',
                'priority': 'high'
            },
            
            # === SAYAKA SERIES ===
            'sayaka_40g': {
                'name': 'Sayaka Matcha 40g', 
                'url': 'https://ippodotea.com/products/sayaka-no-mukashi',
                'category': 'Rich & Smooth',
                'expected_price': '$37',
                'priority': 'high'
            },
            'sayaka_100g': {
                'name': 'Sayaka Matcha 100g',
                'url': 'https://ippodotea.com/products/sayaka-100g',
                'category': 'Rich & Smooth',
                'expected_price': '$81',
                'priority': 'high'
            },
            
            # === UMMON SERIES ===
            'ummon_20g': {
                'name': 'Ummon Matcha 20g',
                'url': 'https://ippodotea.com/products/ummon-no-mukashi-20g',
                'category': 'Rich & Robust',
                'expected_price': '$27',
                'priority': 'high'
            },
            'ummon_40g': {
                'name': 'Ummon Matcha 40g',
                'url': 'https://ippodotea.com/products/ummon-no-mukashi-40g',
                'category': 'Rich & Robust',
                'expected_price': '$50',
                'priority': 'high'
            },
            
            # === OTHER POPULAR PRODUCTS ===
            'horai_20g': {
                'name': 'Horai Matcha 20g',
                'url': 'https://ippodotea.com/products/horai-no-mukashi',
                'category': 'Rich & Smooth', 
                'expected_price': '$20',
                'priority': 'medium'
            },
            'kan_30g': {
                'name': 'Kan Matcha 30g',
                'url': 'https://ippodotea.com/products/kan',
                'category': 'Medium & Round',
                'expected_price': '$25',
                'priority': 'medium'
            },
            'wakaki_40g': {
                'name': 'Wakaki Matcha 40g',
                'url': 'https://ippodotea.com/products/wakaki-shiro',
                'category': 'Light & Sharp',
                'expected_price': '$13',
                'priority': 'low'
            },
            'seiun_40g': {
                'name': 'Seiun Matcha 40g',
                'url': 'https://ippodotea.com/products/seiun',
                'category': 'Rich & Replenishing',
                'expected_price': '$45',
                'priority': 'medium'
            }
        }
    
    def get_random_user_agent(self):
        """Get a random user agent string to rotate between requests."""
        return random.choice(self.user_agents)
    
    def add_delay(self, custom_delay=None):
        """
        Add a random delay between requests to be respectful to the server.
        
        Args:
            custom_delay (tuple, optional): Custom delay range for this request
        """
        delay_range = custom_delay if custom_delay else self.delay_range
        delay = random.uniform(delay_range[0], delay_range[1])
        print(f"⏱️  Waiting {delay:.1f} seconds to be respectful...")
        time.sleep(delay)
    
    def check_single_product(self, product_id, product_info):
        """
        Check the stock status of a single matcha product.
        
        Args:
            product_id (str): The product identifier key
            product_info (dict): Product information including URL and metadata
            
        Returns:
            dict: Comprehensive product status information
        """
        result = {
            'product_id': product_id,
            'product_name': product_info['name'],
            'url': product_info['url'],
            'category': product_info['category'],
            'expected_price': product_info['expected_price'],
            'priority': product_info['priority'],
            'in_stock': False,
            'actual_price': 'Unknown',
            'status_text': '',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'scrape_success': False
        }
        
        try:
            with sync_playwright() as p:
                # Launch browser with random user agent
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=self.get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                print(f"🌐 Checking {product_info['name']}...")
                print(f"    URL: {product_info['url']}")
                
                # Navigate to the product page
                response = page.goto(product_info['url'], wait_until='domcontentloaded', timeout=60000)
                
                if response.status != 200:
                    print(f"❌ Failed to load page. Status code: {response.status}")
                    result['status_text'] = f"Page load failed: {response.status}"
                    return result
                
                # Wait for page to fully load
                page.wait_for_load_state('domcontentloaded')
                
                # Extract product name (try multiple selectors)
                try:
                    product_name = page.locator('h1').first.inner_text()
                    result['product_name'] = product_name.strip()
                    print(f"    📦 Found: {result['product_name']}")
                except:
                    print(f"    ⚠️  Could not extract product name, using default")
                
                # Extract price
                try:
                    price_selectors = ['[data-price]', '.price', '[class*="price"]', 'span:has-text("$")']
                    for selector in price_selectors:
                        try:
                            price_element = page.locator(selector).first
                            if price_element.is_visible():
                                result['actual_price'] = price_element.inner_text().strip()
                                print(f"    💰 Price: {result['actual_price']}")
                                break
                        except:
                            continue
                except:
                    print(f"    ⚠️  Could not extract price")
                
                # STOCK DETECTION LOGIC
                page_content = page.content().lower()
                
                # Method 1: Look for "Add to cart" or "Add to bag" button (IN STOCK)
                add_to_cart_found = False
                try:
                    add_to_cart_selectors = [
                        'text="Add to cart"',
                        'text="Add to Cart"',
                        'text="Add to bag"',
                        'text="Add to Bag"',
                        '[data-testid="add-to-cart"]',
                        'button:has-text("Add to cart")',
                        'button:has-text("Add to Cart")',
                        'button:has-text("Add to bag")',
                        'button:has-text("Add to Bag")'
                    ]
                    
                    for selector in add_to_cart_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible() and not element.is_disabled():
                                add_to_cart_found = True
                                print(f"    ✅ Found active purchase button - IN STOCK")
                                break
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Look for out-of-stock indicators
                sold_out_found = False
                out_of_stock_indicators = [
                    "sold out",
                    "pre order",
                    "out of stock",
                    "currently sold out",
                    "expected in stock by",
                    "notify me when available",
                    "notify me",
                    "back in stock"
                ]
                
                for indicator in out_of_stock_indicators:
                    if indicator in page_content:
                        sold_out_found = True
                        print(f"    ❌ Found out of stock indicator: '{indicator}'")
                        break
                
                # Method 3: Check for email notification forms
                notify_form_found = False
                try:
                    notify_selectors = [
                        'input[type="email"]',
                        'button:has-text("Notify")',
                        '[placeholder*="email"]',
                        'input[placeholder*="notify"]'
                    ]
                    
                    for selector in notify_selectors:
                        if page.locator(selector).first.is_visible():
                            notify_form_found = True
                            print(f"    📧 Found email notification form")
                            break
                except:
                    pass
                
                # DETERMINE FINAL STOCK STATUS
                if add_to_cart_found and not sold_out_found:
                    result['in_stock'] = True
                    result['status_text'] = "In Stock - Purchase button available"
                    print(f"    🟢 FINAL STATUS: IN STOCK")
                    
                elif sold_out_found or notify_form_found:
                    result['in_stock'] = False
                    result['status_text'] = "Out of Stock - Sold out indicators found"
                    print(f"    🔴 FINAL STATUS: OUT OF STOCK")
                    
                else:
                    result['in_stock'] = False
                    result['status_text'] = "Status unclear - defaulting to out of stock"
                    print(f"    🟡 FINAL STATUS: UNCLEAR (defaulting to OUT OF STOCK)")
                
                result['scrape_success'] = True
                browser.close()
                
        except Exception as e:
            print(f"    ❌ Error occurred while scraping {product_info['name']}: {str(e)}")
            result['status_text'] = f"Error: {str(e)}"
            result['scrape_success'] = False
        
        return result
    
    def monitor_all_products(self, priority_filter=None):
        """
        Monitor all products in the catalog for stock status.
        
        Args:
            priority_filter (str, optional): Only monitor products with this priority level
                                           ('high', 'medium', 'low')
        
        Returns:
            list: List of dictionaries containing status for each product
        """
        print("🍃 MatchaRush - Starting Multi-Product Monitoring...")
        print("=" * 60)
        
        results = []
        products_to_check = self.products.items()
        
        # Filter by priority if specified
        if priority_filter:
            products_to_check = [(pid, pinfo) for pid, pinfo in self.products.items() 
                               if pinfo['priority'] == priority_filter]
            print(f"🎯 Monitoring only '{priority_filter}' priority products")
        
        print(f"📋 Checking {len(products_to_check)} products...")
        print()
        
        for i, (product_id, product_info) in enumerate(products_to_check):
            # Check the product
            result = self.check_single_product(product_id, product_info)
            results.append(result)
            
            # Add delay between products (except for the last one)
            if i < len(products_to_check) - 1:
                self.add_delay()
                print()  # Add spacing between products
        
        return results
    
    def save_results_to_file(self, results, filename=None):
        """
        Save monitoring results to a JSON file.
        
        Args:
            results (list): List of product monitoring results
            filename (str, optional): Custom filename, defaults to timestamp-based name
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"monitoring_results_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")
    
    def print_summary_report(self, results):
        """
        Print a formatted summary of monitoring results.
        
        Args:
            results (list): List of product monitoring results
        """
        print("\n" + "=" * 60)
        print("📊 MONITORING SUMMARY REPORT")
        print("=" * 60)
        
        in_stock_count = sum(1 for r in results if r['in_stock'])
        out_of_stock_count = len(results) - in_stock_count
        
        print(f"🟢 In Stock: {in_stock_count}")
        print(f"🔴 Out of Stock: {out_of_stock_count}")
        print(f"📦 Total Products: {len(results)}")
        print()
        
        # Detailed breakdown
        for result in results:
            status_emoji = "🟢" if result['in_stock'] else "🔴"
            print(f"{status_emoji} {result['product_name']}")
            print(f"    Price: {result['actual_price']} (Expected: {result['expected_price']})")
            print(f"    Status: {result['status_text']}")
            print(f"    Priority: {result['priority']}")
            print()
        
        print(f"⏰ Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """
    Main function to demonstrate the expanded monitoring system.
    """
    print("🍃 MatchaRush - Expanded Product Monitoring System")
    print("=" * 60)
    
    # Initialize monitor
    monitor = ProductMonitor(headless=True, delay_range=(3, 5))
    
    print("📋 Available products in monitoring system:")
    for product_id, product_info in monitor.products.items():
        print(f"  • {product_info['name']} ({product_info['priority']} priority)")
    print()
    
    # Monitor all products
    print("🚀 Starting comprehensive monitoring...")
    results = monitor.monitor_all_products()
    
    # Print summary report
    monitor.print_summary_report(results)
    
    # Save results to file
    monitor.save_results_to_file(results)
    
    print("\n🎉 Monitoring complete!")
    print("\n💡 Next steps:")
    print("  • Review the results file for historical tracking")
    print("  • Set up notifications for stock changes")
    print("  • Add more products to the monitoring list")

if __name__ == "__main__":
    main()