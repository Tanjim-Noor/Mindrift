import argparse
import csv
import json
import os
import random
import re
import time
from typing import List, Tuple

import requests

import individual_url_scraper as pipeline


MCP_SERVER_PREFIX = "https://mcp.so/server/"


def read_urls(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.read().splitlines()

    urls: List[str] = []
    seen = set()

    for line in raw_lines:
        s = (line or "").strip()
        if not s:
            continue

        # Fix known extraction artifact: whitespace inside the URL path.
        # Example: "https://mcp.so/server/ image-tools-mcp/kshern"
        if MCP_SERVER_PREFIX in s and re.search(r"\s", s):
            s = re.sub(r"\s+", "", s)

        if not s.startswith("http"):
            continue
        if MCP_SERVER_PREFIX not in s:
            continue

        # Normalize trailing whitespace/slash
        s = s.strip()

        if s not in seen:
            seen.add(s)
            urls.append(s)

    return urls


def fetch_html(url: str, session: requests.Session, retries: int = 3, timeout: float = 30.0) -> Tuple[int, str]:
    last_exc = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout)
            return resp.status_code, resp.text
        except Exception as e:
            last_exc = e
            time.sleep(0.75 * (2**attempt))
    raise RuntimeError(f"Failed to fetch after {retries} tries: {last_exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP per-URL pipeline for a small sample and output a CSV")
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "mcp_servers_complete.txt"),
        help="Path to the input URL list (one per line)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "mcp_sample_100.csv"),
        help="CSV output path",
    )
    parser.add_argument("--count", type=int, default=100, help="Number of URLs to process")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests (seconds)")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle URLs before sampling")
    parser.add_argument("--seed", type=int, default=1337, help="Random seed when using --shuffle")
    parser.add_argument(
        "--html-dir",
        default=os.path.join(os.path.dirname(__file__), "html_samples"),
        help="Directory to store fetched HTML files",
    )
    parser.add_argument(
        "--debug-json",
        default=os.path.join(os.path.dirname(__file__), "mcp_sample_100_debug.json"),
        help="Where to write debug info (JSON)",
    )

    args = parser.parse_args()

    urls = read_urls(args.input)
    if not urls:
        raise SystemExit(f"No usable URLs found in: {args.input}")

    if args.shuffle:
        rng = random.Random(args.seed)
        rng.shuffle(urls)

    sample = urls[: max(0, args.count)]

    os.makedirs(args.html_dir, exist_ok=True)

    debug_records = []

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=pipeline.FIELDNAMES)
        writer.writeheader()

        for idx, url in enumerate(sample, start=1):
            debug: List[str] = []
            status_code = 0
            html_path = ""

            try:
                status_code, html = fetch_html(url, pipeline.session)
                safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.replace("https://", "").replace("http://", ""))
                html_path = os.path.join(args.html_dir, f"{idx:03d}_{safe_name}.html")
                with open(html_path, "w", encoding="utf-8", errors="ignore") as hf:
                    hf.write(html)

                row = pipeline.extract_server(url, html_path, pipeline.session, debug)
            except Exception as e:
                debug.append(str(e))
                row = {k: "" for k in pipeline.FIELDNAMES}
                row["mcp_detail_url"] = url

            writer.writerow(row)

            debug_records.append(
                {
                    "index": idx,
                    "url": url,
                    "status_code": status_code,
                    "html_file": html_path,
                    "debug": debug,
                }
            )

            time.sleep(max(0.0, float(args.delay)))

    try:
        with open(args.debug_json, "w", encoding="utf-8") as jf:
            json.dump(debug_records, jf, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(f"Wrote CSV: {args.output}")
    print(f"Saved HTML under: {args.html_dir}")
    print(f"Wrote debug JSON: {args.debug_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
