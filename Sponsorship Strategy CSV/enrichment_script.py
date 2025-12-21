import os
import pandas as pd
import json
import time
from dotenv import load_dotenv
from apify_client import ApifyClient

# Load environment variables
load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
if not APIFY_TOKEN:
    raise ValueError("APIFY_TOKEN not found in .env file")

client = ApifyClient(APIFY_TOKEN)

# Get script directory to ensure correct file paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "input.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "processed_contacts.jsonl")
FINAL_OUTPUT_MD = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.md")
FINAL_OUTPUT_CSV = os.path.join(SCRIPT_DIR, "Sponsorship_Strategy_Analysis.csv")

# --- Helper Functions ---

def parse_role_column(role_str):
    """
    Extracts Job Title and Company from the Role column.
    Assumes format: "Title, Company" or similar.
    """
    if not isinstance(role_str, str):
        return "Unknown Role", "Unknown Company"
    
    parts = role_str.split(',', 1)
    if len(parts) > 1:
        title = parts[0].strip()
        company = parts[1].strip()
    else:
        title = role_str.strip()
        company = "Unknown Company" # Will try to find via search if possible, or leave as is
    return title, company

def determine_category(role, company, sector):
    """
    Categorizes target into Category A (Sponsor) or Category B (Booker).
    """
    role_lower = role.lower()
    company_lower = company.lower()
    sector_lower = sector.lower() if isinstance(sector, str) else ""

    # Keywords for Category B: Cultlab Artists Booker (Music industry, venues, promoters)
    booker_keywords = [
        "venue", "promoter", "booking", "programmer", "artistic director", 
        "talent", "music", "festival", "label", "record", "agent", "manager",
        "production", "event", "live"
    ]
    
    # Keywords for Category A: Jazzylea Festival Sponsor (Corporate, Marketing, Brand)
    sponsor_keywords = [
        "marketing", "brand", "sponsorship", "partnership", "director", "head of",
        "ceo", "founder", "corporate", "relations", "development", "commercial",
        "communication", "philanthrop", "investor"
    ]

    # Logic: Check Booker first as it's more specific to the music industry function
    if any(kw in role_lower for kw in booker_keywords) or \
       any(kw in company_lower for kw in booker_keywords) or \
       "festival" in sector_lower:
        return "Category B: Cultlab Artists Booker"
    
    # Default to Sponsor if high-level corporate role
    if any(kw in role_lower for kw in sponsor_keywords):
        return "Category A: Jazzylea Festival Sponsor"

    # Fallback based on sector if available
    if "partner" in sector_lower:
        return "Category A: Jazzylea Festival Sponsor"

    return "Category A: Jazzylea Festival Sponsor" # Default fallback

def estimate_potential_value(category, role, company_scale):
    """
    Estimates potential value: $, $$, $$$
    """
    role_lower = role.lower()
    
    is_high_level = any(x in role_lower for x in ["ceo", "founder", "president", "chief", "head", "director", "vp"])
    is_global = company_scale == "Global"
    
    if category == "Category A: Jazzylea Festival Sponsor":
        if is_global and is_high_level:
            return "$$$"
        elif is_global or is_high_level:
            return "$$"
        else:
            return "$"
    else: # Category B
        if is_high_level and is_global: # Major venue or promoter
            return "$$$"
        elif is_high_level or is_global:
            return "$$"
        else:
            return "$"

def generate_hook(category, name, company, role, business_category):
    """
    Generates a strategic hook.
    """
    if category == "Category A: Jazzylea Festival Sponsor":
        return f"Leveraging {company}'s leadership in {business_category} to elevate the Jazzylea Festival experience for a premium audience."
    else:
        return f"Partnering with {company} to bring cutting-edge talent to Cultlab's stage, aligning with your work in {business_category}."

def run_apify_search(queries):
    """
    Runs the Google Search Scraper actor for a list of queries.
    """
    run_input = {
        "queries": "\n".join(queries),
        "maxPagesPerQuery": 1,
        "resultsPerPage": 5, # Increased to 5 to find better results
        "countryCode": "gb", 
        "languageCode": "en",
    }
    
    print(f"Starting Apify run for {len(queries)} queries...")
    run = client.actor("apify/google-search-scraper").call(run_input=run_input)
    print(f"Apify run finished: {run['id']}")
    
    # Fetch results
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items
    return dataset_items

