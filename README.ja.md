<h1 align="center">All Can Grab</h1>

<p align="center">
  <strong>AI エージェントに本来あるべきウェブ取得能力を。</strong><br>
  「すみません、このページにアクセスできません」はもう終わり。4層フォールバック戦略で公開コンテンツを取得。<br>
  Python ファイル1つ。4層フォールバック。すべての公開ページを、1コマンドで。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-MIT-D4A5A5?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/python-3.8%2B-B8A9C9?style=flat-square" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/dependencies-minimal-A8B5A0?style=flat-square" alt="Minimal Dependencies">
  <img src="https://img.shields.io/badge/claude_code-skill-E8B4B8?style=flat-square" alt="Claude Code Skill">
</p>

<p align="center">
  <a href="README.md">English</a> &nbsp;|&nbsp; <a href="README.zh-TW.md">繁體中文</a> &nbsp;|&nbsp; <b>日本語</b>
</p>

---

## 課題

- AI エージェントに公開 Facebook 投稿を読ませようとすると——*「すみません、このページにアクセスできません」*と返される。
- ワークフローが毎回ここで止まる。自分でブラウザを開いてコピペして、また戻す。
- コンテンツは公開されているのに、エージェントは各プラットフォームの防御を突破できない。
- プラットフォームごとにロックが違う。一つの鍵では全部開かない。

## 解決策

Python スクリプト1本で、**4層フォールバック戦略**がプラットフォーム別の防御を自動処理。

| 機能 | 説明 |
|------|------|
| スマート UA 切替 | Facebook/Threads は Googlebot UA、YouTube/GitHub は通常 UA |
| TLS フィンガープリント回避 | curl_cffi で Cloudflare 保護サイト（Medium など）に対応 |
| 有料 API フォールバック | Apify 連携、完全ロックされたプラットフォーム（Instagram など）用 |
| ブラウザレンダリング | ヘッドレス Playwright、JavaScript が必要なページ用 |
| 構造化出力 | 統一 JSON スキーマ、status・source・blocker フィールド付き |
| 正直な報告 | 成功を偽らない——なぜ失敗したか、次に何をすべきか明確に報告 |

## :package: インストール

```bash
# ステップ 1：コア依存パッケージをインストール
pip install requests beautifulsoup4

# ステップ 2：オプションのフォールバックをインストール（多いほど取得範囲が広がる）
pip install curl_cffi                          # TLS フィンガープリント回避（Cloudflare）
pip install playwright && playwright install chromium  # ブラウザレンダリング

# ステップ 3：試してみる
python grab.py "https://www.facebook.com/share/p/xxxxx/"
```

## :brain: 仕組み

4層戦略、速いものから順に：

1. **素のHTTP**（HTTP request）——ブラウザを開かず、適切な User-Agent で直接 HTML を取得。ほとんどの公開ページはこれで十分。
2. **TLS フィンガープリント**（curl_cffi）——実際のブラウザの TLS フィンガープリントを模倣。Cloudflare 保護（Medium など）に対応。
3. **有料 API**（Apify）——プラットフォームが無料アクセスを完全にブロックした場合の最終手段（Instagram 単体投稿など）。
4. **ブラウザレンダリング**（Playwright）——上記すべてが失敗した場合、ヘッドレスブラウザで JavaScript をレンダリング。

ログインなし。Cookie 保存なし。ログインウォール回避なし。公開コンテンツのみ。

## :detective: プラットフォーム対応

| プラットフォーム | 素の取得戦略 | フォールバック | ステータス | 備考 |
|-----------------|-------------|---------------|-----------|------|
| Facebook | Googlebot UA | Playwright | Tested | 公開投稿・ページ安定；OG URL 検証含む |
| Threads | Googlebot UA | Playwright | Tested | |
| YouTube | Normal UA | - | Tested | タイトルと説明のみ；動画コンテンツは未対応 |
| GitHub | Normal UA | - | Tested | |
| PTT | Normal UA + over18 cookie | Playwright | Tested | over18 cookie 自動設定 |
| 104 Job Bank | Normal UA | - | Limited | 公開求人ページは取得可能；**プロフィール共有ページ（pda.104.com.tw）は Vue SPA で取得不可** |
| Notion（公開ページ） | Googlebot UA | - | Tested | 公開 Notion ページは Googlebot に完全なコンテンツをレンダリング |
| Astro / SSG サイト | Normal UA | - | Tested | サーバーレンダリング HTML、最も安定 |
| LinkedIn | Googlebot UA | - | Not supported | 全メソッドで 999 エラー；取得可能なコンテンツなし |
| Instagram | - | - | Partial | プロフィール（ユーザー名/フォロワー数）のみ；**単体投稿の無料手段なし** |
| X / Twitter | Normal UA | Playwright | Limited | ログイン要求が増加中；公開ツイートも取得不保証 |
| Medium | Normal UA | curl_cffi -> Playwright | Limited | Cloudflare + SPA 二重防御 |
| Dcard | Normal UA | Playwright | Limited | 一部投稿はログイン必要；匿名板はほぼロック |
| その他 | Googlebot UA | Playwright | Best effort | |

