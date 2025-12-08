#!/usr/bin/env python3
"""Debug markdown extraction."""

import re

MARKDOWN = r"""## Services Available

### [Clinical Podiatry](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

Our centres provide the full scope of clinical podiatry including comprehensive foot assessments, various treatments and surgery.

### [Health Funds](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/health-funds/)

At My FootDr we are passionate about providing all our patient's treatment options that lead to better health outcomes for not only themselves, but their families too.

### [Custom Foot Orthotics](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/custom-foot-orthotics/)

Our custom foot orthotics are manufactured with precision from digital foot scans and are typically available on the same day.

### [Video Gait Analysis](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/video-gait-analysis/)

We use this advanced form of motion analysis to assists us in diagnosing complex motion related pathology of the foot, ankle, knee hip and lower back.

### [Diabetes and Footcare](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/diabetes-and-footcare/)

Regular podiatric care plays an integral role in the prevention of diabetic foot complications.

### [National Disability Insurance Scheme (NDIS)](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/national-disability-insurance-scheme-ndis/)

My FootDr is a proud supporter of the NDIS and are an innovative, nationally registered provider of podiatry services to NDIS participants across Australia.

### [Seniors Footcare](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/seniors-footcare/)

With Australia's advancing aged population, it has never been more important to highlight foot care in the elderly.

### [Resources](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/resources/)

Useful resources for doctors including our Referral Form.

## Local News"""

# Test regex - need to capture from "Services Available" all the way to next ## header
print("Looking for Services Available section...")
services_match = re.search(
    r'##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)',
    MARKDOWN,
    re.IGNORECASE | re.DOTALL
)

if services_match:
    print("✓ Found Services Available section")
    services_section = services_match.group(0) if services_match.group(0) else services_match.group(1)
    print(f"Section length: {len(services_section)} chars")
    print(f"First 500 chars:\n{services_section[:500]}\n...")
    
    # Find ### headings
    service_lines = re.findall(r'^###\s+(.+?)(?:\n|$)', services_section, re.MULTILINE)
    print(f"\nFound {len(service_lines)} service lines:")
    for line in service_lines:
        print(f"  Raw: {line[:60]}")
        # Remove markdown links
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        service_name = service_name.strip()
        print(f"  Clean: {service_name}")
else:
    print("✗ Services Available section not found")
