import argparse
import csv
import json
import os
import re
import sys
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests

import individual_url_scraper as pipeline


MCP_SERVER_PREFIX = "https://mcp.so/server/"


def _raise_csv_field_limit() -> None:
    """Increase CSV field size limit to handle large README fields.

    Python's csv module defaults to 131072 bytes, which is too small for some
    GitHub README content. We bump it to a high value safely.
    """
    target = 50 * 1024 * 1024  # 50MB
    try:
        csv.field_size_limit(target)
        return
    except OverflowError:
        pass
    # Fallback for platforms/builds that can't accept very large ints.
    limit = sys.maxsize
    while limit > 1024 * 1024:
        try:
            csv.field_size_limit(limit)
            return
        except OverflowError:
            limit = limit // 10


def _now() -> float:
    return time.time()


def read_urls(path: str) -> List[str]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        raw_lines = f.read().splitlines()

    urls: List[str] = []
    seen: Set[str] = set()

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
        if not s.startswith(MCP_SERVER_PREFIX):
            continue

        if s not in seen:
            seen.add(s)
            urls.append(s)

    return urls


def load_done_urls_from_csv(csv_path: str) -> Set[str]:
    done: Set[str] = set()
    if not os.path.exists(csv_path):
        return done

    _raise_csv_field_limit()

    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return done
        if "mcp_detail_url" not in (reader.fieldnames or []):
            return done
        for row in reader:
            url = (row.get("mcp_detail_url") or "").strip()
            if url:
                done.add(url)

    return done


def ensure_output_header(csv_path: str) -> None:
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        return

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=pipeline.FIELDNAMES)
        writer.writeheader()


def fetch_html(url: str, session: requests.Session, retries: int = 3, timeout: float = 30.0) -> Tuple[int, str]:
    last_exc: Optional[BaseException] = None

    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout)
            return resp.status_code, resp.text
        except Exception as e:
            last_exc = e
            time.sleep(0.75 * (2**attempt))

    raise RuntimeError(f"Failed to fetch after {retries} tries: {last_exc}")


def append_debug_jsonl(path: str, record: Dict) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def iter_todo_urls(urls: List[str], done: Set[str]) -> Iterable[str]:
    for u in urls:
        if u in done:
            continue
        yield u


