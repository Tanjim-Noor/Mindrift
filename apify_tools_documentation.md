# Apify MCP Tools Documentation

This document lists all the Apify tools currently connected to the LLM.

## Tools Overview

### 1. mcp_apify_rag-web-browser
**Description:** Web browser for OpenAI Assistants, RAG pipelines, or AI agents, similar to a web browser in ChatGPT. It queries Google Search, scrapes the top N pages, and returns their content as Markdown for further processing by an LLM. It can also scrape individual URLs.

**When to use:** 
- User wants to GET or RETRIEVE actual data immediately (one-time data retrieval)
- User wants current/immediate data (e.g., "Get flight prices for tomorrow", "What's the weather today?")
- User needs to fetch specific content now (e.g., "Fetch news articles from CNN", "Get product info from Amazon")
- User has time indicators like "today", "current", "latest", "recent", "now"

**Parameters:**
- `query` (required): Enter Google Search keywords or a URL of a specific web page
- `maxResults` (optional): The maximum number of top organic Google Search results whose web pages will be extracted (default: 3)
- `outputFormats` (optional): Select one or more formats for output (markdown, text, html) (default: markdown)

---

### 2. mcp_apify_screenshot-url
**Description:** Create a screenshot of a website based on a specified URL. The screenshot is stored as the output in a key-value store. It can be used to monitor web changes regularly after setting up the scheduler.

**Parameters:**
- `urls` (required): List of URLs you want to take screenshots of
- `waitUntil` (required): Control when the browser takes a screenshot (load, domcontentloaded, networkidle2, networkidle0)
- `delay` (required): Add delay before a screenshot is taken (minimum: 0, maximum: 3600000ms)
- `viewportWidth` (required): How wide should the website's viewport be (default: 1280)
- `format` (optional): Screenshot file format - png or pdf (default: png)
- `scrollToBottom` (optional): Should the browser scroll to the bottom of the page before taking a screenshot (default: false)
- `selectorsToHide` (optional): List of selectors to hide before taking a screenshot
- `proxy` (optional): Proxy configuration (default: useApifyProxy = true)
- `delayAfterScrolling` (optional): Delay after scrolling in milliseconds (default: 2500)
- `waitUntilNetworkIdleAfterScroll` (optional): Wait for network idle after scrolling (default: false)
- `waitUntilNetworkIdleAfterScrollTimeout` (optional): Network idle timeout in milliseconds (default: 30000)

---

### 3. mcp_apify_web-scraper
**Description:** Crawls arbitrary websites using a web browser and extracts structured data from web pages using a provided JavaScript function. The Actor supports both recursive crawling and lists of URLs, and automatically manages concurrency for maximum performance.

**Key Parameters:**
- `startUrls` (required): One or more URLs of pages where the crawler will start
- `pageFunction` (required): JavaScript (ES6) function that is executed in the context of every page loaded
- `proxyConfiguration` (required): Proxy configuration for the scraper

**Other Parameters Include:**
- `linkSelector`: CSS selector for links to follow
- `globs`: Glob patterns to match links to enqueue
- `excludes`: Glob patterns to exclude from crawling
- `maxConcurrency`: Maximum parallel pages (default: 50)
- `maxCrawlingDepth`: Maximum links away from start URLs (default: 0)
- `maxPagesPerCrawl`: Maximum pages to load (default: 0)
- `maxRequestRetries`: Maximum retries on error (default: 3)
- `maxResultsPerCrawl`: Maximum records to save (default: 0)
- `headless`: Run browsers in headless mode (default: true)
- `injectJQuery`: Inject jQuery library (default: true)
- `downloadCss`: Download CSS files (default: true)
- `downloadMedia`: Download media files (default: true)
- `browserLog`: Include browser console messages in logs (default: false)
- `debugLog`: Include debug messages (default: false)
- `pageLoadTimeoutSecs`: Max wait time for page load (default: 60)
- `pageFunctionTimeoutSecs`: Max wait time for page function (default: 60)
- `maxScrollHeightPixels`: Maximum scrolling distance (default: 5000)
- `keepUrlFragments`: URL fragments identify unique pages (default: false)
- `respectRobotsTxtFile`: Respect robots.txt file (default: false)
- `runMode`: PRODUCTION or DEVELOPMENT (default: PRODUCTION)

