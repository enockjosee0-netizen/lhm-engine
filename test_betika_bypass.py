"""
Betika Anti-Bot Bypass - Multi-Strategy Test
Tests multiple approaches to bypass Betika's protection.
"""
import time
import re
import json
from playwright.sync_api import sync_playwright

def test_strategy(name, url, setup_fn=None, wait_fn=None):
    """Test a specific scraping strategy."""
    print(f"\n{'='*60}")
    print(f"STRATEGY: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Africa/Nairobi",
            )
            
            # Apply stealth
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [
                    {name: 'PDF Viewer', filename: 'internal-pdf-viewer'},
                    {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                ]});
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                delete window.webdriver;
            """)
            
            page = context.new_page()
            
            # Custom setup if provided
            if setup_fn:
                setup_fn(page)
            
            print(f"Navigating to {url}...")
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Custom wait if provided
            if wait_fn:
                wait_fn(page)
            else:
                time.sleep(5)
            
            # Get content
            text = page.evaluate("document.body.innerText")
            content = page.content()
            
            print(f"Body text length: {len(text)}")
            print(f"Page content length: {len(content)}")
            
            if text and len(text) > 100:
                print("SUCCESS - Got content!")
                print(f"First 300 chars: {text[:300]}")
                
                # Look for odds data
                lines = text.split('\n')
                odds_lines = [l for l in lines if re.match(r'\d+\.\d+', l.strip())]
                print(f"Found {len(odds_lines)} odds-like lines")
                
                browser.close()
                return True, text
            else:
                print("FAILED - Empty or too short content")
                print(f"First 200 chars: {text[:200] if text else 'None'}")
            
            browser.close()
            return False, text
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False, str(e)

# Strategy 1: Direct with longer wait
def strategy1():
    def wait(page):
        print("Waiting 10 seconds for JS...")
        time.sleep(10)
        # Try scrolling
        page.evaluate("window.scrollBy(0, 500)")
        time.sleep(2)
    return test_strategy(
        "Direct with extended wait",
        "https://www.betika.com/en-ke/sports/soccer/odds",
        wait_fn=wait
    )

# Strategy 2: Mobile user agent
def strategy2():
    def setup(page):
        print("Using mobile user agent...")
    return test_strategy(
        "Mobile user agent",
        "https://www.betika.com/en-ke/sports/soccer/odds",
        setup_fn=lambda page: page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        })
    )

# Strategy 3: Homepage first, then navigate
def strategy3():
    print(f"\n{'='*60}")
    print("STRATEGY: Homepage session establishment")
    print(f"{'='*60}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            )
            
            page = context.new_page()
            
            # Step 1: Visit homepage
            print("Step 1: Loading homepage...")
            page.goto("https://www.betika.com/en-ke/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)
            
            homepage_text = page.evaluate("document.body.innerText")
            print(f"Homepage text length: {len(homepage_text)}")
            print(f"Homepage first 200 chars: {homepage_text[:200]}")
            
            # Step 2: Click on Soccer
            print("Step 2: Clicking Soccer...")
            try:
                page.click("text=Soccer", timeout=5000)
                time.sleep(3)
            except:
                print("Could not click Soccer, trying direct navigation...")
            
            # Step 3: Navigate to odds
            print("Step 3: Navigating to odds...")
            page.goto("https://www.betika.com/en-ke/sports/soccer/odds", wait_until="domcontentloaded", timeout=30000)
            time.sleep(8)
            
            text = page.evaluate("document.body.innerText")
            print(f"Odds page text length: {len(text)}")
            
            if text and len(text) > 100:
                print("SUCCESS!")
                print(f"First 300 chars: {text[:300]}")
                browser.close()
                return True, text
            
            browser.close()
            return False, text
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False, str(e)

# Strategy 4: Try different Betika domains/paths
def strategy4():
    urls = [
        "https://www.betika.com/en-ke/sports/soccer",
        "https://www.betika.com/en-ke/live",
        "https://www.betika.com/en-ke/sports",
        "https://betika.com/en-ke/sports/soccer/odds",
    ]
    
    for url in urls:
        success, text = test_strategy(
            f"Direct URL test: {url}",
            url,
            wait_fn=lambda page: time.sleep(5)
        )
        if success:
            return True, text
    
    return False, "All URLs failed"

# Strategy 5: Use requests with session persistence
def strategy5():
    print(f"\n{'='*60}")
    print("STRATEGY: Requests with session persistence")
    print(f"{'='*60}")
    
    try:
        import requests
        from requests.cookies import RequestsCookieJar
        
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })
        
        # Step 1: Get homepage to establish cookies
        print("Step 1: Getting homepage cookies...")
        resp1 = session.get("https://www.betika.com/en-ke/", timeout=15)
        print(f"Homepage status: {resp1.status_code}")
        print(f"Cookies: {dict(resp1.cookies)}")
        
        # Step 2: Try odds page with cookies
        print("Step 2: Getting odds page...")
        resp2 = session.get("https://www.betika.com/en-ke/sports/soccer/odds", timeout=15)
        print(f"Odds page status: {resp2.status_code}")
        print(f"Content length: {len(resp2.text)}")
        
        if resp2.status_code == 200 and len(resp2.text) > 1000:
            print("SUCCESS!")
            print(f"First 300 chars: {resp2.text[:300]}")
            return True, resp2.text
        
        return False, resp2.text
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False, str(e)

# Run all strategies
print("="*60)
print("BETIKA ANTI-BOT BYPASS - MULTI-STRATEGY TEST")
print("="*60)

strategies = [
    ("Strategy 1: Direct with extended wait", strategy1),
    ("Strategy 2: Mobile user agent", strategy2),
    ("Strategy 3: Homepage session establishment", strategy3),
    ("Strategy 4: Multiple URLs", strategy4),
    ("Strategy 5: Requests with session persistence", strategy5),
]

results = []
for name, strategy_fn in strategies:
    try:
        success, data = strategy_fn()
        results.append((name, success, len(data) if data else 0))
    except Exception as e:
        print(f"Strategy failed with exception: {e}")
        results.append((name, False, 0))

print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
for name, success, length in results:
    status = "SUCCESS" if success else "FAILED"
    print(f"{name}: {status} (content length: {length})")
