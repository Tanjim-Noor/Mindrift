#!/usr/bin/env python3
import json

with open('data/clinic_service_2.json', 'r') as f:
    data = json.load(f)

total = 0
scraped = 0
saved_clinics = []

for region, clinics_data in data.get('regions', {}).items():
    for clinic, info in clinics_data.get('clinics', {}).items():
        total += 1
        if info.get('scraped'):
            scraped += 1
            saved_clinics.append(f"{clinic}: {len(info['services'])} services")

print("CLINICS WITH SERVICES SAVED:")
for clinic_info in saved_clinics:
    print(f"✓ {clinic_info}")

print(f"\nTOTAL: {total} clinics")
print(f"SCRAPED: {scraped}")
print(f"REMAINING: {total - scraped}")
