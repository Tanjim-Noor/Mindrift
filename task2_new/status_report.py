#!/usr/bin/env python3
"""
COMPREHENSIVE CLINIC SCRAPING STATUS REPORT & CONTINUATION PLAN
Shows: current progress, remaining clinics list, and systematic approach to completion
"""

import json
from pathlib import Path
from collections import defaultdict

JSON_FILE = Path("data/clinic_service_2.json")

def generate_report():
    with open(JSON_FILE, 'r') as f:
        data = json.load(f)
    
    print("\n" + "="*80)
    print(" " * 20 + "CLINIC SCRAPING STATUS REPORT")
    print("="*80 + "\n")
    
    # SECTION 1: Overall Progress
    total = 0
    scraped = 0
    by_region_total = defaultdict(int)
    by_region_scraped = defaultdict(int)
    
    for region, clinics_data in data.get('regions', {}).items():
        for clinic, info in clinics_data.get('clinics', {}).items():
            total += 1
            by_region_total[region] += 1
            if info.get('scraped'):
                scraped += 1
                by_region_scraped[region] += 1
    
    print(f"OVERALL PROGRESS: {scraped}/{total} clinics ({100*scraped//total}%)")
    print(f"Scraped: {scraped} | Remaining: {total - scraped}\n")
    
    # SECTION 2: Progress by Region
    print("-" * 80)
    print("PROGRESS BY REGION:")
    print("-" * 80)
    
    for region in sorted(by_region_total.keys()):
        s = by_region_scraped[region]
        t = by_region_total[region]
        pct = 100 * s // t if t > 0 else 0
        bar_filled = int(pct / 5)
        bar = "█" * bar_filled + "░" * (20 - bar_filled)
        print(f"{region:20} [{bar}] {s:2}/{t:2} ({pct:3}%)")
    
    print("\n" + "-" * 80)
    print("CLINICS ALREADY SCRAPED (6 total):")
    print("-" * 80 + "\n")
    
    count = 1
    for region in sorted(data.get('regions', {}).keys()):
        for clinic_name, info in sorted(data['regions'][region].get('clinics', {}).items()):
            if info.get('scraped'):
                services_count = len(info.get('services', []))
                print(f"{count:2}. {clinic_name:50} ({services_count} services)")
                count += 1
    
    print("\n")

if __name__ == "__main__":
    generate_report()
