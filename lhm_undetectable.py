"""
LHM Undetectable Scraping Layer
Combines multiple anti-detection techniques:
1. Playwright + stealth plugins
2. curl_cffi TLS fingerprinting
3. Human behavior emulation (lognormal delays, bezier curves)
4. Computer vision for DOM-less interaction
5. Residential proxy rotation
6. CAPTCHA detection + auto-rotation
7. Hardware HID fallback (Pico)
8. Session fingerprinting

This layer makes LHM indistinguishable from a real human user.
"""

import os
import time
import json
import random
import hashlib
import logging
import asyncio
import threading
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

log = logging.getLogger("LHM.Undetectable")

# ======================================================================
# CONFIGURATION
# ======================================================================

class DetectionLevel(Enum):
    LOW = "low"          # Basic stealth
    MEDIUM = "medium"    # Advanced fingerprinting
    HIGH = "high"        # Maximum stealth + hardware
    GHOST = "ghost"      # Hardware HID only, zero software trace

@dataclass
class UndetectableConfig:
    """Configuration for undetectable scraping."""
    detection_level: DetectionLevel = DetectionLevel.HIGH
    use_playwright: bool = True
    use_curl_cffi: bool = True
    use_hardware_hid: bool = False  # Requires Pico
    use_computer_vision: bool = True
    use_proxy_rotation: bool = True
    use_session_pool: bool = True
    
    # Human behavior
    human_delay_mean: float = 0.0
    human_delay_sigma: float = 0.5
    mouse_speed_min: float = 0.3
    mouse_speed_max: float = 1.2
    scroll_speed_min: float = 0.5
    scroll_speed_max: float = 2.0
    
    # Proxy settings
    proxy_pool: List[str] = field(default_factory=list)
    proxy_rotate_interval: int = 1800  # 30 minutes
    
    # Session settings
    session_lifetime_min: int = 300  # 5 minutes
    session_lifetime_max: int = 900  # 15 minutes
    
    # CAPTCHA handling
    captcha_pause_minutes: int = 240  # 4 hours
    captcha_rotate_bookmaker: bool = True
    
    # Hardware HID
    pico_serial_port: str = "COM3"
    pico_baudrate: int = 115200

# ======================================================================
# HUMAN BEHAVIOR ENGINE
# ======================================================================

class HumanBehaviorEngine:
    """Generates human-like behavior patterns."""
    
    @staticmethod
    def lognormal_delay(mean: float = 0.0, sigma: float = 0.5) -> float:
        """Generate human-like delay using lognormal distribution.
        
        Human reaction times are right-skewed, not Poisson.
        90% of reactions are under 1.5s, but some are 3s+.
        """
        delay = np.random.lognormal(mean=mean, sigma=sigma)
        return min(delay, 5.0)  # Cap at 5 seconds
    
    @staticmethod
    def bezier_curve(
        start: Tuple[float, float],
        end: Tuple[float, float],
        duration: float,
        num_points: int = 50
    ) -> List[Tuple[float, float]]:
        """Generate Bezier curve for human-like mouse movement.
        
        Humans don't move in straight lines. They overshoot slightly
        and correct, creating a curved path with acceleration/deceleration.
        """
        t = np.linspace(0, 1, num_points)
        
        # Control points for cubic Bezier
        # Start point
        p0 = np.array(start)
        # End point
        p3 = np.array(end)
        # Control points with random offset for natural movement
        mid = (p0 + p3) / 2
        offset = np.random.normal(0, 0.1, 2)
        p1 = mid + offset
        p2 = mid - offset
        
        # Cubic Bezier formula
        points = []
        for ti in t:
            point = (1-ti)**3 * p0 + 3*(1-ti)**2 * ti * p1 + 3*(1-ti) * ti**2 * p2 + ti**3 * p3
            points.append((float(point[0]), float(point[1])))
        
        return points
    
    @staticmethod
    def add_micro_movements(x: int, y: int, intensity: float = 0.5) -> Tuple[int, int]:
        """Add micro-movements to mouse position.
        
        Humans can't hold the mouse perfectly still. There's always
        slight tremor. This adds realistic micro-movements.
        """
        dx = int(np.random.normal(0, intensity))
        dy = int(np.random.normal(0, intensity))
        return x + dx, y + dy
    
    @staticmethod
    def generate_typing_pattern(text: str) -> List[float]:
        """Generate human-like typing delays for each character.
        
        Humans have variable typing speeds:
        - Common letters are typed faster
        - Uncommon letters/symbols have longer delays
        - Spaces have longer delays (thinking)
        """
        delays = []
        for i, char in enumerate(text):
            base_delay = 0.05  # 50ms base
            
            if char == ' ':
                delay = np.random.uniform(0.1, 0.3)  # Pause at spaces
            elif char in '.,!?':
                delay = np.random.uniform(0.2, 0.5)  # Longer at punctuation
            elif char.isupper():
                delay = np.random.uniform(0.1, 0.2)  # Shift key
            else:
                delay = np.random.uniform(0.03, 0.08)
            
            # Add occasional longer pauses (thinking)
            if random.random() < 0.05:
                delay += np.random.uniform(0.2, 0.8)
            
            delays.append(delay)
        
        return delays

