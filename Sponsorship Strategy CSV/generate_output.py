import json
import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSONL = os.path.join(SCRIPT_DIR, "processed_contacts.jsonl")
OUTPUT_MD = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.md")
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.csv")

def main():
    data = []
    if os.path.exists(INPUT_JSONL):
        with open(INPUT_JSONL, 'r') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    
    if not data:
        print("No data found in processed_contacts.jsonl")
        return

    df = pd.DataFrame(data)
    
    # Ensure column order
    columns = [
        "Confiva Link", "Target Name", "Role", "Company", "Business Category", 
        "Website", "HQ Location", "Scale (Global/Local)", "Target Category", 
        "LinkedIn Profile", "Strategic Hook", "Potential Value", "Outreach Message"
    ]
    
    # Fill missing columns if any
    for col in columns:
        if col not in df.columns:
            df[col] = ""
            
    df = df[columns]
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved CSV to {OUTPUT_CSV}")
    
    # Save to Markdown
    markdown_table = df.to_markdown(index=False)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(markdown_table)
    print(f"Saved Markdown to {OUTPUT_MD}")

if __name__ == "__main__":
    main()
