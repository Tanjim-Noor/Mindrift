"""
Step 1: Parse and Validate JSON Structure
==========================================
Load Lexikon.json, verify metadata schema, and identify the 3-field format
across all entries. Count total word entries and log anomalies.
"""

import json
from pathlib import Path
from collections import Counter
from typing import Any

# Configuration
INPUT_FILE = Path("Lexikon.json")
OUTPUT_REPORT = Path("step1_validation_report.json")


def load_json_file(filepath: Path) -> list:
    """Load and parse the JSON file."""
    print(f"Loading {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  Loaded successfully. Type: {type(data).__name__}")
    return data


def validate_metadata(metadata: dict) -> dict:
    """Validate the metadata object (first element) containing schema definition."""
    validation = {
        "is_valid": True,
        "info": None,
        "field_mapping": [],
        "errors": []
    }
    
    # Check for 'info' field
    if "info" in metadata:
        validation["info"] = metadata["info"]
        print(f"  Metadata info: {metadata['info']}")
    else:
        validation["errors"].append("Missing 'info' field in metadata")
        validation["is_valid"] = False
    
    # Check for 'map' field
    if "map" in metadata:
        validation["field_mapping"] = metadata["map"]
        print(f"  Field mapping:")
        for field in metadata["map"]:
            print(f"    - {field}")
    else:
        validation["errors"].append("Missing 'map' field in metadata")
        validation["is_valid"] = False
    
    # Validate expected field structure
    expected_fields = ["0:ord", "1:glosa"]
    for expected in expected_fields:
        if expected not in metadata.get("map", []):
            validation["errors"].append(f"Missing expected field mapping: {expected}")
            validation["is_valid"] = False
    
    return validation


def validate_entry(entry: Any, index: int) -> dict:
    """Validate a single entry follows [ord, glosa, varianter_array] structure."""
    result = {
        "index": index,
        "is_valid": True,
        "entry_type": type(entry).__name__,
        "field_count": 0,
        "ord": None,
        "has_glosa": False,
        "has_varianter": False,
        "errors": []
    }
    
    # Check if entry is a list
    if not isinstance(entry, list):
        result["is_valid"] = False
        result["errors"].append(f"Entry is not a list, got {type(entry).__name__}")
        return result
    
    result["field_count"] = len(entry)
    
    # Check field count (should be 3)
    if len(entry) != 3:
        result["errors"].append(f"Expected 3 fields, got {len(entry)}")
        # Don't mark as invalid if empty list (seems to be placeholder)
        if len(entry) == 0:
            result["is_empty"] = True
            return result
    
    # Extract and validate field 0 (ord)
    if len(entry) >= 1:
        result["ord"] = entry[0]
        if entry[0] is not None and not isinstance(entry[0], str):
            result["errors"].append(f"Field 0 (ord) should be string, got {type(entry[0]).__name__}")
    
    # Check field 1 (glosa)
    if len(entry) >= 2:
        result["has_glosa"] = entry[1] is not None
    
    # Check field 2 (varianter array)
    if len(entry) >= 3:
        result["has_varianter"] = isinstance(entry[2], list) and len(entry[2]) > 0
        if not isinstance(entry[2], list):
            result["errors"].append(f"Field 2 (varianter) should be list, got {type(entry[2]).__name__}")
    
    # Entry is valid if no critical errors
    result["is_valid"] = len([e for e in result["errors"] if "should be" in e]) == 0
    
    return result


def analyze_entries(data: list) -> dict:
    """Analyze all entries (excluding metadata) for structure validation."""
    print("\nAnalyzing entries...")
    
    # Skip first element (metadata)
    entries = data[1:]
    total_entries = len(entries)
    print(f"  Total entries (excluding metadata): {total_entries}")
    
    # Validation results
    results = {
        "total_entries": total_entries,
        "valid_entries": 0,
        "empty_entries": 0,
        "invalid_entries": 0,
        "entries_with_ord": 0,
        "entries_with_glosa": 0,
        "entries_with_varianter": 0,
        "field_count_distribution": Counter(),
        "anomalies": [],
        "sample_entries": []
    }
    
    for i, entry in enumerate(entries):
        validation = validate_entry(entry, i + 1)  # 1-indexed for human readability
        
        results["field_count_distribution"][validation["field_count"]] += 1
        
        if validation.get("is_empty"):
            results["empty_entries"] += 1
        elif validation["is_valid"]:
            results["valid_entries"] += 1
            if validation["ord"]:
                results["entries_with_ord"] += 1
            if validation["has_glosa"]:
                results["entries_with_glosa"] += 1
            if validation["has_varianter"]:
                results["entries_with_varianter"] += 1
        else:
            results["invalid_entries"] += 1
            results["anomalies"].append({
                "index": validation["index"],
                "errors": validation["errors"],
                "entry_preview": str(entry)[:200]
            })
        
        # Collect sample entries (first 10 valid with ord)
        if len(results["sample_entries"]) < 10 and validation["ord"]:
            results["sample_entries"].append({
                "index": validation["index"],
                "ord": validation["ord"],
                "has_glosa": validation["has_glosa"],
                "has_varianter": validation["has_varianter"]
            })
    
    # Convert Counter to dict for JSON serialization
    results["field_count_distribution"] = dict(results["field_count_distribution"])
    
    return results


