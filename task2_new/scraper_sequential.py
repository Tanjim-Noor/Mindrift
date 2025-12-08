#!/usr/bin/env python3
"""
Sequential Clinic Services Scraper
Scrapes each clinic one at a time, extracts services, updates JSON immediately
NO PARALLEL PROCESSING - ONE CLINIC AT A TIME
"""

import json
import re
from pathlib import Path
from typing import List, Tuple

DATA_FILE = Path(__file__).parent / "data" / "clinic_service_2.json"

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services ONLY from ### headings in Services Available section"""
    services = []
    
    # Find "Services Available" section
    services_match = re.search(
        r'##\s*Services?\s+Available.*?(?=\n##|\n###|\Z)',
        markdown,
        re.IGNORECASE | re.DOTALL
    )
    
    if not services_match:
        return []
    
    services_section = services_match.group(0)
    
    # Extract ### heading lines (service titles)
    service_lines = re.findall(r'^###\s+(.+?)(?:\n|$)', services_section, re.MULTILINE)
    
    for line in service_lines:
        # Remove markdown links: [text](url) -> text
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        service_name = service_name.strip()
        
        if service_name and len(service_name) > 3:
            services.append(service_name)
    
    return services


def update_clinic_in_json(region: str, clinic_name: str, services: List[str]) -> bool:
    """Update single clinic in JSON and save immediately"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if region in data["regions"] and clinic_name in data["regions"][region]["clinics"]:
        data["regions"][region]["clinics"][clinic_name]["services"] = services
        data["regions"][region]["clinics"][clinic_name]["scraped"] = True
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False


def get_unscraped_clinics() -> List[Tuple[str, str, str]]:
    """Get list of unscraped clinics: [(region, clinic_name, url), ...]"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    unscraped = []
    for region, region_data in sorted(data.get("regions", {}).items()):
        for clinic_name, clinic_info in sorted(region_data.get("clinics", {}).items()):
            if not clinic_info.get("scraped", False):
                unscraped.append((
                    region,
                    clinic_name,
                    clinic_info.get("link", "")
                ))
    
    return unscraped


def get_scraping_progress():
    """Get progress: (total, scraped, remaining)"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    total = 0
    scraped = 0
    
    for region_data in data.get("regions", {}).values():
        for clinic_info in region_data.get("clinics", {}).values():
            total += 1
            if clinic_info.get("scraped", False):
                scraped += 1
    
    return total, scraped, total - scraped


if __name__ == "__main__":
    total, scraped, remaining = get_scraping_progress()
    print(f"\n{'='*80}")
    print(f"SEQUENTIAL CLINIC SCRAPER - ONE AT A TIME")
    print(f"{'='*80}")
    print(f"Total: {total} | Scraped: {scraped} | Remaining: {remaining}")
    print(f"{'='*80}\n")
    
    if remaining == 0:
        print("✓ All clinics already scraped!")
    else:
        print("Ready to scrape remaining clinics sequentially.")
        print("Use scraper_sequential_execute.py to start scraping.\n")
