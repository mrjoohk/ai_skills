---
name: tab-digest
description: |
  Analyzes a list of URLs (web pages the user has saved or wants to review) and produces a structured digest: a concise summary of each page, the key takeaways, and extracted action items like download links, step-by-step instructions, and commands to run. Outputs both an interactive HTML dashboard and a Word document (.docx).

  ALWAYS use this skill when the user:
  - Pastes a list of URLs and asks for a summary, review, or digest
  - Says things like "탭 정리해줘", "이 링크들 요약해줘", "저장해놓은 페이지들 정리해줘", "url 분석해줘"
  - Wants to know "what's important" across a set of links they've been collecting
  - Asks to extract "할 일", "다운로드", "설치 방법", or "따라할 단계" from a set of pages
  - Mentions they have too many tabs open and want a digest or summary

  Even if the user just pastes raw URLs without much explanation, this skill is likely the right tool.
---

# Tab Digest Skill

You are helping the user get on top of a backlog of web pages they've saved. Your job is to fetch each page, understand it well, and produce a digest that makes it easy to decide what to do next — without the user having to read each page themselves.

## Bundled resources

This skill includes helper files — read them before generating output:

| Resource | When to use |
|----------|-------------|
| `references/webfetch-guide.md` | Read at step 1 for fetch prompt templates, page-type strategies, and the failure/fallback lookup table |
| `references/docx-snippets.md` | Read at step 3 for ready-to-use python-docx code patterns (TL;DR shading, code blocks, separators) |
| `assets/html_template.html` | Use as the base for the HTML output — fill in `{{DATE}}`, `{{COUNT}}`, `{{FILTER_BUTTONS}}`, and `{{CARDS}}` placeholders |
| `scripts/validate_output.py` | Run at step 4 after saving files to verify encoding and structure |

## Language requirement

**All output content MUST be written in Korean (한국어).** This applies to everything visible in the HTML and Word document: page titles (if Korean is more natural), TL;DR text, summaries, action item descriptions, section labels, category names, status messages, and any narrative text. The only exceptions are: original command-line instructions (keep as-is, e.g. `pip install fastapi`), URLs, and technical terms/proper nouns that are universally understood in English (e.g. "FastAPI", "React", "Docker").

## Input

The user will provide a list of URLs — either one per line or comma/space separated. Extract all valid URLs from their message.

## Workflow

Work through these steps in order:

### 1. Fetch and analyze each URL

**First, read `references/webfetch-guide.md`** — it has the exact fetch prompt template, per-page-type strategies (GitHub, docs sites, blogs), and the failure fallback lookup table for well-known tools.

For each URL, use WebFetch to retrieve the content. Use this prompt when fetching:
> "Extract: (1) the page title, (2) a 1-sentence TL;DR in Korean, (3) a 3-5 sentence summary in Korean of the key content, (4) the category (one of: 글/아티클, 도구/라이브러리, 튜토리얼/가이드, 공식문서, 뉴스, 영상, 기타), (5) any download links (software, files, datasets), (6) any step-by-step instructions or commands the reader should follow, (7) any setup/installation/execution commands."

**If a URL fails** (auth wall, timeout, blocked by network):
- First, check if you recognize the tool/project from the URL itself (e.g. `ollama.com`, `python-poetry.org`, `ray.io`). If you do, use your general knowledge to fill in the TL;DR, summary, category, and likely action items — mark the status as `known` and add a note like "페이지 접근 불가 — 일반 지식 기반으로 작성".
- If you genuinely don't recognize it at all, mark it as `failed` (접근 불가) and include the URL so the user can check it manually.
- Never let one failure block the rest of the URLs.

Collect this structured data for each URL:
```
title: ...
url: ...
tldr: ...          ← Korean sentence
summary: ...       ← Korean paragraph
category: ...      ← Korean category name
action_items:
  downloads: [list of {label (Korean), url}]
  steps: [list of Korean step strings]
  commands: [list of command strings — keep in original language]
status: ok | known | failed
note: ...          ← optional, e.g. "페이지 접근 불가 — 일반 지식 기반으로 작성"
```

### 2. Generate the HTML dashboard

**Use `assets/html_template.html` as the base.** Read it, then fill in the four placeholders:
- `{{DATE}}` → today's date (e.g. `2026년 3월 24일`)
- `{{COUNT}}` → number of URLs processed
- `{{FILTER_BUTTONS}}` → one `<button>` per distinct category in the data
- `{{CARDS}}` → one `<article class="card">` block per URL (templates are included in the file as HTML comments)

Do not rewrite the CSS or JS from scratch — the template has it all. Just replace the placeholders and paste in the card HTML.

**Critical: write all HTML content in UTF-8 Korean directly.** Do NOT use Python's `json.dumps(..., ensure_ascii=True)` or any method that converts Korean characters to `\uXXXX` escape sequences in the file. The file must contain actual Korean characters (가나다) so browsers can render them correctly.

