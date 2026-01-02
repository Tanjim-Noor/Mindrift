# Swedish Word Inflections Statistics Report - V3

**Generated**: 2026-01-02 10:02:21
**Version**: 3.0 (Multi-Class Support)

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
| Adjektiv (3/3 forms) | 819 | 89.7% |

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

## Övrigt Categories (Top 20)

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
| preposition (fras) (oböjligt) | 4 |
| konjunktion (oböjligt) | 3 |
| nnh | 2 |
| pronomen (fras) | 2 |
| pronomen (fras) (oböjligt) | 2 |

---

## Key Test Cases (V3 Fixes)

| Word | V2 Issue | V3 Status |
|------|----------|-----------|
| kedja | Only verb, missing noun | ✅ Both substantiv + verb |
| adjö | Wrong noun forms (adjön, adjöt) | ✅ Övrigt: interjektion (oböjligt) |
| kan | Noun (khan) instead of verb | ✅ Verb forms from kunna |
| glad | Noun + adjektiv | ✅ Adjektiv only (noun suppressed) |
| springa | Only verb, missing noun | ✅ Both substantiv + verb |

---

## Frequency-Based Primary Meaning Detection

V3 uses the **wordfreq** library (Swedish corpus data from Wikipedia, Subtitles, Web, Twitter, Reddit) to automatically determine primary word meanings and suppress incorrect/rare word classes.

**Words with noun forms suppressed based on frequency analysis: 161**

Examples of automatic decisions:
- **adjö** (zipf=3.61): interjektion is primary - noun suppressed
- **glad** (zipf=5.28): Adjective is primary - noun suppressed  
- **absolut** (zipf=5.28): adverb is primary - noun suppressed
- **allt** (zipf=6.19): adverb is primary - noun suppressed
- **fan** (zipf=5.86): interjektion is primary - noun suppressed
- **fel** (zipf=5.80): Adjective is primary - noun suppressed
- **fort** (zipf=5.21): adverb is primary - noun suppressed

This is a **systemic solution** that works across all 13,872 words, not manual word-by-word mappings.

---

## Data Quality Notes

1. **Multi-class support**: 341 entries now have inflections for multiple word classes
2. **Övrigt grammar info**: 739 entries have grammatical labels (not null)
3. **Frequency-based suppression**: 161 words have rare noun forms suppressed using corpus frequency data
4. **Coverage unchanged**: 61.7% reflects SALDO coverage for specialized/compound words
5. **Verb form handling**: Modal verbs (kan, ska, vill) correctly linked to lemmas

