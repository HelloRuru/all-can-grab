"""
all-can-grab - Universal public web scraper.
Given a URL, auto-detect the site, pick a strategy, and return structured results.
Only handles publicly accessible content; never bypasses login walls.
"""

import re
import json
import sys
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

# ============================================================
# 1. Data structures
# ============================================================

@dataclass
class PostItem:
    title: str = ""
    snippet: str = ""
    datetime_str: str = ""
    author: str = ""
    url: str = ""

@dataclass
class ClinicSlot:
    doctor: str = ""
    date: str = ""
    time_range: str = ""
    source_url: str = ""

@dataclass
class ScrapeResult:
    summary: str = ""
    items: list = field(default_factory=list)
    clinic_slots: list = field(default_factory=list)
    status: str = "failed"  # success | partial | failed
    blocker: str = ""
    raw_text: str = ""
    source: str = ""  # which strategy was used

# ============================================================
# 2. Site detection + strategy selection
# ============================================================

SITE_STRATEGIES = {
    "facebook":   {"ua": "googlebot", "fallback": "playwright"},
    "threads":    {"ua": "googlebot", "fallback": "playwright"},
    "linkedin":   {"ua": "googlebot", "fallback": None},  # returns 999; not supported
    "notion":     {"ua": "googlebot", "fallback": None},
    "youtube":    {"ua": "normal",    "fallback": None},
    "github":     {"ua": "normal",    "fallback": None},
    "ptt":        {"ua": "normal",    "cookies": {"over18": "1"}, "fallback": "playwright"},
    "instagram":  {"ua": "googlebot", "fallback": "apify"},
    "x_twitter":  {"ua": "normal",    "fallback": "playwright"},
    "medium":     {"ua": "normal",    "fallback": "curl_cffi"},
    "dcard":      {"ua": "normal",    "fallback": "playwright"},
    "104":        {"ua": "normal",    "fallback": "playwright"},
    "default":    {"ua": "googlebot", "fallback": "playwright"},
}

UA_GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
UA_NORMAL = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

def detect_site(url: str) -> str:
    """Detect which site a URL belongs to."""
    host = urlparse(url).hostname or ""
    host = host.lower()

    if "facebook.com" in host or "fb.com" in host:
        return "facebook"
    if "threads.net" in host:
        return "threads"
    if "linkedin.com" in host:
        return "linkedin"
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "github.com" in host:
        return "github"
    if "ptt.cc" in host:
        return "ptt"
    if "instagram.com" in host:
        return "instagram"
    if "x.com" in host or "twitter.com" in host:
        return "x_twitter"
    if "medium.com" in host:
        return "medium"
    if "dcard.tw" in host:
        return "dcard"
    if "104.com.tw" in host:
        return "104"
    if "notion.so" in host or "notion.site" in host:
        return "notion"
    return "default"

def classify_fb_url(url: str) -> str:
    """Classify Facebook URL subtype: post / page / event."""
    if "/share/p/" in url or "/share/" in url:
        return "post"
    if re.search(r"/posts/|/permalink\.php|story_fbid|/videos/|/photos/|/reel/", url):
        return "post"
    if "/events/" in url:
        return "event"
    if re.search(r"facebook\.com/[^/]+/?$", url):
        return "page"
    return "post"

# ============================================================
# 3. HTTP fetching
# ============================================================

