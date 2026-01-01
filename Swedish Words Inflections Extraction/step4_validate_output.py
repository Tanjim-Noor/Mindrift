"""
Step 4: Validate Output and Create Final JSON
==============================================
Validates inflection data against the required schema and produces
the final output JSON with quality metrics.
"""

import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Any
import time

# Configuration
INFLECTIONS_FILE = Path("step3_inflections.json")
CLASSIFICATIONS_FILE = Path("step2_classified_entries.json")
OUTPUT_FILE = Path("swedish_word_inflections.json")
REPORT_FILE = Path("final_validation_report.json")
ERROR_LOG_FILE = Path("validation_errors.json")


# Schema definition
SCHEMA = {
    "ord": str,
    "substantiv": {
        "singular": (str, type(None)),
        "plural": (str, type(None)),
        "bestämd_singular": (str, type(None)),
        "bestämd_plural": (str, type(None))
    },
    "verb": {
        "infinitiv": (str, type(None)),
        "presens": (str, type(None)),
        "preteritum": (str, type(None)),
        "supinum": (str, type(None)),
        "particip": (str, type(None))
    },
    "adjektiv": {
        "positiv": (str, type(None)),
        "komparativ": (str, type(None)),
        "superlativ": (str, type(None))
    },
    "övrigt": (str, type(None))
}


def validate_entry(entry: Dict, index: int) -> Dict:
    """
    Validate a single entry against the schema.
    Returns validation result with any errors.
    """
    result = {
        "index": index,
        "ord": entry.get("ord"),
        "is_valid": True,
        "errors": [],
        "warnings": [],
        "categories_populated": 0
    }
    
    # Check ord field
    if not isinstance(entry.get("ord"), str):
        result["errors"].append("Missing or invalid 'ord' field")
        result["is_valid"] = False
    
    # Check exactly one category is non-null (strict enforcement)
    categories = ["substantiv", "verb", "adjektiv", "övrigt"]
    non_null_categories = []
    
    for cat in categories:
        value = entry.get(cat)
        if value is not None:
            non_null_categories.append(cat)
            result["categories_populated"] += 1
    
    # Validate category objects have proper structure
    if entry.get("substantiv"):
        subst = entry["substantiv"]
        if not isinstance(subst, dict):
            result["errors"].append("substantiv should be a dict or null")
            result["is_valid"] = False
        else:
            for field in ["singular", "plural", "bestämd_singular", "bestämd_plural"]:
                if field not in subst:
                    result["warnings"].append(f"Missing field substantiv.{field}")
                elif subst[field] is not None and not isinstance(subst[field], str):
                    result["errors"].append(f"substantiv.{field} should be string or null")
                    result["is_valid"] = False
    
    if entry.get("verb"):
        verb = entry["verb"]
        if not isinstance(verb, dict):
            result["errors"].append("verb should be a dict or null")
            result["is_valid"] = False
        else:
            for field in ["infinitiv", "presens", "preteritum", "supinum", "particip"]:
                if field not in verb:
                    result["warnings"].append(f"Missing field verb.{field}")
                elif verb[field] is not None and not isinstance(verb[field], str):
                    result["errors"].append(f"verb.{field} should be string or null")
                    result["is_valid"] = False
    
    if entry.get("adjektiv"):
        adj = entry["adjektiv"]
        if not isinstance(adj, dict):
            result["errors"].append("adjektiv should be a dict or null")
            result["is_valid"] = False
        else:
            for field in ["positiv", "komparativ", "superlativ"]:
                if field not in adj:
                    result["warnings"].append(f"Missing field adjektiv.{field}")
                elif adj[field] is not None and not isinstance(adj[field], str):
                    result["errors"].append(f"adjektiv.{field} should be string or null")
                    result["is_valid"] = False
    
    if entry.get("övrigt") is not None and not isinstance(entry.get("övrigt"), str):
        result["errors"].append("övrigt should be string or null")
        result["is_valid"] = False
    
    # Check for multiple categories (warning, not error per plan exception)
    if len(non_null_categories) > 1:
        result["warnings"].append(f"Multiple categories populated: {non_null_categories}")
    
    # Check for zero categories (allowed for genuinely ambiguous words per plan)
    if len(non_null_categories) == 0:
        result["warnings"].append("No categories populated - entry may be ambiguous or unclassified")
    
    return result


