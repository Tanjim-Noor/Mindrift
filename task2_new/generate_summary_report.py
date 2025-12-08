"""
Script to generate a comprehensive summary of the scraping status and remaining work.
"""

import json
from pathlib import Path
from collections import defaultdict

def generate_summary_report():
    """Generate a comprehensive summary of scraping status"""
    
    json_file = Path("data/clinic_service_2.json")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Analyze data
    regions_data = defaultdict(lambda: {'total': 0, 'scraped': 0, 'unscraped': 0})
    total_clinics = 0
    total_scraped = 0
    total_unscraped = 0
    
    for region, region_data in data.get("regions", {}).items():
        clinics = region_data.get("clinics", {})
        
        for clinic_name, clinic_info in clinics.items():
            regions_data[region]['total'] += 1
            total_clinics += 1
            
            if clinic_info.get("scraped", False):
                regions_data[region]['scraped'] += 1
                total_scraped += 1
            else:
                regions_data[region]['unscraped'] += 1
                total_unscraped += 1
    
    # Generate report
    print("\n" + "="*100)
    print("COMPREHENSIVE SCRAPING STATUS REPORT")
    print("="*100)
    
    print(f"\nOVERALL SUMMARY:")
    print(f"-" * 100)
    print(f"Total Clinics: {total_clinics}")
    print(f"Already Scraped: {total_scraped} ({(total_scraped/total_clinics*100):.1f}%)")
    print(f"Remaining to Scrape: {total_unscraped} ({(total_unscraped/total_clinics*100):.1f}%)")
    
    print(f"\nBREAKDOWN BY REGION:")
    print(f"-" * 100)
    print(f"{'Region':<30} {'Total':<10} {'Scraped':<10} {'Unscraped':<10} {'% Complete':<15}")
    print(f"-" * 100)
    
    # Sort regions by name
    for region in sorted(regions_data.keys()):
        stats = regions_data[region]
        pct_complete = (stats['scraped'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"{region:<30} {stats['total']:<10} {stats['scraped']:<10} {stats['unscraped']:<10} {pct_complete:>6.1f}%")
    
    print(f"-" * 100)
    print(f"{'TOTALS':<30} {total_clinics:<10} {total_scraped:<10} {total_unscraped:<10} {(total_scraped/total_clinics*100):>6.1f}%")
    
    print(f"\n{'='*100}")
    print("RESOURCES GENERATED:")
    print(f"{'='*100}")
    print(f"✓ Scraping Queue: scraping_queue.txt")
    print(f"  - Lists all {total_unscraped} unscraped clinics with Wayback Machine URLs")
    print(f"  - Organized by region for easy reference")
    print(f"  - Sequential numbering for tracking progress")
    print(f"\n✓ Source Data: data/clinic_service_2.json")
    print(f"  - Complete clinic database with metadata")
    print(f"  - Scraped status for each clinic")
    print(f"\nNEXT STEPS:")
    print(f"- Use scraping_queue.txt to guide systematic scraping of remaining {total_unscraped} clinics")
    print(f"- Update clinic_service_2.json as clinics are scraped and services are extracted")
    print(f"- Track progress using numbered clinic IDs")
    print(f"{'='*100}\n")

if __name__ == "__main__":
    generate_summary_report()
