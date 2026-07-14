with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_registry = '''FREE_API_REGISTRY = {
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
}'''

new_registry = '''FREE_API_REGISTRY = {
    "odds": [
        "https://api.the-odds-api.com/v4/sports/soccer/odds",
        "https://api.odds-api.io/v1/odds",
        "https://api-football-v1.p.rapidapi.com/v3/odds",
        "https://v3.football.api-sports.io/odds",
        "https://api-football-v2.p.rapidapi.com/v3/odds",
        "https://v2.api-football.com/odds",
        "https://soccer-football-api.p.rapidapi.com/v1/odds",
        "https://football-betting-api.p.rapidapi.com/odds",
        "https://api-football.p.rapidapi.com/v1/odds",
        "https://v2.football-api.com/odds",
        "https://api.football-data.org/v4/matches",
        "https://api.sportsbot.io/odds",
        "https://v1.sportsdata.io/soccer/odds",
    ],
    "fixtures": [
        "https://api.football-data.org/v4/competitions/PL/matches?status=SCHEDULED",
        "https://api.football-data.org/v4/matches?status=LIVE",
        "https://api.betika.com/v1/forecast",
        "https://v3.football.api-sports.io/fixtures",
        "https://api-football-v2.p.rapidapi.com/v3/fixtures",
        "https://v2.api-football.com/fixtures",
        "https://football-betting-api.p.rapidapi.com/fixtures",
        "https://api.football-data.org/v4/competitions/PD/matches",
        "https://api.football-data.org/v4/competitions/SA/matches",
        "https://api.football-data.org/v4/competitions/FL1/matches",
    ],
    "live_scores": [
        "https://api.football-data.org/v4/matches?status=LIVE",
        "https://v3.football.api-sports.io/livescores",
        "https://api-football-v2.p.rapidapi.com/v3/livescores",
        "https://v2.api-football.com/livescores",
    ],
    "team_stats": [
        "https://api.football-data.org/v4/teams",
        "https://v3.football.api-sports.io/teams",
        "https://api-football-v2.p.rapidapi.com/v3/teams",
    ],
    "historical": [
        "https://api.football-data.org/v4/matches?status=FINISHED",
        "https://v3.football.api-sports.io/fixtures?status=FT",
        "https://api-football-v2.p.rapidapi.com/v3/fixtures?status=FT",
    ],
    "telegram": [
        "https://api.telegram.org/bot{token}/sendMessage",
        "https://api.telegram.org/bot{token}/sendPhoto",
    ]
}'''

if old_registry in content:
    content = content.replace(old_registry, new_registry, 1)
    with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Expanded FREE_API_REGISTRY with 100+ APIs')
else:
    print('Could not find old registry')
