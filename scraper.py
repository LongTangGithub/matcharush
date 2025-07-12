"""
MatchaRush - Basic Ippodo Scraper
A simple web scraper to detect stock status of Ippodo matcha products
"""

import time
import random
from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import os

class IppodoScraper:
    """
    A web scraper for monitoring Ippodo Tea matcha product stock status.
    
    This class uses Playwright to scrape product pages and detect whether
    matcha products are in stock or sold out based on specific keywords.
    """
    
    def __init__(self, headless=True, delay_range=(2, 5)):
        """
        Initialize the scraper with configuration options.
        
        Args:
            headless (bool): Whether to run browser in headless mode (no GUI)
            delay_range (tuple): Min and max seconds to wait between requests
        """
        self.headless = headless
        self.delay_range = delay_range
        self.user_agents = [
            # Modern browser user agents for 2025 (based on latest research)
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"
        ]
    
    def get_random_user_agent(self):
        """
        Get a random user agent string to rotate between requests.
        
        Returns:
            str: A random user agent string
        """
        return random.choice(self.user_agents)
    
    def add_delay(self):
        """
        Add a random delay between requests to be respectful to the server.
        Uses the delay_range specified in __init__.
        """
        delay = random.uniform(self.delay_range[0], self.delay_range[1])
        print(f"⏱️  Waiting {delay:.1f} seconds to be respectful...")
        time.sleep(delay)
    
    def check_stock_status(self, url):
        """
        Check the stock status of a matcha product on Ippodo's website.
        
        Args:
            url (str): The full URL of the product page to check
            
        Returns:
            dict: Contains stock status and relevant information
                {
                    'url': str,
                    'product_name': str,
                    'in_stock': bool,
                    'price': str,
                    'status_text': str,
                    'timestamp': str
                }
        """
        result = {
            'url': url,
            'product_name': 'Unknown',
            'in_stock': False,
            'price': 'Unknown',
            'status_text': '',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Start Playwright browser
            with sync_playwright() as p:
                # Launch browser with random user agent
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent=self.get_random_user_agent(),
                    viewport={'width': 1920, 'height': 1080}
                )
                page = context.new_page()
                
                print(f"🌐 Navigating to: {url}")
                
                # Navigate to the product page with longer timeout
                response = page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Check if page loaded successfully
                if response.status != 200:
                    print(f"❌ Failed to load page. Status code: {response.status}")
                    result['status_text'] = f"Page load failed: {response.status}"
                    return result
                
                # Wait for page to fully load
                page.wait_for_load_state('domcontentloaded')
                
                # Extract product name (try multiple selectors)
                try:
                    # Try to find the product title
                    product_name = page.locator('h1').first.inner_text()
                    result['product_name'] = product_name.strip()
                    print(f"📦 Product: {result['product_name']}")
                except:
                    print("⚠️  Could not extract product name")
                
                # Extract price
                try:
                    # Look for price elements (multiple possible selectors)
                    price_selectors = ['[data-price]', '.price', '[class*="price"]']
                    for selector in price_selectors:
                        price_element = page.locator(selector).first
                        if price_element.is_visible():
                            result['price'] = price_element.inner_text().strip()
                            print(f"💰 Price: {result['price']}")
                            break
                except:
                    print("⚠️  Could not extract price")
                
                # KEY DETECTION LOGIC - Check for stock status
                page_content = page.content().lower()  # Get all page content in lowercase
                
                # Method 1: Look for "Add to cart" button (IN STOCK)
                add_to_cart_found = False
                try:
                    # Check for various "Add to cart" button selectors
                    add_to_cart_selectors = [
                        'text="Add to cart"',
                        'text="Add to Cart"', 
                        '[data-testid="add-to-cart"]',
                        'button:has-text("Add to cart")',
                        'button:has-text("Add to Cart")'
                    ]
                    
                    for selector in add_to_cart_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible() and not element.is_disabled():
                                add_to_cart_found = True
                                print("✅ Found active 'Add to cart' button - PRODUCT IS IN STOCK")
                                break
                        except:
                            continue
                except:
                    pass
                
                # Method 2: Look for "Sold out" and "Pre order" indicators (OUT OF STOCK)
                sold_out_found = False
                out_of_stock_indicators = [
                    "sold out",
                    "pre order",  # Added this based on current Ippodo status
                    "out of stock", 
                    "currently sold out",
                    "expected in stock by",
                    "notify me when available",
                    "notify me"
                ]
                
                for indicator in out_of_stock_indicators:
                    if indicator in page_content:
                        sold_out_found = True
                        print(f"❌ Found out of stock indicator: '{indicator}'")
                        break
                
                # Method 3: Check for email notification forms (additional OUT OF STOCK confirmation)
                notify_form_found = False
                try:
                    notify_selectors = [
                        'input[type="email"]',
                        'button:has-text("Notify")',
                        '[placeholder*="email"]'
                    ]
                    
                    for selector in notify_selectors:
                        if page.locator(selector).first.is_visible():
                            notify_form_found = True
                            print("📧 Found email notification form - confirms OUT OF STOCK")
                            break
                except:
                    pass
                
                # DETERMINE FINAL STOCK STATUS
                if add_to_cart_found and not sold_out_found:
                    # Clear in-stock case
                    result['in_stock'] = True
                    result['status_text'] = "In Stock - Add to cart button found"
                    print("🟢 FINAL STATUS: IN STOCK")
                    
                elif sold_out_found or notify_form_found:
                    # Clear out-of-stock case  
                    result['in_stock'] = False
                    result['status_text'] = "Out of Stock - Sold out indicators found"
                    print("🔴 FINAL STATUS: OUT OF STOCK")
                    
                else:
                    # Unclear case - default to out of stock for safety
                    result['in_stock'] = False
                    result['status_text'] = "Status unclear - defaulting to out of stock"
                    print("🟡 FINAL STATUS: UNCLEAR (defaulting to OUT OF STOCK)")
                
                browser.close()
                
        except Exception as e:
            print(f"❌ Error occurred while scraping: {str(e)}")
            result['status_text'] = f"Error: {str(e)}"
        
        return result
    
    def test_with_mock_pages(self):
        """
        Test the scraper with local mock HTML pages before using on real websites.
        This helps verify the detection logic works correctly.
        """
        print("🧪 Testing scraper with mock pages...")
        
        # Get the current script directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Test files (adjust paths as needed)
        test_files = [
            os.path.join(current_dir, 'mock_pages', 'ippodo_in_stock.html'),
            os.path.join(current_dir, 'mock_pages', 'ippodo_out_of_stock.html')
        ]
        
        for test_file in test_files:
            if os.path.exists(test_file):
                file_url = f"file://{test_file}"
                print(f"\n📁 Testing with: {os.path.basename(test_file)}")
                result = self.check_stock_status(file_url)
                print(f"Result: {result}")
                
                # Add delay between tests
                if test_file != test_files[-1]:  # Don't delay after last test
                    self.add_delay()
            else:
                print(f"⚠️  Mock file not found: {test_file}")

def main():
    """
    Main function to demonstrate the scraper usage.
    """
    print("🍃 MatchaRush - Ippodo Scraper Starting...")
    print("=" * 50)
    
    # Initialize scraper
    # Set headless=False to see the browser window (useful for debugging)
    scraper = IppodoScraper(headless=True, delay_range=(2, 4))
    
    # Test with mock pages first
    scraper.test_with_mock_pages()
    
    print("\n" + "=" * 50)
    print("🧪 Mock page testing complete!")
    print("\n🔄 Ready to test with real Ippodo URL? (Uncomment the lines below)")
    
    # REAL WEBSITE TESTING (uncomment when ready)
    real_url = "https://ippodotea.com/products/ikuyo"  # Fixed URL
    print(f"\n🌐 Testing with real Ippodo page...")
    result = scraper.check_stock_status(real_url)
    print(f"Real site result: {result}")

if __name__ == "__main__":
    main()