def fetch_via_http(url: str, ua: str = "googlebot", cookies: dict = None) -> Optional[dict]:
    """Fetch a page with the specified UA and return parsed result or None."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    user_agent = UA_GOOGLEBOT if ua == "googlebot" else UA_NORMAL
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }

    try:
        r = requests.get(url, headers=headers, cookies=cookies,
                         allow_redirects=True, timeout=15)
        if r.status_code != 200:
            # Googlebot blocked -- retry with normal UA
            if ua == "googlebot":
                return fetch_via_http(url, ua="normal", cookies=cookies)
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # OG tags
        og = {}
        for tag in soup.find_all("meta", attrs={"property": True}):
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if content:
                og[prop] = content

        # meta description fallback
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            og.setdefault("meta:description", meta_desc["content"])

        title = og.get("og:title", "")
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

        description = og.get("og:description", og.get("meta:description", ""))
        og_url = og.get("og:url", url)

        # Full body text: prefer semantic tags to avoid nav/sidebar noise
        full_text = ""

        # Layer 1: semantic selectors (article > main > [role=main])
        semantic_selectors = ["article", "main", "[role='main']"]
        for sel in semantic_selectors:
            el = soup.select_one(sel)
            if el:
                # Strip nav/header/footer/aside before extracting text
                for junk in el.find_all(["nav", "header", "footer", "aside"]):
                    junk.decompose()
                candidate = el.get_text(separator="\n", strip=True)
                if len(candidate) > 200:
                    full_text = candidate
                    break

        # Layer 2 fallback: find the longest meaningful block
        if not full_text:
            skip_words = ["登入", "cookie", "sign in", "log in", "accept"]
            for el in soup.find_all(["div", "p", "section"]):
                text = el.get_text(strip=True)
                if len(text) > 100:
                    text_lower = text.lower()
                    if not any(w in text_lower for w in skip_words):
                        if len(text) > len(full_text):
                            full_text = text

        best_text = full_text if len(full_text) > len(description) else description

        # Login / error page detection
        login_signals = ["登入或註冊", "sign up", "create an account", "log in to"]
        error_signals = ["post無法顯示", "此頁面無法使用", "this page isn't available",
                         "此連結可能故障", "content isn't available"]
        combined = (title + best_text).lower()
        if any(s in combined for s in error_signals):
            return None
        if any(s in combined for s in login_signals):
            if len(best_text) < 200:
                return None

        if not best_text and not title:
            return None

        return {
            "title": title,
            "text": best_text,
            "url": og_url,
            "og": og,
            "method": f"http-{ua}",
            "soup": soup,
        }

    except Exception:
        return None

# ============================================================
# 3.5 curl_cffi fallback (bypass Cloudflare TLS fingerprinting)
# ============================================================

def fetch_via_curl_cffi(url: str) -> Optional[dict]:
    """Use curl_cffi to mimic a real browser TLS fingerprint, bypassing Cloudflare."""
    try:
        from curl_cffi import requests as cffi_requests
        from bs4 import BeautifulSoup
    except ImportError:
        return None

    try:
        r = cffi_requests.get(url, impersonate="chrome", timeout=15)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")

        # Check if still on Cloudflare challenge page
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""
        if "just a moment" in title.lower():
            return None

        # OG tags
        og = {}
        for tag in soup.find_all("meta", attrs={"property": True}):
            prop = tag.get("property", "")
            content = tag.get("content", "")
            if content:
                og[prop] = content

        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            og.setdefault("meta:description", meta_desc["content"])

        og_title = og.get("og:title", title)
        description = og.get("og:description", og.get("meta:description", ""))

        # Body text
        full_text = ""
        for el in soup.find_all(["article", "div", "p", "section"]):
            text = el.get_text(strip=True)
            if len(text) > 100 and len(text) > len(full_text):
                full_text = text

        best_text = full_text if len(full_text) > len(description) else description

        if not best_text and not og_title:
            return None

        return {
            "title": og_title,
            "text": best_text,
            "url": og.get("og:url", url),
            "og": og,
            "method": "curl_cffi",
        }

    except Exception:
        return None

# ============================================================
# 3.6 Apify fallback (for IG posts)
# ============================================================

def fetch_via_apify(url: str) -> Optional[dict]:
    """Use Apify Instagram Post Scraper to fetch IG posts. Requires APIFY_TOKEN."""
    try:
        import requests as req
        import os
    except ImportError:
        return None

    token = os.environ.get("APIFY_TOKEN") or os.environ.get("APIFY_API_TOKEN")
    if not token:
        return None

    try:
        run_url = f"https://api.apify.com/v2/acts/apify~instagram-post-scraper/run-sync-get-dataset-items?token={token}"
        payload = {
            "username": [url],
            "resultsLimit": 1,
            "dataDetailLevel": "basicData",
        }
        r = req.post(run_url, json=payload, timeout=60)
        if r.status_code != 200:
            return None

        items = r.json()
        if not items or not isinstance(items, list) or len(items) == 0:
            return None

        post = items[0]
        caption = post.get("caption", "")
        username = post.get("ownerUsername", post.get("username", ""))
        full_name = post.get("ownerFullName", "")
        post_url = post.get("url", url)
        timestamp = post.get("timestamp", "")

        if not caption and not username:
            return None

        author = full_name if full_name else f"@{username}" if username else ""
        title = f"{author} on Instagram" if author else "Instagram Post"

        return {
            "title": title,
            "text": caption,
            "url": post_url,
            "og": {},
            "method": "apify",
            "author_name": author,
        }

    except Exception:
        return None

# ============================================================
# 4. Playwright fallback
# ============================================================

def fetch_via_playwright(url: str, site: str = "") -> Optional[dict]:
    """Use headless Playwright browser to load the page. No login."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            # Prefer system Chrome (more human-like); fall back to bundled Chromium
            launch_args = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            }
            try:
                browser = p.chromium.launch(channel="chrome", **launch_args)
            except Exception:
                browser = p.chromium.launch(**launch_args)
            context = browser.new_context(
                user_agent=UA_NORMAL,
                locale="zh-TW",
                viewport={"width": 1920, "height": 1080},
            )
            # Hide webdriver flag
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            # PTT requires over18 cookie
            if site == "ptt":
                context.add_cookies([{
                    "name": "over18",
                    "value": "1",
                    "domain": ".ptt.cc",
                    "path": "/",
                }])

            page = context.new_page()

            # Sites behind Cloudflare (e.g. Medium) need longer timeouts
            timeout = 30000 if site in ("medium",) else 20000
            try:
                page.goto(url, wait_until="networkidle", timeout=timeout)
            except Exception:
                # networkidle timed out -- try domcontentloaded
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    page.wait_for_timeout(3000)
                except Exception:
                    browser.close()
                    return None

            # Cloudflare challenge wait: if title is "Just a moment...", wait for redirect
            for _ in range(6):
                t = page.title()
                if t and "just a moment" not in t.lower():
                    break
                page.wait_for_timeout(2000)

            # Dismiss popups
            for selector in ['[aria-label="Close"]', '[aria-label="關閉"]',
                             'button:has-text("Accept")', 'button:has-text("接受")']:
                try:
                    btn = page.locator(selector)
                    if btn.count() > 0:
                        btn.first.click(timeout=2000)
                except Exception:
                    pass

            title = page.title()

            # OG tags (also extract via Playwright for better accuracy)
            og = {}
            try:
                og_tags = page.evaluate("""
                    () => {
                        const og = {};
                        document.querySelectorAll('meta[property^="og:"]').forEach(el => {
                            og[el.getAttribute('property')] = el.getAttribute('content') || '';
                        });
                        const desc = document.querySelector('meta[name="description"]');
                        if (desc) og['meta:description'] = desc.getAttribute('content') || '';
                        return og;
                    }
                """)
                og = og_tags or {}
            except Exception:
                pass

            # Extract main text content
            text_content = page.evaluate("""
                () => {
                    // Try common content selectors first
                    const selectors = [
                        'article', '[role="article"]',
                        '[data-testid="post_message"]', 'div[dir="auto"]',
                        '.post-content', '.entry-content', 'main',
                    ];
                    let longest = '';
                    for (const sel of selectors) {
                        document.querySelectorAll(sel).forEach(el => {
                            const t = (el.innerText || '').trim();
                            if (t.length > longest.length) longest = t;
                        });
                    }
                    // Fallback: longest div
                    if (longest.length < 100) {
                        document.querySelectorAll('div, p').forEach(el => {
                            const t = (el.innerText || '').trim();
                            if (t.length > 200 && t.length > longest.length) longest = t;
                        });
                    }
                    return longest;
                }
            """)

            # OG description fallback
            if not text_content or len(text_content) < 50:
                og_desc = og.get("og:description", og.get("meta:description", ""))
                if og_desc and len(og_desc) > len(text_content or ""):
                    text_content = og_desc

            final_url = page.url
            browser.close()

            if not text_content and not title:
                return None

            return {
                "title": og.get("og:title", title),
                "text": text_content,
                "url": final_url,
                "og": og,
                "method": "playwright",
            }

    except Exception:
        return None

