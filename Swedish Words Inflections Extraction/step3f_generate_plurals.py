#!/usr/bin/env python
"""
Step 3f: Generate Synthetic Plural Forms for Singularia Tantum Nouns

PROBLEM:
SALDO classifies ~732 nouns as "singularia tantum" (singular-only) using nn_0* paradigms.
However, QA indicates many of these nouns have valid, attested plural forms in modern Swedish.
Examples:
  - arbetskraft → arbetskrafter, arbetskrafterna
  - manikyr → manikyrer, manikyrerna
  
SOLUTION:
Generate synthetic plural forms based on the noun's gender and ending pattern.
Swedish noun plural formation follows predictable patterns:

For common gender (utrum/u) nouns:
  - Nouns ending in consonant → add -er/-erna (e.g., kraft → krafter)
  - Nouns ending in -a → add -or/-orna (e.g., flora → floror)  
  - Nouns ending in -e → add -ar/-arna (e.g., kaffe → kaffear) OR same/-n (oböjligt)
  - Nouns ending in unstressed vowel → add -r/-rna or -er/-erna

For neuter gender (n) nouns:
  - Nouns ending in consonant → same form (e.g., ansvar → ansvar)
  - Nouns ending in -e → add -n/-na (e.g., syre → syren/syrena)
  
We'll use the singular definite form to help determine the pattern.
"""

import json
import re
from collections import defaultdict

# Configuration
INPUT_FILE = 'swedish_word_inflections_v4.1.json'
OUTPUT_FILE = 'swedish_word_inflections_v4.2.json'
REPORT_FILE = 'step3f_plural_generation_report.json'

# Paradigm patterns for generating plurals
# The key is the paradigm name, value is (plural_suffix, def_plural_suffix) or None if truly uncountable
PARADIGM_PLURAL_RULES = {
    # Common gender (utrum) paradigms - most can have plurals
    'nn_0u_boskap': ('er', 'erna'),      # kraft → krafter, arbetskraft → arbetskrafter
    'nn_0u_månsing': ('er', 'erna'),     # manikyr → manikyrer
    'nn_0u_radar': (None, None),         # loan words, often truly invariable
    'nn_0u_akribi': ('er', 'erna'),      # anarki → anarkier
    'nn_0u_hin': (None, None),           # truly singular (action, april)
    'nn_0u_kärnkraft': ('er', 'erna'),   # kraft-compounds
    'nn_0u_svenska': ('or', 'orna'),     # svenska → svenskor (but usually uncountable)
    'nn_0u_samverkan': (None, None),     # abstract -an nouns, truly uncountable
    'nn_0u_tro': (None, None),           # abstract concepts
    'nn_0u_mjölk': (None, None),         # mass nouns
    'nn_0u_hemsjuka': ('or', 'orna'),    # -sjuka compounds 
    'nn_0u_tjockolja': ('or', 'orna'),   # -olja compounds
    'nn_0u_skam': (None, None),          # abstract
    'nn_0u_saltsyra': ('or', 'orna'),    # -syra compounds
    'nn_0u_hälsa': ('or', 'orna'),       # -a ending nouns
    'nn_0u_praxis': (None, None),        # Latin loans
    
    # Neuter paradigms - many are truly invariable
    'nn_0n_ansvar': (None, None),        # ansvar → ansvar (same)
    'nn_0n_dalt': (None, None),          # truly singular
    'nn_0n_syre': ('n', 'na'),           # syre → syren/syrena (rare)
    'nn_0n_babbel': (None, None),        # truly uncountable
    'nn_0n_latin': (None, None),         # language names
    'nn_0n_hindi': (None, None),         # language names
    'nn_0n_skum': (None, None),          # mass nouns
    'nn_0n_raseri': ('er', 'erna'),      # raserier (rare but possible)
    'nn_0n_koksalt': (None, None),       # chemical compounds
    'nn_0n_opium': (None, None),         # substances
    'nn_0n_toapapper': (None, None),     # mass nouns
    
    # Variable paradigms
    'nn_0v_bikarbonat': (None, None),    # chemical compounds
    'nn_0v_blod': (None, None),          # mass nouns
    'nn_0v_manna': (None, None),         # biblical
    'nn_0v_gin': (None, None),           # drinks
    'nn_0v_dregel': (None, None),        # truly uncountable
    'nn_0v_facit': (None, None),         # invariable
    'nn_0v_saffran': (None, None),       # spices
    'nn_0v_status': (None, None),        # Latin loans
}

