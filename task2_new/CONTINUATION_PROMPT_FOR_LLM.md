# CONTINUATION PROMPT FOR CLINIC SERVICES SCRAPING - TASK 2

## CURRENT STATUS & PROGRESS

**Workspace Location:** `d:\Work\Mindrift\task2_new\`

**JSON File Location:** `d:\Work\Mindrift\task2_new\data\clinic_service_2.json`

**Total Clinics:** 97 across 11 Australian regions

**Currently Scraped:** 6 clinics (5.8% complete)
- ✅ Allsports Podiatry Albany Creek (8 services)
- ✅ Allsports Podiatry Aspley (0 services - no Services Available section)
- ✅ Allsports Podiatry Calamvale (9 services including CAM Walker)
- ✅ Allsports Podiatry Camp Hill (9 services including CAM Walker)
- ✅ Allsports Podiatry Indooroopilly (9 services including CAM Walker)
- ✅ Allsports Podiatry Red Hill (8 services including CAM Walker)

**Remaining:** 98 clinics (94.2%)

---

## HELPER SCRIPTS FOR STATUS CHECKING

**Before starting and during work, use these scripts to understand current progress:**

1. **`status_report.py`** - Comprehensive progress overview
   ```bash
   python status_report.py
   ```
   Shows: Overall progress %, progress by region with visual progress bars, list of all already-scraped clinics with service counts

2. **`show_remaining.py`** - List all remaining clinics to scrape by region
   ```bash
   python show_remaining.py
   ```
   Shows: Total remaining count (98), organized by region, with sample clinic names and counts per region

3. **`show_progress.py`** - Quick progress check with next 5 clinics
   ```bash
   python show_progress.py
   ```
   Shows: Quick summary (6/97 done), next 5 clinics to scrape with URLs

4. **`next_clinic.py`** - Get the NEXT SINGLE clinic to scrape (PRIMARY TOOL FOR LLM)
   ```bash
   python next_clinic.py
   ```
   Shows: Clinic #N, region, clinic name, exact URL to use in Apify, and workflow steps
   **USE THIS BEFORE EVERY SCRAPE** to get the next clinic URL and region/name for JSON update

**Workflow pattern:**
```
python next_clinic.py                    # Get next clinic URL & update info
↓
mcp_apify_rag-web-browser [URL]         # Scrape the clinic page
↓
extract_services_from_markdown()        # Parse markdown for services
↓
save_clinic_to_json(region, name, svc)  # Update JSON
↓
python next_clinic.py                    # Repeat!
```

---

## CURRENT STATUS (as of this prompt creation)

**✓ 6 Clinics Already Scraped:**
1. Allsports Podiatry Albany Creek (8 services)
2. Allsports Podiatry Aspley (0 services)
3. Allsports Podiatry Calamvale (9 services)
4. Allsports Podiatry Camp Hill (9 services)
5. Allsports Podiatry Indooroopilly (9 services)
6. Allsports Podiatry Red Hill (8 services)

**⏳ 98 Clinics Remaining:**
- Brisbane: 25 more (19% done, 31 total)
- Victoria: 15 clinics
- NSW: 12 clinics
- South Australia: 9 clinics
- Central Queensland: 8 clinics
- Sunshine Coast: 8 clinics
- Gold Coast: 7 clinics
- North Queensland: 6 clinics
- Western Australia: 5 clinics
- Tasmania: 2 clinics
- Northern Territory: 1 clinic

**Next Clinic to Scrape:** Allsports Podiatry Forest Lake (Brisbane) - Run `python next_clinic.py`

---

## YOUR TASK

**Primary Objective:** Scrape individual clinic pages and extract their unique services, updating the JSON file with actual scraped data (NOT generic fallbacks).

**Critical Rules:**
1. **SEQUENTIAL PROCESSING ONLY** - Scrape one clinic at a time, NOT in parallel
2. **NO GENERIC FALLBACKS** - Only save services actually found on each clinic's page
3. **IMMEDIATE JSON UPDATES** - Save to JSON after EVERY clinic (don't wait for batches)
4. **EXACT SERVICE NAMES** - Extract from `### [Service Name](url)` markdown headings
5. **TOKEN AWARE** - Use sequential approach to manage token budget across conversations

---

## EXTRACTION LOGIC

