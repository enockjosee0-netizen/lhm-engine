#!/usr/bin/env python3
"""
Fix field validators - move them to nested classes.
"""

from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')
BACKUP = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py.validators_backup')

text = MAIN.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)

if not BACKUP.exists():
    BACKUP.write_text(text, encoding='utf-8')
    print('Backup created')

# Find line numbers (1-indexed)
risk_end = None
ml_end = None
data_end = None
settings_validators_start = None
settings_validators_end = None

for i, line in enumerate(lines):
    if line.strip() == 'class DataSettings(BaseModel):' and risk_end is None:
        risk_end = i  # RiskSettings ends just before DataSettings
    if line.strip() == 'class RiskHardeningSettings(BaseModel):' and ml_end is None:
        ml_end = i  # MLConfig ends just before RiskHardeningSettings
    if line.strip() == 'class ExchangeSettings(BaseModel):' and data_end is None:
        data_end = i  # DataSettings ends just before ExchangeSettings
    if '@field_validator' in line and settings_validators_start is None:
        # Check if this is inside Settings class
        settings_validators_start = i
    if settings_validators_start is not None and '    def redacted_dict(self)' in line:
        settings_validators_end = i
        break

print(f'RiskSettings ends at line {risk_end}')
print(f'MLConfig ends at line {ml_end}')
print(f'DataSettings ends at line {data_end}')
print(f'Settings validators: lines {settings_validators_start+1}-{settings_validators_end+1}')

# Extract validator code
validators = ''.join(lines[settings_validators_start:settings_validators_end])

# Remove validators from Settings
new_lines = lines[:settings_validators_start] + lines[settings_validators_end:]
text = ''.join(new_lines)
lines = text.splitlines(keepends=True)

# Now find the actual end lines again in the modified text
risk_end = None
ml_end = None
data_end = None
for i, line in enumerate(lines):
    if line.strip() == 'class DataSettings(BaseModel):' and risk_end is None:
        risk_end = i
    if line.strip() == 'class RiskHardeningSettings(BaseModel):' and ml_end is None:
        ml_end = i
    if line.strip() == 'class ExchangeSettings(BaseModel):' and data_end is None:
        data_end = i

print(f'After removal - RiskSettings ends at line {risk_end}')
print(f'After removal - MLConfig ends at line {ml_end}')
print(f'After removal - DataSettings ends at line {data_end}')

# Split validators by function
validator_functions = []
current = []
for line in validators.splitlines(keepends=True):
    if line.startswith('    @field_validator') and current:
        validator_functions.append(''.join(current))
        current = [line]
    else:
        current.append(line)
if current:
    validator_functions.append(''.join(current))

print(f'Found {len(validator_functions)} validator functions')

# Categorize validators
risk_validators = []
ml_validators = []
data_validators = []
settings_validators = []

for vf in validator_functions:
    if 'risk.max_stake_per_bet' in vf or 'risk.fractional_kelly_factor' in vf or 'risk.min_single_edge' in vf:
        risk_validators.append(vf)
    elif 'ml.deepseek_api_key' in vf or 'ml.deepseek_api_base_url' in vf or 'ml.deepseek_model' in vf:
        ml_validators.append(vf)
    elif 'data.proxy_list' in vf:
        data_validators.append(vf)
    else:
        settings_validators.append(vf)

print(f'Risk validators: {len(risk_validators)}')
print(f'ML validators: {len(ml_validators)}')
print(f'Data validators: {len(data_validators)}')
print(f'Settings validators: {len(settings_validators)}')

# Insert validators before the end of each class
# RiskSettings - insert before DataSettings
if risk_validators:
    insert_pos = risk_end
    for vf in risk_validators:
        lines.insert(insert_pos, vf)
        insert_pos += 1
    print(f'Inserted {len(risk_validators)} validators into RiskSettings')

# Recalculate positions after insertion
for i, line in enumerate(lines):
    if line.strip() == 'class RiskHardeningSettings(BaseModel):' and ml_end is None:
        ml_end = i
    if line.strip() == 'class ExchangeSettings(BaseModel):' and data_end is None:
        data_end = i

# MLConfig - insert before RiskHardeningSettings
if ml_validators:
    insert_pos = ml_end
    for vf in ml_validators:
        lines.insert(insert_pos, vf)
        insert_pos += 1
    print(f'Inserted {len(ml_validators)} validators into MLConfig')

# Recalculate positions
for i, line in enumerate(lines):
    if line.strip() == 'class ExchangeSettings(BaseModel):' and data_end is None:
        data_end = i

# DataSettings - insert before ExchangeSettings
if data_validators:
    insert_pos = data_end
    for vf in data_validators:
        lines.insert(insert_pos, vf)
        insert_pos += 1
    print(f'Inserted {len(data_validators)} validators into DataSettings')

# Write back
MAIN.write_text(''.join(lines), encoding='utf-8')
print('Validators moved to nested classes successfully')
