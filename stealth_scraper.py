#!/usr/bin/env python3
"""
Stealth Scraping Engine - Professional-grade undetectable scraping.
Uses curl_cffi, Playwright stealth, residential proxy rotation, and human behavior emulation.
"""

import asyncio
import hashlib
import json
import logging
import os
import random
import re
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    CURL_CFFI_AVAILABLE = False

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    from playwright_stealth import stealth_async
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    stealth_async = None

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

log = logging.getLogger("LHM.Stealth")

# ======================================================================
# CONFIGURATION
# ======================================================================

class StealthConfig:
    TLS_IMPERSONATE = "chrome120"
    VIEWPORT_MIN_WIDTH = 1024
    VIEWPORT_MAX_WIDTH = 1920
    VIEWPORT_MIN_HEIGHT = 768
    VIEWPORT_MAX_HEIGHT = 1080
    MIN_CLICK_DELAY = 0.8
    MAX_CLICK_DELAY = 2.5
    MIN_SCROLL_DELAY = 0.3
    MAX_SCROLL_DELAY = 1.2
    MIN_PAGE_LOAD_DELAY = 2.0
    MAX_PAGE_LOAD_DELAY = 8.0
    MOUSE_MOVE_DURATION_MIN = 0.4
    MOUSE_MOVE_DURATION_MAX = 1.2
    MOUSE_MICRO_JITTER = 0.05
    PROXY_ROTATE_INTERVAL = 1800
    PROXY_POOL_SIZE = 20
    SESSION_MIN_LIFETIME = 600
    SESSION_MAX_LIFETIME = 3600
    REQUEST_LAMBDA = 3.0
    RETRY_BASE_DELAY = 5.0
    RETRY_MAX_DELAY = 60.0
    PERSIST_SESSIONS = True
    SESSION_DIR = os.path.join(os.path.dirname(__file__), "stealth_sessions")
    ENABLE_WEBDRIVER_PATCH = True
    ENABLE_CHROME_PATCH = True
    ENABLE_IFRAME_PATCH = True
    ENABLE_PERMISSIONS_PATCH = True
    ENABLE_WEBGL_PATCH = True
    ENABLE_AUDIO_PATCH = True
    ENABLE_PLUGINS_PATCH = True
    ENABLE_LANGUAGES_PATCH = True
    ENABLE_TIMEZONE_PATCH = True
    ENABLE_GEOLOCATION_PATCH = True


# ======================================================================
# RESIDENTIAL PROXY MANAGER
# ======================================================================

class ResidentialProxyManager:
    def __init__(self, config: StealthConfig = None):
        self.config = config or StealthConfig()
        self._pool: List[Dict[str, str]] = []
        self._current_idx = 0
        self._last_rotate = time.time()
        self._health: Dict[str, bool] = {}
        self._lock = asyncio.Lock()

    async def initialize(self):
        await self._fetch_free_proxies()
        if not self._pool:
            log.warning("No residential proxies loaded; running direct")
            self._pool = [{}]

    async def _fetch_free_proxies(self):
        sources = [
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
            "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
            "https://raw.githubusercontent.com/HyperBeam/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/HyperBeam/proxy-list/main/https.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/UserR3D/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/UserR3D/proxy-list/main/proxies/https.txt",
            "https://raw.githubusercontent.com/ProxyScrape/proxy-list/main/http.txt",
            "https://raw.githubusercontent.com/ProxyScrape/proxy-list/main/https.txt",
        ]
        proxies = []
        seen = set()
        if AIOHTTP_AVAILABLE:
            async with aiohttp.ClientSession() as session:
                for url in sources:
                    try:
                        async with session.get(url, timeout=5) as resp:
                            if resp.status == 200:
                                text = await resp.text()
                                for line in text.splitlines():
                                    line = line.strip()
                                    if line and ":" in line and line not in seen:
                                        seen.add(line)
                                        proxies.append({"http": f"http://{line}", "https": f"http://{line}"})
                    except Exception:
                        continue
        self._pool = proxies[:self.config.PROXY_POOL_SIZE]
        log.info(f"Loaded {len(self._pool)} residential proxies")

    async def get_proxy(self) -> Dict[str, str]:
        async with self._lock:
            now = time.time()
            if now - self._last_rotate > self.config.PROXY_ROTATE_INTERVAL:
                await self._rotate_proxy()
            if not self._pool:
                return {}
            proxy = self._pool[self._current_idx % len(self._pool)]
            self._current_idx += 1
            return proxy

    async def _rotate_proxy(self):
        self._current_idx = (self._current_idx + 1) % max(1, len(self._pool))
        self._last_rotate = time.time()


