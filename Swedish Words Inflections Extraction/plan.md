# Swedish Text Translation & Summary

## Client Request Clarification

The client has provided a Swedish language dataset (Lexikon.json) containing approximately **13,872 word entries** (277,937 lines in the JSON file due to multi-line formatting). They request:

1. **Extract field 0** (the headword) from each entry
2. **Identify and categorize all Swedish grammatical inflections** for each word across four categories:
   - **Substantiv (Nouns)**: singular/plural forms, definite/indefinite forms
   - **Verb**: infinitive, present, past, supine, participle forms
   - **Adjektiv (Adjectives)**: positive, comparative, superlative forms
   - **Övriga ordklasser (Other word classes)**: relevant grammar where applicable
3. **Output format**: Structured JSON with one object per word, showing inflections grouped by word class, with `null` values for inapplicable categories
4. **Critical constraint**: "No guesses or interpretations" means:
   - Do NOT invent words that do not exist in Swedish (prevents hallucinations and grammatical errors)
   - DO use internal linguistic knowledge to generate correct standard inflections for the headword
   - DO apply strict part-of-speech categorization: each word receives inflections only for its actual word class
   - Only set inflections to `null` if word class is ambiguous, rare, or morphologically irregular—not if source data is missing

## Key Discovery

The dataset contains example sentences, variant IDs, and morphological hints in glosses. While explicit inflected forms are sparse in the source file, headwords can be reliably classified by word class (using gloss markers like `@b`, `@num`, `@en`) and processed through **SALDO Web Service** and **Karp-s APIs** (Språkbanken Text) to generate correct standard inflections. These authoritative Swedish linguistic resources provide verified morphological data including lemmatization, inflection generation, and compound decomposition.

---

# Implementation Plan

## Overview

Extract & Categorize Swedish Word Inflections from Lexikon.json

This plan addresses extracting field 0 (headwords) from **~14K entries**, classifying each by word class using gloss markers and Swedish linguistic rules, and generating their standard grammatical inflections using **Språkbanken Text APIs** (SALDO Web Service and Karp-s). The SALDO `/fl/` endpoint provides lemmatization and POS tagging, while `/gen/` generates inflected forms. Confidence thresholds ensure accuracy: high-confidence words receive full API-verified inflections, while rare or irregular words are flagged with `null` to prevent errors.

---

## Step 1: Parse and Validate JSON Structure

**Objective**: Load the file, verify metadata schema, and identify the 3-field format across all **~14K entries**.

**Tasks**:
- Parse Lexikon.json and validate it is a well-formed JSON array
- Extract and verify the metadata object (first element) containing schema definition
- Validate field mapping: `"0:ord"`, `"1:glosa"`, `"2:varianter[id, exempel[m,f,ri], relaterade[m,f,ri]]"`
- Iterate through all entries to confirm each follows `[ord, glosa, varianter_array]` structure
- Log any structural anomalies or malformed entries
- **Count total word entries** (excluding metadata object)

**Deliverable**: Validated entry count and schema confirmation report

**Complexity**: Low - straightforward JSON parsing with validation

---

## Step 2: Extract Field 0 (Headwords) and Classify Word Class

**Objective**: Parse all headwords and classify by word class using gloss markers, Swedish linguistic rules, and **SALDO API validation**. Apply **strict part-of-speech categorization** to ensure each word is only given inflections for its actual word class.

**Tasks**:
- Extract field 0 from each entry
- **Primary classification**: Analyze gloss field (field 1) for morphological markers:
  - `@num` → Numerals (special class)
  - `@b` → Substantiv (common noun marker)
  - `@en` → Proper nouns/English words
  - `^` separator → Compounds (e.g., `AFFÄR^MAN` = "affärsman")
  - Parenthetical notations: `LAG(L)`, `LAG(S)` → morphological hints
  - `@v` or similar patterns → potential verb markers
