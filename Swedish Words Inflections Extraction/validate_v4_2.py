"""Final validation for v4.2"""
import json

print("=" * 70)
print("SWEDISH WORD INFLECTIONS v4.2 - FINAL VALIDATION")
print("=" * 70)

# Load data
data = json.load(open('swedish_word_inflections_v4.2.json', encoding='utf-8'))
print(f"\nTotal entries: {len(data)}")

# Count by type
nouns = sum(1 for e in data if e.get('substantiv'))
verbs = sum(1 for e in data if e.get('verb'))
adjs = sum(1 for e in data if e.get('adjektiv'))
other = sum(1 for e in data if e.get('övrigt'))

print(f"\nBy word class:")
print(f"  Substantiv (nouns):     {nouns}")
print(f"  Verb:                   {verbs}")
print(f"  Adjektiv:               {adjs}")
print(f"  Övrigt (other):         {other}")

# Check for null forms
null_plurals = 0
has_plurals = 0
for e in data:
    sub = e.get('substantiv')
    if sub:
        if sub.get('plural') is None:
            null_plurals += 1
        else:
            has_plurals += 1

print(f"\nNoun plural analysis:")
print(f"  Has plural forms:       {has_plurals}")
print(f"  Null plurals:           {null_plurals}")

# Verify QA words
print("\n" + "-" * 70)
print("QA-FLAGGED WORDS VERIFICATION:")
print("-" * 70)
qa_words = {
    'arbetskraft': ('arbetskrafter', 'arbetskrafterna'),
    'manikyr': ('manikyrer', 'manikyrerna'),
    'allergi': ('allergier', 'allergierna'),
    'kärnkraft': ('kärnkrafter', 'kärnkrafterna'),
    'vindkraft': ('vindkrafter', 'vindkrafterna'),
}

all_pass = True
for word, expected in qa_words.items():
    entry = next((e for e in data if e['ord'] == word), None)
    if entry and entry.get('substantiv'):
        sub = entry['substantiv']
        pl = sub.get('plural')
        bpl = sub.get('bestämd_plural')
        if pl == expected[0] and bpl == expected[1]:
            print(f"  ✓ {word}: {pl} / {bpl}")
        else:
            print(f"  ✗ {word}: expected {expected}, got {pl}/{bpl}")
            all_pass = False
    else:
        print(f"  ✗ {word}: NOT FOUND")
        all_pass = False

# Verify non-countable words
print("\n" + "-" * 70)
print("NON-COUNTABLE WORDS VERIFICATION (should have null plurals):")
print("-" * 70)
non_countable = ['svenska', 'engelska', 'matematik', 'fysik', 'fotboll', 
                 'tennis', 'bensin', 'biologi', 'psykologi', 'bowling']

for word in non_countable:
    entry = next((e for e in data if e['ord'] == word), None)
    if entry and entry.get('substantiv'):
        sub = entry['substantiv']
        pl = sub.get('plural')
        if pl is None:
            print(f"  ✓ {word}: null (correct)")
        else:
            print(f"  ✗ {word}: has plural '{pl}' (should be null)")
            all_pass = False

print("\n" + "=" * 70)
if all_pass:
    print("✓ ALL VALIDATIONS PASSED")
else:
    print("✗ SOME VALIDATIONS FAILED")
print("=" * 70)
