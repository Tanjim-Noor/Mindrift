#!/usr/bin/env python
"""Verify specific words have correct plural forms after fix."""

import json

with open('swedish_word_inflections_v4.2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check specific words from QA
test_words = ['arbetskraft', 'manikyr', 'allergi', 'anarki', 'aptit', 'akrobatik', 
              'filosofi', 'teknologi', 'pedikyr', 'kärnkraft', 'vindkraft']

print("Verification of QA-flagged words:\n")
for w in test_words:
    for entry in data:
        if entry['ord'] == w:
            subst = entry.get('substantiv', {})
            print(f'{w}:')
            print(f'  singular: {subst.get("singular")}')
            print(f'  plural: {subst.get("plural")}')
            print(f'  bestämd_singular: {subst.get("bestämd_singular")}')
            print(f'  bestämd_plural: {subst.get("bestämd_plural")}')
            print()
            break
    else:
        print(f'{w}: NOT FOUND\n')
