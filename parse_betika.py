"""
Betika Parser - Extracts structured odds from Betika page text
"""
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_betika_text(text):
    """Parse Betika page text into structured match data."""
    matches = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for league line with bullet separator
        if '•' in line and not any(x in line for x in ['Login', 'Register', 'Home']):
            league = line
            
            # Next lines should be: date, home, away, odds
            j = i + 1
            while j < len(lines) and j < i + 10:
                next_line = lines[j].strip()
                
                if not next_line:
                    j += 1
                    continue
                
                # Look for date pattern
                date_match = re.match(r'(\d{1,2}/\d{1,2},\s*\d{1,2}:\d{2})', next_line)
                if date_match:
                    kickoff = date_match.group(1)
                    
                    home = None
                    away = None
                    odds = {}
                    
                    k = j + 1
                    while k < len(lines) and k < j + 10:
                        odd_line = lines[k].strip()
                        
                        if not odd_line:
                            k += 1
                            continue
                        
                        # Skip menu items
                        if odd_line in ['Login', 'Register', 'Home', 'Jackpots', 'Shikisha Bet', 
                                        'Aviator', 'World Cup Hub', 'New', 'Ligi Bigi', 'Casino',
                                        'Promotions', 'Virtuals', 'Betika Fasta', 'Crash Games',
                                        'Live Score', 'App', 'Print Matches', 'Search', 'Soccer',
                                        'Table Tennis', 'Boxing', 'Aussie Rules', 'Rugby', 'Basketball',
                                        'ESport', 'Tennis', 'Cricket', 'Baseball', 'Handball',
                                        'Volleyball', 'Snooker', 'Zoom Soccer', 'Highlights',
                                        'Upcoming', 'Countries', 'Filters', 'Today', 'Teams',
                                        'Load more', 'Back to Top']:
                            k += 1
                            continue
                        
                        # Skip "+XX Markets"
                        if re.match(r'\+(\d+) Markets', odd_line):
                            k += 1
                            continue
                        
                        # Parse odds
                        if re.match(r'\d+\.\d+', odd_line):
                            if 'home' not in odds:
                                odds['home'] = float(odd_line)
                            elif 'draw' not in odds:
                                odds['draw'] = float(odd_line)
                            elif 'away' not in odds:
                                odds['away'] = float(odd_line)
                                break  # Got all odds
                        elif not home and odd_line not in ['1', 'X', '2']:
                            home = odd_line
                        elif home and not away and odd_line not in ['1', 'X', '2']:
                            away = odd_line
                        
                        k += 1
                    
                    if home and away and 'home' in odds:
                        matches.append({
                            'home_team': home,
                            'away_team': away,
                            'league': league,
                            'kickoff': kickoff,
                            'odds': odds,
                            'bookmaker': 'Betika'
                        })
                    
                    i = k - 1  # Skip ahead
                    break
            
            i += 1
        else:
            i += 1
    
    return matches


# Test with actual Betika data
text = """Login
Register
Home
Live (163)
Jackpots
Shikisha Bet (1)
Aviator
World Cup Hub
New
Ligi Bigi
New
Casino
New
Promotions (16)
Virtuals
Betika Fasta
Crash Games
Live Score
App
Print Matches
Search
Soccer
Table Tennis
Boxing
Aussie Rules
Rugby
Basketball
ESport Counter-Strike
ESport King of Glory
eSoccer
ESport Call of Duty
Tennis
Cricket
Baseball
ESport League of Legends
Handball
Volleyball
Snooker
Zoom Soccer
Highlights
Upcoming
Countries
Zoom Soccer
Jackpots
New
Turbo
Filters
Today
Highlights
1x2
Teams
1
X
2
International • FIFA World Cup...
14/07, 21:00
France
Spain
2.45
3.20
3.25
+94 Markets
International Clubs • UEFA Cha...
14/07, 17:00
Kuopion Palloseur...
Fk Vardar Skopje
1.50
4.80
6.20
+80 Markets
International Clubs • UEFA Cha...
14/07, 18:00
Inter Club De Esc...
Lincoln Red Imps
1.71
4.40
4.40
+72 Markets
International Clubs • UEFA Cha...
14/07, 18:00
Fc Iberia 1999
Flora Tallinn
1.52
4.80
5.80
+72 Markets
International Clubs • UEFA Cha...
14/07, 19:00
Riga Fc
Fc Ararat Armenia...
1.72
3.95
4.90
+72 Markets"""

matches = parse_betika_text(text)
print(f'Parsed {len(matches)} matches')
for m in matches:
    print(m)
