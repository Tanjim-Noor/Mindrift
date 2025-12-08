#!/usr/bin/env python3
"""
Batch save scraped clinics to JSON.
Run this after getting markdown from Apify scraping.
"""

import json
import re
from pathlib import Path
from typing import List

JSON_FILE = Path("data/clinic_service_2.json")

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services from markdown using correct regex."""
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

def save_clinic_to_json(region: str, clinic_name: str, services: List[str]) -> bool:
    """Update JSON with scraped clinic services."""
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    if region in data.get('regions', {}) and clinic_name in data['regions'][region].get('clinics', {}):
        data['regions'][region]['clinics'][clinic_name]['services'] = services
        data['regions'][region]['clinics'][clinic_name]['scraped'] = True
        
        with open(JSON_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    return False

# CLINIC #4: Allsports Podiatry Indooroopilly
MARKDOWN_C4 = r"""## Services Available

### [Clinical Podiatry](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

Our centres provide the full scope of clinical podiatry including comprehensive foot assessments, various treatments and surgery.

### [Health Funds](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/health-funds/)

At My FootDr we are passionate about providing all our patient's treatment options that lead to better health outcomes for not only themselves, but their families too.

### [Custom Foot Orthotics](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/custom-foot-orthotics/)

Our custom foot orthotics are manufactured with precision from digital foot scans and are typically available on the same day.

### [Video Gait Analysis](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/video-gait-analysis/)

We use this advanced form of motion analysis to assists us in diagnosing complex motion related pathology of the foot, ankle, knee hip and lower back.

### [Diabetes and Footcare](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/diabetes-and-footcare/)

Regular podiatric care plays an integral role in the prevention of diabetic foot complications.

### [National Disability Insurance Scheme (NDIS)](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/national-disability-insurance-scheme-ndis/)

My FootDr is a proud supporter of the NDIS and are an innovative, nationally registered provider of podiatry services to NDIS participants across Australia.

### [CAM Walker (Moon Boot)](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/cam-walker-moon-boot/)

CAM Walkers, otherwise known as Moon Boots, are an integral part of the recovery process for many patients with foot, ankle or lower leg injuries.

### [Seniors Footcare](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/seniors-footcare/)

With Australia's advancing aged population, it has never been more important to highlight foot care in the elderly.

### [Resources](https://web.archive.org/web/20250707233946/https://www.myfootdr.com.au/our-services/resources/)

Useful resources for doctors including our Referral Form.

## Local News"""

if __name__ == "__main__":
    print("PROCESSING CLINIC #4: Allsports Podiatry Indooroopilly")
    services = extract_services_from_markdown(MARKDOWN_C4)
    print(f"Extracted: {len(services)} services")
    for svc in services:
        print(f"  • {svc}")
    
    if save_clinic_to_json("Brisbane", "Allsports Podiatry Indooroopilly", services):
        print("✓ SAVED to clinic_service_2.json\n")
    else:
        print("✗ ERROR saving clinic\n")
