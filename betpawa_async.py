"""
Working BetPawa Scraper using Playwright (Async version)
Fetches real odds from betpawa.co.ke
"""
import re
import time
import asyncio
from typing import List, Dict, Any


class AsyncBetPawaScraper:
    """Scrapes BetPawa Kenya for soccer odds using Playwright async."""
    
    BASE_URL = "https://www.betpawa.co.ke"
    
    async def fetch_odds(self) -> List[Dict[str, Any]]:
        """Fetch odds from BetPawa."""
        playwright = None
        browser = None
        page = None
        
        try:
            from playwright.async_api import async_playwright
            
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            page.set_default_timeout(30000)
            
            url = f"{self.BASE_URL}/events?categoryId=2&marketId=1X2"
            print(f"Fetching {url}...")
            
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(5000)
            
            text = await page.evaluate("document.body.innerText")
            return self._parse_text(text)
        except Exception as e:
            print(f"BetPawa fetch error: {e}")
            return []
        finally:
            if page:
                await page.close()
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
    
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
    async def test():
        scraper = AsyncBetPawaScraper()
        odds = await scraper.fetch_odds()
        print(f"\nFetched {len(odds)} matches from BetPawa")
        for match in odds[:5]:
            print(match)
    
    asyncio.run(test())
