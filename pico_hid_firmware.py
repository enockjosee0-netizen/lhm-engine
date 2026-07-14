#!/usr/bin/env python3
"""
Raspberry Pi Pico HID Firmware
Flash this to your Pico using MicroPython UF2.
It acts as a USB HID mouse/keyboard and receives commands via serial.
"""

# ======================================================================
# This file is meant to be copied to the Pico as main.py
# Flash procedure:
#   1. Hold BOOTSEL on Pico while plugging into PC
#   2. Copy this file to the RPI-RP2 drive as main.py
#   3. Unplug and replug Pico
# ======================================================================

import machine
import time
import struct
import sys

# ======================================================================
# HID DESCRIPTOR SETUP - Mouse + Keyboard composite device
# ======================================================================

# Mouse HID report: 1 byte buttons, 1 byte X, 1 byte Y, 1 byte wheel
# Keyboard HID report: 1 byte modifier, 1 byte reserved, 6 bytes keycodes

# USB HID device setup for Pico
try:
    import usb_hid
    from adafruit_hid.mouse import Mouse
    from adafruit_hid.keyboard import Keyboard
    from adafruit_hid.keycode import Keycode
    HID_AVAILABLE = True
except ImportError:
    HID_AVAILABLE = False
    print("HID libraries not available")

# ======================================================================
# SERIAL COMMAND PROTOCOL
# ======================================================================
# Commands from PC:
#   MOVE <x> <y> <duration_ms>   - move mouse with human-like curve
#   CLICK <button>                - 0=left, 1=middle, 2=right
#   PRESS <keycode>               - press a key
#   TYPE <text>                   - type a string
#   SCROLL <delta>                - scroll wheel
#   DELAY <ms>                    - wait
#   STATUS                        - return ready/error

class PicoHIDGhost:
    def __init__(self):
        self.mouse = None
        self.keyboard = None
        self.uart = None
        self.buffer = ""
        self.running = True
        
        if HID_AVAILABLE:
            try:
                self.mouse = Mouse(usb_hid.Device)
                self.keyboard = Keyboard(usb_hid.Device)
                print("HID devices initialized")
            except Exception as e:
                print(f"HID init error: {e}")
        
        # Setup UART on GPIO0 (TX) and GPIO1 (RX) for PC communication
        try:
            self.uart = machine.UART(0, 115200, tx=machine.Pin(0), rx=machine.Pin(1))
            print("UART initialized on GP0/GP1")
        except Exception as e:
            print(f"UART init error: {e}")
    
    def human_move(self, dx, dy, duration_ms=500):
        """Move mouse with hardware-level human-like jitter."""
        if not self.mouse:
            return
        
        steps = max(10, duration_ms // 10)
        dx_step = dx / steps
        dy_step = dy / steps
        
        for i in range(steps):
            # Add micro-jitter that only hardware can produce
            jitter_x = machine.rng() % 3 - 1  # -1, 0, or 1
            jitter_y = machine.rng() % 3 - 1
            
            self.mouse.move(int(dx_step) + jitter_x, int(dy_step) + jitter_y)
            
            # Hardware-level timing variation
            delay_us = (duration_ms * 1000 // steps) + (machine.rng() % 200 - 100)
            time.sleep_us(max(100, delay_us))
    
    def human_click(self, button=0):
        """Hardware-level click with release jitter."""
        if not self.mouse:
            return
        
        self.mouse.press(1 << button)
        
        # Variable press duration (hardware RNG, not software PRNG)
        press_time_us = 50000 + (machine.rng() % 30000)  # 50-80ms
        time.sleep_us(press_time_us)
        
        self.mouse.release(1 << button)
        
        # Post-click settle time
        time.sleep_ms(50 + (machine.rng() % 50))
    
    def press_key(self, keycode):
        """Press and release a key with hardware timing."""
        if not self.keyboard:
            return
        
        self.keyboard.press(keycode)
        time.sleep_ms(30 + (machine.rng() % 40))
        self.keyboard.release_all()
        time.sleep_ms(20 + (machine.rng() % 30))
    
    def type_text(self, text):
        """Type text character by character with variable delays."""
        for char in text:
            if char.isupper():
                self.keyboard.press(Keycode.SHIFT)
                self.keyboard.press(getattr(Keycode, char.upper(), Keycode.SPACE))
                self.keyboard.release_all()
            elif char == ' ':
                self.press_key(Keycode.SPACE)
            elif char == '\n':
                self.press_key(Keycode.ENTER)
            else:
                self.press_key(getattr(Keycode, char.upper(), Keycode.SPACE))
            
            # Human typing variance: 50-150ms between keystrokes
            time.sleep_ms(50 + (machine.rng() % 100))
    
    def scroll(self, delta):
        """Scroll with hardware jitter."""
        if not self.mouse:
            return
        self.mouse.wheel = delta
        time.sleep_ms(20)
        self.mouse.wheel = 0
    
    def process_command(self, cmd_line):
        """Process a single command from PC."""
        parts = cmd_line.strip().split()
        if not parts:
            return "OK"
        
        cmd = parts[0].upper()
        
        try:
            if cmd == "MOVE" and len(parts) >= 4:
                x, y, dur = int(parts[1]), int(parts[2]), int(parts[3])
                self.human_move(x, y, dur)
            elif cmd == "CLICK" and len(parts) >= 2:
                btn = int(parts[1])
                self.human_click(btn)
            elif cmd == "PRESS" and len(parts) >= 2:
                kc = int(parts[1])
                self.press_key(kc)
            elif cmd == "TYPE" and len(parts) >= 2:
                text = " ".join(parts[1:])
                self.type_text(text)
            elif cmd == "SCROLL" and len(parts) >= 2:
                d = int(parts[1])
                self.scroll(d)
            elif cmd == "DELAY" and len(parts) >= 2:
                ms = int(parts[1])
                time.sleep_ms(ms)
            elif cmd == "STATUS":
                return "READY"
            elif cmd == "QUIT":
                self.running = False
                return "BYE"
            else:
                return f"ERR unknown cmd: {cmd}"
        except Exception as e:
            return f"ERR {e}"
        
        return "OK"
    
    def run(self):
        """Main loop: read serial, execute HID commands."""
        print("Pico HID Ghost v1.0 ready")
        
        # Send ready signal
        if self.uart:
            self.uart.write(b"READY\n")
        
        while self.running:
            if self.uart and self.uart.any():
                try:
                    byte = self.uart.read(1)
                    if byte:
                        char = byte.decode('utf-8', errors='ignore')
                        if char == '\n':
                            response = self.process_command(self.buffer)
                            self.uart.write((response + "\n").encode())
                            self.buffer = ""
                        else:
                            self.buffer += char
                except Exception as e:
                    print(f"Serial error: {e}")
            
            time.sleep_ms(1)


# ======================================================================
# MAIN ENTRY POINT
# ======================================================================
if __name__ == "__main__":
    ghost = PicoHIDGhost()
    ghost.run()
