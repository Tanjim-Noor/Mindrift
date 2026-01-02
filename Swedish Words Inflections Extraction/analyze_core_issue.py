"""
Analyze the core issue: which words have null plurals and why?
"""
import json

# Load step1 data
step1 = json.load(open('step1_word_entries.json', encoding='utf-8'))

# Load v4.1
v41 = json.load(open('swedish_word_inflections_v4.1.json', encoding='utf-8'))
null_plural_words = set(e['ord'] for e in v41 if e.get('substantiv') and e['substantiv'].get('plural') is None)

print(f"Null plural words: {len(null_plural_words)}")

# Find arbetskraft in step1
for e in step1:
    if e.get('word') == 'arbetskraft':
        print("\narbetskraft entry:")
        print(json.dumps(e, indent=2, ensure_ascii=False))
        break

# Check structure of step1
print("\n\nStep1 entry keys:", step1[0].keys())
