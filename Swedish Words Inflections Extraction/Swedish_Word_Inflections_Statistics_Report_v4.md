# Swedish Word Inflections Statistics Report - V4

**Generated**: 2026-01-02 13:34:33
**Version**: 4.0 (Gender-Aware Fixes + Frequency-Based Primary Meaning)

---

## Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Entries** | 13,872 | 100% |
| **With Any Data** | 8,564 | 61.7% |
| **No Data** | 5,308 | 38.3% |
| **Multi-Class Entries** | 341 | 2.5% |

---

## Word Class Distribution

| Word Class | Entries | % of Total |
|------------|---------|------------|
| Substantiv | 6,122 | 44.1% |
| Verb | 1,134 | 8.2% |
| Adjektiv | 913 | 6.6% |
| Övrigt | 739 | 5.3% |

---

## Complete Form Counts

| Word Class | Full Forms | % of Class |
|------------|------------|------------|
| Substantiv (4/4 forms) | 5,307 | 86.7% |
| Verb (5/5 forms) | 1,134 | 100.0% |
| Adjektiv (3/3 forms) | 818 | 89.6% |

---

## V4 Fixes Applied

| Fix Type | Count |
|----------|-------|
| Utrum nouns (-én loanword ending) | 1 |
| Utrum nouns (-n native ending) | 0 |
| Neutrum nouns (-t ending) | 0 |
| **Total noun fixes** | 1 |
| Hyphenated adjectives (comparison nulled) | 1 |
| **Total entries modified** | 2 |

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
| substantiv | 5,820 |
| None | 5,308 |
| verb | 937 |
| adjektiv | 820 |
| övrigt | 646 |
| substantiv + verb | 178 |
| adjektiv + substantiv | 67 |
| substantiv + övrigt | 55 |
| adjektiv + övrigt | 22 |
| verb + övrigt | 13 |
| adjektiv + verb | 3 |
| substantiv + verb + övrigt | 2 |
| adjektiv + verb + övrigt | 1 |

---

## Övrigt Categories (Top 15)

| Category | Count |
|----------|-------|
| verb (fras) | 171 |
| adverb (oböjligt) | 159 |
| adverb (fras) (oböjligt) | 61 |
| egennamn (fras) | 59 |
| interjektion (oböjligt) | 53 |
| preposition (oböjligt) | 45 |
| räkneord | 41 |
| pronomen | 29 |
| sxc | 29 |
| egennamn (förkortning) | 20 |
| interjektion (fras) (oböjligt) | 16 |
| substantiv (fras) | 16 |
| adverb | 15 |
| subjunktion (oböjligt) | 6 |
| adjektiv (fras) (oböjligt) | 4 |

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

