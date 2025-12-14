import argparse
import json
import time
from typing import Optional

import requests


def fetch_with_retries(url: str, retries: int = 5, backoff: float = 1.0, timeout: float = 10.0) -> Optional[requests.Response]:
    session = requests.Session()
    attempt = 0
    while attempt < retries:
        try:
            return session.get(url, timeout=timeout)
        except requests.exceptions.RequestException as e:
            attempt += 1
            # Detect DNS/name resolution problems
            msg = str(e)
            if 'Name or service not known' in msg or 'getaddrinfo failed' in msg or 'Failed to resolve' in msg:
                print(f"DNS resolution failed for {url}: {msg}")
                print("  - Check your network connection, DNS settings, or that the host is reachable.")
                return None
            if attempt >= retries:
                print(f"Request failed after {retries} attempts: {e}")
                return None
            wait = backoff * (2 ** (attempt - 1))
            print(f"Request error: {e} — retrying in {wait:.1f}s (attempt {attempt}/{retries})")
            time.sleep(wait)


def main(base_url: str, retries: int, backoff: float, timeout: float):
    all_servers = []
    cursor = None

    while True:
        url = base_url if not cursor else f"{base_url}?cursor={cursor}"

        print(f"Fetching: {url}")
        response = fetch_with_retries(url, retries=retries, backoff=backoff, timeout=timeout)
        if response is None:
            print("Aborting due to previous error.")
            break

        if response.status_code != 200:
            print(f"Error: {response.status_code} when fetching {url}")
            break

        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from {url}: {e}")
            break

        # Response structure: {"servers": [{"server": {...}, "_meta": {...}}, ...], "metadata": {...}}
        servers = data.get('servers', [])
        all_servers.extend(servers)

        print(f"  Got {len(servers)} servers (total: {len(all_servers)})")

        next_cursor = data.get('metadata', {}).get('nextCursor')
        if not next_cursor:
            break

        cursor = next_cursor

    print(f"\nTotal servers: {len(all_servers)}")

    # Convert to mcp.so URLs
    # Server name format: "namespace/server-name" e.g., "ai.aliengiraffe/spotdb"
    mcp_urls = []
    for item in all_servers:
        server = item.get('server', {})
        name = server.get('name', '')
        if name and '/' in name:
            # name format: "namespace/server-name" -> extract parts
            parts = name.split('/')
            if len(parts) >= 2:
                author = parts[0]  # e.g., "ai.aliengiraffe"
                server_name = '/'.join(parts[1:])  # e.g., "spotdb"
                mcp_urls.append(f"https://mcp.so/server/{server_name}/{author}")

    print(f"Total mcp.so URLs: {len(mcp_urls)}")

    # Save
    if mcp_urls:
        with open('mcp_servers_complete.txt', 'w') as f:
            for url in mcp_urls:
                f.write(url + '\n')

        print("Done! URLs saved to mcp_servers_complete.txt")
    else:
        print("No URLs to save.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fetch MCP registry servers and save mcp.so URLs')
    parser.add_argument('--base-url', default='https://registry.modelcontextprotocol.io/v0/servers', help='Base registry URL')
    parser.add_argument('--retries', type=int, default=5, help='Number of retries for network calls')
    parser.add_argument('--backoff', type=float, default=1.0, help='Base backoff (seconds)')
    parser.add_argument('--timeout', type=float, default=10.0, help='Per-request timeout (seconds)')

    args = parser.parse_args()
    main(args.base_url, args.retries, args.backoff, args.timeout)