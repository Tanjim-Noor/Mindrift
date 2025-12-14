import os, re, csv, json, time, random
from bs4 import BeautifulSoup
import requests
import langid

# --- Locked Pipeline Configuration ---
HEADERS = {
    "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language":"en-US,en;q=0.9"
}
session = requests.Session()
session.headers.update(HEADERS)

FIELDNAMES = ["mcp_detail_url","github_url","name","description","language","category","tags","overview","readme","github_stars"]

# Language detection config - FIXED: single backslashes in raw strings
langid.set_languages(['en','zh','ja','es','fr','de','ru','pt','it','ca'])
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
HIRAGANA_RE = re.compile(r"[\u3040-\u309F]")
KATAKANA_RE = re.compile(r"[\u30A0-\u30FF]")
LANG_MAP = {
    'en':'English','zh':'Chinese','ja':'Japanese','es':'Spanish','fr':'French','de':'German','ru':'Russian','pt':'Portuguese','it':'Italian','ca':'Catalan'
}

# --- Core Functions ---

def text(el):
    return (el.get_text(' ', strip=True) if el else '').strip()

def classify_language_langid(desc: str) -> str:
    d = desc or ''
    if not d.strip():
        return ''
    if CJK_RE.search(d):
        return 'Chinese'
    if HIRAGANA_RE.search(d) or KATAKANA_RE.search(d):
        return 'Japanese'
    # FIXED: single backslash for non-ASCII detection
    if len(d.strip()) < 40 and not re.search(r"[^\x00-\x7F]", d):
        return 'English'
    try:
        code, score = langid.classify(d)
        # FIXED: single backslash for non-ASCII detection
        if score < 0.80 and not re.search(r"[^\x00-\x7F]", d):
            return 'English'
        return LANG_MAP.get(code, code)
    except Exception:
        return ''

def get_stars_owner_repo(owner: str, repo: str, session: requests.Session, debug: list) -> str:
    tries = 2
    for attempt in range(tries):
        try:
            url = f"https://github.com/{owner}/{repo}"
            r = session.get(url, timeout=25)
            status = r.status_code
            if status != 200:
                debug.append(f"{owner}/{repo} status {status}")
                time.sleep(0.8 + random.random() * 0.4)
                continue
            if r.history:
                final_url = r.url.rstrip('/')
                parts = final_url.split('/')
                if len(parts) >= 5 and 'github.com' in parts[2].lower():
                    owner = parts[-2]
                    repo = parts[-1]
            s = BeautifulSoup(r.text, 'html.parser')
            # FIXED: single backslash in raw string
            pattern = re.compile(rf"(https://github\.com)?/{re.escape(owner)}/{re.escape(repo)}/stargazers", re.IGNORECASE)
            a = s.find('a', href=pattern)
            if not a:
                meta = s.find('meta', {'name': 'description'})
                if meta:
                    content = meta.get('content', '')
                    m_meta = re.search(r"([0-9,]+)\s+stars?", content, flags=re.IGNORECASE)
                    if m_meta:
                        return m_meta.group(1).replace(',', '')
                debug.append(f"{owner}/{repo} no stargazers anchor/meta")
                time.sleep(0.8 + random.random() * 0.4)
                continue
            t_anchor = a.get_text(' ', strip=True)
            m = re.search(r"([\d,]+)", t_anchor)
            if m:
                val = m.group(1).replace(',', '')
                try:
                    return str(int(val))
                except Exception:
                    return val
            for descendant in a.descendants:
                if hasattr(descendant, 'get_text'):
                    txt = descendant.get_text(' ', strip=True)
                    m2 = re.search(r"^([\d,]+)$", txt)
                    if m2:
                        val = m2.group(1).replace(',', '')
                        try:
                            return str(int(val))
                        except Exception:
                            return val
            for attr, val in a.attrs.items():
                vals = val if isinstance(val, list) else [val]
                for v in vals:
                    if isinstance(v, str):
                        m3 = re.search(r"([\d,]+)", v)
                        if m3:
                            valn = m3.group(1).replace(',', '')
                            try:
                                return str(int(valn))
                            except Exception:
                                return valn
            parent = a.parent
            if parent:
                for descendant in parent.descendants:
                    if hasattr(descendant, 'get_text'):
                        txt = descendant.get_text(' ', strip=True)
                        m4 = re.search(r"^([\d,]+)$", txt)
                        if m4:
                            val = m4.group(1).replace(',', '')
                            try:
                                return str(int(val))
                            except Exception:
                                return val
            debug.append(f"{owner}/{repo} stars not parsed; attempt {attempt+1}")
            time.sleep(0.8 + random.random() * 0.6)
        except Exception as e:
            debug.append(f"{owner}/{repo} exception {e}")
            time.sleep(0.8 + random.random() * 0.6)
    return ''

