import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_betpawa_text(text):
    """Parse BetPawa page text into structured match data."""
    matches = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for time pattern
        time_match = re.match(r'(\d{1,2}:\d{2}\s*(?:am|pm)\s*\w+\s*\d{1,2}/\d{1,2})', line)
        if time_match:
            kickoff = time_match.group(1)
            
            home = None
            away = None
            league = None
            odds = {}
            
            j = i + 1
            while j < len(lines) and j < i + 20:
                next_line = lines[j].strip()
                
                if not next_line:
                    j += 1
                    continue
                
                if not home:
                    home = next_line
                elif not away:
                    away = next_line
                elif not league and ('Football' in next_line or 'Basketball' in next_line or 'Tennis' in next_line):
                    league = next_line
                elif next_line == '1':
                    if j + 1 < len(lines):
                        try:
                            odds['home'] = float(lines[j + 1].strip())
                            j += 1  # Skip the odds line
                        except:
                            pass
                elif next_line == 'X':
                    if j + 1 < len(lines):
                        try:
                            odds['draw'] = float(lines[j + 1].strip())
                            j += 1  # Skip the odds line
                        except:
                            pass
                elif next_line == '2':
                    if j + 1 < len(lines):
                        try:
                            odds['away'] = float(lines[j + 1].strip())
                            j += 1  # Skip the odds line
                        except:
                            pass
                elif next_line == '1X2 | Full Time':
                    pass
                elif 'Football' in next_line or 'Basketball' in next_line or 'Tennis' in next_line:
                    break
                else:
                    if league and 'home' in odds:
                        break
                
                j += 1
            
            if home and away and 'home' in odds:
                matches.append({
                    'home_team': home,
                    'away_team': away,
                    'league': league,
                    'kickoff': kickoff,
                    'odds': odds,
                    'bookmaker': 'BetPawa'
                })
        
        i += 1
    
    return matches


# Test with actual data
text = """LOGIN
JOIN NOW
UPCOMING
POPULAR
LIVE
OUTRIGHTS
Leagues
Markets
Show 1UP & 2UP
5:00 pm Tue 14/07
SV Wehen Wiesbaden
Fagiano Okayama

Football / International / Club Friendly Games

1
2.91
X
3.74
2
2.18
5:00 pm Tue 14/07
FK Dukla Banská Bystrica
Hapoel Tel Aviv

Football / International / Club Friendlies

1
5.21
X
4.17
2
1.57"""

matches = parse_betpawa_text(text)
print(f'Parsed {len(matches)} matches')
for m in matches:
    print(m)
