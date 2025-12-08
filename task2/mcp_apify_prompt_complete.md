**Reference context (MCP / Apify tools & behaviour — use these only as reference, do not change their docs):**

- Preferred actor for multi-page crawling: **`mcp_apify_web-scraper`** (supports `startUrls`, `pageFunction`, link selectors, concurrency control, and stores results in a dataset).  
- When running any Apify Actor via the MCP `call-actor` tool, use the required two-step workflow: first call with `step="info"` to retrieve the Actor input schema and README; then call with `step="call"` and provide `input`. Use `mcp_apify_fetch-actor-details` if you need extra actor README/schema detail.  
- After an actor run completes, use **`mcp_apify_get-actor-output`** with the resulting `datasetId` to retrieve items and convert them to the CSV required.  
- If you need to take screenshots for debugging, use `mcp_apify_screenshot-url`.  
- Be mindful of API / actor limits: keep `maxConcurrency` modest and include polite delays to avoid rate limiting. Use Apify proxy via `proxyConfiguration` to reduce blocking.

---

**Task to execute (instructions — required; be explicit and follow these precisely):**

1. **Goal:** Crawl the archived page at `https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/`, enter each region, then enter every clinic page and extract into a CSV with exactly these column names (no variations):
   - `Name of Clinic`
   - `Address`
   - `Email`
   - `Phone`
   - `Services`

2. **Tools to use (explicit):**
   - Primary: `mcp_apify_web-scraper` (call via `mcp_apify_call-actor` with two-step workflow).
   - Before calling, fetch actor details with `mcp_apify_fetch-actor-details` for `apify/web-scraper` (or the exact actor id if fetch shows a different name) to confirm input schema.
   - After run completes, retrieve results using `mcp_apify_get-actor-output` and convert to a CSV file.

3. **Two-step actor call flow (must be followed):**
   - Step A (info): Call `mcp_apify_call-actor` with `actor` = the web-scraper Actor name and `step="info"`. Parse the returned input schema and README to confirm exact parameter names.
   - Step B (call): Call `mcp_apify_call-actor` with `step="call"` and the `input` JSON provided below (adapt field names if the Actor schema names differ — but keep semantics identical).

4. **Actor `input` configuration (recommended defaults; set these in the `step="call"` input):**

```json
{
  "startUrls": [
    { "url": "https://web.archive.org/web/20250708180027/https://www.myfootdr.com.au/our-clinics/" }
  ],
  "pageFunction": "/* SEE BELOW: multi-purpose pageFunction JS */",
  "linkSelector": "a",
  "proxyConfiguration": { "useApifyProxy": true },
  "maxConcurrency": 5,
  "maxPagesPerCrawl": 1000,
  "maxCrawlingDepth": 4,
  "headless": true,
  "injectJQuery": false,
  "pageLoadTimeoutSecs": 60,
  "pageFunctionTimeoutSecs": 60,
  "respectRobotsTxtFile": false
}
```

> Note: If `mcp_apify_fetch-actor-details` shows different parameter names, map the above keys to the actor input schema fields. Keep concurrency low (5) and `maxPagesPerCrawl` conservative to avoid overload.

5. **PageFunction (exact JavaScript to include as the `pageFunction` string).**  
   - This function should enqueue region and clinic links when run on directory pages, and extract the target fields from clinic pages. It uses robust fallbacks (searches for mailto, tel, address-like blocks, lists of services). Paste this entire JS into the actor input `pageFunction` field (as a string) or reference it exactly if actor input supports inline code.

