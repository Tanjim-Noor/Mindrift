import csv
import re
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    inp = base / "mcp_servers_complete.txt"
    out = base / "mcp_all.csv"

    if not inp.exists():
        print(f"Missing input file: {inp}")
        return 2
    if not out.exists():
        print(f"Missing output CSV: {out}")
        return 2

    urls = set()
    for line in inp.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = (line or "").strip()
        if not s.startswith("https://mcp.so/server/"):
            continue
        s = re.sub(r"\s+", "", s)
        if s:
            urls.add(s)

    # Handle large README fields.
    csv.field_size_limit(50 * 1024 * 1024)

    done = set()
    with out.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = (row.get("mcp_detail_url") or "").strip()
            if u:
                done.add(u)

    missing = urls - done

    print(f"input_unique={len(urls)}")
    print(f"csv_unique={len(done)}")
    print(f"missing={len(missing)}")
    if missing:
        print(f"missing_example={next(iter(missing))}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
