<h1 align="center">All Can Grab</h1>

<p align="center">
  <strong>Give your AI agent the web-scraping ability it should have had all along.</strong><br>
  No more "Sorry, I can't access that page." Four-layer fallback strategy for public content.<br>
  One Python file. Four fallback layers. Every public page, one command.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-D4A5A5?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/python-3.8%2B-B8A9C9?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/dependencies-minimal-A8B5A0?style=flat-square" alt="Minimal Dependencies">
  <img src="https://img.shields.io/badge/claude_code-skill-E8B4B8?style=flat-square" alt="Claude Code Skill">
</p>

<p align="center">
  <b>English</b> &nbsp;|&nbsp; <a href="README.zh-TW.md">繁體中文</a> &nbsp;|&nbsp; <a href="README.ja.md">日本語</a>
</p>

---

## The Problem

- You ask your AI agent to read a public Facebook post -- it says *"Sorry, I can't access that page."*
- Your workflow breaks every time. You open the browser yourself, copy-paste, and feed it back.
- The content is public. The agent just doesn't know how to get past each platform's defenses.
- Every platform has a different lock. One key doesn't fit all.

## The Solution

A single Python script with a **four-layer fallback strategy** that handles platform-specific defenses automatically.

| Feature | Description |
|---------|-------------|
| Smart UA selection | Googlebot UA for Facebook/Threads, normal UA for YouTube/GitHub |
| TLS fingerprint bypass | curl_cffi for Cloudflare-protected sites like Medium |
| Paid API fallback | Apify integration for locked-down platforms like Instagram |
| Browser rendering | Headless Playwright when JavaScript rendering is required |
| Structured output | Consistent JSON schema with status, source, and blocker fields |
| Honest failure | Never pretends success -- reports exactly why it failed and what to try next |

## :package: Installation

**Step 1** -- Clone and install as a Claude Code global skill:

```bash
# This path makes Claude Code auto-detect the skill globally
git clone https://github.com/HelloRuru/all-can-grab.git ~/.claude/skills/learned/all-can-grab
```

**Step 2** -- Install dependencies:

```bash
# Core (required)
pip install requests beautifulsoup4

# Optional fallbacks (more = wider coverage)
pip install curl_cffi                          # TLS fingerprint bypass (Cloudflare)
pip install playwright && playwright install chromium  # Browser rendering
```

**Step 3** -- Try it:

```bash
python ~/.claude/skills/learned/all-can-grab/grab.py "https://www.facebook.com/share/p/xxxxx/"
```

> **Important:** The skill **must** be placed in `~/.claude/skills/learned/all-can-grab/` for Claude Code to auto-trigger it when you paste a URL. Other locations will not activate the skill.

## :brain: How It Works

Four layers, fastest first:

1. **Raw HTTP** -- No browser. Just the right User-Agent requesting HTML directly. Works for most public pages.
2. **TLS Fingerprint** (curl_cffi) -- Mimics a real browser's TLS fingerprint. Targets Cloudflare protection (e.g., Medium).
3. **Paid API** (Apify) -- Last resort for platforms that completely block free access (e.g., Instagram single posts).
4. **Browser Rendering** (Playwright) -- Opens a headless browser when JavaScript rendering is required.

No login. No stored cookies. No bypassing paywalls. Public content only.

## :detective: Platform Support

| Platform | Raw Strategy | Fallback | Status | Notes |
|----------|-------------|----------|--------|-------|
| Facebook | Googlebot UA | Playwright | Tested | Public posts & pages; includes OG URL validation |
| Threads | Googlebot UA | Playwright | Tested | |
| YouTube | Normal UA | - | Tested | Title & description only; video content not processed |
| GitHub | Normal UA | - | Tested | |
| PTT | Normal UA + over18 cookie | Playwright | Tested | Auto-sets over18 cookie |
| 104 Job Bank | Normal UA | - | Limited | Public job listing pages work; **profile share pages (pda.104.com.tw) are Vue SPA -- cannot be scraped** |
| Notion (public) | Googlebot UA | - | Tested | Public Notion pages render for Googlebot; full content extracted |
| Astro / SSG sites | Normal UA | - | Tested | Server-rendered HTML, most reliable category |
| LinkedIn | Googlebot UA | - | Not supported | Returns 999 for all methods; no usable content extracted |
| Instagram | - | - | Partial | Profile page (username/followers) only; **no free solution for single posts** |
| X / Twitter | Normal UA | Playwright | Limited | Increasingly login-gated; public tweets not guaranteed |
| Medium | Normal UA | curl_cffi -> Playwright | Limited | Cloudflare + SPA dual protection |
| Dcard | Normal UA | Playwright | Limited | Some posts require login; anonymous boards mostly locked |
| Others | Googlebot UA | Playwright | Best effort | |

