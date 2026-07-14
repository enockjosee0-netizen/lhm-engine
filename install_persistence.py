#!/usr/bin/env python3
"""
LHM + Ghost Protocol Persistent Installer
Installs auto-start on boot using Windows Task Scheduler and Startup folder.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(levelname)s: %(message)s')
log = logging.getLogger("LHM.Installer")

DOWNLOADS = Path(r"C:\Users\enock\Downloads")
STARTUP = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"))


def create_startup_shortcut():
    """Create startup shortcut for Ghost Protocol + Engine."""
    bat_path = DOWNLOADS / "start_lhm_ghost.bat"
    shortcut_path = STARTUP / "LHM_Ghost_Protocol.bat"
    
    # Create a wrapper bat that points to the actual launcher
    wrapper = f"""@echo off
cd /d "{DOWNLOADS}"
start /B "" "{bat_path}"
"""
    shortcut_path.write_text(wrapper)
    log.info(f"Created startup shortcut: {shortcut_path}")
    return True


def install_task_scheduler():
    """Install Windows Task Scheduler tasks for both services."""
    python_exe = sys.executable
    
    # Task for Ghost Protocol
    ghost_task_name = "LHM_GhostProtocol"
    ghost_cmd = f'schtasks /create /tn "{ghost_task_name}" /tr "\\"{python_exe}\\" \\"{DOWNLOADS / "ghost_protocol_service.py"}\\"" /sc onlogon /ru "{os.getlogin()}" /rl HIGHEST /f'
    
    # Task for Main Engine
    engine_task_name = "LHM_Engine"
    engine_cmd = f'schtasks /create /tn "{engine_task_name}" /tr "\\"{python_exe}\\" \\"{DOWNLOADS / "deepseek_python_20260707_a6bd19.py"}\\"" /sc onlogon /ru "{os.getlogin()}" /rl HIGHEST /f'
    
    try:
        subprocess.run(ghost_cmd, shell=True, check=True, capture_output=True)
        log.info(f"Created Task Scheduler task: {ghost_task_name}")
    except subprocess.CalledProcessError as e:
        log.warning(f"Task Scheduler ghost task failed: {e}")
    
    try:
        subprocess.run(engine_cmd, shell=True, check=True, capture_output=True)
        log.info(f"Created Task Scheduler task: {engine_task_name}")
    except subprocess.CalledProcessError as e:
        log.warning(f"Task Scheduler engine task failed: {e}")


def main():
    log.info("=" * 60)
    log.info("LHM Ghost Protocol + Engine Persistent Installer")
    log.info("=" * 60)
    
    # Create startup shortcut
    create_startup_shortcut()
    
    # Install Task Scheduler tasks
    install_task_scheduler()
    
    log.info("")
    log.info("Persistence setup complete!")
    log.info("Services will auto-start on next reboot.")
    log.info("")
    log.info("To start now:")
    log.info(f"  1. Run: {DOWNLOADS / 'ghost_protocol_service.py'}")
    log.info(f"  2. Run: {DOWNLOADS / 'deepseek_python_20260707_a6bd19.py'}")
    log.info("")
    log.info("To remove auto-start:")
    log.info("  - Delete from Startup folder: %APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\LHM_Ghost_Protocol.bat")
    log.info("  - Or run: schtasks /delete /tn LHM_GhostProtocol /f")
    log.info("  - Or run: schtasks /delete /tn LHM_Engine /f")


if __name__ == "__main__":
    main()
