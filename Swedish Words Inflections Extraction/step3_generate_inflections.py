"""
Step 3: Generate Inflections using SALDO API
=============================================
Uses the SALDO /gen/ endpoint to generate inflections for classified words.
Applies confidence thresholds to ensure accuracy.
"""

import json
import re
import time
import requests
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict, field
import threading
from urllib.parse import quote

# Configuration
INPUT_FILE = Path("step2_classified_entries.json")
OUTPUT_FILE = Path("step3_inflections.json")
REPORT_FILE = Path("step3_inflection_report.json")
CACHE_FILE = Path("step3_api_cache.json")

SALDO_BASE_URL = "https://spraakbanken.gu.se/ws/saldo-ws"
RATE_LIMIT_DELAY = 0.12  # ~8 requests per second
MAX_RETRIES = 3
TIMEOUT = 15

# Thread-safe rate limiting
rate_limit_lock = threading.Lock()
last_request_time = 0


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


@dataclass
class WordInflections:
    """Complete word inflection result."""
    ord: str
    substantiv: Optional[Dict] = None
    verb: Optional[Dict] = None
    adjektiv: Optional[Dict] = None
    övrigt: Optional[str] = None
    _metadata: Dict = field(default_factory=dict)


class APICache:
    """Thread-safe cache for API responses."""
    
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self._load_cache()
    
    def _load_cache(self):
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                print(f"  Loaded {len(self.cache)} cached API responses")
            except Exception as e:
                print(f"  Warning: Could not load cache: {e}")
                self.cache = {}
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any):
        with self.lock:
            self.cache[key] = value
    
    def save(self):
        with self.lock:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False)
            print(f"  Saved {len(self.cache)} API responses to cache")
            print(f"  Cache stats: {self.hits} hits, {self.misses} misses")


def rate_limited_request(url: str, cache: APICache) -> Optional[Dict]:
    """Make rate-limited API request with caching and retries."""
    global last_request_time
    
    # Check cache first
    cached = cache.get(url)
    if cached is not None:
        return cached if cached != "NULL" else None
    
    # Rate limiting
    with rate_limit_lock:
        elapsed = time.time() - last_request_time
        if elapsed < RATE_LIMIT_DELAY:
            time.sleep(RATE_LIMIT_DELAY - elapsed)
        last_request_time = time.time()
    
    # Make request with retries
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT)
            if response.status_code == 200:
                try:
                    data = response.json()
                    cache.set(url, data)
                    return data
                except json.JSONDecodeError:
                    cache.set(url, "NULL")
                    return None
            elif response.status_code == 404:
                cache.set(url, "NULL")
                return None
            elif response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            else:
                if attempt == MAX_RETRIES - 1:
                    cache.set(url, "NULL")
                    return None
        except requests.exceptions.Timeout:
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(1)
        except requests.exceptions.RequestException:
            if attempt == MAX_RETRIES - 1:
                return None
            time.sleep(1)
    
    return None


def extract_noun_forms(api_data: Dict) -> NounInflection:
    """Extract noun forms from SALDO /gen/ response."""
    inflection = NounInflection()
    
    if not api_data or 'value' not in api_data:
        return inflection
    
    forms = api_data['value']
    if not isinstance(forms, list):
        return inflection
    
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
        
        # Parse morphological descriptor
        if 'sg indef nom' in msd:
            inflection.singular = form
        elif 'sg def nom' in msd:
            inflection.bestämd_singular = form
        elif 'pl indef nom' in msd:
            inflection.plural = form
        elif 'pl def nom' in msd:
            inflection.bestämd_plural = form
    
    return inflection


def extract_verb_forms(api_data: Dict) -> VerbInflection:
    """Extract verb forms from SALDO /gen/ response."""
    inflection = VerbInflection()
    
    if not api_data or 'value' not in api_data:
        return inflection
    
    forms = api_data['value']
    if not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        # Parse verb forms
        if 'inf' in msd and 'aktiv' in msd:
            inflection.infinitiv = form
        elif 'pres' in msd and 'ind' in msd and 'aktiv' in msd:
            inflection.presens = form
        elif 'pret' in msd and 'ind' in msd and 'aktiv' in msd:
            inflection.preteritum = form
        elif 'sup' in msd and 'aktiv' in msd:
            inflection.supinum = form
        elif 'pres_part' in msd or ('pres' in msd and 'part' in msd):
            if not inflection.particip:
                inflection.particip = form
    
    return inflection


