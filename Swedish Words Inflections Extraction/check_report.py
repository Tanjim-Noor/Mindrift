import json

with open('step3_frequency_enhanced_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

print('Frequency Analysis Report:')
print('=' * 60)
print('Statistics:')
for k, v in report['statistics'].items():
    print(f'  {k}: {v}')

print(f'\nTotal decisions made: {report["total_decisions"]}')

print('\nSample decisions (first 30):')
for d in report['decisions'][:30]:
    print(f"  {d['word']:15} => {d['reason']}")
