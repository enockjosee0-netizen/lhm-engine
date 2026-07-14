#!/usr/bin/env python3
"""
Ghost Protocol - Hardware HID Layer
Raspberry Pi Pico + OpenCV Computer Vision = Undetectable Betting Bot
"""

import os
import sys
import time
import json
import struct
import threading
import queue
import random
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Dict, Any
from enum import Enum

import numpy as np

log = logging.getLogger("LHM.GhostProtocol")

# ======================================================================
# CONFIGURATION
# ======================================================================

@dataclass
class GhostConfig:
    # Pico serial settings
    pico_serial_port: str = "COM3"
    pico_baudrate: int = 115200
    pico_timeout: float = 2.0
    
    # Human behavior parameters (Lognormal distribution)
    human_delay_mean: float = 0.0
    human_delay_sigma: float = 0.5
    human_click_min_ms: int = 50
    human_click_max_ms: int = 80
    human_typing_min_ms: int = 50
    human_typing_max_ms: int = 150
    
    # Vision settings
    vision_confidence_threshold: float = 0.7
    vision_template_dir: str = "templates"
    vision_screenshot_dir: str = "screenshots"
    
    # Safety limits
    max_session_duration_minutes: int = 120
    captcha_pause_minutes: int = 4
    max_bets_per_bookmaker: int = 3
    max_stake_pct_per_bet: float = 0.02
    
    enabled: bool = False


# ======================================================================
# SERIAL PROTOCOL TO PICO
# ======================================================================

class PicoCommand:
    """Command types for Pico HID device."""
    MOVE = "MOVE"
    CLICK = "CLICK"
    PRESS = "PRESS"
    TYPE = "TYPE"
    SCROLL = "SCROLL"
    DELAY = "DELAY"
    STATUS = "STATUS"
    QUIT = "QUIT"


class PicoHIDInterface:
    """Low-level serial interface to Raspberry Pi Pico HID device."""
    
    def __init__(self, config: GhostConfig):
        self.config = config
        self.serial = None
        self.connected = False
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self._lock = threading.Lock()
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
    
    def connect(self) -> bool:
        """Connect to Pico via serial."""
        try:
            import serial
            self.serial = serial.Serial(
                port=self.config.pico_serial_port,
                baudrate=self.config.pico_baudrate,
                timeout=self.config.pico_timeout
            )
            time.sleep(2)  # Wait for Pico to reset
            
            # Read startup message
            if self.serial.in_waiting:
                msg = self.serial.readline().decode('utf-8', errors='ignore').strip()
                log.info(f"Pico says: {msg}")
            
            self.connected = True
            self._reader_thread = threading.Thread(target=self._read_responses, daemon=True)
            self._reader_thread.start()
            log.info(f"Connected to Pico HID on {self.config.pico_serial_port}")
            return True
            
        except ImportError:
            log.error("pyserial not installed. Run: pip install pyserial")
            return False
        except Exception as e:
            log.error(f"Failed to connect to Pico: {e}")
            return False
    
    def _read_responses(self):
        """Background thread to read Pico responses."""
        while not self._stop_event.is_set():
            try:
                if self.serial and self.serial.in_waiting:
                    line = self.serial.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.response_queue.put(line)
                time.sleep(0.01)
            except Exception as e:
                log.debug(f"Reader error: {e}")
                break
    
    def send(self, command: str, *args) -> Optional[str]:
        """Send command to Pico and wait for response."""
        if not self.connected or not self.serial:
            log.warning("Pico not connected, simulating command")
            return "OK_SIM"
        
        with self._lock:
            cmd_str = f"{command} {' '.join(str(a) for a in args)}\n"
            try:
                self.serial.write(cmd_str.encode('utf-8'))
                self.serial.flush()
                
                # Wait for response
                start = time.time()
                while time.time() - start < self.config.pico_timeout:
                    try:
                        resp = self.response_queue.get(timeout=0.1)
                        return resp
                    except queue.Empty:
                        continue
                
                log.warning(f"Pico timeout on command: {command}")
                return None
            except Exception as e:
                log.error(f"Serial write error: {e}")
                return None
    
    def move_mouse(self, dx: int, dy: int, duration_ms: int = 500):
        """Move mouse with human-like motion."""
        return self.send(PicoCommand.MOVE, dx, dy, duration_ms)
    
    def click(self, button: int = 0):
        """Click mouse button (0=left, 1=middle, 2=right)."""
        return self.send(PicoCommand.CLICK, button)
    
    def press_key(self, keycode: int):
        """Press a single key."""
        return self.send(PicoCommand.PRESS, keycode)
    
    def type_text(self, text: str):
        """Type a string."""
        return self.send(PicoCommand.TYPE, text)
    
    def scroll(self, delta: int):
        """Scroll wheel."""
        return self.send(PicoCommand.SCROLL, delta)
    
    def delay(self, ms: int):
        """Wait."""
        return self.send(PicoCommand.DELAY, ms)
    
    def disconnect(self):
        """Disconnect from Pico."""
        self._stop_event.set()
        if self.serial:
            try:
                self.send(PicoCommand.QUIT)
                self.serial.close()
            except Exception:
                pass
        self.connected = False
        log.info("Disconnected from Pico")