---

### 4. mcp_apify_website-content-crawler
**Description:** Crawl websites and extract text content to feed AI models, LLM applications, vector databases, or RAG pipelines. The Actor supports rich formatting using Markdown, cleans the HTML, downloads files, and integrates well with LangChain, LlamaIndex, and the wider LLM ecosystem.

**Key Parameters:**
- `startUrls` (required): One or more URLs of pages where the crawler will start
- `proxyConfiguration` (required): Proxy configuration for crawling

**Notable Parameters:**
- `crawlerType`: Select the crawling engine (adaptive switching, Firefox headless, Cheerio HTTP, JSDOM, Chrome headless) (default: playwright:firefox)
- `htmlTransformer`: How to transform HTML (readableTextIfPossible, readableText, extractus, defuddle, none) (default: readableText)
- `maxCrawlDepth`: Maximum crawling depth (default: 20)
- `maxCrawlPages`: Maximum pages to crawl (default: 9999999)
- `maxResults`: Maximum resulting pages to store (default: 9999999)
- `maxConcurrency`: Maximum concurrent crawlers (default: 200)
- `maxScrollHeightPixels`: Maximum scroll height (default: 5000)
- `saveMarkdown`: Save as Markdown (default: true)
- `saveHtml`: Save HTML to dataset (deprecated)
- `saveHtmlAsFile`: Save HTML to key-value store
- `saveScreenshots`: Save screenshots (headless browser only)
- `saveFiles`: Download and save files (PDF, DOC, DOCX, XLS, XLSX, CSV)
- `removeCookieWarnings`: Remove cookie consent dialogs (default: true)
- `expandIframes`: Expand iframe elements (default: true)
- `clickElementsCssSelector`: CSS selector for elements to click (default: [aria-expanded="false"])
- `dynamicContentWaitSecs`: Max time to wait for dynamic content (default: 10)

---

### 5. mcp_apify_call-actor
**Description:** Call any Actor from the Apify Store using a mandatory two-step workflow. This ensures you first get the Actor's input schema and details before executing it safely.

**Workflow:**
1. Call with `step="info"` to get Actor details and input schema (REQUIRED first step)
2. Call with `step="call"` to run the Actor (only after getting info)

**Parameters:**
- `actor` (required): The name of the Actor in format "username/name" (e.g., "apify/rag-web-browser")
- `step` (required): "info" to get details or "call" to execute
- `input` (optional): Input JSON for the Actor (use only with step="call")
- `callOptions` (optional): Call options including memory and timeout configuration

---

### 6. mcp_apify_fetch-actor-details
**Description:** Get detailed information about an Actor by its ID or full name. Returns the Actor's title, description, URL, README (documentation), input schema, pricing/usage information, and basic stats.

**Use Cases:**
- User asks about an Actor's details, input schema, README, or how to use it
- User wants to understand pricing for an Actor
- User needs to see examples of how an Actor works

**Parameters:**
- `actor` (required): Actor ID or full name in format "username/name" (e.g., "apify/rag-web-browser")

---

### 7. mcp_apify_fetch-apify-docs
**Description:** Fetch the full content of an Apify documentation page by its URL. Use this after finding a relevant page with the search-apify-docs tool.

**Parameters:**
- `url` (required): Full URL of the Apify documentation page to fetch (including protocol)

---

### 8. mcp_apify_search-actors
**Description:** Search the Apify Store to FIND and DISCOVER what scraping tools/Actors exist for specific platforms or use cases. This tool provides INFORMATION about available Actors - it does NOT retrieve actual data or run any scraping tasks.