### Markdown Pattern to Extract
Each clinic page has a "## Services Available" section containing service headings at the `###` level:

```markdown
## Services Available

### [Clinical Podiatry](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/clinical-podiatry/)

Our centres provide the full scope of clinical podiatry...

### [Health Funds](https://web.archive.org/web/20250517064322/https://www.myfootdr.com.au/our-services/health-funds/)

At My FootDr we are passionate about providing...
```

### Python Extraction Function (CORRECT)

```python
import json
import re
from pathlib import Path
from typing import List

def extract_services_from_markdown(markdown: str) -> List[str]:
    """Extract services from markdown using regex."""
    services = []
    
    # Find Services Available section
    services_match = re.search(
        r'##\s+Services?\s+Available\s*\n(.*?)(?=\n##\s|\Z)',
        markdown,
        re.IGNORECASE | re.DOTALL
    )
    
    if not services_match:
        return []  # No services section - return empty list
    
    services_section = services_match.group(0)
    
    # Extract all ### level headings
    service_lines = re.findall(r'^###\s+(.+?)(?:\n|$)', services_section, re.MULTILINE)
    
    for line in service_lines:
        # Remove markdown links [text](url) → text
        service_name = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        service_name = service_name.strip()
        
        # Only add meaningful services
        if service_name and len(service_name) > 3:
            services.append(service_name)
    
    return services

def save_clinic_to_json(region: str, clinic_name: str, services: List[str]) -> None:
    """Update JSON with scraped services."""
    json_file = Path("data/clinic_service_2.json")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if region in data.get("regions", {}) and clinic_name in data["regions"][region].get("clinics", {}):
        data["regions"][region]["clinics"][clinic_name]["services"] = services
        data["regions"][region]["clinics"][clinic_name]["scraped"] = True
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ {clinic_name}: {len(services)} services saved")
    else:
        print(f"✗ ERROR: Could not find {clinic_name} in {region}")
```

---

## WORKFLOW FOR EACH CLINIC

**For EVERY remaining clinic, follow this exact sequence:**

1. **Get next unscraped clinic URL** from `data/clinic_service_2.json`
   - Look for `"scraped": false` entries

2. **Call Apify web scraper:**
   ```
   Tool: mcp_apify_apify-slash-rag-web-browser
   Query: [paste the clinic URL from the JSON]
   outputFormats: ["markdown"]
   maxResults: 1
   ```

3. **Extract services from markdown response:**
   - Use the regex pattern above
   - Remove markdown link syntax: `[Service Name](url)` → `Service Name`
   - Return list of service strings

4. **Immediately update JSON:**
   - Set `"services": [list of extracted services]`
   - Set `"scraped": true`
   - Save to file

5. **Print progress:**
   ```
   ✓ Clinic Name: X services saved
   Progress: Y/97 clinics done
   ```

6. **Loop to next clinic** - Repeat for all remaining 98 clinics

---

## JSON STRUCTURE

**Current Structure Location:** `data/clinic_service_2.json`

```json
{
  "scrape_metadata": {...},
  "regions": {
    "Brisbane": {
      "clinics": {
        "Allsports Podiatry Albany Creek": {
          "services": ["Clinical Podiatry", "Health Funds", ...],
          "scraped": true,
          "link": "https://web.archive.org/web/..."
        },
        "Next Clinic": {
          "services": [],
          "scraped": false,
          "link": "https://web.archive.org/web/..."
        }
      }
    },
    "Victoria": {...},
    ...
  }
}
```

**What to update:**
- Change `"scraped": false` → `true` after scraping
- Replace `"services": []` with actual extracted services
- NEVER modify the `"link"` field

---

## NEXT CLINICS TO SCRAPE (In Order)

**Brisbane Region (26 remaining of 31 total):**
1. Allsports Podiatry Forest Lake
2. Allsports Podiatry Hawthorne
3. Allsports Podiatry Kangaroo Point
4. Allsports Podiatry The Gap
5. Allsports Podiatry Toowong
6. Allsports Podiatry Wavell Heights
7. Anytime Physio & Podiatry Newstead
8. My FootDr Brisbane CBD
9. My FootDr Brookside
10. My FootDr Brookwater
11. My FootDr Camp Hill
12. My FootDr Cleveland
13. My FootDr Fortitude Valley
14. My FootDr Gumdale
15. My FootDr Indooroopilly
16. My FootDr Ipswich
17. My FootDr Jindalee
18. My FootDr Mt Gravatt
19. My FootDr North Lakes
20. My FootDr Red Hill
21. My FootDr Redcliffe
22. My FootDr Shailer Park
23. My FootDr Stafford
24. My FootDr Toowoomba
25. My FootDr Wellington Point

