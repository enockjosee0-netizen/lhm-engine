import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.betika.com/',
}

urls = [
    'https://www.betika.com/en-ke/s/soccer/countries',
    'https://www.betika.com/en-ke/download-fixtures',
    'https://www.betika.com/en-ke/livescore',
]

for url in urls:
    print(f'\n=== {url} ===')
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f'Status: {resp.status_code}')
        print(f'Content-Type: {resp.headers.get("Content-Type")}')
        print(f'Length: {len(resp.text)}')
        if resp.status_code == 200:
            print(f'First 300 chars: {resp.text[:300]}')
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')
