import json

with open('swedish_word_inflections_v4.2.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

qa_not_found = ['bajonett', 'silhuett', 'konfekt', 'etikett', 'kadett', 'kassett', 'balalaika', 'mamelucker']
print('Searching for missing QA words...')
for word in qa_not_found:
    found = False
    for entry in data:
        if entry.get('ord', '').lower() == word.lower():
            print(f'{word}: FOUND as {entry["ord"]}')
            found = True
            break
    if not found:
        print(f'{word}: NOT IN DATA')

print()
# Check v4.1 too
with open('swedish_word_inflections_v4.1.json', 'r', encoding='utf-8') as f:
    v41 = json.load(f)

print('Checking v4.1...')
for word in qa_not_found[:3]:
    found = False
    for entry in v41:
        if entry.get('ord', '').lower() == word.lower():
            print(f'{word}: FOUND in v4.1')
            found = True
            break
    if not found:
        print(f'{word}: NOT IN v4.1 either')

# Search Lexikon
print()
print('Checking Lexikon.json...')
with open('Lexikon.json', 'r', encoding='utf-8') as f:
    lexikon = json.load(f)

for word in qa_not_found:
    if word in lexikon:
        print(f'{word}: IN LEXIKON')
    else:
        print(f'{word}: NOT IN LEXIKON')
