"""
Step 4: Validate V4 Output
===========================
Validates the V4 output with specific checks for:
1. No nouns ending in 'e' with identical definite/indefinite singular
2. No hyphenated adjectives with synthetic comparison forms
3. General schema validation
"""

import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple

INPUT_FILE = Path("swedish_word_inflections_v4.1.json")
REPORT_FILE = Path("step4_validation_report_v4.json")


def validate_noun_e_endings(entries: List[Dict]) -> List[Dict]:
    """Check for nouns ending in 'e' with identical sg/def_sg."""
    issues = []
    for entry in entries:
        if not entry.get('substantiv'):
            continue
        
        s = entry['substantiv']
        sg = s.get('singular', '')
        def_sg = s.get('bestämd_singular', '')
        
        # Only check words ending in 'e'
        if sg and sg.endswith('e') and sg == def_sg:
            issues.append({
                'word': entry['ord'],
                'issue': 'identical_e_ending',
                'singular': sg,
                'bestämd_singular': def_sg
            })
    
    return issues


def validate_hyphenated_adjectives(entries: List[Dict]) -> List[Dict]:
    """Check for hyphenated adjectives with comparison forms."""
    issues = []
    for entry in entries:
        word = entry.get('ord', '')
        if '-' not in word:
            continue
        
        adj = entry.get('adjektiv')
        if not adj:
            continue
        
        komp = adj.get('komparativ')
        sup = adj.get('superlativ')
        
        if komp is not None or sup is not None:
            issues.append({
                'word': word,
                'issue': 'hyphenated_with_comparison',
                'komparativ': komp,
                'superlativ': sup
            })
    
    return issues


def validate_schema(entry: Dict) -> Tuple[bool, List[str]]:
    """Validate entry follows expected schema."""
    warnings = []
    
    # Required field
    if 'ord' not in entry:
        return False, ['Missing required field: ord']
    
    # Validate substantiv structure if present
    if entry.get('substantiv'):
        s = entry['substantiv']
        expected_keys = {'singular', 'plural', 'bestämd_singular', 'bestämd_plural'}
        if not isinstance(s, dict):
            return False, ['substantiv is not a dict']
        extra_keys = set(s.keys()) - expected_keys
        if extra_keys:
            warnings.append(f'Extra keys in substantiv: {extra_keys}')
    
    # Validate verb structure if present
    if entry.get('verb'):
        v = entry['verb']
        expected_keys = {'infinitiv', 'presens', 'preteritum', 'supinum', 'particip'}
        if not isinstance(v, dict):
            return False, ['verb is not a dict']
    
    # Validate adjektiv structure if present
    if entry.get('adjektiv'):
        a = entry['adjektiv']
        expected_keys = {'positiv', 'komparativ', 'superlativ'}
        if not isinstance(a, dict):
            return False, ['adjektiv is not a dict']
    
    return True, warnings


def main():
    print("=" * 60)
    print("Step 4: Validate V4 Output")
    print("=" * 60)
    
    # Load data
    print(f"\n📂 Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"   Loaded {len(entries):,} entries")
    
    # Validation
    print("\n🔍 Running validations...")
    
    # Check 1: Nouns ending in 'e' with identical forms
    e_ending_issues = validate_noun_e_endings(entries)
    print(f"\n   Nouns ending in 'e' with identical sg/def_sg: {len(e_ending_issues)}")
    if e_ending_issues:
        print("   ⚠️  Examples:")
        for issue in e_ending_issues[:5]:
            print(f"      {issue['word']}: {issue['singular']} == {issue['bestämd_singular']}")
    else:
        print("   ✅ All nouns ending in 'e' have correct definite forms")
    
    # Check 2: Hyphenated adjectives
    hyphen_issues = validate_hyphenated_adjectives(entries)
    print(f"\n   Hyphenated adjectives with comparison forms: {len(hyphen_issues)}")
    if hyphen_issues:
        print("   ⚠️  Examples:")
        for issue in hyphen_issues[:5]:
            print(f"      {issue['word']}: komp={issue['komparativ']}, sup={issue['superlativ']}")
    else:
        print("   ✅ All hyphenated adjectives have null comparison forms")
    
    # Check 3: Schema validation
    valid_count = 0
    invalid_count = 0
    warning_count = 0
    
    for entry in entries:
        is_valid, warnings = validate_schema(entry)
        if is_valid:
            valid_count += 1
            if warnings:
                warning_count += 1
        else:
            invalid_count += 1
    
    print(f"\n   Schema validation:")
    print(f"      Valid: {valid_count:,}")
    print(f"      Invalid: {invalid_count}")
    print(f"      With warnings: {warning_count}")
    
    # Class distribution
    print("\n📊 Class Distribution:")
    has_substantiv = sum(1 for e in entries if e.get('substantiv'))
    has_verb = sum(1 for e in entries if e.get('verb'))
    has_adjektiv = sum(1 for e in entries if e.get('adjektiv'))
    has_ovrigt = sum(1 for e in entries if e.get('övrigt'))
    has_any = sum(1 for e in entries if any(e.get(k) for k in ['substantiv','verb','adjektiv','övrigt']))
    
    print(f"   Substantiv: {has_substantiv:,} ({100*has_substantiv/len(entries):.1f}%)")
    print(f"   Verb: {has_verb:,} ({100*has_verb/len(entries):.1f}%)")
    print(f"   Adjektiv: {has_adjektiv:,} ({100*has_adjektiv/len(entries):.1f}%)")
    print(f"   Övrigt: {has_ovrigt:,} ({100*has_ovrigt/len(entries):.1f}%)")
    print(f"   With any data: {has_any:,} ({100*has_any/len(entries):.1f}%)")
    
    # Key test cases
    print("\n✅ Key Test Case Verification:")
    test_cases = [
        ('abbe', 'substantiv', 'bestämd_singular', 'abbén'),
        ('a-social', 'adjektiv', 'komparativ', None),
        ('kedja', 'substantiv', 'singular', 'kedja'),
        ('kedja', 'verb', 'infinitiv', 'kedja'),
        ('kan', 'verb', 'presens', 'kan'),
        ('adjö', 'övrigt', None, 'interjektion (oböjligt)'),
        ('glad', 'adjektiv', 'positiv', 'glad'),
    ]
    
    for word, category, field, expected in test_cases:
        for entry in entries:
            if entry['ord'].lower() == word.lower():
                if field:
                    actual = entry.get(category, {}).get(field) if entry.get(category) else None
                else:
                    actual = entry.get(category)
                
                status = '✅' if actual == expected else '❌'
                print(f"   {word}.{category}.{field or 'value'}: {actual} {status}")
                break
    
    # Save report
    report = {
        'total_entries': len(entries),
        'e_ending_issues': len(e_ending_issues),
        'hyphen_issues': len(hyphen_issues),
        'valid_entries': valid_count,
        'invalid_entries': invalid_count,
        'class_distribution': {
            'substantiv': has_substantiv,
            'verb': has_verb,
            'adjektiv': has_adjektiv,
            'övrigt': has_ovrigt,
            'with_any_data': has_any
        },
        'e_ending_issue_details': e_ending_issues,
        'hyphen_issue_details': hyphen_issues
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Report saved to {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("✅ Validation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
