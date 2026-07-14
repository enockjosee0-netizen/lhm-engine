import sys
sys.path.insert(0, r'C:\Users\enock\Downloads')
import deepseek_python_20260707_a6bd19 as m

c = m.CONFIG
print('=== FINAL VERIFICATION ===')
print(f'Config loaded: {c is not None}')
print(f'Has stealth: {hasattr(c, "stealth")}')
print(f'Has security: {hasattr(c, "security")}')
print(f'Has ghost_protocol: {hasattr(m, "GhostProtocol")}')
print(f'Has PicoHIDInterface: {hasattr(m, "PicoHIDInterface")}')
print(f'Has VisionEngine: {hasattr(m, "VisionEngine")}')
print(f'secret_key set: {bool(c.security.secret_key)}')
print(f'encryption_key set: {bool(c.security.encryption_key)}')
print(f'telegram_token set: {bool(c.notification.telegram_token)}')
print(f'use_free_scrapers: {c.use_free_scrapers}')
print(f'dry_run: {c.dry_run}')
print('==========================')
