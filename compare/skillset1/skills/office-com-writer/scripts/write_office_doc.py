#!/usr/bin/env python3
"""DRM(DocuRay 등) 환경에서 MS Office 문서를 허용 앱 COM(pywin32)으로 쓰고 고친다.

파이썬 라이브러리는 DRM 문서를 열지 못하고, 파이썬이 만든 파일은 보호가 걸려 있지 않다.
Excel/Word/PowerPoint 에게 저장을 시켜 그 두 문제를 해결한다.

    python write_office_doc.py --mode protect <파일> [--out 출력] [--overwrite] [--no-backup] [--log 결과.md]
    python write_office_doc.py --mode replace <파일> --map 치환표.md [--out 출력] …
    python write_office_doc.py --mode fill    <파일.xlsx> --data 데이터.md [--sheet 이름] [--cell B3] [--no-header] …

치환표(--map)는 UTF-8 JSON 본문, 데이터(--data)는 머리글 행이 있는 CSV 본문이다. 확장자는 보지 않는다.

쓰기는 되돌릴 수 없다. 그래서
  - 원본을 덮어쓰지 않는다. --out 이 없으면 <원본>_out.<확장자> 를 만든다
  - --overwrite 는 명시해야 하고, 그때도 .bak 을 먼저 만든다 (--no-backup 은 일회용 사본에만)
  - 문서가 열려 있으면(~$ 잠금 파일) 또는 PowerPoint 창이 떠 있으면 시작하지 않는다
  - 저장 후 선두 바이트로 DocuRay 보호 여부를 판정한다

종료코드: 0 저장·보호 확인 / 1 실패·중단 / 3 저장은 됐으나 보호 확인 실패, 또는 pywin32 없음
"""
import argparse
import csv
import html
import io
import json
import os
import re
import shutil
import sys

EXCEL_EXT = {".xlsx", ".xlsm", ".xlsb", ".xls", ".xltx", ".xltm"}
WORD_EXT = {".docx", ".docm", ".doc", ".dotx", ".dotm", ".rtf"}
PPT_EXT = {".pptx", ".pptm", ".ppt", ".potx"}
# 열기암호 파일은 암호 대화상자로 헤드리스 실행을 멈춘다. 가짜 암호를 주면 대화상자 대신 오류가 난다 (암호 없는 파일엔 무시됨)
DUMMY_PW = "__drmHWP_no_password__"
# COM 메서드에서 건너뛸 자리. pywin32 동적 디스패치는 이름 인자 사이에 빈 자리가 있으면 그 뒤 인자를 말없이
# 버린다 — Open(…, Password=) 의 암호, Add(After=) 의 After, Find 의 LookAt 등이 그렇게 사라졌다 (F-085).
# 그래서 COM 호출은 자리 인자로만 쓰고 빈 자리에 OMIT 을 넣는다. pythoncom.Empty 는 '생략(기본값)'으로 전달된다.
try:
    import pythoncom as _pythoncom
    OMIT = _pythoncom.Empty
except ImportError:                     # pywin32 없는 환경(가짜 COM 시험)
    OMIT = type("Omit", (), {"__repr__": lambda s: "OMIT"})()

# 출력 확장자 → 저장 형식 코드 (F-004). 고정 코드는 .xlsm 매크로를 버리고 확장자-내용을 어긋나게 했다.
SAVE_FORMAT = {
    "Excel": {".xlsx": 51, ".xlsm": 52, ".xlsb": 50, ".xls": 56, ".xltx": 54, ".xltm": 53},
    "Word": {".docx": 16, ".docm": 13, ".dotx": 14, ".dotm": 15, ".doc": 0, ".rtf": 6},
    "PowerPoint": {".pptx": 24, ".pptm": 25, ".potx": 26, ".ppt": 1},
}
STORY_NAME = {1: "본문", 2: "각주", 3: "미주", 4: "메모", 5: "텍스트 상자", 6: "머리글(짝수)", 7: "머리글",
              8: "바닥글(짝수)", 9: "바닥글", 10: "머리글(첫 쪽)", 11: "바닥글(첫 쪽)"}
NUMBER_RE = re.compile(r"^-?(0|[1-9]\d{0,14})(\.\d+)?$")