# ======================================================================
# HUMAN BEHAVIOR EMULATOR
# ======================================================================

class HumanBehavior:
    @staticmethod
    def poisson_delay(lam: float = 3.0) -> float:
        return max(0.1, random.expovariate(1.0 / lam))

    @staticmethod
    def lognormal_delay(mean: float = 0.0, sigma: float = 0.5) -> float:
        val = random.lognormal(mean, sigma)
        return max(0.1, min(val, 10.0))

    @staticmethod
    def bezier_move(x1: float, y1: float, x2: float, y2: float, duration: float) -> List[Tuple[float, float]]:
        points = []
        steps = max(10, int(duration * 60))
        cx1 = x1 + random.uniform(-50, 50)
        cy1 = y1 + random.uniform(-50, 50)
        cx2 = x2 + random.uniform(-50, 50)
        cy2 = y2 + random.uniform(-50, 50)
        for i in range(steps):
            t = i / steps
            bx = (1-t)**3*x1 + 3*(1-t)**2*t*cx1 + 3*(1-t)*t**2*cx2 + t**3*x2
            by = (1-t)**3*y1 + 3*(1-t)**2*t*cy1 + 3*(1-t)*t**2*cy2 + t**3*y2
            bx += random.gauss(0, StealthConfig.MOUSE_MICRO_JITTER)
            by += random.gauss(0, StealthConfig.MOUSE_MICRO_JITTER)
            points.append((bx, by))
        return points

    @staticmethod
    def random_scroll_distance() -> int:
        return random.randint(50, 300)

    @staticmethod
    def random_scroll_direction() -> str:
        return random.choice(["down", "down", "down", "up"])

    @staticmethod
    def get_viewport() -> Tuple[int, int]:
        w = random.randint(StealthConfig.VIEWPORT_MIN_WIDTH, StealthConfig.VIEWPORT_MAX_WIDTH)
        h = random.randint(StealthConfig.VIEWPORT_MIN_HEIGHT, StealthConfig.VIEWPORT_MAX_HEIGHT)
        return w, h

    @staticmethod
    def get_user_agent() -> str:
        agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/120.0",
        ]
        return random.choice(agents)

    @staticmethod
    def get_sec_ch_ua() -> str:
        return '"Chromium";v="120", "Google Chrome";v="120", "Not;A=Brand";v="99"'

    @staticmethod
    def get_accept_encoding() -> str:
        return "gzip, deflate, br"

    @staticmethod
    def get_accept() -> str:
        return "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"

    @staticmethod
    def get_accept_language() -> str:
        langs = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "en-US,en;q=0.9,fr;q=0.8",
            "en-US,en;q=0.9,es;q=0.8",
            "en-US,en;q=0.9,de;q=0.8",
            "en-US,en;q=0.9,pt;q=0.8",
            "en-US,en;q=0.9,it;q=0.8",
            "en-US,en;q=0.9,ru;q=0.8",
            "en-US,en;q=0.9,sw;q=0.8",
            "en-US,en;q=0.9,af;q=0.8",
        ]
        return random.choice(langs)

    @staticmethod
    def get_headers(extra: Dict[str, str] = None) -> Dict[str, str]:
        headers = {
            "host": "",
            "connection": "keep-alive",
            "cache-control": "max-age=0",
            "sec-ch-ua": HumanBehavior.get_sec_ch_ua(),
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "upgrade-insecure-requests": "1",
            "user-agent": HumanBehavior.get_user_agent(),
            "accept": HumanBehavior.get_accept(),
            "sec-fetch-site": random.choice(["none", "same-origin", "cross-site"]),
            "sec-fetch-mode": random.choice(["navigate", "cors", "no-cors"]),
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "accept-encoding": HumanBehavior.get_accept_encoding(),
            "accept-language": HumanBehavior.get_accept_language(),
        }
        if extra:
            headers.update(extra)
        return headers

    @staticmethod
    async def human_delay(min_sec: float, max_sec: float):
        delay = random.uniform(min_sec, max_sec)
        delay += random.gauss(0, 0.1)
        delay = max(0.05, delay)
        await asyncio.sleep(delay)


