"""
Analyze null plural issue in V4.1 output
"""
import json
from collections import Counter

# Load current output
with open('swedish_word_inflections_v4.1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count nouns with various null patterns
has_subst = [e for e in data if e.get('substantiv')]
null_plural = [e for e in has_subst if e['substantiv'].get('plural') is None]
null_def_plural = [e for e in has_subst if e['substantiv'].get('bestämd_plural') is None]
null_both = [e for e in has_subst if e['substantiv'].get('plural') is None and e['substantiv'].get('bestämd_plural') is None]

print(f'Total nouns: {len(has_subst)}')
print(f'Nouns with null plural: {len(null_plural)}')
print(f'Nouns with null bestämd_plural: {len(null_def_plural)}')
print(f'Nouns with BOTH null: {len(null_both)}')
print()

print('Sample of nouns with null plural (first 30):')
for e in null_plural[:30]:
    s = e['substantiv']
    print(f"  {e['ord']}: sg={s.get('singular')}, def_sg={s.get('bestämd_singular')}")

# Save list for further analysis
with open('_null_plural_nouns.json', 'w', encoding='utf-8') as f:
    json.dump([e['ord'] for e in null_plural], f, ensure_ascii=False, indent=2)
print(f"\nSaved list to _null_plural_nouns.json")