- **API validation**: For ambiguous or unmarked entries, call `GET /ws/saldo-ws/fl/json/{headword}` to:
  - Retrieve authoritative POS tags (`pos` field: `nn` for nouns, `vb` for verbs, `av` for adjectives, etc.)
  - Get lemma forms and SALDO identifiers for further processing
  - Disambiguate homographs (e.g., "plan" as noun vs. adjective)
- Handle null glosses: Use API as fallback; mark as `unknown_class` with Low confidence if API returns no results
- Establish classification confidence levels:
  - **High (≥80%)**: Gloss marker + API confirmation match
  - **Medium (50-79%)**: Only gloss marker or only API result
  - **Low (<50%)**: Ambiguous results from both sources
- Create lookup tables for each word class
- **Strict categorization enforcement**: A word receives inflections ONLY for its actual word class per API response

**API Integration Details**:
- **Base URL**: `https://spraakbanken.gu.se/ws/saldo-ws/`
- **Endpoint**: `/fl/json/{wordform}`
- **Response parsing**: Extract `pos`, `lem` (lemma), and `id` (SALDO identifier) fields
- **Rate limiting**: Max 10 requests/second; implement batching for large volumes
- **Caching strategy**: Cache API responses to avoid duplicate calls for same headwords

**Deliverable**: Classification index mapping headword → word_class with confidence scores + SALDO identifiers

**Complexity**: Medium - requires pattern matching, API integration, and response parsing

---

## Step 3: Conduct Feasibility Audit on Example Data

**Objective**: Determine what actual inflection data exists in examples and variant references; identify retrieval success rates by word class.

**Tasks**:
- Sample 500+ entries stratified by word class (nouns, verbs, adjectives, other)
- For each sample:
  - Count variant entries per headword
  - Analyze example sentences for linguistic patterns indicating inflected forms
  - Check related entry IDs (third field in examples) - do they point to inflected variants?
  - Look for marked forms in gloss parentheticals
- Document:
  - % of entries with explicit plural forms
  - % of entries with verb conjugations
  - % of entries with adjective comparative/superlative forms
  - % of entries with no inflection data
- Identify patterns in variant ID codes that might correlate with inflection type

**Deliverable**: Feasibility audit report with extraction success rates and patterns

**Complexity**: Medium - requires systematic sampling and pattern analysis

---

## Step 4: Design Morphological Data Generation Logic

**Objective**: Define rules for generating correct standard Swedish inflections using **SALDO Web Service API** based on word class. Apply confidence thresholds to flag rare or irregular forms that should not be generated.

**API Integration Architecture**:
- **Primary API**: SALDO Web Service (`https://spraakbanken.gu.se/ws/saldo-ws/`)
- **Fallback**: Karp-s API for lexical queries (`https://ws.spraakbanken.gu.se/ws/karps/v1/`)
- **Strategy**: Two-stage approach
  1. **Lemmatization & POS confirmation** via `/fl/json/{wordform}` (already done in Step 2)
  2. **Inflection generation** via `/gen/json/{paradigm}/{baseform}`

**Tasks**:

### For Substantiv (Nouns):
- **High Confidence Nouns (≥80%)**: Use SALDO API to generate all four forms
  - **API Call**: `GET /ws/saldo-ws/gen/json/{paradigm}/{baseform}`
  - **Process**:
    1. Extract `paradigm` from Step 2's `/fl/` response (e.g., `nn_2u_cykel`)
    2. Use headword as `baseform`
    3. Parse API response to extract: `singular`, `plural`, `bestämd_singular`, `bestämd_plural`
  - **Example**: "bil" → API returns `{singular: "bil", plural: "bilar", bestämd_singular: "bilen", bestämd_plural: "bilarna"}`
- **Validation strategy**: 
  - Verify paradigm exists in API response
  - Cross-reference with gloss markers (`@b`)
  - Check variant IDs and example sentences for confirmation
- **Low Confidence/Irregular (<80%)**: If API returns error, incomplete data, or paradigm is ambiguous → set all fields to `null` with confidence annotation
- **Compound handling**: Use `/sms/json/{wordform}` endpoint to decompose compounds before inflection (e.g., "affärsman" → "affär" + "man")
- **Output composition**: Inflection object with fields: `singular`, `plural`, `bestämd_singular`, `bestämd_plural`

