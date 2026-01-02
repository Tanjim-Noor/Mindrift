#!/usr/bin/env python
"""Analyze nouns with singularia tantum (nn_0) paradigms in SALDO."""

import json

# Load classified entries
with open('archive/v3/step2_classified_entries_v3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find words with nn_0 paradigms (singularia tantum)
nn_0_words = []
paradigm_counts = {}
for entry in data:
    paradigm = entry.get('primary_paradigm', '')
    if paradigm and paradigm.startswith('nn_0'):
        nn_0_words.append({'ord': entry['ord'], 'paradigm': paradigm})
        if paradigm not in paradigm_counts:
            paradigm_counts[paradigm] = 0
        paradigm_counts[paradigm] += 1

print(f'Total nn_0* paradigm words: {len(nn_0_words)}')
print(f'\nParadigm breakdown:')
for p, count in sorted(paradigm_counts.items(), key=lambda x: -x[1]):
    print(f'  {p}: {count}')
print(f'\nSample words:')
for w in nn_0_words[:30]:
    print(f'  {w["ord"]}: {w["paradigm"]}')

# Now check what's in the current output
print('\n\n=== Checking current output ===')
with open('swedish_word_inflections_v4.1.json', 'r', encoding='utf-8') as f:
    output = json.load(f)

# Find all nouns with null plural
null_plural_nouns = []
for entry in output:
    subst = entry.get('substantiv')
    if subst and subst.get('singular') and not subst.get('plural'):
        null_plural_nouns.append(entry['ord'])

print(f'Nouns with null plural in output: {len(null_plural_nouns)}')
print(f'\nSample of null plural nouns:')
for w in null_plural_nouns[:20]:
    print(f'  {w}')

# Cross-reference: how many of the null plural nouns have nn_0 paradigms?
nn_0_ords = set(w['ord'] for w in nn_0_words)
null_plural_from_nn_0 = [w for w in null_plural_nouns if w in nn_0_ords]
print(f'\nNull plural nouns that have nn_0 paradigms: {len(null_plural_from_nn_0)}')
print(f'Null plural nouns WITHOUT nn_0 paradigms: {len(null_plural_nouns) - len(null_plural_from_nn_0)}')
