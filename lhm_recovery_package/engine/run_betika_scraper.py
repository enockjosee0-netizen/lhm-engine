#!/usr/bin/env python3
"""Run Betika web scraper to fetch odds."""
import subprocess
import sys
import os

SCRAPER_DIR = os.path.join(os.path.dirname(__file__), "integrations", "smartBetika")

def main():
    if not os.path.exists(SCRAPER_DIR):
        print("ERROR: smartBetika not found at", SCRAPER_DIR)
        print("Falling back to Ezee-Kits BETPAWA-WEB-SCRAPER for Betika-style data...")
        scraper_dir = os.path.join(os.path.dirname(__file__), "integrations", "betpawa-web-scraper")
        if os.path.exists(scraper_dir):
            print("Run manually:", os.path.join(scraper_dir, "betpawa.py"))
        sys.exit(1)
    cmd = [sys.executable, os.path.join(SCRAPER_DIR, "main.py"), "--normal", "--upcoming"]
    print("Starting Betika scraper...")
    print("Command:", " ".join(cmd))
    proc = subprocess.Popen(cmd, cwd=SCRAPER_DIR)
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nStopping scraper...")
        proc.terminate()
        proc.wait()
    sys.exit(proc.returncode)

if __name__ == "__main__":
    main()