def ensure_schema_compliance(entry: Dict) -> Dict:
    """
    Ensure entry has all required fields with proper null values.
    """
    output = {
        "ord": entry.get("ord", ""),
        "substantiv": None,
        "verb": None,
        "adjektiv": None,
        "övrigt": None
    }
    
    # Copy existing values
    if entry.get("substantiv"):
        output["substantiv"] = {
            "singular": entry["substantiv"].get("singular"),
            "plural": entry["substantiv"].get("plural"),
            "bestämd_singular": entry["substantiv"].get("bestämd_singular"),
            "bestämd_plural": entry["substantiv"].get("bestämd_plural")
        }
    
    if entry.get("verb"):
        output["verb"] = {
            "infinitiv": entry["verb"].get("infinitiv"),
            "presens": entry["verb"].get("presens"),
            "preteritum": entry["verb"].get("preteritum"),
            "supinum": entry["verb"].get("supinum"),
            "particip": entry["verb"].get("particip")
        }
    
    if entry.get("adjektiv"):
        output["adjektiv"] = {
            "positiv": entry["adjektiv"].get("positiv"),
            "komparativ": entry["adjektiv"].get("komparativ"),
            "superlativ": entry["adjektiv"].get("superlativ")
        }
    
    if entry.get("övrigt"):
        output["övrigt"] = entry["övrigt"]
    
    return output


def count_inflection_coverage(entry: Dict) -> Dict:
    """Count how many inflection fields are populated."""
    coverage = {
        "substantiv_fields": 0,
        "verb_fields": 0,
        "adjektiv_fields": 0,
        "has_övrigt": False
    }
    
    if entry.get("substantiv"):
        for field in ["singular", "plural", "bestämd_singular", "bestämd_plural"]:
            if entry["substantiv"].get(field):
                coverage["substantiv_fields"] += 1
    
    if entry.get("verb"):
        for field in ["infinitiv", "presens", "preteritum", "supinum", "particip"]:
            if entry["verb"].get(field):
                coverage["verb_fields"] += 1
    
    if entry.get("adjektiv"):
        for field in ["positiv", "komparativ", "superlativ"]:
            if entry["adjektiv"].get(field):
                coverage["adjektiv_fields"] += 1
    
    if entry.get("övrigt"):
        coverage["has_övrigt"] = True
    
    return coverage