### ステータス定義

- **Tested** ——安定動作、公開コンテンツはほぼ取得可能
- **Partial** ——一部機能は動作するが、コア機能に制限あり
- **Limited** ——プラットフォーム防御が厳しく、部分情報（タイトル・要約）は取得可能。失敗時は原因と提案を報告
- **Not supported** ——プラットフォームが全スクレイピング手法を積極的にブロック；取得可能なコンテンツなし
- **Best effort** ——専用戦略なし、汎用ロジックで最善を尽くす

### アクセス不可能なプラットフォーム

| プラットフォーム | 理由 |
|-----------------|------|
| LINE グループ / 投稿 | クローズドエコシステム、公開 URL なし |
| 小紅書（RED） | クローズド + 地域制限 |
| 有料コンテンツ | サブスクリプション必要；ペイウォール回避はしない |

### Instagram 単体投稿（2026-03-13 時点）

**無料で信頼できる手段なし。** Instagram は 2024 年末から未認証アクセスを完全ブロック。以下の方法はすべて失敗：Googlebot UA、通常/モバイル UA、`/embed/` エンドポイント、oEmbed API、未認証 Playwright、Google cache、IG 内部 API。

| 代替手段 | 説明 | 費用 |
|----------|------|------|
| 手動確認 | ユーザー自身が IG にログインし、スクリーンショットやテキストを提供 | 無料 |
| 公式埋め込み | Meta oEmbed で表示埋め込み可能（完全データ抽出は不可） | 無料 |
| Apify 有料フォールバック | grab.py に内蔵；`APIFY_TOKEN` 設定で有効化 | 従量課金 |

```bash
# トークン設定時のみ IG 単体投稿で Apify を使用；未設定なら他の機能に影響なし
export APIFY_TOKEN="apify_api_xxxxx"
```

## :open_file_folder: ファイル構成

```text
all-can-grab/
  grab.py         # メインスクリプト
  SKILL.md        # スキル説明（Claude Code 統合用）
  README.md       # 英語版ドキュメント
  README.zh-TW.md # 繁体字中国語ドキュメント
  README.ja.md    # 日本語ドキュメント
  LICENSE         # MIT
```

**Claude Code スキルとして：** `~/.claude/skills/learned/all-can-grab/` に配置すると、Claude Code が自動判断して使用。
**スタンドアロン：** 任意のディレクトリで `python grab.py <URL>` を実行。

## :wrench: カスタマイズ

- **プラットフォーム追加**：`grab.py` のプラットフォーム設定に戦略エントリを追加
- **カスタムパーサー**：`clinic_slots` フィールドがドメイン固有のパーサー追加方法を実演（歯科予約枠の例、コア機能ではない）
- **環境変数**：`APIFY_TOKEN` を設定して Instagram 有料フォールバックを有効化

## :bulb: 設計思想

- **素の取得優先** ——ブラウザを開かずに済むなら開かない。リソースと時間を節約。
- **戦略分離** ——各サイトに独自の取得設定。新しいサイトの追加は1エントリだけ。
- **失敗は正直に** ——成功を偽らない。何が問題か、次に何をすべきか報告。
- **公開コンテンツのみ** ——ログインなし、認証情報保存なし、防御回避なし。

### 出力スキーマ

```json
{
  "summary": "3~5文の要約",
  "items": [
    {
      "title": "投稿タイトル",
      "snippet": "コンテンツ抜粋...",
      "datetime_str": "2026-03-13",
      "author": "著者名",
      "url": "https://..."
    }
  ],
  "clinic_slots": [],
  "status": "success",
  "blocker": "",
  "raw_text": "完全な原文...",
  "source": "http-googlebot"
}
```

| フィールド | 説明 |
|-----------|------|
| `status` | `success` / `partial` / `failed` |
| `source` | 使用した戦略：`http-googlebot` / `http-normal` / `curl_cffi` / `playwright` |
| `blocker` | 失敗原因（次のステップの判断用） |
| `clinic_slots` | 拡張例：カスタムパーサーのデモ（コア機能ではない） |

## 動作要件

- Python 3.8+
- `requests` + `beautifulsoup4`（必須）
- `curl_cffi`（オプション——Cloudflare 回避）
- `playwright`（オプション——ブラウザレンダリング）

## ライセンス

[MIT](LICENSE)

---

<p align="center">
  Give your agent the web it deserves.
</p>
