"""시험용 가짜 한/글 COM 객체 — 한/글 없이 hwpx-drm 의 흐름·판정 논리를 시험한다.

실제 한/글의 동작을 흉내 내지 않는다. 흉내 내는 것은 '호출 계약'(메서드 이름·인자·반환 형태)뿐이다.
호출 기록(self.log)으로 '지원 안 되는 형식을 부르지 않았는지' 같은 계약을 검사한다.
"""
import re
import time
from pathlib import Path

_INST = re.compile(r"^(.*)\{\{(\d+)\}\}$")

DECL16 = '<?xml version="1.0" encoding="UTF-16" standalone="no" ?>'


# 표 서식(P-040) — 실측 G1(P-038 PoC): HwpLineType·HwpLineWidth 값은 이 목록의 차례
LINE_TYPES = ["None", "Solid", "Dash", "Dot", "DashDot", "DashDotDot", "LongDash", "Circle", "DoubleSlim", "SlimThick",
              "ThickSlim", "SlimThickSlim"]
LINE_WIDTHS = ["0.1mm", "0.12mm", "0.15mm", "0.2mm", "0.25mm", "0.3mm", "0.4mm", "0.5mm", "0.6mm", "0.7mm", "1.0mm"]
SUBSETS = {"CellBorderFill": ("FillAttr",), "ShapeObject": ("ShapeTableCell", "ShapeCaption")}   # 형식 래퍼의 하위 집합
#                                                       (실측 G1 · ShapeCaption 은 한컴 포럼·pyhwpx 꼴, 실측 전 U-30)
SIDE_TYPES = ["Left", "Right", "Top", "Bottom"]                 # SideType 값 차례(흉내 — 실제 값은 실측 전, 이름으로만 쓴다)
AUTONUM_TYPES = ["Page", "Footnote", "Endnote", "Figure", "Table", "Equation"]   # AutoNumType 이름(pyhwpx) — 값은 흉내
OBJ_TAGS = ("TABLE", "PICTURE", "LINE", "RECTANGLE", "ELLIPSE", "ARC", "POLYGON", "CURVE", "CONNECTLINE", "CONTAINER",
            "OLE", "TEXTART", "EQUATION")                          # 번호 종류(SHAPEOBJECT NumberingType)가 있는 개체
_NUM_RX = re.compile(r"<(/?)(%s|NEWNUM|AUTONUM|HEADER|FOOTER|MASTERPAGE)\b([^>]*?)(/?)>" % "|".join(OBJ_TAGS))
_SO_RX = re.compile(r'\s*<SHAPEOBJECT\b[^>]*?NumberingType="(\w+)"')


class _HSet:
    def __init__(self, owner):
        self.owner = owner
        self.items = {}

    def SetItem(self, k, v):
        self.items[k] = v
        self.owner.log.append(("SetItem", k))


class _Arr:
    """CreateItemArray 로 만든 배열 항목(HArray) 흉내 — SetItem(i, v) · Item(i)."""

    def __init__(self, n):
        self.values = [0] * n

    def SetItem(self, i, v):
        self.values[i] = v

    def Item(self, i):
        return self.values[i]


class _PS:
    """형식 래퍼. unsettable 에 든 항목은 실제 pywin32 처럼 속성 대입이 거부된다 (F-063)."""

    def __init__(self, owner, unsettable):
        object.__setattr__(self, "HSet", _HSet(owner))
        object.__setattr__(self, "_unsettable", unsettable)
        object.__setattr__(self, "_owner", owner)

    def __setattr__(self, k, v):
        if k in self._unsettable:
            raise AttributeError("Property '<unknown>.%s' can not be set." % k)
        object.__setattr__(self, k, v)

    def CreateItemArray(self, name, n):          # TableCreation ColWidth 등 (P-040 칸 너비)
        if "CreateItemArray" in self._owner.fail_actions:
            raise RuntimeError("fake failure: CreateItemArray")
        arr = _Arr(n)
        object.__setattr__(self, name, arr)
        return arr


class _ParamSets:
    def __init__(self, owner, unsettable):
        object.__setattr__(self, "_owner", owner)
        object.__setattr__(self, "_unsettable", unsettable)

    def __getattr__(self, name):              # HInsertText, HTableCreation, HStyle, HHeaderFooter ...
        if not name.startswith("H"):
            raise AttributeError(name)
        ps = _PS(self._owner, self._unsettable.get(name[1:], ()))
        for sub in SUBSETS.get(name[1:], ()):
            object.__setattr__(ps, sub, _PS(self._owner, ()))
        object.__setattr__(self, name, ps)
        return ps


class _Action:
    def __init__(self, hwp):
        self.h = hwp

    def GetDefault(self, name, hset):
        if name in ("CellBorderFill", "TablePropertyDialog", "TableCreate"):   # 기본값으로(앞 호출 값이 남지 않게)
            self.h._param_default(name)
        self.h.defaults_got.add(name)
        return True

    def Execute(self, name, hset):
        self.h.log.append(("Action", name))
        if name == "TablePropertyDialog":      # 표/개체 속성은 GetDefault(지금 개체 값) 없이 Execute 하면 기본값으로 덮을 수
            if name not in self.h.defaults_got:   # 있다(실측 전) — 작성기는 늘 GetDefault 먼저(검토 P-049 D1-③-06)
                raise RuntimeError("fake: Execute %s without GetDefault" % name)
            self.h.defaults_got.discard(name)
        if name in self.h.fail_actions:
            return False
        ps = self.h.HParameterSet
        if self.h.caption is not None:                                      # 캡션 안 (P-049 캡션 넣기)
            return self.h._caption_action(name, ps)
        if name == "NewNumber" and self.h.hwpml is not None:                # 새 번호로 시작 (P-050)
            if self.h.cell is not None:
                raise RuntimeError("fake: NewNumber inside a table cell")
            if "NewNumber" not in self.h.defaults_got:
                raise RuntimeError("fake: Execute NewNumber without GetDefault")
            self.h.defaults_got.discard("NewNumber")
            return self.h._new_number(ps.HAutoNum)
        if self.h.cell is not None and name in ("InsertText", "Style"):     # 표 칸 안 (P-027 작성기)
            return self.h._cell_action(name, ps)
        if self.h.cell is not None and name == "CellBorderFill":            # 칸 테두리/배경 (P-040 표 서식)
            return self.h._cell_border_fill(ps.HCellBorderFill)
        if self.h.cell is not None and name == "TablePropertyDialog":       # 표/셀 속성 (P-040 표 서식)
            return self.h._table_property(ps.HShapeObject)
        if name == "RepeatFind":                                            # 다시 찾기 (P-037 자리별 값)
            return self.h._repeat_find(ps.HFindReplace.FindString)
        if name == "InsertText" and self.h.find_at is not None:             # 찾아 지운 자리에 넣기 (P-037)
            self.h.inserted.append(ps.HInsertText.Text)
            return self.h._find_insert(ps.HInsertText.Text)
        if name == "TableCreate" and self.h.hwpml is not None:
            tc = ps.HTableCreation
            arr = getattr(tc, "ColWidth", None)
            if getattr(tc, "WidthType", 0) == 2 and isinstance(arr, _Arr):     # 칸 너비를 정해 만들기 (P-040)
                self.h.create_widths = self.h._colwidth_cells(arr.values, getattr(tc, "WidthValue", 0))
                self.h.log.append(("TableCreateWidth", getattr(tc, "WidthValue", None), list(arr.values)))
            return self.h._table_create(tc.Rows, tc.Cols)
        if name == "InsertText" and self.h.hwpml is not None and self.h.cpos is not None:
            self.h.inserted.append(ps.HInsertText.Text)    # 캐럿 문단 안에 끼운다 (P-025 캐럿 편집)
            self.h._insert_chars(ps.HInsertText.Text)
        elif name == "InsertText":
            self.h.texts.append(ps.HInsertText.Text)
            self.h.inserted.append(ps.HInsertText.Text)    # Clear 로 지워지지 않는 기록
        elif name == "Style":
            return self.h._apply_style(ps.HStyle.Apply)
        elif name == "CharShape" and self.h.hwpml is not None:              # 글자 크기만 (P-031 본문 글자 크기)
            return self.h._char_height(ps.HCharShape.Height)
        elif name == "StyleDelete" and self.h.hwpml is not None:            # 스타일 지우기 (P-033 PoC 흉내)
            return self.h._style_delete(ps.HStyleDelete.Target, ps.HStyleDelete.Alternation)
        elif name == "ParagraphShape" and self.h.hwpml is not None:         # 개요 수준 (P-031 제목 수준 고치기)
            return self.h._para_level(getattr(ps.HParaShape, "HeadingType", None), getattr(ps.HParaShape, "Level", None))
        elif name == "InsertFile":
            f = ps.HInsertFile
            return self.h._insert_file(f.FileName, getattr(f, "KeepStyle", 1))
        elif name == "AllReplace":
            f, r = ps.HFindReplace.FindString, ps.HFindReplace.ReplaceString
            self.h.texts = [t.replace(f, r) for t in self.h.texts]
            if self.h.hwpml is not None:
                self.h.hwpml = self.h.hwpml.replace(f, r)
        return True


class _GenSet:
    """CreateAction(...).CreateSet() 흉내 — 항목과 하위 집합(CreateItemSet/Item)."""

    def __init__(self, owner, setid=None):
        self.owner, self.setid, self.items = owner, setid, {}

    def SetItem(self, k, v):
        self.items[k] = v
        self.owner.log.append(("GenSetItem", self.setid, k, v))

    def Item(self, k):
        return self.items.get(k)

    def ItemExist(self, k):
        return k in self.items

    def CreateItemSet(self, k, setid):
        self.items.setdefault(k, _GenSet(self.owner, setid))
        return self.items[k]