def determine_business_category(company, snippet):
    """
    Determines business category based on company name and search snippet.
    """
    text = (company + " " + snippet).lower()
    
    categories = {
        "Ticketing / Live Entertainment": ["ticket", "event", "live", "festival", "concert", "booking", "venue", "entertainment"],
        "Insurance": ["insurance", "risk", "underwriting", "broker", "claims"],
        "Marketing / Advertising": ["marketing", "agency", "brand", "creative", "digital", "advertising", "pr ", "public relations"],
        "Food & Beverage": ["food", "drink", "culinary", "beverage", "restaurant", "catering", "brewery", "distillery"],
        "Technology": ["software", "platform", "app", "tech", "digital", "data", "saas", "cloud", "it services"],
        "Media / Publishing": ["media", "news", "publishing", "broadcast", "radio", "tv", "magazine"],
        "Finance": ["bank", "invest", "capital", "finance", "wealth", "fund", "asset"],
        "Legal": ["law", "legal", "solicitor", "attorney"],
        "Consulting": ["consulting", "consultancy", "advisory", "strategy"],
        "Retail": ["retail", "shop", "store", "fashion", "apparel"],
        "Education": ["university", "college", "school", "education", "training"],
        "Healthcare": ["health", "medical", "pharma", "care"],
        "Real Estate": ["real estate", "property", "development", "construction"],
        "Non-Profit": ["charity", "foundation", "non-profit", "ngo", "association"]
    }
    
    for category, keywords in categories.items():
        if any(kw in text for kw in keywords):
            return category
            
    return "Business Services" # Default fallback

def determine_scale(company, snippet, country):
    """
    Determines scale (Global/Local) based on snippet and country.
    """
    text = snippet.lower()
    if any(kw in text for kw in ["global", "worldwide", "international", "multinational", "across the globe", "world's leading"]):
        return "Global"
    
    # Known global entities (simple list)
    known_global = ["ticketmaster", "coca-cola", "pepsi", "google", "amazon", "microsoft", "apple", "spotify", "live nation", "aeg"]
    if any(kg in company.lower() for kg in known_global):
        return "Global"

    if country == "UK":
        return "Local" # Default for UK if no global indicators
    
    return "Global" # Default for non-UK (often implies international context in this dataset)

def get_clean_website(url):
    """
    Cleans a URL to be just the homepage if it looks like a deep link to a person.
    """
    if not url:
        return "none"
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        # If path contains 'person', 'profile', 'people', it's likely not the main company site we want
        if any(x in parsed.path.lower() for x in ['/person', '/profile', '/people', '/in/']):
            return f"{parsed.scheme}://{parsed.netloc}"
    except:
        pass
    
    return url

