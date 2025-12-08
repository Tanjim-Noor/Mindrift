#!/usr/bin/env python3
"""
Master coordinator for sequential scraping of all remaining 99 clinics.
This script identifies which clinics need scraping and provides URLs for systematic processing.
"""

import json
from pathlib import Path
from collections import defaultdict

JSON_FILE = Path("data/clinic_service_2.json")

def get_unscraped_clinics_by_region():
    """Get all unscraped clinics organized by region."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    unscraped = defaultdict(list)
    
    for region, clinics_data in data.get('regions', {}).items():
        for clinic_name, info in clinics_data.get('clinics', {}).items():
            if not info.get('scraped', False):
                unscraped[region].append({
                    'name': clinic_name,
                    'url': info.get('link', '')
                })
    
    return dict(unscraped)

def main():
    unscraped = get_unscraped_clinics_by_region()
    
    total_remaining = sum(len(clinics) for clinics in unscraped.values())
    
    print(f"\n{'='*70}")
    print(f"REMAINING CLINICS TO SCRAPE: {total_remaining}")
    print(f"{'='*70}\n")
    
    # Print summary by region
    for region in sorted(unscraped.keys()):
        clinics = unscraped[region]
        print(f"{region}: {len(clinics)} clinics")
        for i, clinic in enumerate(clinics[:3], 1):  # Show first 3
            print(f"  {i}. {clinic['name']}")
        if len(clinics) > 3:
            print(f"  ... and {len(clinics) - 3} more")
        print()

if __name__ == "__main__":
    main()
