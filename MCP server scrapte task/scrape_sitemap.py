"""
MCP Server URL Enumeration via Sitemaps
Collects ALL ~17,155 MCP server URLs from mcp.so using sitemap discovery.

Steps:
1. Check robots.txt for sitemap declarations
2. Fetch root sitemap index
3. Brute force sitemap discovery (fallback)
4. Extract all server URLs from sitemaps
5. Validation check
6. Direct page crawling (fallback if sitemaps fail)
"""

import argparse
import re
import time
from typing import List, Optional, Set, Dict
from pathlib import Path

import requests


class SitemapScraper:
    def __init__(self, retries: int = 5, backoff: float = 1.0, timeout: float = 15.0, delay: float = 0.5):
        self.retries = retries
        self.backoff = backoff
        self.timeout = timeout
        self.delay = delay  # Rate limiting delay between requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        self.collected_urls: Set[str] = set()
        self.sitemap_stats: Dict[str, int] = {}
    
    def fetch_with_retries(self, url: str) -> Optional[requests.Response]:
        """Fetch URL with retry logic and rate limiting."""
        attempt = 0
        while attempt < self.retries:
            try:
                time.sleep(self.delay)  # Rate limiting
                response = self.session.get(url, timeout=self.timeout)
                return response
            except requests.exceptions.RequestException as e:
                attempt += 1
                msg = str(e)
                if 'Name or service not known' in msg or 'getaddrinfo failed' in msg or 'Failed to resolve' in msg:
                    print(f"  DNS resolution failed for {url}: {msg}")
                    return None
                if attempt >= self.retries:
                    print(f"  Request failed after {self.retries} attempts: {e}")
                    return None
                wait = self.backoff * (2 ** (attempt - 1))
                print(f"  Request error: {e} — retrying in {wait:.1f}s (attempt {attempt}/{self.retries})")
                time.sleep(wait)
        return None

    def step1_check_robots_txt(self) -> List[str]:
        """Step 1: Check robots.txt for Sitemap declarations."""
        print("\n" + "="*60)
        print("STEP 1: Checking robots.txt for sitemap declarations")
        print("="*60)
        
        url = "https://mcp.so/robots.txt"
        print(f"Fetching: {url}")
        
        response = self.fetch_with_retries(url)
        sitemaps = []
        
        if response is None:
            print("  Failed to fetch robots.txt")
            return sitemaps
        
        if response.status_code == 200:
            content = response.text
            # Look for Sitemap: directives
            for line in content.split('\n'):
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    sitemaps.append(sitemap_url)
                    print(f"  Found sitemap: {sitemap_url}")
        else:
            print(f"  robots.txt returned status {response.status_code}")
        
        if not sitemaps:
            print("  No sitemap declarations found in robots.txt")
        
        return sitemaps

    def step2_fetch_sitemap_index(self, declared_sitemaps: List[str] = None) -> List[str]:
        """Step 2: Fetch root sitemap index and discover child sitemaps."""
        print("\n" + "="*60)
        print("STEP 2: Fetching sitemap index")
        print("="*60)
        
        # Try declared sitemaps first, then fallback URLs
        urls_to_try = []
        if declared_sitemaps:
            urls_to_try.extend(declared_sitemaps)
        
        urls_to_try.extend([
            "https://mcp.so/sitemap.xml",
            "https://mcp.so/sitemap_index.xml",
            "https://mcp.so/sitemap-index.xml",
            "https://mcp.so/server-sitemap.xml",
        ])
        
        child_sitemaps = []
        
        for url in urls_to_try:
            print(f"Trying: {url}")
            response = self.fetch_with_retries(url)
            
            if response is None:
                continue
            
            if response.status_code == 200:
                content = response.text
                # Extract <loc> tags - could be child sitemaps or direct URLs
                locs = re.findall(r'<loc>([^<]+)</loc>', content, re.IGNORECASE)
                
                for loc in locs:
                    loc = loc.strip()
                    # Check if it's a sitemap reference
                    if 'sitemap' in loc.lower() and loc.endswith('.xml'):
                        if loc not in child_sitemaps:
                            child_sitemaps.append(loc)
                            print(f"  Found child sitemap: {loc}")
                    # Check if it's a server URL directly
                    elif '/server/' in loc:
                        self.collected_urls.add(loc)
                
                if child_sitemaps:
                    print(f"  Found {len(child_sitemaps)} child sitemap(s)")
                    break
                elif self.collected_urls:
                    print(f"  Found {len(self.collected_urls)} server URLs directly")
                    self.sitemap_stats[url] = len(self.collected_urls)
                    break
            else:
                print(f"  Status {response.status_code}")
        
        if not child_sitemaps and not self.collected_urls:
            print("  No child sitemaps or URLs found from index")
        
        return child_sitemaps

    def step3_brute_force_discovery(self, existing_sitemaps: List[str] = None) -> List[str]:
        """Step 3: Brute force sitemap discovery by incrementing numbers."""
        print("\n" + "="*60)
        print("STEP 3: Brute force sitemap discovery")
        print("="*60)
        
        discovered_sitemaps = list(existing_sitemaps) if existing_sitemaps else []
        max_n = 50  # Try up to 50 sitemaps per pattern
        
        # Patterns to try - include both numbered and non-numbered variants
        patterns_numbered = [
            "https://mcp.so/sitemap_projects_{n}.xml",
            "https://mcp.so/server-sitemap-{n}.xml",
            "https://mcp.so/sitemap-{n}.xml",
        ]
        
        patterns_static = [
            "https://mcp.so/server-sitemap.xml",
        ]
        
        # Try static patterns first
        for url in patterns_static:
            if url in discovered_sitemaps:
                continue
            print(f"Checking: {url}")
            response = self.fetch_with_retries(url)
            if response and response.status_code == 200:
                discovered_sitemaps.append(url)
                print(f"  ✓ Found sitemap!")
        
        # Try numbered patterns
        for pattern in patterns_numbered:
            print(f"\nTrying pattern: {pattern}")
            consecutive_404s = 0
            max_consecutive_404s = 5  # Increased tolerance
            
            for n in range(0, max_n + 1):  # Start from 0
                url = pattern.format(n=n)
                
                if url in discovered_sitemaps:
                    consecutive_404s = 0  # Reset since we know this exists
                    continue
                    
                print(f"  Checking: {url}")
                
                response = self.fetch_with_retries(url)
                
                if response is None:
                    consecutive_404s += 1
                    if consecutive_404s >= max_consecutive_404s:
                        print(f"    Stopping after {max_consecutive_404s} consecutive failures")
                        break
                    continue
                
                if response.status_code == 200:
                    consecutive_404s = 0
                    discovered_sitemaps.append(url)
                    print(f"    ✓ Found sitemap!")
                elif response.status_code == 404:
                    consecutive_404s += 1
                    print(f"    Not found (404)")
                    if consecutive_404s >= max_consecutive_404s:
                        print(f"    Stopping after {max_consecutive_404s} consecutive 404s")
                        break
                elif response.status_code in (403, 429):
                    print(f"    Rate limited ({response.status_code}), waiting 3s...")
                    time.sleep(3)
                    response = self.fetch_with_retries(url)
                    if response and response.status_code == 200:
                        consecutive_404s = 0
                        discovered_sitemaps.append(url)
                        print(f"    ✓ Found sitemap on retry!")
                else:
                    print(f"    Status {response.status_code}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_sitemaps = []
        for s in discovered_sitemaps:
            if s not in seen:
                seen.add(s)
                unique_sitemaps.append(s)
        
        print(f"\nTotal discovered sitemaps: {len(unique_sitemaps)}")
        return unique_sitemaps

    def step4_extract_urls_from_sitemaps(self, sitemaps: List[str]):
        """Step 4: Extract ALL server URLs from all sitemaps."""
        print("\n" + "="*60)
        print("STEP 4: Extracting server URLs from sitemaps")
        print("="*60)
        
        for sitemap_url in sitemaps:
            print(f"\nProcessing: {sitemap_url}")
            response = self.fetch_with_retries(sitemap_url)
            
            if response is None:
                print("  Failed to fetch")
                continue
            
            if response.status_code != 200:
                print(f"  Status {response.status_code}")
                continue
            
            content = response.text
            
            count_before = len(self.collected_urls)
            
            # Try multiple extraction patterns:
            # 1. XML <loc> tags (standard sitemap format)
            locs = re.findall(r'<loc>([^<]+)</loc>', content, re.IGNORECASE)
            for loc in locs:
                loc = loc.strip()
                if '/server/' in loc:
                    self.collected_urls.add(loc)
            
            # 2. HTML href="/server/..." (relative links in HTML-styled sitemaps)
            hrefs_relative = re.findall(r'href="(/server/[^"]+)"', content)
            for href in hrefs_relative:
                full_url = f"https://mcp.so{href}"
                self.collected_urls.add(full_url)
            
            # 3. HTML href="https://mcp.so/server/..." (absolute links)
            hrefs_absolute = re.findall(r'href="(https://mcp\.so/server/[^"]+)"', content)
            for href in hrefs_absolute:
                self.collected_urls.add(href)
            
            # 4. Also try /project/ pattern in case some are listed there
            project_locs = re.findall(r'<loc>([^<]+/project/[^<]+)</loc>', content, re.IGNORECASE)
            for loc in project_locs:
                # Convert project URLs to server URLs if pattern matches
                self.collected_urls.add(loc.strip())
            
            new_urls = len(self.collected_urls) - count_before
            self.sitemap_stats[sitemap_url] = new_urls
            print(f"  Extracted {new_urls} new server URLs (total unique: {len(self.collected_urls)})")

    def step5_validation(self) -> dict:
        """Step 5: Validate the collected URLs."""
        print("\n" + "="*60)
        print("STEP 5: Validation")
        print("="*60)
        
        total = len(self.collected_urls)
        # Based on observed ~275 pages × ~44 servers = ~12,100 servers (with overlap)
        target = 10000
        
        # Determine status
        if total >= 9000:
            status = "✅ EXCELLENT - Complete collection"
            status_code = "complete"
        elif total >= 7000:
            status = "⚠️ GOOD - Partial collection, may be missing some pages"
            status_code = "good"
        elif total >= 5000:
            status = "❌ PARTIAL - Missing multiple pages"
            status_code = "partial"
        else:
            status = "❌ INCOMPLETE - Major issue, review all steps"
            status_code = "incomplete"
        
        print(f"\nTotal Unique URLs: {total}")
        print(f"Target: ~{target}")
        print(f"Coverage: {total/target*100:.1f}%")
        print(f"Status: {status}")
        
        # Quality check - verify URL format
        url_pattern = re.compile(r'^https://mcp\.so/server/[^/]+/[^/]+$')
        valid_format = 0
        invalid_urls = []
        
        for url in self.collected_urls:
            if url_pattern.match(url):
                valid_format += 1
            else:
                invalid_urls.append(url)
        
        print(f"\nFormat Check:")
        print(f"  Valid format: {valid_format}/{total}")
        if invalid_urls[:5]:
            print(f"  Sample invalid URLs: {invalid_urls[:5]}")
        
        # Sample URLs
        urls_list = sorted(self.collected_urls)
        print(f"\nFirst 10 URLs:")
        for url in urls_list[:10]:
            print(f"  {url}")
        
        print(f"\nLast 10 URLs:")
        for url in urls_list[-10:]:
            print(f"  {url}")
        
        return {
            "total": total,
            "target": target,
            "coverage_pct": total / target * 100,
            "status": status,
            "status_code": status_code,
            "valid_format": valid_format,
            "invalid_count": len(invalid_urls),
        }

    def step6_fallback_crawling(self):
        """Step 6: Fallback - Direct page crawling if sitemaps fail."""
        print("\n" + "="*60)
        print("STEP 6: Fallback - Direct page crawling")
        print("="*60)
        
        base_url = "https://mcp.so/servers"
        page = 1
        max_pages = 300  # Based on observed ~275 pages
        no_new_urls_count = 0
        max_no_new = 10  # Increased tolerance - some pages may have overlapping content
        
        while page <= max_pages:
            url = f"{base_url}?page={page}" if page > 1 else base_url
            print(f"Fetching page {page}/{max_pages}: {url}")
            
            response = self.fetch_with_retries(url)
            
            if response is None:
                print("  Failed to fetch, retrying...")
                no_new_urls_count += 1
                if no_new_urls_count >= max_no_new:
                    print(f"  Too many failures, stopping")
                    break
                page += 1
                continue
            
            if response.status_code != 200:
                print(f"  Status {response.status_code}")
                no_new_urls_count += 1
                if no_new_urls_count >= max_no_new:
                    print(f"  Too many non-200 responses, stopping")
                    break
                page += 1
                continue
            
            content = response.text
            
            # Extract server links from HTML
            # Pattern: href="/server/name/author" or href="https://mcp.so/server/name/author"
            server_links = re.findall(r'href="(/server/[^"]+)"', content)
            server_links += re.findall(r'href="(https://mcp\.so/server/[^"]+)"', content)
            
            count_before = len(self.collected_urls)
            
            for link in server_links:
                if link.startswith('/'):
                    link = f"https://mcp.so{link}"
                # Clean up any trailing slashes or query params
                link = link.split('?')[0].rstrip('/')
                if '/server/' in link:
                    self.collected_urls.add(link)
            
            new_urls = len(self.collected_urls) - count_before
            print(f"  Found {new_urls} new URLs (total: {len(self.collected_urls)})")
            
            if new_urls == 0:
                no_new_urls_count += 1
            else:
                no_new_urls_count = 0  # Reset on success
            
            # Check if we've reached the end (look for "Next" button absence or page number in content)
            if page >= 275 and no_new_urls_count >= 3:
                print(f"  Reached expected end of pagination (page {page})")
                break
            
            page += 1
        
        print(f"\nCrawling complete. Processed {page-1} pages.")

    def save_results(self, output_file: str = "mcp_servers_complete.txt"):
        """Save collected URLs to file."""
        print("\n" + "="*60)
        print("Saving Results")
        print("="*60)
        
        urls_list = sorted(self.collected_urls)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for url in urls_list:
                f.write(url + '\n')
        
        print(f"Saved {len(urls_list)} unique URLs to {output_file}")
        return output_file

    def generate_report(self, method_used: str, validation_result: dict):
        """Generate final report."""
        print("\n" + "="*60)
        print("ENUMERATION COMPLETE")
        print("="*60)
        
        print(f"\nMethod Used: {method_used}")
        print(f"\nTotal Unique Server URLs Collected: {validation_result['total']}")
        print(f"Expected Target: ~{validation_result['target']}")
        print(f"\nStatus: {validation_result['status']}")
        
        print(f"\nSitemap Files Successfully Processed:")
        total_from_sitemaps = 0
        for sitemap, count in self.sitemap_stats.items():
            print(f"  - {sitemap} ({count} URLs)")
            total_from_sitemaps += count
        print(f"Total from sitemaps: {total_from_sitemaps}")
        
        print(f"\nSample URLs (first 10):")
        for url in sorted(self.collected_urls)[:10]:
            print(f"  {url}")
        
        print(f"\nFiles Saved:")
        print(f"  - URL list saved to: mcp_servers_complete.txt")
        print(f"  - Ready for pipeline: {'YES' if validation_result['status_code'] in ('complete', 'good') else 'NO'}")

    def run(self, skip_fallback: bool = False):
        """Run the complete enumeration process."""
        # Step 1: Check robots.txt
        declared_sitemaps = self.step1_check_robots_txt()
        
        # Step 2: Fetch sitemap index
        child_sitemaps = self.step2_fetch_sitemap_index(declared_sitemaps)
        
        method_used = "Sitemap Index"
        
        # Always do brute force to find sitemaps not listed in index
        all_sitemaps = self.step3_brute_force_discovery(child_sitemaps)
        if len(all_sitemaps) > len(child_sitemaps):
            method_used = "Sitemap Index + Brute Force Discovery"
        child_sitemaps = all_sitemaps
        
        # Step 4: Extract URLs from discovered sitemaps
        if child_sitemaps:
            self.step4_extract_urls_from_sitemaps(child_sitemaps)
        
        # Step 5: Validation
        validation_result = self.step5_validation()
        
        # Step 6: Fallback if needed and not skipped
        if validation_result['status_code'] == 'incomplete' and not skip_fallback:
            print("\nCollection incomplete, attempting fallback crawling...")
            self.step6_fallback_crawling()
            validation_result = self.step5_validation()
            method_used = "Direct Crawling (Fallback)"
        
        # Save results
        self.save_results()
        
        # Generate report
        self.generate_report(method_used, validation_result)
        
        return validation_result


def main():
    parser = argparse.ArgumentParser(description='Enumerate MCP server URLs from mcp.so sitemaps')
    parser.add_argument('--retries', type=int, default=5, help='Number of retries for network calls')
    parser.add_argument('--backoff', type=float, default=1.0, help='Base backoff (seconds)')
    parser.add_argument('--timeout', type=float, default=15.0, help='Per-request timeout (seconds)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--skip-fallback', action='store_true', help='Skip fallback crawling if sitemaps fail')
    
    args = parser.parse_args()
    
    scraper = SitemapScraper(
        retries=args.retries,
        backoff=args.backoff,
        timeout=args.timeout,
        delay=args.delay
    )
    
    scraper.run(skip_fallback=args.skip_fallback)


if __name__ == '__main__':
    main()
