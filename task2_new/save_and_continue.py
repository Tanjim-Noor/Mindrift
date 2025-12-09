#!/usr/bin/env python3
"""
Save clinic data and get next clinic
"""
import json
import sys
from pathlib import Path

if len(sys.argv) < 4:
    print("Usage: python save_and_continue.py <region> <clinic_name> <service1,service2,...>")
    sys.exit(1)

region = sys.argv[1]
clinic_name = sys.argv[2]
services_str = sys.argv[3]
services = [s.strip() for s in services_str.split('|')]

# Handle an empty services argument -> store an empty list instead of ['']
if len(services) == 1 and services[0] == "":
    services = []

# Save to JSON
json_file = Path("data/clinic_service_2.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

if region in data['regions'] and clinic_name in data['regions'][region]['clinics']:
    data['regions'][region]['clinics'][clinic_name]['services'] = services
    data['regions'][region]['clinics'][clinic_name]['scraped'] = True
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'✓ {clinic_name}: {len(services)} services saved')
else:
    print(f'✗ ERROR: Could not find {clinic_name} in {region}')
