with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

registry = '''
# ======================================================================
# FREE API REGISTRY
# ======================================================================
FREE_API_REGISTRY = {
    "odds": [
        "https://api.the-odds-api.com/v4/sports/soccer/odds",
        "https://api.odds-api.io/v1/odds",
        "https://api-football-v1.p.rapidapi.com/v3/odds",
    ],
    "fixtures": [
        "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED",
        "https://api.football-data.org/v4/matches?status=LIVE",
        "https://api.betika.com/v1/forecast",
    ],
    "live_scores": [
        "https://api.football-data.org/v4/matches?status=LIVE",
    ],
    "team_stats": [
        "https://api.football-data.org/v4/teams",
    ],
    "historical": [
        "https://api.football-data.org/v4/matches?status=FINISHED",
    ],
    "telegram": [
        "https://api.telegram.org/bot{token}/sendMessage",
        "https://api.telegram.org/bot{token}/sendPhoto",
    ]
}

'''

if 'FREE_API_REGISTRY' not in content:
    content = content.replace('logging.basicConfig(', registry + 'logging.basicConfig(', 1)
    with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added FREE_API_REGISTRY to lhm_enhanced.py')
else:
    print('FREE_API_REGISTRY already exists')
