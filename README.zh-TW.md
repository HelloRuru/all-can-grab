<h1 align="center">All Can Grab</h1>

<p align="center">
  <strong>貼連結，AI 說「抱歉我看不到」？</strong><br>
  其實那些內容都是公開的。問題不在 AI，在沒人教它怎麼開門。<br>
  這支腳本就是那串鑰匙。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-D4A5A5?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/python-3.8%2B-B8A9C9?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/dependencies-minimal-A8B5A0?style=flat-square" alt="Minimal Dependencies">
  <img src="https://img.shields.io/badge/claude_code-skill-E8B4B8?style=flat-square" alt="Claude Code Skill">
</p>

<p align="center">
  <a href="README.md">English</a> &nbsp;|&nbsp; <b>繁體中文</b> &nbsp;|&nbsp; <a href="README.ja.md">日本語</a>
</p>

---

## 痛點

你丟了一條 Facebook 連結給 AI。

它回你：*「抱歉，我無法擷取這個網頁。」*

……那篇貼文明明是公開的。

你只好自己開瀏覽器、複製、貼回去。每次都這樣。

說真的，光是「複製貼上」這件事，一天就能吃掉半小時。

問題不在 AI 不想幫你。是每個平台的門鎖不一樣，它手上沒有對的鑰匙。

## 解法

一支 Python 腳本，四層備援，自動幫 AI 配好每道門的鑰匙。

| 功能 | 說明 |
|------|------|
| 智慧 UA 切換 | Facebook/Threads 用 Googlebot UA，YouTube/GitHub 用一般 UA |
| TLS 指紋繞過 | curl_cffi 應對 Cloudflare 防護（如 Medium） |
| 付費 API 備援 | Apify 串接，處理完全封鎖免費存取的平台（如 Instagram） |
| 瀏覽器渲染 | 無頭 Playwright，處理需要 JavaScript 才能載入的頁面 |
| 結構化輸出 | 一致的 JSON schema，包含 status、source、blocker 欄位 |
| 誠實回報 | 不會假裝成功——明確告訴你為什麼失敗、建議怎麼做 |

## :package: 安裝

**第一步** -- Clone 並安裝為 Claude Code 全域技能：

```bash
# 這個路徑讓 Claude Code 全域自動偵測這個技能
git clone https://github.com/HelloRuru/all-can-grab.git ~/.claude/skills/learned/all-can-grab
```

**第二步** -- 安裝套件：

```bash
# 核心（必裝）
pip install requests beautifulsoup4

# 選用備援（裝越多，能抓的越多）
pip install curl_cffi                          # TLS 指紋繞過（Cloudflare）
pip install playwright && playwright install chromium  # 瀏覽器渲染
```

**第三步** -- 試一下：

```bash
python ~/.claude/skills/learned/all-can-grab/grab.py "https://www.facebook.com/share/p/xxxxx/"
```

> **重要：** 技能**必須**放在 `~/.claude/skills/learned/all-can-grab/` 才會讓 Claude Code 在你貼連結時自動觸發。放到其他位置不會啟用。

## :brain: 運作原理

四層策略，先快後穩：

1. **裸抓**（HTTP request）——不開瀏覽器，直接用適合的 User-Agent 去要 HTML。大多數公開網頁這樣就夠了。
2. **TLS 指紋備援**（curl_cffi）——模擬真實瀏覽器的 TLS 指紋，專門對付 Cloudflare 防護（如 Medium）。
3. **付費 API 備援**（Apify）——平台徹底封鎖免費存取時的最後手段（如 Instagram 單篇貼文）。
4. **瀏覽器備援**（Playwright）——前面都失敗就開無頭瀏覽器渲染，處理需要 JavaScript 的頁面。

不登入、不存 cookie、不繞過登入牆。只碰公開內容。

## :detective: 平台支援

| 平台 | 裸抓策略 | 備援 | 狀態 | 備註 |
|------|----------|------|------|------|
| Facebook | Googlebot UA | Playwright | Tested | 公開貼文、粉專穩定；含 OG URL 驗證防抓錯頁 |
| Threads | Googlebot UA | Playwright | Tested | |
| YouTube | Normal UA | - | Tested | 抓得到標題和描述，影片內容不處理 |
| GitHub | Normal UA | - | Tested | |
| PTT | Normal UA + over18 cookie | Playwright | Tested | 自動帶 over18 cookie |
| 104 人力銀行 | Normal UA | - | Limited | 公開職缺頁面可抓；**履歷分享頁（pda.104.com.tw）是 Vue SPA，抓不到** |
| Notion（公開頁面） | Googlebot UA | - | Tested | 公開 Notion 頁面對 Googlebot 會渲染完整內容 |
| Astro / SSG 靜態網站 | Normal UA | - | Tested | HTML 直出，最穩的一類 |
| LinkedIn | Googlebot UA | - | Not supported | 所有方法都回傳 999，完全抓不到任何內容 |
| Instagram | - | - | Partial | 個人頁面僅限帳號名/粉絲數；**單篇貼文無免費方案** |
| X / Twitter | Normal UA | Playwright | Limited | 越來越多內容鎖登入，公開推文也不一定抓得到 |
| Medium | Normal UA | curl_cffi -> Playwright | Limited | Cloudflare + SPA 雙重防護 |
| Dcard | Normal UA | Playwright | Limited | 部分文章要登入，匿名板幾乎都鎖 |
| 其他 | Googlebot UA | Playwright | Best effort | |

