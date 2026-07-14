#!/usr/bin/env python3
"""
Ghost Protocol Persistent Service
Runs 24/7, auto-restarts on failure, survives reboots via startup shortcut.
"""

import sys
import time
import logging
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ghost_protocol import GhostProtocol, GhostConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("ghost_protocol.log"),
        logging.StreamHandler()
    ]
)

log = logging.getLogger("Ghost.Service")

def main():
    """Run Ghost Protocol with auto-restart."""
    config = GhostConfig(enabled=True)
    
    while True:
        try:
            ghost = GhostProtocol(config)
            ghost.run_session()
        except Exception as e:
            log.error(f"Session crashed: {e}")
            log.error(traceback.format_exc())
            log.info("Restarting in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    main()
