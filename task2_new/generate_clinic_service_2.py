"""
Generate clinic_service_2.json from clinics_data dictionary
This script creates a new JSON file with clinic links and checks for region/clinic matching
"""

import json
from datetime import datetime

# Import clinics_data from scrape_clinics.py
import sys
sys.path.append('.')
from scrape_clinics import clinics_data

def generate_clinic_service_2():
    """
    Generate clinic_service_2.json with all clinics from clinics_data
    Structure similar to clinic_services.json but with:
    - scraped: false
    - services: empty list
    - link: clinic URL
    """
    
    # Load existing clinic_services.json to compare
    try:
        with open('data/clinic_services.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    except FileNotFoundError:
        print("Warning: clinic_services.json not found in data/")
        existing_data = {"regions": {}}
    
    # Build new structure
    new_structure = {
        "scrape_metadata": {
            "scrape_date": "2024-12-08",
            "source_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/",
            "total_clinics": sum(len(clinics) for clinics in clinics_data.values()),
            "clinics_with_links": sum(len(clinics) for clinics in clinics_data.values()),
            "notes": "All clinics from clinics_data dictionary with their links. Services empty and scraped=false as placeholder for future scraping"
        },
        "regions": {}
    }
    
    # Comparison report
    comparison_report = {
        "region_comparison": {},
        "clinic_comparison": {},
        "summary": {}
    }
    
    # Process each region
    for region, clinics in clinics_data.items():
        new_structure["regions"][region] = {"clinics": {}}
        comparison_report["region_comparison"][region] = {}
        
        # Check if region exists in existing data
        if region in existing_data.get("regions", {}):
            existing_clinics = set(existing_data["regions"][region].get("clinics", {}).keys())
        else:
            existing_clinics = set()
        
        # Process clinics in this region
        for clinic in clinics:
            clinic_name = clinic["name"]
            
            # Create clinic entry with empty services and link
            clinic_entry = {
                "services": [],
                "scraped": False,
                "link": clinic["url"]
            }
            
            new_structure["regions"][region]["clinics"][clinic_name] = clinic_entry
        
        # Compare regions and clinics
        new_clinics = set(new_structure["regions"][region]["clinics"].keys())
        
        comparison_report["region_comparison"][region] = {
            "status": "EXISTS" if region in existing_data.get("regions", {}) else "NEW",
            "clinics_in_clinics_data": len(new_clinics),
            "clinics_in_clinic_services.json": len(existing_clinics),
            "matching_clinics": len(new_clinics & existing_clinics),
            "clinics_only_in_clinics_data": sorted(list(new_clinics - existing_clinics)),
            "clinics_only_in_clinic_services.json": sorted(list(existing_clinics - new_clinics))
        }
        
        # Detailed clinic comparison
        if region not in comparison_report["clinic_comparison"]:
            comparison_report["clinic_comparison"][region] = {
                "matching": [],
                "only_in_clinics_data": [],
                "only_in_clinic_services": []
            }
        
        comparison_report["clinic_comparison"][region]["matching"] = sorted(list(new_clinics & existing_clinics))
        comparison_report["clinic_comparison"][region]["only_in_clinics_data"] = sorted(list(new_clinics - existing_clinics))
        comparison_report["clinic_comparison"][region]["only_in_clinic_services"] = sorted(list(existing_clinics - new_clinics))
    
    # Generate summary statistics
    all_new_clinics = set()
    all_existing_clinics = set()
    
    for region in new_structure["regions"]:
        all_new_clinics.update(new_structure["regions"][region]["clinics"].keys())
    
    for region in existing_data.get("regions", {}):
        all_existing_clinics.update(existing_data["regions"][region].get("clinics", {}).keys())
    
    comparison_report["summary"] = {
        "total_clinics_in_clinics_data": len(all_new_clinics),
        "total_clinics_in_clinic_services.json": len(all_existing_clinics),
        "total_matching_clinics": len(all_new_clinics & all_existing_clinics),
        "total_new_clinics": len(all_new_clinics - all_existing_clinics),
        "total_only_in_services": len(all_existing_clinics - all_new_clinics),
        "regions_in_clinics_data": len(clinics_data),
        "regions_in_clinic_services.json": len(existing_data.get("regions", {}))
    }
    
    # Save clinic_service_2.json
    with open('data/clinic_service_2.json', 'w', encoding='utf-8') as f:
        json.dump(new_structure, f, indent=2)
    
    print("✓ Generated: data/clinic_service_2.json")
    print(f"  Total clinics: {new_structure['scrape_metadata']['total_clinics']}")
    
    # Save comparison report
    with open('data/clinic_comparison_report.json', 'w', encoding='utf-8') as f:
        json.dump(comparison_report, f, indent=2)
    
    print("✓ Generated: data/clinic_comparison_report.json")
    
    # Print summary
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"Total clinics in clinics_data: {comparison_report['summary']['total_clinics_in_clinics_data']}")
    print(f"Total clinics in clinic_services.json: {comparison_report['summary']['total_clinics_in_clinic_services.json']}")
    print(f"Matching clinics: {comparison_report['summary']['total_matching_clinics']}")
    print(f"Only in clinics_data: {comparison_report['summary']['total_new_clinics']}")
    print(f"Only in clinic_services.json: {comparison_report['summary']['total_only_in_services']}")
    print(f"\nRegions in clinics_data: {comparison_report['summary']['regions_in_clinics_data']}")
    print(f"Regions in clinic_services.json: {comparison_report['summary']['regions_in_clinic_services.json']}")
    
    print("\n" + "="*80)
    print("DETAILED REGION COMPARISON")
    print("="*80)
    for region, comp in comparison_report["region_comparison"].items():
        print(f"\n{region}:")
        print(f"  Status: {comp['status']}")
        print(f"  Clinics in clinics_data: {comp['clinics_in_clinics_data']}")
        print(f"  Clinics in clinic_services.json: {comp['clinics_in_clinic_services.json']}")
        print(f"  Matching: {comp['matching_clinics']}")
        
        if comp['clinics_only_in_clinics_data']:
            print(f"  Only in clinics_data ({len(comp['clinics_only_in_clinics_data'])}): {', '.join(comp['clinics_only_in_clinics_data'][:3])}")
            if len(comp['clinics_only_in_clinics_data']) > 3:
                print(f"    ... and {len(comp['clinics_only_in_clinics_data']) - 3} more")
        
        if comp.get('clinics_only_in_clinic_services.json', []):
            print(f"  Only in clinic_services.json ({len(comp['clinics_only_in_clinic_services.json'])}): {', '.join(comp['clinics_only_in_clinic_services.json'][:3])}")
            if len(comp['clinics_only_in_clinic_services.json']) > 3:
                print(f"    ... and {len(comp['clinics_only_in_clinic_services.json']) - 3} more")
    
    return new_structure, comparison_report


if __name__ == "__main__":
    generate_clinic_service_2()
