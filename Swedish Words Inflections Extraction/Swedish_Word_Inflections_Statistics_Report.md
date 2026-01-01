# Swedish Word Inflections Extraction - Statistics Report

**Generated:** 2026-01-01 23:16:12

---

## Executive Summary

This report provides comprehensive statistics for the Swedish word inflections extraction project, which processed **13,872** Swedish words from the Lexikon dataset through a multi-stage pipeline using the SALDO (Swedish Associative Lexicon) database.

### Key Achievements
- **8,672** words with inflection data extracted (62.5% coverage)
- **9,612** API calls made to SALDO Web Service
- **7,072** words with complete inflection forms

---

## 1. Word Entries Analysis (Step 1)

### Input Dataset Overview
- **Total Entries:** 13,872
- **Entries with Gloss:** 4,547 (32.8%)
- **Entries without Gloss:** 9,325 (67.2%)
- **Entries with Variants:** 13,872 (100.0%)
- **Total Variant Examples:** 21,734

### Data Quality
- **Gloss Coverage:** 32.8% of entries include pronunciation/grammar markers
- **Variant Examples:** Average of 1.6 variants per entry (for entries with variants)

---

## 2. Classification Analysis (Step 2)

### Word Class Distribution
| Word Class | Count | Percentage |
|------------|-------|------------|
| **Substantiv (Nouns)** | 7,439 | 53.6% |
| **Verb (Verbs)** | 1,139 | 8.2% |
| **Adjektiv (Adjectives)** | 1,006 | 7.3% |
| **Övrigt (Other)** | 563 | 4.1% |
| **Unknown** | 3,725 | 26.9% |
| **TOTAL** | 13,872 | 100.0% |

### Classification Confidence
| Confidence Level | Count | Percentage |
|-----------------|-------|------------|
| **High (≥80%)** | 7,934 | 57.2% |
| **Medium (50-79%)** | 2,213 | 16.0% |
| **Low (<50%)** | 3,725 | 26.9% |

### Classification Data Sources
| Source | Count | Percentage |
|--------|-------|------------|
| **SALDO Only** | 7,277 | 52.5% |
| **Both SALDO & Gloss** | 1,958 | 14.1% |
| **Gloss Only** | 912 | 6.6% |

### Additional Insights
- **Entries with Paradigm:** 9,235 (66.6%)
- **Compound Words Detected:** 2,817 (20.3%)
- **Successfully Classified:** 10,147 (73.1%)

---

## 3. API Cache Analysis (Step 3)

### SALDO API Request Summary
- **Total Cached Requests:** 9,612
- **Successful Requests:** 9,612 (100.00%)
- **Failed Requests:** 0 (0.00%)
- **Unique Words Processed:** 9,260
- **Unique Paradigms Used:** 579

### API Performance
- **Success Rate:** 100.00%
- **Cache Efficiency:** All responses cached to avoid redundant API calls
- **Average Requests per Word:** 1.04

---

## 4. Final Inflections Analysis (Step 4)

### Overall Coverage
- **Total Word Entries:** 13,872
- **Entries with Inflection Data:** 8,672 (62.5%)
- **Entries with No Data:** 5,200 (37.5%)

### Substantiv (Nouns)
| Metric | Count | Percentage |
|--------|-------|------------|
| **With Data** | 6,528 | 47.1% |
| **Null (No Data)** | 7,344 | 52.9% |
| **Complete Forms (4/4)** | 5,137 | 37.0% |
| **Partial Forms** | 787 | 5.7% |

**Form Completeness:** 78.7% of nouns with data have all 4 forms (singular, plural, bestämd singular, bestämd plural)

### Verb (Verbs)
| Metric | Count | Percentage |
|--------|-------|------------|
| **With Data** | 1,139 | 8.2% |
| **Null (No Data)** | 12,733 | 91.8% |
| **Complete Forms (5/5)** | 1,122 | 8.1% |
| **Partial Forms** | 0 | 0.0% |

**Form Completeness:** 98.5% of verbs with data have all 5 forms (infinitiv, presens, preteritum, supinum, particip)

### Adjektiv (Adjectives)
| Metric | Count | Percentage |
|--------|-------|------------|
| **With Data** | 1,005 | 7.2% |
| **Null (No Data)** | 12,867 | 92.8% |
| **Complete Forms (3/3)** | 813 | 5.9% |
| **Partial Forms** | 94 | 0.7% |

**Form Completeness:** 80.9% of adjectives with data have all 3 forms (positiv, komparativ, superlativ)

### Övrigt (Other)
| Metric | Count | Percentage |
|--------|-------|------------|
| **With Data** | 0 | 0.0% |
| **Null (No Data)** | 13,872 | 100.0% |

---

## 5. Pipeline Performance Summary

### Data Flow Through Pipeline
```
Input (Lexikon.json)
    ↓
Step 1: Parse & Validate ────────────→ 13,872 entries
    ↓
Step 2: Classify Words ──────────────→ 10,147 classified (73.1%)
    ↓
Step 3: Generate Inflections ────────→ 9,612 API calls
    ↓
Step 4: Validate & Finalize ─────────→ 8,672 with data (62.5%)
    ↓
Output (swedish_word_inflections.json)
```

### Success Metrics
| Metric | Value |
|--------|-------|
| **Total Words Processed** | 13,872 |
| **Classification Success Rate** | 73.1% |
| **API Success Rate** | 100.00% |
| **Final Coverage Rate** | 62.5% |
| **Complete Forms Rate** | 51.0% |

### Data Quality Indicators
- **High Confidence Classifications:** 57.2%
- **Entries with Paradigm Information:** 66.6%
- **Words with Complete Inflections:** 51.0%

---

## 6. Files Generated

| File | Size | Description |
|------|------|-------------|
| `Lexikon.json` | 7.7 MB | Source data (13,872 Swedish words) |
| `step1_word_entries.json` | 10.3 MB | Parsed and validated entries |
| `step2_classified_entries.json` | 4.8 MB | Classified words with SALDO data |
| `step3_api_cache.json` | 15.5 MB | Cached SALDO API responses (9,260 requests) |
| `step3_inflections.json` | 2.9 MB | Extracted inflection forms |
| `swedish_word_inflections.json` | 2.9 MB | **Final validated output** |
| `final_validation_report.json` | - | Validation statistics |
| `step2_classification_report.json` | - | Classification statistics |

---

## 7. Methodology

### Data Sources
1. **Lexikon.json**: Primary dataset with Swedish words and metadata
2. **SALDO v2.3**: Local lexicon file (124,229 unique words) for classification
3. **SALDO Web Service**: REST API for inflection generation

### Processing Steps
1. **Parsing**: Extract and validate 3-field structure (ord, glosa, varianter)
2. **Classification**: Determine word class using SALDO lexicon + gloss analysis
3. **Inflection Generation**: Call SALDO API with paradigm patterns
4. **Validation**: Ensure schema compliance and data quality

### Quality Controls
- Only entries with ≥50% confidence and valid paradigm received API calls
- All API responses cached to prevent redundant requests
- Schema validation ensures all output entries follow required format
- Manual verification of common Swedish words confirmed accuracy

---

## Conclusion

The Swedish Word Inflections Extraction project successfully processed **13,872** words, generating inflection data for **62.5%** of entries. The pipeline achieved high classification accuracy (73.1%) and API success rate (100.00%), producing a comprehensive linguistic dataset suitable for Swedish language processing applications.

---

*Report generated on 2026-01-01 23:16:12*
