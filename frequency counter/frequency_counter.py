import json
import re
import sys
from collections import Counter

def create_frequency_dict(input_file, output_file):
    """
    Create a frequency dictionary from a text file and save it as JSON.
    
    Args:
        input_file: Path to input TXT file
        output_file: Path to output JSON file
    """
    try:
        # Read the text file with robust encoding handling
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Convert to lowercase and extract words (lowercase letters only, no digits)
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    # Count word frequencies
    word_counts = Counter(words)
    
    # Sort by frequency (descending), then alphabetically
    sorted_words = sorted(word_counts.items(), 
                         key=lambda x: (-x[1], x[0]))
    
    # Convert to list of objects for robust ordering
    freq_list = [{"word": word, "freq": count} for word, count in sorted_words]
    
    # Save to JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(freq_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    # Print statistics
    total_words = sum(word_counts.values())
    unique_words = len(word_counts)
    print(f"Successfully processed: {input_file}")
    print(f"Total words: {total_words:,}")
    print(f"Unique words: {unique_words:,}")
    print(f"Output saved to: {output_file}")
    print(f"\nTop 10 most frequent words:")
    for item in freq_list[:10]:
        print(f"  {item['word']}: {item['freq']}")

def print_help():
    """Print usage instructions."""
    help_text = """
Word Frequency Counter
======================

Usage:
    python word_frequency_counter.py <input_file.txt> <output_file.json>

Arguments:
    input_file.txt   - Path to the input text file to analyze
    output_file.json - Path where the frequency JSON will be saved

Example:
    python word_frequency_counter.py alice_wonderland.txt frequency.json

Description:
    This script analyzes word frequencies in a text file and outputs a JSON
    file containing words sorted by frequency (descending) and alphabetically
    for words with equal frequency.
    
    Tokenization: Extracts lowercase alphabetic words only (a-z), excluding
    numbers, punctuation, and special characters.

Output Format:
    The JSON output is an ordered list of objects:
    [
      {"word": "the", "freq": 1642},
      {"word": "and", "freq": 872},
      ...
    ]
"""
    print(help_text)

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) == 2 and sys.argv[1] in ['-h', '--help', 'help']:
        print_help()
        sys.exit(0)
    
    if len(sys.argv) != 3:
        print("Error: Invalid number of arguments.\n")
        print("Usage: python word_frequency_counter.py <input_file.txt> <output_file.json>")
        print("For more information, run: python word_frequency_counter.py --help")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    create_frequency_dict(input_file, output_file)
