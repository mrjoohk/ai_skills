# WebFetch Guide for Tab Digest

This document covers strategies for fetching URLs, handling different page types, and gracefully managing failures.

---

## Fetch prompt template

Use this prompt string when calling WebFetch on each URL:

```
Extract the following from this page and return as structured text:
1. PAGE TITLE: The title of the page
2. TLDR: A single Korean sentence summarizing what this page is about and why it matters
3. SUMMARY: 3-5 Korean sentences explaining the key content — what does this page teach, offer, or announce?
4. CATEGORY: One of: 글/아티클, 도구/라이브러리, 튜토리얼/가이드, 공식문서, 뉴스, 영상, 기타
5. DOWNLOADS: Any software downloads, datasets, or files available (label + URL)
6. STEPS: Step-by-step instructions the reader should follow (in Korean, numbered)
7. COMMANDS: Any terminal/shell commands to copy and run (keep in original language)
```

---

## Page type strategies

Different pages yield different quality results from WebFetch. Adjust extraction accordingly:

### GitHub repositories
- The README is the most important part — it contains install commands, usage examples, and feature list
- Look for the "Installation" or "Getting Started" section specifically
- Badge links (build status, version) are noise — skip them
- The `pip install X`, `npm install X`, or `cargo add X` line is almost always in the README

### Documentation sites (Read the Docs, Docusaurus, GitBook, etc.)
- Focus on the "Getting Started" or "Installation" page if that's what's linked
- If it's an index/overview page, extract the high-level purpose and link to key sections
- Look for "Quick Start" code blocks — those are the most actionable content

### Blog articles / Medium / Substack
- The title and first 2-3 paragraphs usually contain the core thesis
- Look for numbered lists or bolded section headers — they're often the key takeaways
- If there's a "TL;DR" or "Summary" section in the article itself, prioritize that

### Product landing pages (e.g. ollama.com, ray.io)
- Focus on the "Get Started" or "Install" CTA section
- The hero tagline is usually a good TL;DR source
- Pricing/plan info is usually not relevant for a digest

### Video pages (YouTube, Vimeo)
- Use the title and description for the summary
- Note that the actual content can't be extracted — just what's described

---

## Handling fetch failures

When WebFetch returns an error or empty content:

### Step 1: Identify the tool from the URL
Parse the domain and path to recognize well-known tools:

| URL pattern | Tool |
|-------------|------|
| `ollama.com` | Ollama — local LLM runner |
| `python-poetry.org` | Poetry — Python dependency manager |
| `ray.io` | Ray — distributed computing framework |
| `github.com/fastapi/*` | FastAPI — Python web framework |
| `tailwindcss.com` | Tailwind CSS — utility-first CSS |
| `huggingface.co/docs/transformers` | HuggingFace Transformers |
| `docs.astro.build` | Astro — web framework |
| `docs.pydantic.dev` | Pydantic — Python data validation |
| `docker.com/get-started` | Docker — containerization |
| `docs.python.org` | Python official docs |
| `nextjs.org/docs` | Next.js — React framework |
| `vite.dev` or `vitejs.dev` | Vite — frontend build tool |

### Step 2: Fill from general knowledge
If recognized, write the entry from what you know — mark status as `known` and add a note:
```
note: "페이지 접근 불가 — 일반 지식 기반으로 작성"
```

### Step 3: Truly unknown URLs
If the URL is completely unrecognizable (e.g. a private company domain, an obscure personal blog):
```
status: failed
note: "페이지에 접근할 수 없습니다. 직접 확인이 필요합니다."
```
Leave action_items empty — don't guess.

---

## Quality checklist for each extracted entry

Before moving to HTML generation, verify each entry has:

- [ ] `tldr` — a complete Korean sentence (not just a phrase)
- [ ] `summary` — at least 3 Korean sentences with real content
- [ ] `category` — one of the 7 valid Korean category names
- [ ] `commands` — at least 1 command if the page is about a tool or library
- [ ] `status` — `ok`, `known`, or `failed`

If `tldr` is missing or vague (e.g. just "This is a tool"), rewrite it to be more informative before generating output.