# ======================================================================
# HUMAN BEHAVIOR ENGINE
# ======================================================================

class HumanBehaviorEngine:
    """
    Generates human-like input patterns.
    Uses Lognormal distribution for reaction times (not Poisson).
    Hardware RNG from Pico adds microsecond-level noise.
    """
    
    @staticmethod
    def lognormal_delay(mean: float = 0.0, sigma: float = 0.5) -> float:
        """Generate human reaction time in seconds (lognormal distribution)."""
        delay = np.random.lognormal(mean=mean, sigma=sigma)
        return max(0.1, min(delay, 5.0))  # Clamp 100ms to 5s
    
    @staticmethod
    def poisson_delay(rate: float = 3.0) -> float:
        """Poisson-based delay for inter-request timing."""
        return max(0.1, np.random.poisson(rate) / rate)
    
    @staticmethod
    def bezier_curve(start: Tuple[float, float], end: Tuple[float, float], 
                     duration: float, points: int = 50) -> List[Tuple[float, float]]:
        """Generate Bezier curve points for mouse movement."""
        # Control points with random offset for natural movement
        cp1 = (
            start[0] + random.uniform(-50, 50),
            start[1] + random.uniform(-50, 50)
        )
        cp2 = (
            end[0] + random.uniform(-50, 50),
            end[1] + random.uniform(-50, 50)
        )
        
        curve = []
        for i in range(points):
            t = i / (points - 1)
            # Cubic Bezier
            x = (1-t)**3 * start[0] + 3*(1-t)**2 * t * cp1[0] + 3*(1-t) * t**2 * cp2[0] + t**3 * end[0]
            y = (1-t)**3 * start[1] + 3*(1-t)**2 * t * cp1[1] + 3*(1-t) * t**2 * cp2[1] + t**3 * end[1]
            curve.append((x, y))
        
        return curve
    
    @staticmethod
    def get_viewport() -> Tuple[int, int]:
        """Get random human-like viewport size."""
        widths = [1366, 1440, 1536, 1600, 1680, 1920]
        heights = [768, 900, 1024, 1050, 1080]
        return random.choice(widths), random.choice(heights)
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        """Get realistic browser headers."""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        return {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    @staticmethod
    def micro_acceleration() -> float:
        """Add micro-acceleration noise (hardware-level)."""
        return random.gauss(0, 0.1)


# ======================================================================
# COMPUTER VISION - DOM-LESS ELEMENT DETECTION
# ======================================================================

class VisionEngine:
    """
    OpenCV-based visual element detection.
    Never parses DOM - only sees pixels.
    Bypasses honeypot elements completely.
    """
    
    def __init__(self, config: GhostConfig):
        self.config = config
        self.templates: Dict[str, np.ndarray] = {}
        self.screenshot_count = 0
        
        # Ensure directories exist
        Path(config.vision_template_dir).mkdir(parents=True, exist_ok=True)
        Path(config.vision_screenshot_dir).mkdir(parents=True, exist_ok=True)
        
        self._load_templates()
    
    def _load_templates(self):
        """Load template images for button matching."""
        template_dir = Path(self.config.vision_template_dir)
        if not template_dir.exists():
            return
        
        for img_path in template_dir.glob("*.png"):
            name = img_path.stem
            template = cv2.imread(str(img_path))
            if template is not None:
                self.templates[name] = template
                log.info(f"Loaded template: {name}")
    
    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture current screen."""
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        except ImportError:
            log.error("mss not installed. Run: pip install mss")
            return None
        except Exception as e:
            log.error(f"Screen capture failed: {e}")
            return None
    
    def find_element(self, template_name: str, screen: np.ndarray) -> Optional[Tuple[int, int]]:
        """Find template element on screen, return center coordinates."""
        if template_name not in self.templates:
            log.warning(f"Template not found: {template_name}")
            return None
        
        template = self.templates[template_name]
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.config.vision_confidence_threshold:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            log.debug(f"Found {template_name} at ({center_x}, {center_y}) confidence={max_val:.2f}")
            return (center_x, center_y)
        
        return None
    
    def find_text_region(self, text: str, screen: np.ndarray) -> Optional[Tuple[int, int]]:
        """Find text on screen using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            pil_img = Image.fromarray(cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT)
            
            for i, word in enumerate(data["text"]):
                if text.lower() in word.lower():
                    x = data["left"][i] + data["width"][i] // 2
                    y = data["top"][i] + data["height"][i] // 2
                    log.debug(f"Found text '{text}' at ({x}, {y})")
                    return (x, y)
        except ImportError:
            log.warning("pytesseract not installed. OCR disabled.")
        except Exception as e:
            log.error(f"OCR error: {e}")
        
        return None
    
    def save_screenshot(self, screen: np.ndarray, suffix: str = ""):
        """Save screenshot for debugging."""
        self.screenshot_count += 1
        path = Path(self.config.vision_screenshot_dir) / f"screenshot_{self.screenshot_count:04d}{suffix}.png"
        cv2.imwrite(str(path), screen)
        log.debug(f"Screenshot saved: {path}")


# ======================================================================
# GHOST PROTOCOL - MAIN CLASS
# ======================================================================

class GhostProtocol:
    """
    Main Ghost Protocol controller.
    Integrates Pico HID + OpenCV Vision + Human Behavior Engine.
    """
    
    def __init__(self, config: Optional[GhostConfig] = None):
        self.config = config or GhostConfig()
        self.hid = PicoHIDInterface(self.config)
        self.vision = VisionEngine(self.config)
        self.human = HumanBehaviorEngine()
        self.current_position = (0, 0)
        self.session_start = time.time()
        self.bets_this_session = 0
        self.running = False
    
    def initialize(self) -> bool:
        """Initialize hardware layer."""
        if not self.config.enabled:
            log.info("Ghost Protocol disabled in config")
            return False
        
        # Try to connect to Pico
        if not self.hid.connect():
            log.warning("Pico not connected - running in simulation mode")
            return False
        
        log.info("Ghost Protocol initialized - Hardware HID active")
        return True
    
    def human_delay(self, base_seconds: float = 1.0):
        """Wait with human-like timing (lognormal distribution)."""
        delay = self.human.lognormal_delay() * base_seconds
        time.sleep(max(0.1, delay))
    
    def move_to_element(self, template_name: str, duration_ms: int = 800) -> bool:
        """Move mouse to a visual element using Bezier curve."""
        screen = self.vision.capture_screen()
        if screen is None:
            return False
        
        target = self.vision.find_element(template_name, screen)
        if target is None:
            log.warning(f"Element not found: {template_name}")
            return False
        
        # Generate Bezier curve
        curve = self.human.bezier_curve(self.current_position, target, duration_ms / 1000.0)
        
        # Execute movement via Pico
        dx_total = target[0] - self.current_position[0]
        dy_total = target[1] - self.current_position[1]
        self.hid.move_mouse(int(dx_total), int(dy_total), duration_ms)
        
        self.current_position = target
        
        # Human think time after moving
        self.human_delay(0.5)
        return True
    
    def click_element(self, template_name: str) -> bool:
        """Move to element and click it."""
        if not self.move_to_element(template_name):
            return False
        
        self.hid.click(0)  # Left click
        
        # Human settle time after click
        time.sleep_ms(random.randint(50, 100))
        return True
    
    def detect_captcha(self, screen: Optional[np.ndarray] = None) -> bool:
        """Detect CAPTCHA on screen."""
        if screen is None:
            screen = self.vision.capture_screen()
        if screen is None:
            return False
        
        # Look for common CAPTCHA patterns
        captcha_indicators = ["captcha", "recaptcha", "hcaptcha", "verify"]
        for indicator in captcha_indicators:
            region = self.vision.find_text_region(indicator, screen)
            if region:
                log.warning(f"CAPTCHA detected: {indicator}")
                return True
        
        return False
    
    def handle_captcha(self):
        """Handle CAPTCHA detection - pause and rotate."""
        log.warning("CAPTCHA detected! Pausing for 4 hours...")
        
        # Save screenshot for analysis
        screen = self.vision.capture_screen()
        if screen:
            self.vision.save_screenshot(screen, "_captcha")
        
        # Pause for cooldown
        pause_seconds = self.config.captcha_pause_minutes * 60
        time.sleep(pause_seconds)
        
        return True
    
    def place_bet_sequence(self, bookmaker: str, selection: str, stake: float) -> bool:
        """
        Full bet placement sequence using hardware HID.
        Never touches DOM - only visual elements.
        """
        log.info(f"Placing bet: {bookmaker} - {selection} - ${stake}")
        
        # Check session limits
        if self.bets_this_session >= self.config.max_bets_per_bookmaker:
            log.warning("Max bets per session reached")
            return False
        
        # Check stake limit
        if stake > self.config.max_stake_pct_per_bet:
            log.warning(f"Stake {stake} exceeds max {self.config.max_stake_pct_per_bet}")
            return False
        
        # Sequence of visual actions
        actions = [
            ("bet_slip_button", "Click bet slip"),
            ("stake_input", "Click stake input"),
            ("stake_input", "Clear stake field"),
            ("place_bet_button", "Click place bet"),
        ]
        
        for template_name, description in actions:
            log.debug(f"Action: {description}")
            
            if not self.click_element(template_name):
                log.error(f"Failed to find element: {template_name}")
                return False
            
            # Human think time between actions
            self.human_delay(1.0)
        
        self.bets_this_session += 1
        log.info(f"Bet placed successfully. Total this session: {self.bets_this_session}")
        return True
    
    def run_session(self):
        """Run a betting session."""
        self.running = True
        self.session_start = time.time()
        self.bets_this_session = 0
        
        log.info("Ghost Protocol session started")
        
        # Initialize hardware
        if not self.initialize():
            log.error("Failed to initialize Ghost Protocol")
            return
        
        try:
            while self.running:
                # Check session duration
                elapsed = time.time() - self.session_start
                if elapsed > self.config.max_session_duration_minutes * 60:
                    log.info("Session timeout")
                    break
                
                # Check for CAPTCHA
                if self.detect_captcha():
                    self.handle_captcha()
                    continue
                
                # Main loop - check for betting opportunities
                # This is where LHM engine integration happens
                self.human_delay(2.0)
                
        except KeyboardInterrupt:
            log.info("Session interrupted by user")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown."""
        self.running = False
        self.hid.disconnect()
        log.info("Ghost Protocol shutdown complete")


# ======================================================================
# PERSISTENT SERVICE INSTALLER
# ======================================================================

class GhostServiceInstaller:
    """Install Ghost Protocol as Windows service for 24/7 persistence."""
    
    @staticmethod
    def install() -> bool:
        """Install as Windows service using nssm."""
        try:
            import win32service
            import win32serviceutil
            
            # Service configuration
            service_name = "GhostProtocol"
            display_name = "LHM Ghost Protocol HID Layer"
            
            # Create service
            # Note: Requires nssm.exe in PATH or same directory
            log.info(f"Installing {service_name} as Windows service...")
            
            # For now, create startup shortcut
            startup_dir = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
            shortcut_path = startup_dir / "GhostProtocol.bat"
            
            bat_content = f"""@echo off
cd /d "{Path(__file__).parent}"
start /B pythonw.exe ghost_protocol_service.py
"""
            shortcut_path.write_text(bat_content)
            log.info(f"Created startup shortcut: {shortcut_path}")
            return True
            
        except Exception as e:
            log.error(f"Service install failed: {e}")
            return False
    
    @staticmethod
    def uninstall() -> bool:
        """Remove startup shortcut."""
        try:
            startup_dir = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))
            shortcut_path = startup_dir / "GhostProtocol.bat"
            if shortcut_path.exists():
                shortcut_path.unlink()
                log.info("Removed Ghost Protocol startup shortcut")
            return True
        except Exception as e:
            log.error(f"Uninstall failed: {e}")
            return False


# ======================================================================
# MAIN ENTRY POINT
# ======================================================================

def main():
    """Main entry point for Ghost Protocol."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    )
    
    config = GhostConfig()
    
    # Check if Pico HID is enabled
    if not config.enabled:
        log.info("Ghost Protocol disabled. Set enabled=True in config to activate.")
        return
    
    ghost = GhostProtocol(config)
    ghost.run_session()


if __name__ == "__main__":
    main()