def process_search_results(search_results, original_data_batch):
    """
    Matches search results back to original data and extracts info.
    """
    enriched_data = []
    
    # Map results by query for easier lookup
    results_by_query = {}
    for item in search_results:
        query = item.get("searchQuery", {}).get("term")
        if query:
            if query not in results_by_query:
                results_by_query[query] = []
            results_by_query[query].extend(item.get("organicResults", []))

    for row in original_data_batch:
        name = row['Name']
        raw_role = row['Role']
        extracted_title, extracted_company = parse_role_column(raw_role)
        
        # Reconstruct the query used
        query = f"{name} {extracted_company} {extracted_title} business profile linkedin"
        
        results = results_by_query.get(query, [])
        
        # Extraction logic
        linkedin_url = "none"
        website = "none"
        hq_location = "none" 
        business_category = "Business Services" # Default
        combined_snippet = ""
        
        # Try to find LinkedIn and Website from results
        for res in results:
            url = res.get("url", "")
            title = res.get("title", "")
            snippet = res.get("description", "")
            combined_snippet += " " + snippet
            
            if "linkedin.com/in/" in url and linkedin_url == "none":
                linkedin_url = url
            
            if "linkedin.com" not in url and website == "none" and "facebook" not in url and "instagram" not in url:
                website = url

            if "based in" in snippet.lower() and hq_location == "none":
                try:
                    hq_location = snippet.lower().split("based in")[1].split(".")[0].strip().title()
                except:
                    pass
        
        # Refine Company Name if "Unknown"
        final_company = extracted_company
        if final_company == "Unknown Company" and website != "none":
             try:
                 from urllib.parse import urlparse
                 domain = urlparse(website).netloc
                 final_company = domain.replace("www.", "").split(".")[0].title()
             except:
                 pass

        # Clean Website
        website = get_clean_website(website)

        # Determine Business Category
        business_category = determine_business_category(final_company, combined_snippet)

        # Determine Scale
        scale = determine_scale(final_company, combined_snippet, row.get("Country"))
        if "Global" in raw_role or "International" in raw_role:
            scale = "Global"

        # Categorize
        target_category = determine_category(extracted_title, final_company, row.get("Sector", ""))
        
        # Value
        potential_value = estimate_potential_value(target_category, extracted_title, scale)
        
        # Hook
        hook = generate_hook(target_category, name, final_company, extracted_title, business_category)

        enriched_row = {
            "Confiva Link": row.get("Confiva Link", ""),
            "Target Name": name,
            "Role": extracted_title,
            "Company": final_company,
            "Business Category": business_category,
            "Website": website,
            "HQ Location": row.get("Country", "Unknown") if hq_location == "none" else hq_location,
            "Scale (Global/Local)": scale,
            "Target Category": target_category,
            "LinkedIn Profile": linkedin_url,
            "Strategic Hook": hook,
            "Potential Value": potential_value,
            "Outreach Message": ""
        }
        enriched_data.append(enriched_row)
        
    return enriched_data

# --- Main Execution ---

def main():
    # 1. Load Data
    df = pd.read_csv(INPUT_FILE)
    total_rows = len(df)
    print(f"Loaded {total_rows} rows from {INPUT_FILE}")

    # 2. Check Progress
    processed_count = 0
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r') as f:
            processed_count = sum(1 for _ in f)
    
    print(f"Already processed: {processed_count}")
    
    # 3. Filter Data
    df_to_process = df.iloc[processed_count:]
    
    # TEST MODE: Limit to 10 rows
    # TEST_LIMIT = 10
    # if len(df_to_process) > TEST_LIMIT:
    #     print(f"TEST MODE: Limiting to first {TEST_LIMIT} rows.")
    #     df_to_process = df_to_process.head(TEST_LIMIT)
    
    if df_to_process.empty:
        print("No new rows to process.")
        return

    # 4. Batch Process
    BATCH_SIZE = 10 # Apify handles batches well
    
    # Convert to list of dicts for easier handling
    records = df_to_process.to_dict('records')
    
    for i in range(0, len(records), BATCH_SIZE):
        batch = records[i:i+BATCH_SIZE]
        print(f"Processing batch {i//BATCH_SIZE + 1} (Rows {processed_count + i + 1} to {processed_count + i + len(batch)})...")
        
        # Prepare Queries
        queries = []
        for row in batch:
            title, company = parse_role_column(row['Role'])
            # Query: Name + Company + Title + "business profile" to bias towards LinkedIn/Corporate
            query = f"{row['Name']} {company} {title} business profile linkedin"
            queries.append(query)
        
        # Call Apify
        try:
            search_results = run_apify_search(queries)
            enriched_batch = process_search_results(search_results, batch)
            
            # Save to JSONL
            with open(OUTPUT_FILE, 'a') as f:
                for item in enriched_batch:
                    f.write(json.dumps(item) + '\n')
            
            print(f"Batch saved.")
            
        except Exception as e:
            print(f"Error processing batch: {e}")
            # Ideally handle retry or logging here
            break
            
        # Sleep briefly to avoid rate limits if any (though Apify handles this)
        time.sleep(1)

    print("Test run complete.")

if __name__ == "__main__":
    main()
