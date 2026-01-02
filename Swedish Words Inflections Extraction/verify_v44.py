import json

with open('swedish_word_inflections_v4.4.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count nouns
nouns = [e for e in data if e.get('substantiv')]
with_plural = [e for e in nouns if e['substantiv'].get('plural')]
null_plural = [e for e in nouns if e['substantiv'].get('plural') is None]

print('='*70)
print('V4.4 FINAL STATISTICS - Conservative Correction Complete')
print('='*70)
print(f'Total entries:           {len(data)}')
print(f'Nouns:                   {len(nouns)}')
print(f'  With plural:           {len(with_plural)} ({100*len(with_plural)/len(nouns):.1f}%)')
print(f'  Null plural:           {len(null_plural)} ({100*len(null_plural)/len(nouns):.1f}%)')
print()

# Load report
with open('swedish_word_inflections_v4.4_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

stats = report['statistics']
print('Corrections applied:')
print(f'  Nullified - Languages:          {stats["nullified_languages"]}')
print(f'  Nullified - Academic fields:    {stats["nullified_academic_fields"]}')
print(f'  Nullified - Sports:             {stats["nullified_sports"]}')
print(f'  Nullified - Mass nouns:         {stats["nullified_mass_nouns"]}')
print(f'  Nullified - Specific:           {stats["nullified_specific_uncountables"]}')
print(f'  Morphological fixes:            {stats["morphological_fixes"]}')
print(f'  Unchanged (kept valid plurals): {stats["unchanged"]}')
print()

print('User-reported issues FIXED:')
qa_words = [
    ('likhet', 'likheter', 'likheterna'),
    ('dimma', 'dimmor', 'dimmorna'),
    ('möjlighet', 'möjligheter', 'möjligheterna')
]

for word, expected_pl, expected_def in qa_words:
    for entry in data:
        if entry.get('ord') == word:
            sub = entry['substantiv']
            pl = sub.get('plural')
            bpl = sub.get('bestämd_plural')
            status = '✅' if pl == expected_pl and bpl == expected_def else '❌'
            print(f'  {status} {word}: {pl} / {bpl}')
            break

print()
print('Incorrectly generated plurals REMOVED:')
removed = [
    ('fotboll', 'sport'),
    ('svenska', 'language'),
    ('matematik', 'academic field')
]
for word, category in removed:
    for entry in data:
        if entry.get('ord') == word:
            sub = entry['substantiv']
            pl = sub.get('plural')
            status = '✅' if pl is None else '❌'
            print(f'  {status} {word}: {pl} (was incorrectly generated, {category})')
            break
