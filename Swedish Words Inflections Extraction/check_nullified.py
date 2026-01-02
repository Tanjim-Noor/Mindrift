import json

with open('swedish_word_inflections_v4.3_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

# Check what was nullified
nullified_abstract = report['corrections']['nullified_abstract']
print(f'Total abstract words wrongly nullified: {len(nullified_abstract)}')
print()
print('Sample (first 30):')
for item in nullified_abstract[:30]:
    word = item['word']
    removed = item['removed_plural']
    print(f'  {word}: {removed} -> NULL')