**Then Victoria (15 clinics), NSW (12), SA (9), Central QLD (8), Sunshine Coast (8), Gold Coast (7), North QLD (6), WA (5), Tasmania (2), Northern Territory (1)**

---

## KEY EXAMPLES OF UNIQUE SERVICES

Some clinics have unique services NOT found in all clinics:

- **CAM Walker (Moon Boot)** - Present in: Calamvale, Camp Hill, Indooroopilly, Red Hill (and possibly others)
- **Clinical Podiatry** - Standard in most clinics
- **Health Funds** - Standard in most clinics
- **Resources** - Standard in most clinics
- **NDIS** - Standard in most clinics

**Aspley Example:** No Services Available section = 0 services (NOT 8 generic ones)

---

## CRITICAL SUCCESS FACTORS

✅ **DO:**
- Extract ONLY services from `### headings` in Services Available section
- Save immediately after each clinic
- Process sequentially (one at a time)
- Keep the URL/link field unchanged
- Use raw strings in Python to avoid escape sequence errors

❌ **DON'T:**
- Use generic fallback services
- Scrape multiple clinics in parallel
- Wait to batch multiple clinics before saving
- Modify the structure of the JSON
- Use hardcoded service lists

---

## QUICK START CHECKLIST

**START HERE:**
1. [ ] Check workspace: `d:\Work\Mindrift\task2_new\`
2. [ ] Run: `python status_report.py` - See full progress
3. [ ] Run: `python next_clinic.py` - Get next clinic to scrape
4. [ ] Copy the URL shown by next_clinic.py

**FOR EACH CLINIC (repeat 98 times):**
1. [ ] Run `python next_clinic.py` to get: region name, clinic name, and URL
2. [ ] Call `mcp_apify_rag-web-browser` with the URL from step 1
3. [ ] Get markdown response from Apify
4. [ ] Extract services using the regex function (extract_services_from_markdown)
5. [ ] Call `save_clinic_to_json(region, clinic_name, services_list)`
6. [ ] Verify save by checking JSON file (services should be populated and scraped=true)
7. [ ] Print: `✓ Clinic Name: X services saved (Y/97 total)`
8. [ ] Loop back to step 1 for next clinic

**VERIFICATION:**
- [ ] After every 5-10 clinics, run `python status_report.py` to verify saves working
- [ ] Should see progress bar growing and scraped count increasing
- [ ] If clinic doesn't appear in "CLINICS ALREADY SCRAPED" section, debug the save function

**COMPLETION:**
- [ ] When all 97 clinics show `scraped: true` in JSON
- [ ] Run `python status_report.py` - should show 97/97 (100%)
- [ ] Task is complete!

---

## VERIFYING SAVES ARE WORKING

**After updating a clinic, verify the JSON was saved:**

```bash
# Quick check: Shows first 3 remaining clinics
python show_remaining.py

# Detailed check: Shows progress bar and all scraped clinics
python status_report.py

# Look for your clinic in the "CLINICS ALREADY SCRAPED" section
# If it's not there after the save function runs, something went wrong
```

**If a clinic doesn't appear in scraped list after save:**
1. Check the file path in `save_clinic_to_json()` - must be `data/clinic_service_2.json`
2. Verify region name matches exactly (case-sensitive)
3. Verify clinic name matches exactly (case-sensitive)
4. Ensure JSON syntax is valid (run `python -m json.tool data/clinic_service_2.json`)

---

## STOPPING POINT

When all clinics have `"scraped": true` in the JSON, the task is complete. This will result in:
- 97 clinics with their actual unique services extracted
- No generic fallback data
- Accurate representation of each clinic's offerings

Total expected time: ~97 sequential API calls to mcp_apify_rag-web-browser

Good luck! The foundation is solid - just keep processing clinics one-by-one and the JSON will be complete.
