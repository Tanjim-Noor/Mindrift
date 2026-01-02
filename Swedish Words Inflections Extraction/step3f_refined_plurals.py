"""
Step 3f (Refined): Selective plural generation for singularia tantum nouns

The previous step3f was too aggressive - it generated plurals for words that
should NOT have plurals (languages, academic fields, mass nouns, etc.)

This refined version:
1. Reverts all generated plurals first
2. Only adds plurals for explicitly verified countable nouns (whitelist approach)
3. Uses category-based exclusions as a safety net

Key insight: SALDO's "singularia tantum" (nn_0*) designation is MOSTLY correct.
Only specific exceptions (like compound nouns with -kraft) should get plurals.
"""

import json
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
INPUT_FILE = "swedish_word_inflections_v4.2.json"  # Has overgenerated plurals
OUTPUT_FILE = "swedish_word_inflections_v4.2_refined.json"
REPORT_FILE = "step3f_refined_plurals_report.json"

# === QA-VERIFIED COUNTABLE NOUNS ===
# These are words explicitly confirmed by QA to need plural forms
# Format: word -> (plural, definite_plural)
QA_VERIFIED_COUNTABLES = {
    # QA-flagged examples
    "arbetskraft": ("arbetskrafter", "arbetskrafterna"),
    "manikyr": ("manikyrer", "manikyrerna"),
    "allergi": ("allergier", "allergierna"),
    "anarki": ("anarkier", "anarkierna"),
    "kärnkraft": ("kärnkrafter", "kärnkrafterna"),
    "vindkraft": ("vindkrafter", "vindkrafterna"),
    
    # Other compound words with -kraft (force/power - can be plural in contexts)
    "atomkraft": ("atomkrafter", "atomkrafterna"),
    "vattenkraft": ("vattenkrafter", "vattenkrafterna"),
    "solkraft": ("solkrafter", "solkrafterna"),
    "tyngdkraft": ("tyngdkrafter", "tyngdkrafterna"),
    "försvarsmakt": ("försvarsmakter", "försvarsmakterna"),
    "köpkraft": ("köpkrafter", "köpkrafterna"),
    
    # Time periods (can be plural: "different eras", "several medieval periods")
    "medeltid": ("medeltider", "medeltiderna"),
    "dåtid": ("dåtider", "dåtiderna"),
    "fritid": ("fritider", "fritiderna"),
    "livstid": ("livstider", "livstiderna"),
    "nutid": ("nutider", "nutiderna"),
    "framtid": ("framtider", "framtiderna"),
    
    # Abstract concepts that CAN be counted in some contexts
    "vänskap": ("vänskaper", "vänskaperna"),  # "many friendships"
    "konkurrens": ("konkurrenser", "konkurrenserna"),  # "different competitions"
    "kontroll": ("kontroller", "kontrollerna"),  # "multiple controls"
    
    # Compound nouns with -vård (care/treatment - can be plural)
    "tandvård": ("tandvårder", "tandvårderna"),
    "sjukvård": ("sjukvårder", "sjukvårderna"),
    "barnomsorg": ("barnomsorger", "barnomsorgerna"),
    
    # Rights (can be plural: "different rights")
    "rösträtt": ("rösträtter", "rösträtterna"),
    "upphovsrätt": ("upphovsrätter", "upphovsrätterna"),
    "vetorätt": ("vetorätter", "vetorätterna"),
    
    # Services (can be plural in institutional contexts)
    "färdtjänst": ("färdtjänster", "färdtjänsterna"),
    "kundtjänst": ("kundtjänster", "kundtjänsterna"),
    "socialtjänst": ("socialtjänster", "socialtjänsterna"),
    
    # Medical conditions (can be plural: "different allergies", "types of migraines")
    "migrän": ("migräner", "migränerna"),
    "psoriasis": ("psoriasiser", "psoriasiserna"),
    "demens": ("demenser", "demenserna"),
    
    # Other verified countables
    "begåvning": ("begåvningar", "begåvningarna"),
    "massage": ("massager", "massagerna"),
    "design": ("designer", "designerna"),
    "stress": ("stresser", "stresserna"),
}

# === CATEGORIES THAT SHOULD NEVER HAVE PLURALS ===
# These patterns identify words that should remain singular-only

