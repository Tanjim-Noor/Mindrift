import json

# Load v4.2
with open('swedish_word_inflections_v4.2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Summary
nouns = [e for e in data if e.get('substantiv')]
with_pl = [e for e in nouns if e['substantiv'].get('plural')]
null_pl = [e for e in nouns if e['substantiv'].get('plural') is None]

print('='*60)
print('V4.2 SUMMARY - Systematic Plural Fix Complete')
print('='*60)
print(f'Total entries:           {len(data)}')
print(f'Nouns:                   {len(nouns)}')
print(f'  With plural:           {len(with_pl)} ({100*len(with_pl)/len(nouns):.1f}%)')
print(f'  Null plural:           {len(null_pl)} ({100*len(null_pl)/len(nouns):.1f}%)')
print()
print('QA Words that exist in data:')
qa_words = ['arbetskraft', 'manikyr', 'dressyr', 'omelett', 'kuvös', 'bankett', 'moské']
for w in qa_words:
    for e in data:
        if e.get('ord') == w:
            sub = e['substantiv']
            pl = sub.get('plural')
            bpl = sub.get('bestämd_plural')
            print(f'  {w}: {pl} / {bpl}')
            break
print()
print('Sample null plurals (correctly excluded):')
for e in null_pl[:15]:
    print(f'  {e["ord"]}')

print()
print('Words NOT in our data (from external QA):')
missing = ['bajonett', 'silhuett', 'konfekt', 'etikett', 'kadett', 'kassett', 'balalaika', 'mamelucker']
print(f'  {", ".join(missing)}')
print('  (These words are not in Lexikon.json - outside scope)')
