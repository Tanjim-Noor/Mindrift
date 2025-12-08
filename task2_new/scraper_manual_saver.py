#!/usr/bin/env python3
"""
Manual execution script - processes clinics one by one
Call this after each scrape to update JSON
"""

import json
import re
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "clinic_service_2.json"

def extract_services(markdown: str) -> list:
    """Extract services from markdown"""
    services = []
    services_match = re.search(
        r'##\s*Services?\s+Available.*?(?=\n##|\n###|\Z)',
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


def save_clinic(region: str, clinic_name: str, services: list):
    """Save clinic to JSON"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if region in data["regions"] and clinic_name in data["regions"][region]["clinics"]:
        data["regions"][region]["clinics"][clinic_name]["services"] = services
        data["regions"][region]["clinics"][clinic_name]["scraped"] = True
        
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ {clinic_name}: {len(services)} services saved")
        return True
    return False


# Usage: After scraping with mcp_apify, paste markdown and call:
# markdown = """..."""
# services = extract_services(markdown)
# save_clinic("Brisbane", "Clinic Name", services)
