#!/usr/bin/env python3
"""Run BetPawa odds scraper (lorenzosntr-pawa/odds-scraper) as a subprocess."""
import subprocess
import sys
import os

SCRAPER_DIR = os.path.join(os.path.dirname(__file__), "integrations", "odds-scraper")
CONFIG_PATH = os.path.join(SCRAPER_DIR, "config.yaml")

def main():
    if not os.path.exists(SCRAPER_DIR):
        print("ERROR: odds-scraper not found at", SCRAPER_DIR)
        sys.exit(1)
    if not os.path.exists(CONFIG_PATH):
        print("ERROR: config.yaml not found at", CONFIG_PATH)
        sys.exit(1)
    cmd = [
        sys.executable, "-m", "odds_scraper.main",
        "--config", CONFIG_PATH,
    ]
    print("Starting BetPawa odds scraper...")
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
