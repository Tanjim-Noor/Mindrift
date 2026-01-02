"""
Step 3b v3: Extract Multi-Class Inflections
=============================================
Processes cached API responses to extract inflections for ALL word classes per word.
Key changes from v2:
- Populates MULTIPLE word class fields when applicable (e.g., kedja = noun + verb)
- Provides grammar labels in övrigt field for adverbs, interjections, etc.
- Handles invariable nouns (adjö) by detecting MSD 'invar' markers
- For inflected forms like "kan", uses lemma paradigm but reports original word
- Suppresses questionable noun forms when övrigt or adjektiv is primary
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
import time
from urllib.parse import quote

# Configuration
INPUT_FILE = Path("step2_classified_entries_v3.json")
CACHE_FILE = Path("step3_api_cache_v3.json")
OUTPUT_FILE = Path("step3_inflections_v3.json")
FINAL_OUTPUT = Path("swedish_word_inflections_v3.json")
REPORT_FILE = Path("step3_inflection_report_v3.json")

# Special verb form mappings - words that are primarily verb forms of other lemmas
# These should get verb forms from their parent lemma
VERB_FORM_MAPPINGS = {
    # Present tense forms that appear as headwords
    'kan': ('kunna', 'vb_om_kunna'),  # kan = present of kunna
    'ska': ('skola', 'vb_om_skola'),  # ska = present of skola
    'vill': ('vilja', 'vb_om_vilja'), # vill = present of vilja
    'måste': ('måste', 'vb_om_måste'), # måste is same in infinitive
}

# Words where noun forms should be SUPPRESSED if another primary class exists
# (These are primarily adjectives/interjections, noun use is derivative/rare)
SUPPRESS_NOUN_IF_PRIMARY = {
    'adjö': 'in',      # Interjection is primary, noun "ett adjö" is derivative
    'glad': 'av',      # Adjective is primary, noun "en glad" (type of fabric) is rare
    'hej': 'in',       # Interjection is primary
    'hallå': 'in',     # Interjection is primary  
    'oj': 'in',        # Interjection is primary
    'aj': 'in',        # Interjection is primary
    'tack': 'in',      # Interjection is primary (though noun is common too)
}


@dataclass
class NounInflection:
    """Noun inflection forms."""
    singular: Optional[str] = None
    plural: Optional[str] = None
    bestämd_singular: Optional[str] = None
    bestämd_plural: Optional[str] = None


@dataclass
class VerbInflection:
    """Verb inflection forms."""
    infinitiv: Optional[str] = None
    presens: Optional[str] = None
    preteritum: Optional[str] = None
    supinum: Optional[str] = None
    particip: Optional[str] = None


@dataclass
class AdjectiveInflection:
    """Adjective inflection forms."""
    positiv: Optional[str] = None
    komparativ: Optional[str] = None
    superlativ: Optional[str] = None


# Full names for övrigt POS types
POS_FULL_NAMES = {
    'in': 'interjektion',
    'inm': 'interjektion (fras)',
    'ab': 'adverb',
    'abm': 'adverb (fras)',
    'pp': 'preposition',
    'ppm': 'preposition (fras)',
    'kn': 'konjunktion',
    'knm': 'konjunktion (fras)',
    'sn': 'subjunktion',
    'snm': 'subjunktion (fras)',
    'pn': 'pronomen',
    'pnm': 'pronomen (fras)',
    'hp': 'interrogativt/relativt pronomen',
    'hs': 'determinativ',
    'nl': 'räkneord',
    'nlm': 'räkneord (fras)',
    'ie': 'infinitivmärke',
    'pm': 'egennamn',
    'pma': 'egennamn (förkortning)',
    'pmm': 'egennamn (fras)',
    # Noun/verb/adj multiword - these show up as övrigt sometimes
    'nnm': 'substantiv (fras)',
    'vbm': 'verb (fras)',
    'avm': 'adjektiv (fras)',
}

# POS tags that should have övrigt info
OVRIGT_POS = {'in', 'ab', 'pp', 'kn', 'sn', 'pn', 'hp', 'hs', 'nl', 'ie'}


def is_invariable(forms: List[Dict]) -> bool:
    """Check if word is invariable based on API response."""
    if not forms:
        return False
    for f in forms:
        msd = f.get('msd', '').lower()
        if 'invar' in msd:
            return True
    return False


def has_valid_plural(forms: List[Dict]) -> bool:
    """Check if word has valid distinct plural forms."""
    singular = None
    plural = None
    
    for f in forms:
        msd = f.get('msd', '').strip()
        form = f.get('form', '')
        
        if msd == 'sg indef nom':
            singular = form
        elif msd == 'pl indef nom':
            plural = form
    
    # If plural equals singular, it might be uncountable
    if singular and plural and singular == plural:
        return False
    
    return plural is not None


def extract_noun_forms(forms: List[Dict], word: str) -> NounInflection:
    """
    Extract noun forms with improved handling for invariable/uncountable nouns.
    """
    inflection = NounInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    # Check for invariable nouns
    invariable = is_invariable(forms)
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        # Skip compound forms
        if 'ci' in msd or 'cm' in msd or 'sms' in msd:
            continue
        if form.endswith('-'):
            continue
        
        msd_stripped = msd.strip()
        
        # First-match logic for modern forms
        if msd_stripped == 'sg indef nom' and not inflection.singular:
            inflection.singular = form
        elif msd_stripped == 'sg def nom' and not inflection.bestämd_singular:
            inflection.bestämd_singular = form
        elif msd_stripped == 'pl indef nom' and not inflection.plural:
            # Only set plural if not same as singular (for uncountable nouns)
            if not invariable or form != inflection.singular:
                inflection.plural = form
        elif msd_stripped == 'pl def nom' and not inflection.bestämd_plural:
            if not invariable or (inflection.plural and form != inflection.plural):
                inflection.bestämd_plural = form
    
    return inflection


def extract_verb_forms(forms: List[Dict], original_word: str = None) -> VerbInflection:
    """
    Extract verb forms from SALDO /gen/ response.
    If original_word is an inflected form (e.g., "kan"), fill presens with it.
    """
    inflection = VerbInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        msd_lower = msd.lower().strip()
        
        if 'inf aktiv' in msd_lower:
            if not inflection.infinitiv:
                inflection.infinitiv = form
        elif 'pres ind aktiv' in msd_lower:
            if not inflection.presens:
                inflection.presens = form
        elif 'pret ind aktiv' in msd_lower:
            if not inflection.preteritum:
                inflection.preteritum = form
        elif 'sup aktiv' in msd_lower:
            if not inflection.supinum:
                inflection.supinum = form
        elif 'pres_part nom' in msd_lower or 'prespart' in msd_lower:
            if not inflection.particip:
                inflection.particip = form
    
    return inflection


def extract_adjective_forms(forms: List[Dict]) -> AdjectiveInflection:
    """Extract adjective forms from SALDO /gen/ response."""
    inflection = AdjectiveInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        msd_lower = msd.lower().strip()
        
        # Positive form
        if 'pos' in msd_lower and 'indef' in msd_lower:
            if 'sg' in msd_lower or 'masc' in msd_lower:
                if not inflection.positiv:
                    inflection.positiv = form
        elif msd_lower == 'pos sg indef':
            if not inflection.positiv:
                inflection.positiv = form
        
        # Comparative
        if 'komp' in msd_lower:
            if not inflection.komparativ:
                inflection.komparativ = form
        
        # Superlative
        if 'super' in msd_lower:
            if 'indef' in msd_lower:
                if not inflection.superlativ:
                    inflection.superlativ = form
            elif not inflection.superlativ and 'def' not in msd_lower:
                inflection.superlativ = form
    
    return inflection


def extract_ovrigt_info(forms: List[Dict], pos: str) -> Optional[str]:
    """
    Generate descriptive string for övrigt category.
    Per requirement: "Övriga ordklasser: ge relevant grammatik om möjligt."
    """
    pos_name = POS_FULL_NAMES.get(pos, pos)
    
    if forms:
        # Check if invariable
        for f in forms:
            msd = f.get('msd', '').lower()
            if 'invar' in msd:
                return f"{pos_name} (oböjligt)"
        
        # For other cases, just return the POS name
        return pos_name
    
    return pos_name


def get_cache_key(paradigm: str, word: str) -> str:
    """Generate cache key URL."""
    encoded_word = quote(word, safe='')
    return f"https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{paradigm}/{encoded_word}"


def process_entry(entry: Dict, cache: Dict) -> Dict:
    """
    Process a single entry with multi-class support.
    Populates ALL applicable word class fields.
    Handles special cases like verb forms and suppressed nouns.
    """
    ord_value = entry['ord']
    all_entries = entry.get('all_saldo_entries', [])
    is_placeholder = entry.get('is_placeholder', False)
    primary_class = entry.get('primary_word_class', 'unknown')
    
    result = {
        'ord': ord_value,
        'substantiv': None,
        'verb': None,
        'adjektiv': None,
        'övrigt': None,
        '_metadata': {
            'primary_class': primary_class,
            'all_pos': [e['pos'] for e in all_entries],
            'is_placeholder': is_placeholder,
            'api_success': False,
            'forms_extracted': 0,
            'classes_populated': [],
            'notes': []
        }
    }
    
    # Handle placeholders
    if is_placeholder:
        result['_metadata']['notes'].append("Placeholder entry - all fields null")
        return result
    
    # Check for special verb form mappings FIRST (kan -> kunna, etc.)
    if ord_value.lower() in VERB_FORM_MAPPINGS:
        lemma, paradigm = VERB_FORM_MAPPINGS[ord_value.lower()]
        cache_key = get_cache_key(paradigm, lemma)
        api_data = cache.get(cache_key)
        
        if api_data and api_data != "NULL":
            forms = api_data if isinstance(api_data, list) else api_data.get('value', [])
            if forms:
                verb_forms = extract_verb_forms(forms, ord_value)
                verb_dict = asdict(verb_forms)
                if any(v for v in verb_dict.values() if v):
                    result['verb'] = verb_dict
                    result['_metadata']['classes_populated'].append('verb')
                    result['_metadata']['forms_extracted'] += sum(1 for v in verb_dict.values() if v)
                    result['_metadata']['notes'].append(f"Verb forms from {lemma} ({paradigm})")
                    result['_metadata']['api_success'] = True
                    # For verb-form words like "kan", don't add noun forms
                    return result
    
    # Check if noun should be suppressed for this word
    suppress_noun = ord_value.lower() in SUPPRESS_NOUN_IF_PRIMARY
    suppress_noun_primary_pos = SUPPRESS_NOUN_IF_PRIMARY.get(ord_value.lower())
    
    # No SALDO entries
    if not all_entries:
        result['_metadata']['notes'].append("No SALDO entries found")
        return result
    
    # Determine what POS types exist for this word
    has_ovrigt = any(e.get('word_class') == 'övrigt' for e in all_entries)
    has_adjektiv = any(e.get('pos') == 'av' for e in all_entries)
    
    # Process EACH word class entry
    ovrigt_entries = []  # Collect övrigt POS tags
    
    for saldo_entry in all_entries:
        pos = saldo_entry.get('pos', '')
        paradigm = saldo_entry.get('paradigm', '')
        word_class = saldo_entry.get('word_class', '')
        is_inflected = saldo_entry.get('is_inflected_form', False)
        lemma = saldo_entry.get('lemma')
        
        if not paradigm:
            continue
        
        # Determine which word to use for API lookup
        word_for_api = lemma if is_inflected and lemma else ord_value
        
        # Get cached API response
        cache_key = get_cache_key(paradigm, word_for_api)
        api_data = cache.get(cache_key)
        
        if api_data is None or api_data == "NULL":
            result['_metadata']['notes'].append(f"No cache for {pos}:{paradigm}")
            continue
        
        forms = api_data if isinstance(api_data, list) else api_data.get('value', [])
        
        if not forms:
            continue
        
        result['_metadata']['api_success'] = True
        
        # Extract based on word class
        if word_class == 'substantiv' and result['substantiv'] is None:
            # Check if we should suppress noun forms
            if suppress_noun and suppress_noun_primary_pos:
                result['_metadata']['notes'].append(f"Noun suppressed - {suppress_noun_primary_pos} is primary for '{ord_value}'")
                continue
            
            noun_forms = extract_noun_forms(forms, ord_value)
            noun_dict = asdict(noun_forms)
            if any(v for v in noun_dict.values() if v):
                result['substantiv'] = noun_dict
                result['_metadata']['classes_populated'].append('substantiv')
                forms_count = sum(1 for v in noun_dict.values() if v)
                result['_metadata']['forms_extracted'] += forms_count
                result['_metadata']['notes'].append(f"Noun forms from {paradigm}")
        
        elif word_class == 'verb' and result['verb'] is None:
            verb_forms = extract_verb_forms(forms, ord_value)
            verb_dict = asdict(verb_forms)
            if any(v for v in verb_dict.values() if v):
                result['verb'] = verb_dict
                result['_metadata']['classes_populated'].append('verb')
                forms_count = sum(1 for v in verb_dict.values() if v)
                result['_metadata']['forms_extracted'] += forms_count
                result['_metadata']['notes'].append(f"Verb forms from {paradigm}")
        
        elif word_class == 'adjektiv' and result['adjektiv'] is None:
            adj_forms = extract_adjective_forms(forms)
            adj_dict = asdict(adj_forms)
            if any(v for v in adj_dict.values() if v):
                result['adjektiv'] = adj_dict
                result['_metadata']['classes_populated'].append('adjektiv')
                forms_count = sum(1 for v in adj_dict.values() if v)
                result['_metadata']['forms_extracted'] += forms_count
                result['_metadata']['notes'].append(f"Adjective forms from {paradigm}")
        
        elif word_class == 'övrigt':
            # Collect övrigt POS for combined output
            ovrigt_entries.append((pos, forms))
    
    # Handle övrigt - generate grammar label
    if ovrigt_entries and result['övrigt'] is None:
        # Use first övrigt entry for the label
        pos, forms = ovrigt_entries[0]
        ovrigt_info = extract_ovrigt_info(forms, pos)
        if ovrigt_info:
            result['övrigt'] = ovrigt_info
            result['_metadata']['classes_populated'].append('övrigt')
            result['_metadata']['notes'].append(f"Övrigt info: {ovrigt_info}")
    
    # If only övrigt entries exist (e.g., pure interjection), ensure we have something
    if not result['_metadata']['classes_populated'] and ovrigt_entries:
        pos, forms = ovrigt_entries[0]
        result['övrigt'] = extract_ovrigt_info(forms, pos)
        result['_metadata']['classes_populated'].append('övrigt')
    
    return result


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 3b v3: Multi-Class Inflection Extraction")
    print("=" * 60)
    
    # Load classifications
    print(f"\nLoading classifications from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} entries")
    
    # Load cache
    print(f"\nLoading API cache from {CACHE_FILE}...")
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    print(f"  Loaded {len(cache)} cached responses")
    
    # Process entries
    print("\n--- Extracting Inflections ---")
    start_time = time.time()
    
    results = []
    for i, entry in enumerate(entries):
        result = process_entry(entry, cache)
        results.append(result)
        
        if (i + 1) % 2000 == 0:
            pct = ((i + 1) / len(entries)) * 100
            print(f"  Progress: {i + 1}/{len(entries)} ({pct:.1f}%)")
    
    elapsed = time.time() - start_time
    print(f"\n  Processed {len(results)} entries in {elapsed:.1f} seconds")
    
    # Compile statistics
    print("\n--- Inflection Statistics ---")
    
    noun_with_forms = sum(1 for r in results if r['substantiv'] and any(v for v in r['substantiv'].values() if v))
    verb_with_forms = sum(1 for r in results if r['verb'] and any(v for v in r['verb'].values() if v))
    adj_with_forms = sum(1 for r in results if r['adjektiv'] and any(v for v in r['adjektiv'].values() if v))
    other_with_info = sum(1 for r in results if r['övrigt'])
    
    # Count entries with multiple classes populated
    multi_class_count = sum(1 for r in results if len(r['_metadata']['classes_populated']) > 1)
    
    # Count combinations
    class_combos = Counter(tuple(sorted(r['_metadata']['classes_populated'])) for r in results)
    
    print(f"\n  Entries with noun forms: {noun_with_forms}")
    print(f"  Entries with verb forms: {verb_with_forms}")
    print(f"  Entries with adjective forms: {adj_with_forms}")
    print(f"  Entries with övrigt info: {other_with_info}")
    print(f"  Multi-class entries: {multi_class_count}")
    
    print(f"\n  Class combination distribution (top 15):")
    for combo, count in class_combos.most_common(15):
        combo_str = '+'.join(combo) if combo else 'none'
        pct = (count / len(results)) * 100
        print(f"    {combo_str}: {count} ({pct:.1f}%)")
    
    # Prepare clean output
    print(f"\n--- Saving Results ---")
    
    output_data = []
    for r in results:
        output_entry = {
            'ord': r['ord'],
            'substantiv': r['substantiv'],
            'verb': r['verb'],
            'adjektiv': r['adjektiv'],
            'övrigt': r['övrigt']
        }
        output_data.append(output_entry)
    
    # Save detailed output with metadata
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"  Detailed output saved to: {OUTPUT_FILE}")
    
    # Save final clean output
    with open(FINAL_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Final output saved to: {FINAL_OUTPUT}")
    
    # Save report
    report = {
        "total_entries": len(results),
        "processing_time_seconds": elapsed,
        "inflection_counts": {
            "nouns_with_forms": noun_with_forms,
            "verbs_with_forms": verb_with_forms,
            "adjectives_with_forms": adj_with_forms,
            "other_with_info": other_with_info,
            "multi_class_entries": multi_class_count
        },
        "class_combinations": {'+'.join(k) if k else 'none': v for k, v in class_combos.most_common(50)},
        "sample_multi_class": [
            r for r in results 
            if len(r['_metadata']['classes_populated']) > 1
        ][:30]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 3b v3 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