class Out:
    def __init__(self, log_path=None):
        self.f = open(log_path, "w", encoding="utf-8-sig") if log_path else None

    def __call__(self, text=""):
        if self.f:                      # 로그를 먼저 쓴다 — 화면 출력이 실패해도 기록은 남는다
            self.f.write(text + "\n")
            self.f.flush()
        print(text)                     # main 에서 stdout 을 errors="replace" 로 바꿔 둔다

    def close(self):
        if self.f:
            self.f.close()


def safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def com_error_text(e):
    """COM 오류 설명을 한 줄로. Office 메시지의 CR 이 콘솔에서 앞 글자를 덮어쓴다 (F-086).
    Excel 은 설명을 HTML 이스케이프해서 준다 — '&lt;Caps Lock&gt;' (F-088)."""
    try:
        info = e.args[2]
        text = info[2] if info and info[2] else e.args[1]
    except Exception:
        text = e
    return " ".join(html.unescape(str(text)).split())


# ---------------------------------------------------------------- 순수 로직 (COM 없이 시험 가능)

def save_format(app, out_path):
    ext = os.path.splitext(out_path)[1].lower()
    code = SAVE_FORMAT[app].get(ext)
    if code is None:
        raise ValueError("%s 로 저장할 수 없는 출력 확장자: %s" % (app, ext))
    return code


def cell_input(text):
    """CSV 문자열 → Excel 에 넣을 값. Excel 은 대입된 문자열을 입력처럼 해석해 "001"→1,
    "1-2"→날짜로 바꾼다 (F-009). 평범한 10진수만 숫자로, 나머지는 ' 접두 텍스트로."""
    if text is None or text == "":
        return None
    if NUMBER_RE.match(text):
        return float(text)
    return "'" + text


def load_grid(data_path, no_header):
    with open(data_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(io.StringIO(f.read())))
    rows = [r for r in rows if any(x != "" for x in r)]
    if len(rows) < 2:
        raise ValueError("데이터에 머리글 아래 데이터 행이 없다")
    width = len(rows[0])
    if no_header:
        rows = rows[1:]
    return [[cell_input(r[c] if c < len(r) else "") for c in range(width)] for r in rows]


def load_map(map_path):
    with open(map_path, encoding="utf-8-sig") as f:
        m = json.load(f)
    if not isinstance(m, dict) or not m:
        raise ValueError("치환표가 비어 있거나 JSON 객체가 아니다")
    return {str(k): str(v) for k, v in m.items()}


def protection_verdict(path):
    """저장 결과의 선두 바이트로 판정 (F-007). python.exe 는 DocuRay 허용 앱이 아니어서 암호문을 읽는다."""
    with open(path, "rb") as f:
        head = f.read(16)
    if head.startswith(b"BMS DocuRay"):
        return "protected"
    if head.startswith(b"PK\x03\x04"):
        return "plain"
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        return "ole2"
    return "unknown"


def lock_file_exists(full):
    d, name = os.path.split(full)
    # Office 잠금 파일은 이름 앞 0~2글자를 ~$ 로 바꾼다 (Word 는 이름 길이에 따라 1글자만 바꾸기도 한다)
    return any(os.path.exists(os.path.join(d, c)) for c in ("~$" + name, "~$" + name[1:], "~$" + name[2:]))


# ---------------------------------------------------------------- Excel

def find_cells(ws, key):
    """시트에서 key 를 포함한 셀의 (행, 열) 목록. Excel Find 로 찾으므로 큰 시트도 전부 읽지 않는다."""
    what = re.sub(r"([~*?])", r"~\1", key)      # Find 의 와일드카드를 글자로
    # What, After(생략), LookIn=xlFormulas, LookAt=xlPart, SearchOrder=xlByRows, SearchDirection=xlNext, MatchCase.
    # 이름 인자로 쓰면 빈 After 자리 뒤가 버려져 Excel 이 직전 검색 설정을 쓴다 (F-085)
    first = ws.Cells.Find(what, OMIT, -4123, 2, 1, 1, False)
    found, seen, cur = [], set(), first
    while cur is not None and len(found) < 100000:
        addr = str(cur.Address)
        if addr in seen:                         # FindNext 는 처음 셀로 돌아오면 끝
            break
        seen.add(addr)
        found.append((int(cur.Row), int(cur.Column)))
        cur = ws.Cells.FindNext(cur)
    return found


