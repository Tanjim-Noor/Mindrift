#!/usr/bin/env python3
"""
Step 3h: Comprehensive plural correction for ALL entries
=========================================================

Problem identified:
- step3f_complete.py only GENERATED plurals for null entries (nn_0* paradigms)
- But the ORIGINAL API data contains INCORRECT plurals that need correction
- Examples: fotboll→fotboller (should be fotbollar), svenska→svenskor (should be null)

This script:
1. Loads the entire dataset
2. Corrects ALL incorrect plurals (not just null ones):
   - Removes plurals for languages
   - Removes plurals for academic fields (-ik, -logi, -nomi, etc.)
   - Removes plurals for sports
   - Removes plurals for mass nouns and abstracts
   - Fixes morphological errors (e.g., fotboll→fotboller to fotbollar)
3. Applies corrections systematically to the entire dataset

Date: 2026-01-02
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

def is_language(word: str) -> bool:
    """Check if word is a language name"""
    word_lower = word.lower()
    
    # Explicit list of languages (same as step3f_complete.py)
    languages = {
        'afrikaans', 'albanska', 'arabiska', 'arameiska', 'armeniska',
        'assyriska', 'baskiska', 'bengali', 'bosniska', 'bulgariska',
        'danska', 'dari', 'engelska', 'esperanto', 'estniska',
        'finska', 'franska', 'frisiska', 'färöiska', 'grekiska',
        'grönländska', 'hebreiska', 'hindi', 'isländska', 'italienska',
        'japanska', 'jiddisch', 'katalanska', 'kinesiska', 'koreanska',
        'kroatiska', 'kurdiska', 'latin', 'lettiska', 'litauiska',
        'makedonska', 'nederländska', 'norska', 'persiska', 'polska',
        'portugisiska', 'rikssvenska', 'romani', 'rumänska', 'ryska',
        'samiska', 'serbiska', 'slovakiska', 'slovenska', 'spanska',
        'svenska', 'swahili', 'thailändska', 'tjeckiska', 'turkiska',
        'tyska', 'ukrainska', 'ungerska', 'urdu', 'vietnamesiska',
        'östsvenska'
    }
    
    return word_lower in languages

def is_academic_field(word: str) -> bool:
    """Check if word is an academic field (plural would mean practitioners)"""
    word_lower = word.lower()
    
    # -ik endings (matematik, fysik, etc.)
    if word_lower.endswith('ik'):
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
        if word_lower in ik_words:
            return True
    
    # -logi/-nomi/-grafi/-sofi endings (biologi, astronomi, etc.)
    if word_lower.endswith(('logi', 'nomi', 'grafi', 'sofi', 'atri', 'pedi', 'urgi')):
        return True
    
    # -terapi endings
    if word_lower.endswith('terapi'):
        return True
    
    return False

def is_sport(word: str) -> bool:
    """Check if word is a sport/game name"""
    word_lower = word.lower()
    
    sports = {
        'fotboll', 'handboll', 'basket', 'basketboll', 'volleyboll',
        'innebandy', 'bandy', 'ishockey', 'tennis', 'bordtennis',
        'badminton', 'golf', 'bangolf', 'frisbee', 'bowling',
        'biljard', 'snooker', 'dart', 'curling', 'cricket',
        'baseboll', 'softboll', 'rugby', 'pingis', 'squash',
        'boxning', 'brottning', 'fäktning', 'skytte', 'bågskytte',
        'simning', 'dykning', 'segling', 'rodd', 'kanotsport',
        'cykling', 'längdskidåkning', 'slalom', 'skidskytte',
        'konståkning', 'speedway', 'motorsport', 'dragrace',
        'brännboll', 'kubb', 'boule', 'petanque', 'krocket',
        'aikido', 'judo', 'karate', 'taekwondo', 'kickboxning',
        'thaiboxning', 'jiujitsu', 'kendo', 'sumo'
    }
    
    return word_lower in sports

def is_mass_noun(word: str) -> bool:
    """Check if word is a mass noun (uncountable substance/material)"""
    word_lower = word.lower()
    
    # Substances, materials, foods
    mass_nouns = {
        'guld', 'silver', 'brons', 'järn', 'koppar', 'bly', 'aluminium',
        'stål', 'plast', 'gummi', 'lera', 'sand', 'grus', 'cement',
        'betong', 'asfalt', 'tegel', 'sten', 'marmor', 'granit',
        'olja', 'bensin', 'diesel', 'fotogen', 'petroleum',
        'vatten', 'luft', 'ånga', 'rök', 'dimma', 'is', 'snö',
        'mjölk', 'grädde', 'smör', 'ost', 'bröd', 'kött', 'fisk',
        'mjöl', 'socker', 'salt', 'peppar', 'krydda', 'honung',
        'sylt', 'marmelad', 'juice', 'kaffe', 'te', 'choklad',
        'ris', 'pasta', 'sallad', 'soppa', 'sås', 'buljong',
        'bomull', 'ull', 'silke', 'linne', 'läder', 'päls',
        'trä', 'papper', 'kartong', 'wellpapp', 'papp',
        'glas', 'kristall', 'porslin', 'keramik', 'lergods',
        'blod', 'svett', 'saliv', 'urin', 'avföring', 'spya',
        'pus', 'var', 'slim', 'snor', 'tårar',
        'acne', 'akne', 'eksem', 'psoriasis', 'cancer', 'diabetes',
        'astma', 'aids', 'hiv', 'hepatit', 'malaria', 'tuberkulos',
        'bacon', 'korv', 'skinka', 'fläsk', 'nötkött', 'kalvkött',
        'lammkött', 'fårkött', 'viltkött', 'fågel', 'fjäderfä',
        'kyckling', 'kalkon', 'anka', 'gås',
        'bröstmjölk', 'ersättning', 'välling', 'gröt',
        'blomkål', 'brysselkål', 'vitkål', 'rödkål', 'grönkål',
        'spenat', 'sallat', 'isbergssallat', 'rucola',
        'akryl', 'nylon', 'polyester', 'latex', 'plexiglas',
        'asbest', 'grafit', 'kisel', 'kvarts', 'diamant'
    }
    
    if word_lower in mass_nouns:
        return True
    
    # Sex-related compounds
    if 'sex' in word_lower and word_lower.endswith('sex'):
        return True
    
    return False

def is_abstract_uncountable(word: str) -> bool:
    """Check if word is an abstract uncountable concept"""
    word_lower = word.lower()
    
    # Abstract concepts typically uncountable
    if word_lower.endswith(('het', 'nad', 'ande', 'else', 'skap', 'dom')):
        # But exclude some that are countable
        if word_lower in ['förhet', 'grannskap', 'vänskap']:
            return False
        if word_lower.endswith(('skapelse', 'rörelsehinder')):
            return False
        return True
    
    # Months
    months = {
        'januari', 'februari', 'mars', 'april', 'maj', 'juni',
        'juli', 'augusti', 'september', 'oktober', 'november', 'december'
    }
    if word_lower in months:
        return True
    
    # Compound abstracts
    if word_lower.endswith(('glädje', 'sorg', 'ilska', 'rädsla', 'ångest')):
        return True
    
    # Common abstracts
    abstracts = {
        'kärlek', 'hat', 'rädsla', 'glädje', 'sorg', 'ilska',
        'lycka', 'olycka', 'fred', 'krig', 'hälsa', 'sjukdom',
        'liv', 'död', 'födseln', 'livet', 'döden',
        'allvar', 'ansvar', 'tålamod', 'aptit', 'allmakt',
        'action', 'advent', 'aids', 'allmäntillstånd'
    }
    
    return word_lower in abstracts

def is_singular_only_compound(word: str) -> bool:
    """Check if word is a compound that's inherently singular-only"""
    word_lower = word.lower()
    
    # Common singular-only compound endings
    singular_endings = [
        'liv', 'stöd', 'försvar', 'sken', 'bruk', 'språk',
        'land', 'spel', 'mjöl', 'skydd', 'skap', 'tal', 'drag'
    ]
    
    for ending in singular_endings:
        if word_lower.endswith(ending) and len(word_lower) > len(ending):
            # Compounds like arbetsliv, fastland, privatliv, etc.
            return True
    
    return False

