"""
Step 3 v3: Make API Calls for All Paradigms (Multi-Class Support)
==================================================================
Makes SALDO API calls for ALL paradigms of each word, not just the primary one.
This enables multi-class output (e.g., kedja as both noun AND verb).
"""

import json
import time
import requests
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Set, Optional
from urllib.parse import quote

# Configuration
INPUT_FILE = Path("step2_classified_entries_v3.json")
CACHE_FILE = Path("step3_api_cache.json")
OUTPUT_CACHE = Path("step3_api_cache_v3.json")
REPORT_FILE = Path("step3_api_calls_report_v3.json")

# SALDO API endpoint
SALDO_GEN_API = "https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{paradigm}/{word}"

# Rate limiting
REQUEST_DELAY = 0.1  # seconds between requests
MAX_RETRIES = 3


def load_existing_cache(filepath: Path) -> Dict:
    """Load existing API cache."""
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def make_api_call(paradigm: str, word: str, retries: int = MAX_RETRIES) -> Optional[List[Dict]]:
    """Make SALDO gen API call with retry logic."""
    encoded_word = quote(word, safe='')
    url = SALDO_GEN_API.format(paradigm=paradigm, word=encoded_word)
    
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                data = response.json()
                # Handle both list and dict responses
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return data.get('value', [])
            elif response.status_code == 404:
                return None
            else:
                print(f"    Warning: Status {response.status_code} for {word}")
        except requests.exceptions.Timeout:
            print(f"    Timeout for {word}, attempt {attempt + 1}")
        except Exception as e:
            print(f"    Error for {word}: {e}")
        
        if attempt < retries - 1:
            time.sleep(1)
    
    return None


def get_cache_key(paradigm: str, word: str) -> str:
    """Generate cache key URL."""
    encoded_word = quote(word, safe='')
    return f"https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{paradigm}/{encoded_word}"


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 3 v3: Multi-Paradigm API Calls")
    print("=" * 60)
    
    # Load classifications
    print(f"\nLoading classifications from {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} entries")
    
    # Load existing cache
    print(f"\nLoading existing cache from {CACHE_FILE}...")
    cache = load_existing_cache(CACHE_FILE)
    print(f"  Loaded {len(cache)} cached responses")
    
    # Identify all paradigm/word combinations needed
    print("\n--- Identifying Required API Calls ---")
    required_calls: Dict[str, Dict] = {}  # cache_key -> {paradigm, word, entry_index}
    
    for entry in entries:
        ord_value = entry['ord']
        all_entries = entry.get('all_saldo_entries', [])
        
        # Skip placeholders
        if entry.get('is_placeholder', False):
            continue
        
        for saldo_entry in all_entries:
            paradigm = saldo_entry.get('paradigm')
            if not paradigm:
                continue
            
            # Handle inflected forms - use lemma for API call
            word_for_api = ord_value
            if saldo_entry.get('is_inflected_form'):
                lemma = saldo_entry.get('lemma')
                if lemma:
                    word_for_api = lemma
            
            cache_key = get_cache_key(paradigm, word_for_api)
            
            if cache_key not in required_calls:
                required_calls[cache_key] = {
                    'paradigm': paradigm,
                    'word': word_for_api,
                    'original_word': ord_value,
                    'pos': saldo_entry.get('pos')
                }
    
    print(f"  Total paradigm/word combinations needed: {len(required_calls)}")
    
    # Find new calls (not in cache)
    new_calls = {k: v for k, v in required_calls.items() if k not in cache}
    cached_calls = len(required_calls) - len(new_calls)
    
    print(f"  Already cached: {cached_calls}")
    print(f"  New calls needed: {len(new_calls)}")
    
    if not new_calls:
        print("\n  All paradigms already cached!")
        # Copy cache to v3 output
        with open(OUTPUT_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
        print(f"  Cache copied to: {OUTPUT_CACHE}")
        return
    
    # Make API calls
    print(f"\n--- Making {len(new_calls)} API Calls ---")
    start_time = time.time()
    
    success_count = 0
    error_count = 0
    new_cache_entries = {}
    
    call_list = list(new_calls.items())
    
    for i, (cache_key, call_info) in enumerate(call_list):
        paradigm = call_info['paradigm']
        word = call_info['word']
        
        result = make_api_call(paradigm, word)
        
        if result is not None:
            new_cache_entries[cache_key] = result
            cache[cache_key] = result
            success_count += 1
        else:
            new_cache_entries[cache_key] = "NULL"
            cache[cache_key] = "NULL"
            error_count += 1
        
        # Progress reporting
        if (i + 1) % 100 == 0 or (i + 1) == len(call_list):
            pct = ((i + 1) / len(call_list)) * 100
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(call_list) - i - 1) / rate if rate > 0 else 0
            print(f"  Progress: {i + 1}/{len(call_list)} ({pct:.1f}%) - "
                  f"Success: {success_count}, Errors: {error_count} - "
                  f"ETA: {remaining:.0f}s")
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    elapsed = time.time() - start_time
    print(f"\n  Completed {len(new_calls)} API calls in {elapsed:.1f} seconds")
    print(f"  Success: {success_count}, Errors: {error_count}")
    
    # Save updated cache
    print(f"\n--- Saving Cache ---")
    with open(OUTPUT_CACHE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    print(f"  Cache saved to: {OUTPUT_CACHE} ({len(cache)} total entries)")
    
    # Save report
    report = {
        "total_required_calls": len(required_calls),
        "already_cached": cached_calls,
        "new_calls_made": len(new_calls),
        "success_count": success_count,
        "error_count": error_count,
        "processing_time_seconds": elapsed,
        "cache_size": len(cache),
        "sample_new_calls": [
            {"key": k, "paradigm": v['paradigm'], "word": v['word']}
            for k, v in list(new_calls.items())[:20]
        ]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {REPORT_FILE}")
    
    print("\n" + "=" * 60)
    print("Step 3 v3 Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