```javascript
// pageFunction: runs in browser context for each loaded page
async function pageFunction(context) {
  const { request, enqueueLinks, log } = context || {}; // some Apify actors supply these helpers

  // helper regexes
  function extractEmails(text) {
    if(!text) return [];
    return Array.from(new Set((text.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/ig) || []).map(s => s.trim())));
  }
  function extractPhones(text) {
    if(!text) return [];
    return Array.from(new Set((text.match(/(\\+?\\d{1,4}[\\s-])?(?:\\(?\\d+\\)?[\\s-]?){3,}/g) || []).map(s => s.trim())));
  }

  // utility: normalise whitespace
  function norm(t){ return (t||'').replace(/[\\t\\r\\n]+/g,' ').replace(/\\s{2,}/g,' ').trim(); }

  // If this looks like the main "regions" listing page -> enqueue region links
  const url = window.location.href;
  const results = [];

  // Heuristic: region links are anchors under the main content
  const regionAnchors = Array.from(document.querySelectorAll('a'))
    .filter(a => a.href && a.href.includes('/our-clinics') && a.hostname && a.href !== url);

  // Enqueue region links (if we are on the top page or an archive directory)
  if (regionAnchors.length > 0 && /our-clinics/i.test(document.body.innerText.slice(0, 1000))) {
    // Only enqueue links that look like region pages or anchors to subsections
    const uniqueRegionUrls = Array.from(new Set(regionAnchors.map(a => a.href)));
    for (const u of uniqueRegionUrls) {
      try { await enqueueLinks({ urls: [u] }); } catch(e) { /* ignore if not available */ }
    }
  }

  // When on any page, find clinic links and enqueue them (links to individual clinic pages)
  // Clinic links often contain the clinic slug or the word 'clinic' or city names
  const clinicCandidates = Array.from(document.querySelectorAll('a'))
    .filter(a => a.href && /clinic|our-clinics|podiatrist|/i.test(a.href) || /clinic|podiatrist|practice|our-clinics/i.test(a.textContent))
    .map(a => a.href);
  const clinicUrls = Array.from(new Set(clinicCandidates));
  for (const u of clinicUrls) {
    try { await enqueueLinks({ urls: [u] }); } catch(e) { /* ok */ }
  }

  // If this page appears to be a clinic detail page, extract required fields.
  // Heuristics for a clinic page: presence of address block, contact info, or an <h1> title
  const titleEl = document.querySelector('h1') || document.querySelector('title');
  const pageText = document.body.innerText || '';
  const hasContact = /@|tel:|\\+?0?[\\d\\s()-]{6,}|address|services/i.test(pageText);

  if (titleEl && hasContact) {
    // Extract name
    const name = norm(titleEl.textContent || document.title || '');

    // Extract emails (mailto links prioritized)
    const mailtoEls = Array.from(document.querySelectorAll('a[href^="mailto:"]'));
    let emails = mailtoEls.map(a => a.href.replace(/^mailto:/i,'').split('?')[0].trim());
    if (emails.length === 0) emails = extractEmails(pageText);

    // Extract phones (tel: links prioritized)
    const telEls = Array.from(document.querySelectorAll('a[href^=\"tel:\"]'));
    let phones = telEls.map(a => a.href.replace(/^tel:/i,'').trim());
    if (phones.length === 0) phones = extractPhones(pageText);

    // Extract address: look for elements with address-like class or <address> tag
    let address = '';
    const addressEl = document.querySelector('address') ||
                      document.querySelector('[class*=\"address\"]') ||
                      Array.from(document.querySelectorAll('p,div,li')).find(n => /[0-9]{1,4}\\s+\\w+/.test(n.textContent || ''));
    if (addressEl) address = norm(addressEl.innerText);

    // Extract services: look for ordered/unordered lists with known headings
    let services = '';
    // find a heading containing 'Services' or look for lists below headings
    const serviceHeading = Array.from(document.querySelectorAll('h2,h3,h4')).find(h=>/services|treatments|we offer|areas of practice/i.test(h.textContent));
    if (serviceHeading) {
      const next = serviceHeading.nextElementSibling;
      if (next && (next.tagName.toLowerCase()==='ul' || next.tagName.toLowerCase()==='ol')) {
        services = Array.from(next.querySelectorAll('li')).map(li=>norm(li.textContent)).join('; ');
      } else {
        services = norm(serviceHeading.nextElementSibling ? serviceHeading.nextElementSibling.innerText : '');
      }
    }
    // fallback: attempt to extract from main content by searching for known words
    if (!services) {
      const possibleServices = (pageText.match(/(?:Orthotics|Ingrown Toenails|Biomechanics|Verruca|Wart|Diabetic Foot|Podiatry|Foot|Ankle|Surgery|Shockwave)[^.,;\\n]*/gi) || []).slice(0,20);
      services = Array.from(new Set(possibleServices)).join('; ');
    }

    // Ensure single string values; if multiple emails or phones pick first but keep others in parentheses
    const record = {
      "Name of Clinic": name || '',
      "Address": address || '',
      "Email": (emails.length>0) ? emails.join('; ') : '',
      "Phone": (phones.length>0) ? phones.join('; ') : '',
      "Services": services || ''
    };

    // Return / save the record in the expected dataset format
    return { result: record };
  }

  // If nothing extracted, return null (no record)
  return null;
}
```

