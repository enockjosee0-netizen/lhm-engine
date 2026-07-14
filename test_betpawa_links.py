import undetected_chromedriver as uc
import time
import json

try:
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    
    # Enable CDP
    driver.execute_cdp_cmd('Network.enable', {})
    
    # Collect requests
    requests = []
    
    # We can't easily intercept requests with selenium, but we can
    # try to find API patterns by checking the page source
    
    driver.get('https://www.betpawa.co.ke/')
    time.sleep(10)
    
    # Get all links
    links = driver.find_elements("tag name", "a")
    print(f'Found {len(links)} links')
    
    api_links = []
    for link in links[:50]:
        try:
            href = link.get_attribute('href')
            if href and ('api' in href.lower() or 'odds' in href.lower() or 'match' in href.lower() or 'event' in href.lower() or 'fixture' in href.lower()):
                api_links.append(href)
        except:
            pass
    
    print(f'API-like links: {api_links[:10]}')
    
    # Get all script srcs
    scripts = driver.find_elements("tag name", "script")
    print(f'Found {len(scripts)} script tags')
    
    for script in scripts[:20]:
        try:
            src = script.get_attribute('src')
            if src:
                print(f'Script: {src[:100]}')
        except:
            pass
    
    driver.quit()
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass
