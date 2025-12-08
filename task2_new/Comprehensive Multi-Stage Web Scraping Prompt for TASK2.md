TASK: Multi-Level Clinic Directory Web Scraping with Staged Data Collection

OBJECTIVE:
Scrape all clinic information from the My FootDr website archive using a staged approach with intermediate data storage, then compile into a final CSV file.

TARGET WEBSITE:
https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/

WEBSITE STRUCTURE (3 LEVELS):
1. Main Page: Lists all regions/locations (e.g., Sunshine Coast, Brisbane, Gold Coast, North Queensland, etc.)
2. Region Pages: Each region page contains multiple clinic listings (e.g., /regions/north-queensland/ shows Cairns, Thuringowa, Townsville, etc.)
3. Individual Clinic Pages: Each clinic has a dedicated page with detailed information

═══════════════════════════════════════════════════════════════════════════════
STAGE 1: DISCOVER AND MAP ALL REGIONS
═══════════════════════════════════════════════════════════════════════════════

GOAL: Extract all region/location links from the main page

MCP: you must use MCP Apify tools for web scraping. Suggested tools are provided below.

TOOL: mcp_apify_rag-web-browser or mcp_apify_website-content-crawler

ACTIONS:
1. Scrape the main page: https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/
2. Extract all region names and their corresponding URLs
3. Store results in: regions_mapping.json

OUTPUT STRUCTURE (regions_mapping.json):
```json
{
  "scrape_metadata": {
    "scrape_date": "2025-12-08",
    "source_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/",
    "total_regions": 11
  },
  "regions": [
    {
      "region_id": "sunshine-coast",
      "region_name": "Sunshine Coast",
      "region_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/regions/sunshine-coast/",
      "scrape_status": "pending"
    },
    {
      "region_id": "brisbane",
      "region_name": "Brisbane",
      "region_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/regions/brisbane/",
      "scrape_status": "pending"
    }
    // ... more regions
  ]
}
```

VALIDATION:
- Verify all region cards/links from the main page are captured
- Expected regions: ~11 based on website structure (Sunshine Coast, Brisbane, Gold Coast, North Queensland, Central Queensland, New South Wales, Victoria, South Australia, Western Australia, Northern Territory, Tasmania)

═══════════════════════════════════════════════════════════════════════════════
STAGE 2: DISCOVER ALL CLINICS PER REGION (BATCH PROCESSING)
═══════════════════════════════════════════════════════════════════════════════

GOAL: For each region, extract all clinic names and URLs

BATCH STRATEGY: Process 2-3 regions at a time to avoid timeouts and manage complexity

TOOL: mcp_apify_rag-web-browser or mcp_apify_website-content-crawler

ACTIONS FOR EACH REGION:
1. Read regions_mapping.json
2. Select next batch of regions with scrape_status="pending"
3. For each region in batch:
   - Visit the region page URL
   - Extract all clinic names and their detail page URLs
   - Store results in region-specific file
4. Update regions_mapping.json to mark regions as "completed"
5. Repeat until all regions processed

OUTPUT STRUCTURE (clinics_by_region.json):
```json
{
  "scrape_metadata": {
    "last_updated": "2025-12-08T14:30:00Z",
    "total_regions_processed": 11,
    "total_clinics_discovered": 114
  },
  "regions": {
    "sunshine-coast": {
      "region_name": "Sunshine Coast",
      "region_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/regions/sunshine-coast/",
      "total_clinics": 8,
      "scrape_status": "completed",
      "clinics": [
        {
          "clinic_id": "noosa",
          "clinic_name": "Podiatrist Noosa",
          "clinic_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/noosa/",
          "detail_scrape_status": "pending"
        },
        {
          "clinic_id": "maroochydore",
          "clinic_name": "Maroochydore Podiatry",
          "clinic_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/maroochydore/",
          "detail_scrape_status": "pending"
        }
        // ... more clinics
      ]
    },
    "north-queensland": {
      "region_name": "North Queensland",
      "region_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/regions/north-queensland/",
      "total_clinics": 5,
      "scrape_status": "completed",
      "clinics": [
        {
          "clinic_id": "cairns",
          "clinic_name": "Cairns",
          "clinic_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cairns/",
          "detail_scrape_status": "pending"
        }
        // ... more clinics
      ]
    }
    // ... more regions
  }
}
```

BATCH PROCESSING GUIDELINES:
- Batch 1: Sunshine Coast, Brisbane, Gold Coast
- Batch 2: North Queensland, Central Queensland, New South Wales
- Batch 3: Victoria, South Australia, Western Australia
- Batch 4: Northern Territory, Tasmania
- Allow 2-5 minutes between batches to respect rate limits
- Log progress after each batch

VALIDATION PER BATCH:
- Verify all clinics from region page are captured
- Cross-check clinic count matches visual inspection
- Ensure URLs are complete and properly formatted

═══════════════════════════════════════════════════════════════════════════════
STAGE 3: SCRAPE DETAILED CLINIC INFORMATION (BATCH PROCESSING)
═══════════════════════════════════════════════════════════════════════════════

GOAL: Extract complete information from each individual clinic page

BATCH STRATEGY: Process 10-15 clinics at a time

TOOL: mcp_apify_website-content-crawler or mcp_apify_web-scraper

ACTIONS:
1. Read clinics_by_region.json
2. Select next batch of clinics with detail_scrape_status="pending"
3. Configure crawler to visit clinic detail pages
4. Extract all required fields using flexible matching
5. Store detailed results in clinic_details_full.json
6. Update clinics_by_region.json to mark clinics as "completed"
7. Repeat until all clinics processed

REQUIRED DATA FIELDS (with flexible matching):
- **Name of Clinic**: H1 tag, page title, or main heading
- **Address**: Look for:
  - Elements with class/id containing "address", "location", "contact"
  - Text near "Address:", "Location:", "Visit us at:"
  - Google Maps embedded links or direction links
  - Schema.org structured data (if available)
  
- **Email**: Look for:
  - mailto: links
  - Text patterns matching email format (xxx@xxx.xxx)
  - Contact form email addresses
  - Elements with class/id containing "email"
  
- **Phone**: Look for:
  - tel: links
  - Text near "Phone:", "Call:", "Contact:", "Tel:"
  - Patterns matching phone formats (1800 xxx xxx, (07) xxxx xxxx)
  - Click-to-call buttons
  
- **Services**: Look for:
  - Sections titled: "Services", "Our Services", "Services Available", "What We Offer", "Treatments", "Services Offered"
  - List items (ul/ol) in service sections
  - Service cards or tiles
  - "Services Available" headers with following content

OUTPUT STRUCTURE (clinic_details_full.json):
```json
{
  "scrape_metadata": {
    "last_updated": "2025-12-08T16:45:00Z",
    "total_clinics_scraped": 114,
    "successful_scrapes": 110,
    "failed_scrapes": 4,
    "completeness_rate": "96.5%"
  },
  "clinics_data": {
    "sunshine-coast": {
      "region_name": "Sunshine Coast",
      "clinics": [
        {
          "clinic_id": "noosa",
          "clinic_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/noosa/",
          "scrape_status": "success",
          "scrape_timestamp": "2025-12-08T16:20:15Z",
          "data": {
            "name_of_clinic": "Podiatrist Noosa - Orthotics, Ingrown Toenails",
            "address": "123 Sunshine Beach Road, Noosa Heads QLD 4567",
            "email": "noosa@myfootdr.com.au",
            "phone": "1800 366 837",
            "services": [
              "Custom Foot Orthotics",
              "Ingrown Toenail Treatment",
              "Diabetes and Footcare",
              "Shockwave Therapy",
              "Video Gait Analysis",
              "Heel Pain Treatment",
              "Bunion Treatment",
              "Sports Podiatry"
            ]
          },
          "raw_html_snippet": "<!-- Store for debugging if needed -->"
        },
        {
          "clinic_id": "cowboys-centre",
          "clinic_url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/cowboys-centre-of-excellence-nq-foot-ankle-centre/",
          "scrape_status": "success",
          "scrape_timestamp": "2025-12-08T16:22:30Z",
          "data": {
            "name_of_clinic": "NQ Foot & Ankle Centre Cowboys Centre of Excellence",
            "address": "26 Graham Murray Place, Railway Estate QLD 4810",
            "email": "kirwan@nqfootandankle.com.au",
            "phone": "07 4723 5500",
            "services": [
              "Custom Foot Orthotics",
              "Video Gait Analysis",
              "Diabetes and Footcare",
              "Shockwave Therapy"
            ]
          }
        }
        // ... more clinics
      ]
    },
    "north-queensland": {
      "region_name": "North Queensland",
      "clinics": [
        // ... clinics for this region
      ]
    }
    // ... more regions
  },
  "scrape_errors": [
    {
      "clinic_id": "example-failed-clinic",
      "clinic_url": "https://...",
      "error_type": "timeout",
      "error_message": "Page failed to load after 60 seconds",
      "timestamp": "2025-12-08T16:25:00Z"
    }
  ]
}
```

BATCH PROCESSING GUIDELINES:
- Process 10-15 clinics per batch
- Allow 1-2 minutes between batches
- Implement retry logic for failed scrapes (max 2 retries)
- Log progress with clinic counts: "Batch 3/10 completed: 45/114 clinics processed"

DATA EXTRACTION LOGIC:
```javascript
// Pseudo-code for flexible field extraction
function extractClinicData(page) {
  return {
    name: extractName(page),          // H1, title, or main heading
    address: extractAddress(page),    // Multiple strategies with fallbacks
    email: extractEmail(page),        // Regex + DOM search
    phone: extractPhone(page),        // Regex + DOM search
    services: extractServices(page)   // List extraction with flexible headers
  };
}

function extractServices(page) {
  // Strategy 1: Look for common service section headers
  const serviceHeaders = ['Services', 'Our Services', 'Services Available', 
                          'What We Offer', 'Treatments', 'Services Offered'];
  
  // Strategy 2: Extract list items following the header
  // Strategy 3: Extract from service cards/tiles
  // Return as array
}
```

VALIDATION PER BATCH:
- Check that at least 80% of clinics have all required fields
- Identify and log clinics with missing data
- Flag unusual patterns (e.g., all clinics missing email)

═══════════════════════════════════════════════════════════════════════════════
STAGE 4: TRANSFORM TO FINAL CSV FORMAT
═══════════════════════════════════════════════════════════════════════════════

GOAL: Convert the structured JSON data to the required CSV format

INPUT: clinic_details_full.json

ACTIONS:
1. Read clinic_details_full.json
2. Flatten the hierarchical structure
3. Transform services array to comma-separated string
4. Apply data cleaning rules
5. Generate CSV with exact column headers
6. Validate output

DATA TRANSFORMATION RULES:
- **Name of Clinic**: Use as-is from data.name_of_clinic
- **Address**: 
  - Remove extra whitespace and newlines
  - Replace multiple spaces with single space
  - Trim leading/trailing whitespace
  
- **Email**: 
  - Extract from mailto: if needed
  - Validate email format
  - Use "N/A" if missing
  
- **Phone**: 
  - Keep original format (don't reformat)
  - Trim whitespace
  - Remove invisible characters
  - Use "N/A" if missing
  
- **Services**: 
  - Join array with " | " separator (e.g., "Service 1 | Service 2 | Service 3")
  - OR use comma separation: "Service 1, Service 2, Service 3"
  - If services is empty/missing, use "N/A"
  - Remove duplicate services

CSV OUTPUT STRUCTURE (myfootdr_clinics.csv):
```csv
Name of Clinic,Address,Email,Phone,Services
"Podiatrist Noosa - Orthotics, Ingrown Toenails","123 Sunshine Beach Road, Noosa Heads QLD 4567",noosa@myfootdr.com.au,1800 366 837,"Custom Foot Orthotics | Ingrown Toenail Treatment | Diabetes and Footcare | Shockwave Therapy | Video Gait Analysis"
"NQ Foot & Ankle Centre Cowboys Centre of Excellence","26 Graham Murray Place, Railway Estate QLD 4810",kirwan@nqfootandankle.com.au,07 4723 5500,"Custom Foot Orthotics | Video Gait Analysis | Diabetes and Footcare | Shockwave Therapy"
...
```

QUALITY CHECKS:
- Total rows matches total clinics in clinic_details_full.json
- No duplicate clinic entries
- All required columns present with exact names
- CSV is properly escaped (quotes around fields containing commas)
- File can be opened in Excel/Google Sheets without errors

GENERATE SUMMARY REPORT:
```json
{
  "summary": {
    "total_regions": 11,
    "total_clinics_found": 114,
    "total_clinics_scraped": 110,
    "clinics_in_csv": 110,
    "data_completeness": {
      "all_fields_present": 105,
      "missing_email": 3,
      "missing_phone": 1,
      "missing_services": 1,
      "missing_address": 0
    },
    "scrape_duration": "~2 hours",
    "csv_file": "myfootdr_clinics.csv",
    "backup_files": [
      "regions_mapping.json",
      "clinics_by_region.json",
      "clinic_details_full.json"
    ]
  }
}
```

═══════════════════════════════════════════════════════════════════════════════
RECOMMENDED MCP APIFY TOOLS BY STAGE
═══════════════════════════════════════════════════════════════════════════════

STAGE 1 (Region Discovery):
- PRIMARY: mcp_apify_rag-web-browser
  - query: "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/"
  - maxResults: 1
  - outputFormats: ["markdown"]

STAGE 2 (Clinic Discovery):
- PRIMARY: mcp_apify_rag-web-browser (for smaller batches)
  - Process 2-3 region pages per call
- ALTERNATIVE: mcp_apify_website-content-crawler (for larger batches)
  - startUrls: [region URLs from batch]
  - maxCrawlDepth: 1

STAGE 3 (Detailed Scraping):
- PRIMARY: mcp_apify_website-content-crawler
  - startUrls: [clinic URLs from batch]
  - maxCrawlDepth: 0 (only scrape provided URLs)
  - crawlerType: "playwright:firefox"
  - saveMarkdown: true
  - htmlTransformer: "readableText"
  - maxConcurrency: 10
  
- Configure for batch processing:
```javascript
  {
    "startUrls": [
      {"url": "clinic_url_1"},
      {"url": "clinic_url_2"},
      // ... 10-15 URLs per batch
    ],
    "maxCrawlDepth": 0,
    "maxCrawlPages": 15,
    "proxyConfiguration": {"useApifyProxy": true}
  }
```

STAGE 4 (CSV Generation):
- Use standard file I/O and CSV libraries (no Apify tool needed)
- Python: pandas, csv module
- JavaScript: papaparse, csv-stringify

═══════════════════════════════════════════════════════════════════════════════
EXECUTION WORKFLOW
═══════════════════════════════════════════════════════════════════════════════

STEP-BY-STEP EXECUTION:

1. **Initialize Project Structure**
   - Create data/ directory for JSON files
   - Create output/ directory for CSV
   - Set up logging system

2. **Execute Stage 1**
   - Run region discovery
   - Save regions_mapping.json
   - Validate region count (~11 expected)
   - Manual review: Check if all visible regions captured

3. **Execute Stage 2 (Batch Loop)**
   - FOR each batch of 2-3 regions:
     - Run clinic discovery for batch
     - Update clinics_by_region.json
     - Log progress: "Batch X/Y: Discovered Z clinics"
     - Wait 2 minutes before next batch
   - END loop
   - Validate total clinic count (~100-120 expected)

4. **Execute Stage 3 (Batch Loop)**
   - FOR each batch of 10-15 clinics:
     - Run detailed scraper for batch
     - Update clinic_details_full.json
     - Log progress: "Scraped clinic X/Y"
     - Wait 1 minute before next batch
     - IF failures occur, add to retry queue
   - END loop
   - Process retry queue (max 2 retry attempts)
   - Generate scrape_errors.log for failed clinics

5. **Execute Stage 4**
   - Load clinic_details_full.json
   - Transform to CSV format
   - Apply data cleaning
   - Validate CSV structure
   - Generate myfootdr_clinics.csv
   - Create summary_report.json

6. **Final Validation**
   - Open CSV in spreadsheet software
   - Spot-check 10-15 random clinics against website
   - Verify data completeness
   - Review scrape_errors.log
   - Archive all intermediate JSON files

═══════════════════════════════════════════════════════════════════════════════
ERROR HANDLING & RECOVERY
═══════════════════════════════════════════════════════════════════════════════

CHECKPOINT SYSTEM:
- Each stage saves progress to JSON files
- If script fails, resume from last completed checkpoint
- Use scrape_status fields to track progress

RETRY LOGIC:
- Failed clinic scrapes: Retry up to 2 times with 30-second delay
- Timeout errors: Increase page load timeout on retry
- Network errors: Use different proxy on retry

FALLBACK STRATEGIES:
- If automated extraction fails for a field, mark as "MANUAL_REVIEW_NEEDED"
- Maintain a separate file: manual_review_needed.json
- Include URL and raw HTML snippet for manual extraction

RATE LIMITING:
- Respect Apify API rate limits
- Wait 1-2 minutes between batches
- Monitor for 429 (Too Many Requests) errors
- Implement exponential backoff if rate limited

═══════════════════════════════════════════════════════════════════════════════
SPECIAL CONSIDERATIONS
═══════════════════════════════════════════════════════════════════════════════

WEB ARCHIVE HANDLING:
- Archive.org URLs may have additional wrapper elements
- Some JavaScript may not execute properly in archived pages
- Use headless browser (Playwright/Puppeteer) for better compatibility
- If archive.org blocks scraping, consider alternative approaches

DATA QUALITY:
- Some clinics may have incomplete information on website
- Document which fields are commonly missing
- Provide data completeness metrics in summary report

PROXY CONFIGURATION:
- Use Apify's built-in proxy: {"useApifyProxy": true}
- Residential proxies recommended for archive.org
- Rotate proxies between batches

PERFORMANCE OPTIMIZATION:
- Disable unnecessary resource loading (images, fonts) to speed up scraping
- Use maxConcurrency wisely (don't exceed 10-15 for archive.org)
- Cache results to avoid re-scraping on failures

═══════════════════════════════════════════════════════════════════════════════
DELIVERABLES
═══════════════════════════════════════════════════════════════════════════════

PRIMARY OUTPUT:
✓ myfootdr_clinics.csv - Final CSV with all clinic data

INTERMEDIATE FILES (for reference/debugging):
✓ regions_mapping.json - All regions discovered
✓ clinics_by_region.json - All clinics organized by region
✓ clinic_details_full.json - Complete structured data
✓ summary_report.json - Scraping statistics and metrics
✓ scrape_errors.log - Failed scrapes and issues

DOCUMENTATION:
✓ execution_log.txt - Timestamped log of all operations
✓ data_quality_report.md - Analysis of data completeness
✓ manual_review_needed.json - Clinics requiring manual verification (if any)

═══════════════════════════════════════════════════════════════════════════════

Execute this multi-stage scraping task using the MCP Apify tools available in the development environment. Prioritize data integrity, completeness, and systematic progress tracking through all stages.

BEGIN WITH STAGE 1 and proceed sequentially through all stages.