def excel_replace_key(ws, key, val, out):
    """시트의 key 를 val 로 바꾸고 바꾼 셀 수를 돌려준다.
    Range.Replace 는 바뀐 셀을 키보드 입력처럼 다시 해석해 "001"→1, "3-4"→날짜로 바꾸고(F-048),
    255자를 넘는 값은 실패한다. 그래서 셀 텍스트를 읽어 파이썬에서 바꾸고, 수식이면 Formula 로,
    아니면 Fill 과 같은 규칙(cell_input, 텍스트 서식이면 ' 생략)으로 써넣는다."""
    cells = find_cells(ws, key)
    if not cells:
        return 0
    pat = re.compile(re.escape(key), re.I)
    failed = 0
    for r, c in cells:
        cell = ws.Cells(r, c)
        try:
            text = str(cell.Formula)
            new = pat.sub(lambda m: val, text)
            if new == text:
                continue
            if new.startswith("="):
                cell.Formula = new
            else:
                v = cell_input(new)
                if isinstance(v, str) and safe(lambda: cell.NumberFormat == "@", False):
                    v = v[1:]
                cell.Value2 = v
        except Exception:
            failed += 1                          # 보호된 시트 등
    after = len(find_cells(ws, key))
    rest = " — %d개 남음 (보호된 시트이거나 값에 키가 들어 있다)" % after if after else ""
    out("  %s: '%s' 포함 셀 %d개 → %d개%s" % (ws.Name, key, len(cells), after, rest))
    return len(cells) - after


def strip_prefix_for_text_cells(target, grid):
    """텍스트(@) 서식 셀은 ' 를 글자로 저장한다. 그 셀에 들어갈 값에서만 ' 를 뗀다 (F-038).
    서식은 열 단위로 묻고, 열 안에 서식이 섞였을 때(None)만 셀 단위로 묻는다."""
    for c in range(len(grid[0])):
        col_fmt = safe(lambda: target.Columns(c + 1).NumberFormat)
        for r in range(len(grid)):
            v = grid[r][c]
            if not (isinstance(v, str) and v.startswith("'")):
                continue
            if isinstance(col_fmt, str):
                is_text = col_fmt == "@"
            else:
                is_text = safe(lambda: target.Cells(r + 1, c + 1).NumberFormat == "@", False)
            if is_text:
                grid[r][c] = v[1:]


