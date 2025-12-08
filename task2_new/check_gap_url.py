import json
from pathlib import Path

json_file = Path("data/clinic_service_2.json")
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

gap = data['regions']['Brisbane']['clinics']['Allsports Podiatry The Gap']
print(f'The Gap URL: {gap.get("link", "N/A")}')
print(f'Scraped: {gap.get("scraped")}')