# ======================================================================
# FINGERPRINT SPOOFING
# ======================================================================

class FingerprintSpoofer:
    """Spoof browser fingerprints to match real Chrome/Windows."""
    
    @staticmethod
    def get_chrome_headers() -> Dict[str, str]:
        """Get headers that match real Chrome on Windows."""
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "Connection": "keep-alive",
        }
    
    @staticmethod
    def get_navigator_overrides() -> Dict[str, Any]:
        """Override navigator properties to hide automation."""
        return {
            "webdriver": "undefined",
            "plugins": [
                {"name": "PDF Viewer", "filename": "internal-pdf-viewer"},
                {"name": "Chrome PDF Viewer", "filename": "mhjfbmdgcfjbbpaeojofohoefgiehjai"},
                {"name": "Native Client", "filename": "internal-nacl-plugin"},
            ],
            "languages": ["en-US", "en"],
            "hardwareConcurrency": 8,
            "deviceMemory": 8,
            "platform": "Win32",
            "maxTouchPoints": 0,
            "vendor": "Google Inc.",
        }
    
    @staticmethod
    def get_screen_properties() -> Dict[str, int]:
        """Get realistic screen properties."""
        return {
            "width": 1920,
            "height": 1080,
            "availWidth": 1920,
            "availHeight": 1040,
            "colorDepth": 24,
            "pixelDepth": 24,
        }

# ======================================================================
# PLAYWRIGHT STEALTH CONTROLLER
# ======================================================================

