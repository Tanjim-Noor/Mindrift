import pandas as pd
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.csv")
MD_PATH = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.md")

def main():
    if not os.path.exists(CSV_PATH):
        print(f"File not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH)
    print(f"Original rows: {len(df)}")

    # 1. Deduplicate based on 'Target Name' and 'Company'
    df = df.drop_duplicates(subset=['Target Name', 'Company'], keep='last')
    print(f"Rows after deduplication: {len(df)}")

    # 2. Fix FKP Scorpio
    # Category -> Ticketing / Live Entertainment
    # Scale -> Global
    mask_fkp = df['Company'].str.contains('FKP Scorpio', case=False, na=False)
    df.loc[mask_fkp, 'Business Category'] = 'Ticketing / Live Entertainment'
    df.loc[mask_fkp, 'Scale (Global/Local)'] = 'Global'
    
    # Update Strategic Hook for FKP Scorpio to reflect the new category
    # "Partnering with FKP Scorpio to bring cutting-edge talent to Cultlab's stage, aligning with your work in Ticketing / Live Entertainment."
    # We need to regenerate the hook for these rows
    for index, row in df[mask_fkp].iterrows():
        company = row['Company']
        category = row['Business Category']
        new_hook = f"Partnering with {company} to bring cutting-edge talent to Cultlab's stage, aligning with your work in {category}."
        df.at[index, 'Strategic Hook'] = new_hook

    # 3. Save CSV (Standard headers)
    df.to_csv(CSV_PATH, index=False)
    print(f"Saved patched CSV to {CSV_PATH}")

    # 4. Save Markdown (Backticked headers)
    md_columns = [f"`{col}`" for col in df.columns]
    df_md = df.copy()
    df_md.columns = md_columns
    markdown_table = df_md.to_markdown(index=False)
    
    with open(MD_PATH, 'w', encoding='utf-8') as f:
        f.write(markdown_table)
    print(f"Saved patched Markdown to {MD_PATH}")

if __name__ == "__main__":
    main()