# ======================================================================
# CURL_CFFI STEALTH CLIENT
# ======================================================================

class CurlCffiStealthClient:
    def __init__(self, config: StealthConfig = None, proxy_manager: ResidentialProxyManager = None):
        self.config = config or StealthConfig()
        self.proxy_manager = proxy_manager
        self.session = None
        self._session_start = time.time()
        self._session_lifetime = random.randint(
            self.config.SESSION_MIN_LIFETIME,
            self.config.SESSION_MAX_LIFETIME
        )

    async def _ensure_session(self):
        if self.session is None or time.time() - self._session_start > self._session_lifetime:
            await self._create_session()

    async def _create_session(self):
        if not CURL_CFFI_AVAILABLE:
            raise RuntimeError("curl_cffi not installed")
        proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else {}
        self.session = curl_requests.Session(
            impersonate=self.config.TLS_IMPERSONATE,
            proxies=proxy if proxy else None,
        )
        self._session_start = time.time()
        self._session_lifetime = random.randint(
            self.config.SESSION_MIN_LIFETIME,
            self.config.SESSION_MAX_LIFETIME
        )
        log.debug(f"Created new curl_cffi session with TLS={self.config.TLS_IMPERSONATE}")

    async def get(self, url: str, headers: Dict[str, str] = None, timeout: int = 30):
        await self._ensure_session()
        await HumanBehavior.human_delay(self.config.MIN_CLICK_DELAY, self.config.MAX_CLICK_DELAY)
        hdrs = HumanBehavior.get_headers(headers)
        try:
            resp = await asyncio.to_thread(
                self.session.get, url, headers=hdrs, timeout=timeout, allow_redirects=True
            )
            return resp
        except Exception as e:
            log.warning(f"curl_cffi GET failed: {e}")
            return None

    async def post(self, url: str, data=None, json_data=None, headers: Dict[str, str] = None, timeout: int = 30):
        await self._ensure_session()
        await HumanBehavior.human_delay(self.config.MIN_CLICK_DELAY, self.config.MAX_CLICK_DELAY)
        hdrs = HumanBehavior.get_headers(headers)
        try:
            resp = await asyncio.to_thread(
                self.session.post, url, data=data, json=json_data, headers=hdrs, timeout=timeout, allow_redirects=True
            )
            return resp
        except Exception as e:
            log.warning(f"curl_cffi POST failed: {e}")
            return None


# ======================================================================
# PLAYWRIGHT STEALTH CLIENT
# ======================================================================

