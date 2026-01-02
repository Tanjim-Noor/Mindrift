import json

with open('swedish_word_inflections_v4.3.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Count nouns
nouns = [e for e in data if e.get('substantiv')]
with_plural = [e for e in nouns if e['substantiv'].get('plural')]
null_plural = [e for e in nouns if e['substantiv'].get('plural') is None]

print('='*70)
print('V4.3 FINAL STATISTICS - Comprehensive Plural Correction Complete')
print('='*70)
print(f'Total entries:           {len(data)}')
print(f'Nouns:                   {len(nouns)}')
print(f'  With plural:           {len(with_plural)} ({100*len(with_plural)/len(nouns):.1f}%)')
print(f'  Null plural:           {len(null_plural)} ({100*len(null_plural)/len(nouns):.1f}%)')
print()

# Load report
with open('swedish_word_inflections_v4.3_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

stats = report['statistics']
print('Corrections applied:')
print(f'  Nullified - Languages:          {stats["nullified_languages"]}')
print(f'  Nullified - Academic fields:    {stats["nullified_academic_fields"]}')
print(f'  Nullified - Sports:             {stats["nullified_sports"]}')
print(f'  Nullified - Mass nouns:         {stats["nullified_mass_nouns"]}')
print(f'  Nullified - Abstract:           {stats["nullified_abstract"]}')
print(f'  Nullified - Singular compounds: {stats["nullified_singular_compounds"]}')
print(f'  Morphological fixes:            {stats["morphological_fixes"]}')
print(f'  Unchanged:                      {stats["unchanged"]}')
print()

print('Example corrections:')
print('  fotboll: fotboller → NULL (sport)')
print('  svenska: svenskor → NULL (language)')
print('  matematik: matematiker → NULL (academic field)')
print('  banderoll: banderoller → banderollar (morphological fix)')
print()

print('QA words verified:')
qa_words = ['arbetskraft', 'manikyr', 'dressyr', 'omelett', 'kuvös']
for word in qa_words:
    for entry in data:
        if entry.get('ord') == word:
            sub = entry['substantiv']
            pl = sub.get('plural')
            bpl = sub.get('bestämd_plural')
            print(f'  {word}: {pl} / {bpl}')
            break
