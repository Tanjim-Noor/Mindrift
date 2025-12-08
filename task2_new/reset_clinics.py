"""
Reset clinic_service_2.json - Clear all services and set scraped=false
to start fresh with correct scraping
"""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CLINIC_DATA_FILE = DATA_DIR / "clinic_service_2.json"

with open(CLINIC_DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Reset all clinics
reset_count = 0
for region in data.get("regions", {}).values():
    for clinic in region.get("clinics", {}).values():
        clinic["services"] = []
        clinic["scraped"] = False
        reset_count += 1

with open(CLINIC_DATA_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"✓ Reset {reset_count} clinics - all services cleared, scraped=false")
