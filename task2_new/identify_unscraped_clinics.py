"""
Script to identify all unscraped clinics and generate a systematic scraping queue.
This script reads the clinic_service_2.json file and lists all clinics with scraped=false
"""

import json
import os
from pathlib import Path

def identify_unscraped_clinics():
    """Read JSON and identify all unscraped clinics"""
    
    # File paths
    json_file = Path("data/clinic_service_2.json")
    output_file = Path("scraping_queue.txt")
    
    if not json_file.exists():
        print(f"Error: {json_file} not found!")
        return
    
    # Load JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collect all unscraped clinics
    unscraped_clinics = []
    clinic_number = 1
    
    for region, region_data in data.get("regions", {}).items():
        clinics = region_data.get("clinics", {})
        
        for clinic_name, clinic_info in clinics.items():
            if not clinic_info.get("scraped", False):  # If scraped is False
                unscraped_clinics.append({
                    'number': clinic_number,
                    'name': clinic_name,
                    'region': region,
                    'url': clinic_info.get('link', 'N/A'),
                    'services_count': len(clinic_info.get('services', []))
                })
                clinic_number += 1
    
    # Sort by region for grouping
    unscraped_clinics.sort(key=lambda x: x['region'])
    
    # Generate output
    total_unscraped = len(unscraped_clinics)
    print(f"\n{'='*100}")
    print(f"UNSCRAPED CLINICS IDENTIFICATION REPORT")
    print(f"{'='*100}")
    print(f"Total unscraped clinics: {total_unscraped}")
    print(f"{'='*100}\n")
    
    # Group by region and display
    current_region = None
    output_lines = [
        f"UNSCRAPED CLINICS IDENTIFICATION REPORT",
        f"Total unscraped clinics: {total_unscraped}",
        f"Generated: {Path(json_file).stat().st_mtime}",
        "",
        "="*100,
        ""
    ]
    
    for clinic in unscraped_clinics:
        # Print region header when it changes
        if clinic['region'] != current_region:
            current_region = clinic['region']
            region_clinics = [c for c in unscraped_clinics if c['region'] == current_region]
            print(f"\n{current_region.upper()} ({len(region_clinics)} clinics)")
            print("-" * 100)
            output_lines.append(f"\n{current_region.upper()} ({len(region_clinics)} clinics)")
            output_lines.append("-" * 100)
        
        # Format clinic entry
        clinic_entry = (
            f"#{clinic['number']:03d} | {clinic['name']:<50} | {clinic['region']:<25}\n"
            f"      URL: {clinic['url']}"
        )
        print(clinic_entry)
        output_lines.append(clinic_entry)
    
    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"\n{'='*100}")
    print(f"SUMMARY")
    print(f"{'='*100}")
    print(f"Total clinics in file: {data['scrape_metadata']['total_clinics']}")
    print(f"Already scraped: {data['scrape_metadata']['total_clinics'] - total_unscraped}")
    print(f"Remaining to scrape: {total_unscraped}")
    print(f"\nScraping queue saved to: {output_file.absolute()}")
    print(f"{'='*100}\n")
    
    return unscraped_clinics

if __name__ == "__main__":
    identify_unscraped_clinics()