# Words ending in these that refer to languages (not people)
LANGUAGE_ENDINGS = {"svenska", "danska", "norska", "finska", "engelska", "tyska", 
                    "franska", "spanska", "ryska", "italienska", "hebreiska",
                    "arabiska", "japanska", "kinesiska", "polska", "portugisiska"}

# Academic/scientific fields ending in -ik (the plural form would mean practitioners)
ACADEMIC_IK_WORDS = {"matematik", "fysik", "kemi", "biologi", "psykologi", "pedagogik",
                     "lingvistik", "fonetik", "fonologi", "semantik", "pragmatik",
                     "logik", "etik", "estetik", "retorik", "politik", "grammatik",
                     "statistik", "akustik", "optik", "genetik", "geologi", "ekologi",
                     "sociologi", "antropologi", "filosofi", "teologi", "arkeologi",
                     "astronomi", "ekonomi", "anatomi", "fysiologi", "patologi",
                     "farmakologi", "toxikologi", "mikrobiologi", "zoologi", "botanik",
                     "geografi", "topografi", "kartografi", "etnografi", "demografi",
                     "historiografi", "bibliografi", "grafik", "musik", "gymnastik",
                     "akrobatik", "erotik", "exotik", "mystik", "romantik", "dramatik",
                     "keramik", "mekanik", "teknik", "elektronik", "informatik",
                     "datorlingvistik", "psykolingvistik", "sociolingvistik", 
                     "korpuslingvistik", "neurologi", "psykiatri", "geriatrik",
                     "pediatrik", "ortopedi", "kirurgi", "kardiologi", "dermatologi",
                     "oftalmologi", "urologi", "gynekologi", "obstetrik", "onkologi",
                     "radiologi", "anestesiologi"}

# Mass nouns / substances
MASS_NOUN_PATTERNS = {
    # Metals and elements
    "koppar", "bly", "guld", "silver", "järn", "stål", "aluminium", "titan",
    "kol", "syre", "kväve", "väte", "helium", "argon", "neon", "fluor", "klor",
    
    # Food/drink substances
    "mjölk", "smör", "ost", "grädde", "socker", "salt", "mjöl", "ris", "pasta",
    "bensin", "diesel", "olja", "vatten", "kaffe", "te", "öl", "vin", "sprit",
    "ketchup", "senap", "sirap", "honung", "kaviar", "marsipan", "mandelmassa",
    "majs", "vete", "havre", "råg", "korn", "spenat", "broccoli", "blomkål",
    "vitkål", "rödkål", "grönkål", "purjolök", "gräslök", "vitlök", "lök",
    "jäst", "bakpulver", "vanilj", "kanel", "kardemumma", "peppar", "curry",
    "filmjölk", "gräddfil", "yoghurt", "kvarg", "kesella", "creme fraiche",
    "kolsyra", "syrgas", "kvävgas", "vätgas",
    
    # Textiles/materials
    "bomull", "linne", "silke", "ull", "sammet", "denim", "fleece",
    "gummi", "plast", "glas", "porslin", "keramik", "trä", "sten", "tegel",
    
    # Abstract substances
    "dynamit", "nitroglycerin", "cannabis", "kokain", "heroin", "morfin",
    "tobak", "snus", "röktobak"
}

# Sports/games (as activities, not countable)
SPORT_ACTIVITY_WORDS = {
    "fotboll", "handboll", "volleyboll", "basket", "basketboll", "tennis",
    "bordtennis", "bowling", "curling", "dart", "golf", "minigolf", "bangolf",
    "baseball", "baseboll", "brännboll", "ishockey", "hockey", "bandy",
    "rugby", "cricket", "badminton", "squash", "paddel", "simning",
    "crawl", "ryggsim", "bröstsim", "fjärilsim", "frisim", "slalom",
    "storslalom", "utförsåkning", "längdskidåkning", "skidskytte",
    "speedway", "isracing", "rallycross", "motocross", "trial",
    "fäktning", "brottning", "boxning", "judo", "karate", "taekwondo",
    "bågskytte", "pistolskytte", "lerduveskytte", "skytte", "krocket",
    "fiske", "flugfiske", "sportfiske", "jakt", "orientering"
}