### For Verb:
- **High Confidence Verbs (≥80%)**: Use SALDO API to generate all five forms
  - **API Call**: `GET /ws/saldo-ws/gen/json/{paradigm}/{baseform}`
  - **Process**:
    1. Extract verb `paradigm` from Step 2's `/fl/` response (e.g., `vb_1a_prata`)
    2. Use infinitive form as `baseform`
    3. Parse API response to extract: `infinitiv`, `presens`, `preteritum`, `supinum`, `particip`
  - **Example**: "tala" → API returns `{infinitiv: "tala", presens: "talar", preteritum: "talade", supinum: "talat", particip: "talande"}`
- **Validation strategy**: 
  - Confirm POS tag is `vb` from `/fl/` endpoint
  - Check for verb markers in gloss (`@v` or context)
  - Verify all five forms are present in API response
- **Low Confidence/Irregular (<80%)**: If verb is irregular (API may return incomplete conjugation), defective, or paradigm is ambiguous → set all fields to `null` with confidence annotation
- **Output composition**: Inflection object with fields: `infinitiv`, `presens`, `preteritum`, `supinum`, `particip`

### For Adjektiv (Adjectives):
- **High Confidence Adjectives (≥80%)**: Use SALDO API to generate all three degrees
  - **API Call**: `GET /ws/saldo-ws/gen/json/{paradigm}/{baseform}`
  - **Process**:
    1. Extract adjective `paradigm` from Step 2's `/fl/` response (e.g., `av_1_god`)
    2. Use positive form as `baseform`
    3. Parse API response to extract: `positiv`, `komparativ`, `superlativ`
  - **Example**: "glad" → API returns `{positiv: "glad", komparativ: "gladare", superlativ: "gladast"}`
- **Validation strategy**: 
  - Confirm POS tag is `av` from `/fl/` endpoint
  - Identify adjectives via gloss context and example usage
  - Handle irregular comparatives (e.g., "bra" → "bättre" → "bäst")
- **Low Confidence/Irregular (<80%)**: If adjective is participial, rare, or API returns incomplete data → set all fields to `null` with confidence annotation
- **Output composition**: Inflection object with fields: `positiv`, `komparativ`, `superlativ`

### For Övriga Ordklasser (Other Classes):
- **Classify remaining words**: Pronouns, adverbs, prepositions, conjunctions, interjections, numerals
- **API strategy**: 
  - Use `/fl/` endpoint to get POS tags (`ab` for adverbs, etc.)
  - Most of these classes don't inflect; document grammatical properties instead
- **Low Confidence default**: For ambiguous or rare words, set to `null` rather than generate uncertain forms
- **Output composition**: String describing relevant grammar (e.g., "adverb - no inflections") or `null`

### Confidence Thresholds (Strict Enforcement):
- **High Confidence (≥80%)**: 
  - Gloss marker matches API POS tag
  - API returns complete paradigm with all expected forms
  - No API errors or ambiguities
  - → Apply full inflection generation
- **Medium Confidence (50-79%)**: 
  - API returns partial data (e.g., missing one inflection form)
  - Slight mismatch between gloss and API
  - → Flag with confidence score; include generated forms with warning
- **Low Confidence (<50%)**: 
  - API returns error (404, timeout, malformed response)
  - Multiple ambiguous paradigms
  - Rare/archaic word not in SALDO
  - → Set all inflections to `null`; log reason

### API Error Handling:
- **404 Not Found**: Word not in SALDO → mark as Low confidence, set to `null`
- **Timeout/Network Error**: Retry up to 3 times with exponential backoff; if still fails → mark for manual review
- **Rate Limit (429)**: Implement queue system; wait and retry
- **Malformed Response**: Log error, set to `null`, flag entry

### Caching Strategy:
- **Cache all API responses** (both `/fl/` and `/gen/`) in local key-value store
- **Cache key**: `{endpoint}_{wordform}_{paradigm}`
- **Cache hit rate target**: 40-60% (many words will be unique, but common words repeat)
- **Reduces API load**: From 14K calls to ~8-9K actual API requests

