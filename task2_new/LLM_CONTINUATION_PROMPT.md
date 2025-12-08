# CLINIC SERVICES SCRAPING - LLM CONTINUATION PROMPT

## Getting Started

**First step:** Check current progress by running the status command (see Step 0 below).

---

## Task Overview
Extract podiatry services from Australian clinic web pages and update a JSON database. All clinics are accessed via Wayback Machine archive URLs containing cached pages.

**Constraint:** Process SEQUENTIALLY - one clinic at a time (no batch processing)

---

## Exact Process to Follow

### Step 0: Check Current Progress
```bash
cd "d:\Work\Mindrift\task2_new"
python status_report.py
```

This will show you:
- Total clinics scraped vs remaining
- Progress breakdown by region
- List of already completed clinics

---

### Step 1: Determine Next Clinic
```bash
cd "d:\Work\Mindrift\task2_new"
python next_clinic.py
```

**Output format:**
```
NEXT CLINIC TO SCRAPE
Progress: XX/104 (XX%) | Remaining: XX

CLINIC #XX:
Region: [Region Name]
Name: [Clinic Name]
URL FOR APIFY (copy and use in mcp_apify_rag-web-browser):
https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/[clinic-slug]/
```

**Note:** Copy the full URL from output - this is critical for Apify web scraper.

---

### Step 2: Scrape Clinic Page with Apify Web Browser
Use the `mcp_apify_apify-slash-rag-web-browser` tool with these exact parameters:

**Tool Settings:**
- `maxResults: 1`
- `outputFormats: ["markdown"]`
- `query: [URL from step 1]`

**Example Command:**
```
Tool: mcp_apify_apify-slash-rag-web-browser
Parameters:
  maxResults: 1
  outputFormats: ["markdown"]
  query: https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/[clinic-slug]/
```

**Expected Output:** Markdown content containing clinic details and services list.

---

### Step 3: Extract Services from Markdown

From the markdown response, locate and extract services using this regex-based pattern:

1. **Find the Services section:**
   - Pattern: `##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)`
   - This captures content between "## Services Available" and the next section

2. **Extract service names:**
   - Within that section, find all `###` level headings
   - Pattern: `^###\s+(.+?)(?:\n|$)`
   - Examples: `### Clinical Podiatry`, `### Health Funds`, etc.

3. **Clean service names:**
   - Remove markdown link syntax: `\[([^\]]+)\]\([^\)]+\)` → `\1`
   - Result: `Clinical Podiatry` instead of `[Clinical Podiatry](url)`

4. **Handle special cases:**
   - If no "Services Available" section exists, save with **0 services** (placeholder: "None")
   - Some clinics have no services listed (e.g., Allsports Podiatry Aspley, Advanced Foot Care Monto, Allsports Podiatry Pimpama)

**Expected Services List (example from My FootDr Burwood):**
```
Clinical Podiatry
Health Funds
Custom Foot Orthotics
Video Gait Analysis
Diabetes and Footcare
National Disability Insurance Scheme (NDIS)
CAM Walker (Moon Boot)
Shockwave Therapy
Footwear
Resources
```

---

### Step 4: Save Services to JSON

Once services are extracted, run this command:

```bash
python save_and_continue.py "Region Name" "Clinic Name" "service1|service2|service3|..."
```

**Format Details:**
- Services separated by pipe character `|` (no spaces around pipes)
- Region Name: Exact match from JSON (e.g., "New South Wales", "Victoria", "South Australia")
- Clinic Name: Exact match from JSON
- If no services: use placeholder `"None"` or the clinic name will fail

**Example Commands Executed Previously:**
```bash
python save_and_continue.py "New South Wales" "My FootDr Burwood" "Clinical Podiatry|Health Funds|Custom Foot Orthotics|Video Gait Analysis|Diabetes and Footcare|National Disability Insurance Scheme (NDIS)|CAM Walker (Moon Boot)|Shockwave Therapy|Footwear|Resources"

python save_and_continue.py "North Queensland" "Foundation Podiatry" "None"

python save_and_continue.py "Northern Territory" "My FootDr Palmerston" "Clinical Podiatry|Health Funds|Custom Foot Orthotics|Video Gait Analysis|Fungal Nail Infection Laser Treatment|Diabetes and Footcare|National Disability Insurance Scheme (NDIS)|CAM Walker (Moon Boot)|Footwear|Cryotherapy For Plantar Warts|Resources"
```

**Expected Output:**
```
✓ [Clinic Name]: XX services saved
```

---

### Step 5: Repeat for Next Clinic
Go back to Step 1. The workflow continues until all 104 clinics are complete.

**Progress Check (Optional):**
At any time, verify progress with:
```bash
python status_report.py
```

---

## Complete Workflow Loop

```
0. python status_report.py                             [Check current progress]
1. python next_clinic.py                               [Get next clinic URL & details]
2. mcp_apify_rag-web-browser [URL]                     [Scrape clinic page as markdown]
3. Extract services using regex from markdown          [Parse response locally]
4. python save_and_continue.py "Region" "Name" "svc1|svc2|..."  [Save to JSON]
5. REPEAT → Go to step 1
```

---

## Key Data Files

**Location:** `d:\Work\Mindrift\task2_new\`

- **`data/clinic_service_2.json`** - Main output file (DO NOT edit manually)
  - Structure: `regions → region_name → clinics → clinic_name → {services: [], scraped: true/false, link: url}`
  
- **`next_clinic.py`** - Identifies next unscraped clinic
- **`save_and_continue.py`** - Saves to JSON and marks clinic as scraped
- **`status_report.py`** - Shows progress breakdown by region

---

## Completed Regions

Run `python status_report.py` to see the current status of all regions and completed clinics.

---

## Service Names Reference (Typical Services Found)

Common services that appear across clinics:
- Clinical Podiatry
- Health Funds
- Custom Foot Orthotics
- Video Gait Analysis
- Fungal Nail Infection Laser Treatment
- Diabetes and Footcare
- Custom Footwear
- National Disability Insurance Scheme (NDIS)
- CAM Walker (Moon Boot)
- Cosmetic Nail Restoration
- Shockwave Therapy
- Footwear
- Paraffin Wax Bath Treatment
- Cryotherapy For Plantar Warts
- Resources
- Ankle-Foot Orthoses

---

## Important Notes

1. **Sequential Processing:** Do NOT batch scrape multiple clinics in parallel. Process one at a time to manage resources.

2. **Service Extraction:** The regex patterns are designed to extract `###` level headings from within the "## Services Available" section. 

3. **Zero-Service Clinics:** Some clinics legitimately have 0 or 1 service (placeholder). This is normal - save as-is.

4. **Exact Naming:** Region and clinic names MUST match exactly as they appear in the JSON file. Use the output from `next_clinic.py`.

5. **Wayback Machine URLs:** All URLs are from web.archive.org - these are cached versions, not live sites. This ensures stable, reproducible scraping.

6. **Working Directory:** Always operate from `d:\Work\Mindrift\task2_new\`

---

## Quick Start Command

To begin (or continue) the scraping process:

```bash
cd "d:\Work\Mindrift\task2_new"
python status_report.py                    [Check current progress first]
python next_clinic.py                      [Get the next clinic to scrape]
```

Then follow the exact process above for each clinic until completion.

---
