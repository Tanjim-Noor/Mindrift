"""
Make new API calls for words with changed paradigms and merge into cache.
"""

import json
import requests
import time
from urllib.parse import quote
from pathlib import Path

# Configuration
CHANGED_FILE = Path("changed_paradigms.json")
CACHE_FILE = Path("step3_api_cache.json")
RATE_LIMIT_DELAY = 0.15  # seconds between requests
MAX_RETRIES = 3

def make_api_call(paradigm: str, word: str) -> dict:
    """Make a single API call with retries."""
    encoded_word = quote(word, safe='')
    url = f"https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{paradigm}/{encoded_word}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return {'url': url, 'data': response.json(), 'status': 'success'}
            else:
                return {'url': url, 'data': None, 'status': f'error_{response.status_code}'}
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
            else:
                return {'url': url, 'data': None, 'status': f'exception: {str(e)}'}
    
    return {'url': url, 'data': None, 'status': 'max_retries'}


def main():
    print("=" * 60)
    print("Making API Calls for Changed Paradigms")
    print("=" * 60)
    
    # Load changed paradigms
    with open(CHANGED_FILE, 'r', encoding='utf-8') as f:
        changed = json.load(f)
    print(f"  Loaded {len(changed)} words with changed paradigms")
    
    # Load existing cache
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        cache = json.load(f)
    print(f"  Existing cache: {len(cache)} entries")
    
    # Make new API calls
    print("\n--- Making API Calls ---")
    success_count = 0
    error_count = 0
    
    for i, item in enumerate(changed):
        word = item['ord']
        new_paradigm = item['new_paradigm']
        
        # Check if already in cache
        encoded_word = quote(word, safe='')
        url = f"https://spraakbanken.gu.se/ws/saldo-ws/gen/json/{new_paradigm}/{encoded_word}"
        
        if url in cache:
            print(f"  [{i+1}/{len(changed)}] {word}: Already cached")
            continue
        
        # Make API call
        result = make_api_call(new_paradigm, word)
        
        if result['status'] == 'success':
            cache[result['url']] = result['data']
            success_count += 1
            print(f"  [{i+1}/{len(changed)}] {word}: Success")
        else:
            cache[result['url']] = "NULL"
            error_count += 1
            print(f"  [{i+1}/{len(changed)}] {word}: {result['status']}")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        # Progress every 50
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{len(changed)} ({(i+1)/len(changed)*100:.1f}%)")
    
    # Save updated cache
    print("\n--- Saving Cache ---")
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)
    
    print(f"\n  Updated cache: {len(cache)} entries")
    print(f"  New successful calls: {success_count}")
    print(f"  Errors: {error_count}")
    print("\nDone!")


if __name__ == '__main__':
    main()
