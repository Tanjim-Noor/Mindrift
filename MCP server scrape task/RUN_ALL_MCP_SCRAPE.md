# Run All MCP Server URLs → CSV (Serial + Resume)

This folder contains a serial scraper that reads URLs from `mcp_servers_complete.txt`, fetches each MCP detail page, extracts fields, and appends rows to a CSV.

The scraper supports:
- **Fresh start** (delete old outputs and start from URL 0)
- **Resume from CSV** (skip URLs already written to the output CSV)
- **Batching** (process N new URLs per run)
- **Auto-batch loop** (run batch after batch automatically)
- **Terminal progress** (prints rate/ETA every N URLs)

## What You Run

Main runner:
- `run_pipeline_all.py` — scrape all URLs serially into one CSV, with optional resume.

Input:
- `mcp_servers_complete.txt` — the URL list (one per line).

Pipeline:
- `individual_url_scraper.py` — contains the extraction logic (`extract_server`) and the CSV schema (`FIELDNAMES`).

## Outputs

Default output files (created in this folder):
- `mcp_all.csv` — append-only CSV containing one row per URL (including failures as blank rows with only `mcp_detail_url`).
- `mcp_all_debug.jsonl` — append-only debug log, one JSON object per URL. Includes HTTP status code and any exceptions.
- `html_all/` — saved HTML snapshots for each fetched MCP page (for debugging only).

## One-time Setup

Make sure the workspace venv is active and required packages are installed.

If you already used the sample run, your venv should already have these, but if not:

- Activate venv (PowerShell):
  - `D:/Work/Mindrift/.venv/Scripts/Activate.ps1`
- Install deps:
  - `D:/Work/Mindrift/.venv/Scripts/python.exe -m pip install beautifulsoup4 langid requests`

## Commands (Most Common)

### 1) Start from 0 (fresh run)

Deletes existing `mcp_all.csv` and `mcp_all_debug.jsonl`, then starts from the first URL in `mcp_servers_complete.txt`.

- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --fresh --progress-every 10 --delay 0.35`

### 2) Resume (skip already-scraped URLs)

Reads `mcp_all.csv`, collects all `mcp_detail_url` values, and skips those URLs on the next run.

- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --resume --progress-every 10 --delay 0.35`

### 3) Run in batches (recommended)

Processes only N *new* URLs per invocation (useful for long jobs, restarts, or cautious throttling).

Example: process 250 new URLs per run:
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --resume --limit 250 --progress-every 10 --delay 0.35`

Repeat the batch command until it reports there is nothing left to do.

### 4) Fully automated continuous batching (no manual re-run)

If you don’t want to manually run the batch command thousands of times, use `--loop`.

In `--loop` mode:
- The script runs a batch of `--limit` URLs, then sleeps for `--batch-sleep` seconds, then starts the next batch.
- **Resume-by-CSV is always enabled** (each new batch re-reads the CSV and skips URLs already present).
- It stops automatically when there are no remaining URLs.

Start fresh and run continuously until done (recommended):
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --fresh --loop --limit 250 --batch-sleep 15 --progress-every 10 --delay 0.35`

If you want to stop after a certain number of batches (useful for overnight runs):
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --fresh --loop --limit 250 --max-batches 20 --batch-sleep 15 --progress-every 10 --delay 0.35`

## Progress Output (What It Means)

Every `--progress-every N` processed URLs, the runner prints a line like:

- `[120] ok=118 fail=2 rate=0.41/s elapsed=4m 52s eta=1h 10m last_status=200`

Fields:
- `[...]` — number processed *in this run* (not total in file).
- `ok` / `fail` — success/failure count in this run.
- `rate` — URLs/second.
- `elapsed` — runtime so far.
- `eta` — estimated time remaining (based on current rate).
- `last_status` — last MCP page HTTP status code.

## All Flags (Full Reference)

- `--input PATH`
  - URL list file. Default: `mcp_servers_complete.txt`
- `--output PATH`
  - Output CSV path. Default: `mcp_all.csv`
- `--debug-jsonl PATH`
  - Debug log path (JSON Lines). Default: `mcp_all_debug.jsonl`
- `--html-dir DIR`
  - Where to store fetched HTML files. Default: `html_all/`

Mode flags (choose one):
- `--fresh`
  - Deletes existing output CSV/debug logs and starts from 0.
- `--resume`
  - Reads output CSV and skips already completed URLs.

Automation flags:
- `--loop`
  - Automatically runs batch after batch until finished.
  - Forces resume-by-CSV internally (so each batch continues where the CSV left off).
- `--batch-sleep SECONDS`
  - Sleep between batches in `--loop` mode. Default: `15`.
- `--max-batches N`
  - Stop after N batches in `--loop` mode. Default: `0` (no limit).

Runtime flags:
- `--limit N`
  - Process at most N new URLs in this run (batching). Default: `0` (no limit).
- `--delay SECONDS`
  - Sleep between MCP URL fetches. Default: `0.35`
- `--timeout SECONDS`
  - Per-request timeout for MCP page fetch. Default: `30`
- `--retries N`
  - Retries for MCP page fetch. Default: `3`
- `--progress-every N`
  - Print progress every N processed URLs. Default: `10`

## How To Complete The Full Process (End-to-End)

Recommended approach:

1) Do a small smoke test (10 URLs):
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --fresh --limit 10 --progress-every 1 --delay 0.35`

2) Start the automated run (fresh + continuous batching) and let it complete:
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --fresh --loop --limit 250 --batch-sleep 15 --progress-every 10 --delay 0.35`

3) If the process stops (network/rate limits/reboot), just resume with loop:
- `D:/Work/Mindrift/.venv/Scripts/python.exe "D:/Work/Mindrift/MCP server scrape task/run_pipeline_all.py" --loop --limit 250 --batch-sleep 15 --progress-every 10 --delay 0.35`

4) When finished, `mcp_all.csv` is your final CSV.

## Notes / Troubleshooting

- GitHub calls can be the slowest part of this pipeline:
  - If the MCP page contains a GitHub link, `individual_url_scraper.py` will fetch GitHub to parse stars and attempt to fetch `README.md` from `raw.githubusercontent.com`.
  - If you hit GitHub rate limits or many 403/429 responses, increase `--delay`.

- Resume behavior is CSV-based (by design):
  - We do **not** resume via cached HTML, so there is no “HTML mapping” dependency.

- If you see `_csv.Error: field larger than field limit (131072)` while resuming:
  - This happens when the `readme` column contains large README content.
  - The runner now increases the CSV field-size limit automatically.
  - Re-run the same command without `--fresh` (so it resumes from the existing CSV).

- Some MCP URLs may return 404:
  - The script still writes a row (so the URL is considered done on resume), and the HTTP status/error is stored in `mcp_all_debug.jsonl`.
