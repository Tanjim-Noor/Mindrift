import json

# Load the clinic_service_2.json file
with open(r'd:\Work\Mindrift\task2_new\data\clinic_service_2.json', 'r') as f:
    data = json.load(f)

# Missing clinics to add
missing_to_add = {
    'Brisbane': [
        {
            'clinic_name': 'Brookside (Mitchelton)',
            'clinic_url': 'https://web.archive.org/web/20250618202752/https://www.myfootdr.com.au/our-clinics/mitchelton-podiatry-centre/'
        }
    ],
    'Gold Coast': [
        {
            'clinic_name': 'Allsports Podiatry Parkwood',
            'clinic_url': 'https://web.archive.org/web/20250829222349/https://www.myfootdr.com.au/our-clinics/allsports-podiatry-parkwood/'
        },
        {
            'clinic_name': 'Varsity Lakes',
            'clinic_url': 'https://web.archive.org/web/20250829222349/https://www.myfootdr.com.au/our-clinics/robina-podiatry-centre/'
        }
    ],
    'South Australia': [
        {
            'clinic_name': 'Hove',
            'clinic_url': 'https://web.archive.org/web/20250707233302/https://www.myfootdr.com.au/our-clinics/hove-podiatry-centre/'
        },
        {
            'clinic_name': 'My FootDr Woodville',
            'clinic_url': 'https://web.archive.org/web/20250707233302/https://www.myfootdr.com.au/our-clinics/bim-podiatry-woodville/'
        },
        {
            'clinic_name': 'Semaphore',
            'clinic_url': 'https://web.archive.org/web/20250707233302/https://www.myfootdr.com.au/our-clinics/semaphore-podiatry-clinic/'
        },
        {
            'clinic_name': 'Stirling',
            'clinic_url': 'https://web.archive.org/web/20250707233302/https://www.myfootdr.com.au/our-clinics/stirling-podiatry-centre/'
        },
        {
            'clinic_name': 'Unley',
            'clinic_url': 'https://web.archive.org/web/20250707233302/https://www.myfootdr.com.au/our-clinics/unley-podiatry-centre/'
        }
    ],
    'Tasmania': [
        {
            'clinic_name': 'Ispahan',
            'clinic_url': 'https://web.archive.org/web/20250516141742/https://www.myfootdr.com.au/our-clinics/south-hobart-ispahan-podiatry-centre/'
        }
    ]
}

# Add missing clinics to the data
for region_name, clinics in missing_to_add.items():
    if region_name not in data['regions']:
        print(f"Error: Region {region_name} not found!")
        continue
    
    for clinic in clinics:
        clinic_name = clinic['clinic_name']
        clinic_url = clinic['clinic_url']
        
        # Check if clinic already exists
        if clinic_name in data['regions'][region_name]['clinics']:
            print(f"Clinic {clinic_name} already exists in {region_name}")
            continue
        
        # Add the clinic with format: services=[], scraped=false
        data['regions'][region_name]['clinics'][clinic_name] = {
            'services': [],
            'scraped': False,
            'link': clinic_url
        }
        print(f"Added {clinic_name} to {region_name}")

# Save the updated data back to the file
with open(r'd:\Work\Mindrift\task2_new\data\clinic_service_2.json', 'w') as f:
    json.dump(data, f, indent=2)

print("\nSuccessfully updated clinic_service_2.json!")

# Verify the update
with open(r'd:\Work\Mindrift\task2_new\data\clinic_service_2.json', 'r') as f:
    updated_data = json.load(f)
    print("\nUpdated clinic counts per region:")
    for region in sorted(updated_data['regions'].keys()):
        count = len(updated_data['regions'][region]['clinics'])
        print(f"  {region}: {count} clinics")