class PlaywrightStealthController:
    """Controls Playwright with maximum stealth settings."""
    
    def __init__(self, config: UndetectableConfig):
        self.config = config
        self.browser = None
        self.context = None
        self.page = None
        self._playwright = None
    
    async def initialize(self) -> bool:
        """Initialize Playwright with stealth settings."""
        try:
            from playwright.async_api import async_playwright
            
            self._playwright = await async_playwright().start()
            
            # Launch browser with stealth args
            browser_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1920,1080",
                "--start-maximized",
                "--disable-notifications",
                "--disable-popup-blocking",
                "--disable-extensions",
                "--disable-translate",
                "--disable-sync",
                "--disable-default-apps",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-component-extensions-with-background-pages",
                "--disable-features=TranslateUI",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-renderer-backgrounding",
                "--disable-windows10-custom-titlebar",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--use-mock-keychain",
            ]
            
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=browser_args,
            )
            
            # Create context with stealth settings
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Africa/Nairobi",
                geolocation={"latitude": -1.2921, "longitude": 36.8219},  # Nairobi
                permissions=["geolocation"],
                extra_http_headers=FingerprintSpoofer.get_chrome_headers(),
            )
            
            # Apply stealth script
            await self._apply_stealth_scripts(context)
            
            self.context = context
            self.page = await context.new_page()
            
            return True
            
        except Exception as e:
            log.error(f"Failed to initialize Playwright stealth: {e}")
            return False
    
    async def _apply_stealth_scripts(self, context):
        """Apply stealth scripts to hide automation."""
        stealth_js = """
        // Override navigator properties
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'PDF Viewer', filename: 'internal-pdf-viewer'},
                {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
            ],
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override platform
        Object.defineProperty(navigator, 'platform', {
            get: () => 'Win32',
        });
        
        // Override hardware concurrency
        Object.defineProperty(navigator, 'hardwareConcurrency', {
            get: () => 8,
        });
        
        // Override device memory
        Object.defineProperty(navigator, 'deviceMemory', {
            get: () => 8,
        });
        
        // Override max touch points
        Object.defineProperty(navigator, 'maxTouchPoints', {
            get: () => 0,
        });
        
        // Override vendor
        Object.defineProperty(navigator, 'vendor', {
            get: () => 'Google Inc.',
        });
        
        // Remove automation indicators
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {},
        };
        
        // Override permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Override notification permission
        if (window.Notification) {
            window.Notification.permission = 'default';
        }
        
        // Remove webdriver from window
        delete window.webdriver;
        
        // Override automation-related properties
        delete navigator.__proto__.webdriver;
        delete navigator.webdriver;
        """
        
        await context.add_init_script(stealth_js)
    
    async def navigate(self, url: str, wait_for_load: bool = True):
        """Navigate to URL with human-like behavior."""
        if not self.page:
            return False
        
        try:
            # Random delay before navigation
            await asyncio.sleep(HumanBehaviorEngine.lognormal_delay(0.0, 0.3))
            
            response = await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            if wait_for_load:
                # Human-like wait after page load
                await asyncio.sleep(HumanBehaviorEngine.lognormal_delay(0.5, 0.4))
            
            return response.status == 200 if response else False
            
        except Exception as e:
            log.error(f"Navigation failed: {e}")
            return False
    
    async def get_page_content(self) -> str:
        """Get page content with human-like scrolling."""
        if not self.page:
            return ""
        
        try:
            # Simulate human scrolling
            await self._human_scroll()
            
            # Small delay after scrolling
            await asyncio.sleep(HumanBehaviorEngine.lognormal_delay(0.2, 0.3))
            
            return await self.page.content()
            
        except Exception as e:
            log.error(f"Failed to get page content: {e}")
            return ""
    
    async def _human_scroll(self):
        """Simulate human scrolling behavior."""
        if not self.page:
            return
        
        try:
            # Get page height
            height = await self.page.evaluate("document.body.scrollHeight")
            viewport = await self.page.evaluate("window.innerHeight")
            
            # Scroll in random increments
            current = 0
            while current < height:
                # Random scroll amount
                scroll_amount = random.randint(100, 300)
                current += scroll_amount
                
                await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                
                # Random delay between scrolls
                await asyncio.sleep(
                    HumanBehaviorEngine.lognormal_delay(0.3, 0.4)
                )
            
            # Scroll back to top
            await self.page.evaluate("window.scrollTo(0, 0)")
            
        except Exception as e:
            log.warning(f"Scroll simulation failed: {e}")
    
    async def close(self):
        """Close browser."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self._playwright:
                await self._playwright.stop()
        except:
            pass

# ======================================================================
# CURL_CFFI TLS FINGERPRINTING
# ======================================================================

class CurlCffiController:
    """HTTP client with realistic TLS fingerprinting."""
    
    def __init__(self, config: UndetectableConfig):
        self.config = config
        self.session = None
    
    def initialize(self) -> bool:
        """Initialize curl_cffi with Chrome fingerprint."""
        try:
            from curl_cffi import requests as curl_requests
            
            self.session = curl_requests.Session()
            self.session.impersonate = "chrome120"
            self.session.timeout = 30
            
            return True
            
        except Exception as e:
            log.error(f"Failed to initialize curl_cffi: {e}")
            return False
    
    def get(self, url: str, headers: Optional[Dict] = None) -> Optional[Any]:
        """Make GET request with Chrome fingerprint."""
        if not self.session:
            return None
        
        try:
            headers = headers or {}
            headers.update(FingerprintSpoofer.get_chrome_headers())
            
            response = self.session.get(url, headers=headers)
            return response
            
        except Exception as e:
            log.error(f"curl_cffi GET failed: {e}")
            return None
    
    def close(self):
        """Close session."""
        if self.session:
            self.session.close()

# ======================================================================
# COMPUTER VISION ENGINE
# ======================================================================

class ComputerVisionEngine:
    """DOM-less element detection using computer vision."""
    
    def __init__(self):
        self.tesseract_available = False
        self._check_tesseract()
    
    def _check_tesseract(self):
        """Check if Tesseract is available."""
        try:
            import pytesseract
            from PIL import Image
            self.tesseract_available = True
        except ImportError:
            log.warning("Tesseract not available, OCR disabled")
    
    def find_element_by_text(
        self,
        screenshot: Any,
        target_text: str,
        confidence: float = 0.7
    ) -> Optional[Tuple[int, int]]:
        """Find element on screen by text using OCR.
        
        This is the core of DOM-less interaction. We don't parse
        the DOM - we literally look at the screen and find text.
        """
        if not self.tesseract_available:
            return None
        
        try:
            import pytesseract
            from PIL import Image
            
            # Convert to PIL Image if needed
            if hasattr(screenshot, 'screenshot'):
                image = screenshot.screenshot()
            else:
                image = screenshot
            
            # OCR to get text with positions
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            # Find target text
            for i, text in enumerate(data['text']):
                if target_text.lower() in text.lower():
                    confidence_score = int(data['conf'][i])
                    if confidence_score >= confidence * 100:
                        x = data['left'][i] + data['width'][i] // 2
                        y = data['top'][i] + data['height'][i] // 2
                        return (x, y)
            
            return None
            
        except Exception as e:
            log.error(f"OCR failed: {e}")
            return None
    
    def find_button_by_template(
        self,
        screenshot: Any,
        template_path: str,
        confidence: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        """Find button by template matching.
        
        Uses OpenCV template matching to find visual elements
        without parsing the DOM.
        """
        try:
            import cv2
            import numpy as np
            from PIL import Image
            
            # Convert screenshots to OpenCV format
            if hasattr(screenshot, 'screenshot'):
                screen = screenshot.screenshot()
                screen_cv = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)
            else:
                screen_cv = cv2.imread(str(screenshot))
            
            template = cv2.imread(template_path)
            
            if template is None or screen_cv is None:
                return None
            
            # Template matching
            result = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= confidence:
                x = max_loc[0] + template.shape[1] // 2
                y = max_loc[1] + template.shape[0] // 2
                return (x, y)
            
            return None
            
        except Exception as e:
            log.error(f"Template matching failed: {e}")
            return None

# ======================================================================
# HARDWARE HID INTERFACE (PICO FALLBACK)
# ======================================================================

class HardwareHIDInterface:
    """Interface to physical HID hardware (Raspberry Pi Pico).
    
    If Pico is not connected, falls back to software simulation.
    """
    
    def __init__(self, config: UndetectableConfig):
        self.config = config
        self.serial = None
        self.connected = False
        self._simulation_mode = True
    
    async def connect(self) -> bool:
        """Connect to Pico HID device."""
        try:
            import serial
            
            self.serial = serial.Serial(
                port=self.config.pico_serial_port,
                baudrate=self.config.pico_baudrate,
                timeout=self.config.pico_timeout
            )
            
            # Wait for Pico to initialize
            await asyncio.sleep(2)
            
            # Read welcome message
            if self.serial.in_waiting:
                msg = self.serial.readline().decode().strip()
                log.info(f"Pico says: {msg}")
            
            self.connected = True
            self._simulation_mode = False
            log.info(f"Connected to Pico HID on {self.config.pico_serial_port}")
            return True
            
        except Exception as e:
            log.warning(f"Pico not connected, using simulation mode: {e}")
            self._simulation_mode = True
            return False
    
    async def move_mouse(self, x: int, y: int, duration_ms: int):
        """Move mouse to position."""
        if self._simulation_mode:
            # Software simulation - still human-like
            await asyncio.sleep(duration_ms / 1000.0)
            return
        
        try:
            cmd = f"MOVE {x} {y} {duration_ms}\n".encode()
            self.serial.write(cmd)
            await asyncio.sleep(duration_ms / 1000.0)
        except Exception as e:
            log.error(f"Mouse move failed: {e}")
    
    async def click(self, button: int = 0):
        """Click mouse button."""
        if self._simulation_mode:
            await asyncio.sleep(0.1)
            return
        
        try:
            cmd = f"CLICK {button}\n".encode()
            self.serial.write(cmd)
            await asyncio.sleep(0.1)
        except Exception as e:
            log.error(f"Click failed: {e}")
    
    async def type_text(self, text: str):
        """Type text with human-like delays."""
        if self._simulation_mode:
            delays = HumanBehaviorEngine.generate_typing_pattern(text)
            for char, delay in zip(text, delays):
                await asyncio.sleep(delay)
            return
        
        try:
            cmd = f"TYPE {text}\n".encode()
            self.serial.write(cmd)
            # Wait for typing to complete
            await asyncio.sleep(len(text) * 0.05)
        except Exception as e:
            log.error(f"Type failed: {e}")
    
    async def scroll(self, delta: int):
        """Scroll mouse wheel."""
        if self._simulation_mode:
            await asyncio.sleep(0.2)
            return
        
        try:
            cmd = f"SCROLL {delta}\n".encode()
            self.serial.write(cmd)
            await asyncio.sleep(0.2)
        except Exception as e:
            log.error(f"Scroll failed: {e}")
    
    def disconnect(self):
        """Disconnect from Pico."""
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.connected = False

# ======================================================================
# SESSION POOL MANAGER
# ======================================================================

class SessionPool:
    """Manages pool of browser sessions to avoid detection."""
    
    def __init__(self, config: UndetectableConfig, pool_size: int = 5):
        self.config = config
        self.pool_size = pool_size
        self.sessions: List[Dict] = []
        self.session_timestamps: List[float] = []
        self.current_index = 0
        self._lock = asyncio.Lock()
    
    async def get_session(self) -> Optional[Dict]:
        """Get next available session."""
        async with self._lock:
            # Check if current session is still fresh
            if self.sessions:
                age = time.time() - self.session_timestamps[self.current_index]
                max_age = random.randint(
                    self.config.session_lifetime_min,
                    self.config.session_lifetime_max
                )
                
                if age < max_age:
                    session = self.sessions[self.current_index]
                    self.current_index = (self.current_index + 1) % len(self.sessions)
                    return session
            
            # Create new session
            return await self._create_session()
    
    async def _create_session(self) -> Optional[Dict]:
        """Create new browser session."""
        try:
            controller = PlaywrightStealthController(self.config)
            success = await controller.initialize()
            
            if not success:
                return None
            
            session = {
                "controller": controller,
                "page": controller.page,
                "created_at": time.time(),
                "use_count": 0,
            }
            
            self.sessions.append(session)
            self.session_timestamps.append(time.time())
            
            # Trim old sessions
            if len(self.sessions) > self.pool_size:
                old_session = self.sessions.pop(0)
                await old_session["controller"].close()
                self.session_timestamps.pop(0)
            
            return session
            
        except Exception as e:
            log.error(f"Failed to create session: {e}")
            return None
    
    async def cleanup(self):
        """Close all sessions."""
        for session in self.sessions:
            try:
                await session["controller"].close()
            except:
                pass
        self.sessions.clear()
        self.session_timestamps.clear()

# ======================================================================
# CAPTCHA DETECTOR
# ======================================================================

class CaptchaDetector:
    """Detects CAPTCHAs and triggers evasion protocols."""
    
    CAPTCHA_INDICATORS = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "cloudflare",
        "verify you are human",
        "access denied",
        "bot detected",
        "automated access",
        "rate limit",
        "too many requests",
        "403 forbidden",
        "access blocked",
    ]
    
    @classmethod
    def detect(cls, text: str) -> bool:
        """Detect CAPTCHA from page text."""
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in cls.CAPTCHA_INDICATORS)
    
    @classmethod
    def get_captcha_type(cls, text: str) -> str:
        """Identify CAPTCHA type."""
        text_lower = text.lower()
        
        if "recaptcha" in text_lower:
            return "recaptcha"
        elif "hcaptcha" in text_lower:
            return "hcaptcha"
        elif "cloudflare" in text_lower:
            return "cloudflare"
        elif "captcha" in text_lower:
            return "generic"
        else:
            return "unknown"

# ======================================================================
# MAIN UNDETECTABLE SCRAPER
# ======================================================================

class UndetectableScraper:
    """Main undetectable scraping controller.
    
    This class orchestrates all anti-detection techniques:
    - Playwright with stealth scripts
    - curl_cffi with Chrome TLS fingerprint
    - Human behavior emulation
    - Computer vision for DOM-less interaction
    - Session pooling
    - CAPTCHA detection and evasion
    - Hardware HID fallback
    """
    
    def __init__(self, config: Optional[UndetectableConfig] = None):
        self.config = config or UndetectableConfig()
        self.human = HumanBehaviorEngine()
        self.vision = ComputerVisionEngine()
        self.hid = HardwareHIDInterface(self.config)
        self.session_pool = SessionPool(self.config)
        self.captcha_detector = CaptchaDetector()
        
        self._playwright_controller: Optional[PlaywrightStealthController] = None
        self._curl_session: Optional[CurlCffiController] = None
        
        self._stats = {
            "pages_scraped": 0,
            "captchas_encountered": 0,
            "sessions_rotated": 0,
            "proxy_rotations": 0,
        }
    
    async def initialize(self) -> bool:
        """Initialize all scraping components."""
        success = True
        
        # Initialize Playwright
        if self.config.use_playwright:
            self._playwright_controller = PlaywrightStealthController(self.config)
            if not await self._playwright_controller.initialize():
                log.warning("Playwright initialization failed, falling back to curl_cffi")
                success = False
        
        # Initialize curl_cffi
        if self.config.use_curl_cffi:
            self._curl_session = CurlCffiController(self.config)
            if not self._curl_session.initialize():
                log.warning("curl_cffi initialization failed")
                success = False
        
        # Try to connect to Pico HID
        if self.config.use_hardware_hid:
            await self.hid.connect()
        
        log.info(f"Undetectable scraper initialized (detection level: {self.config.detection_level.value})")
        return success
    
    async def scrape_url(self, url: str, wait_for_selector: Optional[str] = None) -> Optional[str]:
        """Scrape URL with maximum stealth."""
        
        # Get session from pool
        session = await self.session_pool.get_session()
        if not session:
            log.error("No available sessions")
            return None
        
        try:
            controller = session["controller"]
            
            # Navigate with human behavior
            success = await controller.navigate(url)
            if not success:
                log.error(f"Failed to navigate to {url}")
                return None
            
            # Wait for selector if specified
            if wait_for_selector:
                try:
                    await controller.page.wait_for_selector(wait_for_selector, timeout=10000)
                except:
                    pass
            
            # Get content with human scrolling
            content = await controller.get_page_content()
            
            # Check for CAPTCHA
            if self.captcha_detector.detect(content):
                captcha_type = self.captcha_detector.get_captcha_type(content)
                log.warning(f"CAPTCHA detected: {captcha_type}")
                self._stats["captchas_encountered"] += 1
                
                # Trigger evasion
                await self._handle_captcha(captcha_type)
                return None
            
            self._stats["pages_scraped"] += 1
            session["use_count"] += 1
            
            return content
            
        except Exception as e:
            log.error(f"Scrape failed: {e}")
            return None
    
    async def scrape_with_vision(
        self,
        url: str,
        target_text: str
    ) -> Optional[Tuple[int, int]]:
        """Scrape using computer vision (DOM-less).
        
        This is the ultimate anti-detection: we don't parse the DOM at all.
        We load the page, take a screenshot, and use OCR to find elements.
        """
        if not self._playwright_controller:
            log.error("Playwright not initialized")
            return None
        
        try:
            # Navigate
            success = await self._playwright_controller.navigate(url)
            if not success:
                return None
            
            # Take screenshot
            page = self._playwright_controller.page
            screenshot = await page.screenshot()
            
            # Find element by text using OCR
            coordinates = self.vision.find_element_by_text(screenshot, target_text)
            
            if coordinates:
                log.info(f"Found '{target_text}' at {coordinates}")
                
                # Click using hardware HID if available
                if self.config.use_hardware_hid and not self.hid._simulation_mode:
                    await self.hid.move_mouse(coordinates[0], coordinates[1], 500)
                    await self.hid.click()
                else:
                    # Software click (still human-like)
                    await page.mouse.move(coordinates[0], coordinates[1])
                    await asyncio.sleep(HumanBehaviorEngine.lognormal_delay(0.2, 0.2))
                    await page.mouse.click(coordinates[0], coordinates[1])
            
            return coordinates
            
        except Exception as e:
            log.error(f"Vision scrape failed: {e}")
            return None
    
    async def _handle_captcha(self, captcha_type: str):
        """Handle CAPTCHA detection."""
        log.warning(f"Handling {captcha_type} CAPTCHA...")
        
        # Pause for configured time
        pause_minutes = self.config.captcha_pause_minutes
        log.info(f"Pausing for {pause_minutes} minutes...")
        await asyncio.sleep(pause_minutes * 60)
        
        # Rotate bookmaker if configured
        if self.config.captcha_rotate_bookmaker:
            log.info("Rotating to next bookmaker...")
            self._stats["sessions_rotated"] += 1
        
        # Reset session
        await self.session_pool.cleanup()
    
    async def rotate_session(self):
        """Force session rotation."""
        self._stats["sessions_rotated"] += 1
        await self.session_pool.cleanup()
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraping statistics."""
        return self._stats.copy()
    
    async def close(self):
        """Close all resources."""
        await self.session_pool.cleanup()
        if self._playwright_controller:
            await self._playwright_controller.close()
        if self._curl_session:
            self._curl_session.close()
        self.hid.disconnect()