**Use Cases:**
- Find what scraping tools exist for a platform (e.g., "What tools can scrape Instagram?")
- Discover available Actors for a use case (e.g., "Find an Actor for Amazon products")
- Browse existing solutions (e.g., "Show me scrapers for news sites")

**Parameters:**
- `keywords` (optional): Space-separated keywords (1-3 terms max) to search for Actors
- `category` (optional): Filter by category
- `limit` (optional): Maximum number of Actors to return (default: 10)
- `offset` (optional): Number of elements to skip (default: 0)

**Search Guidelines:**
- Use 1-3 simple keywords maximum (e.g., "Instagram posts", "Twitter")
- Platform names and data types are most effective
- Avoid generic terms like "crawler", "data extraction"

---

### 9. mcp_apify_search-apify-docs
**Description:** Search Apify documentation using full-text search. Find relevant documentation based on keywords about Apify console, Actors, development, deployment, builds, runs, schedules, storages, Proxy, Integrations, and Apify Academy.

**Parameters:**
- `query` (required): Full-text search query using keywords (use only keywords, not full sentences)
- `limit` (optional): Maximum search results to return (default: 5)
- `offset` (optional): Offset for pagination (default: 0)

---

### 10. mcp_apify_get-actor-output
**Description:** Retrieve the output dataset items of a specific Actor run using its datasetId. Supports selecting specific fields and pagination.

**Use Cases:**
- Read Actor output data (full items or selected fields)
- Fetch specific fields from results
- Paginate through results

**Parameters:**
- `datasetId` (required): Actor output dataset ID to retrieve from
- `fields` (optional): Comma-separated list of fields to include (supports dot notation)
- `limit` (optional): Maximum items to return (default: 100)
- `offset` (optional): Number of items to skip (default: 0)

---

### 11. mcp_apify_scraperlink-slash-google-search-results-serp-scraper
**Description:** Only $0.50 per 1,000 search results pages. **CHEAPEST** Google Search Results (SERP) Scraper with real-time SERP data and support for multiple countries.

**Parameters:**
- `keyword` (required): Search keyword(s) - one full search query per line
- `limit` (optional): Number of results (10, 20, 30, 40, 50, 100, or "all") (default: "all")
- `country` (optional): Country code (ISO 3166 A-2)
- `gl` (optional): Override country localization (ISO 3166 A-2)
- `cr` (optional): Restrict results by country (countryUS, countryFR, etc.)
- `hl` (optional): UI language code (en, fr, de, etc.)
- `lr` (optional): Restrict results by language (lang_en, lang_fr, etc.)
- `tbs` (optional): Time filters (qdr:d for past day, qdr:w for week, etc.)
- `page` (optional): Page number for pagination
- `start` (optional): Result starting number
- `proxy_location` (optional): Force proxy region (us, ca)
- `include_merged` (optional): Include merged result row combining all pages (default: true)

---

## Tool Selection Guidelines

| Use Case | Recommended Tool |
|----------|------------------|
| General web scraping and data retrieval | `mcp_apify_rag-web-browser` |
| Take website screenshots | `mcp_apify_screenshot-url` |
| Complex multi-page crawling | `mcp_apify_web-scraper` |
| Extract content for AI/LLM use | `mcp_apify_website-content-crawler` |
| Search Google | `mcp_apify_scraperlink-slash-google-search-results-serp-scraper` |
| Find specific Actors | `mcp_apify_search-actors` |
| Get Actor documentation | `mcp_apify_fetch-actor-details` |
| Search Apify docs | `mcp_apify_search-apify-docs` |
| Retrieve Actor run results | `mcp_apify_get-actor-output` |
| Run any custom Actor | `mcp_apify_call-actor` |

## Notes

- **Dedicated Actor tools** (like `rag-web-browser`) are preferred over the generic `call-actor` tool when available
- Most Actors produce output stored in **datasets** (structured data) and **key-value stores** (flexible storage)
- Always check an Actor's **README and input schema** before execution
- Use `search-actors` first to discover relevant tools before building custom solutions
