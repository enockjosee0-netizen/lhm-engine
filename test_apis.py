import aiohttp
import asyncio

async def test_apis():
    headers = {'User-Agent': 'LHM-Engine/1.0'}
    apis = [
        ('football-data.org competitions', 'https://api.football-data.org/v4/competitions'),
        ('football-data.org areas', 'https://api.football-data.org/v4/areas'),
        ('football-data.org teams', 'https://api.football-data.org/v4/teams?limit=10'),
        ('football-data.org matches FT', 'https://api.football-data.org/v4/matches?status=FINISHED&limit=10'),
        ('football-data.org matches SCHEDULED', 'https://api.football-data.org/v4/matches?status=SCHEDULED&limit=10'),
    ]
    
    async with aiohttp.ClientSession() as session:
        for name, url in apis:
            try:
                async with session.get(url, headers=headers, timeout=10) as resp:
                    print(f'{name}: {resp.status}')
                    if resp.status == 200:
                        data = await resp.json()
                        if 'matches' in data:
                            print(f'  Matches: {len(data.get("matches", []))}')
                        elif 'teams' in data:
                            print(f'  Teams: {len(data.get("teams", []))}')
                        elif 'competitions' in data:
                            print(f'  Competitions: {len(data.get("competitions", []))}')
            except Exception as e:
                print(f'{name}: Error - {type(e).__name__}: {str(e)[:50]}')

asyncio.run(test_apis())
