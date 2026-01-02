"""
Step 2 v3: Extract Headwords and Classify Word Class (Multi-Class Support)
===========================================================================
Stores ALL SALDO entries for each word to enable multi-class inflection extraction.
Key changes from v2:
- Stores all_saldo_entries list for words with multiple POS types
- Adds lemmatization lookup for inflected verb forms (e.g., "kan" -> "kunna")
- Prioritizes primary word class for övrigt display
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, asdict, field
import time
import requests
from urllib.parse import quote

# Configuration
INPUT_FILE = Path("step1_word_entries.json")
SALDO_FILE = Path("saldo_2.3/saldo20v03.txt")
OUTPUT_FILE = Path("step2_classified_entries_v3.json")
REPORT_FILE = Path("step2_classification_report_v3.json")

# SALDO API for lemmatization
SALDO_FL_API = "https://spraakbanken.gu.se/ws/saldo-ws/fl/json/{word}"


@dataclass
class SaldoEntry:
    """A single SALDO lexicon entry."""
    pos: str
    paradigm: str
    lemgram: Optional[str] = None
    baseform: Optional[str] = None
    word_class: Optional[str] = None  # substantiv, verb, adjektiv, övrigt


@dataclass
class WordClassification:
    """Classification result for a word entry with multi-class support."""
    index: int
    ord: str
    glosa: Optional[str]
    primary_word_class: str  # substantiv, verb, adjektiv, övrigt, unknown
    primary_pos_tag: Optional[str]
    primary_paradigm: Optional[str]
    confidence: float
    source: str
    is_compound: bool
    is_placeholder: bool
    all_saldo_entries: List[Dict] = field(default_factory=list)  # NEW: all POS entries
    notes: List[str] = field(default_factory=list)


# POS tag to word class mapping
POS_TO_CLASS = {
    'nn': 'substantiv',
    'nna': 'substantiv',
    'vb': 'verb',
    'av': 'adjektiv',
    'ab': 'övrigt',
    'pp': 'övrigt',
    'kn': 'övrigt',
    'pn': 'övrigt',
    'in': 'övrigt',
    'nl': 'övrigt',
    'pm': 'substantiv',
    'sn': 'övrigt',
    'ie': 'övrigt',
    'hp': 'övrigt',
    'hs': 'övrigt',
    'abh': 'övrigt',
    'pnp': 'övrigt',
}

# POS tags that can have inflections (for primary class selection)
INFLECTABLE_POS = {'nn', 'nna', 'vb', 'av', 'pm'}

# Full names for övrigt POS types
POS_FULL_NAMES = {
    'in': 'interjektion',
    'ab': 'adverb',
    'pp': 'preposition',
    'kn': 'konjunktion',
    'sn': 'subjunktion',
    'pn': 'pronomen',
    'hp': 'interrogativt/relativt pronomen',
    'hs': 'determinativ',
    'nl': 'räkneord',
    'ie': 'infinitivmärke',
}

# Gloss pattern mappings
GLOSS_PATTERNS = {
    r'@num': ('övrigt', 'nl', 0.9),
    r'@tal': ('övrigt', 'nl', 0.9),
    r'@b\b': ('substantiv', 'nn', 0.85),
    r'@en\b': ('substantiv', 'nn', 0.80),
    r'@pt\b': ('substantiv', 'pm', 0.80),
    r'@v\b': ('verb', 'vb', 0.85),
    r'@adj\b': ('adjektiv', 'av', 0.85),
    r'@adv\b': ('övrigt', 'ab', 0.85),
}


def load_saldo_lexicon(filepath: Path) -> Dict[str, List[Dict]]:
    """Load SALDO lexicon into a lookup dictionary."""
    print(f"Loading SALDO lexicon from {filepath}...")
    lexicon = defaultdict(list)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                baseform = parts[4].strip()
                pos = parts[5].strip()
                paradigm = parts[6].strip() if len(parts) > 6 else None
                lemgram = parts[3].strip() if len(parts) > 3 else None
                
                if baseform and pos:
                    word_class = POS_TO_CLASS.get(pos, 'övrigt')
                    entry = {
                        'baseform': baseform,
                        'pos': pos,
                        'paradigm': paradigm,
                        'lemgram': lemgram,
                        'word_class': word_class
                    }
                    lexicon[baseform.lower()].append(entry)
    
    unique_words = len(lexicon)
    total_entries = sum(len(v) for v in lexicon.values())
    print(f"  Loaded {unique_words:,} unique words ({total_entries:,} total entries)")
    
    return lexicon


def normalize_word(word: str) -> str:
    """Normalize word for lookup."""
    word = word.strip()
    word = word.replace('–', '-')
    return word.lower()


def is_placeholder_or_non_lexical(word: str) -> bool:
    """Detect placeholder entries that should not receive inflections."""
    if re.match(r'^\([^)]+\)$', word):
        return True
    if re.match(r'^\d', word):
        return True
    if re.match(r'^[\d\s\-\+x\/]+$', word):
        return True
    if len(word) == 1 and word.lower() not in ['i', 'å', 'ö', 'o']:
        return True
    return False


def lookup_saldo_lemma(word: str) -> Optional[List[Dict]]:
    """
    Use SALDO /fl/ API to find lemma for inflected forms.
    Returns list of {lemma, pos} entries if word is an inflected form.
    """
    try:
        url = SALDO_FL_API.format(word=quote(word, safe=''))
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                results = []
                for item in data:
                    if isinstance(item, dict):
                        lemgram = item.get('lem', '')
                        pos = item.get('pos', '')
                        if lemgram and pos:
                            # Extract lemma from lemgram (e.g., "kunna..vb.1" -> "kunna")
                            lemma = lemgram.split('..')[0]
                            results.append({'lemma': lemma, 'pos': pos, 'lemgram': lemgram})
                return results if results else None
    except Exception as e:
        pass
    return None


def get_all_distinct_pos_entries(entries: List[Dict]) -> List[Dict]:
    """
    Get one entry per distinct POS tag.
    Returns list of entries with unique POS types.
    """
    if not entries:
        return []
    
    by_pos = {}
    for e in entries:
        pos = e['pos']
        if pos not in by_pos:
            by_pos[pos] = e
    
    return list(by_pos.values())


def select_primary_entry(entries: List[Dict], gloss_hint: Optional[str] = None) -> Dict:
    """
    Select the PRIMARY SALDO entry for word class display.
    Priority: vb > av > nn (verbs/adjectives often primary meanings)
    """
    if len(entries) == 1:
        return entries[0]
    
    # Check if gloss hints at word class
    gloss_class = None
    if gloss_hint:
        gloss_lower = gloss_hint.lower()
        if '@v' in gloss_lower or 'verb' in gloss_lower:
            gloss_class = 'vb'
        elif '@adj' in gloss_lower or 'adjektiv' in gloss_lower:
            gloss_class = 'av'
        elif '@b' in gloss_lower or '@en' in gloss_lower:
            gloss_class = 'nn'
    
    if gloss_class:
        matching = [e for e in entries if e['pos'] == gloss_class]
        if matching:
            return matching[0]
    
    # Priority order: vb > av > nn > others
    priority = {'vb': 1, 'av': 2, 'nn': 3, 'nna': 3, 'pm': 4, 'in': 5, 'ab': 5}
    sorted_entries = sorted(entries, key=lambda x: priority.get(x['pos'], 10))
    
    return sorted_entries[0]


def analyze_gloss(glosa: Optional[str]) -> Tuple[Optional[str], Optional[str], float, List[str]]:
    """Analyze gloss field for word class markers."""
    if not glosa:
        return None, None, 0.0, ["No gloss available"]
    
    notes = []
    
    if '^' in glosa:
        notes.append(f"Compound structure: {glosa}")
    
    parens = re.findall(r'\([^)]+\)', glosa)
    if parens:
        notes.append(f"Morphological hints: {parens}")
    
    for pattern, (word_class, pos_tag, confidence) in GLOSS_PATTERNS.items():
        if re.search(pattern, glosa, re.IGNORECASE):
            notes.append(f"Matched pattern: {pattern}")
            return word_class, pos_tag, confidence, notes
    
    if glosa and (glosa.isupper() or (glosa[0].isupper() and '@' not in glosa)):
        if not any(c.isdigit() for c in glosa):
            notes.append("Uppercase pattern suggests proper noun")
            return 'substantiv', 'pm', 0.6, notes
    
    return None, None, 0.0, notes


def classify_word(entry: Dict, lexicon: Dict[str, List[Dict]], 
                  lemma_cache: Dict[str, Optional[List[Dict]]]) -> WordClassification:
    """
    Classify a word with full multi-class support.
    Stores ALL SALDO entries to enable multi-class inflection extraction.
    """
    index = entry['index']
    ord_value = entry['ord']
    glosa = entry.get('glosa')
    
    all_notes = []
    
    # Check for placeholder/non-lexical entries first
    if is_placeholder_or_non_lexical(ord_value):
        all_notes.append(f"Non-lexical entry detected: '{ord_value}'")
        return WordClassification(
            index=index,
            ord=ord_value,
            glosa=glosa,
            primary_word_class='unknown',
            primary_pos_tag=None,
            primary_paradigm=None,
            confidence=0.0,
            source='none',
            is_compound=False,
            is_placeholder=True,
            all_saldo_entries=[],
            notes=all_notes
        )
    
    is_compound = '^' in (glosa or '') or ' ' in ord_value
    
    # Step 1: Analyze gloss
    gloss_class, gloss_pos, gloss_conf, gloss_notes = analyze_gloss(glosa)
    all_notes.extend(gloss_notes)
    
    # Step 2: Direct SALDO lookup
    normalized = normalize_word(ord_value)
    saldo_entries = lexicon.get(normalized)
    
    if not saldo_entries:
        clean = re.sub(r'[^\wåäöÅÄÖ]', '', normalized)
        saldo_entries = lexicon.get(clean)
    
    # Step 3: If no entries or only noun for potential verb form, try lemmatization
    # This fixes "kan" (verb form of "kunna") being classified as noun "khan"
    needs_lemma_lookup = False
    if not saldo_entries:
        needs_lemma_lookup = True
    elif len(saldo_entries) == 1 and saldo_entries[0]['pos'] == 'nn':
        # Single noun entry - might be an inflected verb form
        needs_lemma_lookup = True
    
    if needs_lemma_lookup:
        # Check lemma cache first
        if ord_value.lower() not in lemma_cache:
            lemma_results = lookup_saldo_lemma(ord_value)
            lemma_cache[ord_value.lower()] = lemma_results
        
        lemma_results = lemma_cache.get(ord_value.lower())
        
        if lemma_results:
            for lr in lemma_results:
                lemma = lr['lemma']
                lemma_pos = lr['pos']
                # Look up the lemma in lexicon
                lemma_entries = lexicon.get(lemma.lower())
                if lemma_entries:
                    for le in lemma_entries:
                        if le['pos'] == lemma_pos:
                            # Add this as a valid entry
                            entry_copy = le.copy()
                            entry_copy['is_inflected_form'] = True
                            entry_copy['inflected_form'] = ord_value
                            entry_copy['lemma'] = lemma
                            if saldo_entries is None:
                                saldo_entries = []
                            saldo_entries.append(entry_copy)
                            all_notes.append(f"Lemmatized: '{ord_value}' -> '{lemma}' ({lemma_pos})")
    
    # Step 4: Get all distinct POS entries
    all_distinct_entries = []
    if saldo_entries:
        all_distinct_entries = get_all_distinct_pos_entries(saldo_entries)
    
    # Step 5: Select primary entry and determine classification
    primary_class, primary_pos, primary_paradigm = 'unknown', None, None
    confidence = 0.0
    source = 'none'
    
    if all_distinct_entries:
        primary_entry = select_primary_entry(all_distinct_entries, gloss_hint=glosa)
        primary_pos = primary_entry['pos']
        primary_paradigm = primary_entry['paradigm']
        primary_class = POS_TO_CLASS.get(primary_pos, 'övrigt')
        confidence = 0.9
        source = 'saldo'
        
        pos_types = [e['pos'] for e in all_distinct_entries]
        if len(all_distinct_entries) > 1:
            all_notes.append(f"Multi-class word: {pos_types}")
        else:
            all_notes.append(f"SALDO: {primary_pos} ({primary_paradigm})")
    elif gloss_class:
        primary_class = gloss_class
        primary_pos = gloss_pos
        confidence = gloss_conf
        source = 'gloss'
    else:
        all_notes.append("Could not classify from any source")
    
    # Convert entries to serializable format
    serializable_entries = []
    for e in all_distinct_entries:
        serializable_entries.append({
            'pos': e['pos'],
            'paradigm': e['paradigm'],
            'word_class': e.get('word_class', POS_TO_CLASS.get(e['pos'], 'övrigt')),
            'lemgram': e.get('lemgram'),
            'is_inflected_form': e.get('is_inflected_form', False),
            'lemma': e.get('lemma')
        })
    
    return WordClassification(
        index=index,
        ord=ord_value,
        glosa=glosa,
        primary_word_class=primary_class,
        primary_pos_tag=primary_pos,
        primary_paradigm=primary_paradigm,
        confidence=confidence,
        source=source,
        is_compound=is_compound,
        is_placeholder=False,
        all_saldo_entries=serializable_entries,
        notes=all_notes
    )


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 2 v3: Multi-Class Word Classification")
    print("=" * 60)
    
    # Load SALDO lexicon
    lexicon = load_saldo_lexicon(SALDO_FILE)
    
    # Load word entries from Step 1
    print(f"\nLoading word entries from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} word entries")
    
    # Lemma cache for API calls
    lemma_cache: Dict[str, Optional[List[Dict]]] = {}
    
    # Process entries
    print("\n--- Classifying Words ---")
    start_time = time.time()
    
    classifications = []
    lemma_lookups = 0
    multi_class_count = 0
    
    for i, entry in enumerate(entries):
        cache_size_before = len(lemma_cache)
        result = classify_word(entry, lexicon, lemma_cache)
        classifications.append(result)
        
        if len(lemma_cache) > cache_size_before:
            lemma_lookups += 1
        
        if len(result.all_saldo_entries) > 1:
            multi_class_count += 1
        
        if (i + 1) % 2000 == 0:
            pct = ((i + 1) / len(entries)) * 100
            print(f"  Progress: {i + 1}/{len(entries)} ({pct:.1f}%) - Lemma lookups: {lemma_lookups}")
    
    elapsed = time.time() - start_time
    print(f"\n  Classified {len(classifications)} entries in {elapsed:.1f} seconds")
    print(f"  Lemma API lookups made: {lemma_lookups}")
    print(f"  Multi-class words found: {multi_class_count}")
    
    # Compile statistics
    print("\n--- Classification Statistics ---")
    class_counts = Counter(c.primary_word_class for c in classifications)
    source_counts = Counter(c.source for c in classifications)
    pos_counts = Counter(c.primary_pos_tag for c in classifications if c.primary_pos_tag)
    
    # Count entries by number of word classes
    class_count_distribution = Counter(len(c.all_saldo_entries) for c in classifications)
    
    print("\n  Primary Word Class Distribution:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(classifications)) * 100
        print(f"    {cls}: {count} ({pct:.1f}%)")
    
    print("\n  Multi-Class Distribution:")
    for num_classes, count in sorted(class_count_distribution.items()):
        pct = (count / len(classifications)) * 100
        label = f"{num_classes} class(es)" if num_classes > 0 else "No SALDO entry"
        print(f"    {label}: {count} ({pct:.1f}%)")
    
    print("\n  Classification Source:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(classifications)) * 100
        print(f"    {src}: {count} ({pct:.1f}%)")
    
    # Count potential multi-class words
    multi_class_examples = []
    for c in classifications:
        if len(c.all_saldo_entries) > 1:
            pos_list = [e['pos'] for e in c.all_saldo_entries]
            multi_class_examples.append({'ord': c.ord, 'pos_types': pos_list})
    
    print(f"\n  Sample multi-class words:")
    for ex in multi_class_examples[:10]:
        print(f"    {ex['ord']}: {ex['pos_types']}")
    
    # Placeholder count
    placeholder_count = sum(1 for c in classifications if c.is_placeholder)
    print(f"\n  Placeholder entries: {placeholder_count}")
    
    # Save classifications
    print(f"\n--- Saving Results ---")
    output_data = [asdict(c) for c in classifications]
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Classifications saved to: {OUTPUT_FILE}")
    
    # Save report
    report = {
        "total_entries": len(classifications),
        "processing_time_seconds": elapsed,
        "lemma_api_lookups": lemma_lookups,
        "multi_class_words": multi_class_count,
        "placeholder_entries": placeholder_count,
        "class_distribution": dict(class_counts),
        "source_distribution": dict(source_counts),
        "class_count_distribution": {str(k): v for k, v in class_count_distribution.items()},
        "multi_class_examples": multi_class_examples[:50],
        "sample_classifications": output_data[:30]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 2 v3 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
