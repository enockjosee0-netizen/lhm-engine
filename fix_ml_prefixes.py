with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("'ml.deepseek_api_base_url'", "'deepseek_api_base_url'")
content = content.replace("'ml.deepseek_model'", "'deepseek_model'")

with open(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed remaining ml. prefixes')
