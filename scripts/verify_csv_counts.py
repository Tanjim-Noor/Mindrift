import importlib.util
import csv
import sys
from collections import defaultdict

# Load clinics_data from csv_maker
spec = importlib.util.spec_from_file_location("csv_maker", "d:/Work/Mindrift/task2_v3/csv_maker.py")
csv_maker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csv_maker)

# Build mapping clinic_name -> region
name_to_region = {}
for region, clinics in csv_maker.clinics_data.items():
    for clinic in clinics:
        name_to_region[clinic['name']] = region

# Count clinics by region from clinics_data
expected_counts = {region: len(clinics) for region, clinics in csv_maker.clinics_data.items()}
expected_total = sum(expected_counts.values())

# Read CSV and compute counts
csv_file = 'd:/Work/Mindrift/myfootdr_clinics.csv'
csv_counts = defaultdict(int)
unknown_names = []
rows_total = 0

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows_total += 1
        name = row['Name of Clinic'].strip()
        region = name_to_region.get(name)
        if region:
            csv_counts[region] += 1
        else:
            unknown_names.append(name)

# Prepare output
print('Expected clinic counts by region (from clinics_data):')
for region in sorted(expected_counts.keys()):
    print(f'  {region}: {expected_counts[region]}')

print('\nCounts in CSV grouped by region (using clinics_data to map names):')
for region in sorted(expected_counts.keys()):
    print(f'  {region}: {csv_counts.get(region, 0)}')

print(f'\nTotal rows in CSV: {rows_total}')
print(f'Expected total clinics (from clinics_data): {expected_total}')
print(f'Number of clinics found in CSV that could not be mapped to regions: {len(unknown_names)}')
if unknown_names:
    print('\nSample unmatched clinic names (first 10):')
    for name in unknown_names[:10]:
        print('  ' + name)

# Quick checks
if rows_total != expected_total:
    print('\n⚠️ Row count mismatch: CSV rows do not match clinics_data total.\n')
else:
    print('\n✅ Row count matches clinics_data total.\n')

# Also check if every expected clinic is present in CSV
missing_in_csv = [n for n in name_to_region.keys() if n not in unknown_names and n not in [r['Name of Clinic'] for r in []]]
# The above line is a placeholder; we check presence differently

# Build a set of names from CSV
csv_names = set()
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_names.add(row['Name of Clinic'].strip())

missing_names = [n for n in name_to_region.keys() if n not in csv_names]
if missing_names:
    print(f'\nClinics present in clinics_data but missing from CSV: {len(missing_names)}')
    for n in missing_names[:10]:
        print('  ' + n)
else:
    print('\nAll clinics from clinics_data appear in the CSV.\n')
