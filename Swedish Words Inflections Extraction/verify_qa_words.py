"""Verify QA-flagged words have correct plurals"""
import json

d = json.load(open('swedish_word_inflections_v4.2_cleaned.json', encoding='utf-8'))

# QA flagged words that SHOULD have plurals
should_have = ['arbetskraft', 'manikyr', 'allergi', 'anarki', 'kärnkraft', 'vindkraft']

# Words that should NOT have plurals
should_not_have = ['matematik', 'fysik', 'svenska', 'engelska', 'fotboll', 'tennis', 'bensin']

print("QA Verification of Plurals in v4.2_cleaned")
print("=" * 60)
print()
print("SHOULD HAVE PLURALS (QA-verified countable nouns):")
print("-" * 40)
for w in should_have:
    entries = [e for e in d if e['ord'] == w]
    if entries:
        e = entries[0]
        sub = e.get('substantiv')
        if sub:
            pl = sub.get('plural')
            bpl = sub.get('bestämd_plural')
            status = "✓" if pl else "✗ MISSING"
            print(f"{status} {w}: {pl} / {bpl}")
        else:
            print(f"✗ {w}: no substantiv data")
    else:
        print(f"✗ {w}: NOT FOUND")

print()
print("SHOULD NOT HAVE PLURALS (languages, academic fields, mass nouns, sports):")
print("-" * 40)
for w in should_not_have:
    entries = [e for e in d if e['ord'] == w]
    if entries:
        e = entries[0]
        sub = e.get('substantiv')
        if sub:
            pl = sub.get('plural')
            bpl = sub.get('bestämd_plural')
            status = "✓" if pl is None else "✗ HAS PLURAL"
            print(f"{status} {w}: {pl}")
        else:
            print(f"✓ {w}: no substantiv data")
    else:
        print(f"  {w}: NOT FOUND")
