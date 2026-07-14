with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_config = '''    model_config = ConfigDict(
        env_file=".env",
        env_prefix="LHM_",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )'''

new_config = '''    model_config = ConfigDict(
        env_file=".env",
        env_prefix="LHM_",
        env_nested_delimiter="__",
        case_sensitive=False,
        env_file_encoding="utf-8",
        extra="ignore",
    )'''

if old_config in content:
    content = content.replace(old_config, new_config, 1)
    with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added env_nested_delimiter to Settings model_config')
else:
    print('Could not find model_config')
