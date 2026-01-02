"""
Step 3e: Remove Unattested PM-Derived Noun Forms
================================================
QA Issue: Words like "abbe" have noun forms (abbar, abbarna) derived from 
SALDO's proper name paradigm (pm_mph_sture for nicknames), NOT from an 
attested common noun paradigm.

Real Swedish: "abbé" → "abbéer" (plural) - this is a different word
The form "abbe" as common noun is unattested and violates Requirement #5:
"Gör inga egna gissningar" (Don't make your own guesses)

This script:
1. Identifies words where pos='pm' was mapped to word_class='substantiv'
2. Checks if the word has ONLY pm paradigm (no real nn paradigm)
3. Nulls the substantiv field for such words

Root Cause: In classification, POS_TO_CLASS maps 'pm' → 'substantiv'
           This should be 'pm' → 'övrigt' (egennamn)
           
Prevention: Document that pm paradigms should map to 'övrigt', not 'substantiv'
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set


# Configuration
INPUT_FILE = Path("swedish_word_inflections_v4.1.json")
CLASSIFIED_FILE = Path("archive/v3/step2_classified_entries_v3.json")
OUTPUT_FILE = Path("swedish_word_inflections_v4.1.json")  # Overwrite v4.1
REPORT_FILE = Path("step3e_pm_noun_removal_report.json")


def load_json(filepath: Path) -> any:
    """Load JSON file with UTF-8 encoding."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: any, filepath: Path):
    """Save JSON file with UTF-8 encoding and Swedish characters."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def identify_pm_only_nouns(classified_data: List[Dict]) -> Dict[str, Dict]:
    """
    Find words where:
    1. primary_pos_tag == 'pm' (proper name)
    2. primary_word_class == 'substantiv' (incorrectly mapped)
    3. No other paradigm is a real noun paradigm (nn_*)
    
    Returns dict of {word: classification_info}
    """
    pm_only_nouns = {}
    
    for entry in classified_data:
        ord_word = entry.get('ord', '')
        primary_pos = entry.get('primary_pos_tag', '')
        primary_class = entry.get('primary_word_class', '')
        
        # Check if this is a pm → substantiv mapping
        if primary_pos == 'pm' and primary_class == 'substantiv':
            # Check all SALDO entries for this word
            all_entries = entry.get('all_saldo_entries', [])
            
            # Look for any real noun paradigm (nn_*)
            has_real_noun = False
            pm_paradigms = []
            
            for saldo_entry in all_entries:
                paradigm = saldo_entry.get('paradigm', '')
                pos = saldo_entry.get('pos', '')
                
                if pos == 'nn' or paradigm.startswith('nn_'):
                    has_real_noun = True
                    break
                    
                if pos == 'pm' or paradigm.startswith('pm_'):
                    pm_paradigms.append(paradigm)
            
            # If no real noun paradigm, this word should NOT have substantiv
            if not has_real_noun and pm_paradigms:
                pm_only_nouns[ord_word] = {
                    'pm_paradigms': pm_paradigms,
                    'classification': entry
                }
    
    return pm_only_nouns


def remove_pm_noun_forms(inflections: List[Dict], pm_only_nouns: Dict[str, Dict]) -> tuple:
    """
    Remove substantiv from words that only have pm paradigms.
    
    Returns: (modified_data, changes_list)
    """
    changes = []
    
    for entry in inflections:
        ord_word = entry.get('ord', '')
        
        if ord_word in pm_only_nouns and entry.get('substantiv') is not None:
            old_substantiv = entry['substantiv'].copy()
            entry['substantiv'] = None
            
            changes.append({
                'ord': ord_word,
                'action': 'nulled_substantiv',
                'reason': 'pm-only paradigm (no attested noun)',
                'pm_paradigms': pm_only_nouns[ord_word]['pm_paradigms'],
                'removed_forms': old_substantiv
            })
    
    return inflections, changes


def generate_scope_report(pm_only_nouns: Dict[str, Dict]) -> Dict:
    """Generate scope report showing all affected words."""
    
    # Group by paradigm pattern
    by_paradigm = defaultdict(list)
    for word, info in pm_only_nouns.items():
        for paradigm in info['pm_paradigms']:
            by_paradigm[paradigm].append(word)
    
    return {
        'total_affected': len(pm_only_nouns),
        'words_affected': sorted(pm_only_nouns.keys()),
        'by_paradigm': {k: sorted(v) for k, v in sorted(by_paradigm.items())},
        'root_cause': "POS_TO_CLASS maps 'pm' → 'substantiv' (should be 'övrigt')",
        'prevention': "In step2_classify_words.py, change POS_TO_CLASS['pm'] from 'substantiv' to 'övrigt'"
    }


def main():
    print("Step 3e: Remove Unattested PM-Derived Noun Forms")
    print("=" * 60)
    
    # Load data
    print("\nLoading data...")
    inflections = load_json(INPUT_FILE)
    classified = load_json(CLASSIFIED_FILE)
    
    print(f"  Loaded {len(inflections)} inflection entries")
    print(f"  Loaded {len(classified)} classified entries")
    
    # Identify pm-only nouns
    print("\nIdentifying words with pm-only paradigms mapped to substantiv...")
    pm_only_nouns = identify_pm_only_nouns(classified)
    print(f"  Found {len(pm_only_nouns)} words with pm-only paradigms")
    
    if pm_only_nouns:
        print("\n  Affected words:")
        for word in sorted(pm_only_nouns.keys())[:20]:  # Show first 20
            paradigms = pm_only_nouns[word]['pm_paradigms']
            print(f"    - {word}: {', '.join(paradigms)}")
        if len(pm_only_nouns) > 20:
            print(f"    ... and {len(pm_only_nouns) - 20} more")
    
    # Remove pm-derived noun forms
    print("\nRemoving unattested noun forms...")
    inflections, changes = remove_pm_noun_forms(inflections, pm_only_nouns)
    print(f"  Applied {len(changes)} changes")
    
    # Generate scope report
    scope_report = generate_scope_report(pm_only_nouns)
    
    # Save results
    print("\nSaving results...")
    save_json(inflections, OUTPUT_FILE)
    print(f"  Updated: {OUTPUT_FILE}")
    
    # Save detailed report
    report = {
        'summary': {
            'total_pm_only_nouns': len(pm_only_nouns),
            'changes_applied': len(changes),
            'input_file': str(INPUT_FILE),
            'output_file': str(OUTPUT_FILE)
        },
        'scope': scope_report,
        'changes': changes,
        'prevention': {
            'issue': "pm paradigms incorrectly mapped to substantiv",
            'fix': "In POS_TO_CLASS, change 'pm': 'substantiv' to 'pm': 'övrigt'",
            'file': "step2_classify_words.py"
        }
    }
    save_json(report, REPORT_FILE)
    print(f"  Report: {REPORT_FILE}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total pm-only nouns identified: {len(pm_only_nouns)}")
    print(f"Substantiv fields nulled: {len(changes)}")
    
    if changes:
        print("\nChanges made:")
        for change in changes:
            print(f"  - {change['ord']}: nulled substantiv (was {change['removed_forms']})")
    
    print("\nPrevention:")
    print("  Root cause: POS_TO_CLASS maps 'pm' → 'substantiv'")
    print("  Fix: Change to 'pm' → 'övrigt' in step2_classify_words.py")
    
    return len(changes)


if __name__ == "__main__":
    main()
