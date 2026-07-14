#!/usr/bin/env python3
"""
Fix validator field names after moving to nested classes.
"""

from pathlib import Path

MAIN = Path(r'C:\Users\enock\Downloads\deepseek_python_20260707_a6bd19.py')

text = MAIN.read_text(encoding='utf-8')
lines = text.splitlines(keepends=True)

# Find and fix validators in RiskSettings
in_risk = False
for i, line in enumerate(lines):
    if 'class RiskSettings(BaseModel):' in line:
        in_risk = True
    if in_risk and 'class ' in line and 'RiskSettings' not in line:
        in_risk = False
    if in_risk:
        if "@field_validator('risk.max_stake_per_bet'" in line:
            lines[i] = line.replace("'risk.max_stake_per_bet'", "'max_stake_per_bet'")
        if "@field_validator('risk.fractional_kelly_factor'" in line:
            lines[i] = line.replace("'risk.fractional_kelly_factor'", "'fractional_kelly_factor'")
        if "@field_validator('risk.min_single_edge'" in line:
            lines[i] = line.replace("'risk.min_single_edge'", "'min_single_edge'")

# Find and fix validators in MLConfig
in_ml = False
for i, line in enumerate(lines):
    if 'class MLConfig(BaseModel):' in line:
        in_ml = True
    if in_ml and 'class ' in line and 'MLConfig' not in line:
        in_ml = False
    if in_ml:
        if "@field_validator('ml.deepseek_api_key', 'ml.deepseek_api_base_url', 'ml.deepseek_model'" in line:
            lines[i] = line.replace("'ml.deepseek_api_key', 'ml.deepseek_api_base_url', 'ml.deepseek_model'", "'deepseek_api_key', 'deepseek_api_base_url', 'deepseek_model'")
        if "@field_validator('ml.deepseek_api_key'" in line:
            lines[i] = line.replace("'ml.deepseek_api_key'", "'deepseek_api_key'")

# Find and fix validators in DataSettings
in_data = False
for i, line in enumerate(lines):
    if 'class DataSettings(BaseModel):' in line:
        in_data = True
    if in_data and 'class ' in line and 'DataSettings' not in line:
        in_data = False
    if in_data:
        if "@field_validator('data.proxy_list'" in line:
            lines[i] = line.replace("'data.proxy_list'", "'proxy_list'")

MAIN.write_text(''.join(lines), encoding='utf-8')
print('Fixed validator field names in nested classes')
