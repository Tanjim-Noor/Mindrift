"""
Step 3g: Revert spurious plurals for non-countable noun categories

The previous step3f fixed the QA issue (arbetskraft, manikyr, etc.) but also
generated spurious plurals for words that shouldn't have them:
- Languages: svenska → svenskor (wrong - "svenskor" means "Swedish women")
- Academic fields: matematik → matematiker (wrong - "matematiker" means "mathematician")
- Sports: fotboll → fotboller (wrong - sports as activities don't pluralize)
- Mass nouns: bensin → bensiner (wrong - substances don't pluralize)

This step reverts those spurious plurals while preserving the QA-verified ones.
"""

import json
from datetime import datetime

INPUT_FILE = "swedish_word_inflections_v4.2.json"
OUTPUT_FILE = "swedish_word_inflections_v4.2_cleaned.json"
REPORT_FILE = "step3g_cleanup_report.json"

# Words that should KEEP their plurals (QA-verified)
KEEP_PLURALS = {
    "arbetskraft", "manikyr", "allergi", "anarki", "kärnkraft", "vindkraft",
    "atomkraft", "vattenkraft", "solkraft", "tyngdkraft", "försvarsmakt",
    "köpkraft", "medeltid", "dåtid", "fritid", "livstid", "nutid", "framtid",
    "vänskap", "konkurrens", "kontroll", "tandvård", "sjukvård", "barnomsorg",
    "rösträtt", "upphovsrätt", "vetorätt", "färdtjänst", "kundtjänst",
    "socialtjänst", "migrän", "demens", "begåvning", "massage", "design", "stress"
}

# Languages (plural forms refer to women of that nationality, not the language)
LANGUAGES = {
    "svenska", "danska", "norska", "finska", "engelska", "tyska", "franska",
    "spanska", "ryska", "italienska", "hebreiska", "arabiska", "japanska",
    "kinesiska", "polska", "portugisiska", "grekiska", "holländska", "flamländska",
    "isländska", "estniska", "lettiska", "litauiska", "ukrainska", "tjeckiska",
    "slovakiska", "bulgariska", "rumänska", "ungerska", "turkiska", "persiska",
    "bengaliska", "thailändska", "vietnamesiska", "koreanska", "indonesiska",
    "malajiska", "afrikaans", "swahili", "rikssvenska", "tornedalsfinska"
}

# Academic fields ending in -ik where plural would mean practitioners
ACADEMIC_FIELDS_IK = {
    "matematik", "fysik", "kemi", "pedagogik", "lingvistik", "fonetik",
    "fonologi", "semantik", "pragmatik", "logik", "etik", "estetik", "retorik",
    "politik", "grammatik", "statistik", "akustik", "optik", "genetik",
    "mekanik", "teknik", "elektronik", "informatik", "datorlingvistik",
    "psykolingvistik", "sociolingvistik", "korpuslingvistik", "grafik", "musik",
    "gymnastik", "akrobatik", "erotik", "exotik", "mystik", "romantik",
    "dramatik", "keramik", "didaktik", "metodik", "tematik", "systematik",
    "problematik", "schematik", "taktik", "strategik", "analektik", "dialektik",
    "rytmik", "dynamik", "statik", "kinetik", "kosmetik", "aromaterapi",
    "geriatrik", "pediatrik", "psykiatri", "kirurgi", "ortopedi", "neurologi",
    "kardiologi", "dermatologi", "urologi", "gynekologi", "onkologi", "radiologi",
    "sjukgymnastik", "fysioterapi", "ergoterapi", "mimik", "motorik", "panik",
    "kolik", "eugenik", "högertrafik", "lokaltrafik", "kollektivtrafik", "trafik",
    "forskningsetik", "juridik", "biologi", "ekologi", "geologi", "psykologi",
    "sociologi", "antropologi", "filosofi", "teologi", "arkeologi", "geografi",
    "lexikologi", "fonologi", "morfologi", "syntaktik", "typologi", "filologi",
    "etnologi", "fenomenologi", "kronologi", "klimatologi", "meteorologi",
    "hydrologi", "minerologi", "petrologi", "vulkanologi", "seismologi",
    "oceanologi", "kosmologi", "astrologi", "astronomi", "ekonomi", "anatomi",
    "fysiologi", "patologi", "farmakologi", "toxikologi", "mikrobiologi",
    "zoologi", "botanik", "numismatik", "heraldik"
}

# Sports and games (as activities, not countable)
SPORTS = {
    "fotboll", "handboll", "volleyboll", "basket", "basketboll", "tennis",
    "bordtennis", "bowling", "curling", "dart", "golf", "minigolf", "bangolf",
    "baseball", "baseboll", "brännboll", "ishockey", "hockey", "bandy",
    "rugby", "cricket", "badminton", "squash", "slalom", "storslalom",
    "speedway", "isracing", "krocket", "fiske", "flugfiske", "sportfiske"
}

