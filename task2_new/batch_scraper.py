#!/usr/bin/env python3
"""
Batch scraper for clinic services - processes multiple clinics sequentially
"""

import json
import re
import subprocess
from pathlib import Path
from typing import List, Tuple

def get_next_clinic_info() -> Tuple[str, str, str]:
    """Get the next clinic to scrape using next_clinic.py"""
    result = subprocess.run(['python', 'next_clinic.py'], capture_output=True, text=True)
    output = result.stdout
    
    # Extract region, clinic name, and URL from output
    region_match = re.search(r'Region: (.+?)$', output, re.MULTILINE)
    name_match = re.search(r'Name: (.+?)$', output, re.MULTILINE)
    url_match = re.search(r'URL FOR APIFY.*?\n(https://[^\n]+)', output, re.MULTILINE | re.DOTALL)
    
    if region_match and name_match and url_match:
        return region_match.group(1).strip(), name_match.group(1).strip(), url_match.group(1).strip()
    return None, None, None

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services from markdown using regex."""
    services = []
    
    # Find Services Available section
    services_match = re.search(
        r'##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)',
        markdown,
        re.IGNORECASE | re.DOTALL
    )
    
    if not services_match:
        return []  # No services section - return empty list
    
    services_section = services_match.group(0)
    
    # Extract all ### level headings
    service_lines = re.findall(r'^###\s+\[?([^\]]+)\]?', services_section, re.MULTILINE)
    
    for line in service_lines:
        # Remove markdown links [text](url) → text
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        # Remove leading characters that aren't part of the service name
        service_name = re.sub(r'^[^a-zA-Z]*', '', service_name)
        service_name = service_name.strip()
        
        # Only add meaningful services
        if service_name and len(service_name) > 3:
            services.append(service_name)
    
    return services

def save_clinic_to_json(region: str, clinic_name: str, services: List[str]) -> bool:
    """Update JSON with scraped services."""
    json_file = Path("data/clinic_service_2.json")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if region in data.get("regions", {}) and clinic_name in data["regions"][region].get("clinics", {}):
            data["regions"][region]["clinics"][clinic_name]["services"] = services
            data["regions"][region]["clinics"][clinic_name]["scraped"] = True
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        else:
            print(f"✗ ERROR: Could not find {clinic_name} in {region}")
            return False
    except Exception as e:
        print(f"✗ ERROR saving {clinic_name}: {str(e)}")
        return False

def scrape_clinic(region: str, clinic_name: str, url: str) -> bool:
    """Scrape a single clinic using Apify API (placeholder)"""
    # This would call mcp_apify_rag-web-browser
    # For now, return False to indicate we need to use the main script
    return False

if __name__ == "__main__":
    print("Batch Scraper Ready - Use main scraping script")
    print("This module provides helper functions for batch processing")
