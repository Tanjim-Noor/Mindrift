import json

with open('swedish_word_inflections_v4.1.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check specific test cases
test_words = ['abbe', 'a-social', 'tabbe', 'grabbe', 'vinge', 'armé', 'café', 'kedja', 'kan', 'adjö', 'glad']
print('V4 Output Verification:')
print('=' * 60)
for word in test_words:
    for entry in data:
        if entry['ord'].lower() == word.lower():
            print(f'\n{word}:')
            if entry.get('substantiv'):
                s = entry['substantiv']
                print(f"  substantiv: sg={s.get('singular')} / def_sg={s.get('bestämd_singular')} / pl={s.get('plural')} / def_pl={s.get('bestämd_plural')}")
            if entry.get('verb'):
                v = entry['verb']
                print(f"  verb: inf={v.get('infinitiv')} / pres={v.get('presens')}")
            if entry.get('adjektiv'):
                a = entry['adjektiv']
                print(f"  adjektiv: pos={a.get('positiv')} / komp={a.get('komparativ')} / sup={a.get('superlativ')}")
            if entry.get('övrigt'):
                print(f"  övrigt: {entry['övrigt']}")
            break
    else:
        print(f'\n{word}: NOT FOUND')

# Count entries with safety trigger condition
print('\n' + '=' * 60)
print('Checking for any remaining identical sg/def_sg:')
issues = []
for entry in data:
    if entry.get('substantiv'):
        s = entry['substantiv']
        sg = s.get('singular')
        def_sg = s.get('bestämd_singular')
        if sg and def_sg and sg == def_sg:
            issues.append((entry['ord'], sg, def_sg))

print(f'Found {len(issues)} entries with sg == def_sg')
if issues:
    print('Examples:')
    for word, sg, def_sg in issues[:10]:
        print(f'  {word}: {sg} == {def_sg}')