def load_data():
    """Load the current v4.2 data (with overgenerated plurals)"""
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list and dict formats
        if isinstance(data, list):
            return {"entries": data}
        return data


def should_revert_plural(word, word_data, paradigm):
    """
    Determine if a generated plural should be reverted to null.
    Returns True if the word should NOT have plurals.
    """
    word_lower = word.lower()
    
    # Check if it's in the verified countables list (keep plural)
    if word in QA_VERIFIED_COUNTABLES or word_lower in QA_VERIFIED_COUNTABLES:
        return False  # Don't revert - this word should have plurals
    
    # Check if it's a language name
    if word_lower in LANGUAGE_ENDINGS:
        return True  # Revert - languages don't have plurals
    
    # Check if it ends like a language (-ska pattern and is a language)
    if word_lower.endswith("ska") and paradigm == "nn_0u_svenska":
        return True  # Likely a language
    
    # Check if it's an academic field
    if word_lower in ACADEMIC_IK_WORDS:
        return True  # Revert - academic fields don't pluralize
    
    # Check compound academic fields (e.g., "datorlingvistik", "socialpsykologi")
    for field in ["lingvistik", "psykologi", "biologi", "kemi", "fysik", "logik", 
                  "grafi", "nomi", "logi", "sofi", "pedi", "atri"]:
        if word_lower.endswith(field) and len(word_lower) > len(field):
            return True
    
    # Check if it's a mass noun
    if word_lower in MASS_NOUN_PATTERNS:
        return True
    
    # Check for mass noun patterns
    for pattern in MASS_NOUN_PATTERNS:
        if word_lower.endswith(pattern):
            return True  # Compounds ending in mass nouns (e.g., bröstmjölk)
    
    # Check if it's a sport/activity
    if word_lower in SPORT_ACTIVITY_WORDS:
        return True
    
    # Check for sport compounds
    for sport in SPORT_ACTIVITY_WORDS:
        if word_lower.endswith(sport) and len(word_lower) > len(sport):
            return True  # e.g., "strandfotboll", "gatuhockey"
    
    # Words ending in -het are usually abstract and don't pluralize
    # (exceptions like "egenhet" should be in QA_VERIFIED if needed)
    if word_lower.endswith("het"):
        return True
    
    # Words ending in -skap are usually abstract
    # (exception: "vänskap" is in QA_VERIFIED)
    if word_lower.endswith("skap"):
        return True
    
    # By default, if it was in nn_0* paradigm and not in our verified list,
    # trust SALDO's judgment that it's singular-only
    return True


def process_entries(data):
    """Process entries, reverting inappropriate plurals and keeping verified ones"""
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "description": "Refined plural generation - reverted overgenerated plurals",
        "reverted": [],  # Words where plural was removed
        "verified_kept": [],  # QA-verified words that kept plurals
        "qa_updated": [],  # Words updated from QA list
        "unchanged": [],  # Words already had null plurals
        "summary": {}
    }
    
    entries = data.get("entries", [])
    
    for entry in entries:
        if entry.get("ordklass") != "substantiv":
            continue
            
        word = entry.get("ord", "")
        paradigm = entry.get("paradigm", "")
        
        # Only process words from nn_0* paradigms
        if not paradigm or not paradigm.startswith("nn_0"):
            continue
        
        current_plural = entry.get("plural")
        current_def_plural = entry.get("bestämd_plural")
        
        word_lower = word.lower()
        
        # Case 1: Word is in QA-verified list - use verified forms
        if word in QA_VERIFIED_COUNTABLES:
            verified = QA_VERIFIED_COUNTABLES[word]
            if current_plural != verified[0] or current_def_plural != verified[1]:
                report["qa_updated"].append({
                    "word": word,
                    "paradigm": paradigm,
                    "old_plural": current_plural,
                    "new_plural": verified[0],
                    "old_def_plural": current_def_plural,
                    "new_def_plural": verified[1]
                })
                entry["plural"] = verified[0]
                entry["bestämd_plural"] = verified[1]
            else:
                report["verified_kept"].append(word)
            continue
        
        if word_lower in QA_VERIFIED_COUNTABLES and word not in QA_VERIFIED_COUNTABLES:
            verified = QA_VERIFIED_COUNTABLES[word_lower]
            if current_plural != verified[0] or current_def_plural != verified[1]:
                report["qa_updated"].append({
                    "word": word,
                    "paradigm": paradigm,
                    "old_plural": current_plural,
                    "new_plural": verified[0],
                    "old_def_plural": current_def_plural,
                    "new_def_plural": verified[1]
                })
                entry["plural"] = verified[0]
                entry["bestämd_plural"] = verified[1]
            continue
        
        # Case 2: Already null - leave as is
        if current_plural is None and current_def_plural is None:
            report["unchanged"].append(word)
            continue
        
        # Case 3: Check if plural should be reverted
        if should_revert_plural(word, entry, paradigm):
            if current_plural is not None or current_def_plural is not None:
                report["reverted"].append({
                    "word": word,
                    "paradigm": paradigm,
                    "old_plural": current_plural,
                    "old_def_plural": current_def_plural,
                    "reason": get_revert_reason(word, paradigm)
                })
                entry["plural"] = None
                entry["bestämd_plural"] = None
        else:
            # Shouldn't reach here if should_revert returns True by default
            report["unchanged"].append(word)
    
    # Generate summary
    report["summary"] = {
        "plurals_reverted": len(report["reverted"]),
        "qa_verified_kept": len(report["verified_kept"]),
        "qa_updated": len(report["qa_updated"]),
        "unchanged_nulls": len(report["unchanged"]),
        "total_processed": len(report["reverted"]) + len(report["verified_kept"]) + 
                          len(report["qa_updated"]) + len(report["unchanged"])
    }
    
    return data, report


