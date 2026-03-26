# python-docx Code Snippets for Tab Digest

Use these patterns when generating the Word document. All snippets assume python-docx is installed
(`pip install python-docx --break-system-packages`) and that Korean strings are passed as native
Python str objects (never escape them with `ascii()` or `json.dumps`).

---

## Document setup

```python
# -*- coding: utf-8 -*-
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import datetime

doc = Document()

# Set default font to support Korean characters
style = doc.styles['Normal']
style.font.name = '맑은 고딕'
style.font.size = Pt(11)

# Title
title = doc.add_heading('탭 다이제스트', 0)
title.alignment = WD_ALIGN_PARAGRAPH.CENTER

# Subtitle with date and count
today = datetime.date.today()
subtitle = doc.add_paragraph(f"{len(pages)}개 페이지 분석 결과 — {today.year}년 {today.month}월 {today.day}일")
subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
subtitle.runs[0].italic = True
subtitle.runs[0].font.color.rgb = RGBColor(0x71, 0x71, 0x71)

doc.add_paragraph()  # spacer
```

---

## Per-page section header

```python
def add_page_section(doc, title, url, category):
    # Page title as Heading 2
    doc.add_heading(title, level=2)

    # Source URL (italic, blue-gray)
    p = doc.add_paragraph()
    run = p.add_run(f"출처: {url}")
    run.italic = True
    run.font.color.rgb = RGBColor(0x55, 0x77, 0x99)
    run.font.size = Pt(9)

    # Category (bold)
    p2 = doc.add_paragraph()
    run2 = p2.add_run(f"분류: {category}")
    run2.bold = True
    run2.font.size = Pt(10)
```

---

## TL;DR box (yellow highlighted paragraph)

```python
def add_tldr(doc, tldr_text):
    p = doc.add_paragraph()
    run = p.add_run(f"💡 한 줄 요약: {tldr_text}")
    run.bold = True

    # Apply yellow highlight shading via XML
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), 'FFF9C4')  # light yellow
    pPr.append(shd)

    # Add left border for TL;DR emphasis
    pBdr = OxmlElement('w:pBdr')
    left = OxmlElement('w:left')
    left.set(qn('w:val'), 'single')
    left.set(qn('w:sz'), '24')
    left.set(qn('w:space'), '4')
    left.set(qn('w:color'), 'F59E0B')
    pBdr.append(left)
    pPr.append(pBdr)
```

---

## Summary paragraph

```python
def add_summary(doc, summary_text):
    p = doc.add_paragraph()
    run = p.add_run("요약  ")
    run.bold = True
    doc.add_paragraph(summary_text)
```

---

## Action items section

```python
def add_action_items(doc, downloads, steps, commands):
    if not (downloads or steps or commands):
        return

    doc.add_paragraph()
    h = doc.add_paragraph()
    h.add_run("액션 아이템").bold = True

    if downloads:
        doc.add_paragraph("📥 다운로드 링크", style='List Bullet')
        for item in downloads:
            p = doc.add_paragraph(style='List Bullet 2')
            run = p.add_run(f"{item['label']}: ")
            run.bold = True
            p.add_run(item['url'])

    if steps:
        doc.add_paragraph("👣 따라할 단계", style='List Bullet')
        for i, step in enumerate(steps, 1):
            doc.add_paragraph(f"{i}. {step}", style='List Number')

    if commands:
        doc.add_paragraph("💻 실행 명령어", style='List Bullet')
        for cmd in commands:
            p = doc.add_paragraph(cmd)
            run = p.runs[0]
            run.font.name = 'Courier New'
            run.font.size = Pt(9)
            # Light gray background for code
            pPr = p._p.get_or_add_pPr()
            shd = OxmlElement('w:shd')
            shd.set(qn('w:val'), 'clear')
            shd.set(qn('w:color'), 'auto')
            shd.set(qn('w:fill'), 'F3F4F6')
            pPr.append(shd)
```

---

## Horizontal rule between entries

```python
def add_separator(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '6')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), 'CCCCCC')
    pBdr.append(bottom)
    pPr.append(pBdr)
    doc.add_paragraph()  # spacing after rule
```

---

## Failed / known entry

```python
def add_failed_entry(doc, url, note, status='failed'):
    badge = "⚠️ 일반 지식 기반" if status == 'known' else "❌ 접근 불가"
    p = doc.add_paragraph()
    run = p.add_run(badge)
    run.bold = True
    run.font.color.rgb = RGBColor(0xD9, 0x73, 0x06) if status == 'known' else RGBColor(0xDC, 0x26, 0x26)
    doc.add_paragraph(f"URL: {url}")
    if note:
        doc.add_paragraph(note).italic = True
```

---

## Save the document

```python
output_path = f"/sessions/inspiring-dazzling-hawking/mnt/ai_skills/tab-digest-{datetime.date.today().strftime('%Y%m%d')}.docx"
doc.save(output_path)
print(f"저장됨: {output_path}")
```

---

## Common pitfalls

- **Never** call `ascii(text)` or `text.encode('ascii', 'backslashreplace')` on Korean strings — this produces `\uc548\ub155` in the document
- **Always** pass Korean strings as native Python str literals — Python 3 handles UTF-8 by default
- If a run's font doesn't support Korean (e.g. Calibri), characters may render as boxes on some systems — use `'맑은 고딕'` or `'나눔고딕'` for Korean runs
- python-docx's `add_heading()` uses built-in styles; the font may revert to the theme font — set `run.font.name` explicitly if needed
