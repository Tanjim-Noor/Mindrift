#!/usr/bin/env python3
"""
Batch save clinic #5 and prepare for mass scraping.
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

# CLINIC #5: Allsports Podiatry Red Hill
CLINIC_5_SERVICES = [
    "Clinical Podiatry",
    "Health Funds",
    "Custom Foot Orthotics",
    "Video Gait Analysis",
    "Diabetes and Footcare",
    "National Disability Insurance Scheme (NDIS)",
    "CAM Walker (Moon Boot)",
    "Resources"
]

print("SAVING CLINIC #5: Allsports Podiatry Red Hill")
if save_clinic_services("Brisbane", "Allsports Podiatry Red Hill", CLINIC_5_SERVICES):
    print(f"✓ Saved {len(CLINIC_5_SERVICES)} services\n")
else:
    print("✗ Error saving\n")

# Check progress
with open(JSON_FILE, 'r') as f:
    data = json.load(f)

total = 0
scraped = 0
for region, clinics_data in data.get('regions', {}).items():
    for clinic, info in clinics_data.get('clinics', {}).items():
        total += 1
        if info.get('scraped'):
            scraped += 1

print(f"PROGRESS: {scraped}/{total} clinics saved")
print(f"Remaining: {total - scraped} clinics to scrape")
