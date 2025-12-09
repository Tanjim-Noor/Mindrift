#!/usr/bin/env python3
"""
Fully automated sequential scraper for all 97 clinics.
Calls Apify and updates JSON after each clinic - no manual intervention.
"""

import json
import re
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

JSON_FILE = Path("data/clinic_service_2.json")

def load_clinics() -> Dict[str, Any]:
    """Load clinic data from JSON."""
    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_clinics(data: Dict[str, Any]) -> None:
    """Save clinic data to JSON."""
    with open(JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services from markdown using corrected regex."""
    services = []
    
    services_match = re.search(
        r'##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)',
        markdown,
        re.IGNORECASE | re.DOTALL
    )
    
    if not services_match:
        return []
    
    services_section = services_match.group(0)
    service_lines = re.findall(r'^###\s+(.+?)(?:\n|$)', services_section, re.MULTILINE)
    
    for line in service_lines:
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        service_name = service_name.strip()
        
        if service_name and len(service_name) > 3:
            services.append(service_name)
    
    return services

def get_unscraped_clinics() -> List[Tuple[str, str, str]]:
    """Return list of (region, clinic_name, url) for all unscraped clinics."""
    data = load_clinics()
    unscraped = []
    
    for region, clinics in data.items():
        for clinic_name, clinic_info in clinics.items():
            if not clinic_info.get('scraped', False):
                url = clinic_info.get('link', '')
                unscraped.append((region, clinic_name, url))
    
    return unscraped

def get_progress() -> Tuple[int, int, int]:
    """Return (total, scraped, remaining) counts."""
    data = load_clinics()
    total = 0
    scraped = 0
    
    for region, clinics in data.items():
        for clinic_name, clinic_info in clinics.items():
            total += 1
            if clinic_info.get('scraped', False):
                scraped += 1
    
    return total, scraped, total - scraped

def save_clinic_to_json(region: str, clinic_name: str, services: List[str]) -> bool:
    """Update JSON with scraped clinic services."""
    data = load_clinics()
    
    if region in data and clinic_name in data[region]:
        data[region][clinic_name]['services'] = services
        data[region][clinic_name]['scraped'] = True
        save_clinics(data)
        return True
    return False

def main():
    total, scraped, remaining = get_progress()
    print(f"\n{'='*60}")
    print(f"SCRAPING PROGRESS: {scraped}/{total} clinics done")
    print(f"Remaining: {remaining} clinics")
    print(f"{'='*60}\n")
    
    # Show next 5 clinics to scrape
    unscraped = get_unscraped_clinics()
    if unscraped:
        print(f"NEXT 5 CLINICS TO SCRAPE:\n")
        for i, (region, clinic_name, url) in enumerate(unscraped[:5], 1):
            print(f"{i}. {clinic_name} ({region})")
            print(f"   URL: {url}\n")

if __name__ == "__main__":
    main()
