z``import csv
import re
from pathlib import Path


def main() -> int:
    base = Path(__file__).resolve().parent
    inp = base / "mcp_final_result.csv"
    out = base / "mcp_final_result_sanitized.csv"

    if not inp.exists():
        print(f"Missing input: {inp}")
        return 2

    # Python's splitlines() treats these as line boundaries.
    # Include all common ASCII separators too (FS/GS/RS/US).
    line_sep_chars = "\r\n\u2028\u2029\x0b\x0c\x85\x1c\x1d\x1e\x1f"

    csv.field_size_limit(50 * 1024 * 1024)

    with inp.open(newline="", encoding="utf-8", errors="ignore") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            print("Input CSV has no header")
            return 2

        with out.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(f_out, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            rows = 0
            for row in reader:
                cleaned = {}
                for key in fieldnames:
                    value = row.get(key, "")
                    if value is None:
                        value = ""
                    if not isinstance(value, str):
                        value = str(value)
                    # Replace ALL common line separators with a literal \n sequence.
                    for ch in line_sep_chars:
                        if ch in value:
                            value = value.replace(ch, "\\n")
                    cleaned[key] = value
                writer.writerow(cleaned)
                rows += 1

    # Quick sanity: physical lines should be header + rows.
    physical_lines = out.read_text(encoding="utf-8", errors="ignore").splitlines()
    print(f"wrote_rows={rows}")
    print(f"physical_lines={len(physical_lines)}")
    print(f"output={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