def fmt_eta(seconds: float) -> str:
    if seconds <= 0:
        return "0s"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the MCP per-URL scraping pipeline serially, writing to CSV, with resume support by existing CSV rows."
        )
    )
    parser.add_argument(
        "--input",
        default=os.path.join(os.path.dirname(__file__), "mcp_servers_complete.txt"),
        help="Path to the input URL list (one per line)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(__file__), "mcp_all.csv"),
        help="CSV output path",
    )
    parser.add_argument(
        "--debug-jsonl",
        default=os.path.join(os.path.dirname(__file__), "mcp_all_debug.jsonl"),
        help="Append-only JSONL debug log path",
    )
    parser.add_argument(
        "--html-dir",
        default=os.path.join(os.path.dirname(__file__), "html_all"),
        help="Directory to store fetched HTML files (for debugging only; not used for resume)",
    )

    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Start from 0: delete existing output CSV/debug logs before running",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume: skip URLs already present in the output CSV",
    )

    parser.add_argument("--limit", type=int, default=0, help="Process at most this many NEW (not-yet-done) URLs in this run")
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between MCP page requests (seconds)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-request timeout (seconds)")
    parser.add_argument("--retries", type=int, default=3, help="Retries for MCP page fetch")
    parser.add_argument("--progress-every", type=int, default=10, help="Print progress every N processed URLs")

    parser.add_argument(
        "--loop",
        action="store_true",
        help=(
            "Keep running in batches until finished (or until --max-batches). "
            "In loop mode, resume-by-CSV is always enabled; each loop processes --limit URLs per batch (default 250)."
        ),
    )
    parser.add_argument(
        "--batch-sleep",
        type=float,
        default=15.0,
        help="Seconds to sleep between batches when using --loop",
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=0,
        help="Stop after N batches in --loop mode (0 = no limit)",
    )

    args = parser.parse_args()

    if args.fresh:
        for p in [args.output, args.debug_jsonl]:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    urls = read_urls(args.input)
    if not urls:
        print(f"No usable URLs found in: {args.input}")
        return 2

    os.makedirs(args.html_dir, exist_ok=True)
    ensure_output_header(args.output)

    def run_one_batch(batch_no: int, batch_limit: int) -> Tuple[int, int, int]:
        done = load_done_urls_from_csv(args.output) if args.resume else set()
        total = len(urls)
        already_done = len(done)
        remaining_est = max(0, total - already_done)

        if batch_no == 1:
            print(f"Total URLs in list: {total}")
            if args.resume:
                print(f"Already done (from CSV): {already_done}")
                print(f"Remaining (estimated): {remaining_est}")
            else:
                print("Resume disabled: will process in-order from the beginning.")
        else:
            print(f"Batch {batch_no}: already_done={already_done} remaining~={remaining_est}")

        todo_iter = iter_todo_urls(urls, done)

        processed = 0
        success = 0
        failed = 0
        start_ts = _now()

        with open(args.output, "a", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=pipeline.FIELDNAMES)

            for url in todo_iter:
                if batch_limit and processed >= batch_limit:
                    break

                idx_in_run = processed + 1
                debug: List[str] = []
                status_code = 0
                html_path = ""

                try:
                    status_code, html = fetch_html(url, pipeline.session, retries=args.retries, timeout=args.timeout)
                    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", url.replace("https://", "").replace("http://", ""))
                    html_path = os.path.join(args.html_dir, f"{already_done + idx_in_run:05d}_{safe_name}.html")
                    with open(html_path, "w", encoding="utf-8", errors="ignore") as hf:
                        hf.write(html)

                    row = pipeline.extract_server(url, html_path, pipeline.session, debug)
                    writer.writerow(row)
                    success += 1
                except Exception as e:
                    failed += 1
                    debug.append(str(e))
                    row = {k: "" for k in pipeline.FIELDNAMES}
                    row["mcp_detail_url"] = url
                    writer.writerow(row)

                processed += 1

                append_debug_jsonl(
                    args.debug_jsonl,
                    {
                        "ts": int(_now()),
                        "url": url,
                        "status_code": status_code,
                        "html_file": html_path,
                        "debug": debug,
                        "batch": batch_no,
                    },
                )

                if args.progress_every and (processed % args.progress_every == 0):
                    now = _now()
                    elapsed = now - start_ts
                    rate = processed / elapsed if elapsed > 0 else 0.0
                    remaining = max(0, (batch_limit - processed)) if batch_limit else 0
                    eta = (remaining / rate) if (rate > 0 and remaining > 0) else 0
                    msg = (
                        f"[batch {batch_no} | {processed}] ok={success} fail={failed} "
                        f"rate={rate:.2f}/s elapsed={fmt_eta(elapsed)} eta={fmt_eta(eta)} "
                        f"last_status={status_code}"
                    )
                    print(msg)
                    sys.stdout.flush()

                time.sleep(max(0.0, float(args.delay)))

        elapsed_total = _now() - start_ts
        print(
            f"Batch {batch_no} done. Processed={processed} ok={success} fail={failed} elapsed={fmt_eta(elapsed_total)}"
        )
        return processed, success, failed

    if args.loop:
        # Loop mode always needs CSV-based skipping; otherwise each batch would repeat.
        args.resume = True
        if args.limit <= 0:
            args.limit = 250

        batch_no = 0
        while True:
            batch_no += 1
            if args.max_batches and batch_no > args.max_batches:
                print(f"Stopping after max batches: {args.max_batches}")
                break

            processed, ok, fail = run_one_batch(batch_no, batch_limit=args.limit)
            if processed == 0:
                print("No remaining URLs detected; loop complete.")
                break

            if args.batch_sleep > 0:
                print(f"Sleeping {args.batch_sleep:.0f}s before next batch...")
                time.sleep(args.batch_sleep)
    else:
        # Single-run mode (optionally limited)
        run_one_batch(batch_no=1, batch_limit=args.limit)

    print(f"CSV: {args.output}")
    print(f"HTML: {args.html_dir}")
    print(f"Debug JSONL: {args.debug_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
