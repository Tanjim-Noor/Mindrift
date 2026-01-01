"""
Compare old and new classifications to identify changed paradigms.
"""

import json

# Load old and new classifications
old = {e['ord']: e for e in json.load(open('archive/v1/step2_classified_entries.json', encoding='utf-8'))}
new = {e['ord']: e for e in json.load(open('step2_classified_entries.json', encoding='utf-8'))}

# Find words where paradigm changed
changed = []
for word, new_entry in new.items():
    old_entry = old.get(word)
    if old_entry and old_entry.get('paradigm') != new_entry.get('paradigm'):
        if new_entry.get('paradigm'):  # Only if new paradigm exists
            changed.append({
                'ord': word,
                'old_paradigm': old_entry.get('paradigm'),
                'new_paradigm': new_entry.get('paradigm'),
                'old_class': old_entry.get('word_class'),
                'new_class': new_entry.get('word_class')
            })

print(f'Words with changed paradigms: {len(changed)}')
print(f'Examples:')
for item in changed[:15]:
    print(f"  {item['ord']}: {item['old_class']} ({item['old_paradigm']}) -> {item['new_class']} ({item['new_paradigm']})")

# Save for API calls
with open('changed_paradigms.json', 'w', encoding='utf-8') as f:
    json.dump(changed, f, ensure_ascii=False, indent=2)
print(f'\nSaved {len(changed)} entries to changed_paradigms.json')