class PlaywrightStealthClient:
    def __init__(self, config: StealthConfig = None, proxy_manager: ResidentialProxyManager = None):
        self.config = config or StealthConfig()
        self.proxy_manager = proxy_manager
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None

    async def _ensure_browser(self):
        if self._browser is None or not self._browser.is_connected():
            await self._launch()

    async def _launch(self):
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("playwright not installed")
        self._playwright = await async_playwright().start()
        proxy = await self.proxy_manager.get_proxy() if self.proxy_manager else None
        proxy_url = None
        if proxy and "http" in proxy:
            proxy_url = proxy["http"].replace("http://", "")
        launch_args = {
            "headless": True,
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-infobars",
                "--disable-session-crashed-bubble",
                "--disable-popup-blocking",
                "--disable-translate",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-accelerated-2d-canvas",
                "--disable-accelerated-jpeg-decoding",
                "--disable-accelerated-mjpeg-decode",
                "--disable-accelerated-video-decode",
                "--disable-async-dns",
                "--disable-automation",
                "--disable-cache",
                "--disable-component-update",
                "--disable-crash-reporter",
                "--disable-domain-reliability",
                "--disable-features=AudioServiceOutOfProcess",
                "--disable-features=OptimizationGuideModelDownloading",
                "--disable-features=Translate",
                "--disable-hang-monitor",
                "--disable-logging",
                "--disable-memory-pressure-compositor",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--disable-threaded-animation",
                "--disable-threaded-scrolling",
                "--disable-unified-media-pipeline",
                "--disable-zygote-as-module-launcher",
                "--enable-features=NetworkService,NetworkServiceInProcess",
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
                "--in-process-gpu",
                "--log-level=3",
                "--no-first-run",
                "--no-pings",
                "--no-zygote",
                "--password-store=basic",
                "--remote-allow-origins=*",
                "--safebrowsing-disable-auto-update",
                "--single-process",
                "--use-mock-keychain",
                "--window-size=1920,1080",
            ]
        }
        if proxy_url:
            launch_args["proxy"] = {"server": proxy_url}
        self._browser = await self._playwright.chromium.launch(**launch_args)
        w, h = HumanBehavior.get_viewport()
        self._context = await self._browser.new_context(
            viewport={"width": w, "height": h},
            user_agent=HumanBehavior.get_user_agent(),
            locale="en-US",
            timezone_id="America/New_York",
            geolocation={"latitude": 40.7128, "longitude": -74.0060},
            permissions=["geolocation"],
            extra_http_headers={
                "Accept-Language": HumanBehavior.get_accept_language(),
            }
        )
        if stealth_async and self._page:
            await stealth_async(self._page)
        log.debug("Playwright stealth browser launched")

    async def new_page(self):
        await self._ensure_browser()
        page = await self._context.new_page()
        if stealth_async:
            await stealth_async(page)
        self._page = page
        return page

    async def close(self):
        try:
            if self._page:
                await self._page.close()
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None


# ======================================================================
# STEALTH SCRAPER ORCHESTRATOR
# ======================================================================

