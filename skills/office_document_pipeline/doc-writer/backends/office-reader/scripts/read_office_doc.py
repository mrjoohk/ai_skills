#!/usr/bin/env python3
"""DRM(DocuRay 등)이 걸린 MS Office 문서를 허용 앱 COM(pywin32)으로 판독한다.

파이썬은 DocuRay 허용 앱이 아니어서 DRM 파일을 직접 열면 암호문을 받는다(BadZipFile).
그래서 Excel/Word/PowerPoint 에게 파일을 열게 하고 COM 으로 값만 받아온다.
암호를 풀거나 키를 꺼내지 않는다. 허용 앱이 아니면 실패하는 것이 정상이다.

    python read_office_doc.py <파일> [--pattern 키1,키2] [--sheet 이름|순번] [--fill-merged]
                              [--preview 5] [--max-rows 5000] [--max-cols 200]
                              [--log 결과.md] [--dump 전문.md]

기본은 아무 파일도 만들지 않는다. --log 는 화면 출력을 그대로, --dump 는 문서 전문을
.md 로 남긴다(평문 사본이 생긴다). PDF/PNG 는 만들지 않는다 (D-003).

종료코드: 0 완료 / 1 실패·지원하지 않는 형식·PowerPoint 창이 열려 있음 / 3 pywin32 없음
"""
import argparse
import datetime
import html
import os
import sys

EXCEL_EXT = {".xlsx", ".xlsm", ".xlsb", ".xltx", ".xltm", ".xls"}
WORD_EXT = {".docx", ".docm", ".doc", ".rtf", ".dotx", ".dotm"}
PPT_EXT = {".pptx", ".pptm", ".ppt", ".potx"}
# 열기암호가 걸린 파일은 암호 대화상자를 띄워 헤드리스 실행이 멈춘다. 가짜 암호를 주면 대화상자 대신 오류가 난다.
# 암호가 없는 파일에는 무시된다 (DocuRay 보호는 Office 암호가 아니다).
DUMMY_PW = "__office_no_password__"
# COM 메서드에서 건너뛸 자리. pywin32 동적 디스패치는 이름 인자 사이에 빈 자리가 있으면 그 뒤 인자를 말없이
# 버린다 — Open(…, Password=) 의 암호, Add(After=) 의 After 가 그렇게 사라졌다 (F-085). 그래서 COM 호출은
# 자리 인자로만 쓰고 빈 자리에 OMIT 을 넣는다. pythoncom.Empty 는 '생략(기본값)'으로 전달된다.
try:
    import pythoncom as _pythoncom
    OMIT = _pythoncom.Empty
except ImportError:                     # pywin32 없는 환경(가짜 COM 시험)
    OMIT = type("Omit", (), {"__repr__": lambda s: "OMIT"})()
# VT_ERROR 셀은 pywin32 가 정수 SCODE 로 준다
XL_ERRORS = {-2146826281: "#DIV/0!", -2146826246: "#N/A", -2146826259: "#NAME?", -2146826288: "#NULL!",
             -2146826252: "#NUM!", -2146826265: "#REF!", -2146826273: "#VALUE!"}

STORY_NAME = {2: "각주", 3: "미주", 4: "메모", 5: "텍스트 상자", 6: "머리글(짝수)", 7: "머리글",
              8: "바닥글(짝수)", 9: "바닥글", 10: "머리글(첫 쪽)", 11: "바닥글(첫 쪽)"}


class Out:
    """화면과 --log 파일(UTF-8 BOM)에 같은 줄을 쓴다. cmd 의 > 리다이렉트는 한글을 깨뜨린다."""

    def __init__(self, log_path=None):
        self.f = open(log_path, "w", encoding="utf-8-sig") if log_path else None
        self.hits = 0

    def __call__(self, text=""):
        if self.f:                      # 로그를 먼저 쓴다 — 화면 출력이 실패해도 기록은 남는다
            self.f.write(text + "\n")
            self.f.flush()
        print(text)                     # main 에서 stdout 을 errors="replace" 로 바꿔 둔다

    def close(self):
        if self.f:
            self.f.close()


# ---------------------------------------------------------------- 공통 도우미