def extract_word_entries(data: list) -> list:
    """Extract all valid word entries (entries with field 0 populated)."""
    word_entries = []
    
    for i, entry in enumerate(data[1:], start=1):
        if isinstance(entry, list) and len(entry) >= 1 and entry[0] is not None:
            word_entries.append({
                "index": i,
                "ord": entry[0],
                "glosa": entry[1] if len(entry) >= 2 else None,
                "varianter": entry[2] if len(entry) >= 3 else []
            })
    
    return word_entries


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 1: Parse and Validate JSON Structure")
    print("=" * 60)
    
    # Load JSON file
    data = load_json_file(INPUT_FILE)
    
    # Validate it's an array
    if not isinstance(data, list):
        print(f"ERROR: Expected JSON array, got {type(data).__name__}")
        return
    
    print(f"\nTotal elements in JSON array: {len(data)}")
    
    # Validate metadata (first element)
    print("\n--- Metadata Validation ---")
    if len(data) < 1:
        print("ERROR: JSON array is empty")
        return
    
    metadata_validation = validate_metadata(data[0])
    
    # Analyze all entries
    print("\n--- Entry Structure Analysis ---")
    analysis = analyze_entries(data)
    
    # Calculate statistics
    word_count = analysis["entries_with_ord"]
    print(f"\n--- Summary Statistics ---")
    print(f"  Total word entries (with ord field): {word_count}")
    print(f"  Empty entries (placeholders): {analysis['empty_entries']}")
    print(f"  Invalid entries: {analysis['invalid_entries']}")
    print(f"  Entries with glosa: {analysis['entries_with_glosa']}")
    print(f"  Entries with varianter: {analysis['entries_with_varianter']}")
    print(f"\n  Field count distribution:")
    for count, freq in sorted(analysis["field_count_distribution"].items()):
        print(f"    {count} fields: {freq} entries")
    
    # Extract word entries for next step
    print("\n--- Extracting Word Entries ---")
    word_entries = extract_word_entries(data)
    print(f"  Extracted {len(word_entries)} word entries")
    
    # Sample of first 10 words
    print("\n  Sample words (first 10):")
    for entry in word_entries[:10]:
        glosa_info = f" [{entry['glosa']}]" if entry['glosa'] else ""
        print(f"    {entry['index']}: {entry['ord']}{glosa_info}")
    
    # Compile report
    report = {
        "status": "SUCCESS",
        "metadata": metadata_validation,
        "analysis": {
            "total_json_elements": len(data),
            "total_entries_excluding_metadata": analysis["total_entries"],
            "word_entries_count": word_count,
            "empty_entries_count": analysis["empty_entries"],
            "invalid_entries_count": analysis["invalid_entries"],
            "entries_with_glosa": analysis["entries_with_glosa"],
            "entries_with_varianter": analysis["entries_with_varianter"],
            "field_count_distribution": analysis["field_count_distribution"]
        },
        "sample_entries": analysis["sample_entries"],
        "anomalies": analysis["anomalies"][:20]  # First 20 anomalies
    }
    
    # Save report
    print(f"\n--- Saving Validation Report ---")
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Report saved to: {OUTPUT_REPORT}")
    
    # Save extracted word entries for Step 2
    word_entries_file = Path("step1_word_entries.json")
    with open(word_entries_file, 'w', encoding='utf-8') as f:
        json.dump(word_entries, f, ensure_ascii=False, indent=2)
    print(f"  Word entries saved to: {word_entries_file}")
    
    print("\n" + "=" * 60)
    print("Step 1 Complete!")
    print(f"  Word entries extracted: {len(word_entries)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