class _GenAction:
    """hwp.CreateAction(name) 흉내. StyleChangeToCurrentShape 만 뜻이 있다(P-031) — restyle_mode 로 실측 전 가정을 고른다:
    current(GetDefault 가 캐럿 자리 글자 크기를 채움) / style(스타일 자기 크기를 채움 → 하위 집합 Height 를 직접 넣어야 바뀜) /
    nosubset(하위 집합 없음, 바뀌지 않음) / ignore(Execute 가 아무것도 안 함) / collateral(문단 모양도 바뀜 — 음성대조) /
    zero(GetDefault 의 NameLocal 이 '바탕글' — 실측 P-031: 이름을 안 주면 바탕글 정의가 바뀌었다) /
    rename(기본 대상은 바탕글, NameLocal 을 바꾸면 바탕글 이름이 바뀐다 — 음성대조) /
    wrongtarget(NameLocal 을 무시하고 바탕글 정의를 바꾼다 — 음성대조, 실측 P-031 첫 실행과 같은 결과).
    Execute 의 대상 스타일 = NameLocal 이름의 스타일(없으면 캐럿 문단 스타일)."""

    def __init__(self, hwp, name):
        self.h, self.name = hwp, name

    def CreateSet(self):
        return _GenSet(self.h, self.name)

    def GetDefault(self, ps):
        h = self.h
        if self.name != "StyleChangeToCurrentShape" or h.hwpml is None or h.restyle_mode == "nosubset":
            return True
        el = h._para_el(h.caret)
        st = h._head_items(h.hwpml, "STYLE").get(el.get("Style", "0"))
        text = el.find("TEXT")
        cur = h._charshape_attrs(text.get("CharShape", "0") if text is not None else "0").get("Height")
        own = h._charshape_attrs(h._attr(st, "CharShape") or "0").get("Height")
        styles = h._head_items(h.hwpml, "STYLE")
        ps.items["NameLocal"] = (h._attr(styles["0"], "Name") if h.restyle_mode in ("zero", "rename", "wrongtarget")
                                 else h._attr(st, "Name"))
        ps.items["Type"] = 0
        self.default_name = ps.items["NameLocal"]
        ps.CreateItemSet("CharShape", "CharShape").items["Height"] = cur if h.restyle_mode in ("current", "zero") else own
        return True

    def Execute(self, ps):
        h = self.h
        h.log.append(("Action", self.name))
        if self.name != "StyleChangeToCurrentShape" or h.hwpml is None or h.restyle_mode == "ignore":
            return True
        name = ps.Item("NameLocal")
        if h.restyle_mode == "rename" and name != getattr(self, "default_name", name):
            sid = next(k for k, v in h._head_items(h.hwpml, "STYLE").items() if h._attr(v, "Name") == self.default_name)
            h._set_head_attr("STYLE", sid, "Name", name)
            return True
        cs = ps.Item("CharShape")
        if cs is None:
            return True
        if h.restyle_mode == "wrongtarget":                                  # 이름을 무시하고 기본 대상(바탕글)을 바꾸면
            name = self.default_name
        sid = next((k for k, v in h._head_items(h.hwpml, "STYLE").items() if h._attr(v, "Name") == name), None)
        return h._restyle(h.caret, cs.Item("Height"), collateral=h.restyle_mode == "collateral", sid=sid)


class _FakeProps:
    def __init__(self, items):
        self.items = dict(items)

    def Item(self, k):
        return self.items.get(k)

    def SetItem(self, k, v):
        self.items[k] = v


class _FakeCtrl:
    """조판 개체 하나(HeadCtrl 연결 목록의 마디). Properties 로 쪽 번호 위치(DrawPos)를 바꾼다 - 0 이면 '없음'."""

    def __init__(self, owner, para, tag, k):
        self.owner, self.para, self.tag, self.k = owner, para, tag, k
        self.CtrlID = owner.CTRL_IDS[tag]
        self.Next = None

    def GetAnchorPos(self, kind):
        return _FakeProps({"List": 0, "Para": self.para, "Pos": 0})

    @property
    def Properties(self):
        _, c = self.owner._ctrl_el(self)
        a = dict(c.attrib) if c is not None else {}
        if self.tag == "PAGENUM":
            a["DrawPos"] = 0 if a.get("Pos", "None") == "None" else 5
        return _FakeProps(a)

    @Properties.setter
    def Properties(self, ps):
        self.owner.log.append(("SetProperties", self.CtrlID, self.para))
        if "Properties" in self.owner.ignore:              # 음성대조: 속성 대입이 먹지 않은 척
            return
        el, c = self.owner._ctrl_el(self)
        if c is not None and self.tag == "PAGENUM" and ps.items.get("DrawPos") == 0:
            c.set("Pos", "None")
            self.owner._put_para(self.para, el)


