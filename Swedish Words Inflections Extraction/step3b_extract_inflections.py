"""
Step 3b: Process Cached API Responses to Extract Inflections
=============================================================
Reprocesses the cached API responses with corrected extraction logic.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
import time

# Configuration
INPUT_FILE = Path("step2_classified_entries.json")
CACHE_FILE = Path("step3_api_cache.json")
OUTPUT_FILE = Path("step3_inflections.json")
REPORT_FILE = Path("step3_inflection_report.json")


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


def extract_noun_forms(forms: List[Dict]) -> NounInflection:
    """Extract noun forms from SALDO /gen/ response (list format)."""
    inflection = NounInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        # Skip compound forms and forms ending with hyphen
        if 'ci' in msd or 'cm' in msd or 'sms' in msd:
            continue
        if form.endswith('-'):
            continue
        
        # Parse morphological descriptor
        if 'sg indef nom' == msd.strip():
            inflection.singular = form
        elif 'sg def nom' == msd.strip():
            inflection.bestämd_singular = form
        elif 'pl indef nom' == msd.strip():
            inflection.plural = form
        elif 'pl def nom' == msd.strip():
            inflection.bestämd_plural = form
    
    return inflection


def extract_verb_forms(forms: List[Dict]) -> VerbInflection:
    """Extract verb forms from SALDO /gen/ response (list format)."""
    inflection = VerbInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        # Parse verb forms by MSD
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
    """Extract adjective forms from SALDO /gen/ response (list format)."""
    inflection = AdjectiveInflection()
    
    if not forms or not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        msd_lower = msd.lower().strip()
        
        # Positive form (basic form, usually masc/sg/indef)
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
        
        # Superlative (indefinite preferred)
        if 'super' in msd_lower:
            if 'indef' in msd_lower:
                if not inflection.superlativ:
                    inflection.superlativ = form
            elif not inflection.superlativ and 'def' not in msd_lower:
                inflection.superlativ = form
    
    return inflection


def process_entry(entry: Dict, cache: Dict) -> Dict:
    """Process a single entry using cached API data."""
    ord_value = entry['ord']
    word_class = entry['word_class']
    paradigm = entry.get('paradigm')
    confidence = entry.get('confidence', 0.0)
    pos_tag = entry.get('pos_tag')
    
    result = {
        'ord': ord_value,
        'substantiv': None,
        'verb': None,
        'adjektiv': None,
        'övrigt': None,
        '_metadata': {
            'original_class': word_class,
            'pos_tag': pos_tag,
            'paradigm': paradigm,
            'confidence': confidence,
            'api_success': False,
            'forms_extracted': 0,
            'notes': []
        }
    }
    
    # Skip entries without paradigm or low confidence
    if confidence < 0.5:
        result['_metadata']['notes'].append("Low confidence - skipped")
        return result
    
    if not paradigm:
        result['_metadata']['notes'].append("No paradigm available")
        return result
    
    # Look up cached API response
    from urllib.parse import quote
    encoded_word = quote(ord_value, safe='')
    url = f"https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{paradigm}/{encoded_word}"
    
    api_data = cache.get(url)
    
    if api_data is None or api_data == "NULL":
        result['_metadata']['notes'].append("No cached API data")
        return result
    
    # Handle both list and dict responses
    forms = api_data if isinstance(api_data, list) else api_data.get('value', [])
    
    if not forms:
        result['_metadata']['notes'].append("Empty API response")
        return result
    
    result['_metadata']['api_success'] = True
    
    # Extract forms based on word class
    if word_class == 'substantiv':
        noun_forms = extract_noun_forms(forms)
        result['substantiv'] = asdict(noun_forms)
        forms_count = sum(1 for v in asdict(noun_forms).values() if v)
        result['_metadata']['forms_extracted'] = forms_count
        result['_metadata']['notes'].append(f"Extracted {forms_count} noun forms")
    
    elif word_class == 'verb':
        verb_forms = extract_verb_forms(forms)
        result['verb'] = asdict(verb_forms)
        forms_count = sum(1 for v in asdict(verb_forms).values() if v)
        result['_metadata']['forms_extracted'] = forms_count
        result['_metadata']['notes'].append(f"Extracted {forms_count} verb forms")
    
    elif word_class == 'adjektiv':
        adj_forms = extract_adjective_forms(forms)
        result['adjektiv'] = asdict(adj_forms)
        forms_count = sum(1 for v in asdict(adj_forms).values() if v)
        result['_metadata']['forms_extracted'] = forms_count
        result['_metadata']['notes'].append(f"Extracted {forms_count} adjective forms")
    
    elif word_class == 'övrigt':
        pos_desc = {
            'ab': 'adverb - no inflections',
            'abm': 'adverb (multi-word) - no inflections',
            'pp': 'preposition - no inflections',
            'kn': 'conjunction - no inflections',
            'sn': 'subordinating conjunction - no inflections',
            'in': 'interjection - no inflections',
            'pn': 'pronoun',
            'nl': 'numeral',
            'pm': 'proper noun',
            'pmm': 'proper noun (multi-word)',
            'vbm': 'verb (multi-word)',
        }
        result['övrigt'] = pos_desc.get(pos_tag, f'{pos_tag or "unknown"} - limited inflections')
        result['_metadata']['forms_extracted'] = 1
    
    return result


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 3b: Process Cached API Responses")
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
    
    total_with_data = noun_with_forms + verb_with_forms + adj_with_forms + other_with_info
    
    print(f"\n  Nouns with inflection forms: {noun_with_forms}")
    print(f"  Verbs with inflection forms: {verb_with_forms}")
    print(f"  Adjectives with inflection forms: {adj_with_forms}")
    print(f"  Other with grammatical info: {other_with_info}")
    print(f"  Total entries with data: {total_with_data}")
    
    # Form count distribution
    form_counts = Counter(r['_metadata']['forms_extracted'] for r in results)
    print(f"\n  Forms extracted distribution:")
    for count in sorted(form_counts.keys()):
        freq = form_counts[count]
        pct = (freq / len(results)) * 100
        print(f"    {count} forms: {freq} entries ({pct:.1f}%)")
    
    # Prepare clean output (without metadata)
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
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Inflections saved to: {OUTPUT_FILE}")
    
    # Save detailed report
    sample_with_forms = [r for r in results if r['_metadata']['forms_extracted'] > 0][:50]
    
    report = {
        "total_entries": len(results),
        "processing_time_seconds": elapsed,
        "inflection_counts": {
            "nouns_with_forms": noun_with_forms,
            "verbs_with_forms": verb_with_forms,
            "adjectives_with_forms": adj_with_forms,
            "other_with_info": other_with_info,
            "total_with_data": total_with_data
        },
        "form_count_distribution": dict(form_counts),
        "sample_outputs": sample_with_forms
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 3b Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