# ============================================================
# 5. Text parsing
# ============================================================

def parse_author(raw: dict, site: str, soup=None) -> str:
    """Extract author name from OG tags / meta / byline."""
    og = raw.get("og", {})

    # 1. OG / meta author fields
    junk_values = {"undefined", "null", "none", ""}
    for key in ["og:article:author", "article:author"]:
        val = og.get(key, "").strip()
        if val and val.lower() not in junk_values:
            return val

    # 2. BeautifulSoup: meta[name=author] / byline class
    if soup:
        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            return meta_author["content"]
        for sel in [".author", ".byline", "[rel='author']", ".post-author"]:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(strip=True)
                if 2 <= len(text) <= 50:
                    return text

    # 3. Social platforms: infer from title (FB/IG/Threads title is usually the account name)
    title = raw.get("title", "")
    platform_names = ["Facebook", "Facebook - 登入或註冊", "LinkedIn", "YouTube",
                      "GitHub", "Instagram", "Threads", ""]
    if title in platform_names:
        return ""

    # FB/IG/Threads: title IS the account name
    if site in ("facebook", "instagram", "threads"):
        return title

    return ""

def generate_summary(text: str, max_sentences: int = 5) -> str:
    """Take the first few sentences as a summary."""
    if not text:
        return ""
    sentences = re.split(r'(?<=[。！？\.\!\?\n])\s*', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 5]
    return " ".join(sentences[:max_sentences])

