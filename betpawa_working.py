"""
Working BetPawa Scraper using Playwright
Fetches real odds from betpawa.co.ke
"""
import re
import time
from typing import List, Dict, Any

class BetPawaScraper:
    """Scrapes BetPawa Kenya for soccer odds using Playwright."""
    
    BASE_URL = "https://www.betpawa.co.ke"
    
    def __init__(self):
        self.browser = None
        self.page = None
    
    def _init_browser(self):
        """Initialize Playwright browser."""
        try:
            from playwright.sync_api import sync_playwright
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=True)
            self.page = self.browser.new_page()
            self.page.set_default_timeout(30000)
            return True
        except Exception as e:
            print(f"Failed to init browser: {e}")
            return False
    
    def _close_browser(self):
        """Close browser."""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self._playwright:
                self._playwright.stop()
        except:
            pass
        finally:
            self.page = None
            self.browser = None
            self._playwright = None
    
    def fetch_odds(self) -> List[Dict[str, Any]]:
        """Fetch odds from BetPawa."""
        if not self._init_browser():
            return []
        
        try:
            url = f"{self.BASE_URL}/events?categoryId=2&marketId=1X2"
            print(f"Fetching {url}...")
            
            self.page.goto(url, wait_until="domcontentloaded")
            time.sleep(5)
            
            text = self.page.evaluate("document.body.innerText")
            return self._parse_text(text)
        except Exception as e:
            print(f"BetPawa fetch error: {e}")
            return []
        finally:
            self._close_browser()
    
    def _parse_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse BetPawa page text into structured data."""
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
                    elif not league and any(x in next_line for x in ['Football', 'Basketball', 'Tennis', 'Rugby']):
                        league = next_line
                    elif next_line == '1':
                        if j + 1 < len(lines):
                            try:
                                odds['home'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == 'X':
                        if j + 1 < len(lines):
                            try:
                                odds['draw'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == '2':
                        if j + 1 < len(lines):
                            try:
                                odds['away'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif '1X2' in next_line or 'Full Time' in next_line:
                        pass
                    elif any(x in next_line for x in ['Football', 'Basketball', 'Tennis', 'Rugby']):
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


if __name__ == "__main__":
    scraper = BetPawaScraper()
    odds = scraper.fetch_odds()
    print(f"\nFetched {len(odds)} matches from BetPawa")
    for match in odds[:5]:
        print(match)
