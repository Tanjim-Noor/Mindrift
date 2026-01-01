# Swedish Lexical & Morphological API Guide: Karp-s and SALDO

This guide provides a technical overview and integration strategies for two primary Swedish language APIs provided by Språkbanken Text: **Karp-s** and the **SALDO Web Service**. These tools are essential for developers looking to enhance Large Language Models (LLMs) with structured Swedish linguistic data.

---

### 1. Architectural Overview

To build robust Swedish NLP applications, it is critical to understand the distinct yet complementary roles of these two systems:

*   **Karp-s (Lexical Search Engine):** Acts as the structured "Search Engine" for Språkbanken's vast collection of Swedish lexicons (e.g., SALDO, SAOL, SO). It is optimized for querying entries based on complex filters, retrieving metadata, and exploring the relationships between different lexical resources.
*   **SALDO Web Service (Morphological Engine):** Serves as the "Morphological Engine" focused on word-level analysis. It handles the "mechanics" of the language—inflections, compound decomposition, and lemmatization.
*   **SALDO as the "Pivot":** SALDO (Swedish Associative Lexicon) is the central resource in this ecosystem. Most other lexicons in Karp-s use SALDO identifiers (lemgrams and sense IDs) as a "pivot" to link data across different resources, making it the backbone of Swedish lexical integration.

---

### 2. Endpoint Dictionary: Karp-s (Lexical Search)

Karp-s provides a powerful Query DSL to search across multiple Swedish lexicons simultaneously.

#### Key Endpoints
*   **Search:** `GET /query/{resources}?q={query}`
    *   Returns a list of entries matching the query.
    *   `resources`: Comma-separated list of resource IDs (e.g., `saldo,saol`).
*   **Statistics:** `GET /query/stats/{resources}?q={query}`
    *   Returns the count of matches per resource without the full entry data.
*   **Entry Lookup:** `GET /query/entries/{resource_id}/{entry_ids}`
    *   Retrieves specific entries by their unique identifiers.

#### Query Syntax (DSL)
Queries are passed via the `q` parameter using a pipe-separated operator syntax:
*   `equals|<field>|<string>`: Exact match (e.g., `equals|wf|bil`).
*   `contains|<field>|<string>`: Substring match.
*   `startswith|<field>|<string>`: Prefix match.
*   **Logical Operators:** `and(expr1||expr2)`, `or(expr1||expr2)`, `not(expr)`.

#### Identifying Word Classes
In the response schema, word classes (Part-of-Speech) are typically found in the `pos` or `ud_pos` fields. Common tags include:
*   `nn`: Noun (*Substantiv*)
*   `vb`: Verb (*Verb*)
*   `av`: Adjective (*Adjektiv*)
*   `ab`: Adverb (*Adverb*)

---

### 3. Endpoint Dictionary: SALDO Web Service (Morphology)

The SALDO Web Service provides specialized endpoints for morphological processing. All endpoints support `{format}` as `json`, `xml`, or `html`.

#### Primary Endpoints
*   **Fullform Lookup (`/fl/{format}/{wordform}`):**
    *   Finds the base forms (lemmas), part-of-speech tags, and semantic identifiers for a given inflected word form.
*   **Compound Analysis (`/sms/{format}/{wordform}`):**
    *   Decomposes Swedish compound words into their constituent parts. 
    *   *Note: Check current availability as some versions may be in transition.*
*   **Inflection Engine (`/gen/{format}/{paradigm}/{baseform}`):**
    *   Generates all inflected forms of a word based on a specific paradigm (inflectional pattern).
*   **Lemma-ID Lookup (`/lid/{format}/{lemma-id}`):**
    *   Retrieves detailed information about a specific lemma (e.g., `bil..nn.1`).

---

### 4. Integration Recipes for LLMs

#### Recipe A: Syntactic Tagging (Disambiguation)
**Use Case:** Distinguishing ambiguous words like "plan" (can be a noun "plane/plan" or an adjective "flat").
1.  **Call:** `GET /ws/saldo-ws/fl/json/plan`
2.  **Analyze:** The response returns multiple entries: one with `pos: "nn"` and another with `pos: "av"`.
3.  **LLM Prompting:** Inject these tags into the LLM context:
    > "The word 'plan' in this sentence is identified by the lexicon as either a Noun (nn) or Adjective (av). Based on the context, which one is it?"

#### Recipe B: Compound Decomposition
**Use Case:** Processing long compounds like "fastighetsskötare" (property caretaker).
1.  **Call:** `GET /ws/saldo-ws/sms/json/fastighetsskötare`
2.  **Analyze:** The service returns the components: `fastighet` (property) + `skötare` (caretaker).
3.  **LLM Workflow:** Pre-process text to split unknown or long compounds, allowing the LLM to perform semantic analysis on the individual roots, which is especially helpful for RAG systems.

#### Recipe C: Base-Form Normalization (Lemmatization)
**Use Case:** Improving retrieval in Vector Databases/RAG by indexing base forms.
1.  **Call:** `GET /ws/saldo-ws/fl/json/{word}` for every token in the document.
2.  **Extract:** Take the `lem` (lemma) field from the response.
3.  **Index:** Store the lemmatized version of the text in your Vector Database. This ensures that a search for "bilar" (cars) correctly matches documents containing "bil" (car).

---

### 5. Developer Quick-Start

#### Authentication Policy
*   **No API Key Required:** Public endpoints are open for research and development.
*   **Base URL (SALDO):** `https://spraakbanken.gu.se/ws/saldo-ws/`
*   **Base URL (Karp-s):** `https://ws.spraakbanken.gu.se/ws/karps/v1/`

#### "Good Citizen" Guidelines
*   **Rate Limiting:** Avoid aggressive multi-threading. Limit requests to ~10 per second.
*   **Batching:** For large-scale processing, consider downloading the source datasets (SALDO/Lexikon) for local use instead of hitting the API.

#### Sample cURL Command
To look up the word "springa" (to run/a crack):
```bash
curl -X GET "https://spraakbanken.gu.se/ws/saldo-ws/fl/json/springa"
```

---

### Technical Glossary
*   **Lemgram:** A unique identifier for a word sense and its inflectional category (e.g., `bord..nn.1`).
*   **Paradigm:** A template or rule-set defining how a word inflects (e.g., how a noun changes from singular to plural).
*   **Descriptor:** A brief semantic hint used to distinguish between different senses of the same word.