**Deliverable**: Morphological generation implementation with SALDO API integration, error handling, caching, and confidence scoring

**Complexity**: High - requires API integration, response parsing, error handling, and retry logic

---

## Step 5: Implement Output JSON Schema Validation

**Objective**: Enforce strict schema compliance to ensure output is well-formed and exactly one word-class object is populated per entry (except for genuinely ambiguous entries).

**Tasks**:
- Define target JSON schema based on provided examples:
  ```
  {
    "ord": "word_string",
    "substantiv": {
      "singular": "form|null",
      "plural": "form|null",
      "bestämd_singular": "form|null",
      "bestämd_plural": "form|null"
    } | null,
    "verb": {
      "infinitiv": "form|null",
      "presens": "form|null",
      "preteritum": "form|null",
      "supinum": "form|null",
      "particip": "form|null"
    } | null,
    "adjektiv": {
      "positiv": "form|null",
      "komparativ": "form|null",
      "superlativ": "form|null"
    } | null,
    "övrigt": "string|null"
  }
  ```
- **Strict enforcement**: Exactly one of {substantiv, verb, adjektiv, övrigt} must be non-null per entry (all others must be `null`)
  - Exception: Only allow all categories `null` for genuinely ambiguous words with low confidence
- For each entry, validate against schema before output
- Ensure all inflection fields within populated categories are either valid strings or `null` (no empty strings, numbers, or arrays)
- Log validation errors with entry index and specific violations
- Only include entries that pass validation in output dataset

**Deliverable**: Validated output JSON with schema compliance report (% entries passing, validation errors by type)

**Complexity**: Medium - schema validation and enforcement

---

## Step 6: Address "No Guesses" Constraint & Error Handling

**Objective**: Ensure strict adherence to "no guesses" (meaning: prevent hallucinations and grammatical errors while using linguistic knowledge). Maintain data integrity through confidence thresholds and comprehensive error documentation.

**Tasks**:

### Confidence Thresholds (Strict Application):
- **High confidence (≥80%)**: Correct standard Swedish inflection from SALDO API with clear word class → output full inflection forms
- **Medium confidence (50-79%)**: Generated forms are plausible but API returns partial data or word class has some ambiguity → include in output but annotate confidence score for user review
- **Low confidence (<50%)**: Word is rare (not in SALDO), API error occurs, or word class is ambiguous → set all inflections to `null` to prevent errors; do not attempt generation

### API Error Handling:
- **SALDO API Errors**:
  - **404 Not Found**: Word not in SALDO database → mark as Low confidence, set to `null`, log with reason
  - **Timeout (>5s)**: Retry up to 3 times with exponential backoff (1s, 2s, 4s); if still fails → mark for manual review
  - **429 Rate Limit**: Implement queue with delay; respect rate limiting (~10 req/sec)
  - **500 Server Error**: Retry once; if persists → mark as Low confidence, set to `null`
  - **Network errors**: Catch connection errors, retry 3 times, then mark for offline processing
- **Malformed API Response**: 
  - Log full response for debugging
  - Attempt to parse partial data if possible
  - If unparseable → set to `null`, flag entry
- **Incomplete API Data**: 
  - If API returns some but not all inflection forms (e.g., only singular but no plural)
  - Mark as Medium confidence
  - Include available forms, set missing forms to `null`
  - Annotate with "partial_api_data" flag

### Handling Missing Data:
- For each word, track which inflection fields could not be populated
- Create "extraction report" per entry documenting:
  - Which fields were found vs. not found
  - Confidence score for each populated field
  - Reason for null values (not found in data vs. not applicable to word class)

### Error Handling Strategy:
- **Malformed entries**: Skip with detailed error log (line number, entry structure)
- **Null glosses**: Classify as `unknown_class`; set all inflection categories to `null`; flag for manual review
- **Ambiguous classifications**: Create `ambiguous_entries.json` for manual validation
- **Placeholder text entries**: Skip with note (e.g., "Översättning kommer...")