def extract_adjective_forms(api_data: Dict) -> AdjectiveInflection:
    """Extract adjective forms from SALDO /gen/ response."""
    inflection = AdjectiveInflection()
    
    if not api_data or 'value' not in api_data:
        return inflection
    
    forms = api_data['value']
    if not isinstance(forms, list):
        return inflection
    
    for form_entry in forms:
        if not isinstance(form_entry, dict):
            continue
        
        form = form_entry.get('form', '')
        msd = form_entry.get('msd', '')
        
        # Parse adjective forms
        if 'pos' in msd and 'sg' in msd and 'indef' in msd:
            if 'nom' in msd or ('nom' not in msd and 'gen' not in msd):
                if not inflection.positiv:
                    inflection.positiv = form
        elif 'komp' in msd:
            if not inflection.komparativ:
                inflection.komparativ = form
        elif 'super' in msd and 'indef' in msd:
            if not inflection.superlativ:
                inflection.superlativ = form
    
    return inflection


def generate_inflections(entry: Dict, cache: APICache) -> WordInflections:
    """Generate inflections for a classified word entry."""
    ord_value = entry['ord']
    word_class = entry['word_class']
    paradigm = entry.get('paradigm')
    confidence = entry.get('confidence', 0.0)
    pos_tag = entry.get('pos_tag')
    
    result = WordInflections(ord=ord_value)
    result._metadata = {
        'original_class': word_class,
        'pos_tag': pos_tag,
        'paradigm': paradigm,
        'confidence': confidence,
        'api_called': False,
        'api_success': False,
        'notes': []
    }
    
    # Skip low confidence entries or entries without paradigm
    if confidence < 0.5:
        result._metadata['notes'].append("Low confidence - skipped API call")
        if word_class == 'substantiv':
            result.substantiv = asdict(NounInflection())
        elif word_class == 'verb':
            result.verb = asdict(VerbInflection())
        elif word_class == 'adjektiv':
            result.adjektiv = asdict(AdjectiveInflection())
        elif word_class == 'övrigt':
            result.övrigt = None
        return result
    
    if not paradigm:
        result._metadata['notes'].append("No paradigm available")
        if word_class == 'substantiv':
            result.substantiv = asdict(NounInflection())
        elif word_class == 'verb':
            result.verb = asdict(VerbInflection())
        elif word_class == 'adjektiv':
            result.adjektiv = asdict(AdjectiveInflection())
        elif word_class == 'övrigt':
            result.övrigt = None
        return result
    
    # Call SALDO /gen/ endpoint
    encoded_word = quote(ord_value, safe='')
    url = f"{SALDO_BASE_URL}/gen/json/{paradigm}/{encoded_word}"
    
    result._metadata['api_called'] = True
    api_data = rate_limited_request(url, cache)
    
    if api_data:
        result._metadata['api_success'] = True
        
        if word_class == 'substantiv':
            noun_forms = extract_noun_forms(api_data)
            result.substantiv = asdict(noun_forms)
            result._metadata['notes'].append(f"Generated {sum(1 for v in asdict(noun_forms).values() if v)} noun forms")
        
        elif word_class == 'verb':
            verb_forms = extract_verb_forms(api_data)
            result.verb = asdict(verb_forms)
            result._metadata['notes'].append(f"Generated {sum(1 for v in asdict(verb_forms).values() if v)} verb forms")
        
        elif word_class == 'adjektiv':
            adj_forms = extract_adjective_forms(api_data)
            result.adjektiv = asdict(adj_forms)
            result._metadata['notes'].append(f"Generated {sum(1 for v in asdict(adj_forms).values() if v)} adjective forms")
        
        elif word_class == 'övrigt':
            # For other word classes, just note the POS tag
            pos_desc = {
                'ab': 'adverb - no inflections',
                'pp': 'preposition - no inflections',
                'kn': 'conjunction - no inflections',
                'sn': 'subordinating conjunction - no inflections',
                'in': 'interjection - no inflections',
                'pn': 'pronoun',
                'nl': 'numeral',
            }
            result.övrigt = pos_desc.get(pos_tag, f'{pos_tag or "unknown"} - limited inflections')
    else:
        result._metadata['notes'].append("API call failed or returned no data")
        # Set empty inflection object for the word class
        if word_class == 'substantiv':
            result.substantiv = asdict(NounInflection())
        elif word_class == 'verb':
            result.verb = asdict(VerbInflection())
        elif word_class == 'adjektiv':
            result.adjektiv = asdict(AdjectiveInflection())
        elif word_class == 'övrigt':
            result.övrigt = None
    
    return result


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 3: Generate Inflections using SALDO API")
    print("=" * 60)
    
    # Load classifications from Step 2
    print(f"\nLoading classifications from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} classified entries")
    
    # Filter entries that need API calls
    entries_with_paradigm = [e for e in entries if e.get('paradigm') and e.get('confidence', 0) >= 0.5]
    print(f"  Entries with paradigm and sufficient confidence: {len(entries_with_paradigm)}")
    
    # Initialize cache
    print("\nInitializing API cache...")
    cache = APICache(CACHE_FILE)
    
    # Process entries
    print("\n--- Generating Inflections ---")
    print("  (API calls required - this may take a while)")
    
    start_time = time.time()
    results = []
    api_calls = 0
    successful_api = 0
    
    for i, entry in enumerate(entries):
        result = generate_inflections(entry, cache)
        results.append(result)
        
        if result._metadata.get('api_called'):
            api_calls += 1
            if result._metadata.get('api_success'):
                successful_api += 1
        
        if (i + 1) % 500 == 0:
            pct = ((i + 1) / len(entries)) * 100
            elapsed = time.time() - start_time
            eta = (elapsed / (i + 1)) * (len(entries) - i - 1)
            print(f"  Progress: {i + 1}/{len(entries)} ({pct:.1f}%) - ETA: {eta:.0f}s")
    
    elapsed = time.time() - start_time
    print(f"\n  Processed {len(results)} entries in {elapsed:.1f} seconds")
    print(f"  API calls made: {api_calls}")
    print(f"  Successful API calls: {successful_api}")
    
    # Save cache
    cache.save()
    
    # Compile statistics
    print("\n--- Inflection Statistics ---")
    
    noun_with_forms = sum(1 for r in results if r.substantiv and any(v for v in r.substantiv.values() if v))
    verb_with_forms = sum(1 for r in results if r.verb and any(v for v in r.verb.values() if v))
    adj_with_forms = sum(1 for r in results if r.adjektiv and any(v for v in r.adjektiv.values() if v))
    other_with_info = sum(1 for r in results if r.övrigt)
    
    print(f"\n  Nouns with inflection forms: {noun_with_forms}")
    print(f"  Verbs with inflection forms: {verb_with_forms}")
    print(f"  Adjectives with inflection forms: {adj_with_forms}")
    print(f"  Other with grammatical info: {other_with_info}")
    
    # Prepare output (remove metadata for clean output)
    print(f"\n--- Saving Results ---")
    
    output_data = []
    for r in results:
        output_entry = {
            'ord': r.ord,
            'substantiv': r.substantiv,
            'verb': r.verb,
            'adjektiv': r.adjektiv,
            'övrigt': r.övrigt
        }
        output_data.append(output_entry)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"  Inflections saved to: {OUTPUT_FILE}")
    
    # Save detailed report
    report = {
        "total_entries": len(results),
        "processing_time_seconds": elapsed,
        "api_calls_made": api_calls,
        "successful_api_calls": successful_api,
        "cache_hits": cache.hits,
        "cache_misses": cache.misses,
        "inflection_counts": {
            "nouns_with_forms": noun_with_forms,
            "verbs_with_forms": verb_with_forms,
            "adjectives_with_forms": adj_with_forms,
            "other_with_info": other_with_info
        },
        "sample_outputs": [
            {
                'ord': r.ord,
                'substantiv': r.substantiv,
                'verb': r.verb,
                'adjektiv': r.adjektiv,
                'övrigt': r.övrigt,
                '_metadata': r._metadata
            }
            for r in results[:30]
        ]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 3 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
