with open(r'C:\Users\enock\Downloads\lhm_enhanced.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Simple URL extraction
words = content.split()
urls = [w for w in words if w.startswith('http://') or w.startswith('https://')]
for u in sorted(set(urls))[:30]:
    print(u)
