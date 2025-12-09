import json
import re

# Load both files
with open(r'd:\Work\Mindrift\task2_v3\data\clinics_by_region.json', 'r') as f:
    clinics_by_region = json.load(f)

with open(r'd:\Work\Mindrift\task2_new\data\clinic_service_2.json', 'r') as f:
    clinic_service_2 = json.load(f)

# Mapping of region keys between the two files
region_mapping = {
    'brisbane': 'Brisbane',
    'central-queensland': 'Central Queensland',
    'gold-coast': 'Gold Coast',
    'new-south-wales': 'New South Wales',
    'north-queensland': 'North Queensland',
    'northern-territory': 'Northern Territory',
    'south-australia': 'South Australia',
    'sunshine-coast': 'Sunshine Coast',
    'tasmania': 'Tasmania',
    'victoria': 'Victoria',
    'western-australia': 'Western Australia'
}

def normalize_clinic_name(name):
    """Normalize clinic name for matching"""
    # Remove 'My FootDr' prefix if present
    name = re.sub(r'^My FootDr\s+', '', name)
    # Convert to lowercase
    name = name.lower().strip()
    return name

print("\n" + "="*80)
print("CHECKING FOR MISSING CLINICS")
print("="*80 + "\n")

missing_clinics = {}
found_clinics = {}

for region_key, region_name in region_mapping.items():
    clinics_from_region = clinics_by_region['regions'][region_key]['clinics']
    clinics_in_service = clinic_service_2['regions'].get(region_name, {}).get('clinics', {})
    
    missing_clinics[region_name] = []
    found_clinics[region_name] = []
    
    print(f"\n{region_name}:")
    print(f"  Expected from region page: {len(clinics_from_region)}")
    print(f"  Currently in service file: {len(clinics_in_service)}")
    
    # Check each clinic from the region page
    for clinic in clinics_from_region:
        clinic_name = clinic['clinic_name']
        normalized_name = normalize_clinic_name(clinic_name)
        
        # Try to find matching clinic in service file
        found = False
        for service_name in clinics_in_service.keys():
            normalized_service_name = normalize_clinic_name(service_name)
            if normalized_service_name == normalized_name:
                found = True
                found_clinics[region_name].append(clinic_name)
                break
        
        if not found:
            missing_clinics[region_name].append({
                'clinic_name': clinic_name,
                'clinic_url': clinic['clinic_url']
            })

# Print summary
print("\n" + "="*80)
print("SUMMARY OF MISSING CLINICS")
print("="*80 + "\n")

total_missing = 0
for region_name, missing in missing_clinics.items():
    if missing:
        total_missing += len(missing)
        print(f"\n{region_name}: {len(missing)} missing clinic(s)")
        for clinic in missing:
            print(f"  - {clinic['clinic_name']}")
            print(f"    URL: {clinic['clinic_url']}")

if total_missing == 0:
    print("\nAll clinics from region pages are listed in clinic_service_2.json!")
else:
    print(f"\n\nTotal missing clinics: {total_missing}")

# Save missing clinics to a file for reference
with open(r'd:\Work\Mindrift\missing_clinics.json', 'w') as f:
    json.dump(missing_clinics, f, indent=2)

print("\nMissing clinics saved to: missing_clinics.json")