def should_have_null_plural(word: str) -> Tuple[bool, str]:
    """
    Determine if a word should have null plural (is truly uncountable)
    Returns: (should_be_null, reason)
    """
    if is_language(word):
        return (True, 'language')
    if is_academic_field(word):
        return (True, 'academic_field')
    if is_sport(word):
        return (True, 'sport')
    if is_mass_noun(word):
        return (True, 'mass_noun')
    if is_abstract_uncountable(word):
        return (True, 'abstract')
    if is_singular_only_compound(word):
        return (True, 'singular_compound')
    
    return (False, '')

def fix_morphological_plural(word: str, current_plural: str) -> Optional[str]:
    """
    Fix known morphological errors in plurals
    Returns corrected plural or None if no fix needed
    """
    word_lower = word.lower()
    current_lower = current_plural.lower() if current_plural else ''
    
    # fotboll → fotboller is WRONG, should be fotbollar
    # Pattern: words ending in -oll should use -ollar not -oller
    if word_lower.endswith('oll') and current_lower.endswith('oller'):
        return word[:-3] + 'ollar'
    
    # Words ending in -all should use -allar not -aller
    if word_lower.endswith('all') and current_lower.endswith('aller'):
        return word[:-3] + 'allar'
    
    # Add more morphological corrections as needed
    
    return None

