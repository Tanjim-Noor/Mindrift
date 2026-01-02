"""
Step 3d: Apply V4 Fixes - Gender-Aware Noun Definite Forms & Hyphenated Adjectives
==================================================================================
Fixes two systemic issues identified in QA verification:

1. Nouns ending in 'e' with identical definite/indefinite singular:
   - Safety trigger: Only fix when singular == bestämd_singular
   - Utrum (en-words): Apply -én (loanwords) or -n (standard) ending
   - Neutrum (ett-words): Apply -t ending

2. Hyphenated adjectives should not have synthetic comparison:
   - If word contains '-' and has adjektiv forms, null out komparativ/superlativ
   - These use periphrastic comparison (mer/mest) in standard Swedish

This script works SYSTEMICALLY across the entire dataset, not just specific words.
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple, Set


# Configuration
INPUT_FILE = Path("swedish_word_inflections_v3.json")
CLASSIFIED_FILE = Path("step2_classified_entries_v3.json")
OUTPUT_FILE = Path("swedish_word_inflections_v4.1.json")
REPORT_FILE = Path("step3d_v4_fixes_report.json")


# Known loanword patterns that take -én ending (stressed final 'e')
# These are typically French/Latin loanwords where the 'e' is pronounced
LOANWORD_PATTERNS = {
    # Common loanword endings that indicate stressed 'e'
    'abbe',      # abbé (priest/title)
    'ape',       # (if exists)
    'cafe',      # café
    'cliche',    # cliché  
    'communique', # communiqué
    'debutante', # if applicable
    'emigre',    # émigré
    'entree',    # entrée
    'fiance',    # fiancé
    'flambe',    # flambé
    'frappe',    # frappé
    'matinee',   # matinée
    'melee',     # mêlée
    'naive',     # (as noun)
    'protege',   # protégé
    'puree',     # purée
    'resume',    # résumé
    'risque',    # risqué
    'saute',     # sauté
    'soiree',    # soirée
    'souffle',   # soufflé
}

# Words ending in these suffixes are typically loanwords with stressed 'e'
LOANWORD_SUFFIXES = [
    'é',  # Already accented - definitely loanword
    'ee', # Often loanword (matinee, soiree)
    'ée', # French feminine
]

# Swedish native word patterns ending in unstressed 'e' (take -n, not -én)
NATIVE_E_PATTERNS = {
    # Common native Swedish -e endings (unstressed)
    'pojke',   # pojken
    'flicke',  # (rare)
    'vinge',   # vingen
    'granne',  # grannen
    'timme',   # timmen
    'dröppe',  # droppen
    'grabbe',  # grabben - BUT this is colloquial, different from abbé
    'gubbe',   # gubben
    'stabbe',  # stabben
    'snubbe',  # snubben
    'tabbe',   # tabben
}


def detect_gender_from_paradigm(paradigm: str) -> Optional[str]:
    """
    Detect grammatical gender from SALDO paradigm name.
    
    SALDO paradigm naming conventions:
    - nn_*u_* : Utrum (en-words)
    - nn_*n_* : Neutrum (ett-words)
    - pm_u* : Proper name, utrum
    - pm_n* : Proper name, neutrum
    
    Returns: 'utrum', 'neutrum', or None if unknown
    """
    if not paradigm:
        return None
    
    paradigm_lower = paradigm.lower()
    
    # Common noun patterns
    if paradigm_lower.startswith('nn_'):
        # nn_2u_vinge -> utrum
        # nn_3n_bord -> neutrum
        parts = paradigm_lower.split('_')
        if len(parts) >= 3:
            gender_part = parts[1]
            if 'u' in gender_part:
                return 'utrum'
            elif 'n' in gender_part:
                return 'neutrum'
    
    # Proper name patterns
    if paradigm_lower.startswith('pm_'):
        # pm_mph_sture - need to check further
        # pm_uuu_karl - utrum
        # pm_nnn_stockholm - neutrum
        if '_u' in paradigm_lower or 'pm_u' in paradigm_lower:
            return 'utrum'
        if '_n' in paradigm_lower or 'pm_n' in paradigm_lower:
            return 'neutrum'
        # Default proper names to utrum (most common for personal names)
        if 'pm_mph' in paradigm_lower:
            return 'utrum'
    
    return None


def is_loanword_stressed_e(word: str, paradigm: str = None) -> bool:
    """
    Determine if a word ending in 'e' is a loanword with stressed final 'e'.
    These take -én ending in definite singular.
    
    Heuristics:
    1. Word already contains accent (é, è, ê) → loanword
    2. Word is in known loanword list
    3. Word ends in double-e patterns (matinee, soiree)
    4. Paradigm is pm_mph_* (proper name pattern used for loanwords)
    """
    word_lower = word.lower()
    
    # Check for existing accents anywhere in word
    if any(c in word for c in 'éèêëÉÈÊË'):
        return True
    
    # Check known loanword list
    if word_lower in LOANWORD_PATTERNS:
        return True
    
    # Check loanword suffixes
    for suffix in LOANWORD_SUFFIXES:
        if word_lower.endswith(suffix):
            return True
    
    # Check paradigm - pm_mph_* is used for nickname/loanword patterns
    # where definite == indefinite, suggesting foreign origin
    if paradigm and 'pm_mph' in paradigm.lower():
        # This paradigm produces identical forms - likely loanword/foreign
        return True
    
    return False


def is_native_unstressed_e(word: str) -> bool:
    """
    Check if word matches native Swedish patterns with unstressed final 'e'.
    These take -n ending (not -én).
    """
    word_lower = word.lower()
    
    # Check known native patterns
    if word_lower in NATIVE_E_PATTERNS:
        return True
    
    # Common Swedish diminutive/colloquial -e patterns
    # These often end in double consonant + e
    if re.match(r'.*[bcdfghjklmnpqrstvwxz]{2}e$', word_lower):
        # Double consonant before -e suggests native pattern
        # BUT need to be careful - some loanwords also have this
        # Return False to let it fall through to loanword check
        pass
    
    return False


def fix_noun_definite_singular(
    entry: Dict,
    paradigm: str,
    gender: str
) -> Tuple[bool, str, str]:
    """
    Fix noun definite singular form if safety trigger is met.
    
    Safety trigger: singular == bestämd_singular AND word ends in 'e'
    
    Returns: (was_fixed, fix_type, new_form)
    """
    substantiv = entry.get('substantiv')
    if not substantiv:
        return False, '', ''
    
    singular = substantiv.get('singular', '')
    bestämd_singular = substantiv.get('bestämd_singular', '')
    
    # Safety trigger: only fix if forms are identical
    if singular != bestämd_singular:
        return False, '', ''
    
    # Only handle words ending in 'e' (including accented é)
    if not singular or not (singular.endswith('e') or singular.endswith('é')):
        return False, '', ''
    
    word = entry.get('ord', '')
    
    # Determine the correct definite form based on gender
    if gender == 'neutrum':
        # Neutrum nouns: bälte → bältet
        new_form = singular + 't'
        return True, 'neutrum_t', new_form
    
    elif gender == 'utrum':
        # Utrum nouns: need to distinguish loanwords from native
        
        # Check if already has accent
        if singular.endswith('é'):
            # armé → armén (just add n)
            new_form = singular + 'n'
            return True, 'utrum_accented_n', new_form
        
        # Check if loanword with stressed 'e'
        if is_loanword_stressed_e(word, paradigm):
            # abbe → abbén (replace e with én)
            new_form = singular[:-1] + 'én'
            return True, 'utrum_loanword_én', new_form
        
        # Check if native unstressed 'e' OR default case
        # For native Swedish words: vinge → vingen (add n)
        # Also use this as fallback for unclear cases
        new_form = singular + 'n'
        return True, 'utrum_native_n', new_form
    
    else:
        # Gender unknown - make best guess based on word pattern
        if is_loanword_stressed_e(word, paradigm):
            new_form = singular[:-1] + 'én'
            return True, 'unknown_loanword_én', new_form
        else:
            # Default to -n for unknown gender
            new_form = singular + 'n'
            return True, 'unknown_default_n', new_form


def fix_hyphenated_adjective(entry: Dict) -> Tuple[bool, str]:
    """
    Null out comparative/superlative forms for hyphenated adjectives.
    
    Returns: (was_fixed, fix_description)
    """
    word = entry.get('ord', '')
    adjektiv = entry.get('adjektiv')
    
    if '-' not in word:
        return False, ''
    
    if not adjektiv:
        return False, ''
    
    # Check if has synthetic comparison forms to null out
    komparativ = adjektiv.get('komparativ')
    superlativ = adjektiv.get('superlativ')
    
    if komparativ is None and superlativ is None:
        return False, ''
    
    # Null out the comparison forms
    adjektiv['komparativ'] = None
    adjektiv['superlativ'] = None
    
    return True, f"Nulled: {komparativ}/{superlativ}"


def build_paradigm_lookup(classified_entries: List[Dict]) -> Dict[str, Dict]:
    """
    Build a lookup from word → paradigm info from classified entries.
    """
    lookup = {}
    
    for entry in classified_entries:
        word = entry.get('ord', '')
        all_entries = entry.get('all_saldo_entries', [])
        
        # Get substantiv paradigm if exists
        for saldo_entry in all_entries:
            word_class = saldo_entry.get('word_class', '')
            if word_class == 'substantiv':
                paradigm = saldo_entry.get('paradigm', '')
                pos = saldo_entry.get('pos', '')
                lookup[word] = {
                    'paradigm': paradigm,
                    'pos': pos,
                    'gender': detect_gender_from_paradigm(paradigm)
                }
                break
        
        # If no substantiv, check for pm (proper name treated as noun)
        if word not in lookup:
            for saldo_entry in all_entries:
                pos = saldo_entry.get('pos', '')
                if pos == 'pm':
                    paradigm = saldo_entry.get('paradigm', '')
                    lookup[word] = {
                        'paradigm': paradigm,
                        'pos': pos,
                        'gender': detect_gender_from_paradigm(paradigm)
                    }
                    break
    
    return lookup


def main():
    """Main execution function."""
    print("=" * 70)
    print("Step 3d: Apply V4 Fixes - Gender-Aware Definite Forms")
    print("=" * 70)
    
    # Load v3 output
    print(f"\n📂 Loading {INPUT_FILE}...")
    if not INPUT_FILE.exists():
        print(f"❌ Error: {INPUT_FILE} not found")
        return
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"   Loaded {len(entries):,} entries")
    
    # Load classified entries for paradigm info
    print(f"\n📂 Loading {CLASSIFIED_FILE}...")
    if not CLASSIFIED_FILE.exists():
        print(f"❌ Error: {CLASSIFIED_FILE} not found")
        return
    
    with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
        classified_entries = json.load(f)
    print(f"   Loaded {len(classified_entries):,} classified entries")
    
    # Build paradigm lookup
    print("\n🔧 Building paradigm lookup...")
    paradigm_lookup = build_paradigm_lookup(classified_entries)
    print(f"   Built lookup for {len(paradigm_lookup):,} words")
    
    # Count genders
    gender_counts = Counter(v.get('gender') for v in paradigm_lookup.values())
    print(f"   Genders detected: {dict(gender_counts)}")
    
    # Apply fixes
    print("\n🔧 Applying V4 fixes...")
    
    stats = {
        'noun_fixes': Counter(),
        'adjective_fixes': 0,
        'total_modified': 0,
    }
    
    fix_details = []
    
    for entry in entries:
        word = entry.get('ord', '')
        modified = False
        
        # Get paradigm info for this word
        paradigm_info = paradigm_lookup.get(word, {})
        paradigm = paradigm_info.get('paradigm', '')
        gender = paradigm_info.get('gender')
        
        # Fix 1: Noun definite singular
        if entry.get('substantiv'):
            was_fixed, fix_type, new_form = fix_noun_definite_singular(
                entry, paradigm, gender
            )
            if was_fixed:
                old_form = entry['substantiv']['bestämd_singular']
                entry['substantiv']['bestämd_singular'] = new_form
                stats['noun_fixes'][fix_type] += 1
                modified = True
                fix_details.append({
                    'word': word,
                    'type': 'noun',
                    'fix_type': fix_type,
                    'old': old_form,
                    'new': new_form,
                    'gender': gender,
                    'paradigm': paradigm
                })
        
        # Fix 2: Hyphenated adjectives
        was_fixed, fix_desc = fix_hyphenated_adjective(entry)
        if was_fixed:
            stats['adjective_fixes'] += 1
            modified = True
            fix_details.append({
                'word': word,
                'type': 'adjective',
                'fix_type': 'hyphenated_null_comparison',
                'description': fix_desc
            })
        
        if modified:
            stats['total_modified'] += 1
    
    # Report
    print("\n" + "=" * 70)
    print("📊 V4 FIXES SUMMARY")
    print("=" * 70)
    
    print("\n📌 Noun Definite Singular Fixes:")
    utrum_en_count = stats['noun_fixes'].get('utrum_loanword_én', 0) + \
                     stats['noun_fixes'].get('unknown_loanword_én', 0)
    utrum_n_count = stats['noun_fixes'].get('utrum_native_n', 0) + \
                    stats['noun_fixes'].get('utrum_accented_n', 0) + \
                    stats['noun_fixes'].get('unknown_default_n', 0)
    neutrum_t_count = stats['noun_fixes'].get('neutrum_t', 0)
    
    print(f"   Utrum nouns fixed (-én ending): {utrum_en_count}")
    print(f"   Utrum nouns fixed (-n ending):  {utrum_n_count}")
    print(f"   Neutrum nouns fixed (-t ending): {neutrum_t_count}")
    print(f"   Total noun fixes: {sum(stats['noun_fixes'].values())}")
    
    print("\n📌 Detailed noun fix breakdown:")
    for fix_type, count in sorted(stats['noun_fixes'].items()):
        print(f"   {fix_type}: {count}")
    
    print(f"\n📌 Hyphenated Adjectives:")
    print(f"   Comparison forms nulled: {stats['adjective_fixes']}")
    
    print(f"\n📌 Total Entries Modified: {stats['total_modified']}")
    
    # Show sample fixes
    print("\n📝 Sample Noun Fixes:")
    noun_samples = [d for d in fix_details if d['type'] == 'noun'][:15]
    for fix in noun_samples:
        print(f"   {fix['word']}: {fix['old']} → {fix['new']} ({fix['fix_type']})")
    
    print("\n📝 Sample Adjective Fixes:")
    adj_samples = [d for d in fix_details if d['type'] == 'adjective'][:10]
    for fix in adj_samples:
        print(f"   {fix['word']}: {fix['description']}")
    
    # Verify key test cases
    print("\n✅ Key Test Case Verification:")
    test_cases = {
        'abbe': 'abbén',
        'a-social': 'null comparison',
    }
    
    for word, expected in test_cases.items():
        for entry in entries:
            if entry['ord'].lower() == word.lower():
                if word == 'abbe':
                    actual = entry.get('substantiv', {}).get('bestämd_singular', 'N/A')
                    status = '✅' if actual == expected else '❌'
                    print(f"   {word}: bestämd_singular = {actual} (expected: {expected}) {status}")
                elif word == 'a-social':
                    adj = entry.get('adjektiv', {})
                    komp = adj.get('komparativ') if adj else 'N/A'
                    status = '✅' if komp is None else '❌'
                    print(f"   {word}: komparativ = {komp} (expected: None) {status}")
                break
    
    # Save fixed output
    print(f"\n💾 Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    
    # Save detailed report
    print(f"💾 Saving report to {REPORT_FILE}...")
    report = {
        'summary': {
            'utrum_en_fixes': utrum_en_count,
            'utrum_n_fixes': utrum_n_count,
            'neutrum_t_fixes': neutrum_t_count,
            'total_noun_fixes': sum(stats['noun_fixes'].values()),
            'adjective_fixes': stats['adjective_fixes'],
            'total_modified': stats['total_modified'],
        },
        'detailed_counts': dict(stats['noun_fixes']),
        'all_fixes': fix_details,
    }
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("✅ Step 3d Complete - V4 Fixes Applied!")
    print("=" * 70)


if __name__ == "__main__":
    main()
