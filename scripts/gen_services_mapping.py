import json
from pathlib import Path

json_path = Path(r'd:/Work/Mindrift/task2_new/data/clinic_service_2.json')
with json_path.open('r', encoding='utf-8') as f:
    data = json.load(f)

mapping = {}
for region, region_info in data['regions'].items():
    clinics = region_info.get('clinics', {})
    for name, cinfo in clinics.items():
        services = cinfo.get('services', [])
        scraped = cinfo.get('scraped', False)
        # Only include clinics with scraped=True and non-empty services list that isn't placeholder
        if not scraped:
            continue
        if not services:
            continue
        if len(services) == 1 and services[0].lower().startswith('n/a'):
            continue
        if len(services) == 1 and services[0].lower() == 'none':
            continue
        val = ', '.join(services)
        mapping[name] = val

# Build python dict string
lines = []
lines.append('SCRAPED_CLINIC_SERVICES = {')
for k in sorted(mapping.keys()):
    # Escape backslashes and quote characters in keys/values
    key = k.replace('\\', '\\\\').replace('"', '\\"')
    val = mapping[k].replace('\\', '\\\\').replace('"', '\\"')
    lines.append(f'    "{key}": "{val}",')
lines.append('}')

out = '\n'.join(lines)
print(out)

# Also write to a temp file for verification
out_path = Path('d:/Work/Mindrift/scripts/scraped_services_mapping_snippet.txt')
out_path.write_text(out, encoding='utf-8')
print('\nWrote snippet to', out_path)