def col_name(index):
    """1 -> A, 27 -> AA. 검색 좌표를 writer 의 --cell 과 같은 A1 표기로 보고한다 (F-014)."""
    name = ""
    while index > 0:
        index, m = divmod(index - 1, 26)
        name = chr(65 + m) + name
    return name


def fmt_value(v):
    """셀 값을 문자열로. 날짜는 일련번호가 아니라 yyyy-MM-dd (F-015)."""
    if v is None:
        return ""
    if isinstance(v, datetime.datetime):
        if (v.year, v.month, v.day) == (1899, 12, 30):          # 시각만 있는 셀
            return v.strftime("%H:%M:%S")
        if (v.hour, v.minute, v.second) == (0, 0, 0):
            return v.strftime("%Y-%m-%d")
        return v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, int) and v in XL_ERRORS:                    # Excel 숫자는 float 로 온다. int 는 오류 값
        return XL_ERRORS[v]
    if isinstance(v, float):
        if v.is_integer() and abs(v) < 1e15:
            return str(int(v))
        return "%.15g" % v
    return str(v)


def as_grid(vals):
    """Range.Value 를 2차원 리스트로. 단일 셀이면 스칼라가 온다."""
    if not isinstance(vals, (tuple, list)):
        return [[vals]]
    return [list(row) if isinstance(row, (tuple, list)) else [row] for row in vals]


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def com_error_text(e):
    """pywintypes.com_error 에서 사람이 읽을 설명을 한 줄로 꺼낸다.
    Office 메시지에는 줄바꿈(CR)이 섞여 있어 콘솔에서 앞 글자를 덮어쓴다 (F-086).
    Excel 은 설명을 HTML 이스케이프해서 준다 — '&lt;Caps Lock&gt;' (F-088)."""
    try:
        info = e.args[2]
        text = info[2] if info and info[2] else e.args[1]
    except Exception:
        text = e
    return " ".join(html.unescape(str(text)).split())


def hit(out, text, where, keys):
    """키워드에 걸리면 위치와 문맥(120자)을 출력한다. 한 텍스트에 첫 키 하나만 센다."""
    if not keys or not text:
        return False
    low = text.lower()
    for k in keys:
        if k.lower() in low:
            snip = " ".join(text.split())[:120]
            out("  [%s] %s  %s" % (k, where, snip))
            out.hits += 1
            return True
    return False


def powerpoint_window_open():
    """사용자 화면에 PowerPoint 창(PPTFrameClass)이 떠 있는가.
    PowerPoint 는 단일 인스턴스라 COM 이 그 창에 붙었다가 Quit() 으로 함께 닫는다 (F-028).
    창 없는 잔류 프로세스는 직전 자동화의 것이라 붙어도 안전하다 — 프로세스 유무로 판단하면
    방금 닫은 인스턴스가 남아 있는 동안 거짓 거부가 난다 (F-046, P-010 V5r)."""
    try:
        import win32gui
    except ImportError:
        return False
    found = []

    def cb(h, _):
        try:
            if win32gui.GetClassName(h) == "PPTFrameClass" and win32gui.IsWindowVisible(h):
                found.append(h)
        except Exception:               # 열거 중 창이 닫히면 오류 1400 — 그 창은 건너뛴다
            pass
        return True

    try:
        win32gui.EnumWindows(cb, None)
    except Exception:
        pass
    return bool(found)


def com_create(progid):
    """새 인스턴스를 동적 디스패치로 만든다 (makepy 캐시 유무에 따라 동작이 바뀌지 않게)."""
    import win32com.client
    import win32com.client.dynamic
    app = win32com.client.DispatchEx(progid)
    return win32com.client.dynamic.Dispatch(app._oleobj_)


# ---------------------------------------------------------------- Excel