# High-value countable nouns that should definitely have plurals
# These override PARADIGM_PLURAL_RULES
FORCE_PLURAL_NOUNS = {
    # Words from QA feedback - confirmed to have attested plurals
    'arbetskraft': ('arbetskrafter', 'arbetskrafterna'),
    'manikyr': ('manikyrer', 'manikyrerna'),
    
    # Common nouns that clearly should have plurals
    'anarki': ('anarkier', 'anarkierna'),
    'allergi': ('allergier', 'allergierna'),
    'biografi': ('biografier', 'biografierna'),
    'demokrati': ('demokratier', 'demokratierna'),
    'strategi': ('strategier', 'strategierna'),
    'terapi': ('terapier', 'terapierna'),
    
    # -kraft compounds
    'andnöd': ('andnöder', 'andnöderna'),  # Actually -nöd not -kraft
    'kärnkraft': ('kärnkrafter', 'kärnkrafterna'),
    'köpkraft': ('köpkrafter', 'köpkrafterna'),
    'levnadskraft': ('levnadskrafter', 'levnadskrafterna'),
    'livskraft': ('livskrafter', 'livskrafterna'),
    'muskelkraft': ('muskelkrafter', 'muskelkrafterna'),
    'solkraft': ('solkrafter', 'solkrafterna'),
    'strömkraft': ('strömkrafter', 'strömkrafterna'),
    'vattenkraft': ('vattenkrafter', 'vattenkrafterna'),
    'vindkraft': ('vindkrafter', 'vindkrafterna'),
    'allmakt': ('allmakter', 'allmakterna'),
    
    # Activity/service nouns that can be counted (multiple instances)
    'pedikyr': ('pedikyrer', 'pedikyrerna'),
    'massage': ('massager', 'massagerna'),
    
    # Abstract nouns that can be pluralized in context
    'aptit': ('aptiter', 'aptiterna'),
    'desperation': ('desperationer', 'desperationerna'),
    
    # Disciplines/fields that can be pluralized
    'filosofi': ('filosofier', 'filosofierna'),
    'psykologi': ('psykologier', 'psykologierna'),
    'sociologi': ('sociologier', 'sociologierna'),
    'antropologi': ('antropologier', 'antropologierna'),
    'arkeologi': ('arkeologier', 'arkeologierna'),
    'ekologi': ('ekologier', 'ekologierna'),
    'geologi': ('geologier', 'geologierna'),
    'ideologi': ('ideologier', 'ideologierna'),
    'kronologi': ('kronologier', 'kronologierna'),
    'metodologi': ('metodologier', 'metodologierna'),
    'teknologi': ('teknologier', 'teknologierna'),
    'teologi': ('teologier', 'teologierna'),
}