class StealthScraperOrchestrator:
    def __init__(self, config: StealthConfig = None):
        self.config = config or StealthConfig()
        self.proxy_manager = ResidentialProxyManager(self.config)
        self.curl_client = CurlCffiStealthClient(self.config, self.proxy_manager)
        self.playwright_client = PlaywrightStealthClient(self.config, self.proxy_manager)
        self._last_request_time = 0
        self._request_count = 0
        self._session_id = secrets.token_hex(8)

    async def initialize(self):
        await self.proxy_manager.initialize()

    async def fetch(self, url: str, method: str = "GET", data=None, json_data=None,
                    use_browser: bool = None, headers: Dict[str, str] = None,
                    timeout: int = 30, retries: int = 3) -> Optional[Any]:
        await self._human_pacing()
        if use_browser is None:
            use_browser = self._needs_browser(url)
        last_error = None
        for attempt in range(retries):
            try:
                if use_browser:
                    result = await self._fetch_with_browser(url, method, data, json_data, headers, timeout)
                else:
                    result = await self._fetch_with_curl(url, method, data, json_data, headers, timeout)
                if result is not None:
                    return result
            except Exception as e:
                last_error = e
                log.warning(f"Stealth fetch attempt {attempt+1}/{retries} failed: {e}")
            await self.proxy_manager._rotate_proxy()
            await HumanBehavior.human_delay(
                self.config.RETRY_BASE_DELAY * (2 ** attempt),
                min(self.config.RETRY_MAX_DELAY, self.config.RETRY_BASE_DELAY * (2 ** attempt) * 2)
            )
        log.error(f"All {retries} stealth fetch attempts failed for {url}: {last_error}")
        return None

    async def _human_pacing(self):
        now = time.time()
        elapsed = now - self._last_request_time
        min_delay = HumanBehavior.poisson_delay(self.config.REQUEST_LAMBDA)
        if elapsed < min_delay:
            await asyncio.sleep(min_delay - elapsed)
        self._last_request_time = time.time()
        self._request_count += 1

    @staticmethod
    def _needs_browser(url: str) -> bool:
        js_heavy = [
            "betpawa", "betika", "betway", "sportybet", "betwinner", "22bet",
            "melbet", "1xbet", "parimatch", "bet365", "bwin", "unibet",
            "paddypower", "skybet", "ladbrokes", "coral", "betfred",
            "marathonbet", "fonbet", "leon", "betclic", "pmu", "zebet",
            "fdj", "smarkets", "matchbook", "betdaq", "pinnacle",
        ]
        url_lower = url.lower()
        return any(j in url_lower for j in js_heavy)

    async def _fetch_with_curl(self, url, method, data, json_data, headers, timeout):
        if not CURL_CFFI_AVAILABLE:
            return None
        if method.upper() == "GET":
            resp = await self.curl_client.get(url, headers, timeout)
        else:
            resp = await self.curl_client.post(url, data, json_data, headers, timeout)
        if resp is not None and resp.status_code == 200:
            return resp
        return None

    async def _fetch_with_browser(self, url, method, data, json_data, headers, timeout):
        if not PLAYWRIGHT_AVAILABLE:
            return None
        page = await self.playwright_client.new_page()
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=timeout * 1000)
            await HumanBehavior.human_delay(self.config.MIN_PAGE_LOAD_DELAY, self.config.MAX_PAGE_LOAD_DELAY)
            await self._human_scroll(page)
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout * 1000)
            await HumanBehavior.human_delay(1.0, 3.0)
            content = await page.content()
            return {"text": content, "url": page.url, "status": resp.status if resp else 0}
        except Exception as e:
            log.warning(f"Browser fetch failed: {e}")
            return None
        finally:
            await page.close()

    async def _human_scroll(self, page):
        scrolls = random.randint(1, 4)
        for _ in range(scrolls):
            distance = HumanBehavior.random_scroll_distance()
            direction = HumanBehavior.random_scroll_direction()
            if direction == "down":
                await page.mouse.wheel(0, distance)
            else:
                await page.mouse.wheel(0, -distance)
            await HumanBehavior.human_delay(self.config.MIN_SCROLL_DELAY, self.config.MAX_SCROLL_DELAY)

    async def close(self):
        await self.playwright_client.close()


# ======================================================================
# BETPAWA STEALTH SCRAPER
# ======================================================================

