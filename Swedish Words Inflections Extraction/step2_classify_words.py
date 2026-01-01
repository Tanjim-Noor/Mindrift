"""
Step 2: Extract Headwords and Classify Word Class (Local SALDO)
================================================================
Uses the local SALDO 2.3 dataset file for efficient word classification
instead of API calls. Falls back to pattern-based classification for
words not in SALDO.
"""

import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple, Set
from dataclasses import dataclass, asdict
import time

# Configuration
INPUT_FILE = Path("step1_word_entries.json")
SALDO_FILE = Path("saldo_2.3/saldo20v03.txt")
OUTPUT_FILE = Path("step2_classified_entries.json")
REPORT_FILE = Path("step2_classification_report.json")


@dataclass
class WordClassification:
    """Classification result for a word entry."""
    index: int
    ord: str
    glosa: Optional[str]
    word_class: str  # substantiv, verb, adjektiv, övrigt, unknown
    pos_tag: Optional[str]  # SALDO POS tag (nn, vb, av, ab, etc.)
    confidence: float  # 0.0 to 1.0
    source: str  # saldo, gloss, both, none
    paradigm: Optional[str]
    is_compound: bool
    notes: List[str]


# POS tag to word class mapping
POS_TO_CLASS = {
    'nn': 'substantiv',
    'nna': 'substantiv',  # noun abbreviation
    'vb': 'verb',
    'av': 'adjektiv',
    'ab': 'övrigt',  # adverb
    'pp': 'övrigt',  # preposition
    'kn': 'övrigt',  # conjunction
    'pn': 'övrigt',  # pronoun
    'in': 'övrigt',  # interjection
    'nl': 'övrigt',  # numeral
    'pm': 'substantiv',  # proper noun (treat as substantiv for inflection purposes)
    'sn': 'övrigt',  # subordinating conjunction
    'ie': 'övrigt',  # infinitive marker
    'hp': 'övrigt',  # pronoun (interrogative/relative)
    'hs': 'övrigt',  # determiner (interrogative/relative)
    'abh': 'övrigt',  # adverb head
    'pnp': 'övrigt',  # possessive pronoun
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
    """
    Load SALDO lexicon into a lookup dictionary.
    Returns dict mapping base form (lowercase) to list of entries.
    """
    print(f"Loading SALDO lexicon from {filepath}...")
    lexicon = defaultdict(list)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                # Format: sense_id, parent1, parent2, lemgram, baseform, pos, paradigm
                baseform = parts[4].strip()
                pos = parts[5].strip()
                paradigm = parts[6].strip() if len(parts) > 6 else None
                lemgram = parts[3].strip() if len(parts) > 3 else None
                
                if baseform and pos:
                    entry = {
                        'baseform': baseform,
                        'pos': pos,
                        'paradigm': paradigm,
                        'lemgram': lemgram
                    }
                    # Store by lowercase for lookup
                    lexicon[baseform.lower()].append(entry)
    
    unique_words = len(lexicon)
    total_entries = sum(len(v) for v in lexicon.values())
    print(f"  Loaded {unique_words:,} unique words ({total_entries:,} total entries)")
    
    return lexicon


def normalize_word(word: str) -> str:
    """Normalize word for lookup."""
    # Remove leading/trailing whitespace
    word = word.strip()
    # Handle some special cases
    word = word.replace('–', '-')
    return word.lower()


def is_placeholder_or_non_lexical(word: str) -> bool:
    """
    Detect placeholder entries and non-lexical items that should not receive inflections.
    These are not real Swedish words and should have all-null inflection fields.
    """
    # Entries wrapped in parentheses like "(siffra)", "(årtal)"
    if re.match(r'^\([^)]+\)$', word):
        return True
    
    # Entries with numeric prefixes/patterns like "1-2-3 regeln", "10 metersstraff"
    if re.match(r'^\d', word):
        return True
    
    # Pure numeric entries
    if re.match(r'^[\d\s\-\+x\/]+$', word):
        return True
    
    # Very short entries (single character except valid Swedish words)
    if len(word) == 1 and word.lower() not in ['i', 'å', 'ö', 'o']:
        return True
    
    return False


def lookup_saldo(word: str, lexicon: Dict[str, List[Dict]], gloss_hint: Optional[str] = None) -> Optional[List[Dict]]:
    """
    Look up word in SALDO lexicon.
    Returns ALL matching entries (not just one) to allow context-based selection.
    """
    normalized = normalize_word(word)
    
    entries = lexicon.get(normalized)
    if not entries:
        # Try without special characters
        clean = re.sub(r'[^\wåäöÅÄÖ]', '', normalized)
        entries = lexicon.get(clean)
    
    if not entries:
        return None
    
    return entries  # Return all entries for context-based selection


def select_best_saldo_entry(entries: List[Dict], gloss_hint: Optional[str] = None) -> Dict:
    """
    Select the best SALDO entry based on context from gloss and frequency heuristics.
    
    Priority logic:
    1. If gloss hints at word class, prefer that class
    2. For ambiguous words, prefer: vb > av > nn (verbs/adjectives are often primary meanings)
    3. Among same POS, prefer entries with more common paradigms
    """
    if len(entries) == 1:
        return entries[0]
    
    # Check if gloss gives hints about word class
    gloss_class = None
    if gloss_hint:
        gloss_lower = gloss_hint.lower()
        if '@v' in gloss_lower or 'verb' in gloss_lower:
            gloss_class = 'vb'
        elif '@adj' in gloss_lower or 'adjektiv' in gloss_lower:
            gloss_class = 'av'
        elif '@b' in gloss_lower or '@en' in gloss_lower:
            gloss_class = 'nn'
    
    # If gloss hints at a class, prefer entries of that class
    if gloss_class:
        matching = [e for e in entries if e['pos'] == gloss_class]
        if matching:
            return matching[0]
    
    # For words with both verb and noun entries, prefer verb (more common primary meaning)
    # For words with both adjective and noun entries, prefer adjective
    # This fixes: "glad" (adj primary), "springa" (verb primary)
    priority = {'vb': 1, 'av': 2, 'nn': 3, 'nna': 3, 'pm': 4, 'ab': 5}
    sorted_entries = sorted(entries, key=lambda x: priority.get(x['pos'], 10))
    
    return sorted_entries[0]


def analyze_gloss(glosa: Optional[str]) -> Tuple[Optional[str], Optional[str], float, List[str]]:
    """
    Analyze gloss field for word class markers.
    Returns: (word_class, pos_tag, confidence, notes)
    """
    if not glosa:
        return None, None, 0.0, ["No gloss available"]
    
    notes = []
    
    # Check for compound marker
    if '^' in glosa:
        notes.append(f"Compound structure: {glosa}")
    
    # Check for parenthetical markers
    parens = re.findall(r'\([^)]+\)', glosa)
    if parens:
        notes.append(f"Morphological hints: {parens}")
    
    # Match against patterns
    for pattern, (word_class, pos_tag, confidence) in GLOSS_PATTERNS.items():
        if re.search(pattern, glosa, re.IGNORECASE):
            notes.append(f"Matched pattern: {pattern}")
            return word_class, pos_tag, confidence, notes
    
    # Check for uppercase patterns (often proper nouns)
    if glosa and (glosa.isupper() or (glosa[0].isupper() and '@' not in glosa)):
        if not any(c.isdigit() for c in glosa):
            notes.append("Uppercase pattern suggests proper noun")
            return 'substantiv', 'pm', 0.6, notes
    
    return None, None, 0.0, notes


def classify_word(entry: Dict, lexicon: Dict[str, List[Dict]]) -> WordClassification:
    """
    Classify a single word entry using SALDO lexicon and gloss analysis.
    """
    index = entry['index']
    ord_value = entry['ord']
    glosa = entry.get('glosa')
    
    all_notes = []
    
    # FIX 1: Check for placeholder/non-lexical entries first
    if is_placeholder_or_non_lexical(ord_value):
        all_notes.append(f"Non-lexical entry detected: '{ord_value}'")
        return WordClassification(
            index=index,
            ord=ord_value,
            glosa=glosa,
            word_class='unknown',
            pos_tag=None,
            confidence=0.0,
            source='none',
            paradigm=None,
            is_compound=False,
            notes=all_notes
        )
    
    # Check for compound
    is_compound = '^' in (glosa or '') or ' ' in ord_value
    
    # Step 1: Analyze gloss
    gloss_class, gloss_pos, gloss_conf, gloss_notes = analyze_gloss(glosa)
    all_notes.extend(gloss_notes)
    
    # Step 2: Lookup in SALDO (FIX 2: get all entries, then select best one)
    saldo_entries = lookup_saldo(ord_value, lexicon, gloss_hint=glosa)
    
    saldo_class, saldo_pos, saldo_paradigm, saldo_conf = None, None, None, 0.0
    if saldo_entries:
        # Select best entry based on context
        saldo_entry = select_best_saldo_entry(saldo_entries, gloss_hint=glosa)
        saldo_pos = saldo_entry['pos']
        saldo_paradigm = saldo_entry['paradigm']
        saldo_class = POS_TO_CLASS.get(saldo_pos, 'övrigt')
        saldo_conf = 0.9
        if len(saldo_entries) > 1:
            all_notes.append(f"SALDO: {saldo_pos} ({saldo_paradigm}) - selected from {len(saldo_entries)} entries")
        else:
            all_notes.append(f"SALDO: {saldo_pos} ({saldo_paradigm})")
    else:
        all_notes.append("Not found in SALDO")
    
    # Step 3: Combine results
    if gloss_class and saldo_class:
        # Both sources available
        if gloss_class == saldo_class:
            # Agreement - high confidence
            word_class = gloss_class
            pos_tag = saldo_pos or gloss_pos
            confidence = min(0.95, (gloss_conf + saldo_conf) / 2 + 0.1)
            source = 'both'
            all_notes.append("Gloss and SALDO agree")
        else:
            # Disagreement - use SALDO with slightly lower confidence
            word_class = saldo_class
            pos_tag = saldo_pos
            confidence = max(gloss_conf, saldo_conf) * 0.85
            source = 'saldo'
            all_notes.append(f"Gloss ({gloss_class}) and SALDO ({saldo_class}) disagree, using SALDO")
    elif saldo_class:
        # Only SALDO
        word_class = saldo_class
        pos_tag = saldo_pos
        confidence = saldo_conf
        source = 'saldo'
    elif gloss_class:
        # Only gloss
        word_class = gloss_class
        pos_tag = gloss_pos
        confidence = gloss_conf
        source = 'gloss'
    else:
        # Neither - unknown
        word_class = 'unknown'
        pos_tag = None
        confidence = 0.0
        source = 'none'
        all_notes.append("Could not classify from any source")
    
    return WordClassification(
        index=index,
        ord=ord_value,
        glosa=glosa,
        word_class=word_class,
        pos_tag=pos_tag,
        confidence=confidence,
        source=source,
        paradigm=saldo_paradigm,
        is_compound=is_compound,
        notes=all_notes
    )


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 2: Extract Headwords and Classify Word Class")
    print("=" * 60)
    
    # Load SALDO lexicon
    lexicon = load_saldo_lexicon(SALDO_FILE)
    
    # Load word entries from Step 1
    print(f"\nLoading word entries from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} word entries")
    
    # Process entries
    print("\n--- Classifying Words ---")
    start_time = time.time()
    
    classifications = []
    for i, entry in enumerate(entries):
        result = classify_word(entry, lexicon)
        classifications.append(result)
        
        if (i + 1) % 2000 == 0:
            pct = ((i + 1) / len(entries)) * 100
            print(f"  Progress: {i + 1}/{len(entries)} ({pct:.1f}%)")
    
    elapsed = time.time() - start_time
    print(f"\n  Classified {len(classifications)} entries in {elapsed:.1f} seconds")
    
    # Compile statistics
    print("\n--- Classification Statistics ---")
    class_counts = Counter(c.word_class for c in classifications)
    source_counts = Counter(c.source for c in classifications)
    pos_counts = Counter(c.pos_tag for c in classifications if c.pos_tag)
    confidence_buckets = defaultdict(int)
    
    for c in classifications:
        if c.confidence >= 0.8:
            confidence_buckets['high (≥80%)'] += 1
        elif c.confidence >= 0.5:
            confidence_buckets['medium (50-79%)'] += 1
        else:
            confidence_buckets['low (<50%)'] += 1
    
    print("\n  Word Class Distribution:")
    for cls, count in sorted(class_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(classifications)) * 100
        print(f"    {cls}: {count} ({pct:.1f}%)")
    
    print("\n  Classification Source:")
    for src, count in sorted(source_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(classifications)) * 100
        print(f"    {src}: {count} ({pct:.1f}%)")
    
    print("\n  POS Tag Distribution (top 10):")
    for pos, count in sorted(pos_counts.items(), key=lambda x: -x[1])[:10]:
        pct = (count / len(classifications)) * 100
        print(f"    {pos}: {count} ({pct:.1f}%)")
    
    print("\n  Confidence Distribution:")
    for bucket, count in sorted(confidence_buckets.items()):
        pct = (count / len(classifications)) * 100
        print(f"    {bucket}: {count} ({pct:.1f}%)")
    
    # Compounds count
    compound_count = sum(1 for c in classifications if c.is_compound)
    print(f"\n  Compound words detected: {compound_count}")
    
    # Entries with paradigm
    paradigm_count = sum(1 for c in classifications if c.paradigm)
    print(f"  Entries with SALDO paradigm: {paradigm_count}")
    
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
        "class_distribution": dict(class_counts),
        "source_distribution": dict(source_counts),
        "pos_distribution": dict(pos_counts),
        "confidence_distribution": dict(confidence_buckets),
        "compound_count": compound_count,
        "paradigm_count": paradigm_count,
        "sample_classifications": [asdict(c) for c in classifications[:30]]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 2 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
