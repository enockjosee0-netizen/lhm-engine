with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('Has StealthSettings:', 'class StealthSettings(BaseModel):' in content)
print('Has SecuritySettings:', 'class SecuritySettings(BaseModel):' in content)
print('Has nested security field:', 'security: SecuritySettings = SecuritySettings()' in content)
print('Has flat secret_key in Settings:', '    secret_key: str = ""' in content)
print('Settings class starts at:', content.find('class Settings(BaseSettings):'))