**Layout:**
- Header: "📋 탭 다이제스트" + 오늘 날짜 + 총 URL 수 (예: "3개 페이지 분석")
- Filter bar: buttons to filter cards by category — labels in Korean
- Card grid: one card per URL

**Each card contains:**
- **제목** (linked to original URL) + category badge (Korean)
- **한 줄 요약 (TL;DR)** — shown prominently in a colored highlight box (light yellow background, e.g. `#fffbeb`)
- **요약** — 3-5 sentences, collapsible with `<details><summary>자세히 보기</summary>...</details>` if long
- **액션 아이템** section (only show if there are any):
  - 📥 **다운로드**: clickable download links with Korean labels
  - 👣 **따라할 단계**: numbered list of steps in Korean
  - 💻 **실행 명령어**: monospaced code blocks (commands stay in English/original)
- If the page was inaccessible but known: show a "⚠️ 일반 지식 기반" badge
- If truly failed: show a "❌ 접근 불가" badge and the URL

**Styling guidance:**
- Use a clean sans-serif font (system-ui or -apple-system)
- Responsive card grid: `display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 1.5rem;`
- Category badges: small pill-shaped labels with distinct background colors per category
- TL;DR box: `background: #fffbeb; border-left: 4px solid #f59e0b; padding: 0.75rem 1rem;`
- Action items: clearly separated section with a light gray background block

All CSS and JS inline in the single HTML file. Set `<meta charset="UTF-8">` as the first tag inside `<head>`.

### 3. Generate the Word document

**Read `references/docx-snippets.md`** — it has copy-paste-ready Python code for the TL;DR yellow-shaded box, code blocks in monospace, horizontal rules between entries, and the document title/subtitle setup. Use those patterns directly rather than writing from scratch.

Create a .docx file using Python (python-docx). All content must be written in Korean (except commands and proper nouns).

**Critical:** When building strings in Python that contain Korean text, make sure Python source files or string literals properly encode Korean. Use `# -*- coding: utf-8 -*-` at the top of any Python script you write, and always pass `encoding='utf-8'` when writing files. Never use `ascii()` or any method that would convert Korean to escape sequences.

**Document structure:**
```
제목 (Title style): 탭 다이제스트
부제 (Subtitle style): [N]개 페이지 분석 결과 — [YYYY년 MM월 DD일]

For each URL (in order):
  Heading 2: [페이지 제목]
  본문 (italic gray): 출처: [URL]
  본문 (bold): 분류: [카테고리]

  한 줄 요약 (TL;DR):
  → highlighted paragraph (yellow shading) with the 1-sentence Korean summary

  요약:
  [3-5 sentence Korean summary as a normal paragraph]

  액션 아이템 (only if present):
    📥 다운로드 링크 (bold heading):
      • [Korean label]: [URL]
    👣 따라할 단계 (bold heading):
      1. 단계 1 (Korean)
      2. 단계 2 (Korean)
    💻 실행 명령어 (bold heading):
      [monospace font paragraph — commands in original language]

  [paragraph border/horizontal rule between entries]
```

Install python-docx if needed: `pip install python-docx --break-system-packages`

### 4. Save, validate, and present outputs

Save both files to `/sessions/inspiring-dazzling-hawking/mnt/ai_skills/`:
- `tab-digest-[YYYYMMDD].html`
- `tab-digest-[YYYYMMDD].docx`

**Run the validation script** to catch encoding issues before presenting to the user:
```bash
python <skill_dir>/scripts/validate_output.py /sessions/inspiring-dazzling-hawking/mnt/ai_skills/
```
If any checks fail (especially "유니코드 이스케이프 없음" or "한국어 문자 포함"), fix the file before presenting.

Then present both files to the user using the `present_files` tool if available, or share as computer:// links.

## Tips for good output

- **Write in Korean throughout.** Every summary, label, step description, and section header should be in natural Korean. The user should be able to read the digest without switching languages.
- **Be concise but informative.** The TL;DR should actually tell the user something — not just "This is an article about X." Tell them *what it says*, e.g. "FastAPI는 Python 타입 힌트 기반의 고성능 API 프레임워크로, 자동 API 문서 생성과 빠른 개발 속도가 특징이다."
- **Prioritize action items.** If a page has installation steps or commands, capture them precisely — this is often the most valuable part of the digest.
- **Use general knowledge as fallback.** For well-known tools (e.g. Ollama, Poetry, Docker), if the URL fails, use what you know to write a useful summary and likely commands rather than leaving a blank entry.
- **Don't invent action items.** If a page is genuinely unknown (e.g. a private/unknown URL that failed), don't fabricate steps. Leave the action items empty and note "직접 확인 필요".
- **Encode output correctly.** All output files must use UTF-8 encoding with actual Korean characters — not unicode escape sequences like `\uc548\ub155`. Always set `<meta charset="UTF-8">` in HTML and use proper encoding when writing files from Python.
