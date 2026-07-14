with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "_auto_fields = {\n            'enable_auto_self_test', 'enable_auto_backtest_cycle', 'enable_auto_adaptation_cycle',"
new = "_auto_fields = {\n            'enable_auto_self_test', 'enable_auto_backtest_cycle', 'enable_auto_adaptation_cycle', 'enable_auto_vacuum', 'enable_migration_retry', 'enable_file_watcher', 'enable_health_server',"

content = content.replace(old, new)

with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed enable_auto_vacuum backward compat')
