with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find API-related sections
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'api' in line.lower() and ('http' in line.lower() or 'endpoint' in line.lower() or 'url' in line.lower()):
        print(f'{i+1}: {line}')
