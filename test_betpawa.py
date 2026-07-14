import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import re
import time
import json

try:
    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = uc.Chrome(options=options)
    driver.get('https://www.betpawa.co.ke/')
    time.sleep(8)
    
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    
    # Look for any JSON data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('matches' in script.string.lower() or 'events' in script.string.lower()):
            print('Found potential data script')
            text = script.string
            matches = re.findall(r'\[.*?\]', text, re.DOTALL)
            for m in matches[:3]:
                print(f'Array: {m[:200]}')
                print('---')
    
    # Try to find by class names
    classes = soup.find_all(class_=re.compile('match|event|game|fixture|bet|odd', re.I))
    print(f'Found {len(classes)} elements with betting-related classes')
    
    if classes:
        for c in classes[:5]:
            print(f'Class: {c.get("class")}, Text: {c.get_text()[:100]}')
    
    driver.quit()
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
    import traceback
    traceback.print_exc()
    try:
        driver.quit()
    except:
        pass
