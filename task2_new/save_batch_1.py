#!/usr/bin/env python3
"""
Batch save multiple clinics at once.
Clinics #6-15 (first 10 batch of remaining Brisbane clinics)
"""

import json
from pathlib import Path

JSON_FILE = Path("data/clinic_service_2.json")

def save_clinic_services(region: str, clinic_name: str, services: list):
    """Save a clinic's services to JSON."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    if region in data.get('regions', {}) and clinic_name in data['regions'][region].get('clinics', {}):
        data['regions'][region]['clinics'][clinic_name]['services'] = services
        data['regions'][region]['clinics'][clinic_name]['scraped'] = True
        
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False

# CLINIC #6: Allsports Podiatry Camp Hill
clinics_batch_1 = [
    ("Allsports Podiatry Camp Hill", [
        "Clinical Podiatry",
        "Health Funds",
        "Custom Foot Orthotics",
        "Video Gait Analysis",
        "Diabetes and Footcare",
        "National Disability Insurance Scheme (NDIS)",
        "CAM Walker (Moon Boot)",
        "Seniors Footcare",
        "Resources"
    ])
]

print("SAVING BATCH 1 (Brisbane):\n")
for clinic_name, services in clinics_batch_1:
    if save_clinic_services("Brisbane", clinic_name, services):
        print(f"✓ {clinic_name}: {len(services)} services")

# Check total progress
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

total = 0
scraped = 0
for region, clinics_data in data.get('regions', {}).items():
    for clinic, info in clinics_data.get('clinics', {}).items():
        total += 1
        if info.get('scraped'):
            scraped += 1

print(f"\n{'='*50}")
print(f"TOTAL PROGRESS: {scraped}/{total} clinics ({100*scraped//total}%)")
print(f"Remaining: {total - scraped} clinics")
print(f"{'='*50}\n")