def load_classified_entries():
    """Load the classified entries to get paradigm info."""
    with open('archive/v3/step2_classified_entries_v3.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {entry['ord']: entry for entry in data}

def generate_plural_from_pattern(word, singular, singular_def, paradigm):
    """Generate plural forms based on word ending and paradigm."""
    
    # First check force list
    if word in FORCE_PLURAL_NOUNS:
        return FORCE_PLURAL_NOUNS[word]
    
    # Get paradigm rules
    rules = PARADIGM_PLURAL_RULES.get(paradigm)
    if not rules or rules == (None, None):
        return (None, None)  # Truly uncountable
    
    plural_suffix, def_plural_suffix = rules
    
    # Generate based on word ending
    if singular.endswith('a'):
        # -a nouns usually get -or
        if plural_suffix == 'or':
            plural = singular[:-1] + 'or'
            def_plural = singular[:-1] + 'orna'
        else:
            plural = singular + plural_suffix
            def_plural = singular + def_plural_suffix
    elif singular.endswith('e'):
        # -e nouns vary
        if plural_suffix == 'ar':
            plural = singular[:-1] + 'ar'
            def_plural = singular[:-1] + 'arna'
        elif plural_suffix == 'n':
            plural = singular + 'n'
            def_plural = singular + 'na'
        else:
            plural = singular + plural_suffix
            def_plural = singular + def_plural_suffix
    elif singular.endswith('i'):
        # -i nouns (like allergi) get -er
        plural = singular + 'er'
        def_plural = singular + 'erna'
    elif singular.endswith('r'):
        # -r nouns (like manikyr) get -er
        plural = singular + 'er'
        def_plural = singular + 'erna'
    else:
        # Default: consonant ending → -er
        plural = singular + plural_suffix
        def_plural = singular + def_plural_suffix
    
    return (plural, def_plural)

def main():
    print("=" * 60)
    print("Step 3f: Generate Synthetic Plural Forms")
    print("=" * 60)
    
    # Load current output
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load classified entries for paradigm info
    classified = load_classified_entries()
    
    # Track changes
    changes = []
    unchanged_null_plurals = []
    
    for entry in data:
        word = entry['ord']
        subst = entry.get('substantiv')
        
        if not subst:
            continue
            
        singular = subst.get('singular')
        singular_def = subst.get('bestämd_singular')
        plural = subst.get('plural')
        def_plural = subst.get('bestämd_plural')
        
        # Only process nouns with null plural
        if singular and not plural:
            # Get paradigm from classified entries
            classified_entry = classified.get(word, {})
            paradigm = classified_entry.get('primary_paradigm', '')
            
            if paradigm.startswith('nn_0'):
                # This is a singularia tantum noun - try to generate plural
                new_plural, new_def_plural = generate_plural_from_pattern(
                    word, singular, singular_def, paradigm
                )
                
                if new_plural:
                    changes.append({
                        'word': word,
                        'paradigm': paradigm,
                        'old_plural': plural,
                        'new_plural': new_plural,
                        'old_def_plural': def_plural,
                        'new_def_plural': new_def_plural
                    })
                    subst['plural'] = new_plural
                    subst['bestämd_plural'] = new_def_plural
                else:
                    unchanged_null_plurals.append({
                        'word': word,
                        'paradigm': paradigm,
                        'reason': 'Paradigm rules indicate truly uncountable'
                    })
            else:
                # Non nn_0 paradigm with null plural - investigate
                unchanged_null_plurals.append({
                    'word': word,
                    'paradigm': paradigm or 'unknown',
                    'reason': 'Not an nn_0 paradigm'
                })
    
    # Save output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Generate report
    report = {
        'summary': {
            'total_entries': len(data),
            'plurals_generated': len(changes),
            'unchanged_null_plurals': len(unchanged_null_plurals)
        },
        'changes': changes,
        'unchanged_null_plurals': unchanged_null_plurals[:50]  # Sample
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults:")
    print(f"  Total entries processed: {len(data)}")
    print(f"  Plural forms generated: {len(changes)}")
    print(f"  Unchanged null plurals: {len(unchanged_null_plurals)}")
    print(f"\nOutput saved to: {OUTPUT_FILE}")
    print(f"Report saved to: {REPORT_FILE}")
    
    # Show sample changes
    print(f"\nSample changes:")
    for change in changes[:10]:
        print(f"  {change['word']}: {change['new_plural']}, {change['new_def_plural']}")

if __name__ == '__main__':
    main()