### Quality Assurance:
- Generate summary statistics:
  - Total entries processed
  - % successfully classified by word class
  - % with at least one inflection extracted
  - % with all categories as null
  - % with errors/flags
- Create "confidence distribution" histogram

**Deliverable**: Output JSON + extraction_report.json + quality_metrics.json + error_log.json

**Complexity**: High - requires systematic error tracking and reporting

---

## Critical Decision Points

### 1. Data Completeness & Generation Strategy (DECIDED: Option B with SALDO API)

**Decision**: **ADOPT OPTION B** – Use **SALDO Web Service and Karp-s APIs** (Språkbanken Text) to generate correct standard Swedish inflections.

**Rationale**:
- "No guesses" constraint clarified: Prevent hallucinations and grammatical errors (do not invent non-existent words), not limit to literal file extraction
- SALDO is the authoritative Swedish morphological lexicon maintained by Språkbanken Text (University of Gothenburg)
- API-based approach provides verified inflections from linguistic research rather than rule-based generation
- Confidence thresholds ensure accuracy: only apply API results to high-confidence standard words; flag or null when API returns errors/incomplete data

**Approach**:
- **Headword classification**: Use gloss markers + SALDO `/fl/` endpoint to determine word class with authoritative POS tags
- **Inflection generation**: Use SALDO `/gen/` endpoint with paradigm information to generate correct inflections
- **Compound handling**: Use SALDO `/sms/` endpoint to decompose compounds before processing
- **Error prevention**: Apply confidence thresholds rigorously; set to `null` for API errors, ambiguous results, or words not in SALDO
- **Validation**: All generated forms come from SALDO database (no invented forms)

**API Details**:
- **Base URL**: `https://spraakbanken.gu.se/ws/saldo-ws/`
- **Authentication**: No API key required (public endpoints)
- **Rate Limiting**: ~10 requests/second recommended
- **Caching**: Implement local caching to reduce API calls by 40-60%

**Result**: Complete inflection coverage for ~85-95% of entries; high data quality from authoritative source; transparent confidence annotation

**Success**: Combines linguistic authority with completeness while respecting the intent of "no guesses" (prevent errors, use verified data source)

---

### 2. Variant ID Interpretation

**Issue**: Unclear whether variant IDs represent inflected forms or different word senses.

**Investigation Required**:
- Sample 100 entries with 3+ variants
- Manually review whether variants are morphological or semantic in nature
- Establish if variant ID patterns correlate with inflection type
- Document findings before implementing extraction logic

**Impact**: Directly affects Rules for Substantiv/Verb/Adjektiv extraction

---

### 3. Word Class Confidence Threshold

**Issue**: Gloss markers are not always explicit; confidence in word class classification varies.

**Decision Required**:
- Should output include words with medium (50-79%) or only high (≥80%) confidence?
- Should ambiguous entries be excluded or included with confidence annotation?

**Recommendation**: Include all entries but annotate confidence; user can filter post-processing.

---

## Resource & Complexity Estimates

| Phase | Estimated Effort | Complexity | Dependencies |
|-------|------------------|-----------|--------------|
| Step 1: Parse & Validate | 2-4 hours | Low | None |
| Step 2: Extract & Classify + API Integration | 6-10 hours | Medium-High | Step 1, SALDO API |
| Step 3: Feasibility Audit | 4-8 hours | Medium | Step 2 |
| Step 4: Design Logic + API Integration | 8-16 hours | High | Step 3, SALDO API |
| Step 5: Implement Schema | 4-8 hours | Medium | Step 4 |
| Step 6: Error Handling + API Retry Logic | 6-10 hours | High | Steps 4-5 |
| **Total** | **30-56 hours** | **High** | Sequential |

### Processing Performance (with API Integration)
- **Input size**: 13,872 word entries (~14K)
- **API calls required**: 
  - Step 2: ~14K `/fl/` calls (with ~40% cache hit rate after initial processing) = ~8.4K actual calls
  - Step 4: ~14K `/gen/` calls (with similar cache rate) = ~8.4K actual calls
  - **Total**: ~16.8K API calls