def parse_clinic_slots(text: str, source_url: str) -> list:
    """Extract clinic appointment info from text."""
    slots = []
    pattern = r'([^\s,，、]{1,5}(?:醫師|醫生|主任|院長))\s*(\d{1,2}[/.-]\d{1,2}(?:[（(][一二三四五六日][）)])?)\s*((?:上午|下午|晚間|早上|晚上)?\s*\d{1,2}:\d{2}\s*[-~至]\s*\d{1,2}:\d{2})'
    for m in re.finditer(pattern, text):
        slots.append(ClinicSlot(
            doctor=m.group(1),
            date=m.group(2),
            time_range=m.group(3).strip(),
            source_url=source_url,
        ))
    return slots

# ============================================================
# 6. Main pipeline
# ============================================================

def scrape(url: str) -> ScrapeResult:
    """Main entry: given any URL, return structured scrape results."""
    result = ScrapeResult()
    site = detect_site(url)
    strategy = SITE_STRATEGIES.get(site, SITE_STRATEGIES["default"])

    # === Round 1: HTTP fetch ===
    cookies = strategy.get("cookies")
    raw = fetch_via_http(url, ua=strategy["ua"], cookies=cookies)

    # === Facebook content validation ===
    # FB Googlebot sometimes returns wrong pages; verify OG title against URL slug
    if raw and site == "facebook":
        og_title = raw.get("og", {}).get("og:title", "")
        og_url = raw.get("og", {}).get("og:url", "")
        # If OG URL path differs completely from original, likely wrong page
        if og_url and og_title:
            from urllib.parse import urlparse as _up
            orig_path = _up(url).path.strip("/").lower()
            og_path = _up(og_url).path.strip("/").lower()
            if orig_path and og_path and orig_path != og_path:
                raw = None  # Force playwright fallback

    # === Round 2: Fallback ===
    fallback = strategy.get("fallback")
    if not raw or not raw.get("text"):
        if fallback == "apify":
            raw = fetch_via_apify(url)
        elif fallback == "curl_cffi":
            raw = fetch_via_curl_cffi(url)
            if not raw or not raw.get("text"):
                raw = fetch_via_playwright(url, site=site)
        elif fallback == "playwright":
            raw = fetch_via_playwright(url, site=site)

    if not raw or not raw.get("text"):
        result.status = "failed"
        if site == "medium":
            result.blocker = f"[{site}] Medium uses Cloudflare + SPA dual protection; auto-scraping is limited. Suggestion: copy-paste the article content directly."
        else:
            result.blocker = f"[{site}] Scrape failed. Possible reasons: login required, content hidden, or site blocked the request. Suggestion: copy-paste the content directly, or use a screenshot."
        return result

    # === Error page detection (shared across all strategies) ===
    error_signals = ["post無法顯示", "此頁面無法使用", "this page isn't available",
                     "此連結可能故障", "content isn't available"]
    raw_text_lower = (raw.get("title", "") + raw.get("text", "")).lower()
    if any(s in raw_text_lower for s in error_signals):
        result.status = "failed"
        result.blocker = f"[{site}] Platform returned an error page (may require login or post was deleted). Suggestion: copy-paste the content directly, or use a screenshot."
        return result

    # === Parse ===
    text = raw["text"]
    author = parse_author(raw, site, soup=raw.get("soup"))
    canonical_url = raw.get("url", url)

    item = PostItem(
        title=raw.get("title", ""),
        snippet=text[:2000],
        datetime_str=datetime.now().strftime("%Y-%m-%d"),
        author=author,
        url=canonical_url,
    )

    result.items = [asdict(item)]
    result.raw_text = text
    result.summary = generate_summary(text)
    result.status = "success"
    result.source = raw.get("method", "unknown")

    # === Clinic slot extraction (bonus) ===
    clinic_slots = parse_clinic_slots(text, canonical_url)
    if clinic_slots:
        result.clinic_slots = [asdict(s) for s in clinic_slots]

    return result

# ============================================================
# 7. CLI entry point
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grab.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    result = scrape(url)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