def fetch_readme_markdown(owner: str, repo: str, session: requests.Session) -> str:
    for b in ['main','master']:
        raw = f"https://raw.githubusercontent.com/{owner}/{repo}/{b}/README.md"
        try:
            r = session.get(raw, timeout=25)
            if r.status_code == 200 and r.text and r.text.strip():
                return r.text
        except Exception:
            continue
    return ''

def extract_server(url: str, html_file: str, session: requests.Session, debug: list) -> dict:
    row = {k: '' for k in FIELDNAMES}
    row['mcp_detail_url'] = url
    try:
        html = open(html_file, 'r', encoding='utf-8', errors='ignore').read()
        soup = BeautifulSoup(html, 'html.parser')
        row['name'] = text(soup.find(['h1','h2','h3']))
        desc_div = soup.select_one('div.text-sm.mt-4.mb-4')
        if desc_div:
            description = text(desc_div)
        else:
            description = ''
            smalls = soup.select('div.text-sm')
            if smalls:
                for d in smalls:
                    txt = text(d)
                    if txt:
                        description = txt
                        break
            if not description:
                paras = [text(p) for p in soup.find_all('p')]
                paras = [t for t in paras if t and not t.startswith('@')]
                cjk = [t for t in paras if CJK_RE.search(t)]
                description = max(cjk, key=len) if cjk else (max(paras, key=len) if paras else '')
        row['description'] = description
        row['language'] = classify_language_langid(description)
        row['category'] = text(soup.find('a', href=re.compile(r"/category/"))) if soup.find('a', href=re.compile(r"/category/")) else ''
        tags = []
        for t in soup.find_all('a', href=re.compile(r"/tag/")):
            txt = text(t)
            txt = re.sub(r'^#', '', txt).strip()
            if txt:
                tags.append(txt)
        row['tags'] = '; '.join(tags)
        overview = ''
        ov_head = soup.find(lambda tag: tag.name in ['h2','h3','h4'] and 'overview' in text(tag).lower())
        if ov_head:
            container = ov_head.find_next(['div','section','article'])
            overview = text(container)
        if not overview:
            md = soup.find('div', class_=re.compile(r"markdown", re.I))
            overview = text(md)
        row['overview'] = overview
        github_url = ''
        owner = repo = None
        # FIXED: single backslashes in raw string regex
        for a in soup.find_all('a', href=re.compile(r"https?://github\.com/")):
            href = a.get('href','').strip()
            m = re.search(r"https?://github\.com/([\w-]+)/([\w.-]+)(?:$|[/?])", href)
            if m:
                if '/issues' in href:
                    continue
                o, rname = m.group(1), m.group(2)
                github_url = f"https://github.com/{o}/{rname}"
                owner, repo = o, rname
                break
        row['github_url'] = github_url
        readme_md = ''
        stars_numeric = ''
        if github_url and owner and repo:
            stars_numeric = get_stars_owner_repo(owner, repo, session, debug)
            readme_md = fetch_readme_markdown(owner, repo, session)
        row['readme'] = readme_md
        row['github_stars'] = stars_numeric
    except Exception as e:
        debug.append(f"extract_server error for {url}: {e}")
    return row