### Status Definitions

- **Tested** -- Stable and reliable for public content
- **Partial** -- Some features work, but core functionality is limited
- **Limited** -- Stricter platform defenses; partial info (title, summary) available; reports why it failed
- **Not supported** -- Platform actively blocks all scraping methods; no usable content returned
- **Best effort** -- No specialized strategy; uses generic logic

### Platforms That Cannot Be Accessed

| Platform | Reason |
|----------|--------|
| LINE groups / posts | Closed ecosystem, no public URLs |
| Xiaohongshu | Closed + region-restricted |
| Paywalled content | Requires subscription; we don't bypass paywalls |

### Instagram Single Posts (as of 2026-03-13)

**No free reliable solution.** Instagram has fully blocked unauthenticated access since late 2024. All of the following methods fail: Googlebot UA, normal/mobile UA, `/embed/` endpoint, oEmbed API, unauthenticated Playwright, Google cache, IG internal API.

| Alternative | Description | Cost |
|-------------|-------------|------|
| Manual viewing | User logs into IG and provides screenshot or text | Free |
| Official embed | Meta oEmbed for display embedding (not full data extraction) | Free |
| Apify paid fallback | Built-in integration in grab.py; set `APIFY_TOKEN` to enable | Pay-per-use |

```bash
# Only activates for IG single posts when token is set; other features unaffected
export APIFY_TOKEN="apify_api_xxxxx"
```

## :open_file_folder: File Structure

```
all-can-grab/
  grab.py         # Main script
  SKILL.md        # Skill description (for Claude Code integration)
  README.md       # English docs
  README.zh-TW.md # Traditional Chinese docs
  README.ja.md    # Japanese docs
  LICENSE         # MIT
```

**As a Claude Code skill:** Place in `~/.claude/skills/learned/all-can-grab/` and Claude Code will auto-detect when to use it.
**Standalone:** Run `python grab.py <URL>` from any directory.

## :wrench: Customization

- **Add a new platform**: Add a new strategy entry in the platform config inside `grab.py`
- **Custom parsers**: The `clinic_slots` field demonstrates how to add domain-specific parsing (dental appointment slots as an example)
- **Environment variables**: Set `APIFY_TOKEN` for paid fallback on Instagram

## :bulb: Design Philosophy

- **Raw first** -- Don't open a browser if a simple HTTP request works. Saves resources and time.
- **Strategy separation** -- Each platform has its own scraping config. Adding a new site is just one entry.
- **Honest failure** -- Never fakes success. Reports what went wrong and suggests next steps.
- **Public only** -- No login, no stored credentials, no bypassing any protection.

### Output Schema

```json
{
  "summary": "3-5 sentence plain-language summary",
  "items": [
    {
      "title": "Post Title",
      "snippet": "Content excerpt...",
      "datetime_str": "2026-03-13",
      "author": "Author Name",
      "url": "https://..."
    }
  ],
  "clinic_slots": [],
  "status": "success",
  "blocker": "",
  "raw_text": "Full original text...",
  "source": "http-googlebot"
}
```

| Field | Description |
|-------|-------------|
| `status` | `success` / `partial` / `failed` |
| `source` | Which strategy was used: `http-googlebot` / `http-normal` / `curl_cffi` / `playwright` |
| `blocker` | Failure reason for diagnosing next steps |
| `clinic_slots` | Example extension: custom parser demo (not core functionality) |

## Requirements

- Python 3.8+
- `requests` + `beautifulsoup4` (required)
- `curl_cffi` (optional -- Cloudflare bypass)
- `playwright` (optional -- browser rendering)

## License

[MIT](LICENSE)

---

<p align="center">
  Give your agent the web it deserves.
</p>
