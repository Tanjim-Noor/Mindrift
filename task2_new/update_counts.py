#!/usr/bin/env python3
"""
Recompute total clinics and update metadata & a few generated data files + prompt docs
"""
import json
from pathlib import Path
from datetime import datetime

BASE = Path('d:/Work/Mindrift/task2_new')
CLINIC_JSON = BASE / 'data' / 'clinic_service_2.json'

# Read main JSON
with CLINIC_JSON.open('r', encoding='utf-8') as f:
    data = json.load(f)

regions = data.get('regions', {})
# Recompute totals
total = 0
clinics_with_links = 0
scraped_count = 0
region_counts = {}

for region_name, region_data in regions.items():
    clinics = region_data.get('clinics', {})
    region_total = len(clinics)
    region_scraped = sum(1 for c in clinics.values() if c.get('scraped'))
    region_links = sum(1 for c in clinics.values() if c.get('link'))
    region_counts[region_name] = {
        'total': region_total,
        'scraped': region_scraped,
        'pending': region_total - region_scraped,
    }
    total += region_total
    clinics_with_links += region_links
    scraped_count += region_scraped

pending = total - scraped_count
completion = 0.0 if total == 0 else round((scraped_count/total)*100, 2)

# Update scrape_metadata
if 'scrape_metadata' not in data:
    data['scrape_metadata'] = {}
data['scrape_metadata']['total_clinics'] = total
data['scrape_metadata']['clinics_with_links'] = clinics_with_links

# Save updated main JSON
with CLINIC_JSON.open('w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f'Updated main JSON metadata: total_clinics={total}, clinics_with_links={clinics_with_links}, scraped={scraped_count}, pending={pending}')

# Update services_summary.json if exists
SERV_SUM = BASE / 'data' / 'services_summary.json'
if SERV_SUM.exists():
    with SERV_SUM.open('r', encoding='utf-8') as f:
        ss = json.load(f)
    ss['timestamp'] = datetime.utcnow().isoformat()
    ss['total_clinics'] = total
    ss['total_scraped'] = scraped_count
    ss['total_pending'] = pending
    ss['completion_percentage'] = completion
    ss['regions_status'] = region_counts
    with SERV_SUM.open('w', encoding='utf-8') as f:
        json.dump(ss, f, indent=2, ensure_ascii=False)
    print('Updated services_summary.json')

# Update clinics_by_region.json if exists
CLINICS_BY_REGION = BASE / 'data' / 'clinics_by_region.json'
if CLINICS_BY_REGION.exists():
    with CLINICS_BY_REGION.open('r', encoding='utf-8') as f:
        cbr = json.load(f)
    cbr['total_clinics_discovered'] = total
    with CLINICS_BY_REGION.open('w', encoding='utf-8') as f:
        json.dump(cbr, f, indent=2, ensure_ascii=False)
    print('Updated clinics_by_region.json')

# Update clinic_comparison_report.json if exists
COMPARE = BASE / 'data' / 'clinic_comparison_report.json'
if COMPARE.exists():
    with COMPARE.open('r', encoding='utf-8') as f:
        cr = json.load(f)
    # Update fields if present
    if 'total_clinics_in_clinics_data' in cr:
        cr['total_clinics_in_clinics_data'] = total
    if 'total_clinics_in_clinic_services' in cr:
        cr['total_clinics_in_clinic_services'] = total
    if 'total_matching_clinics' in cr:
        cr['total_matching_clinics'] = total
    with COMPARE.open('w', encoding='utf-8') as f:
        json.dump(cr, f, indent=2, ensure_ascii=False)
    print('Updated clinic_comparison_report.json')

# Update summary_report.json if exists
SUMMARY = BASE / 'summary_report.json'
if SUMMARY.exists():
    with SUMMARY.open('r', encoding='utf-8') as f:
        sr = json.load(f)
    sr['total_clinics'] = total
    with SUMMARY.open('w', encoding='utf-8') as f:
        json.dump(sr, f, indent=2, ensure_ascii=False)
    print('Updated summary_report.json')

# Update textual docs with simple replacement of '104' to current total in relevant files
MD_FILES = [BASE / 'CONTINUATION_PROMPT_FOR_LLM.md', BASE / 'LLM_CONTINUATION_PROMPT.md', BASE / 'task2_prompt_and_response.md']
for md in MD_FILES:
    if md.exists():
        text = md.read_text(encoding='utf-8')
        text = text.replace('104', str(total))
        md.write_text(text, encoding='utf-8')
        print(f'Updated {md.name}')

# Update show_progress.py docstring (first line mentioning '104 clinics')
SHOW = BASE / 'show_progress.py'
if SHOW.exists():
    txt = SHOW.read_text(encoding='utf-8')
    txt = txt.replace('104', str(total))
    SHOW.write_text(txt, encoding='utf-8')
    print('Updated show_progress.py description')

print('All updates complete.')