- **API rate limit**: ~10 requests/second
- **Sequential processing time**: 16,800 / 10 = 1,680 seconds ≈ **28 minutes**
- **With parallelization (5 concurrent workers)**: ~5-6 minutes
- **With aggressive caching + batching (10 workers)**: ~3-4 minutes
- **Output file size**: ~5-15 MB (JSON + reports)

### Storage Requirements
- **Input**: ~13 MB (Lexikon.json)
- **Output datasets**: ~5-15 MB
- **API response cache**: ~10-25 MB (JSON cache of all API responses)
- **Intermediate files**: ~2-5 MB (reports, logs)
- **Total**: ~30-60 MB

### Network & API Requirements
- **Bandwidth**: Minimal (~10-20 KB per API request, ~350-500 MB total)
- **API availability**: Requires stable internet connection; implement offline fallback
- **Authentication**: None required (public API)

---

## Potential Challenges & Mitigation

| Challenge | Risk | Mitigation |
|-----------|------|-----------|
| **SALDO API availability/reliability** | High | Implement robust retry logic; cache all responses; consider downloading SALDO dataset for offline processing if API is unstable |
| **API rate limiting (429 errors)** | High | Respect 10 req/sec limit; implement queue system; use exponential backoff; consider parallel workers with coordination |
| **Words not in SALDO database** | Medium | Expected for rare/archaic words; set to `null` with confidence annotation; track % not found for reporting |
| **API timeout/network errors** | Medium | Retry mechanism (3 attempts); implement fallback queue for offline retry; monitor network stability |
| **Ambiguous gloss markers** | Medium | Use SALDO `/fl/` endpoint as authoritative source; flag mismatches between gloss and API for manual review |
| **Performance with 14K API calls** | Medium | Implement aggressive caching (40-60% hit rate); use concurrent workers (5-10); batch requests where possible; estimated 3-6 minutes with optimization |
| **Incomplete API responses** | Medium | Handle partial data gracefully; mark as Medium confidence; include available inflections, null missing ones |
| **Variant ID interpretation** | Medium | Use SALDO data as primary source; document any conflicts with Lexikon.json internal data |
| **Compound word handling** | Medium | Use SALDO `/sms/` endpoint for decomposition; handle compounds that fail decomposition |
| **Swedish morphological exceptions** | Low | SALDO handles irregular forms; trust API data; document any edge cases in logs |
| **Schema compliance validation** | Low | Automated validation; comprehensive test cases |
| **API response parsing errors** | Medium | Robust JSON parsing with error handling; log malformed responses; skip and flag problematic entries |

---

## Success Criteria

- ✓ All ~14K entries parsed without errors
- ✓ Word class classification accuracy ≥85% (validated on sample; uses gloss markers + SALDO API POS tags)
- ✓ Output JSON conforms to specified schema 100% (exactly one word-class category is non-null per entry, or all null for ambiguous words)
- ✓ All inflection fields are either valid Swedish words from SALDO API or explicitly `null` (no invented forms)
- ✓ No guesses enforcement: All generated inflections come from authoritative SALDO database; rare/irregular words or API errors flagged or nulled
- ✓ Confidence thresholds applied: High-confidence words receive full API-verified inflections; medium-confidence annotated; low-confidence nulled
- ✓ Strict part-of-speech categorization: Each word receives inflections only for its actual word class per SALDO API
- ✓ API integration successful: ≥85% API call success rate; proper error handling for timeouts, 404s, rate limits
- ✓ Caching implemented: 40-60% cache hit rate achieved; reduces API load significantly
- ✓ Comprehensive error log and quality metrics generated (including API error statistics)
- ✓ Processing completes in 3-6 minutes (with parallel workers and caching)
- ✓ Output transparency: confidence scores, API response status, and validation notes included
- ✓ Option B with SALDO API adopted: Uses authoritative Swedish linguistic resource with rigorous error handling
