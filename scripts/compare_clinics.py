import json, importlib.util, os, sys

# Load clinic_service_2.json
with open(r'd:/Work/Mindrift/task2_new/data/clinic_service_2.json','r',encoding='utf-8') as f:
    j = json.load(f)

# Load csv_maker.py as module
spec = importlib.util.spec_from_file_location('csv_maker', r'd:/Work/Mindrift/task2_v3/csv_maker.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Get names from json
json_clinics = {}
for region, region_data in j['regions'].items():
    names = list(region_data.get('clinics',{}).keys())
    json_clinics[region] = set(names)

# Get names from csv_maker clinics_data
csv_clinics = {}
for region, clinics in mod.clinics_data.items():
    csv_clinics[region] = set([cl['name'] for cl in clinics])

# Compute differences
all_regions = set(json_clinics.keys()) | set(csv_clinics.keys())
added = {}
removed = {}
for region in sorted(all_regions):
    jset = json_clinics.get(region, set())
    cset = csv_clinics.get(region, set())
    added[region] = sorted(list(jset - cset))
    removed[region] = sorted(list(cset - jset))

print('ADDED CLINICS (in json but missing from csv_maker.py):')
for r, names in added.items():
    if names:
        print('\nRegion:', r)
        for n in names:
            print('  -', n)

print('\nREMOVED CLINICS (in csv_maker.py but not in json):')
for r, names in removed.items():
    if names:
        print('\nRegion:', r)
        for n in names:
            print('  -', n)

# Output a combined summary file to inspect programmatically
summary = {'added':added, 'removed':removed}
with open(r'd:/Work/Mindrift/diff_summary.json','w',encoding='utf-8') as f:
    json.dump(summary,f,indent=2)

print('\nDiff summary written to d:/Work/Mindrift/diff_summary.json')