### 狀態說明

- **Tested** ——穩定可用，公開內容幾乎都抓得到
- **Partial** ——部分功能可用，但核心功能受限
- **Limited** ——平台防護較嚴，能拿到部分資料（標題、摘要），完整內文不保證。抓不到會回報卡點原因和建議
- **Not supported** ——平台主動封鎖所有抓取方式，完全拿不到任何內容
- **Best effort** ——沒有專門的策略，用通用邏輯盡力抓

### 這些門真的打不開

| 平台 | 原因 |
|------|------|
| LINE 群組 / 貼文 | 封閉生態，沒有公開 URL |
| 小紅書 | 封閉 + 地區限制 |
| 付費牆內容（天下、商周等） | 需要訂閱才看得到，不繞過付費牆 |

### Instagram 單篇貼文（截至 2026-03-13）

**無免費可靠方案。** IG 自 2024 年底全面封鎖未登入存取，以下方法全部失敗：Googlebot UA、一般/手機 UA、`/embed/` 端點、oEmbed API、未登入 Playwright、Google cache、IG 內部 API。

| 替代方式 | 說明 | 費用 |
|----------|------|------|
| 手動查看 | 使用者自行登入 IG，提供截圖或貼上文字 | 免費 |
| 官方嵌入 | Meta oEmbed，可做嵌入顯示，但無法任意抓取完整資料 | 免費 |
| Apify 付費備援 | grab.py 內建接口，設定 `APIFY_TOKEN` 後才啟用 | 按用量付費 |

```bash
# 只有設了 token，IG 單篇貼文才會走 Apify；沒設就跳過，不影響其他功能
export APIFY_TOKEN="apify_api_xxxxx"
```

## :open_file_folder: 檔案結構

```text
all-can-grab/
  grab.py         # 主程式
  SKILL.md        # 技能描述（Claude Code 整合用）
  README.md       # 英文版說明
  README.zh-TW.md # 繁體中文說明
  README.ja.md    # 日文版說明
  LICENSE         # MIT
```

**當作 Claude Code 技能：** 放到 `~/.claude/skills/learned/all-can-grab/`，Claude Code 會自動判斷何時啟用。
**獨立使用：** 在任何目錄執行 `python grab.py <URL>`。

## :wrench: 自訂設定

- **新增平台**：在 `grab.py` 的平台設定裡加一筆策略
- **自訂解析器**：`clinic_slots` 欄位示範如何加入領域專用的解析邏輯（以門診時段為例，非核心功能）
- **環境變數**：設定 `APIFY_TOKEN` 啟用 Instagram 付費備援

## :bulb: 為什麼這樣做

**能不開瀏覽器就不開。**
HTTP 搞得定的事，何必動用 Playwright？省時間，也省資源。

**每個網站一把鑰匙。**
Facebook 要 Googlebot UA，PTT 要 over18 cookie。策略分開寫，加新網站只要加一行。

**抓不到就直說。**
不裝沒事。失敗了會告訴你為什麼，建議你接下來怎麼做。

**只碰公開的。**
不登入、不存密碼、不繞付費牆。你看得到的，它才抓。

### 輸出格式

```json
{
  "summary": "3~5 句白話摘要",
  "items": [
    {
      "title": "貼文標題",
      "snippet": "內容摘錄...",
      "datetime_str": "2026-03-13",
      "author": "作者名稱",
      "url": "https://..."
    }
  ],
  "clinic_slots": [],
  "status": "success",
  "blocker": "",
  "raw_text": "完整原文...",
  "source": "http-googlebot"
}
```

| 欄位 | 說明 |
|------|------|
| `status` | `success` / `partial` / `failed` |
| `source` | 用了哪個策略：`http-googlebot` / `http-normal` / `curl_cffi` / `playwright` |
| `blocker` | 失敗時的原因，方便判斷下一步 |
| `clinic_slots` | 範例擴充：自訂解析器示範（非核心功能） |

## 系統需求

- Python 3.8+
- `requests` + `beautifulsoup4`（必要）
- `curl_cffi`（選裝——Cloudflare 繞過）
- `playwright`（選裝——瀏覽器渲染）

## 授權

[MIT](LICENSE)

---

<p align="center">
  門都開好了。去抓吧。
</p>
