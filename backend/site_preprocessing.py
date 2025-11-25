#!/usr/bin/env python3
"""
Selenium web scraper with uBlock Origin ad-blocking
Waits for page to fully render and outputs HTML without ads
"""

import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def download_ublock_extension():
    """
    Download uBlock Origin extension.
    Returns the path to the .crx file
    """
    import urllib.request
    import os
    
    # uBlock Origin Chrome extension ID and download URL
    extension_id = "cjpalhdlnbpafiamejdnhcphjbkeiagm"
    
    # For a more reliable method, we'll use a pre-built extension path
    # You can download it from: https://github.com/gorhill/uBlock/releases
    print("Note: Download uBlock Origin from Chrome Web Store or GitHub releases")
    print("For this script, we'll use Chrome's built-in extension loading")
    
    return None


def create_driver_with_adblock():
    """
    Create a Chrome WebDriver instance with uBlock Origin installed
    """
    chrome_options = Options()
    
    # Add uBlock Origin extension
    # Method 1: Use the extension from Chrome Web Store (requires manual download)
    # Download from: https://github.com/gorhill/uBlock/releases
    # Uncomment and modify the path below:
    # chrome_options.add_extension('/path/to/uBlock-Origin.crx')
    
    # Method 2: Use unpacked extension directory (recommended for Arch Linux)
    # Download and extract uBlock Origin, then point to the directory
    # Note: Update this path to where you extracted uBlock0.chromium.zip
    ublock_path = "./uBlock0.chromium/uBlock0.chromium"  # Relative to where you run the script
    
    # For unpacked extensions, use --load-extension argument
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    # Attempt to load uBlock Origin if available
    import os
    if os.path.isdir(ublock_path):
        chrome_options.add_argument(f'--load-extension={os.path.abspath(ublock_path)}')
        print("✓ uBlock Origin loaded")
    else:
        print("⚠ uBlock Origin not found - continuing without extension")
        print(f"  Looking for: {os.path.abspath(ublock_path)}")
        print("  Download from: https://github.com/gorhill/uBlock/releases")
        print("  Or install via: wget https://github.com/gorhill/uBlock/releases/latest/download/uBlock0.chromium.zip")
    
    # Create and return driver
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def scrape_page(url, wait_time=1):
    """
    Scrape a webpage with ad-blocking
    
    Args:
        url: The URL to scrape
        wait_time: Time to wait for page to fully render (seconds)
    
    Returns:
        str: The HTML content of the page
    """
    driver = None
    try:
        print(f"Initializing browser with ad-blocker...")
        driver = create_driver_with_adblock()
        
        print(f"Loading URL: {url}")
        driver.get(url)
        
        # Wait for the page to load
        print(f"Waiting {wait_time} second(s) for page to render...")
        time.sleep(wait_time)
        
        # Optional: Wait for specific element (body tag) to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source (HTML)
        html_content = driver.page_source
        
        print(f"✓ Successfully scraped {len(html_content)} characters")
        return html_content
        
    except Exception as e:
        print(f"Error during scraping: {e}", file=sys.stderr)
        return None
        
    finally:
        if driver:
            driver.quit()
            print("Browser closed")


def site_preprocessing(url):
    """Main function"""
    # Example URL - replace with your target
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://www.vogue.com/article/thin-little-scarf-fall-winter-trend"
        print(f"No URL provided, using default: {url}")
        print(f"Usage: python {sys.argv[0]} <url>")
    
    # Scrape the page
    html = scrape_page(url, wait_time=1)
    
    if html:
        # Output the HTML
        print("\n" + "="*80)
        print("HTML OUTPUT:")
        print("="*80 + "\n")
        print(html)
        
        # Optionally save to file
        output_file = "scraped_page.html"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n✓ HTML saved to: {output_file}")
    else:
        print("Failed to scrape the page", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    site_preprocessing()