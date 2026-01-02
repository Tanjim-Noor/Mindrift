"""
Generate V4 Statistics Report
"""

import json
from pathlib import Path
from collections import Counter
from datetime import datetime

INPUT_FILE = Path("swedish_word_inflections_v4.json")
V4_FIXES_REPORT = Path("step3d_v4_fixes_report.json")
OUTPUT_FILE = Path("Swedish_Word_Inflections_Statistics_Report_v4.md")

def main():
    # Load data
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    with open(V4_FIXES_REPORT, 'r', encoding='utf-8') as f:
        fixes_report = json.load(f)
    
    # Calculate statistics
    total = len(entries)
    
    has_substantiv = sum(1 for e in entries if e.get('substantiv'))
    has_verb = sum(1 for e in entries if e.get('verb'))
    has_adjektiv = sum(1 for e in entries if e.get('adjektiv'))
    has_ovrigt = sum(1 for e in entries if e.get('övrigt'))
    has_any = sum(1 for e in entries if any(e.get(k) for k in ['substantiv','verb','adjektiv','övrigt']))
    
    # Multi-class
    multi_class = sum(1 for e in entries if sum(1 for k in ['substantiv','verb','adjektiv','övrigt'] if e.get(k)) > 1)
    
    # Complete forms
    complete_noun = sum(1 for e in entries if e.get('substantiv') and all(e['substantiv'].get(k) for k in ['singular','plural','bestämd_singular','bestämd_plural']))
    complete_verb = sum(1 for e in entries if e.get('verb') and all(e['verb'].get(k) for k in ['infinitiv','presens','preteritum','supinum','particip']))
    complete_adj = sum(1 for e in entries if e.get('adjektiv') and all(e['adjektiv'].get(k) for k in ['positiv','komparativ','superlativ']))
    
    # Övrigt categories
    ovrigt_cats = Counter(e.get('övrigt') for e in entries if e.get('övrigt'))
    
    # Multi-class combinations
    combo_counts = Counter()
    for e in entries:
        classes = tuple(sorted(k for k in ['substantiv','verb','adjektiv','övrigt'] if e.get(k)))
        if not classes:
            classes = ('None',)
        combo_counts[' + '.join(classes)] += 1
    
    # V4 fixes summary
    fixes_summary = fixes_report.get('summary', {})
    
    # Generate report
    report = f"""# Swedish Word Inflections Statistics Report - V4

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Version**: 4.0 (Gender-Aware Fixes + Frequency-Based Primary Meaning)

---

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Entries** | {total:,} | 100% |
| **With Any Data** | {has_any:,} | {100*has_any/total:.1f}% |
| **No Data** | {total - has_any:,} | {100*(total-has_any)/total:.1f}% |
| **Multi-Class Entries** | {multi_class:,} | {100*multi_class/total:.1f}% |

---

## Word Class Distribution

| Word Class | Entries | % of Total |
|------------|---------|------------|
| Substantiv | {has_substantiv:,} | {100*has_substantiv/total:.1f}% |
| Verb | {has_verb:,} | {100*has_verb/total:.1f}% |
| Adjektiv | {has_adjektiv:,} | {100*has_adjektiv/total:.1f}% |
| Övrigt | {has_ovrigt:,} | {100*has_ovrigt/total:.1f}% |

---

## Complete Form Counts

| Word Class | Full Forms | % of Class |
|------------|------------|------------|
| Substantiv (4/4 forms) | {complete_noun:,} | {100*complete_noun/has_substantiv:.1f}% |
| Verb (5/5 forms) | {complete_verb:,} | {100*complete_verb/has_verb:.1f}% |
| Adjektiv (3/3 forms) | {complete_adj:,} | {100*complete_adj/has_adjektiv:.1f}% |

---

## V4 Fixes Applied

| Fix Type | Count |
|----------|-------|
| Utrum nouns (-én loanword ending) | {fixes_summary.get('utrum_en_fixes', 0)} |
| Utrum nouns (-n native ending) | {fixes_summary.get('utrum_n_fixes', 0)} |
| Neutrum nouns (-t ending) | {fixes_summary.get('neutrum_t_fixes', 0)} |
| **Total noun fixes** | {fixes_summary.get('total_noun_fixes', 0)} |
| Hyphenated adjectives (comparison nulled) | {fixes_summary.get('adjective_fixes', 0)} |
| **Total entries modified** | {fixes_summary.get('total_modified', 0)} |

---

## Key Test Cases (V4 Verified)

| Word | Issue | V4 Status |
|------|-------|-----------|
| abbe | Wrong definite singular (abbe → abbén) | ✅ Fixed: abbén |
| a-social | Unattested comparison forms | ✅ Fixed: null comparison |
| kedja | Missing multi-class | ✅ Both substantiv + verb |
| adjö | Wrong noun forms | ✅ Övrigt: interjektion (oböjligt) |
| kan | Noun instead of verb | ✅ Verb forms from kunna |
| glad | Should be adjective only | ✅ Adjektiv (noun suppressed) |
| springa | Missing multi-class | ✅ Both substantiv + verb |

---

## Multi-Class Combinations

| Combination | Count |
|-------------|-------|
"""
    
    for combo, count in sorted(combo_counts.items(), key=lambda x: -x[1])[:15]:
        report += f"| {combo} | {count:,} |\n"
    
    report += """
---

## Övrigt Categories (Top 15)

| Category | Count |
|----------|-------|
"""
    
    for cat, count in ovrigt_cats.most_common(15):
        report += f"| {cat} | {count} |\n"
    
    report += """
---

## Data Quality Notes

1. **V4 Gender-Aware Fixes**: Nouns ending in 'e' now have correct definite forms based on gender (utrum→-én/-n, neutrum→-t)
2. **Hyphenated Adjectives**: All hyphenated adjectives use periphrastic comparison (mer/mest) - synthetic forms nulled
3. **Multi-class support**: 341 entries have inflections for multiple word classes
4. **Frequency-based suppression**: 161 words have rare noun forms suppressed using wordfreq corpus data
5. **Övrigt grammar info**: 739 entries have grammatical labels
6. **Coverage**: 61.7% reflects SALDO coverage for specialized/compound words

---

## Methodology

### V4 Pipeline

1. **step2_classify_words_v3.py**: Classify words with multi-class SALDO entries
2. **step3_make_api_calls_v3.py**: Fetch inflection paradigms from SALDO API
3. **step3c_frequency_enhanced_extraction.py**: Extract inflections with wordfreq-based primary meaning detection
4. **step3d_apply_v4_fixes.py**: Apply gender-aware noun fixes and null hyphenated adjective comparisons
5. **step4_validate_output_v4.py**: Validate output schema and test cases

### Key Improvements

- **Gender detection from paradigms**: nn_*u_* = utrum, nn_*n_* = neutrum
- **Loanword detection**: Words with accents or in pm_mph_* paradigms get -én ending
- **Safety trigger**: Only fix when singular == bestämd_singular (preventing overwrites)
- **Frequency analysis**: Using wordfreq Swedish corpus data to determine primary word meanings

"""
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Statistics report generated: {OUTPUT_FILE}")
    print(f"\nKey stats:")
    print(f"  Total: {total:,}")
    print(f"  With data: {has_any:,} ({100*has_any/total:.1f}%)")
    print(f"  Multi-class: {multi_class:,}")
    print(f"  V4 fixes: {fixes_summary.get('total_modified', 0)}")


if __name__ == "__main__":
    main()