class FakeHwp:
    def __init__(self, open_ok=True, slow_export=0, version="13, 0, 0, 3903", module_ok=False,
                 save_head=b"BMS DocuRay\x03\x01\x00\x00\x00", hwpml_body=None, fail_actions=(),
                 unsettable=None, hwpml=None, fields=None, put_broken=False, docs=None):
        self.open_ok, self.slow_export, self.Version, self.module_ok = open_ok, slow_export, version, module_ok
        self.save_head, self.hwpml_body, self.fail_actions = save_head, hwpml_body, set(fail_actions)
        self.hwpml = hwpml                     # 완전한 HWPML 문자열(선언 포함)을 그대로 돌려줄 때
        self.docs = docs or {}                 # 파일 이름 -> HWPML (Open 할 때 바꿔 끼움)
        self.selection = None
        self._on_quit = None
        # 실측: HHeaderFooter 래퍼는 HeaderFooterCtrlType 속성 대입을 거부한다 (F-063)
        self.HParameterSet = _ParamSets(self, {"HeaderFooter": ("HeaderFooterCtrlType",)} if unsettable is None
                                        else unsettable)
        self.HAction = _Action(self)
        self.log, self.texts, self.saved, self.inserted = [], [], {}, []
        self.defaults_got = set()
        self.flist = [list(f) for f in (fields or [])]       # [[이름, 종류, 값], ...]
        self.put_broken = put_broken
        self.quit = False

    # 수명
    restyle_mode = "current"
    defaults_got = None                        # GetDefault 한 동작 이름(Execute 가 지운다) — __init__ 에서 새 집합
    msgbox_mode = 0

    def SetMessageBoxMode(self, mode):
        self.log.append(("SetMessageBoxMode", mode))
        old, self.msgbox_mode = self.msgbox_mode, mode
        return old

    def CreateAction(self, name):
        self.log.append(("CreateAction", name))
        return _GenAction(self, name)

    def RegisterModule(self, a, b):
        self.log.append(("RegisterModule", a, b))
        return self.module_ok

    def Clear(self, opt):
        self.log.append(("Clear", opt))
        self.texts = []
        self.caret, self.cpos, self.selection, self.cell, self.find_at = 0, None, None, None, None
        self.caption = None

    def Quit(self):
        self.log.append(("Quit",))
        self.quit = True
        if self._on_quit:
            self._on_quit()

    # 문서
    def Open(self, path, fmt, arg):
        self.log.append(("Open", Path(path).name, fmt, arg))
        if Path(path).name in self.docs:
            self.hwpml = self.docs[Path(path).name]
        self.caret, self.cpos, self.selection, self.cell, self.find_at = 0, None, None, None, None
        self.caption = None
        return self.open_ok(path, fmt, arg) if callable(self.open_ok) else self.open_ok

    def GetTextFile(self, fmt, opt):
        self.log.append(("GetTextFile", fmt))
        if self.slow_export:
            time.sleep(self.slow_export)
        if fmt == "HWPML2X" and self.hwpml is not None:
            if self.autonum:                   # 표·그림 자동 번호 = 문서 차례로 센 번호(한/글 흉내, P-049)
                self._renumber()
            return self.hwpml
        if fmt == "HWPML2X":
            body = self.hwpml_body if self.hwpml_body is not None else "".join(
                "<P><TEXT><CHAR>%s</CHAR></TEXT></P>" % t for t in self.texts)
            return DECL16 + "<HWPML Version=\"2.8\"><HEAD/><BODY><SECTION>" + body + "</SECTION></BODY></HWPML>"
        if fmt in ("TEXT", "UNICODE"):
            return "\r\n".join(self.texts)
        return ""

    def SaveAs(self, path, fmt, arg):
        self.log.append(("SaveAs", Path(path).name, fmt))
        if Path(path).exists():                # 실제 한/글은 덮어쓰기 확인 대화상자를 띄울 수 있다 - 부르면 안 되는 호출
            self.log.append(("SaveAs-onto-existing", Path(path).name))
            return False
        Path(path).write_bytes(self.save_head + b"\x00" * 64)
        self.saved[str(Path(path))] = fmt
        if self.hwpml is not None:             # 저장한 내용을 기억 - 다시 열기·끼워 넣기(InsertFile)가 이 내용을 본다
            self.docs[Path(path).name] = self.hwpml
        return True

    def Run(self, name):                      # 실제 계약: void (반환값 없음, F-062)
        self.log.append(("Run", name))
        if name in self.fail_actions:
            raise RuntimeError("fake failure: " + name)
        if name in self.ignore:
            return None
        if self.caption is not None:           # 캡션 안 (P-049) — 캡션 끝·나오기(CloseEx)만 흉내. 나오지 않고 다른 동작을 하면
            if name in self._CAPTION_RUNS:     # 오류(작성기가 캡션에서 나오는지 본다 — 실제 한/글의 캡션 안 동작은 실측 전)
                self._CAPTION_RUNS[name](self)
                return None
            raise RuntimeError("fake: Run %s inside a caption" % name)
        if name == "ShapeObjAttachCaption" and self.hwpml is not None:
            self._attach_caption()
            return None
        if name == "MoveSelNextParaBegin" and self.hwpml is not None and (
                (self.selection and self.selection[0] == "tail") or
                (not self.selection and self.end_mark == (self.caret, self.cpos))):
            k = self.selection or ("tail", self.caret, self.caret, False)
            self.selection = ("tail", k[1], k[2] + 1, False)
            return None
        if name == "MoveSelParaEnd" and self.selection and self.selection[0] == "tail":
            self.selection = self.selection[:3] + (True,)
            return None
        if name == "MoveSelNextParaBegin":
            k = self.selection if self.selection and self.selection[0] == "text" else ("text", self.caret, self.caret)
            self.selection = ("text", k[1], k[2] + 1)
            return None
        if name == "MoveSelParaEnd":
            k = self.selection if self.selection and self.selection[0] == "text" else ("text", self.caret, self.caret)
            self.selection = ("text", k[1], k[2])
            return None
        if name == "MoveSelDocEnd":
            self.selection = ("toend", self.caret, self.cpos)
            return None
        if name == "MoveSelParaBegin" and self.hwpml is not None:
            cur = len(self._units(self.caret)) if self.cpos is None else self.cpos
            self.selection, self.cpos = ("chars", self.caret, cur, 0), 0
            return None
        if self.hwpml is not None and self.cell is not None and name in self._CELL_RUNS:
            self._CELL_RUNS[name](self)
            return None
        if name == "MoveDocBegin" and self.hwpml is not None:                # 다시 찾기 흉내의 시작 자리 (P-037)
            self.find_at, self.selection, self.cell = self.hwpml.find("<BODY>"), None, None
            return None
        if self.hwpml is not None and name in self._CARET_RUNS:
            self.cell = None if name == "MoveDocEnd" else self.cell
            self.find_at = None if name == "MoveDocEnd" else self.find_at
            self._CARET_RUNS[name](self)
            return None
        if name == "Delete" and self.selection and self.hwpml is not None:
            sel = self.selection
            if sel[0] == "find":                                            # 다시 찾기로 고른 글자 (P-037)
                self.hwpml = self.hwpml[:sel[1]] + self.hwpml[sel[2]:]
                self.find_at = sel[1]
            elif sel[0] == "tail":                         # 문단 a 끝 → b 끝(True)·처음(False): a 그대로, a+1..b 를 지운다
                self._delete_tail(*sel[1:])                 # (b 처음까지면 b 글자가 a 뒤에 붙는다)
            elif sel[0] == "text":
                self._merge_paras(sel[1], sel[2] + 1, keep_text_from=None)
            elif sel[0] == "toend" and sel[2]:              # 문단 가운데(끝)에서 문서 끝까지: 앞 글자는 남고 뒤 문단은 사라진다
                self._cut_after(sel[1], sel[2])
            elif sel[0] == "toend":
                self._merge_paras(sel[1], None, keep_text_from=None)
            elif sel[0] == "chars":
                a, b = sorted(sel[2:4])
                self._set_units(sel[1], self._units(sel[1])[:a] + self._units(sel[1])[b:])
                self.cpos = a
            else:
                self._delete_paras(*sel)
        self.selection = None
        return None

    ignore = ()
    caret = 0
    find_at = None                             # 다시 찾기 흉내의 캐럿(HWPML 글자 위치). None = 찾기 모드 아님 (P-037)

    def _repeat_find(self, f):
        """다시 찾기(앞으로) 흉내: find_at 뒤 본문에서 f 를 찾아 고른다. 머리말·꼬리말 안은 건너뛴다(실제 찾기 범위 가정).
        못 찾으면 False — 실측 계약은 U-23."""
        from xml.sax.saxutils import escape
        if self.hwpml is None or self.find_at is None:
            return False
        x = escape(f)
        skip = [(m.start(), m.end()) for m in re.finditer(r"<(HEADER|FOOTER)\b.*?</\1>", self.hwpml, re.S)]
        i = self.hwpml.find(x, self.find_at)
        while i >= 0 and any(a <= i < b for a, b in skip):
            i = self.hwpml.find(x, i + 1)
        if i < 0:
            return False
        self.selection, self.find_at = ("find", i, i + len(x)), i + len(x)
        return True

    def _find_insert(self, text):
        from xml.sax.saxutils import escape
        x = escape(text)
        self.hwpml = self.hwpml[:self.find_at] + x + self.hwpml[self.find_at:]
        self.find_at += len(x)
        return True
    cpos = None                                # 캐럿 문단 안 위치(글자·개체 단위). None = 캐럿 편집 전(옛 흐름)

    def MovePos(self, move_id, para, pos):
        self.log.append(("MovePos", move_id) if move_id == 2 else ("MovePos", move_id, para, pos))
        self.selection = None
        if move_id in (0, 2, 3):
            self.cell, self.caption = None, None
        if move_id == 2:
            self.caret, self.cpos = 0, 0
        elif move_id == 3:                     # moveBottomOfFile
            self._run_doc_end()
        elif move_id == 0:
            if para >= len(self._top_paras()):
                return False
            self.caret, self.cpos = para, pos
        elif move_id == 7:                     # moveEndOfPara
            self.cpos = len(self._units(self.caret))
            self.end_mark = (self.caret, self.cpos)    # 문단 끝에서 시작하는 선택(P-052 끼워 넣기 — 실측 PoC I1)
        elif move_id == 6:                     # moveStartOfPara
            self.cpos = 0
        return True

    # -------------------------------------------------------------- 캐럿 편집 흉내 (P-025)
    # 문단 = 단위 열: 글자 하나 = 1, 글자 아닌 개체(구역 정의·머리말·쪽 번호 위치·표 …) 하나 = 1 (실측 전 가정 -
    # 생성기는 개체가 지울 범위에 끼지 않게 피하고, 결과를 HWPML 로 확인한다)

    _CHARMAP = {"TAB": "\t", "LINEBREAK": "\n", "NBSPACE": " ", "FWSPACE": " "}
    CTRL_IDS = {"SECDEF": "secd", "COLDEF": "cold", "PAGENUM": "pgnp", "NEWNUM": "nwno", "PAGEHIDING": "pghd",
                "HEADER": "head", "FOOTER": "foot", "BOOKMARK": "bokm", "TABLE": "tbl"}

    def _para_el(self, i):
        import xml.etree.ElementTree as ET
        s, e = self._top_paras()[i]
        return ET.fromstring(self.hwpml[s:e])

    def _put_para(self, i, el):
        import xml.etree.ElementTree as ET
        s, e = self._top_paras()[i]
        self.hwpml = self.hwpml[:s] + ET.tostring(el, encoding="unicode") + self.hwpml[e:]

    def _units(self, i, el=None):
        el = self._para_el(i) if el is None else el
        out = []
        for t in el.findall("TEXT"):
            for ch in t:
                if ch.tag == "CHAR":
                    out += [("c", c) for c in (ch.text or "")]
                    for sub in ch:                 # 글자 요소(탭 등)는 글자, 그 밖(제목 차례 표시 등)은 개체
                        out.append(("c", self._CHARMAP[sub.tag]) if sub.tag in self._CHARMAP else ("o", sub))
                        out += [("c", c) for c in (sub.tail or "")]
                else:
                    out.append(("o", ch))
        return [u for u in out if u[0] == "o" or u[1]]

    def _rebuilt(self, el, units):
        import xml.etree.ElementTree as ET
        texts = el.findall("TEXT")
        cs = texts[0].get("CharShape", "0") if texts else "0"
        for t in texts:
            el.remove(t)
        t = ET.SubElement(el, "TEXT", {"CharShape": cs})
        run = None
        for kind, v in units:
            if kind == "o":
                v.tail = None                      # 꼬리 글자는 이미 글자 단위로 셌다
                t.append(v)
                run = None
                continue
            if run is None:
                run = ET.SubElement(t, "CHAR")
                run.text = ""
            tag = next((k for k, c in self._CHARMAP.items() if c == v), None)
            if tag:
                sub = ET.SubElement(run, tag)
                sub.tail = ""
            elif len(run):
                run[-1].tail += v
            else:
                run.text += v
        return el

    def _set_units(self, i, units):
        self._put_para(i, self._rebuilt(self._para_el(i), units))

    def _insert_chars(self, text):
        u = self._units(self.caret)
        self._set_units(self.caret, u[:self.cpos] + [("c", c) for c in text] + u[self.cpos:])
        self.cpos += len(text)

    def _cut_after(self, i, cpos):
        """문단 i 의 cpos 뒤와 그 뒤 모든 문단을 지운다(문단 끝에서 문서 끝까지 선택 + Delete)."""
        import xml.etree.ElementTree as ET
        tops = self._top_paras()
        el = self._rebuilt(self._para_el(i), self._units(i)[:cpos])
        self.hwpml = self.hwpml[:tops[i][0]] + ET.tostring(el, encoding="unicode") + self.hwpml[tops[-1][1]:]

    # -------------------------------------------------------------- 표 만들기·칸 이동 흉내 (P-027 작성기)
    # 표를 만들면 캐럿은 첫 칸(실측 전 가정). 칸 이동은 오른쪽·아래·왼쪽, 오른쪽 끝에서 오른쪽 = 다음 줄 첫 칸.
    cell = None                                # {"para": 루트 문단, "k": 문단 안 몇 번째 표, "r", "c", "p": 칸 안 문단}

    def _table_create(self, rows, cols):
        import xml.etree.ElementTree as ET
        el = self._para_el(self.caret)
        u = self._units(self.caret, el)
        cpos = len(u) if self.cpos is None else self.cpos
        tbl = ET.Element("TABLE", {"ColCount": str(cols), "RowCount": str(rows)})
        ET.SubElement(tbl, "INSIDEMARGIN", {"Left": "510", "Right": "510", "Top": "141", "Bottom": "141"})   # 실측 기본값
        widths, self.create_widths = self.create_widths, None
        if not widths or len(widths) != cols:
            widths = [self.table_width // cols] * cols
        for r in range(rows):
            row = ET.SubElement(tbl, "ROW")
            for c in range(cols):
                cell = ET.SubElement(row, "CELL", {"ColAddr": str(c), "RowAddr": str(r), "RowSpan": "1", "ColSpan": "1",
                                                   "Width": str(widths[c])})
                ET.SubElement(ET.SubElement(ET.SubElement(cell, "PARALIST"), "P", {"ParaShape": "0", "Style": "0"}),
                              "TEXT", {"CharShape": "0"})
        k = sum(1 for kind, v in u[:cpos] if kind == "o" and v.tag == "TABLE")
        self._put_para(self.caret, self._rebuilt(el, u[:cpos] + [("o", tbl)] + u[cpos:]))
        self.cell = {"para": self.caret, "k": k, "r": 0, "c": 0, "p": 0}
        if self.after_table_para:              # 실측 F-100: 표 뒤 빈 문단 — 표 문단의 스타일·문단 모양을 잇는다(흉내)
            a = self._para_el(self.caret)
            e = self._top_paras()[self.caret][1]
            self.hwpml = self.hwpml[:e] + '<P ParaShape="%s" Style="%s"><TEXT CharShape="0"/></P>' % (
                a.get("ParaShape", "0"), a.get("Style", "0")) + self.hwpml[e:]
        return True

    after_table_para = False

    def _cell_ps(self, el):
        tables = [v for t in el.findall("TEXT") for v in t if v.tag == "TABLE"]
        tbl = tables[self.cell["k"]]
        cell = tbl.findall("ROW")[self.cell["r"]].findall("CELL")[self.cell["c"]]
        return tbl, cell.find("PARALIST")

    def _cell_action(self, name, ps):
        if self.cell_block and self.strict_block:   # 셀 블록을 풀지 않고 글자·스타일(검토 P-040 12) — 작성기 시험만 켠다
            raise RuntimeError("fake: %s while a cell block is active (Cancel missing)" % name)
        el = self._para_el(self.cell["para"])
        _, plist = self._cell_ps(el)
        p = plist.findall("P")[self.cell["p"]]
        if name == "InsertText":
            self.inserted.append(ps.HInsertText.Text)
            u = self._units(None, p)
            self._rebuilt(p, u + [("c", ch) for ch in ps.HInsertText.Text])
        else:
            st = self._head_items(self.hwpml, "STYLE").get(str(ps.HStyle.Apply))
            if st is None:
                return False
            p.set("Style", str(ps.HStyle.Apply))
            p.set("ParaShape", self._attr(st, "ParaShape") or "0")
        self._put_para(self.cell["para"], el)
        return True

    def _cell_move(self, dr, dc):
        el = self._para_el(self.cell["para"])
        tbl, _ = self._cell_ps(el)
        rows, cols = int(tbl.get("RowCount")), int(tbl.get("ColCount"))
        r, c = self.cell["r"] + dr, self.cell["c"] + dc
        if dc > 0 and c >= cols and r + 1 < rows:
            r, c = r + 1, 0
        if 0 <= r < rows and 0 <= c < cols:
            self.cell.update(r=r, c=c, p=0)

    def _cell_break(self):
        import xml.etree.ElementTree as ET
        el = self._para_el(self.cell["para"])
        _, plist = self._cell_ps(el)
        cur = plist.findall("P")[self.cell["p"]]
        new = ET.Element("P", {k: v for k, v in cur.attrib.items() if k in ("ParaShape", "Style")})
        ET.SubElement(new, "TEXT", {"CharShape": "0"})
        plist.insert(list(plist).index(cur) + 1, new)
        self.cell["p"] += 1
        self._put_para(self.cell["para"], el)

    def _cell_close(self):
        self.caret, self.cell, self.cell_block = self.cell["para"], None, False
        self.cpos = len(self._units(self.caret))

    def _cell_block(self, on):
        self.cell_block = on
        if not on:
            self.selection = None

    def _no_block(fn):
        def run(h):
            if h.cell_block and h.strict_block:  # 셀 블록 중 칸 이동·문단 나누기·표 나가기 — Cancel 빠짐(검토 P-040 12)
                raise RuntimeError("fake: cell move while a cell block is active (Cancel missing)")
            return fn(h)
        return run

    _CELL_RUNS = {"TableRightCell": _no_block(lambda h: h._cell_move(0, 1)),
                  "TableLeftCell": _no_block(lambda h: h._cell_move(0, -1)),
                  "TableLowerCell": _no_block(lambda h: h._cell_move(1, 0)),
                  "TableUpperCell": _no_block(lambda h: h._cell_move(-1, 0)),
                  "BreakPara": _no_block(_cell_break), "CloseEx": _no_block(_cell_close),
                  "TableCellBlock": lambda h: h._cell_block(True), "Cancel": lambda h: h._cell_block(False)}

    # -------------------------------------------------------------- 표 서식 흉내 (P-040) — 실측 PoC P-038 A1~A3
    cell_block = False
    strict_block = False                       # True: 셀 블록 중 글자·스타일·칸 이동은 오류(작성기 표 서식 시험 — Cancel 확인).
    #                                            채취(capture)의 칸 합치기 흐름은 블록을 다른 동작으로 끝내므로 끈다
    table_width = 43370                        # 실측 G1: 본문 폭 표 너비(HWPUNIT)
    create_widths = None                       # TableCreate ColWidth 로 정한 칸 너비(다음 _table_create 가 쓴다)
    # ColWidth 뜻(실측 전 U-26): content = 칸 안 좌우 여백(510+510)을 뺀 값(pyhwpx 와 같은 가정 — 칸 = 값 + 1020) /
    # cell = 칸 너비 그대로 / ignore = 무시하고 같은 너비로
    colwidth_mode = "content"

    def _colwidth_cells(self, values, total):
        if self.colwidth_mode == "ignore":
            return None
        return [int(v) + (1020 if self.colwidth_mode == "content" else 0) for v in values]

    def HwpLineType(self, name):
        return LINE_TYPES.index(name)

    def HwpLineWidth(self, width):
        return LINE_WIDTHS.index(width)

    def BrushType(self, s):
        return 1 if "WinBrush" in s else 0

    def HatchStyle(self, s):
        return -1 if s == "None" else 0

    def RGBColor(self, r, g, b):
        return r | (g << 8) | (b << 16)

    def _param_default(self, name):
        setid = {"CellBorderFill": "CellBorderFill", "TablePropertyDialog": "ShapeObject",
                 "TableCreate": "TableCreation"}[name]
        ps = getattr(self.HParameterSet, "H" + setid)
        for k in [k for k in vars(ps) if k not in ("HSet", "_unsettable", "_owner")]:
            object.__delattr__(ps, k)
        for sub in SUBSETS.get(setid, ()):
            object.__setattr__(ps, sub, _PS(self, ()))
        if setid == "ShapeObject":                # 표 너비 = 지금 표 첫 줄 칸 너비 합(칸 안이면)
            w = self.table_width
            if self.cell is not None:
                tbl, _ = self._cell_el(self._para_el(self.cell["para"]))
                w = sum(int(c.get("Width", 0)) for c in tbl.findall("ROW")[0].findall("CELL"))
            object.__setattr__(ps, "Width", w)

    def _cell_el(self, el):
        tables = [v for t in el.findall("TEXT") for v in t if v.tag == "TABLE"]
        tbl = tables[self.cell["k"]]
        return tbl, tbl.findall("ROW")[self.cell["r"]].findall("CELL")[self.cell["c"]]

    def _add_borderfill(self, inner):
        if "<BORDERFILLLIST" not in self.hwpml:
            self.hwpml = self.hwpml.replace("<MAPPINGTABLE>", "<MAPPINGTABLE><BORDERFILLLIST></BORDERFILLLIST>", 1)
        nid = str(max([int(x) for x in re.findall(r'<BORDERFILL Id="(\d+)"', self.hwpml)] + [0]) + 1)
        self.hwpml = self.hwpml.replace("</BORDERFILLLIST>", '<BORDERFILL Id="%s">%s</BORDERFILL></BORDERFILLLIST>' % (nid, inner), 1)
        return nid

    shared_edges = True                        # 실측 P-045: 칸 테두리를 입히면 맞닿은 변은 이웃 칸 것도 바뀐다(나중에 입힌 칸이 이긴다)
    #                                            — 실측은 위아래 변(표 6·7 머리 줄 아래)만. 좌우 변도 같다는 것은 흉내의 가정

    def _cell_border_fill(self, ps):
        """지금 칸(셀 블록 없이 — 실측 A1)에 테두리 네 변·배경 → 새 BORDERFILL. 대입하지 않은 변은 기본(실선 0.12mm).
        shared_edges: 이웃 칸의 맞닿은 변도 이 칸 값으로(실측 P-045 — 참고본 표 6·7: 둘째 줄 위 0.15mm 가 머리 줄 아래 0.4mm 를 덮음)."""
        g = lambda o, k, d=None: getattr(o, k, d)                          # noqa: E731
        side = {tag: '<%s Type="%s" Width="%s"/>' % (tag, LINE_TYPES[g(ps, "BorderType" + n, 1)],
                                                      LINE_WIDTHS[g(ps, "BorderWidth" + n, 1)])
                for tag, n in (("LEFTBORDER", "Left"), ("RIGHTBORDER", "Right"), ("TOPBORDER", "Top"),
                               ("BOTTOMBORDER", "Bottom"))}
        fa = ps.FillAttr
        fill = ""
        if g(fa, "type", g(fa, "Type", 0)) == 1 and g(fa, "WindowsBrush", 0):
            fill = '<FILLBRUSH><WINDOWBRUSH Alpha="0" FaceColor="%d" HatchColor="%d"/></FILLBRUSH>' % (
                g(fa, "WinBrushFaceColor", 0), g(fa, "WinBrushHatchColor", 0))
        bid = self._add_borderfill("".join(side.values()) + fill)
        el = self._para_el(self.cell["para"])
        tbl, cell = self._cell_el(el)
        cell.set("BorderFill", bid)
        if self.shared_edges:
            self._share_edges(tbl, cell, side)
        self._put_para(self.cell["para"], el)
        return True

    def _share_edges(self, tbl, cell, side):
        r, c = int(cell.get("RowAddr")), int(cell.get("ColAddr"))
        for dr, dc, mine, theirs in ((-1, 0, "TOPBORDER", "BOTTOMBORDER"), (1, 0, "BOTTOMBORDER", "TOPBORDER"),
                                     (0, -1, "LEFTBORDER", "RIGHTBORDER"), (0, 1, "RIGHTBORDER", "LEFTBORDER")):
            nb = next((x for x in tbl.iter("CELL") if x.get("RowAddr") == str(r + dr) and x.get("ColAddr") == str(c + dc)),
                      None)
            if nb is None:
                continue
            m = re.search(r'<BORDERFILL\b[^>]*\bId="%s"[^>]*>(.*?)</BORDERFILL>' % nb.get("BorderFill"), self.hwpml) \
                if nb.get("BorderFill") else None
            inner = m.group(1) if m else "".join('<%s Type="Solid" Width="0.12mm"/>' % t        # TableCreate 기본(실측)
                                                 for t in ("LEFTBORDER", "RIGHTBORDER", "TOPBORDER", "BOTTOMBORDER"))
            inner = re.sub(r"<%s\b[^>]*/>" % theirs, side[mine].replace(mine, theirs, 1), inner, count=1)
            nb.set("BorderFill", self._add_borderfill(inner))

    def _table_property(self, ps):
        """표/셀 속성: 셀 블록이면 칸(제목 셀·너비 — 실측 A3), 아니면 표(안 여백)."""
        import xml.etree.ElementTree as ET
        el = self._para_el(self.cell["para"])
        tbl, cell = self._cell_el(el)
        if self.cell_block:
            tc = ps.ShapeTableCell
            self.log.append(("TableProperty", "cell", sorted(k for k in ("Header", "Width") if hasattr(tc, k))))
            if hasattr(tc, "Header"):
                cell.set("Header", "true" if tc.Header else "false")
            if hasattr(tc, "Width"):
                cell.set("Width", str(int(tc.Width)))
        else:
            self.log.append(("TableProperty", "table", sorted(k for k in vars(ps) if k.startswith("CellMargin"))))
            im = tbl.find("INSIDEMARGIN")
            if im is None:
                im = ET.SubElement(tbl, "INSIDEMARGIN")
            for k in ("Left", "Right", "Top", "Bottom"):
                if hasattr(ps, "CellMargin" + k):
                    im.set(k, str(int(getattr(ps, "CellMargin" + k))))
        self._put_para(self.cell["para"], el)
        return True

    def GetPos(self):
        if self.caption is not None:           # 캡션 목록(흉내 목록 번호 2)
            return (2, 0, self.caption["cpos"])
        return (0 if self.cell is None else 1, self.caret, self.cpos or 0)

    # -------------------------------------------------------------- 캡션 넣기 흉내 (P-049) — 실측 전 U-30
    # 한/글 캡션 꼴은 hwpxlib 시험 파일 SimpleRectangle.hwpx(한/글이 만든 캡션): '그림 ' + 자동 번호 + ' ', 자리 Bottom.
    # HWPML: 개체 > SHAPEOBJECT > CAPTION(Side·FullSize·Width·Gap) > PARALIST > P > TEXT > CHAR·AUTONUM(어휘 채취).
    caption = None                             # 캡션 안 캐럿 {"para": 루트 문단, "u": 개체 단위 번호, "cpos": 캡션 문단 안 위치}
    caption_mode = "ok"                        # ok / notrail(새 캡션 끝에 빈칸 없음) / start(캐럿이 캡션 처음 — 실측 전 가정 대비)
    caption_pick = "both"                      # both: 캐럿 오른쪽 개체, 없으면 왼쪽(pyhwpx 설명) / right: 오른쪽만(음성 대조)
    autonum = True                             # 내보낼 때 표·그림 자동 번호를 문서 차례로 다시 센다

    def SideType(self, name):
        return SIDE_TYPES.index(name)

    def _attach_caption(self):
        """캡션 넣기: 캐럿 오른쪽(caption_pick both 면 없을 때 왼쪽) 표·그림에 캡션을 만들고 캐럿을 캡션 끝으로(start 면 처음).
        이미 캡션이 있으면 그 캡션 처음으로(pyhwpx 설명). 붙일 개체가 없으면 아무것도 하지 않는다(캐럿 그대로)."""
        import xml.etree.ElementTree as ET
        el = self._para_el(self.caret)
        u = self._units(self.caret, el)
        cur = len(u) if self.cpos is None else self.cpos
        sides = (cur, cur - 1) if self.caption_pick == "both" else (cur,)
        k = next((i for i in sides if 0 <= i < len(u) and u[i][0] == "o" and u[i][1].tag in ("TABLE", "PICTURE")), None)
        if k is None:
            return
        obj = u[k][1]
        so = obj.find("SHAPEOBJECT")
        if so is None:
            so = ET.Element("SHAPEOBJECT")
            obj.insert(0, so)
        cap, at_end = so.find("CAPTION"), False
        if cap is None:
            cap = ET.SubElement(so, "CAPTION", {"Side": "Bottom", "FullSize": "false", "Width": "8504", "Gap": "850"})
            t = ET.SubElement(ET.SubElement(ET.SubElement(cap, "PARALIST"), "P", {"ParaShape": "0", "Style": "0"}),
                              "TEXT", {"CharShape": "0"})
            ET.SubElement(t, "CHAR").text = "표 " if obj.tag == "TABLE" else "그림 "
            num = ET.SubElement(t, "AUTONUM", {"Number": "0", "NumberType": "Table" if obj.tag == "TABLE" else "Figure"})
            ET.SubElement(num, "AUTONUMFORMAT", {"Type": "Digit", "SuffixChar": "", "Superscript": "false"})
            if self.caption_mode != "notrail":
                ET.SubElement(t, "CHAR").text = " "
            at_end = self.caption_mode != "start"
        self._set_units(self.caret, u)
        self.caption = {"para": self.caret, "u": k, "cpos": 0}
        if at_end:
            self.caption["cpos"] = len(self._units(None, self._caption_p()[2]))

    def _caption_p(self):
        """(루트 문단 요소, 캡션 CAPTION 요소, 캡션 첫 문단 P) — 캡션 안 캐럿 자리."""
        el = self._para_el(self.caption["para"])
        obj = self._units(None, el)[self.caption["u"]][1]
        cap = obj.find("SHAPEOBJECT/CAPTION")
        return el, cap, cap.find("PARALIST/P")

    def _caption_action(self, name, ps):
        """캡션 안 동작: 글자 넣기(캐럿 자리) · 스타일(캡션 문단 — 문단·글자 모양) · 표/개체 속성(캡션 자리 Side)."""
        el, cap, p = self._caption_p()
        if name == "InsertText":
            self.inserted.append(ps.HInsertText.Text)
            u = self._units(None, p)
            c = self.caption["cpos"]
            self._rebuilt(p, u[:c] + [("c", ch) for ch in ps.HInsertText.Text] + u[c:])
            self.caption["cpos"] = c + len(ps.HInsertText.Text)
        elif name == "Style":
            st = self._head_items(self.hwpml, "STYLE").get(str(ps.HStyle.Apply))
            if st is None:
                return False
            p.set("Style", str(ps.HStyle.Apply))
            p.set("ParaShape", self._attr(st, "ParaShape") or "0")
            if self._attr(st, "CharShape") is not None:
                for tx in p.findall("TEXT"):
                    tx.set("CharShape", self._attr(st, "CharShape"))
        elif name == "TablePropertyDialog":
            side = getattr(ps.HShapeObject.ShapeCaption, "Side", None)
            self.log.append(("CaptionProperty", None if side is None else SIDE_TYPES[side]))
            if side is not None:
                cap.set("Side", SIDE_TYPES[side])
        else:
            raise RuntimeError("fake: Execute %s inside a caption" % name)
        self._put_para(self.caption["para"], el)
        return True

    def _caption_list_end(self):
        self.caption["cpos"] = len(self._units(None, self._caption_p()[2]))

    def _caption_close(self):
        self.caret, self.cpos, self.caption = self.caption["para"], self.caption["u"] + 1, None

    _CAPTION_RUNS = {"MoveListEnd": _caption_list_end, "CloseEx": _caption_close}

    def _renumber(self):
        """자동 번호 흉내 — 실측 P-050(17.sum_step7 PoC C5): 한/글은 캡션과 관계없이 번호 종류가 있는 개체(SHAPEOBJECT
        NumberingType — 없으면 표 Table·수식 Equation·그림과 도형 Figure, None 은 세지 않음)를 문서 차례로 세고(BEGINNUMBER 1),
        새 번호(NEWNUM)는 그 자리 뒤 같은 종류 개체의 번호를 정한다. 캡션 안 AUTONUM 은 그 개체 번호. 머리말·꼬리말·바탕쪽
        안 개체와 묶음(CONTAINER) 안 개체는 세지 않는다 — 묶음은 하나로 센다(실측 전 — 흉내, 검토 P-050 D1-①-04)."""
        nxt, stack, skip, out, last = {}, [], 0, [], 0
        x = self.hwpml
        for m in _NUM_RX.finditer(x):
            close, tag, attrs, single = m.groups()
            if tag in ("HEADER", "FOOTER", "MASTERPAGE"):
                skip += (-1 if close else (0 if single else 1))
            elif tag == "NEWNUM" and not close:
                t, n = re.search(r'NumberType="(\w+)"', attrs), re.search(r'Number="(\d+)"', attrs)
                if t and n and not skip:
                    nxt[t.group(1)] = int(n.group(1))
            elif tag == "AUTONUM" and not close:
                t = re.search(r'NumberType="(\w+)"', attrs)
                if t and stack and stack[-1][1] == t.group(1) and stack[-1][2] is not None:
                    out.append(x[last:m.start()] + re.sub(r'Number="\d+"', 'Number="%d"' % stack[-1][2], m.group(0), count=1))
                    last = m.end()
            elif tag in OBJ_TAGS:
                if close:
                    if stack and stack[-1][0] == tag:
                        stack.pop()
                    continue
                so = _SO_RX.match(x, m.end())
                t = so.group(1) if so else ("Table" if tag == "TABLE" else "Equation" if tag == "EQUATION" else "Figure")
                num = None
                if t != "None" and not skip and not any(o[0] == "CONTAINER" for o in stack):
                    num = nxt.get(t, 1)
                    nxt[t] = num + 1
                if not single:
                    stack.append((tag, t, num))
        self.hwpml = "".join(out) + x[last:]

    newnum_mode = "ok"                         # ok / ignore(새 번호로 시작이 '됐다'고만 하고 조판을 넣지 않음 — 음성 대조)

    def AutoNumType(self, name):
        return AUTONUM_TYPES.index(name)

    def _new_number(self, ps):
        """새 번호로 시작 흉내(P-050): 캐럿 자리에 NEWNUM(Number·NumberType) 조판 하나. 캐럿은 그 뒤."""
        import xml.etree.ElementTree as ET
        t, n = getattr(ps, "NumType", None), getattr(ps, "NewNumber", None)
        if t is None or n is None:
            return False
        self.log.append(("NewNumber", AUTONUM_TYPES[t], int(n)))
        if self.newnum_mode == "ignore":
            return True
        el = ET.Element("NEWNUM", {"Number": str(int(n)), "NumberType": AUTONUM_TYPES[t]})
        u = self._units(self.caret)
        cpos = len(u) if self.cpos is None else self.cpos
        self._set_units(self.caret, u[:cpos] + [("o", el)] + u[cpos:])
        self.cpos = cpos + 1
        return True

    # -------------------------------------------------------------- 쪽 번호 흉내 (P-050 검토 D1-②-01) — 실측 전 U-31
    # 쪽 = 구역마다 새 쪽, 구역 안 최상위 문단 PARAS_PER_PAGE 개마다 한 쪽. 인쇄 쪽 번호 = 그 쪽이나 앞쪽의 마지막 쪽 새 번호
    # (NEWNUM Page) 번호 + 지난 쪽 수, 없으면 쪽 차례 + 1. page_newnum_rule last_on_page: 같은 쪽에서 뒤에 다른 새 번호(종류
    # 무관)가 있으면 그 쪽 새 번호는 듣지 않는다 — pyhwpx new_number 주의 3 을 종류 무관으로 읽은 꼴(음성 대조).
    PARAS_PER_PAGE = 5
    page_newnum_rule = "per_type"              # per_type / last_on_page
    key_indicator_mode = "ok"                  # ok / raise(KeyIndicator 오류)
    doc_info_mode = "ok"                       # ok / raise(XHwpDocuments 오류 — CurrentPrintPage 를 못 읽음)

    def _pages(self):
        """최상위 문단마다 (구역 번호, 쪽 차례 0…)."""
        secs = [m.start() for m in re.finditer(r"<SECTION\b", self.hwpml)]
        out, base, cur, j = [], 0, None, 0
        for s, _ in self._top_paras():
            si = sum(1 for p in secs if p < s) - 1
            if si != cur:
                if cur is not None:
                    base += max(1, -(-j // self.PARAS_PER_PAGE))
                cur, j = si, 0
            out.append((si, base + j // self.PARAS_PER_PAGE))
            j += 1
        return out

    def _print_page(self, i):
        pages, tops, nn = self._pages(), self._top_paras(), []      # nn: (쪽 차례, 문서 자리, 종류, 번호)
        for k, (s, e) in enumerate(tops):
            for m in re.finditer(r"<NEWNUM\b[^>]*>", self.hwpml[s:e]):
                t, n = re.search(r'NumberType="(\w+)"', m.group(0)), re.search(r'Number="(\d+)"', m.group(0))
                nn.append((pages[k][1], s + m.start(), t.group(1) if t else None, int(n.group(1)) if n else 1))
        eff = [z for z in nn if z[2] == "Page" and (self.page_newnum_rule == "per_type"
                                                    or not any(o[0] == z[0] and o[1] > z[1] for o in nn))]
        q = pages[i][1]
        last = max((z for z in eff if z[0] <= q), key=lambda z: z[1], default=None)
        return last[3] + q - last[0] if last else q + 1

    def KeyIndicator(self):
        """상태 표시줄 정보 (succ, seccnt, secno, prnpageno, colno, line, pos, over, ctrlname) — pyhwpx key_indicator 꼴.
        캐럿 최상위 문단의 인쇄 쪽 번호(흉내)."""
        self.log.append(("KeyIndicator",))
        if self.key_indicator_mode == "raise":
            raise RuntimeError("fake: KeyIndicator")
        if self.hwpml is None:
            return (True, 1, 1, 1, 1, 1, 1, False, "")
        pages = self._pages()
        i = min(self.caret or 0, len(pages) - 1)
        return (True, len(re.findall(r"<SECTION\b", self.hwpml)), pages[i][0] + 1, self._print_page(i), 1, 1,
                (self.cpos or 0) + 1, False, "")

    @property
    def XHwpDocuments(self):
        """XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo 흉내 — CurrentPage(쪽 차례, 0부터)·CurrentPrintPage(인쇄 번호),
        캐럿 최상위 문단 기준(pyhwpx current_page·current_printpage 꼴). doc_info_mode raise: XHwpDocuments 부터 오류,
        nopage: CurrentPage 만 오류."""
        from types import SimpleNamespace as NS
        if self.doc_info_mode == "raise":
            raise AttributeError("fake: XHwpDocuments")
        h = self

        class Info:
            @property
            def CurrentPage(self):
                if h.doc_info_mode == "nopage":
                    raise AttributeError("fake: CurrentPage")
                return 0 if h.hwpml is None else h._pages()[min(h.caret or 0, len(h._pages()) - 1)][1]

            @property
            def CurrentPrintPage(self):
                return 1 if h.hwpml is None else h._print_page(min(h.caret or 0, len(h._pages()) - 1))
        return NS(Active_XHwpDocument=NS(XHwpDocumentInfo=Info()))

    picture_mode = "ok"                        # ok / fail(None 반환) / ghost(개체를 돌려주지만 문서에는 안 들어감)

    def InsertPicture(self, path, embedded, sizeoption, reverse, watermark, effect, width, height):
        """그림 넣기 흉내: 캐럿 자리에 PICTURE 개체(크기 mm → HWPUNIT). 캐럿은 그림 뒤."""
        import xml.etree.ElementTree as ET
        self.log.append(("InsertPicture", Path(path).name, sizeoption, width, height))
        if self.picture_mode == "fail" or self.hwpml is None:
            return None
        if self.picture_mode == "ok":
            pic = ET.Element("PICTURE")
            ET.SubElement(pic, "SHAPECOMPONENT", {"CurWidth": str(int(width * 283.465)), "CurHeight": str(int(height * 283.465))})
            u = self._units(self.caret)
            cpos = len(u) if self.cpos is None else self.cpos
            self._set_units(self.caret, u[:cpos] + [("o", pic)] + u[cpos:])
            self.cpos = cpos + 1
        return object()

    def _run_doc_end(self):
        self.caret = len(self._top_paras()) - 1
        self.cpos = len(self._units(self.caret))

    def _run_break(self):
        import xml.etree.ElementTree as ET
        el = self._para_el(self.caret)
        u = self._units(self.caret, el)
        cpos = len(u) if self.cpos is None else self.cpos
        new = ET.Element("P", {k: v for k, v in el.attrib.items() if k in ("ParaShape", "Style")})
        self._rebuilt(new, [x for x in u[cpos:] if x[0] == "c"])
        self._put_para(self.caret, self._rebuilt(el, u[:cpos]))
        e = self._top_paras()[self.caret][1]
        self.hwpml = self.hwpml[:e] + ET.tostring(new, encoding="unicode") + self.hwpml[e:]
        self.caret, self.cpos = self.caret + 1, 0

    def _run_move(self, d, select):
        n = len(self._units(self.caret))
        cur = 0 if self.cpos is None else self.cpos
        if select:
            sel = self.selection if (self.selection and self.selection[0] == "chars"
                                     and self.selection[1] == self.caret) else ("chars", self.caret, cur, cur)
        self.cpos = max(0, min(n, cur + d))
        self.selection = ("chars", self.caret, sel[2], self.cpos) if select else None

    def _run_align(self, align):
        sel = self.selection
        paras = range(sel[1], sel[2] + 1) if sel and sel[0] == "text" else [self.caret]
        for i in paras:
            el = self._para_el(i)
            el.set("ParaShape", self._clone_parashape(el.get("ParaShape", "0"), Align=align))
            self._put_para(i, el)

    def _run_align_right(self):
        self._run_align("Right")

    def _run_cancel(self):
        self.selection = None

    _CARET_RUNS = {"MoveDocEnd": _run_doc_end, "BreakPara": _run_break,
                   "MoveLeft": lambda h: h._run_move(-1, False), "MoveRight": lambda h: h._run_move(1, False),
                   "MoveSelLeft": lambda h: h._run_move(-1, True), "MoveSelRight": lambda h: h._run_move(1, True),
                   "ParagraphShapeAlignRight": _run_align_right, "Cancel": _run_cancel,
                   "ParagraphShapeAlignCenter": lambda h: h._run_align("Center")}       # 표 가운데 정렬(P-041)

    # 머리 정보: 빈 요소와 자식 요소를 가진 실제 HWPML 정의를 함께 처리한다.

    @staticmethod
    def _head_items(x, tag):
        """Id -> exact element XML, including children, without reserializing it."""
        from xml.parsers import expat
        if not x:
            return {}
        start = re.search(r"<HEAD\b", x)
        end = x.find("</HEAD>", start.start()) if start else -1
        source = x[start.start():end + len("</HEAD>")] if start and end >= 0 else x
        source = re.sub(r"^\ufeff?\s*<\?xml.*?\?>", "", source, count=1, flags=re.S)
        data = b"<FAKE_ROOT>" + source.encode("utf-8") + b"</FAKE_ROOT>"
        parser = expat.ParserCreate(encoding="utf-8")
        stack, items = [], {}

        def opened(name, attrs):
            offset = parser.CurrentByteIndex
            opening = re.match(br'''<(?:[^>"']|"[^"]*"|'[^']*')+>''', data[offset:]) if name == tag else None
            empty = bool(opening and opening.group(0).rstrip().endswith(b"/>"))
            stack.append((name, offset, attrs.get("Id"), empty))

        def closed(name):
            opened_name, offset, iid, empty = stack.pop()
            if opened_name == tag and iid is not None:
                stop = parser.CurrentByteIndex
                if not empty:
                    stop = data.index(b">", stop) + 1
                items[iid] = data[offset:stop].decode("utf-8")

        parser.StartElementHandler, parser.EndElementHandler = opened, closed
        parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        try:
            parser.Parse(data, True)
        except expat.ExpatError:
            return {}
        return items

    @staticmethod
    def _head_attrs(el_xml):
        """Opening-element attributes only; nested Type/Level/Id cannot shadow them."""
        import xml.etree.ElementTree as ET
        if not el_xml:
            return {}
        return dict(ET.fromstring(el_xml).attrib)

    @staticmethod
    def _attr(el_xml, k):
        return FakeHwp._head_attrs(el_xml).get(k)

    def _add_head_item(self, tag, attrs, source_xml=None):
        import xml.etree.ElementTree as ET
        items = self._head_items(self.hwpml, tag)
        nid = str(max([int(k) for k in items] + [-1]) + 1)
        node = ET.fromstring(source_xml) if source_xml else ET.Element(tag)
        node.set("Id", nid)
        for key, value in attrs.items():
            if key != "Id":
                node.set(key, str(value))
        xml = ET.tostring(node, encoding="unicode")
        self.hwpml = self.hwpml.replace("</%sLIST>" % tag, xml + "</%sLIST>" % tag, 1)
        return nid

    def _parashape_attrs(self, x, pid):
        el = self._head_items(x, "PARASHAPE").get(pid)
        return self._head_attrs(el)

    def _clone_parashape(self, pid, **change):
        a = self._parashape_attrs(self.hwpml, pid)
        a.update(change)
        return self._add_head_item("PARASHAPE", a, source_xml=self._head_items(self.hwpml, "PARASHAPE").get(str(pid)))

    def _apply_style(self, idx):
        st = self._head_items(self.hwpml, "STYLE").get(str(idx))
        if st is None:
            return False
        sel = self.selection
        paras = range(sel[1], sel[2] + 1) if sel and sel[0] == "text" else [self.caret]
        cs = self._attr(st, "CharShape")
        for i in paras:
            el = self._para_el(i)
            old_level = self._parashape_attrs(self.hwpml, el.get("ParaShape", "0")).get("Level", "0")
            el.set("Style", str(idx))
            el.set("ParaShape", self._attr(st, "ParaShape") or "0")
            if self.style_keeps_level and old_level not in ("0", None):   # 실측 P-031: SDP '바탕글' 문단(수준 값 4)에
                el.set("ParaShape", self._clone_parashape(el.get("ParaShape"), Level=old_level))   # 스타일을 입혀도 수준 유지
            if cs is not None:                     # 스타일 글자 모양 (합성 HWPML 에 CHARSHAPE 가 있을 때, P-031)
                for tx in el.findall("TEXT"):
                    tx.set("CharShape", cs)
            self._put_para(i, el)
        return True

    style_keeps_level = False

    def _style_delete(self, target, alt):
        """스타일 target 을 지우고 그 스타일 최상위 문단을 alt 스타일로(문단·글자 모양도 alt 것). 번호는 다시 매기지 않는다."""
        items = self._head_items(self.hwpml, "STYLE")
        if str(target) not in items or str(alt) not in items or str(target) == "0":
            return False
        for k in range(len(self._top_paras())):
            el = self._para_el(k)
            if el.get("Style") == str(target):
                caret, self.caret, sel, self.selection = self.caret, k, self.selection, None
                self._apply_style(alt)
                self.caret, self.selection = caret, sel
        self.hwpml = self.hwpml.replace(self._head_items(self.hwpml, "STYLE")[str(target)], "", 1)
        return True

    def _para_level(self, heading_type, level):
        """문단 모양 바꾸기(개요 종류·수준만) — 캐럿 문단."""
        el = self._para_el(self.caret)
        change = {}
        if heading_type is not None:
            change["HeadingType"] = {0: "None", 1: "Outline", 2: "Number", 3: "Bullet"}[int(heading_type)]
        if level is not None:
            change["Level"] = str(level)
        el.set("ParaShape", self._clone_parashape(el.get("ParaShape", "0"), **change))
        self._put_para(self.caret, el)
        return True

    def _charshape_attrs(self, cid):
        el = self._head_items(self.hwpml, "CHARSHAPE").get(str(cid))
        return self._head_attrs(el)

    def _clone_charshape(self, cid, **change):
        a = self._charshape_attrs(cid)
        a.update(change)
        return self._add_head_item("CHARSHAPE", a, source_xml=self._head_items(self.hwpml, "CHARSHAPE").get(str(cid)))

    def _set_head_attr(self, tag, iid, k, v):
        import xml.etree.ElementTree as ET
        old = self._head_items(self.hwpml, tag)[str(iid)]
        attrs = self._head_attrs(old)
        attrs[k] = str(v)
        opening = re.match(r'''<(?:[^>"']|"[^"]*"|'[^']*')+>''', old).group(0)
        new_opening = ET.tostring(ET.Element(tag, attrs), encoding="unicode")
        if not opening.rstrip().endswith("/>"):
            new_opening = new_opening.rsplit("/>", 1)[0].rstrip() + ">"
        new = new_opening + old[len(opening):]
        self.hwpml = self.hwpml.replace(old, new, 1)

    def _char_height(self, height):
        """글자 크기 바꾸기: 선택(없으면 캐럿) 문단의 글자 모양을 크기만 바꾼 사본으로 — 문단 일부 선택도 문단 전체로 흉내."""
        sel = self.selection
        paras = [sel[1]] if sel and sel[0] in ("chars", "text") else [self.caret]
        for i in paras:
            el = self._para_el(i)
            for tx in el.findall("TEXT"):
                tx.set("CharShape", self._clone_charshape(tx.get("CharShape", "0"), Height=str(height)))
            self._put_para(i, el)
        return True

    def _restyle(self, i, height, collateral=False, sid=None):
        """스타일 정의 바꾸기: 스타일 sid(없으면 문단 i 의 스타일) 글자 모양을 크기만 바꾼 사본으로, 그 스타일 문단 중 옛 스타일
        글자 모양을 쓰던 글자는 새 모양으로(직접 서식은 그대로). collateral 이면 문단 모양 정렬도 바뀐다(음성대조)."""
        sid = sid if sid is not None else self._para_el(i).get("Style", "0")
        st = self._head_items(self.hwpml, "STYLE")[sid]
        old = self._attr(st, "CharShape") or "0"
        if str(self._charshape_attrs(old).get("Height")) == str(height) and not collateral:
            return True
        new = self._clone_charshape(old, Height=str(height))
        self._set_head_attr("STYLE", sid, "CharShape", new)
        if collateral:
            self._set_head_attr("STYLE", sid, "ParaShape", self._clone_parashape(self._attr(st, "ParaShape") or "0",
                                                                                 Align="Center"))
        for k in range(len(self._top_paras())):
            pel = self._para_el(k)
            if pel.get("Style") == sid and any(tx.get("CharShape") == old for tx in pel.findall("TEXT")):
                for tx in pel.findall("TEXT"):
                    if tx.get("CharShape") == old:
                        tx.set("CharShape", new)
                self._put_para(k, pel)
        return True

    def _insert_file(self, file_name, keep_style):
        """끼워 넣기 흉내: 넣는 파일의 최상위 문단을 캐럿 문단 뒤에 넣는다(첫 문단은 캐럿 문단에 합친다 - 실측 S1: 넣은
        첫 문단의 조판 개체가 캐럿 문단에 붙는다). 스타일은 넣은 문단이 쓰는 것만, 이름이 없는 것만 더한다(같은 이름은 지금
        문서 정의를 쓴다 = KeepStyle 0, 실측 S1). 문단 모양은 넣는 파일 것을 복사한다."""
        import xml.etree.ElementTree as ET
        src = self.docs.get(Path(file_name).name)
        if src is None or self.hwpml is None:
            return False
        sstyles = {k: (self._attr(v, "Name"), self._attr(v, "ParaShape")) for k, v in self._head_items(src, "STYLE").items()}
        paras = []
        for s, e in self._top_paras(src):
            el = ET.fromstring(src[s:e])
            name, sps = sstyles.get(el.get("Style", "0"), ("바탕글", "0"))
            mine = {self._attr(v, "Name"): k for k, v in self._head_items(self.hwpml, "STYLE").items()}
            if name in mine:
                sid = mine[name]
            else:
                attrs = {"Name": name, "ParaShape": self._add_head_item("PARASHAPE", self._parashape_attrs(src, sps),
                            source_xml=self._head_items(src, "PARASHAPE").get(str(sps)))}
                scs = self._attr(self._head_items(src, "STYLE").get(el.get("Style", "0"), ""), "CharShape")
                if scs is not None and "</CHARSHAPELIST>" in self.hwpml:      # 글자 모양도 가져온다 (P-033 본문 씨앗)
                    sc = self._head_items(src, "CHARSHAPE").get(scs)
                    attrs["CharShape"] = self._add_head_item("CHARSHAPE", self._head_attrs(sc), source_xml=sc)
                sid = self._add_head_item("STYLE", attrs)
            el.set("Style", sid)
            pid = el.get("ParaShape", "0")
            el.set("ParaShape", self._add_head_item("PARASHAPE", self._parashape_attrs(src, pid),
                        source_xml=self._head_items(src, "PARASHAPE").get(str(pid))))
            paras.append(el)
        if not paras:
            return True
        cur = self._para_el(self.caret)
        u = self._units(self.caret, cur)
        self._put_para(self.caret, self._rebuilt(cur, u + self._units(None, paras[0])))
        e = self._top_paras()[self.caret][1]
        self.hwpml = self.hwpml[:e] + "".join(ET.tostring(p, encoding="unicode") for p in paras[1:]) + self.hwpml[e:]
        return True

    # 조판 개체 목록 (HeadCtrl → Next), 개요 번호 글자

    @property
    def HeadCtrl(self):
        items = []
        for i in range(len(self._top_paras())):
            seen = {}
            for kind, v in self._units(i):
                if kind == "o" and v.tag in self.CTRL_IDS:
                    items.append(_FakeCtrl(self, i, v.tag, seen.get(v.tag, 0)))
                    seen[v.tag] = seen.get(v.tag, 0) + 1
        for a, b in zip(items, items[1:]):
            a.Next = b
        return items[0] if items else None

    def _ctrl_el(self, ctrl):
        el = self._para_el(ctrl.para)
        found = [v for t in el.findall("TEXT") for v in t if v.tag == ctrl.tag]
        return el, (found[ctrl.k] if ctrl.k < len(found) else None)

    def DeleteCtrl(self, ctrl):
        self.log.append(("DeleteCtrl", ctrl.CtrlID, ctrl.para))
        el, c = self._ctrl_el(ctrl)
        if c is None:
            return False
        for t in el.findall("TEXT"):
            if c in list(t):
                t.remove(c)
        self._put_para(ctrl.para, el)
        return True

    def GetHeadingString(self):
        """캐럿 문단의 개요 번호 글자 - 개요 문단(문단 모양 HeadingType=Outline)을 문서 처음부터 수준별로 센다.
        형식은 '1.2.1.' (실측 전 가정 - 생성기는 숫자만 비교한다)."""
        count = [0] * 7
        for i in range(self.caret + 1):
            a = self._parashape_attrs(self.hwpml, self._para_el(i).get("ParaShape", "0"))
            if a.get("HeadingType") != "Outline":
                if i == self.caret:
                    return ""
                continue
            lvl = int(a.get("Level", "0"))
            count[lvl] += 1
            count[lvl + 1:] = [0] * (6 - lvl)
            if i == self.caret:
                return ".".join(str(n) for n in count[:lvl + 1]) + "."
        return ""

    def SelectText(self, sp, spos, ep, epos):
        self.log.append(("SelectText", sp, spos, ep, epos))
        self.selection = (sp, ep)
        return True

    merge_keeps_first = True                   # 실측 P-022: 블록 삭제 뒤 남는 문단 = 지운 첫 문단의 그릇(스타일·조판 개체)
    #                                            + 끝 문단의 글자. 끝 문단의 조판 개체(머리말 등)는 사라진다 (F-095)

    def _top_paras(self, x=None):
        """모든 구역의 최상위 P 위치 [(시작, 끝)] — 구역을 이어 센 루트 리스트 번호 순 (실측 P-022 확인, U-15)."""
        import re as _re
        out, depth = [], 0
        pat = _re.compile(r"<(/?)(P|SECTION)\b[^>]*?(/?)>")
        for t in pat.finditer(self.hwpml if x is None else x):
            close, tag, selfc = t.groups()
            if tag == "SECTION":
                continue
            if not close and not selfc:
                if depth == 0:
                    out.append([t.start(), None])
                depth += 1
            elif close:
                depth -= 1
                if depth == 0:
                    out[-1][1] = t.end()
            elif selfc and depth == 0:
                out.append([t.start(), t.end()])
        return out

    @staticmethod
    def _survivor(first_xml, text_from_xml):
        """first 문단의 그릇(여는 태그 + CHAR 아닌 조판 개체) + text_from 문단의 CHAR 들."""
        import xml.etree.ElementTree as ET
        f = ET.fromstring(first_xml)
        ft = f.find("TEXT")
        if ft is None:
            ft = ET.SubElement(f, "TEXT", {"CharShape": "0"})
        for ch in [c for c in ft if c.tag == "CHAR"]:
            ft.remove(ch)
        if text_from_xml is not None:
            t = ET.fromstring(text_from_xml).find("TEXT")
            for ch in ([c for c in t if c.tag == "CHAR"] if t is not None else []):
                ft.append(ch)
        return ET.tostring(f, encoding="unicode")

    def _merge_paras(self, sp, ep, keep_text_from=None):
        """루트 문단 sp..(ep-1) 을 sp 의 그릇 하나로 합친다(글자 없음). ep=None 이면 문서 끝까지. 구역 경계 태그도 지운다."""
        tops = self._top_paras()
        end_i = len(tops) if ep is None else ep
        cut = tops[sp:end_i]
        if not cut:
            return
        first = self.hwpml[cut[0][0]:cut[0][1]]
        surv = self._survivor(first, None)
        # 사이의 구역 경계 태그는 범위와 함께 지워져 뒤 구역이 앞 구역에 합쳐진다
        self.hwpml = self.hwpml[:cut[0][0]] + surv + self.hwpml[cut[-1][1]:]

    end_mark = None                            # (문단, 위치) — MovePos moveEndOfPara 로 간 자리. 캐럿이 움직이면 맞지 않는다

    def _delete_tail(self, a, b, to_end):
        """문단 a 끝부터 선택해 지우기(P-052, 실측 PoC I1 — 앞뒤 문단·그림 문단 그릇 그대로): to_end 면 a+1..b 문단이
        통째로 사라지고 a 는 그대로. 아니면(b 처음까지) a+1..b-1 이 사라지고 b 의 단위(글자·개체)가 a 끝에 붙는다."""
        tops = self._top_paras()
        if b >= len(tops) or b <= a:
            raise RuntimeError("fake: 문단 끝 선택 범위 밖 %d..%d" % (a, b))
        if to_end:
            self.hwpml = self.hwpml[:tops[a + 1][0]] + self.hwpml[tops[b][1]:]
        else:
            ub = self._units(b)
            self.hwpml = self.hwpml[:tops[a + 1][0]] + self.hwpml[tops[b][1]:]
            self._set_units(a, self._units(a) + ub)
        self.end_mark = None

    def _delete_paras(self, sp, ep):
        """SelectText(sp,0,ep,0)+Delete 흉내: 루트 문단 [sp, ep) 를 지우고, 남는 문단은 sp 의 그릇 + ep 의 글자
        (merge_keeps_first, 실측 P-022). False 면 ep 문단을 그대로 둔다(옛 가정). 구역 경계를 넘으면 앞 구역에 합친다."""
        tops = self._top_paras()
        cut = tops[sp:ep]
        if not cut:
            return
        if ep < len(tops) and self.merge_keeps_first:
            first = self.hwpml[cut[0][0]:cut[0][1]]
            last = self.hwpml[tops[ep][0]:tops[ep][1]]
            self.hwpml = self.hwpml[:cut[0][0]] + self._survivor(first, last) + self.hwpml[tops[ep][1]:]
            return
        end = tops[ep][0] if ep < len(tops) else cut[-1][1]
        self.hwpml = self.hwpml[:cut[0][0]] + self.hwpml[end:]

    @property
    def PageCount(self):
        if self.hwpml is None:
            return 1
        return max(1, len(self._top_paras()) // 5)

    # 필드 - [이름, 종류, 값] 목록. 같은 이름 여러 개 허용 (매뉴얼: PutFieldText 이름만 주면 모두 채움)
    def CreateField(self, direction, memo, name):
        self.flist.append([name, "clickhere", ""])
        return True

    def SetCurFieldName(self, name, opt, d, m):
        self.flist.append([name, "cell", ""])
        return True

    def _targets(self, n):
        m = _INST.match(n)
        same = [f for f in self.flist if f[0] == (m.group(1) if m else n)]
        if m:
            i = int(m.group(2))
            return same[i:i + 1]
        return same

    def PutFieldText(self, names, values):
        self.log.append(("PutFieldText", names))
        if self.put_broken:                    # 음성대조용: 넣은 척만 한다
            return
        for n, v in zip(names.split("\x02"), values.split("\x02")):
            for f in self._targets(n):         # 없는 이름은 조용히 무시 (C12)
                f[2] = v

    def GetFieldText(self, names):
        out = []
        for n in names.split("\x02"):
            m = _INST.match(n)
            t = self._targets(n) if m else self._targets(n)[:1]
            out.append(t[0][2] if t else "")
        return "\x02".join(out)

    def FieldExist(self, name):
        return bool(self._targets(name))

    def GetFieldList(self, number, option):
        kinds = {0: ("clickhere", "cell"), 1: ("cell",), 2: ("clickhere",), 8: ("textbox",)}[option]
        fs = [f for f in self.flist if f[1] in kinds]
        if number == 1:
            seen, out = {}, []
            for f in fs:
                out.append("%s{{%d}}" % (f[0], seen.get(f[0], 0)))
                seen[f[0]] = seen.get(f[0], 0) + 1
            return "\x02".join(out)
        return "\x02".join(f[0] for f in fs)

    @property
    def fields(self):
        return {f[0]: f[2] for f in self.flist}

    def FindDir(self, name):
        return {"Forward": 0, "Backward": 1, "AllDoc": 2}[name]


class FakeProcs:
    """여러 세션이 함께 쓰는 가짜 프로세스 표.
    Quit 뒤에도 linger 번 조회될 때까지 살아 있다 (실측: Quit 는 비동기 - F-061). linger=None 이면 끝나지 않는다."""

    def __init__(self, linger=0, start_pid=4242, preexisting=()):
        self.alive, self.next, self.linger = set(preexisting), start_pid, linger
        self.quitting, self.killed, self.spawned = {}, [], []

    def env(self, fake):
        def dispatch():
            pid = self.next
            self.next += 1
            self.alive.add(pid)
            self.spawned.append(pid)
            fake._on_quit = lambda: self.quitting.setdefault(pid, 0)
            return fake
        return dispatch, self.pids, self.kill

    def pids(self):
        for pid in list(self.quitting):
            if self.linger is not None and self.quitting[pid] >= self.linger:
                self.alive.discard(pid)
                del self.quitting[pid]
            else:
                self.quitting[pid] += 1
        return set(self.alive)

    def kill(self, pid):
        self.killed.append(pid)
        self.alive.discard(pid)
        self.quitting.pop(pid, None)


def make_env(fake, pids_before=(), new_pid=4242):
    """HwpSession 주입용 (dispatch, pids, killer, killed 기록). Quit 하면 바로 끝나는 단순한 환경."""
    state = {"started": False, "killed": []}

    def dispatch():
        state["started"] = True
        return fake

    def pids():
        base = set(pids_before)
        alive = state["started"] and new_pid and not fake.quit and new_pid not in state["killed"]
        return base | ({new_pid} if alive else set())

    def killer(pid):
        state["killed"].append(pid)
    return dispatch, pids, killer, state


def _p(*inner):
    return "<P ParaShape=\"0\" Style=\"0\"><TEXT CharShape=\"0\">%s</TEXT></P>" % "".join(inner)


def _c(t):
    return "<CHAR>%s</CHAR>" % t


def _cell(r, c, body, rs=1, cs=1, name=None):
    nm = ' Name="%s"' % name if name else ""
    return ('<CELL ColAddr="%d" ColSpan="%d" RowAddr="%d" RowSpan="%d"%s><PARALIST>%s</PARALIST></CELL>'
            % (c, cs, r, rs, nm, body))


def _table(rows, cols, rows_xml):
    return '<TABLE ColCount="%d" RowCount="%d">%s</TABLE>' % (cols, rows, "".join("<ROW>%s</ROW>" % r for r in rows_xml))


# 합성 문서의 '완성형' 최소 HWPML — 실측 픽스처(tests/fixtures/synthetic_hwpml.md)와 같은 요소 배치를 손으로 줄인 것.
# 머리말·꼬리말 배치(첫 문단 TEXT 안)는 실측 전 가정이다 — 재채취 결과로 확인한다.
SYN_FULL_HWPML = (
    DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="1"><MAPPINGTABLE><STYLELIST Count="2">'
    '<STYLE Id="0" Name="바탕글" ParaShape="0"/><STYLE Id="2" Name="개요 1" ParaShape="2"/></STYLELIST>'
    '<PARASHAPELIST><PARASHAPE Id="0" HeadingType="None" Level="0"/><PARASHAPE Id="2" HeadingType="Outline" Level="0"/>'
    '</PARASHAPELIST></MAPPINGTABLE></HEAD><BODY><SECTION Id="0">'
    '<P ParaShape="2" Style="2"><TEXT CharShape="0"><SECDEF/>'
    '<HEADER ApplyPageType="Both"><PARALIST>' + _p(_c("SYN_HEADER")) + '</PARALIST></HEADER>'
    '<FOOTER ApplyPageType="Both"><PARALIST>' + _p(_c("SYN_FOOTER")) + '</PARALIST></FOOTER>'
    '<CHAR>SYN_H1 개요 제목</CHAR></TEXT></P>'
    + _p("<CHAR>SYN_P1 본문 첫 문단<LINEBREAK/>SYN_P1_LINE2<TAB/>SYN_P1_TAB</CHAR>")
    + _p(_c("SYN_P2 누름틀:"),
         '<FIELDBEGIN Command="Clickhere:set:59:Direction:wstring:9:SYN_GUIDE HelpState:wstring:8:SYN_MEMO  " '
         'Name="SYN_FIELD_A" Type="Clickhere"/>', _c("SYN_FIELD_A_VALUE"), '<FIELDEND Type="Clickhere"/>', "<CHAR/>")
    + _p(_c("SYN_P3 각주 기준"), '<FOOTNOTE><PARALIST><P><TEXT><AUTONUM Number="1" NumberType="Footnote"/>'
         + _c("SYN_FOOTNOTE") + '</TEXT></P></PARALIST></FOOTNOTE>')
    + _p(_c("SYN_P4 메모 "), '<FIELDBEGIN Type="Memo"><PARALIST>' + _p(_c("SYN_MEMO_TEXT")) + '</PARALIST></FIELDBEGIN>',
         _c("기준"), '<FIELDEND Type="Memo"/>')
    + _p(_c("SYN_TA 표 A 앞 문단"))
    + _p(_table(3, 3, [
        _cell(0, 0, _p(_c("SYN_A_R0C0"))) + _cell(0, 1, _p(_c("SYN_A_R0C1"))) + _cell(0, 2, _p(_c("SYN_A_R0C2")), name="SYN_CELL_02"),
        _cell(1, 0, _p(_c("SYN_A_R1C0")) + _p(_c("SYN_A_R1C0_P2"))) + _cell(1, 1, _p(_c("SYN_A_R1C1"))) + _cell(1, 2, _p(_c("SYN_A_R1C2"))),
        _cell(2, 0, _p(_c("SYN_A_R2C0")) + _p(_table(1, 2, [_cell(0, 0, _p(_c("SYN_N_R0C0"))) + _cell(0, 1, _p(_c("SYN_N_R0C1")))]), "<CHAR/>") + _p())
        + _cell(2, 1, _p(_c("SYN_A_R2C1"))) + _cell(2, 2, _p(_c("SYN_A_R2C2")))]), "<CHAR/>")
    + _p()
    + _p(_c("SYN_TB 표 B 앞 문단"))
    + _p(_table(3, 3, [
        _cell(0, 0, _p(_c("SYN_B_R0C0")) + _p(_c("SYN_B_R0C1")), cs=2) + _cell(0, 2, _p(_c("SYN_B_R0C2"))),
        _cell(1, 0, _p(_c("SYN_B_R1C0"))) + _cell(1, 1, _p(_c("SYN_B_R1C1"))) + _cell(1, 2, _p(_c("SYN_B_R1C2")) + _p(_c("SYN_B_R2C2")), rs=2),
        _cell(2, 0, _p(_c("SYN_B_R2C0"))) + _cell(2, 1, _p(_c("SYN_B_R2C1")))]), "<CHAR/>")
    + _p()
    + _p(_c("SYN_END 마지막 문단"))
    + "</SECTION></BODY></HWPML>")