6. **Post-run steps (must be performed):**
   - After the actor run finishes, call `mcp_apify_get-actor-output` with the returned `datasetId` to read all items. Retrieve all fields.
   - **Normalize results**: For each item, ensure CSV columns exactly match these headers: `Name of Clinic`, `Address`, `Email`, `Phone`, `Services`. If any field is missing, use an empty string (`""`) in the CSV cell.
   - **Deduplicate** results by `Name of Clinic` + `Address` (case-insensitive).
   - **CSV formatting**: Use UTF-8 encoding. Commas are delimiters; wrap fields in double quotes. Do not include any extra columns or row headers beyond the five exact column headers above.
   - Save the CSV to the actor output (or as a downloadable asset). Then fetch it and provide a download link (or provide the CSV contents inline if a direct file link is not available).

7. **Robustness & constraints to account for (explicit):**
   - The target is an **archive.org** snapshot. There may be relative links and archive redirects. Use the archived absolute URLs from the page (do not rewrite to live site).
   - The pageFunction must handle both directory pages and clinic pages — this is why it enqueues links and extracts only when clinic content is detected.
   - Keep `maxConcurrency` low (5) and include polite timeouts because archived pages may be slow.
   - If `mcp_apify_fetch-actor-details` suggests different parameter names or stricter security rules, adapt but preserve behavior and the same `pageFunction` semantics.
   - If the actor run hits rate limits or timeouts, retry with reduced concurrency and a `delay` between requests (e.g., 500–1500 ms).

8. **Safety / Authorization:**
   - No authentication should be required for the archive URL. If the site requires auth, stop and report the exact error and missing auth type to me.
   - Respect data use rules. This is a one-time scrape of a public archived page. If actor logs or README demand `respectRobotsTxtFile=true`, follow it or report why it blocked the crawl.

9. **Deliverables (what the agent must return to me at the end):**
   - A single CSV file named `myfootdr_clinics.csv` with headers exactly: `Name of Clinic,Address,Email,Phone,Services`.
   - A short JSON summary with: `{ "datasetId": "<id>", "rowsExtracted": N, "rowsAfterDedup": M, "csvPathOrUrl": "<link or path>" }`.
   - If any clinic pages could not be parsed (e.g., no contact info), include a `failed_pages` list with the page URLs and the reason.

10. **If anything ambiguous or blocked occurs:**  
    - DO NOT guess or proceed to scrape beyond the actor limitations. Instead fetch the actor README via `mcp_apify_fetch-actor-details`, retry with adjusted settings (lower concurrency or longer timeouts), and record the failure reasons in the `failed_pages` output.

**Important meta-notes to the agent (final instructions for Copilot agent):**
- **Distinguish**: treat the top "Reference context" part of this prompt as documentation only — do not output it as a result.
- **Follow the two-step `call-actor` flow** (info → call). Confirm actor input names and adjust the input JSON if needed.
- **Embed the provided `pageFunction` exactly** unless the actor input schema requires a different wrapper syntax; keep JS logic unchanged.
- **Produce exactly the deliverables** listed above (CSV file, summary JSON, failed_pages).
- **Do not add or rename CSV columns**. Use only the five specified column headers.
- **Keep concurrency conservative** and use `proxyConfiguration.useApifyProxy = true`.

---