def main():
    """Main execution function."""
    print("=" * 60)
    print("Step 4: Validate Output and Create Final JSON")
    print("=" * 60)
    
    # Load inflections
    print(f"\nLoading inflections from {INFLECTIONS_FILE}...")
    with open(INFLECTIONS_FILE, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    print(f"  Loaded {len(entries)} entries")
    
    # Load classifications for additional metadata
    print(f"Loading classifications from {CLASSIFICATIONS_FILE}...")
    with open(CLASSIFICATIONS_FILE, 'r', encoding='utf-8') as f:
        classifications = json.load(f)
    
    # Create lookup for classification metadata
    class_lookup = {c['ord']: c for c in classifications}
    
    # Validate entries
    print("\n--- Validating Entries ---")
    start_time = time.time()
    
    validation_results = []
    valid_count = 0
    error_entries = []
    
    for i, entry in enumerate(entries):
        result = validate_entry(entry, i)
        validation_results.append(result)
        
        if result["is_valid"]:
            valid_count += 1
        else:
            error_entries.append({
                "index": i,
                "ord": entry.get("ord"),
                "errors": result["errors"]
            })
    
    elapsed = time.time() - start_time
    print(f"  Validated {len(entries)} entries in {elapsed:.2f} seconds")
    print(f"  Valid entries: {valid_count} ({(valid_count/len(entries))*100:.1f}%)")
    print(f"  Invalid entries: {len(error_entries)}")
    
    # Compile statistics
    print("\n--- Coverage Statistics ---")
    
    category_counts = Counter()
    coverage_stats = defaultdict(Counter)
    
    for entry in entries:
        coverage = count_inflection_coverage(entry)
        
        if entry.get("substantiv"):
            category_counts["substantiv"] += 1
            coverage_stats["substantiv_fields"][coverage["substantiv_fields"]] += 1
        if entry.get("verb"):
            category_counts["verb"] += 1
            coverage_stats["verb_fields"][coverage["verb_fields"]] += 1
        if entry.get("adjektiv"):
            category_counts["adjektiv"] += 1
            coverage_stats["adjektiv_fields"][coverage["adjektiv_fields"]] += 1
        if entry.get("övrigt"):
            category_counts["övrigt"] += 1
        if not any(entry.get(c) for c in ["substantiv", "verb", "adjektiv", "övrigt"]):
            category_counts["no_category"] += 1
    
    print("\n  Category Distribution:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        pct = (count / len(entries)) * 100
        print(f"    {cat}: {count} ({pct:.1f}%)")
    
    print("\n  Noun Form Coverage (out of 4 fields):")
    for fields, count in sorted(coverage_stats["substantiv_fields"].items()):
        print(f"    {fields} fields: {count}")
    
    print("\n  Verb Form Coverage (out of 5 fields):")
    for fields, count in sorted(coverage_stats["verb_fields"].items()):
        print(f"    {fields} fields: {count}")
    
    print("\n  Adjective Form Coverage (out of 3 fields):")
    for fields, count in sorted(coverage_stats["adjektiv_fields"].items()):
        print(f"    {fields} fields: {count}")
    
    # Prepare final output with schema compliance
    print("\n--- Preparing Final Output ---")
    
    output_entries = []
    for entry in entries:
        clean_entry = ensure_schema_compliance(entry)
        output_entries.append(clean_entry)
    
    # Save final output
    print(f"\n--- Saving Results ---")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_entries, f, ensure_ascii=False, indent=2)
    print(f"  Final output saved to: {OUTPUT_FILE}")
    
    # Calculate final quality metrics
    entries_with_inflections = sum(1 for e in output_entries 
                                    if any(e.get(c) for c in ["substantiv", "verb", "adjektiv"]))
    full_noun_coverage = sum(1 for e in output_entries 
                              if e.get("substantiv") and all(e["substantiv"].values()))
    full_verb_coverage = sum(1 for e in output_entries 
                              if e.get("verb") and all(e["verb"].values()))
    full_adj_coverage = sum(1 for e in output_entries 
                             if e.get("adjektiv") and all(e["adjektiv"].values()))
    
    # Save validation report
    report = {
        "summary": {
            "total_entries": len(entries),
            "valid_entries": valid_count,
            "invalid_entries": len(error_entries),
            "validation_rate": f"{(valid_count/len(entries))*100:.1f}%"
        },
        "category_distribution": dict(category_counts),
        "coverage_statistics": {
            "entries_with_inflections": entries_with_inflections,
            "nouns_with_full_coverage": full_noun_coverage,
            "verbs_with_full_coverage": full_verb_coverage,
            "adjectives_with_full_coverage": full_adj_coverage
        },
        "noun_field_distribution": dict(coverage_stats["substantiv_fields"]),
        "verb_field_distribution": dict(coverage_stats["verb_fields"]),
        "adjektiv_field_distribution": dict(coverage_stats["adjektiv_fields"]),
        "sample_valid_entries": [
            output_entries[i] for i in range(min(20, len(output_entries)))
            if any(output_entries[i].get(c) for c in ["substantiv", "verb", "adjektiv", "övrigt"])
        ][:10]
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Validation report saved to: {REPORT_FILE}")
    
    # Save error log
    if error_entries:
        with open(ERROR_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(error_entries, f, ensure_ascii=False, indent=2)
        print(f"  Error log saved to: {ERROR_LOG_FILE}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"  Total word entries processed: {len(output_entries)}")
    print(f"  Entries with inflection data: {entries_with_inflections} ({(entries_with_inflections/len(output_entries))*100:.1f}%)")
    print(f"  Nouns with full forms: {full_noun_coverage}")
    print(f"  Verbs with full forms: {full_verb_coverage}")
    print(f"  Adjectives with full forms: {full_adj_coverage}")
    print(f"\n  Output file: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