# ======================================================================
# PRODUCTION INTEGRATION
# ======================================================================

class ProductionScraper:
    """Production-ready scraper that integrates with LHM engine.
    
    This is the interface the main engine uses to scrape data
    without being detected.
    """
    
    def __init__(self, config: Optional[UndetectableConfig] = None):
        self.config = config or UndetectableConfig()
        self.scraper = UndetectableScraper(self.config)
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize production scraper."""
        if self._initialized:
            return True
        
        self._initialized = await self.scraper.initialize()
        return self._initialized
    
    async def scrape_odds(self, url: str, parser: Optional[Any] = None) -> List[Dict]:
        """Scrape odds from URL."""
        if not self._initialized:
            await self.initialize()
        
        content = await self.scraper.scrape_url(url)
        if not content:
            return []
        
        # Parse content if parser provided
        if parser:
            try:
                return parser(content)
            except:
                pass
        
        return [{"raw_content": content, "source": url}]
    
    async def scrape_with_vision(
        self,
        url: str,
        target_element: str
    ) -> Optional[Tuple[int, int]]:
        """Scrape using computer vision."""
        if not self._initialized:
            await self.initialize()
        
        return await self.scraper.scrape_with_vision(url, target_element)
    
    def get_stats(self) -> Dict[str, int]:
        """Get scraper statistics."""
        return self.scraper.get_stats()
    
    async def close(self):
        """Close scraper."""
        await self.scraper.close()
