# all-can-grab - Universal public web scraper skill

## When to use (auto-trigger)
- **Whenever the user pastes any URL** in the conversation, automatically use this skill to fetch the content. Do NOT wait for the user to ask — just grab it.
- Any message containing a public web link (HTTP/HTTPS) should trigger this skill proactively.
- Covers: social media posts, articles, blog posts, job listings, product pages, documentation, and any publicly accessible web page.

## Usage

```bash
python grab.py "<URL>"
```

## Supported sites + strategies

| Site | Strategy | Fallback | Status |
|------|----------|----------|--------|
| Facebook | Googlebot UA | Playwright | Tested |
| Threads | Googlebot UA | Playwright | Tested |
| YouTube | Normal UA | - | Tested |
| GitHub | Normal UA | - | Tested |
| PTT | Normal UA + over18 cookie | Playwright | Tested |
| 104 Job Bank | Normal UA | - | Limited (pda.104 Vue SPA not supported) |
| Notion (public) | Googlebot UA | - | Tested |
| Astro/SSG sites | Normal UA | - | Tested |
| LinkedIn | Googlebot UA | - | Not supported (returns 999) |
| Instagram | - | - | Partial (profile only; no free solution for single posts) |
| X/Twitter | Normal UA | Playwright | Limited |
| Medium | Normal UA | curl_cffi -> Playwright | Limited |
| Dcard | Normal UA | Playwright | Limited |
| Others | Googlebot UA | Playwright | Best effort |

## Pipeline

1. Detect site -> pick strategy
2. Raw HTTP fetch (fast)
3. If failed -> curl_cffi for TLS fingerprint bypass (Cloudflare sites like Medium)
4. Still failed -> headless browser rendering (Playwright, stable)
5. Parse: title / body / author / datetime / URL (semantic tags first, filter nav/sidebar noise)
6. Error page detection: auto-detect "post not available" etc. as failed
7. On failure: report blocker reason + suggestion
8. (Extension demo) Clinic slot detection: extract doctor + date + time (clinic_slots), demonstrates custom parser addition

## Instagram single posts (as of 2026-03-13)

No free reliable solution. IG has fully blocked unauthenticated access since late 2024 (Googlebot UA, oEmbed, embed, Playwright, Google cache all fail).

Alternatives:
- **Manual**: User logs into IG and provides screenshot or text
- **Official embed**: Meta oEmbed for display embedding (not full data extraction)
- **Paid fallback**: Built-in Apify integration (`apify/instagram-post-scraper`); set `APIFY_TOKEN` env var to enable, pay-per-use. Without token, other features are unaffected

## Output format

```json
{
  "summary": "3-5 sentence summary",
  "items": [{"title", "snippet", "datetime_str", "author", "url"}],
  "clinic_slots": [],
  "status": "success | partial | failed",
  "blocker": "failure reason",
  "raw_text": "full original text",
  "source": "http-googlebot / http-normal / curl_cffi / playwright"
}
```

## Limitations
- Public content only; never bypasses login walls
- Platform rules change anytime; strategies not guaranteed permanent
- IG single posts have no free solution (see above); X/Twitter partially login-gated
- Not supported: LINE groups, Xiaohongshu, paywalled content

## Dependencies
- requests + beautifulsoup4 (required)
- curl_cffi (optional, Cloudflare TLS fingerprint bypass)
- playwright (optional, requires `playwright install chromium`)
- APIFY_TOKEN env var (optional, paid IG post fallback)