def correct_all_plurals(input_file: str, output_file: str) -> Dict:
    """
    Correct ALL plurals in the dataset
    """
    print("="*70)
    print("Step 3h: Comprehensive plural correction")
    print("="*70)
    print()
    
    # Load data
    print(f"1. Loading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"   Loaded {len(data)} entries")
    print()
    
    # Track corrections
    stats = {
        'nullified_language': [],
        'nullified_academic_field': [],
        'nullified_sport': [],
        'nullified_mass_noun': [],
        'nullified_abstract': [],
        'nullified_singular_compound': [],
        'morphological_fixes': [],
        'unchanged': 0
    }
    
    print("2. Processing all entries...")
    for entry in data:
        word = entry.get('ord')
        sub = entry.get('substantiv')
        
        if not sub or not word:
            continue
        
        current_plural = sub.get('plural')
        current_def_plural = sub.get('bestämd_plural')
        
        # Skip if already null
        if current_plural is None:
            stats['unchanged'] += 1
            continue
        
        # Check if should be null
        should_null, reason = should_have_null_plural(word)
        
        if should_null:
            # Nullify incorrect plural
            sub['plural'] = None
            sub['bestämd_plural'] = None
            stats[f'nullified_{reason}'].append({
                'word': word,
                'removed_plural': current_plural,
                'removed_def_plural': current_def_plural
            })
        else:
            # Check for morphological errors
            fixed_plural = fix_morphological_plural(word, current_plural)
            if fixed_plural and fixed_plural != current_plural:
                # Fix the plural
                old_plural = current_plural
                old_def_plural = current_def_plural
                sub['plural'] = fixed_plural
                sub['bestämd_plural'] = fixed_plural + 'na'
                stats['morphological_fixes'].append({
                    'word': word,
                    'old_plural': old_plural,
                    'new_plural': fixed_plural,
                    'old_def_plural': old_def_plural,
                    'new_def_plural': sub['bestämd_plural']
                })
            else:
                stats['unchanged'] += 1
    
    # Save corrected data
    print()
    print(f"3. Saving corrected data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Save report
    report_file = output_file.replace('.json', '_report.json')
    print(f"4. Saving report to {report_file}...")
    report = {
        'timestamp': datetime.now().isoformat(),
        'input_file': input_file,
        'output_file': output_file,
        'statistics': {
            'nullified_languages': len(stats['nullified_language']),
            'nullified_academic_fields': len(stats['nullified_academic_field']),
            'nullified_sports': len(stats['nullified_sport']),
            'nullified_mass_nouns': len(stats['nullified_mass_noun']),
            'nullified_abstract': len(stats['nullified_abstract']),
            'nullified_singular_compounds': len(stats['nullified_singular_compound']),
            'morphological_fixes': len(stats['morphological_fixes']),
            'unchanged': stats['unchanged']
        },
        'corrections': stats
    }
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Nullified plurals:")
    print(f"  Languages:           {len(stats['nullified_language'])}")
    print(f"  Academic fields:     {len(stats['nullified_academic_field'])}")
    print(f"  Sports:              {len(stats['nullified_sport'])}")
    print(f"  Mass nouns:          {len(stats['nullified_mass_noun'])}")
    print(f"  Abstract:            {len(stats['nullified_abstract'])}")
    print(f"  Singular compounds:  {len(stats['nullified_singular_compound'])}")
    print(f"Morphological fixes:   {len(stats['morphological_fixes'])}")
    print(f"Unchanged:             {stats['unchanged']}")
    
    # Show samples
    if stats['nullified_language']:
        print()
        print("Sample nullified (languages):")
        for item in stats['nullified_language'][:5]:
            print(f"  {item['word']}: {item['removed_plural']} → NULL")
    
    if stats['nullified_academic_field']:
        print()
        print("Sample nullified (academic fields):")
        for item in stats['nullified_academic_field'][:5]:
            print(f"  {item['word']}: {item['removed_plural']} → NULL")
    
    if stats['morphological_fixes']:
        print()
        print("Sample morphological fixes:")
        for item in stats['morphological_fixes'][:5]:
            print(f"  {item['word']}: {item['old_plural']} → {item['new_plural']}")
    
    print()
    print("✓ Done!")
    
    return report

if __name__ == '__main__':
    report = correct_all_plurals(
        'swedish_word_inflections_v4.2_refined.json',
        'swedish_word_inflections_v4.3.json'
    )
