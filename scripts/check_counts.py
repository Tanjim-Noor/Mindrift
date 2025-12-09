import importlib.util
import sys

spec = importlib.util.spec_from_file_location("csv_maker", "d:/Work/Mindrift/task2_v3/csv_maker.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

clinics_count = sum(len(v) for v in mod.clinics_data.values())
print(f"clinics_data total: {clinics_count}")
print(f"SCRAPED_CLINIC_SERVICES total: {len(mod.SCRAPED_CLINIC_SERVICES)}")

# print clinics not in services mapping
clinics = [c['name'] for region in mod.clinics_data.values() for c in region]
missing_services = [c for c in clinics if c not in mod.SCRAPED_CLINIC_SERVICES]
print(f"clinics without a scraped services entry: {len(missing_services)}")
if missing_services:
    print('\n'.join(missing_services))
