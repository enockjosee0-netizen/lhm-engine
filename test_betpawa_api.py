import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.betpawa.co.ke/',
}

urls = [
    'https://www.betpawa.co.ke/events?categoryId=2&marketId=1X2',
    'https://www.betpawa.co.ke/events/live?categoryId=2&marketId=1X2',
]

for url in urls:
    print(f'\n=== {url} ===')
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f'Status: {resp.status_code}')
        if resp.status_code == 200:
            data = resp.json()
            print(f'Keys: {list(data.keys())[:10]}')
            if 'events' in data:
                print(f'Events: {len(data.get("events", []))}')
                if data.get('events'):
                    event = data['events'][0]
                    print(f'First event keys: {list(event.keys())[:10]}')
                    print(f'First event: {event}')
            elif 'data' in data:
                print(f'Data items: {len(data.get("data", []))}')
        else:
            print(f'Response: {resp.text[:200]}')
    except Exception as e:
        print(f'Error: {type(e).__name__}: {e}')
