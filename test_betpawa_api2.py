import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.betpawa.co.ke/',
}

url = 'https://www.betpawa.co.ke/events?categoryId=2&marketId=1X2'
resp = requests.get(url, headers=headers, timeout=10)
print(f'Status: {resp.status_code}')
print(f'Content-Type: {resp.headers.get("Content-Type")}')
print(f'Length: {len(resp.text)}')
print(f'First 500 chars: {resp.text[:500]}')