# Mass nouns (substances, materials)
MASS_NOUNS = {
    "bensin", "diesel", "bly", "koppar", "guld", "silver", "järn", "stål",
    "aluminium", "syre", "kväve", "väte", "klor", "fluor", "dynamit",
    "mjölk", "filmjölk", "lättmjölk", "bröstmjölk", "grädde", "smör",
    "kaviar", "marsipan", "sirap", "ketchup", "senap", "honung", "jäst",
    "majs", "vete", "havre", "ris", "spenat", "blomkål", "vitkål", "brysselkål",
    "gräslök", "rödlök", "purjolök", "vitlök", "timjan", "kanel", "vanilj",
    "bomull", "linne", "silke", "ull", "sammet", "tobak", "cannabis",
    "hö", "halm", "torv", "sand", "grus", "cement", "betong", "asfalt",
    "kolsyra", "syrgas", "kvävgas", "vätgas", "etanol", "metanol",
    "ischoklad", "mjölkchoklad", "julmust", "kokos", "mandelmassa"
}

# Words that end in patterns that suggest non-countable usage
UNCOUNTABLE_PATTERNS = {
    # Abstract -het words (unless in KEEP_PLURALS)
    "het": ["flerspråkighet", "tillgänglighet", "dövblindhet", "tvåspråkighet",
            "ohörsamhet", "omtänksamhet", "egenmäktighet", "istadighet",
            "kompledighet", "tillit"],  # Actually tillit doesn't end in -het
    
    # Abstract -skap words (unless in KEEP_PLURALS)
    "skap": ["hemkunskap", "naturkunskap", "religionskunskap", "samhällskunskap"],
}


def load_data():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def should_revert(word):
    """Determine if a word's plural should be reverted to null"""
    word_lower = word.lower()
    
    # Never revert words in the keep list
    if word_lower in KEEP_PLURALS:
        return False
    
    # Revert languages
    if word_lower in LANGUAGES:
        return True
    
    # Revert academic fields
    if word_lower in ACADEMIC_FIELDS_IK:
        return True
    
    # Revert sports
    if word_lower in SPORTS:
        return True
    
    # Revert mass nouns
    if word_lower in MASS_NOUNS:
        return True
    
    # Revert compounds of mass nouns
    for mass in MASS_NOUNS:
        if word_lower.endswith(mass) and len(word_lower) > len(mass):
            if word_lower not in KEEP_PLURALS:
                return True
    
    # Revert compounds of sports
    for sport in SPORTS:
        if word_lower.endswith(sport) and len(word_lower) > len(sport):
            return True
    
    # Don't revert by default (keep the plural)
    return False


def get_revert_reason(word):
    word_lower = word.lower()
    if word_lower in LANGUAGES:
        return "language"
    if word_lower in ACADEMIC_FIELDS_IK:
        return "academic_field"
    if word_lower in SPORTS:
        return "sport"
    if word_lower in MASS_NOUNS:
        return "mass_noun"
    for mass in MASS_NOUNS:
        if word_lower.endswith(mass):
            return "mass_noun_compound"
    for sport in SPORTS:
        if word_lower.endswith(sport):
            return "sport_compound"
    return "other"


def main():
    print("=" * 60)
    print("Step 3g: Clean up spurious plurals")
    print("=" * 60)
    
    print(f"\nLoading {INPUT_FILE}...")
    data = load_data()
    print(f"Loaded {len(data)} entries")
    
    reverted = []
    kept = []
    no_plural = []
    
    for entry in data:
        word = entry.get('ord', '')
        sub = entry.get('substantiv')
        
        if not sub:
            continue
        
        plural = sub.get('plural')
        bplural = sub.get('bestämd_plural')
        
        # Skip if already null
        if plural is None and bplural is None:
            no_plural.append(word)
            continue
        
        # Check if should revert
        if should_revert(word):
            reverted.append({
                "word": word,
                "reason": get_revert_reason(word),
                "old_plural": plural,
                "old_bestämd_plural": bplural
            })
            sub['plural'] = None
            sub['bestämd_plural'] = None
        else:
            kept.append(word)
    
    # Report
    print(f"\nReverted to null: {len(reverted)}")
    print(f"Kept plurals:     {len(kept)}")
    print(f"Already null:     {len(no_plural)}")
    
    # Show samples
    print("\n" + "-" * 40)
    print("Sample reverted:")
    for item in reverted[:20]:
        print(f"  {item['word']}: {item['old_plural']} → null ({item['reason']})")
    
    # Save
    print(f"\nSaving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "reverted_count": len(reverted),
        "kept_count": len(kept),
        "already_null_count": len(no_plural),
        "reverted": reverted,
        "kept_plurals": kept[:50]  # Just a sample
    }
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"Saved report to {REPORT_FILE}")
    print("\n✓ Done!")


if __name__ == "__main__":
    main()
