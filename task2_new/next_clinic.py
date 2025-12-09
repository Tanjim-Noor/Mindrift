#!/usr/bin/env python3
"""
AUTOMATED SCRAPING COORDINATOR
This script helps identify and process the next clinic systematically.
Run this between Apify calls to get the next clinic URL.
"""

import json
from pathlib import Path

JSON_FILE = Path("data/clinic_service_2.json")

def get_next_unscraped_clinic():
    """Get the next single clinic that needs scraping."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    # Iterate through regions in order
    for region in sorted(data.get('regions', {}).keys()):
        for clinic_name, info in data['regions'][region].get('clinics', {}).items():
            if not info.get('scraped', False):
                return region, clinic_name, info.get('link', '')
    
    return None, None, None

def count_progress():
    """Count total and scraped clinics."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    total = 0
    scraped = 0
    
    for region_data in data.get('regions', {}).values():
        for clinic_info in region_data.get('clinics', {}).values():
            total += 1
            if clinic_info.get('scraped'):
                scraped += 1
    
    return total, scraped

def main():
    total, scraped = count_progress()
    remaining = total - scraped
    
    print(f"\n{'='*70}")
    print(f"NEXT CLINIC TO SCRAPE")
    print(f"Progress: {scraped}/{total} ({100*scraped//total}%) | Remaining: {remaining}")
    print(f"{'='*70}\n")
    
    region, clinic_name, url = get_next_unscraped_clinic()
    
    if region and clinic_name:
        print(f"CLINIC #{scraped + 1}:")
        print(f"Region: {region}")
        print(f"Name: {clinic_name}")
        print(f"\nURL FOR APIFY (copy and use in mcp_apify_rag-web-browser):")
        print(f"{url}\n")
        print(f"WORKFLOW:")
        print(f"1. Copy the URL above")
        print(f"2. Call: mcp_apify_rag-web-browser with query='{url}'")
        print(f"3. Extract services using regex from markdown")
        print(f"4. Update JSON with save_clinic_to_json('{region}', '{clinic_name}', services_list)")
        print(f"5. Run: python next_clinic.py (for next clinic)\n")
    else:
        print(f"✓✓✓ ALL {total} CLINICS COMPLETED! ✓✓✓\n")

if __name__ == "__main__":
    main()