def read_excel(create, path, keys, opt, out, dump):
    app = create("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.AskToUpdateLinks = False
    app.EnableEvents = False
    safe(lambda: setattr(app, "AutomationSecurity", 3))   # 매크로 강제 차단 (F-020)
    wb = None
    try:
        # Filename, UpdateLinks=0, ReadOnly=True, Format(생략), Password — 자리 인자로 (F-085)
        wb = app.Workbooks.Open(path, 0, True, OMIT, DUMMY_PW)
        sheets = [wb.Worksheets(i) for i in range(1, wb.Worksheets.Count + 1)]

        out("=== SHEETS ===")
        name_hit = False
        for ws in sheets:
            ur = ws.UsedRange
            addr = safe(lambda: str(ur.Address).replace("$", ""), "")
            out("  %2d. %-34s %7d rows x %4d cols  %s" % (ws.Index, ws.Name, ur.Rows.Count, ur.Columns.Count, addr))
            if opt.sheet and opt.sheet.lower() in str(ws.Name).lower():
                name_hit = True
        out()

        # --sheet 는 이름 부분일치가 우선. 맞는 이름이 없고 숫자일 때만 순번 (F-018, F-039)
        use_index = bool(opt.sheet) and not name_hit and opt.sheet.isdigit()
        matched = 0
        for ws in sheets:
            if opt.sheet:
                if use_index:
                    if int(ws.Index) != int(opt.sheet):
                        continue
                elif opt.sheet.lower() not in str(ws.Name).lower():
                    continue
            matched += 1

            ur = ws.UsedRange
            r0, c0 = int(ur.Row), int(ur.Column)
            nr, nc = int(ur.Rows.Count), int(ur.Columns.Count)
            rows, cols = min(nr, opt.max_rows), min(nc, opt.max_cols)
            if nr > opt.max_rows or nc > opt.max_cols:
                out("  ! %s: %dx%d 중 %dx%d 만 읽는다 (--max-rows/--max-cols 로 조정)" % (ws.Name, nr, nc, rows, cols))

            # Value 는 날짜를 datetime 으로 준다. Value2 는 일련번호(46296)를 준다 (F-015)
            # 상한 안쪽만 가져온다. UsedRange 가 1048576행으로 잡힌 시트를 통째로 받으면 메모리가 터진다
            vals = ws.Range(ws.Cells(r0, c0), ws.Cells(r0 + rows - 1, c0 + cols - 1)).Value
            if vals is None:
                continue
            grid = as_grid(vals)

            # 병합셀은 좌상단에만 값이 있다. --fill-merged 는 실제 병합 영역의 좌상단 값만 채운다 (F-013)
            merge_any = False
            if opt.fill_merged and (rows > 1 or cols > 1):
                merge_any = safe(lambda: ur.MergeCells is not False, True)

            md_rows = []
            shown = 0
            for r in range(1, rows + 1):
                cells = []
                for c in range(1, cols + 1):
                    v = grid[r - 1][c - 1] if r - 1 < len(grid) and c - 1 < len(grid[r - 1]) else None
                    if v is None:
                        s = ""
                        if merge_any:
                            try:
                                cell = ws.Cells(r0 + r - 1, c0 + c - 1)
                                if cell.MergeCells is True:
                                    ma = cell.MergeArea
                                    tr, tc = int(ma.Row) - r0 + 1, int(ma.Column) - c0 + 1
                                    if 1 <= tr <= rows and 1 <= tc <= cols:
                                        s = fmt_value(grid[tr - 1][tc - 1])
                            except Exception:
                                pass
                    else:
                        s = fmt_value(v)
                    cells.append(s)
                    if keys:
                        hit(out, s, "%s!%s%d" % (ws.Name, col_name(c0 + c - 1), r0 + r - 1), keys)
                if dump is not None:
                    md_rows.append(cells)
                if not keys and shown < opt.preview:
                    t = " ".join(" ".join(x for x in cells if x).split())
                    if t:
                        if shown == 0:
                            out("--- %s ---" % ws.Name)
                        out("  " + t[:140])
                        shown += 1
            if shown:
                out()
            if dump is not None:
                dump.append("## %s (%s%d:%s%d)\n" % (ws.Name, col_name(c0), r0, col_name(c0 + cols - 1), r0 + rows - 1))
                dump.extend(md_table(md_rows))
                dump.append("")

        if opt.sheet and matched == 0:
            out("  ! --sheet '%s' 에 맞는 시트가 없다 (이름 일부 또는 위 목록의 순번을 준다)" % opt.sheet)
    finally:
        if wb is not None:
            safe(lambda: wb.Close(False))
        safe(lambda: app.Quit())


def md_table(rows):
    """행 리스트를 마크다운 표 줄로. 첫 행을 머리글로 쓴다."""
    if not rows:
        return ["(빈 시트)"]
    width = max(len(r) for r in rows)

    def esc(s):
        return s.replace("|", "\\|").replace("\r", " ").replace("\n", " / ")

    lines = []
    for i, r in enumerate(rows):
        r = list(r) + [""] * (width - len(r))
        lines.append("| " + " | ".join(esc(x) for x in r) + " |")
        if i == 0:
            lines.append("|" + "---|" * width)
    return lines


# ---------------------------------------------------------------- Word

def word_extra_stories(doc):
    """본문(Content) 밖의 글자: 머리글·바닥글(안의 텍스트 상자 포함)·텍스트 상자·각주·미주 (F-017).
    첫 구역 머리글·바닥글이 비면 StoryRanges 가 뒤 구역 머리글까지 건너뛰므로 StoryType 을
    한 번 읽어 둔다 (F-036, Word MVP 들이 쓰는 우회법)."""
    safe(lambda: doc.Sections(1).Headers(1).Range.StoryType)
    safe(lambda: doc.Sections(1).Footers(1).Range.StoryType)
    extra, seen = [], set()
    for story in doc.StoryRanges:
        st = safe(lambda: int(story.StoryType), 0)
        if st <= 1 or st >= 12:
            continue
        label = STORY_NAME[st]
        rng, guard = story, 0
        while rng is not None and guard < 500:
            guard += 1
            txt = safe(lambda: str(rng.Text), "")
            if 6 <= st <= 11:
                for shp in safe(lambda: list(rng.ShapeRange), []):
                    if safe(lambda: shp.TextFrame.HasText, 0):
                        txt += "\r" + safe(lambda: str(shp.TextFrame.TextRange.Text), "")
            for line in txt.split("\r"):
                line = line.replace("\x07", " ").strip()
                if line and (label, line) not in seen:      # 연결된 머리글은 구역마다 반복된다
                    seen.add((label, line))
                    extra.append((label, line))
            rng = safe(lambda: rng.NextStoryRange)
    return extra


def read_word(create, path, keys, opt, out, dump):
    app = create("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0                                  # wdAlertsNone (열거형)
    safe(lambda: setattr(app, "AutomationSecurity", 3))   # AutoOpen 매크로 차단 (F-020)
    doc = None
    try:
        # FileName, ConfirmConversions, ReadOnly, AddToRecentFiles, PasswordDocument (F-085)
        doc = app.Documents.Open(path, False, True, False, DUMMY_PW)
        n_para, n_tbl = int(doc.Paragraphs.Count), int(doc.Tables.Count)
        out("=== WORD ===")
        out("  문단 %d개 · 표 %d개 · 구역 %d개" % (n_para, n_tbl, int(doc.Sections.Count)))
        out()

        # 본문을 COM 호출 한 번으로. 문단 끝은 \r, 표 셀 끝은 \a(0x07)
        raw = str(doc.Content.Text)
        body = [l.replace("\x07", " ").strip() for l in raw.split("\r")]
        body = [l for l in body if l]
        extra = word_extra_stories(doc)

        heads = []
        cap = min(n_para, 1000)
        for i in range(1, cap + 1):
            para = safe(lambda: doc.Paragraphs(i))
            if para is None:
                continue
            style = safe(lambda: str(para.Style.NameLocal), "")
            if any(k in style for k in ("제목", "Heading", "Title")):
                t = safe(lambda: str(para.Range.Text), "").replace("\r", "").replace("\x07", "").strip()
                if t:
                    heads.append("[%s] %s" % (style, t[:100]))

        if keys:
            # "본문 줄 N" 은 빈 줄을 뺀 순번이다. Word 의 Paragraphs(N) 번호와 다르다
            for i, l in enumerate(body, 1):
                hit(out, l, "본문 줄 %d" % i, keys)
            for label, l in extra:
                hit(out, l, label, keys)
        else:
            out("--- 개요 (제목 스타일) ---")
            out("\n".join("  " + h for h in heads) if heads else "  (제목 스타일 문단 없음)")
            if n_para > cap:
                out("  … 앞 %d문단만 스타일 검사" % cap)
            out()
            out("--- 본문 미리보기 ---")
            if not body:
                out("  (본문 텍스트 없음 — 이미지/도형만 있는 문서일 수 있다)")
            for l in body[:opt.preview]:
                out("  " + l[:140])
            if len(body) > opt.preview:
                out("  … (%d개 더). 전체를 보려면 --preview %d 또는 --dump" % (len(body) - opt.preview, len(body)))
            out()
            out("--- 본문 밖 (머리글·바닥글·텍스트 상자·각주) %d줄 ---" % len(extra))
            if not extra:
                out("  (없음)")
            for label, l in extra[:opt.preview]:
                out("  [%s] %s" % (label, l[:140]))
            if len(extra) > opt.preview:
                out("  … (%d줄 더)" % (len(extra) - opt.preview))

        if dump is not None:
            dump.append("## 본문\n")
            dump.extend(body)
            dump.append("")
            for t in range(1, n_tbl + 1):
                tbl = doc.Tables(t)
                rows = []
                for r in range(1, int(tbl.Rows.Count) + 1):
                    rows.append([safe(lambda: str(tbl.Cell(r, c).Range.Text), "").replace("\r", " ").replace("\x07", "").strip()
                                 for c in range(1, int(tbl.Columns.Count) + 1)])
                dump.append("## 표 %d\n" % t)
                dump.extend(md_table(rows))
                dump.append("")
            if extra:
                dump.append("## 본문 밖 (머리글·바닥글·텍스트 상자·각주)\n")
                dump.extend("- [%s] %s" % (label, l) for label, l in extra)
                dump.append("")
    finally:
        if doc is not None:
            safe(lambda: doc.Close(0))
        safe(lambda: app.Quit(0))


# ---------------------------------------------------------------- PowerPoint

def shape_texts(shapes, depth=0):
    """도형 텍스트를 위→아래, 왼→오른쪽(Top 10pt 단위)으로 모은다. 표·그룹·SmartArt 포함.
    COM 은 z-order 로 열거하므로 그대로 뽑으면 구성도가 뒤죽박죽이 된다."""
    out = []
    if depth > 6:
        return out
    items = [s for s in shapes]
    items.sort(key=lambda s: (round(safe(lambda: float(s.Top), 99999.0) / 10.0), safe(lambda: float(s.Left), 99999.0)))
    for shp in items:
        if safe(lambda: int(shp.Type), 0) == 6:              # msoGroup
            out += safe(lambda: shape_texts(shp.GroupItems, depth + 1), [])
            continue
        if safe(lambda: shp.HasTable, 0) == -1:
            tbl = shp.Table
            for r in range(1, int(tbl.Rows.Count) + 1):
                cells = []
                for c in range(1, int(tbl.Columns.Count) + 1):
                    ct = safe(lambda: str(tbl.Cell(r, c).Shape.TextFrame.TextRange.Text), "")
                    cells.append(" ".join(ct.replace("\r", " ").replace("\x0b", " ").split()))
                out.append("| " + " | ".join(cells) + " |")
            continue
        if safe(lambda: shp.HasSmartArt, 0) == -1:
            for node in safe(lambda: list(shp.SmartArt.AllNodes), []):
                nt = safe(lambda: str(node.TextFrame2.TextRange.Text), "").strip()
                if nt:
                    out.append(nt)
            continue
        if safe(lambda: shp.HasTextFrame == -1 and shp.TextFrame.HasText == -1, False):
            out.append(safe(lambda: str(shp.TextFrame.TextRange.Text), ""))
    return out


def read_powerpoint(create, path, keys, opt, out, dump):
    app = create("PowerPoint.Application")
    safe(lambda: setattr(app, "AutomationSecurity", 3))
    safe(lambda: setattr(app, "DisplayAlerts", 1))      # ppAlertsNone
    pres = None
    try:
        pres = app.Presentations.Open(path, -1, 0, 0)       # ReadOnly, Untitled, WithWindow=False
        n = int(pres.Slides.Count)
        out("=== SLIDES ===")
        out("  슬라이드 %d개" % n)
        out()
        for i in range(1, n + 1):
            slide = pres.Slides(i)
            texts = [t.replace("\r", "\n").replace("\x0b", "\n") for t in safe(lambda: shape_texts(slide.Shapes), [])]
            texts = [t for t in texts if t.strip()]
            notes = []
            for ns in safe(lambda: list(slide.NotesPage.Shapes), []):
                if safe(lambda: ns.HasTextFrame == -1 and ns.TextFrame.HasText == -1, False):
                    nt = safe(lambda: str(ns.TextFrame.TextRange.Text), "")
                    if nt.strip():
                        notes.append(nt.replace("\r", "\n").replace("\x0b", "\n"))
            title = " ".join(texts[0].split())[:80] if texts else ""
            if not keys:
                out("  %3d. %s   (텍스트 %d블록%s)" % (i, title, len(texts), (", 노트 %d" % len(notes)) if notes else ""))
            else:
                for t in texts:
                    hit(out, t, "슬라이드 %d" % i, keys)
                for t in notes:
                    hit(out, t, "슬라이드 %d 노트" % i, keys)
            if dump is not None:
                dump.append("## 슬라이드 %d\n" % i)
                dump.extend(t.strip() for t in texts)
                if notes:
                    dump.append("\n### 발표자 노트\n")
                    dump.extend(t.strip() for t in notes)
                dump.append("")
    finally:
        if pres is not None:
            safe(lambda: pres.Close())
        safe(lambda: app.Quit())


# ---------------------------------------------------------------- main

def main(argv=None, create=None):
    ap = argparse.ArgumentParser(description="DRM MS Office 문서 COM 판독 (pywin32)")
    ap.add_argument("path")
    ap.add_argument("--pattern", help="쉼표 구분 키워드 (대소문자 무시)")
    ap.add_argument("--sheet", help="Excel: 이름 일부, 맞는 이름이 없으면 순번")
    ap.add_argument("--fill-merged", action="store_true", help="Excel: 병합 영역의 좌상단 값으로 채움 (느릴 수 있음)")
    ap.add_argument("--preview", type=int, default=5)
    ap.add_argument("--max-rows", type=int, default=5000)
    ap.add_argument("--max-cols", type=int, default=200)
    ap.add_argument("--log", help="화면 출력을 UTF-8 .md 로도 남긴다")
    ap.add_argument("--dump", help="문서 전문을 .md 로 남긴다 (평문 사본이 생긴다)")
    opt = ap.parse_args(argv)
    # 콘솔이 cp949 라도 표현 못 하는 글자(–, NBSP, 기호) 때문에 실행이 죽지 않게 한다
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass

    if not os.path.exists(opt.path):
        print("NOT FOUND: %s" % opt.path)
        return 1
    full = os.path.abspath(opt.path)
    ext = os.path.splitext(full)[1].lower()
    out = Out(opt.log)
    try:
        out("source : %s" % full)
        keys = [k.strip() for k in (opt.pattern or "").split(",") if k.strip()]
        if keys:
            out("pattern: %s" % ", ".join(keys))
        out()

        if ext in EXCEL_EXT:
            reader = read_excel
        elif ext in WORD_EXT:
            reader = read_word
        elif ext in PPT_EXT:
            reader = read_powerpoint
        else:
            out("중단: 지원하지 않는 확장자: %s — probe_format.py 로 실제 포맷을 먼저 확인한다." % ext)
            return 1
        if reader is read_powerpoint and powerpoint_window_open():
            out("중단: PowerPoint 창이 열려 있다. 열린 프레젠테이션을 저장하고 PowerPoint 를 닫은 뒤 다시 실행한다.")
            return 1

        if create is None:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                out("FAILED: pywin32 가 없다 — python -m pip install pywin32")
                return 3
            create = com_create

        dump = [] if opt.dump else None
        try:
            reader(create, full, keys, opt, out, dump)
        except Exception as e:
            out("FAILED: %s" % com_error_text(e))
            out("허용 앱이 아니거나, 열람 권한이 없거나, 파일이 손상됐을 수 있다 (탐색기에서 직접 열어 구분한다).")
            out("DRM 우회는 시도하지 않는다.")
            return 1

        if keys:
            out("\n총 %d 건 매칭" % out.hits)
        if dump is not None:
            with open(opt.dump, "w", encoding="utf-8") as f:
                f.write("# %s\n\n> DRM 원본에서 추출한 평문 사본이다. 분석이 끝나면 삭제한다.\n\n" % os.path.basename(full))
                f.write("\n".join(dump) + "\n")
            out("평문 덤프: %s" % os.path.abspath(opt.dump))
        out("DONE")
        return 0
    finally:
        out.close()


if __name__ == "__main__":
    sys.exit(main())