def run_excel(create, full, out_path, opt, out):
    app = create("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.AskToUpdateLinks = False
    app.EnableEvents = False
    safe(lambda: setattr(app, "AutomationSecurity", 3))   # 매크로 강제 차단 (F-020)
    wb = None
    changes = 0
    try:
        # Filename, UpdateLinks=0, ReadOnly=False, Format(생략), Password — 자리 인자로 (F-085)
        wb = app.Workbooks.Open(full, 0, False, OMIT, DUMMY_PW)
        if opt.mode == "replace":
            mp = load_map(opt.map)
            for i in range(1, wb.Worksheets.Count + 1):
                ws = wb.Worksheets(i)
                for key, val in mp.items():
                    changes += excel_replace_key(ws, key, val, out)
            out("  치환 적용: 셀 %d 개" % changes)
        elif opt.mode == "fill":
            grid = load_grid(opt.data, opt.no_header)
            rows, cols = len(grid), len(grid[0])
            ws = None
            if opt.sheet:
                for i in range(1, wb.Worksheets.Count + 1):
                    if str(wb.Worksheets(i).Name).lower() == opt.sheet.lower():   # Excel 시트 이름은 대소문자 무시
                        ws = wb.Worksheets(i)
                        break
                if ws is None:
                    # 새 시트는 맨 뒤에 둔다 (F-009). Add(After=…) 는 빈 Before 자리 뒤 인자가 버려져(F-085)
                    # 활성 시트 앞(맨 앞)에 생겼다 (F-060, P-014 V8r). 그래서 Add() 뒤에 기존 시트를 원래 순서대로
                    # 새 시트 앞으로 옮긴다 — Move 의 첫 인자(Before)만 쓴다. 실측 통과(P-015 F1·F2)한 방식이라 유지한다.
                    originals = [wb.Worksheets(i) for i in range(1, wb.Worksheets.Count + 1)]
                    ws = wb.Worksheets.Add()
                    ws.Name = opt.sheet
                    for sh in originals:
                        safe(lambda: sh.Move(ws))
                    pos, total = int(ws.Index), int(wb.Worksheets.Count)
                    if pos == total:
                        out("  시트 생성(맨 뒤): %s" % opt.sheet)
                    else:
                        out("  ! 시트 생성: %s — 맨 뒤로 옮기지 못했다 (위치 %d/%d)" % (opt.sheet, pos, total))
            else:
                ws = wb.Worksheets(1)
            start = ws.Range(opt.cell)
            r1, c1 = int(start.Row), int(start.Column)
            target = ws.Range(ws.Cells(r1, c1), ws.Cells(r1 + rows - 1, c1 + cols - 1))
            strip_prefix_for_text_cells(target, grid)
            target.Value2 = tuple(tuple(r) for r in grid)   # 한 번에 대입 (셀별 COM 왕복 방지)
            out("  기록: %s!%s 에 %d행 x %d열%s" % (ws.Name, opt.cell, rows, cols, " (머리글 행 제외)" if opt.no_header else ""))
        wb.SaveAs(out_path, save_format("Excel", out_path))
    finally:
        if wb is not None:
            safe(lambda: wb.Close(False))
        safe(lambda: app.Quit())


# ---------------------------------------------------------------- Word

def word_replace_all(rng, find, value):
    """rng 안의 find 를 전부 value 로 바꾸고 횟수를 돌려준다.
    Find.Execute 의 ReplaceWith 는 255자 제한이라 긴 값이면 실행 전체가 실패했다 (F-003).
    위치만 Find 로 찾고 글자는 Range.Text 에 직접 넣는다."""
    f = rng.Find
    f.ClearFormatting()
    f.Text = find
    f.Forward = True
    f.Wrap = 0              # wdFindStop
    f.Format = False
    f.MatchCase = False
    f.MatchWholeWord = False
    f.MatchWildcards = False
    f.MatchSoundsLike = False
    f.MatchAllWordForms = False
    n = 0
    while n < 10000 and f.Execute():
        rng.Text = value    # 찾으면 rng 가 찾은 글자로 좁혀진다. 넣은 뒤엔 넣은 글자를 덮는다
        n += 1
        rng.Collapse(0)     # wdCollapseEnd — 넣은 글자 뒤에서 이어 찾는다 (값에 키가 있어도 무한반복 없음)
    return n


def run_word(create, full, out_path, opt, out):
    app = create("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    safe(lambda: setattr(app, "AutomationSecurity", 3))
    doc = None
    changes = 0
    try:
        # FileName, ConfirmConversions, ReadOnly, AddToRecentFiles, PasswordDocument (F-085)
        doc = app.Documents.Open(full, False, False, False, DUMMY_PW)
        if opt.mode == "replace":
            mp = load_map(opt.map)
            # 첫 구역 머리글·바닥글이 비면 StoryRanges 가 뒤 구역 머리글까지 건너뛴다 (F-036)
            safe(lambda: doc.Sections(1).Headers(1).Range.StoryType)
            safe(lambda: doc.Sections(1).Footers(1).Range.StoryType)
            for key, val in mp.items():
                by_story = {}
                for story in doc.StoryRanges:
                    st = safe(lambda: int(story.StoryType), 0)
                    if st < 1 or st >= 12:
                        continue
                    rng, guard = story, 0
                    while rng is not None and guard < 500:
                        guard += 1
                        n = word_replace_all(rng.Duplicate, key, val)
                        if 6 <= st <= 11:          # 머리글·바닥글 안의 텍스트 상자
                            for shp in safe(lambda: list(rng.ShapeRange), []):
                                if safe(lambda: shp.TextFrame.HasText, 0):
                                    n += word_replace_all(shp.TextFrame.TextRange, key, val)
                        if n:
                            by_story[STORY_NAME[st]] = by_story.get(STORY_NAME[st], 0) + n
                            changes += n
                        rng = safe(lambda: rng.NextStoryRange)
                parts = ", ".join("%s %d" % kv for kv in by_story.items()) or "없음"
                out("  '%s' 치환: %s" % (key, parts))
            out("  치환 적용: %d 건" % changes)
            out("  ! SmartArt 안의 글자는 대상이 아니다. 결과를 읽기 스킬로 검산할 것")
        elif opt.mode == "fill":
            raise ValueError("--mode fill 은 Excel 전용이다. Word 는 replace 를 쓴다.")
        doc.SaveAs2(out_path, save_format("Word", out_path))
    finally:
        if doc is not None:
            safe(lambda: doc.Close(0))
        safe(lambda: app.Quit(0))


# ---------------------------------------------------------------- PowerPoint

def ppt_replace_all(shape, find, value):
    """텍스트 프레임 하나에서 find 를 전부 바꾼다. TextRange.Replace 는 첫 일치만 바꾸므로 (F-002)
    바꾼 글자 바로 뒤부터 남은 범위를 잘라 다시 부른다. 위치는 매번 프레임 전체를 새로 받아 계산한다."""
    value = value.replace("\r\n", "\r")   # PowerPoint 는 문단 끝을 CR 하나로 저장한다 (F-043)
    n, pos = 0, 1
    while n < 10000:
        full = shape.TextFrame.TextRange
        length = int(full.Length)
        if pos > length:
            break
        hit = full.Characters(pos, length - pos + 1).Replace(find, value)
        if hit is None:
            break
        n += 1
        pos = int(hit.Start) + len(value.encode("utf-16-le")) // 2   # PowerPoint 위치는 UTF-16 단위
    return n


def ppt_replace_shapes(shapes, mp, depth=0):
    n = 0
    if depth > 6:
        return n
    for shp in shapes:
        if safe(lambda: int(shp.Type), 0) == 6:          # msoGroup
            n += safe(lambda: ppt_replace_shapes(shp.GroupItems, mp, depth + 1), 0)
            continue
        if safe(lambda: shp.HasTable, 0) == -1:
            tbl = shp.Table
            for r in range(1, int(tbl.Rows.Count) + 1):
                for c in range(1, int(tbl.Columns.Count) + 1):
                    cell_shape = tbl.Cell(r, c).Shape
                    for k, v in mp.items():
                        n += ppt_replace_all(cell_shape, k, v)
            continue
        if safe(lambda: shp.HasTextFrame == -1 and shp.TextFrame.HasText == -1, False):
            for k, v in mp.items():
                n += ppt_replace_all(shp, k, v)
    return n


def run_powerpoint(create, full, out_path, opt, out):
    app = create("PowerPoint.Application")
    safe(lambda: setattr(app, "AutomationSecurity", 3))
    safe(lambda: setattr(app, "DisplayAlerts", 1))      # ppAlertsNone
    pres = None
    try:
        pres = app.Presentations.Open(full, 0, 0, 0)      # ReadOnly=False, Untitled=False, WithWindow=False
        if opt.mode == "replace":
            mp = load_map(opt.map)
            changes = 0
            for i in range(1, int(pres.Slides.Count) + 1):
                changes += ppt_replace_shapes(pres.Slides(i).Shapes, mp)
            out("  치환 적용: %d 건 (표·그룹 포함)" % changes)
            out("  ! SmartArt 안의 글자는 치환되지 않는다")
        elif opt.mode == "fill":
            raise ValueError("--mode fill 은 Excel 전용이다.")
        # SaveCopyAs 는 열린 프레젠테이션의 경로를 바꾸지 않는다. 자기 경로 덮어쓰기도 된다 (F-006 기각)
        pres.SaveCopyAs(out_path, save_format("PowerPoint", out_path))
    finally:
        if pres is not None:
            safe(lambda: pres.Close())
        safe(lambda: app.Quit())


# ---------------------------------------------------------------- main

def powerpoint_window_open():
    """사용자 화면에 PowerPoint 창이 떠 있는가 (F-028, F-046). read_office_doc.py 와 같은 판정."""
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
    import win32com.client
    import win32com.client.dynamic
    app = win32com.client.DispatchEx(progid)
    return win32com.client.dynamic.Dispatch(app._oleobj_)


def main(argv=None, create=None):
    ap = argparse.ArgumentParser(description="DRM MS Office 문서 COM 쓰기 (pywin32)")
    ap.add_argument("path")
    ap.add_argument("--mode", required=True, choices=["protect", "replace", "fill"])
    ap.add_argument("--out")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--no-backup", action="store_true")
    ap.add_argument("--map", help="replace: UTF-8 JSON 치환표 ({\"{{키}}\": \"값\"})")
    ap.add_argument("--data", help="fill: 머리글 행이 있는 CSV")
    ap.add_argument("--sheet")
    ap.add_argument("--cell", default="A1")
    ap.add_argument("--no-header", action="store_true", help="fill: CSV 머리글 행을 쓰지 않는다")
    ap.add_argument("--log")
    opt = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(errors="replace")   # cp949 콘솔에서 –·NBSP 등으로 죽지 않게
    except Exception:
        pass

    if not os.path.exists(opt.path):
        print("NOT FOUND: %s" % opt.path)
        return 1
    full = os.path.abspath(opt.path)
    ext = os.path.splitext(full)[1].lower()
    out = Out(opt.log)
    try:
        out("mode   : %s" % opt.mode)
        out("source : %s" % full)
        if ext in EXCEL_EXT:
            runner = run_excel
        elif ext in WORD_EXT:
            runner = run_word
        elif ext in PPT_EXT:
            runner = run_powerpoint
        else:
            out("중단: 지원하지 않는 확장자: %s" % ext)
            return 1
        if opt.mode == "replace" and not opt.map:
            out("중단: --mode replace 에는 --map 이 필요하다")
            return 1
        if opt.mode == "fill" and not opt.data:
            out("중단: --mode fill 에는 --data 가 필요하다")
            return 1
        if runner is run_powerpoint and powerpoint_window_open():
            out("중단: PowerPoint 창이 열려 있다. 열린 프레젠테이션을 저장하고 PowerPoint 를 닫은 뒤 다시 실행한다.")
            return 1
        if lock_file_exists(full):
            out("중단: 문서가 열려 있다 (~$ 잠금 파일). 문서를 닫고 다시 실행한다.")
            return 1

        # 상대 경로는 현재 폴더 기준 절대 경로로 (F-027)
        if opt.out:
            out_path = os.path.abspath(opt.out)
        elif opt.overwrite:
            out_path = full
        else:
            base, e = os.path.splitext(full)
            out_path = base + "_out" + e
        out("output : %s" % out_path)
        same = os.path.normcase(out_path) == os.path.normcase(full)
        if same and not opt.overwrite:
            out("\n중단: 출력 경로가 원본과 같다. 원본에 반영하려면 --overwrite 를 명시한다.")
            return 1
        if same:
            out("\n*** 원본을 덮어쓴다 ***")
            if opt.no_backup:
                out("  ! --no-backup: 백업 없이 덮어쓴다")
            else:
                bak, i = full + ".bak", 1
                while os.path.exists(bak):
                    bak, i = "%s.%d.bak" % (full, i), i + 1
                shutil.copyfile(full, bak)     # python 은 허용 앱이 아니라 암호문 그대로 복사된다
                out("  백업: %s" % os.path.basename(bak))
        elif os.path.exists(out_path) and not opt.overwrite:
            out("\n중단: 출력 파일이 이미 있다. 다른 --out 을 주거나 --overwrite 를 명시한다.")
            return 1
        out()

        if create is None:
            try:
                import pythoncom
                pythoncom.CoInitialize()
            except ImportError:
                out("FAILED: pywin32 가 없다 — python -m pip install pywin32")
                return 3
            create = com_create
        try:
            runner(create, full, out_path, opt, out)
        except Exception as e:
            out("FAILED: %s" % com_error_text(e))
            out("원본은 변경되지 않았을 가능성이 높다. 덮어쓰기였다면 .bak 을 확인한다.")
            return 1

        if not os.path.exists(out_path):
            out("FAILED: 저장이 끝났다는데 출력 파일이 없다")
            return 1
        out("저장 완료: %s" % out_path)
        verdict = protection_verdict(out_path)
        if verdict == "protected":
            out("보호 확인: [보호됨] DocuRay 컨테이너")
            out("DONE")
            return 0
        out("보호 확인: [평문 !!] 판정=%s — DRM 이 다시 걸리지 않았다." % verdict)
        out("이 파일은 원본과 같은 내용을 담은 무방비 사본일 수 있다. 필요 없으면 삭제하고, 정책을 확인한다.")
        out("DONE (보호 확인 실패, 종료코드 3)")
        return 3
    finally:
        out.close()


if __name__ == "__main__":
    sys.exit(main())