def get_revert_reason(word, paradigm):
    """Get the reason why a plural was reverted"""
    word_lower = word.lower()
    
    if word_lower in LANGUAGE_ENDINGS or (word_lower.endswith("ska") and paradigm == "nn_0u_svenska"):
        return "language_name"
    
    if word_lower in ACADEMIC_IK_WORDS:
        return "academic_field"
    
    for field in ["lingvistik", "psykologi", "biologi", "kemi", "fysik", "logik"]:
        if word_lower.endswith(field):
            return "academic_field_compound"
    
    if word_lower in MASS_NOUN_PATTERNS:
        return "mass_noun"
    
    for pattern in MASS_NOUN_PATTERNS:
        if word_lower.endswith(pattern):
            return "mass_noun_compound"
    
    if word_lower in SPORT_ACTIVITY_WORDS:
        return "sport_activity"
    
    for sport in SPORT_ACTIVITY_WORDS:
        if word_lower.endswith(sport):
            return "sport_compound"
    
    if word_lower.endswith("het"):
        return "abstract_het_suffix"
    
    if word_lower.endswith("skap"):
        return "abstract_skap_suffix"
    
    return "default_singulare_tantum"


def main():
    print("=" * 60)
    print("Step 3f REFINED: Selective Plural Generation")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading {INPUT_FILE}...")
    data = load_data()
    
    original_count = len(data.get("entries", []))
    print(f"Loaded {original_count} entries")
    
    # Process entries
    print("\nProcessing entries...")
    data, report = process_entries(data)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Plurals reverted to null:  {report['summary']['plurals_reverted']}")
    print(f"QA-verified plurals kept:  {report['summary']['qa_verified_kept']}")
    print(f"QA-verified plurals added: {report['summary']['qa_updated']}")
    print(f"Already null (unchanged):  {report['summary']['unchanged_nulls']}")
    print(f"Total nn_0* nouns:         {report['summary']['total_processed']}")
    
    # Show some examples of reverted plurals
    if report["reverted"]:
        print("\n" + "-" * 40)
        print("Sample reverted plurals:")
        for item in report["reverted"][:15]:
            print(f"  {item['word']}: {item['old_plural']} → null ({item['reason']})")
    
    # Show QA-updated
    if report["qa_updated"]:
        print("\n" + "-" * 40)
        print("QA-verified plurals added/updated:")
        for item in report["qa_updated"]:
            print(f"  {item['word']}: {item['new_plural']} / {item['new_def_plural']}")
    
    # Save output (as list)
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data["entries"], f, ensure_ascii=False, indent=2)
    
    # Save report
    print(f"Saving report to {REPORT_FILE}...")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
