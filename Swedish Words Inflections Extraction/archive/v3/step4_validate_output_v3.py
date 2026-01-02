"""
Step 4 v3: Validate Output with Multi-Class Support
=====================================================
Validates the v3 output that supports multiple word classes per entry.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Tuple

# Configuration
INPUT_FILE = Path("swedish_word_inflections_v3.json")
REPORT_FILE = Path("step4_validation_report_v3.json")


def validate_entry(entry: Dict) -> Dict:
    """Validate a single entry with multi-class support."""
    result = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'classes_found': []
    }
    
    # Check required field
    if 'ord' not in entry:
        result['errors'].append("Missing 'ord' field")
        result['valid'] = False
        return result
    
    ord_value = entry['ord']
    
    # Check structure
    required_fields = ['ord', 'substantiv', 'verb', 'adjektiv', 'övrigt']
    for field in required_fields:
        if field not in entry:
            result['errors'].append(f"Missing field: {field}")
            result['valid'] = False
    
    # Validate substantiv
    subst = entry.get('substantiv')
    if subst is not None:
        if not isinstance(subst, dict):
            result['errors'].append("substantiv must be dict or null")
            result['valid'] = False
        else:
            result['classes_found'].append('substantiv')
            expected_keys = ['singular', 'plural', 'bestämd_singular', 'bestämd_plural']
            for key in expected_keys:
                if key not in subst:
                    result['warnings'].append(f"substantiv missing key: {key}")
                elif subst[key] is not None and not isinstance(subst[key], str):
                    result['errors'].append(f"substantiv.{key} must be string or null")
                    result['valid'] = False
    
    # Validate verb
    verb = entry.get('verb')
    if verb is not None:
        if not isinstance(verb, dict):
            result['errors'].append("verb must be dict or null")
            result['valid'] = False
        else:
            result['classes_found'].append('verb')
            expected_keys = ['infinitiv', 'presens', 'preteritum', 'supinum', 'particip']
            for key in expected_keys:
                if key not in verb:
                    result['warnings'].append(f"verb missing key: {key}")
                elif verb[key] is not None and not isinstance(verb[key], str):
                    result['errors'].append(f"verb.{key} must be string or null")
                    result['valid'] = False
    
    # Validate adjektiv
    adj = entry.get('adjektiv')
    if adj is not None:
        if not isinstance(adj, dict):
            result['errors'].append("adjektiv must be dict or null")
            result['valid'] = False
        else:
            result['classes_found'].append('adjektiv')
            expected_keys = ['positiv', 'komparativ', 'superlativ']
            for key in expected_keys:
                if key not in adj:
                    result['warnings'].append(f"adjektiv missing key: {key}")
                elif adj[key] is not None and not isinstance(adj[key], str):
                    result['errors'].append(f"adjektiv.{key} must be string or null")
                    result['valid'] = False
    
    # Validate övrigt - NOW ALLOWS STRINGS
    ovrigt = entry.get('övrigt')
    if ovrigt is not None:
        if not isinstance(ovrigt, str):
            result['errors'].append("övrigt must be string or null")
            result['valid'] = False
        else:
            result['classes_found'].append('övrigt')
    
    # Multi-class is now EXPECTED and valid
    if len(result['classes_found']) > 1:
        result['warnings'].append(f"Multi-class entry: {result['classes_found']}")
    
    return result


def main():
    """Main validation function."""
    print("=" * 60)
    print("Step 4 v3: Validate Multi-Class Output")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading data from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} entries")
    
    # Validate each entry
    print("\n--- Validating Entries ---")
    
    valid_count = 0
    invalid_count = 0
    warning_count = 0
    all_errors = []
    all_warnings = []
    
    class_counts = Counter()
    multi_class_counts = Counter()
    
    for i, entry in enumerate(data):
        result = validate_entry(entry)
        
        if result['valid']:
            valid_count += 1
        else:
            invalid_count += 1
            for err in result['errors']:
                all_errors.append({'index': i, 'ord': entry.get('ord'), 'error': err})
        
        if result['warnings']:
            warning_count += 1
            for warn in result['warnings']:
                all_warnings.append({'index': i, 'ord': entry.get('ord'), 'warning': warn})
        
        # Count classes
        for cls in result['classes_found']:
            class_counts[cls] += 1
        
        # Count multi-class combinations
        if len(result['classes_found']) > 1:
            combo = tuple(sorted(result['classes_found']))
            multi_class_counts[combo] += 1
    
    # Print results
    print(f"\n  Valid entries: {valid_count} ({valid_count/len(data)*100:.1f}%)")
    print(f"  Invalid entries: {invalid_count}")
    print(f"  Entries with warnings: {warning_count}")
    
    print(f"\n--- Class Distribution ---")
    for cls, count in class_counts.most_common():
        pct = count / len(data) * 100
        print(f"  {cls}: {count} ({pct:.1f}%)")
    
    print(f"\n--- Multi-Class Combinations ---")
    total_multi = sum(multi_class_counts.values())
    print(f"  Total multi-class entries: {total_multi}")
    for combo, count in multi_class_counts.most_common(10):
        combo_str = ' + '.join(combo)
        print(f"    {combo_str}: {count}")
    
    if all_errors:
        print(f"\n--- Sample Errors (first 10) ---")
        for err in all_errors[:10]:
            print(f"  [{err['index']}] {err['ord']}: {err['error']}")
    
    # Calculate coverage stats
    with_data = sum(1 for e in data if any([
        e.get('substantiv'), e.get('verb'), e.get('adjektiv'), e.get('övrigt')
    ]))
    
    print(f"\n--- Coverage ---")
    print(f"  Entries with any data: {with_data} ({with_data/len(data)*100:.1f}%)")
    print(f"  Entries with no data: {len(data) - with_data}")
    
    # Check specific test cases
    print(f"\n--- Test Case Verification ---")
    test_words = {
        'kedja': 'Should have both substantiv AND verb',
        'adjö': 'Should have övrigt (interjektion) or minimal noun',
        'kan': 'Should have verb forms (from kunna)',
        'glad': 'Should have adjektiv',
        'springa': 'Should have verb',
        'handla': 'Should have verb (possibly noun too)',
        'bete': 'Should have substantiv (possibly verb too)',
    }
    
    for word, expected in test_words.items():
        matches = [e for e in data if e['ord'] == word]
        if matches:
            entry = matches[0]
            classes = []
            if entry.get('substantiv'): classes.append('substantiv')
            if entry.get('verb'): classes.append('verb')
            if entry.get('adjektiv'): classes.append('adjektiv')
            if entry.get('övrigt'): classes.append(f"övrigt({entry['övrigt']})")
            print(f"  {word}: {' + '.join(classes) if classes else 'NO DATA'}")
            print(f"    Expected: {expected}")
        else:
            print(f"  {word}: NOT FOUND")
    
    # Save report
    report = {
        "total_entries": len(data),
        "valid_entries": valid_count,
        "invalid_entries": invalid_count,
        "entries_with_warnings": warning_count,
        "entries_with_data": with_data,
        "coverage_percentage": with_data / len(data) * 100,
        "class_distribution": dict(class_counts),
        "multi_class_counts": {'+'.join(k): v for k, v in multi_class_counts.items()},
        "total_multi_class": total_multi,
        "errors": all_errors[:100],
        "warnings": all_warnings[:100]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 4 v3 Complete!")
    print("=" * 60)
    
    return invalid_count == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