class BetPawaStealthScraper:
    BASE_URL = "https://www.betpawa.co.ke"
    EVENTS_URL = "https://www.betpawa.co.ke/events?categoryId=2&marketId=1X2"
    
    def __init__(self, config=None, undetectable=None):
        self.config = config or StealthConfig()
        self.orchestrator = StealthScraperOrchestrator(self.config)
        self._logged_in = False
        self._token = None
        self._undetectable = undetectable
    
    async def initialize(self):
        if self._undetectable is None:
            try:
                import deepseek_python_20260707_a6bd19 as lhm
                self._undetectable = lhm.UndetectableScraper()
                await self._undetectable.initialize()
            except Exception as e:
                log.warning(f"Undetectable scraper init failed: {e}")
                self._undetectable = None
        else:
            try:
                await self._undetectable.initialize()
            except Exception as e:
                log.warning(f"Undetectable scraper init failed: {e}")
    
    async def _get_headers(self, extra=None):
        headers = {
            "host": "www.betpawa.co.ke",
            "connection": "keep-alive",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
        }
        if self._token:
            headers["authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers
    
    async def fetch_odds(self, sport: str = "soccer") -> List[Dict[str, Any]]:
        odds = []
        try:
            if self._undetectable:
                content = await self._undetectable.scrape_url(self.EVENTS_URL)
                if content:
                    odds = self._parse_betpawa_text(content)
                    if odds:
                        log.info(f"BetPawa undetectable: loaded {len(odds)} odds")
                        return odds
            
            # Fallback to orchestrator
            resp = await self.orchestrator.fetch(
                f"{self.BASE_URL}/sports/{sport}/odds",
                headers=await self._get_headers(),
                use_browser=True,
            )
            if resp and isinstance(resp, dict) and "text" in resp:
                if BS4_AVAILABLE:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp["text"], "lxml")
                    odds = self._parse_odds_page(soup)
                else:
                    odds = self._parse_odds_text(resp["text"])
        except Exception as e:
            log.error(f"BetPawa odds fetch error: {e}")
        return odds
    
    def _parse_betpawa_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse BetPawa page text into structured match data."""
        odds = []
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
                match_odds = {}
                
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
                                match_odds['home'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == 'X':
                        if j + 1 < len(lines):
                            try:
                                match_odds['draw'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == '2':
                        if j + 1 < len(lines):
                            try:
                                match_odds['away'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif '1X2' in next_line or 'Full Time' in next_line:
                        pass
                    elif any(x in next_line for x in ['Football', 'Basketball', 'Tennis', 'Rugby']):
                        break
                    else:
                        if league and 'home' in match_odds:
                            break
                    
                    j += 1
                
                if home and away and 'home' in match_odds:
                    odds.append({
                        "id": f"bp_{hashlib.md5(f'{home}{away}{kickoff}'.encode()).hexdigest()[:8]}",
                        "home_team": home,
                        "away_team": away,
                        "league": league,
                        "kickoff": kickoff,
                        "bookmakers": [
                            {
                                "name": "BetPawa",
                                "markets": [
                                    {
                                        "key": "h2h",
                                        "outcomes": [
                                            {"name": "Home", "price": match_odds.get('home', 0)},
                                            {"name": "Draw", "price": match_odds.get('draw', 0)},
                                            {"name": "Away", "price": match_odds.get('away', 0)},
                                        ]
                                    }
                                ]
                            }
                        ]
                    })
            
            i += 1
        
        return odds
    
    def _parse_odds_page(self, soup) -> List[Dict[str, Any]]:
        # Keep existing BS4 parser as fallback
        odds = []
        try:
            match_rows = soup.select(".match-row, .event-row, [data-event-id]")
            for row in match_rows:
                try:
                    event_id = row.get("data-event-id", "")
                    home_elem = row.select_one(".home-team, .team-home, [data-home]")
                    away_elem = row.select_one(".away-team, .team-away, [data-away]")
                    home = home_elem.text.strip() if home_elem else ""
                    away = away_elem.text.strip() if away_elem else ""
                    odds_elem = row.select_one(".odds, .market-odds, [data-odds]")
                    odds_text = odds_elem.text.strip() if odds_elem else ""
                    if home and away:
                        odds.append({
                            "id": event_id or f"bp_{hashlib.md5(f'{home}{away}'.encode()).hexdigest()[:8]}",
                            "home_team": home,
                            "away_team": away,
                            "bookmakers": [
                                {
                                    "name": "BetPawa",
                                    "markets": [
                                        {
                                            "key": "h2h",
                                            "outcomes": [
                                                {"name": "Home", "price": self._extract_odds(odds_text, 1)},
                                                {"name": "Draw", "price": self._extract_odds(odds_text, 2)},
                                                {"name": "Away", "price": self._extract_odds(odds_text, 3)},
                                            ]
                                        }
                                    ]
                                }
                            ]
                        })
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"BetPawa parse error: {e}")
        return odds
    
    def _parse_odds_text(self, text: str) -> List[Dict[str, Any]]:
        # Fallback text parser
        return self._parse_betpawa_text(text)
    
    def _extract_odds(self, text, position):
        import re
        odds = re.findall(r'\d+\.\d+', text)
        if len(odds) >= position:
            return float(odds[position - 1])
        return 0.0

    def _parse_odds_page(self, soup) -> List[Dict[str, Any]]:
        odds = []
        try:
            match_rows = soup.select(".match-row, .event-row, [data-event-id]")
            for row in match_rows:
                try:
                    event_id = row.get("data-event-id", "")
                    home_elem = row.select_one(".home-team, .team-home, [data-home]")
                    away_elem = row.select_one(".away-team, .team-away, [data-away]")
                    home = home_elem.text.strip() if home_elem else ""
                    away = away_elem.text.strip() if away_elem else ""
                    odds_elem = row.select_one(".odds, .market-odds, [data-odds]")
                    odds_text = odds_elem.text.strip() if odds_elem else ""
                    if home and away:
                        odds.append({
                            "id": event_id or f"bp_{hashlib.md5(f'{home}{away}'.encode()).hexdigest()[:8]}",
                            "home_team": home,
                            "away_team": away,
                            "bookmakers": [
                                {
                                    "name": "BetPawa",
                                    "markets": [
                                        {
                                            "key": "h2h",
                                            "outcomes": [
                                                {"name": "Home", "price": self._extract_odds(odds_text, 1)},
                                                {"name": "Draw", "price": self._extract_odds(odds_text, 2)},
                                                {"name": "Away", "price": self._extract_odds(odds_text, 3)},
                                            ]
                                        }
                                    ]
                                }
                            ]
                        })
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"BetPawa parse error: {e}")
        return odds

    def _parse_odds_text(self, text: str) -> List[Dict[str, Any]]:
        odds = []
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if "vs" in line.lower() or "v" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    odds.append({
                        "id": f"bp_{hashlib.md5(line.encode()).hexdigest()[:8]}",
                        "home_team": parts[0],
                        "away_team": parts[-1],
                        "bookmakers": []
                    })
        return odds

    @staticmethod
    def _extract_odds(text: str, position: int) -> float:
        try:
            parts = text.split()
            if len(parts) >= position:
                return float(parts[position - 1])
        except Exception:
            pass
        return 0.0

    async def close(self):
        await self.orchestrator.close()


# ======================================================================
# BETIKA STEALTH SCRAPER
# ======================================================================

class BetikaStealthScraper:
    BASE_URL = "https://www.betika.com"
    ODDS_URL = "https://www.betika.com/en-ke/sports/soccer/odds"
    
    def __init__(self, config=None, undetectable=None):
        self.config = config or StealthConfig()
        self.orchestrator = StealthScraperOrchestrator(self.config)
        self._logged_in = False
        self._token = None
        self._undetectable = undetectable
    
    async def initialize(self):
        if self._undetectable is None:
            try:
                import deepseek_python_20260707_a6bd19 as lhm
                self._undetectable = lhm.UndetectableScraper()
                await self._undetectable.initialize()
            except Exception as e:
                log.warning(f"Undetectable scraper init failed: {e}")
                self._undetectable = None
        else:
            try:
                await self._undetectable.initialize()
            except Exception as e:
                log.warning(f"Undetectable scraper init failed: {e}")
    
    async def _get_headers(self, extra=None):
        headers = {
            "host": "www.betika.com",
            "connection": "keep-alive",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
        }
        if self._token:
            headers["authorization"] = f"Bearer {self._token}"
        if extra:
            headers.update(extra)
        return headers
    
    async def fetch_odds(self, sport: str = "soccer") -> List[Dict[str, Any]]:
        odds = []
        try:
            # Strategy 1: Use undetectable scraper with Playwright
            if self._undetectable:
                content = await self._undetectable.scrape_url(self.ODDS_URL)
                if content:
                    odds = self._parse_betika_text(content)
                    if odds:
                        log.info(f"Betika undetectable: loaded {len(odds)} odds")
                        return odds
            
            # Strategy 2: Direct Playwright with extended wait
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                        locale="en-US",
                        timezone_id="Africa/Nairobi",
                    )
                    await context.add_init_script("""
                        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                        Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                        window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
                        delete window.webdriver;
                    """)
                    page = await context.new_page()
                    await page.goto(self.ODDS_URL, wait_until="domcontentloaded", timeout=30000)
                    await asyncio.sleep(10)  # Extended wait for JS
                    await page.evaluate("window.scrollBy(0, 1000)")
                    await asyncio.sleep(3)
                    text = await page.evaluate("document.body.innerText")
                    await browser.close()
                    
                    if text and len(text) > 1000:
                        odds = self._parse_betika_text(text)
                        if odds:
                            log.info(f"Betika Playwright: loaded {len(odds)} odds")
                            return odds
            except Exception as e:
                log.warning(f"Betika Playwright strategy failed: {e}")
            
            # Strategy 3: Fallback to orchestrator
            resp = await self.orchestrator.fetch(
                f"{self.BASE_URL}/sports/{sport}/odds",
                headers=await self._get_headers(),
                use_browser=True,
            )
            if resp and isinstance(resp, dict) and "text" in resp:
                if BS4_AVAILABLE:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(resp["text"], "lxml")
                    odds = self._parse_odds_page(soup)
                else:
                    odds = self._parse_odds_text(resp["text"])
        except Exception as e:
            log.error(f"Betika odds fetch error: {e}")
        return odds
    
    def _parse_betika_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse Betika page text into structured match data."""
        odds = []
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
                match_odds = {}
                
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
                                match_odds['home'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == 'X':
                        if j + 1 < len(lines):
                            try:
                                match_odds['draw'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif next_line == '2':
                        if j + 1 < len(lines):
                            try:
                                match_odds['away'] = float(lines[j + 1].strip())
                                j += 1
                            except:
                                pass
                    elif '1X2' in next_line or 'Full Time' in next_line:
                        pass
                    elif any(x in next_line for x in ['Football', 'Basketball', 'Tennis', 'Rugby']):
                        break
                    else:
                        if league and 'home' in match_odds:
                            break
                    
                    j += 1
                
                if home and away and 'home' in match_odds:
                    odds.append({
                        "id": f"bk_{hashlib.md5(f'{home}{away}{kickoff}'.encode()).hexdigest()[:8]}",
                        "home_team": home,
                        "away_team": away,
                        "league": league,
                        "kickoff": kickoff,
                        "bookmakers": [
                            {
                                "name": "Betika",
                                "markets": [
                                    {
                                        "key": "h2h",
                                        "outcomes": [
                                            {"name": "Home", "price": match_odds.get('home', 0)},
                                            {"name": "Draw", "price": match_odds.get('draw', 0)},
                                            {"name": "Away", "price": match_odds.get('away', 0)},
                                        ]
                                    }
                                ]
                            }
                        ]
                    })
            
            i += 1
        
        return odds
    
    def _parse_odds_page(self, soup) -> List[Dict[str, Any]]:
        odds = []
        try:
            match_rows = soup.select(".match-row, .event-row, [data-event-id]")
            for row in match_rows:
                try:
                    event_id = row.get("data-event-id", "")
                    home_elem = row.select_one(".home-team, .team-home")
                    away_elem = row.select_one(".away-team, .team-away")
                    home = home_elem.text.strip() if home_elem else ""
                    away = away_elem.text.strip() if away_elem else ""
                    odds_elem = row.select_one(".odds, .market-odds")
                    odds_text = odds_elem.text.strip() if odds_elem else ""
                    if home and away:
                        odds.append({
                            "id": event_id or f"bk_{hashlib.md5(f'{home}{away}'.encode()).hexdigest()[:8]}",
                            "home_team": home,
                            "away_team": away,
                            "bookmakers": [
                                {
                                    "name": "Betika",
                                    "markets": [
                                        {
                                            "key": "h2h",
                                            "outcomes": [
                                                {"name": "Home", "price": self._extract_odds(odds_text, 1)},
                                                {"name": "Draw", "price": self._extract_odds(odds_text, 2)},
                                                {"name": "Away", "price": self._extract_odds(odds_text, 3)},
                                            ]
                                        }
                                    ]
                                }
                            ]
                        })
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"Betika parse error: {e}")
        return odds

    def _parse_odds_text(self, text: str) -> List[Dict[str, Any]]:
        odds = []
        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            if "vs" in line.lower() or "v" in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    odds.append({
                        "id": f"bk_{hashlib.md5(line.encode()).hexdigest()[:8]}",
                        "home_team": parts[0],
                        "away_team": parts[-1],
                        "bookmakers": []
                    })
        return odds

    @staticmethod
    def _extract_odds(text: str, position: int) -> float:
        try:
            parts = text.split()
            if len(parts) >= position:
                return float(parts[position - 1])
        except Exception:
            pass
        return 0.0

    async def close(self):
        await self.orchestrator.close()
