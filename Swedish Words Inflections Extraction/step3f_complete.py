"""
Step 3f COMPLETE: Systematic plural generation for nn_0* paradigm nouns

CORE ISSUE:
- SALDO uses nn_0* paradigms (singularia tantum) for nouns it considers singular-only
- The API returns NO plural forms for these paradigms
- But many of these words DO have attested plurals in modern Swedish

SOLUTION:
1. Extract paradigm info from SALDO source for all words
2. For nn_0* paradigm nouns, determine if they should have plurals based on:
   - The paradigm's model word (e.g., nn_0u_kärnkraft → kraft → krafter)
   - Word ending patterns
   - Exclusion of truly uncountable categories (languages, academic fields, etc.)
3. Generate plurals using Swedish morphological rules

This runs on v4.1 (the clean base) and produces v4.2.
"""

import json
import re
from pathlib import Path
from datetime import datetime

INPUT_FILE = "swedish_word_inflections_v4.1.json"
OUTPUT_FILE = "swedish_word_inflections_v4.2.json"
SALDO_FILE = "saldo_2.3/saldo20v03.txt"
REPORT_FILE = "step3f_complete_report.json"


def parse_saldo_paradigms():
    """Extract word -> paradigm mapping from SALDO source"""
    word_paradigms = {}
    
    with open(SALDO_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 7:
                # Format: lemma, mother, father, sense_id, word, pos, paradigm
                word = parts[4].strip()
                pos = parts[5].strip()
                paradigm = parts[6].strip()
                
                if pos == 'nn' and paradigm.startswith('nn_0'):
                    # Store the paradigm for this word
                    if word not in word_paradigms:
                        word_paradigms[word] = paradigm
    
    return word_paradigms


# ============================================================
# MORPHOLOGICAL RULES FOR PLURAL GENERATION
# ============================================================

# Paradigm model words and their plural patterns
# nn_0u_X means: noun, 0=no plural, u=utrum, X=model word
PARADIGM_PATTERNS = {
    # -kraft compounds: kraft → krafter
    'nn_0u_kärnkraft': ('er', 'erna'),
    'nn_0u_boskap': ('er', 'erna'),  # Generic consonant-ending utrum
    'nn_0u_månsing': ('er', 'erna'),  # Generic consonant-ending utrum
    'nn_0u_radar': ('er', 'erna'),
    
    # -i endings (Greek/Latin): allergi → allergier
    'nn_0u_akribi': ('er', 'erna'),
    
    # -a endings (native Swedish): flicka → flickor
    'nn_0u_svenska': ('or', 'orna'),  # For languages - but these shouldn't pluralize!
    'nn_0u_hemsjuka': ('or', 'orna'),
    'nn_0u_hälsa': ('or', 'orna'),
    'nn_0u_tjockolja': ('or', 'orna'),
    'nn_0u_saltsyra': ('or', 'orna'),
    
    # -e endings (neuter): syre → syren
    'nn_0n_syre': ('n', 'na'),
    
    # -i endings (neuter with -eri): raseri → raserier
    'nn_0n_raseri': ('er', 'erna'),
    
    # Generic neuter
    'nn_0n_ansvar': ('', ''),  # No good plural pattern for abstract neuter
}


# ============================================================
# EXCLUSION RULES - These words should NOT get plurals
# ============================================================

def is_language(word):
    """Languages - specific list, not just pattern matching"""
    word_lower = word.lower()
    
    # Explicit list of languages
    languages = {
        'svenska', 'danska', 'norska', 'finska', 'engelska', 'tyska',
        'franska', 'spanska', 'ryska', 'italienska', 'hebreiska',
        'arabiska', 'japanska', 'kinesiska', 'polska', 'portugisiska',
        'grekiska', 'holländska', 'isländska', 'estniska', 'lettiska',
        'litauiska', 'ukrainska', 'tjeckiska', 'slovakiska', 'bulgariska',
        'rumänska', 'ungerska', 'turkiska', 'persiska', 'bengaliska',
        'thailändska', 'vietnamesiska', 'koreanska', 'indonesiska',
        'rikssvenska', 'finlandssvenska', 'skånska', 'gotländska',
        'arameiska', 'albanska', 'kroatiska', 'serbiska', 'slovenska',
        'makedonska', 'bosniska', 'afrikaans', 'swahili', 'hindi',
        'urdu', 'bengali', 'tamil', 'telugu', 'marathi', 'gujarati',
        'punjabi', 'malayalam', 'kannada', 'assamese', 'odia',
        'tornedalsfinska'
    }
    
    return word_lower in languages


def is_academic_field(word):
    """Academic fields where plural would mean practitioners"""
    word_lower = word.lower()
    
    # -ik endings (matematik, fysik, etc.)
    if word_lower.endswith('ik'):
        # These are typically academic fields or abstract concepts
        # The plural form would mean the practitioner (matematiker = mathematician)
        ik_words = {
            'matematik', 'fysik', 'logik', 'etik', 'estetik', 'retorik',
            'politik', 'grammatik', 'statistik', 'akustik', 'optik',
            'genetik', 'mekanik', 'teknik', 'elektronik', 'informatik',
            'lingvistik', 'fonetik', 'semantik', 'pragmatik', 'didaktik',
            'pedagogik', 'metodik', 'tematik', 'systematik', 'problematik',
            'taktik', 'strategik', 'dialektik', 'rytmik', 'dynamik',
            'statik', 'kinetik', 'kosmetik', 'geriatrik', 'psykiatrik',
            'grafik', 'musik', 'gymnastik', 'akrobatik', 'erotik',
            'exotik', 'mystik', 'romantik', 'dramatik', 'keramik',
            'mimik', 'motorik', 'panik', 'kolik', 'eugenik',
            'datorlingvistik', 'psykolingvistik', 'sociolingvistik',
            'korpuslingvistik', 'forskningsetik', 'bioetik',
            'aritmetik', 'geometri', 'algebra', 'kalkyl',
            'botanik', 'zoologi', 'ekologi', 'geologi',
            'poetik', 'stilistik', 'narrativistik', 'hermeneutik'
        }
        if word_lower in ik_words or word_lower.endswith(tuple(
            f + 'ik' for f in ['lingvist', 'psykolog', 'biolog', 'geolog', 
                               'sosiolog', 'antropolog', 'arkeolog']
        )):
            return True
    
    # -logi/-nomi/-grafi/-sofi endings (biologi, astronomi, etc.)
    if word_lower.endswith(('logi', 'nomi', 'grafi', 'sofi', 'atri', 'pedi', 'urgi')):
        return True
    
    # -terapi endings (arbetsterapi, fysioterapi) - medical treatments
    if word_lower.endswith('terapi'):
        return True
    
    return False


def is_sport(word):
    """Sports and games as activities (not countable)"""
    word_lower = word.lower()
    sports = {
        'fotboll', 'handboll', 'volleyboll', 'basket', 'basketboll', 
        'tennis', 'bordtennis', 'bowling', 'curling', 'dart', 
        'golf', 'minigolf', 'bangolf', 'baseball', 'baseboll', 
        'brännboll', 'ishockey', 'hockey', 'bandy', 'rugby', 
        'cricket', 'badminton', 'squash', 'slalom', 'storslalom',
        'speedway', 'isracing', 'krocket', 'fiske', 'flugfiske',
        'sportfiske', 'bågskytte', 'pistolskytte', 'lerduveskytte',
        'skidskytte', 'simning', 'crawl', 'friidrott',
        # Martial arts and activities
        'aikido', 'judo', 'karate', 'taekwondo', 'kungfu', 'kendo',
        'yoga', 'pilates', 'aerobics', 'spinning', 'crossfit',
        'jogging', 'paddling', 'canoeing', 'rafting', 'surfing',
        'wakeboarding', 'skateboarding', 'snowboarding', 'skiing'
    }
    if word_lower in sports:
        return True
    # Check compounds
    for sport in ['fotboll', 'handboll', 'volleyboll', 'tennis', 'hockey', 
                  'bowling', 'golf', 'fiske', 'skytte', 'simning']:
        if word_lower.endswith(sport) and len(word_lower) > len(sport):
            return True
    return False


def is_mass_noun(word):
    """Mass nouns (substances, materials) - uncountable"""
    word_lower = word.lower()
    mass_nouns = {
        # Metals & elements
        'bly', 'koppar', 'guld', 'silver', 'järn', 'stål', 'aluminium',
        'syre', 'kväve', 'väte', 'klor', 'fluor', 'helium', 'argon',
        
        # Liquids & substances
        'bensin', 'diesel', 'olja', 'vatten', 'mjölk', 'filmjölk',
        'lättmjölk', 'bröstmjölk', 'grädde', 'gräddfil', 'smör',
        'kolsyra', 'syrgas', 'kvävgas', 'vätgas', 'etanol', 'metanol',
        
        # Food substances
        'kaviar', 'marsipan', 'sirap', 'ketchup', 'senap', 'honung',
        'jäst', 'socker', 'salt', 'mjöl', 'majs', 'vete', 'havre',
        'ris', 'spenat', 'blomkål', 'vitkål', 'brysselkål', 'rödkål',
        'grönkål', 'gräslök', 'vitlök', 'purjolök', 'rödlök',
        'kanel', 'vanilj', 'kardemumma', 'peppar', 'curry', 'timjan',
        'mandelmassa', 'kokos', 'ischoklad', 'mjölkchoklad',
        
        # Materials
        'bomull', 'linne', 'silke', 'ull', 'sammet', 'denim',
        'gummi', 'plast', 'glas', 'porslin', 'trä', 'sten',
        'betong', 'asfalt', 'cement', 'grus', 'sand', 'torv',
        
        # Other substances
        'dynamit', 'tobak', 'cannabis', 'hö', 'halm', 'röktobak',
        'akryl', 'nylon', 'polyester',
        
        # Medical/skin conditions (mass-like)
        'acne', 'akne', 'eksem', 'psoriasis', 'herpes', 'svamp',
        
        # Abstract mass concepts
        'sex', 'analsex', 'oralsex'
    }
    
    if word_lower in mass_nouns:
        return True
    
    # Check compounds ending in mass nouns
    for noun in ['mjölk', 'olja', 'syra', 'gas', 'vatten', 'sex']:
        if word_lower.endswith(noun) and len(word_lower) > len(noun):
            return True
    
    return False


def is_abstract_uncountable(word):
    """Abstract nouns that are typically uncountable"""
    word_lower = word.lower()
    
    # Words ending in -het are usually abstract (exception: some can be counted)
    # Most -het words should NOT get plurals added synthetically
    if word_lower.endswith('het'):
        return True
    
    # Words ending in -nad, -sel are usually abstract
    if word_lower.endswith(('nad', 'sel')):
        return True
    
    # Words ending in -else are usually abstract
    if word_lower.endswith('else'):
        return True
    
    # Words ending in -glädje (compound with glädje)
    if word_lower.endswith('glädje'):
        return True
    
    # Time-related that don't pluralize
    time_words = {
        'januari', 'februari', 'mars', 'april', 'maj', 'juni',
        'juli', 'augusti', 'september', 'oktober', 'november', 'december',
        'midnatt', 'advent', 'action'
    }
    if word_lower in time_words:
        return True
    
    # Specific abstract nouns
    abstracts = {
        'allmakt', 'allvar', 'ansvar', 'aptit', 'eld', 'frost', 'hetta',
        'hygien', 'lyx', 'natur', 'respekt', 'stress', 'trans',
        'aids', 'feedback', 'copyright', 'design', 'input', 'output',
        'overhead', 'support', 'mixed', 'casting', 'doping', 'trafficking',
        'antik', 'aids', 'ALS', 'action', 'allmäntillstånd'
    }
    if word_lower in abstracts:
        return True
    
    return False


def should_have_plural(word, paradigm):
    """
    Determine if a word with nn_0* paradigm should get a synthetic plural.
    Returns False if the word is in an uncountable category.
    """
    # Check exclusion rules
    if is_language(word):
        return False
    if is_academic_field(word):
        return False
    if is_sport(word):
        return False
    if is_mass_noun(word):
        return False
    if is_abstract_uncountable(word):
        return False
    
    # Check paradigm-specific exclusions
    # nn_0n_ansvar type - abstract neuter nouns - typically don't pluralize
    if paradigm.startswith('nn_0n_ansvar'):
        return False
    
    # By default, if not in an exclusion category, generate plural
    return True


def generate_plural(word, paradigm):
    """
    Generate plural forms based on paradigm and word ending.
    Returns (plural, definite_plural) or (None, None) if can't generate.
    """
    word_lower = word.lower()
    
    # Don't generate for words ending in unusual patterns
    if word_lower.endswith(('x', 'z', 'w')):
        # Foreign words - skip synthetic generation
        return None, None
    
    # Words ending in -dje (glädje, etc.) - skip
    if word_lower.endswith('dje'):
        return None, None
    
    # Get the base pattern from the paradigm
    pattern = PARADIGM_PATTERNS.get(paradigm)
    
    if not pattern:
        # Try to infer from paradigm name
        if 'kraft' in paradigm or paradigm.endswith('boskap'):
            pattern = ('er', 'erna')
        elif paradigm.startswith('nn_0u'):
            pattern = ('er', 'erna')  # Default utrum
        elif paradigm.startswith('nn_0n'):
            pattern = ('n', 'na')  # Default neuter with -e ending
        else:
            return None, None
    
    suffix_indef, suffix_def = pattern
    
    # Handle special cases based on word ending
    if word_lower.endswith('a'):
        # -a endings: usually -or/-orna
        plural = word[:-1] + 'or'
        def_plural = word[:-1] + 'orna'
    elif word_lower.endswith('e') and paradigm.startswith('nn_0n'):
        # Neuter -e endings: -en/-ena (e.g., syre → syren)
        plural = word + 'n'
        def_plural = word + 'na'
    elif word_lower.endswith('e') and paradigm.startswith('nn_0u'):
        # Utrum -e endings: typically don't add -er directly
        # Skip these as they often form irregular plurals
        return None, None
    elif word_lower.endswith('i'):
        # -i endings: usually -ier/-ierna (e.g., allergi → allergier)
        plural = word + 'er'
        def_plural = word + 'erna'
    elif word_lower.endswith('y'):
        # -y endings: usually -er/-erna (e.g., manikyr → manikyrer)
        plural = word + 'er'
        def_plural = word + 'erna'
    elif word_lower.endswith('o'):
        # -o endings: foreign words, skip
        return None, None
    elif word_lower.endswith(('r', 's', 't', 'n', 'd', 'k', 'g', 'p', 'f', 'l', 'm', 'v', 'j')):
        # Consonant endings: add -er/-erna
        plural = word + 'er'
        def_plural = word + 'erna'
    else:
        # Unknown pattern - skip
        return None, None
    
    # Preserve capitalization
    if word[0].isupper() and plural:
        plural = plural[0].upper() + plural[1:]
    if word[0].isupper() and def_plural:
        def_plural = def_plural[0].upper() + def_plural[1:]
    
    return plural, def_plural


def main():
    print("=" * 70)
    print("Step 3f COMPLETE: Systematic plural generation for nn_0* nouns")
    print("=" * 70)
    
    # Step 1: Parse SALDO for paradigm information
    print("\n1. Parsing SALDO source for paradigm info...")
    word_paradigms = parse_saldo_paradigms()
    print(f"   Found {len(word_paradigms)} words with nn_0* paradigms")
    
    # Step 2: Load input data
    print(f"\n2. Loading {INPUT_FILE}...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   Loaded {len(data)} entries")
    
    # Step 3: Process entries
    print("\n3. Processing entries...")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "generated": [],
        "excluded": {
            "language": [],
            "academic_field": [],
            "sport": [],
            "mass_noun": [],
            "abstract": [],
            "no_paradigm": [],
            "other": []
        },
        "already_has_plural": 0,
        "no_substantiv": 0
    }
    
    for entry in data:
        word = entry.get('ord', '')
        sub = entry.get('substantiv')
        
        if not sub:
            report["no_substantiv"] += 1
            continue
        
        # Skip if already has plurals
        if sub.get('plural') is not None:
            report["already_has_plural"] += 1
            continue
        
        # Get paradigm
        paradigm = word_paradigms.get(word, '')
        
        if not paradigm:
            report["excluded"]["no_paradigm"].append(word)
            continue
        
        # Check if should have plural
        if not should_have_plural(word, paradigm):
            # Categorize exclusion
            if is_language(word):
                report["excluded"]["language"].append(word)
            elif is_academic_field(word):
                report["excluded"]["academic_field"].append(word)
            elif is_sport(word):
                report["excluded"]["sport"].append(word)
            elif is_mass_noun(word):
                report["excluded"]["mass_noun"].append(word)
            elif is_abstract_uncountable(word):
                report["excluded"]["abstract"].append(word)
            else:
                report["excluded"]["other"].append(word)
            continue
        
        # Generate plural
        plural, def_plural = generate_plural(word, paradigm)
        
        if plural and def_plural:
            report["generated"].append({
                "word": word,
                "paradigm": paradigm,
                "plural": plural,
                "def_plural": def_plural
            })
            sub['plural'] = plural
            sub['bestämd_plural'] = def_plural
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Plurals generated:        {len(report['generated'])}")
    print(f"Already had plural:       {report['already_has_plural']}")
    print(f"Excluded - Language:      {len(report['excluded']['language'])}")
    print(f"Excluded - Academic:      {len(report['excluded']['academic_field'])}")
    print(f"Excluded - Sport:         {len(report['excluded']['sport'])}")
    print(f"Excluded - Mass noun:     {len(report['excluded']['mass_noun'])}")
    print(f"Excluded - Abstract:      {len(report['excluded']['abstract'])}")
    print(f"Excluded - No paradigm:   {len(report['excluded']['no_paradigm'])}")
    print(f"Excluded - Other:         {len(report['excluded']['other'])}")
    
    # Show samples of generated
    print("\n" + "-" * 40)
    print("Sample generated plurals:")
    for item in report["generated"][:15]:
        print(f"  {item['word']} → {item['plural']} / {item['def_plural']}")
    
    # Show samples of excluded
    print("\n" + "-" * 40)
    print("Sample excluded (languages):", report["excluded"]["language"][:10])
    print("Sample excluded (academic):", report["excluded"]["academic_field"][:10])
    print("Sample excluded (sports):", report["excluded"]["sport"][:10])
    
    # Save output
    print(f"\n4. Saving to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Save report
    print(f"5. Saving report to {REPORT_FILE}...")
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n✓ Done!")
    
    # Final counts
    has_plural = sum(1 for e in data if e.get('substantiv') and e['substantiv'].get('plural'))
    null_plural = sum(1 for e in data if e.get('substantiv') and e['substantiv'].get('plural') is None)
    print(f"\nFinal counts: {has_plural} nouns with plurals, {null_plural} with null plurals")


if __name__ == "__main__":
    main()
