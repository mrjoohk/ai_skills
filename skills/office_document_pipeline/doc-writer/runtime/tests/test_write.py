"""문서 작성기 시험 (가짜 COM, 합성 공통 템플릿) — 한/글 없이 명세 해석·쓰기·확인 판정을 시험한다.

가짜 한/글의 표 만들기·칸 이동은 실측 전 가정(표를 만들면 캐럿은 첫 칸)을 따른다 — 실측(9.sum_step1.bat 시험 쓰기)으로 확인한다.
"""
import contextlib
import os
import io
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "backends" / "hwp" / "tests"))
sys.path.insert(0, str(TOOLS / "hwpx-drm" / "tests"))
import write_doc as wd            # noqa: E402
import hwp_session as hs          # noqa: E402
import hwpx_api as api            # noqa: E402
from fake_hwp import FakeHwp, make_env, DECL16   # noqa: E402

STYLES = ["바탕글", "08_표지_제목", "09_표지_장비명", "03_본문_내용", "04_도표그림_제목", "05_도표내용_항목제목",
          "07_도표내용_본문혼합", "14_도움말_파란색"] + ["COMSAF 개요 %d" % i for i in range(1, 8)] + ["06_도표내용_본문중앙"]


def P(text="", style=0, pre=""):
    return '<P ParaShape="%d" Style="%d"><TEXT CharShape="0">%s<CHAR>%s</CHAR></TEXT></P>' % (
        style - 7 if STYLES[style].startswith("COMSAF") else 0, style, pre, text)


# 본문 구역 쪽 설정(A4, 왼·오 7087, 제본 1417 왼쪽) — '단에 맞춤' 표 너비 59528-7087-7087-1417-567 = 43370 (실측 G1 값, P-040)
SECDEF_BODY = ('<SECDEF><PAGEDEF GutterType="LeftOnly" Height="84188" Landscape="0" Width="59528"><PAGEMARGIN Bottom="4252" '
               'Footer="2835" Gutter="1417" Header="2835" Left="7087" Right="7087" Top="7087"/></PAGEDEF></SECDEF>')


def template_hwpml():
    st = "".join('<STYLE Id="%d" Name="%s" ParaShape="%d"/>' % (i, n, (i - 7) if n.startswith("COMSAF") else 0)
                 for i, n in enumerate(STYLES))
    ps = '<PARASHAPE Id="0" HeadingType="None" Level="0"/>' + "".join(
        '<PARASHAPE Id="%d" HeadingType="Outline" Level="%d"/>' % (k + 1, k) for k in range(7))
    head = '<HEADER ApplyPageType="Both"><PARALIST>%s</PARALIST></HEADER>' % P("{{과제명}} {{문서명}}(v{{버전}})")
    cover = [P("문서번호 : {{문서번호}}", pre="<SECDEF/>" + head), P("{{과제명}}", 2), P("{{문서명}}", 1),
             P("({{문서영문명}})", 1), P("목     차", 1)]
    body = [P("개 요", STYLES.index("COMSAF 개요 1"), pre=SECDEF_BODY)]
    return (DECL16 + '<HWPML Version="2.91"><HEAD SecCnt="2"><MAPPINGTABLE><STYLELIST>%s</STYLELIST>'
            '<PARASHAPELIST>%s</PARASHAPELIST></MAPPINGTABLE></HEAD><BODY><SECTION Id="0">%s</SECTION>'
            '<SECTION Id="1">%s</SECTION></BODY></HWPML>' % (st, ps, "".join(cover), "".join(body)))


def _cell(r, c, *texts):
    return '<CELL ColAddr="%d" RowAddr="%d" RowSpan="1" ColSpan="1"><PARALIST>%s</PARALIST></CELL>' % (
        c, r, "".join(P(t) for t in texts))


def _table(rows):
    body = "".join("<ROW>%s</ROW>" % "".join(_cell(r, c, *(x if isinstance(x, tuple) else (x,)))
                                             for c, x in enumerate(row)) for r, row in enumerate(rows))
    return '<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE ColCount="%d" RowCount="%d">%s</TABLE></TEXT></P>' % (
        len(rows[0]), len(rows), body)


def template_sized_hwpml():
    """스타일마다 글자 크기가 있는 공통 템플릿 흉내 (P-038 글자 크기 대조) — 바탕글·표 칸 1000, 본문·캡션 1100,
    도움말 1050, 제목·표지 1300 (HWPUNIT)."""
    sizes = {"바탕글": 0, "05_도표내용_항목제목": 0, "07_도표내용_본문혼합": 0, "06_도표내용_본문중앙": 0, "03_본문_내용": 1,
             "04_도표그림_제목": 1, "14_도움말_파란색": 3}
    cs = '<CHARSHAPELIST>%s</CHARSHAPELIST>' % "".join(
        '<CHARSHAPE Id="%d" Height="%d"/>' % (i, h) for i, h in enumerate((1000, 1100, 1300, 1050)))
    x = template_hwpml().replace("<STYLELIST>", cs + "<STYLELIST>", 1)
    for i, n in enumerate(STYLES):
        x = x.replace('<STYLE Id="%d" Name="%s" ' % (i, n),
                      '<STYLE Id="%d" Name="%s" CharShape="%d" ' % (i, n, sizes.get(n, 2)), 1)
    return x


def template_leftover_hwpml():
    """공통 템플릿 실측 꼴(P-039, F-109): 본문 첫 장 제목 뒤 빈 문단(본문 지우기에서 남은 그릇)이 03 스타일인데 글자 모양은
    옛 본문 12pt(1200, 직접 서식)."""
    x = template_sized_hwpml().replace("</CHARSHAPELIST>", '<CHARSHAPE Id="4" Height="1200"/></CHARSHAPELIST>', 1)
    return x.replace("</SECTION></BODY>", '<P ParaShape="0" Style="%d"><TEXT CharShape="4"/></P></SECTION></BODY>'
                     % STYLES.index("03_본문_내용"))


def template_cover_hwpml():
    """표지 날짜·결재란(칸 하나에 줄 셋)·제·개정 이력서(양식 예시 줄)가 있는 공통 템플릿 흉내 (P-037).
    같은 키가 뜻이 다른 여러 자리에 있다 — {{발행일자}} 3곳, {{검토자}} 2곳, {{결재일자}} 3곳."""
    box = _table([[("작성자 : {{작성자}} 일자 : {{결재일자}}", "검토자1 : {{검토자}} 일자 : {{결재일자}}",
                    "검토자2 : {{검토자}} 일자 : {{결재일자}}")]])
    hist = _table([["제·개정 일자", "버전번호", "개정내용"], ["{{발행일자}}", " V0.1", "신규 제정"],
                   ["{{발행일자}}", " V0.2", "ooo 기능 추가"]])
    toc = P("목     차", 1)
    return template_hwpml().replace(toc, P("{{발행일자}}") + box + hist + toc, 1)


EACH_SPEC = '''# 자리별 값 명세
```json
{"template": "tpl/common.hwpx", "out": "out/doc.hwpx",
 "keys": {"{{문서명}}": "사용자지침서", "{{문서영문명}}": "Software User Manual", "{{과제명}}": "시험 과제",
          "{{문서번호}}": "RTV-1", "{{버전}}": "1.0", "{{작성자}}": "갑",
          "{{발행일자}}": ["2026.10.", "2026.10.15.", ""], "{{검토자}}": ["을", ""], "{{결재일자}}": ["2026. 10.", "2026. 10.", ""]},
 "front": {"V0.1": "Ver 1.0", "V0.2": "", "ooo 기능 추가": ""}}
```
# 개요
![로그인 화면](없는/a.png)
화면은 {{그림:로그인 화면}} 과 같다.
'''


SPEC = '''# 시험 명세
```json
{"template": "tpl/common.hwpx", "out": "out/doc.hwpx",
 "keys": {"{{문서명}}": "사용자지침서", "{{문서영문명}}": "Software User Manual", "{{과제명}}": "시험 과제", "{{없는키}}": "x"}}
```
# 개요
## 적용범위
본 문서는 시험용이다.
- 첫째
  - 하위
표: 소프트웨어 목록
| 이름 | 버전 |
|---|---|
| 가 | 1.0<br>(시험) |
![로그인 화면](원본 s0.p3)
> 운용 사이트 정보
<!-- 문서에 들어가지 않는 메모 -->
# 관련문서
끝 문단.
'''


class TestSpec(unittest.TestCase):
    def test_parse_and_plan(self):
        meta, blocks = wd.parse_spec(SPEC)
        self.assertEqual(meta["out"], "out/doc.hwpx")
        self.assertEqual([b["kind"] for b in blocks],
                         ["heading", "heading", "para", "item", "item", "table", "figure", "need", "heading", "para"])
        self.assertEqual(blocks[5], {"kind": "table", "caption": "소프트웨어 목록", "rows": [["이름", "버전"], ["가", "1.0\n(시험)"]],
                                     "header": True})
        items = wd.plan(blocks, wd.STYLES)                   # 그림 없이(pictures=False): 그림 캡션은 예전처럼 글자 문단
        self.assertEqual([(x.get("text"), x.get("style")) for x in items if x["type"] == "para"], [
            ("적용범위", "COMSAF 개요 2"), ("본 문서는 시험용이다.", "03_본문_내용"), ("○ 첫째", "03_본문_내용"),
            ("  - 하위", "03_본문_내용"),
            ("※ 그림 삽입 필요: 로그인 화면 (출처: 원본 s0.p3)", "14_도움말_파란색"), ("그림 1 로그인 화면", "04_도표그림_제목"),
            ("※ 작성 필요: 운용 사이트 정보", "14_도움말_파란색"), ("관련문서", "COMSAF 개요 1"), ("끝 문단.", "03_본문_내용")])
        tbl = [x for x in items if x["type"] == "table"][0]      # 표 캡션은 글자 문단이 아니라 한/글 캡션(위) — P-049
        self.assertEqual(tbl["cap"], {"text": "표 1 소프트웨어 목록", "title": "소프트웨어 목록", "style": "04_도표그림_제목",
                                      "side": "Top", "newnum": 1})                   # 첫 캡션 표 앞 새 번호(P-050)
        self.assertNotIn("문서에 들어가지 않는", SPEC.split("```")[2].replace("<!-- 문서에 들어가지 않는 메모 -->", ""))

    def test_probe_spec_plan(self):
        """시험 명세 samples/probe_spec.md 의 P-050 기대(명세 머리 메모와 같음) — 캡션 표 1(새 번호 1) · 캡션 없는 표 · 캡션 표 2
        (새 번호 2) · 그림 1(새 번호 1) · 그림 2. 그림 파일이 있든 없든(자리 표시 그림) 같다(검토 P-050 D1-③-07)."""
        _, blocks = wd.parse_spec((HERE.parent / "samples" / "probe_spec.md").read_text(encoding="utf-8"))
        items = wd.plan(blocks, wd.STYLES, pictures=True)
        self.assertEqual([(x["type"], (x.get("cap") or {}).get("text"), (x.get("cap") or {}).get("newnum"))
                          for x in items if x["type"] != "para"],
                         [("table", "표 1 시험 표", 1), ("table", None, None), ("table", "표 2 기호 너비 시험", 2),
                          ("picture", "그림 1 시험 화면", 1), ("picture", "그림 2 없는 그림", None)])

    def test_text_checks_find_stale_citations(self):
        """절 인용 검사(text_checks, P-051) — {{절:}} 인용과 맞는 범위는 조용하고, 범위 넘침·뒤집힘·0)·단계 없는 절, 글자 절 번호
        (맞아도·낡아도·없는 번호·제목을 바꾼 뒤), 인용 밖 글자 '표 N'·'그림 N'(표 칸·표 캡션 안도), 수준 건너뜀을 찾는다(음성 대조).
        낱말 안 '도표 3'·숫자에 붙은 세는 말 '표 3개'·인용 {{표:표 3 화면}} 안 글자는 글자 번호가 아니고, 띄운 '표 3 개요' 는 번호다.
        단계는 항목 줄도 세고, 다시 1) 부터 시작해도 가장 큰 번호다. 인용 뒤 조사 '의' 를 받고, 인용에 붙지 않은 범위는 그 글이 든
        절의 단계와 견준다. 'PFD1 가 절'·'1.1 (참고)' 은 절 번호가 아니다(검토 D2-①-02~06·D2-③-05·D3-③-01·04·06·08)."""
        head = '```json\n{"template": "t.hwpx", "out": "o.hwpx"}\n```\n# 개요\n'
        body = ("## 가 절\n1) 하나\n2) 둘\n3) 셋\n1) 다시 하나\n2)~3)은 한 번에 한다.\n## 나 절\n- 1) 항목 단계\n- 2) 항목 단계\n"
                "## 다 절\n{{절:가 절}} 2)~3)을 수행한 뒤 {{절:나 절}} 2)로 간다. 도표 3 과 {{표:목록}}·{{절:그림 2 처리}}, 그림 2장과 "
                "표 3개, 그림 12장·표 2건·표 4종·표 3가지·표 4행·표 2열·표 3쪽·표 4줄·표 5칸·그림 6점. PFD1 가 절 확인, 1.1 (참고).\n"
                "1. 가 절 버튼을 누른다.\n"
                "표: 목록\n| 가 | 나 |\n|---|---|\n| 1 | 2 |\n## 그림 2 처리\n")
        clean = wd.text_checks(wd.parse_spec(head + body)[1])
        self.assertEqual((wd.text_check_problems(clean), clean["suspect"]), ([], []))
        self.assertEqual([(r["section"], r["lo"], r["hi"], r["steps"], r["by"]) for r in clean["ranges"]],
                         [("1.1", 2, 3, 3, "local"), ("1.1", 2, 3, 3, "ref"), ("1.2", 2, 2, 2, "ref")])
        moved = wd.text_checks(wd.parse_spec(head + "## 새 절\n" + body)[1])           # 앞에 절이 늘어도 {{절:}} 은 따라간다
        self.assertEqual(wd.text_check_problems(moved), [])
        self.assertEqual([r["section"] for r in moved["ranges"]], ["1.2", "1.2", "1.3"])
        loc3 = "이 절(1.1 가 절)의 단계 범위 — 그 절의 단계는 3)까지. 다른 절의 단계면 {{절:제목}} 바로 뒤에 쓴다"
        for old, new, why in (("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)~4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 3)～2)", "단계 범위가 뒤집혔다"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 0)〜2)", "단계는 1)부터"),
                              ("{{절:나 절}} 2)", "{{절:나 절}} 3)", "그 절의 단계는 2)까지"),
                              ("{{절:나 절}} 2)", "{{절:다 절}} 1)", "그 절에는 단계 줄이 없다"),
                              ("{{절:가 절}} 2)~3)", "1.1 가 절 2)~3)", "글자 절 번호 — {{절:가 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:가 절}} 2)~3)", "1.1. 가 절", "글자 절 번호 — {{절:가 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:나 절}} 2)", "1.1 나 절", "그 번호의 절은 '가 절' — '나 절' 는 1.2"),
                              ("{{절:나 절}} 2)", "9.9 나 절", "없는 절 번호 — '나 절' 는 1.2"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}의 2)~4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)-4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)부터 4)까지", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2), 4)", "그 절의 단계는 3)까지"),
                              ("{{절:나 절}} 2)", "1.2절", "글자 절 번호 — {{절:나 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:나 절}} 2)", "제1장", "글자 절 번호 — {{절:개요}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)–4)", "그 절의 단계는 3)까지"),     # en·em 줄표·NBSP·전각
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)—4)", "그 절의 단계는 3)까지"),     # 빈칸·∼(D3F-05·D4-①-02)
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}\u00a02)~4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}\u30002)\u223c4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 의 2)~4)", "그 절의 단계는 3)까지"),   # '의' 앞 빈칸(D3F-N05)
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}의 2)·3)·4)", "그 절의 단계는 3)까지"),  # 나열은 원소마다
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 1), 2), 4)", "그 절의 단계는 3)까지"),  # (D4-①-01)
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2) 및 4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)와 4)", "그 절의 단계는 3)까지"),     # 와·・·－(D5-③-04·D4F-02)
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}의 2)・4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}}의 2)ㆍ4)", "그 절의 단계는 3)까지"),   # 한글 입력기 가운뎃점
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)－4)", "그 절의 단계는 3)까지"),
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2),\u30004)", "그 절의 단계는 3)까지"),   # 나열 뒤 전각 빈칸
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2), 4) {{절:나 절}} 1)", "그 절의 단계는 3)까지"),  # 나열·범위 뒤가
                              ("{{절:가 절}} 2)~3)", "{{절:가 절}} 2)~4) {{절:나 절}} 1)", "그 절의 단계는 3)까지"),  # 인용이어도 단계
                              ("{{절:가 절}} 2)~3)", "1.1\u3000가 절 2)~3)",               # (D5-③-02). 전각 빈칸 글자 번호(D5-③-04)
                               "글자 절 번호 — {{절:가 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:나 절}} 2)", "1.2절의 내용",                                         # 조사 '의'(D4F-03)
                               "글자 절 번호 — {{절:나 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:나 절}} 2)", "{{절:나 절}} 3) {{표:목록}}", "그 절의 단계는 2)까지"),  # 뒤가 표 인용이면 단계(D4-③-02)
                              ("{{절:나 절}} 2)", "1.2항", "글자 절 번호 — {{절:나 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"),
                              ("{{절:나 절}} 2)", "앞 글 1. 가 절", "그 번호의 절은 '개요' — '가 절' 는 1.1"),   # 문단 가운데 'N. '
                              ("{{절:나 절}} 2)", "{{절:나 절}} 2) 다음 {{절:나 절}} 3)", "그 절의 단계는 2)까지"),  # 한 문단 여러
                              ("{{절:나 절}} 2)", "{{절:나 절}} 4)", "그 절의 단계는 2)까지"),   # 인용 — 단계마다 대조(D5-①-03·04)
                              ("2)~3)은 한 번에", "2)~5)는 한 번에", loc3),
                              ("2)~3)은 한 번에", "2)–5)는 한 번에", loc3),
                              ("2)~3)은 한 번에", "2)부터 5)까지 한 번에", loc3),
                              ("2)~3)은 한 번에", "2)\u3000~\u30005)는 한 번에", loc3),   # 전각 빈칸 범위(D5-③-04)
                              ("2)~3)은 한 번에", "5)~5)는 한 번에", loc3),            # 범위 머리는 단계 줄이 아니다(D4-①-06) —
                              ("2)~3)은 한 번에", "5) ~ 5)는 한 번에", loc3),          # 띄운 꼴·줄표·전각 빈칸도(D4F-03·D5-③-04)
                              ("2)~3)은 한 번에", "5) – 5)는 한 번에", loc3),
                              ("2)~3)은 한 번에", "5)\u3000~\u30005)는 한 번에", loc3)):
            got = wd.text_checks(wd.parse_spec(head + body.replace(old, new))[1])
            self.assertEqual([x["why"] for x in got["section"]][-1:], [why], new)
            self.assertEqual(got["literal"], [], new)
        sus = wd.text_checks(wd.parse_spec(head + body.replace("{{절:나 절}} 2)", "1.2 나중 절"))[1])   # 낡은 인용이거나 보통 글
        self.assertEqual((wd.text_check_problems(sus), [x["why"] for x in sus["suspect"]]),
                         ([], ["그 번호의 절은 '나 절' — 절 인용이면 {{절:제목}} 으로"]))
        self.assertTrue([w for w in wd.text_check_warnings(sus) if w.startswith("의심 1곳") and "{{글자:…}} 로" in w])
        sub = wd.text_checks(wd.parse_spec(head + "## 부모\n### 자식\n1) 하나\n2) 둘\n## 다른\n{{절:부모}} 1)~2)를 본다.\n")[1])
        self.assertEqual([x["why"] for x in sub["section"]], ["그 절에는 단계 줄이 없다"])     # 하위 절 단계는 부모 단계가 아니다
        rng = wd.text_checks(wd.parse_spec(head + body.replace("{{절:가 절}} 2)~3)", "1.1 가 절 2)~4)"))[1])
        self.assertEqual([x["why"] for x in rng["section"]], ["글자 절 번호 — {{절:가 절}} 로 쓴다(다른 문서의 절이면 {{글자:…}})", "그 절의 단계는 3)까지"])
        pre = wd.text_checks(wd.parse_spec(head + "# 모의\n## 모의 시작\n2 모의 시작 전에 본다. 9.9 모의 시작 을 본다.\n")[1])
        self.assertEqual(pre["section"], [{"at": 3, "cite": "2 모의", "why": "글자 절 번호 — {{절:모의}} 로 쓴다(다른 문서의 절이면 {{글자:…}})"},  # 긴 제목에
                                          {"at": 3, "cite": "9.9 모의 시작", "why": "없는 절 번호 — '모의 시작' 는 2.1"}])  # 끌리지 않고, 긴 제목 먼저
        bad = body.replace("도표 3", "표 3").replace("| 1 | 2 |", "| 그림 2 | 2 |").replace("표: 목록", "표: 그림 1 목록") \
            .replace("{{표:목록}}", "{{표:그림 1 목록}}")
        got = wd.text_checks(wd.parse_spec(head + bad)[1])
        self.assertEqual([x["text"] for x in got["literal"]], ["표 3", "그림 2"])   # 본문 · 표 칸(인용 안 글자는 아님)
        self.assertEqual([(x["cite"], x["why"]) for x in got["suspect"]],          # 표 캡션 — 인용을 쓸 수 없는 자리라 의심
                         [("그림 1", "캡션 안 — 글자 표·그림 번호")])
        other = wd.text_checks(wd.parse_spec(head + "## 적용범위\n## 가 절\n체계사양서 {{글자:1.1 적용범위}}·{{글자:3.1.1항}} 을 따른다. "
                                             "MIL-STD-498 9.9절 참고. 참고: 1) {{절:가 절}} 2) {{절:적용범위}}\n"
                                             "1. 개요를 먼저 읽는다.\n![1.1 적용범위 화면](a.png)\n")[1])
        self.assertEqual((wd.text_check_problems(other), [(x["cite"], x["why"]) for x in other["suspect"]]),   # 다른 문서의 절·
                         ([], [("9.9절", "이 문서에 없는 절 번호 — 다른 문서의 절이면 {{글자:…}} 로 감싼다"),        # 나열 번호·목록 번호·
                               ("1.1 적용범위", "캡션 안 — 글자 절 번호 — {{절:적용범위}} 로 쓴다(다른 문서의 절이면 "  # 캡션
                                "{{글자:…}})")]))
        plain = [x["text"] for x in wd.plan(wd.parse_spec(head + "## 적용범위\n체계사양서 {{글자:1.1 적용범위}} 를 따른다.\n")[1],
                                             wd.STYLES) if x["type"] == "para"]
        self.assertIn("체계사양서 1.1 적용범위 를 따른다.", plain)                   # {{글자:…}} 는 글자 그대로
        spaced = wd.text_checks(wd.parse_spec(head + "## 가 절\n그림 2 장비 구성도를 본다. 표 3 개요와 같다. 표 1 건의 목록. "
                                                     "표3 을 본다. 그림 4가 보여 준다. 표\u00a05 를 본다. 표\u30006 을 본다.\n")[1])
        self.assertEqual([x["text"] for x in spaced["literal"]], ["그림 2", "표 3", "표 1", "표3", "그림 4", "표\u00a05", "표\u30006"])  # 띄운 글·
        # 조사 '가' 는 세는 말이 아니다(D3-③-01·D4-①-03)
        desc = wd.text_checks(wd.parse_spec(head + body.replace("{{절:가 절}} 2)~3)", "{{절:가 절}} 3), 1)"))[1])
        self.assertEqual(wd.text_check_problems(desc), [])                       # 내림 나열은 뒤집힌 범위가 아니다(D4-①-01)
        self.assertEqual([(r["lo"], r["hi"]) for r in desc["ranges"] if r["by"] == "ref"][:2], [(3, 3), (1, 1)])
        nosp = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n2) 둘\n3)\u3000셋\n4)와 5)는 관리자만 한다.\n3)의 결과를 본다.\n"
                                             "4)설치를 끝낸다.\n4) 및 5)는 관리자만 한다.\n- 4) 또는 5)는 건너뛴다.\n4) 의 결과를 본다.\n"
                                             "4) 에서 2)로 돌아간다.\n4) 그리고 5)는 건너뛴다.\n4) 와 같이 한다.\n"
                                             "4) 에서2)로 돌아간다.\n4) 에서 확인한다.\n4) · 5)는 관리자만 한다.\n4) 과 같이 한다.\n"
                                             "## 나 절\n{{절:가 절}}의 4)를 본다.\n")[1])
        self.assertEqual([x["why"] for x in nosp["section"]], ["그 절의 단계는 3)까지"])   # 번호 뒤 빈칸 없는 문단 머리('4)와 5)는'·
        # '3)의 결과'·'4)설치' — D5-①-02)와 띄어 쓴 나열·조사 머리('4) 및 5)는'·'4) 또는 5)는'·'4) 의 결과'·'4) 에서 2)로' — D6-①-01)는
        # 단계 줄이 아니다. 번호 뒤 전각 빈칸 '3)\u3000셋' 은 단계 줄(D6-③-03). 두 예외(이음말·나열 머리, 조사 머리)는 겹치니 한 갈래로만
        # 빠지는 줄도 둔다 — '그리고'·'에서2)'·'·' 는 머리 예외만, '와 같이'·'에서 확인' 은 조사 머리만(D7-③-02·N01)
        base = head + "## 부모\n모의는 2)~3)의 순서로 한다.\n### 자식\n1) 하나\n2) 둘\n## 가 절\n1) 하나\n2) 둘\n"
        loc = wd.text_checks(wd.parse_spec(base + "> 1)~9) 절차를 채운다\n표: 칸\n| 1)~9) | 점검 |\n|---|---|\n| a | b |\n"
                                           "{{글자:체계사양서 3.2 시험 절차}}의 2)~5)를 따른다.\n")[1])
        self.assertEqual((wd.text_check_problems(loc), loc["suspect"]), ([], []))   # 단계 없는 절·메모·표 칸·{{글자:}} 바로 뒤
        for line, sus in (("{{글자:체계사양서 3.2 시험 절차}} 절차는 2)~5)를 따른다.", ["인용 뒤에 떨어진 단계 범위"]),   # 단계는 보지
                          ("{{절:가 절}}에서 2)~8)을 본다.", ["인용 뒤에 떨어진 단계 범위"]),                          # 않는다.
                          ("운용자 교범 3.1.1항의 2)~5)를 따른다.", ["이 문서에 없는 절 번호", "인용 뒤에 떨어진 단계 범위"]),   # 앞에
                          ("1.2 나중 절차는 2)~5)로 한다.", ["그 번호의 절은 '가 절'", "인용 뒤에 떨어진 단계 범위"])):  # 인용이 있으면
            got = wd.text_checks(wd.parse_spec(base + line + "\n")[1])                           # 갈래마다 의심(D3F-02·D4-①-04·D5-③-01)
            self.assertEqual((wd.text_check_problems(got), [x["why"].split(" — ")[0] for x in got["suspect"]]), ([], sus), line)
        lit = wd.text_checks(wd.parse_spec(base + "1.2 가 절 다음 2)~5)를 한다.\n")[1])
        self.assertEqual(([x["why"].split(" — ")[0] for x in lit["section"]], [x["why"].split(" — ")[0] for x in lit["suspect"]]),
                         (["글자 절 번호"], ["인용 뒤에 떨어진 단계 범위"]))
        try:                                                    # 아주 긴 숫자에서 멈추지 않는다(int 4300 자리 — D4-①-07)
            big = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n{{절:가 절}} " + "9" * 5000 + ")와 1)~" + "9" * 5000
                                               + ")\n")[1])
        except ValueError as e:
            self.fail("긴 숫자에서 멈춤: %s" % e)
        self.assertEqual(wd.text_check_problems(big), [])
        back = wd.text_checks(wd.parse_spec(head + body.replace("{{절:가 절}} 2)~3)", "{{절:가 절}}의 3)에서 2)로 돌아가"))[1])
        self.assertEqual(wd.text_check_problems(back), [])                 # '에서' 는 범위 이음이 아니다(되돌아가기 — D5-①-01)
        enum = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n## 나 절\n참고: 1) {{절:가 절}} 2) {{글자:체계사양서 3.1 적용범위}}, "
                                             "1) {{절:가 절}}, 2) 화면 확인\n참고: 1) {{절:가 절}} 2)\u3000{{절:나 절}}\n")[1])
        self.assertEqual((wd.text_check_problems(enum), enum["suspect"]), ([], []))   # 다음이 글자 인용이면 나열(D5-①-06), 인용
        joined = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n## 나 절\n{{절:가 절}}의 2) {{글자:교범 2.1}} 를 함께 본다.\n")[1])
        self.assertEqual([x["why"] for x in joined["section"]], ["그 절의 단계는 1)까지"])   # 조사 '의' 로 이으면 단계(D6-①-02)
        for alt in ("{{절:가 절}} 2) 또는 4)", "{{절:가 절}} 2) 그리고 4)", "{{절:가 절}}의 2)‧4)",   # '또는'·'그리고'·'‧'·'혹은'·
                    "{{절:가 절}} 2) 혹은 4)", "{{절:가 절}} 2)/4)", "{{절:가 절}} 2) 내지 4)"):    # '/' 는 나열, '내지' 는 범위
            orr = wd.text_checks(wd.parse_spec(head + body.replace("{{절:가 절}} 2)~3)", alt))[1])   # 기호가 아니다 — 첫 단계만
            self.assertEqual(wd.text_check_problems(orr), [], alt)                                  # (D5-③-04·D6-③-05·D8-③-06)
        for word in ("과정을 확인한다.", "의견을 적는다.", "와이파이를 켠다."):     # 머리 낱말 글자로 시작하는 참 단계는 단계 줄 —
            true = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n2) " + word + "\n## 나 절\n{{절:가 절}}의 2)를 본다.\n")[1])
            self.assertEqual(wd.text_check_problems(true), [], word)   # 줄마다 마지막 단계로(단계 수 = 가장 큰 번호 — D8-③-05·D9-③-01)
        for word in ("혹은", "내지", "/"):                                        # 목록 밖 머리 '4) 혹은 5)는'·'4) 내지'·'4) /' 는
            other = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n2) 둘\n3) 셋\n4) " + word + " 5)는 관리자만 한다.\n"
                                                 "## 나 절\n{{절:가 절}}의 4)를 본다.\n")[1])
            self.assertEqual(wd.text_check_problems(other), [], word)  # 단계 줄로 센다(SKILL §3 — D8-③-06·D9-③-03)
        one = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n## 나 절\n{{절:가 절}}의 2)~3)을 본다.\n")[1])
        self.assertEqual(one["section"], [{"at": 4, "cite": "{{절:가 절}}의 2)~3)", "why": "그 절의 단계는 1)까지"}])   # 항목
        lst = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n2) 둘\n3) 셋\n## 나 절\n{{절:가 절}}의 2), 5)를 본다.\n")[1])
        self.assertEqual([x["cite"] for x in lst["section"]], ["{{절:가 절}}의 2), 5)"])   # 나열 꼴도 인용 글 전체(D9-③-05)
        # 전체(인용 글에 범위까지 — D8-③-07)
        blk = wd.text_checks(wd.parse_spec(head + "## 가 절\n1) 하나\n## 나 절\n참고: 1) {{절:가 절}} 2) 화면 확인\n")[1])  # 뒤 쉼표면
        self.assertEqual([x["why"] for x in blk["section"]], ["그 절의 단계는 1)까지"])   # 단계 아님. 쉼표 없는 글 나열은 단계로 읽는다
        word = wd.text_checks(wd.parse_spec(head + "## 가 절\n제1장비를 켠다. 1.1항목을 본다. 1.1절차를 따른다. 1.1절에 따른다.\n")[1])
        self.assertEqual([x["cite"] for x in word["section"]], ["1.1절"])          # 조사 앞만 고칠 것 — 낱말 첫 글자는 의심(D4-①-05)
        self.assertEqual([x["why"].split(" — ")[0] for x in word["suspect"]], ["뒤 글자와 한 낱말일 수 있다"] * 3)
        many = wd.text_checks(wd.parse_spec(head + "표 1 과 표 2 와 표 3 과 표 4 를 본다.\n")[1])
        warn = [w for w in wd.text_check_warnings(many) if w.startswith("글자로 쓴 표·그림 번호 4곳")]
        self.assertTrue(warn and "'표 3'" in warn[0] and "'표 4'" not in warn[0], wd.text_check_warnings(many))  # 앞 3곳만
        skip = wd.text_checks(wd.parse_spec(head + "### 깊은 절\n## 범위\n")[1])
        self.assertEqual(skip["levels"], [{"at": 1, "text": "깊은 절", "why": "수준 1 다음에 3"}])
        self.assertEqual([x["kind"] for x in wd.text_check_problems(skip)], ["levels"])         # 고칠 것·경고로 간다
        self.assertTrue([w for w in wd.text_check_warnings(skip) if w.startswith("제목 수준을 건너뛴 곳 1 ['깊은 절 (수준 1")])
        self.assertEqual([n for n, _, _ in wd.heading_numbers(wd.parse_spec(head + "### 깊은 절\n## 범위\n")[1])],
                         ["1", "1.0.1", "1.1"])

    def test_missing_picture_gets_placeholder_with_caption(self):
        """그림 파일이 없으면(그림 넣기) 작성 필요 메모 + 자리 표시 그림에 같은 캡션(아래) — 캡션을 달 개체가 있어야 한/글 그림
        자동 번호가 명세 번호와 같다(P-049). 명세에 크기가 없으면 PLACEHOLDER_MM."""
        items = wd.plan(wd.parse_spec(SPEC)[1], wd.STYLES, pictures=True)
        k = [i for i, x in enumerate(items) if x.get("figure")][0]
        self.assertEqual((items[k]["type"], items[k]["text"]), ("para", "※ 그림 삽입 필요: 로그인 화면 (출처: 원본 s0.p3)"))
        pic = items[k + 1]
        self.assertEqual((pic["type"], pic["path"], pic["size"], pic["placeholder"], pic["style"]),
                         ("picture", str(wd.PLACEHOLDER), [80.0, 45.0], True, "04_도표그림_제목"))
        self.assertEqual(pic["cap"], {"text": "그림 1 로그인 화면", "title": "로그인 화면", "style": "04_도표그림_제목",
                                      "side": "Bottom", "newnum": 1})                # 첫 그림 앞 새 번호(P-050)
        self.assertTrue(wd.PLACEHOLDER.is_file())
        self.assertFalse([x for x in items if x.get("text") == "그림 1 로그인 화면"])    # 캡션 글자 문단은 없다
        sized = wd.plan(wd.parse_spec(SPEC.replace("(원본 s0.p3)", '(원본 s0.p3 "30x20")'))[1], wd.STYLES, pictures=True)
        self.assertEqual([x["size"] for x in sized if x.get("placeholder")], [[30.0, 20.0]])
        orig = wd.PLACEHOLDER                                    # 자리 표시 파일이 없으면 손대기 전에 명세 오류
        wd.PLACEHOLDER = orig.with_name("없는_자리표시.png")
        try:
            with self.assertRaises(wd.SpecError):
                wd.plan(wd.parse_spec(SPEC)[1], wd.STYLES, pictures=True)
            self.assertTrue(wd.plan(wd.parse_spec(SPEC)[1], wd.STYLES))     # 그림 없이(pictures=False)는 필요 없다
        finally:
            wd.PLACEHOLDER = orig

    def test_tables_and_figures_numbered_in_order(self):
        """표·그림 번호는 명세 차례대로 따로 센다 — SUM 본문이 '그림 k' 로 가리키는 번호가 이것이다(P-029). 캡션 없는 표는
        번호가 없다(한/글 자동 번호도 캡션의 번호만 센다 — 참고본 SUM 앞부분 표 셋 뒤 첫 캡션이 '표 1'). 그림 넣기 여부와
        상관없이 같은 번호(P-049)."""
        body = ('```json\n{"template": "t.hwpx", "out": "o.hwpx"}\n```\n# 개요\n![첫 그림](a.png)\n표: 첫 표\n| a |\n'
                '![둘째 그림](b.png "10x5")\n표: 둘째 표\n| b |\n사이 문단\n| 제목 없는 표 |\n![셋째 그림](c.png)\n')
        for pictures in (False, True):
            items = wd.plan(wd.parse_spec(body)[1], wd.STYLES, pictures)
            self.assertEqual([x["cap"]["text"] if x.get("cap") else x["text"] for x in items
                              if x.get("cap") or (x["type"] == "para" and x["style"] == wd.STYLES["caption"])],
                             ["그림 1 첫 그림", "표 1 첫 표", "그림 2 둘째 그림", "표 2 둘째 표", "그림 3 셋째 그림"], pictures)
            self.assertEqual([x.get("cap") for x in items if x["type"] == "table"][2], None)
            self.assertEqual(sum(1 for x in items if x["type"] == "table"), 3)

    def test_spec_errors(self):
        head = '```json\n{"template": "t.hwpx", "out": "o.hwpx"}\n```\n'
        for body, msg in (("## 개요\n", "첫 블록"), ("# 개요\n표: 목록\n본문\n", "다음 줄은 표"),
                          ("# 개요\n표: 목록\n", "뒤에 표가 없다"), ("# 개요\n| a | b |\n| c |\n", "칸 수가 다르다"),
                          ('# 개요\n![영 크기](a.png "0x5")\n', "0 보다 커야"),
                          ('# 개요\n![영 크기](없는 그림 "10x0")\n', "0 보다 커야")):
            with self.assertRaises(wd.SpecError) as e:
                wd.parse_spec(head + body)
            self.assertIn(msg, str(e.exception))
        with self.assertRaises(wd.SpecError):
            wd.parse_spec("# 개요\n")                                              # json 머리 없음
        with self.assertRaises(wd.SpecError):
            wd.parse_spec('```json\n{"template": "t.hwpx", "out": "o.hwp"}\n```\n# 개요\n')    # .hwpx 아님
        with self.assertRaises(wd.SpecError):
            wd.parse_spec('```json\n{"template": "t", "out": "o.hwpx", "keys": {"과제명": "x"}}\n```\n# 개요\n')
        for out in ("/abs/o.hwpx", "K:/repo/o.hwpx", "K:o.hwpx", "a/../../o.hwpx", "a\\\\..\\\\o.hwpx", "\\\\\\\\srv\\\\o.hwpx",
                    "\\\\abs\\\\o.hwpx"):                                             # 마지막: 드라이브 없는 Windows 루트
            with self.assertRaises(wd.SpecError, msg=out) as e:                # 저장소 밖 출력(md 경로를 못 셈 — 검토 P-051)
                wd.parse_spec('```json\n{"template": "t.hwpx", "out": "%s"}\n```\n# 개요\n' % out)
            self.assertIn("저장소 안 상대 경로", str(e.exception))
        self.assertEqual(wd.parse_spec('```json\n{"template": "t.hwpx", "out": "a/b..c/o.hwpx"}\n```\n# 개요\n')[0]["out"],
                         "a/b..c/o.hwpx")                                       # 이름 속 '..' 은 괜찮다
        for body in ("# 개요\n## {{절:개요}} 보기\n", "# 개요\n표: {{표:다른}} 목록\n| a |\n", "# 개요\n![{{그림:x}}](a.png)\n"):
            with self.assertRaises(wd.SpecError, msg=body) as e:               # 제목·캡션은 인용을 바꾸지 않는 자리(P-051)
                wd.parse_spec(head + body)
            self.assertIn("제목·캡션 안에는", str(e.exception))


class TestRefsAndValues(unittest.TestCase):
    HEAD = '```json\n{"template": "t.hwpx", "out": "o.hwpx"}\n```\n# 개요\n'

    def test_refs_follow_numbers(self):
        """{{그림:캡션}}·{{표:캡션}} 은 그 캡션 번호로 — 앞에 그림이 늘어도 따라간다 (P-037, 1장에 그림이 생겨 번호가 밀림)."""
        body = ("![새 그림](a.png)\n![로그인 화면](b.png)\n표: 목록\n| a |\n"
                "화면은 {{그림:로그인 화면}} 이고 목록은 {{표:목록}} 이다.\n- {{그림:새 그림}} 참고\n"
                "> {{그림:로그인 화면}} 의 값 가림\n| {{표:목록}} 칸 |\n")
        items = wd.plan(wd.parse_spec(self.HEAD + body)[1], wd.STYLES)
        texts = [x["text"] for x in items if x["type"] == "para"]
        self.assertIn("화면은 그림 2 이고 목록은 표 1 이다.", texts)
        self.assertIn("○ 그림 1 참고", texts)
        self.assertIn("※ 작성 필요: 그림 2 의 값 가림", texts)
        self.assertEqual([x for x in items if x["type"] == "table"][-1]["rows"], [["표 1 칸"]])

    def test_ref_errors(self):
        for body, msg in (("{{그림:없는 그림}}\n", "캡션이 없다"),
                          ("![같은](a.png)\n![같은](b.png)\n{{그림:같은}}\n", "모호하다"),
                          ("표: 목록\n| a |\n{{표:다른 목록}}\n", "캡션이 없다"),
                          ("## 가 절\n{{절:가절}} 참고\n", "절 제목이 없다"),
                          ("## 가 절\n# 둘\n## 가 절\n{{절:가 절}} 참고\n", "같은 제목의 절이 2개(1.1·2.1)라 인용이 모호하다"),
                          ("### 깊은 절\n{{절:깊은 절}} 참고\n", "수준을 건너뛴 제목이라 번호를 셀 수 없다")):
            with self.assertRaises(wd.SpecError) as e:
                wd.plan(wd.parse_spec(self.HEAD + body)[1], wd.STYLES)
            self.assertIn(msg, str(e.exception))

    def test_section_refs_follow_headings(self):
        """{{절:제목}} → 명세 제목 차례로 센 '번호 제목'(본문·항목·메모·표 칸 — P-051). 앞에 절이 늘면 번호가 따라가고, 같은 꼴의
        글자 인용과 보이는 글자가 같다(SUM 6.2 가 '4.3.4.1 모의 시작' 을 바꾼 까닭 — 검토 P-051 D2-①-01)."""
        body = ("## 적용범위\n### 범위 세부\n# 운용\n## 모의 시작\n1) 하나\n{{절:모의 시작}} 1)을 하고 {{절:개요}}·{{절:범위 세부}} 를 본다.\n"
                "- {{절:운용}} 참고\n> {{절:적용범위}} 의 값\n| {{절:모의 시작}} | 칸 |\n")
        texts = lambda b: [x["text"] for x in wd.plan(wd.parse_spec(self.HEAD + b)[1], wd.STYLES) if x["type"] == "para"]
        tables = lambda b: [x["rows"] for x in wd.plan(wd.parse_spec(self.HEAD + b)[1], wd.STYLES) if x["type"] == "table"]
        self.assertIn("2.1 모의 시작 1)을 하고 1 개요·1.1.1 범위 세부 를 본다.", texts(body))
        self.assertIn("○ 2 운용 참고", texts(body))
        self.assertIn("※ 작성 필요: 1.1 적용범위 의 값", texts(body))
        self.assertEqual(tables(body), [[["2.1 모의 시작", "칸"]]])
        moved = body.replace("# 운용\n", "# 새 장\n# 운용\n")
        self.assertIn("3.1 모의 시작 1)을 하고 1 개요·1.1.1 범위 세부 를 본다.", texts(moved))

    def test_value_kinds_checked(self):
        bad = ('"keys": {"{{가}}": 1}', '"keys": {"{{가}}": []}', '"keys": {"{{가}}": ["a", 2]}',
               '"keys": {"{{가}}": ["a\\nb"]}', '"front": {"{{가}}": "x"}', '"front": {"가\\n나": "x"}',
               '"front": ["가"]', '"front": {"가": {"x": 1}}')
        for b in bad:
            with self.assertRaises(wd.SpecError, msg=b):
                wd.parse_spec('```json\n{"template": "t", "out": "o.hwpx", %s}\n```\n# 개요\n' % b)
        meta, _ = wd.parse_spec('```json\n{"template": "t", "out": "o.hwpx", "keys": {"{{가}}": ["a", ""]},'
                                ' "front": {"V0.1": "Ver 1.0", "x": ["", "y"]}}\n```\n# 개요\n')
        self.assertEqual(meta["front"]["x"], ["", "y"])

    def test_plan_each_checks(self):
        m = wd.hp.parse(template_cover_hwpml())
        self.assertEqual(wd.plan_each(m, {"{{발행일자}}": ["a", "b", ""], "V0.2": ""}),
                         {"{{발행일자}}": ["a", "b", ""], "V0.2": [""]})
        for each, single, msg in (({"{{발행일자}}": ["a", "b"]}, {}, "자리 3곳"),
                                  ({"{{과제명}}": ["a", "b"]}, {}, "머리말"),
                                  ({"없는 글자": "x"}, {}, "없다"),
                                  ({"V0": "x", "V0.1": "y"}, {}, "겹친다"),
                                  ({"{{발행일자}}": ["V0.2", "", ""], "V0.2": ""}, {}, "다른 찾을 글자"),
                                  ({"{{검토자}}": ["{{검토자}} 님", ""]}, {}, "자기 글자"),
                                  ({"V0.2": ""}, {"V0.2x": "z"}, "겹친다")):
            with self.assertRaises(wd.SpecError, msg=msg) as e:
                wd.plan_each(m, each, single)
            self.assertIn(msg, str(e.exception))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "tpl").mkdir()
        self.tpl = self.tmp / "tpl" / "common.hwpx"
        self.tpl.write_bytes(b"BMS DocuRay\x03\x01\x00\x00\x00common" + b"\x00" * 32)
        self.src = self.tpl.read_bytes()
        self._root, self._orig = wd.ROOT, hs.HwpSession
        wd.ROOT = self.tmp

    def tearDown(self):
        wd.ROOT, hs.HwpSession = self._root, self._orig
        shutil.rmtree(self.tmp, ignore_errors=True)

    def fake(self, cls=FakeHwp, **kw):
        return cls(docs={"common.hwpx": template_hwpml()}, **kw)

    def run_write(self, fake, spec=SPEC, pictures=True):
        self.f = fake
        meta, blocks = wd.parse_spec(spec)
        d, p, k, _ = make_env(fake)
        with api.HwpxSession(session=self._orig(dispatch=d, pids=p, killer=k, sleep=lambda t: None)) as s:
            return wd.write(s, meta, blocks, log=lambda m: None, pictures=pictures)

    def saves(self):
        return [c for c in self.f.log if c[0] == "SaveAs"]


class TestWrite(Base):
    def test_stale_section_citation_warns_and_saves(self):
        """글자 절 번호·글자 표 번호가 있으면 경고만 하고 저장은 한다(text_checks — 고칠지는 사람이 본다, P-051). 경고 줄은 종류마다
        하나이고 앞 3곳의 인용 글과 까닭을 싣는다(검토 D2-③-03). 맞는 명세(SPEC)에는 고칠 것이 없다."""
        r = self.run_write(self.fake(), spec=SPEC.replace("끝 문단.", "9.9 적용범위 를 본다. 목록은 표 1 과 같다."))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([x["why"] for x in r["text_check"]["section"]], ["없는 절 번호 — '적용범위' 는 1.1"])
        self.assertEqual([x["text"] for x in r["text_check"]["literal"]], ["표 1"])
        sec = [w for w in r["warnings"] if w.startswith("절 인용 1곳이")]
        lit = [w for w in r["warnings"] if w.startswith("글자로 쓴 표·그림 번호 1곳")]
        self.assertTrue(sec and "9.9 적용범위 (없는 절 번호" in sec[0], r["warnings"])
        self.assertTrue(lit and "'표 1'" in lit[0], r["warnings"])
        self.assertEqual(wd.text_check_problems(wd.text_checks(wd.parse_spec(SPEC)[1])), [])

    TWO_CHAPTERS = SPEC.replace("# 관련문서\n끝 문단.\n", "# 관련문서\n## 정부 문서\n끝 문단({{절:정부 문서}}).\n")  # 장마다 하위 절

    def test_heading_numbers_checked_after_writing(self):
        """쓴 뒤 제목마다 한/글 개요 번호(GetHeadingString)를 읽어 명세 차례 번호({{절:}} 인용에 쓴 번호)와 숫자를 모두 견준다
        (P-051, U-32) — 같으면 그대로, 장 번호든 하위 수준만이든 다르면 저장하지 않고(제목 수가 달라도), 못 읽으면 경고만(쪽 번호와
        같은 규칙). 시간초과는 삼키지 않는다. pywin32 가 속성 값으로 주어도 읽는다(검토 D3-③-02·05·09·N05)."""
        r = self.run_write(self.fake(), self.TWO_CHAPTERS)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["headings"], {"headings": [4, 4], "checked": 4, "unread": 0, "mismatch_count": 0,
                                                  "mismatch": [], "structural": 0,
                                                  "samples": [["1", "1."], ["1.1", "1.1."]]})  # 수준마다 하나
        save = [i for i, c in enumerate(self.f.log) if c[0] == "SaveAs"][0]           # 저장할 때 캐럿은 본문 첫 장 제목(D3-②-02)
        self.assertEqual([c for c in self.f.log[:save] if c[0] == "MovePos"][-1], ("MovePos", 0, 5, 0))
        (self.tmp / "out" / "doc.hwpx").unlink()

        class Shifted(FakeHwp):                       # 한/글이 개요 문단 하나를 더 센 꼴 — 장 번호가 모두 하나씩 밀림
            def GetHeadingString(self):
                g = FakeHwp.GetHeadingString(self)
                return re.sub(r"^\d+", lambda m: str(int(m.group(0)) + 1), g) if g else g
        r = self.run_write(self.fake(Shifted), self.TWO_CHAPTERS)
        self.assertFalse(r["ok"])
        self.assertIn("제목 개요 번호가 명세 차례와 다르다(4곳)", r["error"])
        self.assertEqual(r["check"]["headings"]["mismatch"][0], {"title": "개요", "want": "1", "got": "2."})
        self.assertEqual(self.saves(), [])
        r = self.run_write(self.fake(Shifted))                  # {{절:}} 인용이 없는 명세 — 문서는 맞으니 경고하고 저장(D3-①-N01)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue([w for w in r["warnings"] if w.startswith("제목 개요 번호가 명세 차례와 다르다(3곳)") and "저장했다" in w
                         and "작성기의 절 번호 셈" in w], r["warnings"])
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.fake(Shifted), SPEC.replace("## 적용범위", "## (제목 수)"))   # 제목 수 표지와 같은 글자의 제목도
        self.assertEqual((r["ok"], r["check"]["headings"]["structural"]), (True, 0))            # 숫자만 다르면 구조가 아니다(D6-②-04)
        (self.tmp / "out" / "doc.hwpx").unlink()
        cell_ref = SPEC.replace("| 가 | 1.0<br>(시험) |", "| {{절:적용범위}} | 1.0<br>(시험) |")   # 표 칸에만 인용(D4-③-03)
        r = self.run_write(self.fake(Shifted), cell_ref)
        self.assertFalse(r["ok"])
        self.assertIn("{{절:}} 인용 번호가 틀린다", r["error"])
        self.assertEqual(self.saves(), [])

        class NoReset(FakeHwp):                       # 장이 바뀌어도 아래 수준을 0 으로 되돌리지 않는 셈 — 하위 수준만 다름
            def GetHeadingString(self):
                count = [0] * 7
                for i in range(self.caret + 1):
                    a = self._parashape_attrs(self.hwpml, self._para_el(i).get("ParaShape", "0"))
                    if a.get("HeadingType") == "Outline":
                        count[int(a.get("Level", "0"))] += 1
                        if i == self.caret:
                            return ".".join(str(n) for n in count[:int(a.get("Level", "0")) + 1]) + "."
                return ""
        r = self.run_write(self.fake(NoReset), self.TWO_CHAPTERS)
        self.assertFalse(r["ok"])
        self.assertEqual((r["check"]["headings"]["mismatch_count"], r["check"]["headings"]["mismatch"]),
                         (1, [{"title": "정부 문서", "want": "2.1", "got": "2.2."}]))
        self.assertEqual(self.saves(), [])

        wh = wd.written_headings                      # 마지막 제목이 개요 문단으로 써지지 않은 꼴 — 번호는 밀리지 않고 수만 다름
        with mock.patch.object(wd, "written_headings", lambda m, broot: wh(m, broot)[:-1]):
            r = self.run_write(self.fake(), self.TWO_CHAPTERS)
        self.assertFalse(r["ok"])
        self.assertEqual(r["check"]["headings"]["mismatch"], [{"title": "(제목 수)", "want": 4, "got": 3}])
        self.assertEqual(self.saves(), [])
        with mock.patch.object(wd, "written_headings", lambda m, broot: wh(m, broot)[:-1]):
            r = self.run_write(self.fake())                     # 인용이 없어도 제목 수가 다르면 쓴 문서가 틀렸다(D4-②-01)
        self.assertFalse(r["ok"])
        self.assertIn("쓴 제목 수가 다르거나 번호 없는 제목이 있다", r["error"])
        self.assertEqual((r["check"]["headings"]["structural"], self.saves()), (1, []))
        with mock.patch.object(wd, "written_headings", lambda m, broot: (lambda g: g + g[-1:])(wh(m, broot))):
            r = self.run_write(self.fake())                     # 쓴 제목이 명세보다 많아도(템플릿에 남은 개요 문단 꼴) 거절(D7-③-03)
        self.assertEqual((r["ok"], r["check"]["headings"]["structural"], r["check"]["headings"]["mismatch"][:1], self.saves()),
                         (False, 1, [{"title": "(제목 수)", "want": 3, "got": 4}], []))

        class Blank(FakeHwp):                         # 마지막 제목이 번호 없는 제목('') — 인용이 없어도 저장하지 않는다
            def GetHeadingString(self):
                g = FakeHwp.GetHeadingString(self)
                return "" if g == "2." else g
        r = self.run_write(self.fake(Blank))
        self.assertFalse(r["ok"])
        self.assertIn("번호 없는 제목이 있다", r["error"])
        self.assertEqual((r["check"]["headings"]["mismatch"], r["check"]["headings"]["structural"], self.saves()),
                         ([{"title": "관련문서", "want": "2", "got": ""}], 1, []))

        for mark in ("•", " "):                      # 글머리표·빈칸만 — 번호 꼴 글자가 없다: 인용이 없어도 거절(D5F-01·D6-③-06)
            class Mark(FakeHwp):
                def GetHeadingString(self, mark=mark):
                    g = FakeHwp.GetHeadingString(self)
                    return mark if g == "1.1." else g
            r = self.run_write(self.fake(Mark))
            self.assertEqual((r["ok"], r["check"]["headings"]["structural"], self.saves()), (False, 1, []), repr(mark))

        class ShiftBlank(FakeHwp):                    # 장 번호가 모두 밀리고 마지막 제목은 번호 없음 — 거절 글에 번호 없는 제목이 먼저
            def GetHeadingString(self):
                g = FakeHwp.GetHeadingString(self)
                return "" if g == "2." else re.sub(r"^\d+", lambda m: str(int(m.group(0)) + 1), g) if g else g
        r = self.run_write(self.fake(ShiftBlank))
        self.assertFalse(r["ok"])
        self.assertEqual(([(x["title"], x["got"]) for x in r["check"]["headings"]["mismatch"]], r["check"]["headings"]["structural"]),
                         ([("관련문서", ""), ("개요", "2."), ("적용범위", "2.1.")], 1))   # 구조 먼저, 숫자 어긋남도 남는다(D6-③-04)
        self.assertIn("'got': ''", r["error"])                                       # (D5-②-06)

        class Hangul(FakeHwp):                        # 수준 2 번호 꼴이 '가.' — 번호는 있다(숫자가 아닐 뿐): 인용 없으면 경고·저장
            def GetHeadingString(self):
                g = FakeHwp.GetHeadingString(self)
                return "가." if g == "1.1." else g
        r = self.run_write(self.fake(Hangul))
        self.assertTrue(r["ok"], r.get("error"))                                     # (D5-②-01)
        self.assertEqual((r["check"]["headings"]["structural"], r["check"]["headings"]["mismatch_count"]), (0, 1))
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.fake(Hangul), self.TWO_CHAPTERS)                     # 인용이 있으면 거절
        self.assertFalse(r["ok"])
        self.assertIn("{{절:}} 인용 번호가 틀린다", r["error"])

        class PropHeading(FakeHwp):                   # pywin32 늦은 바인딩이 메서드가 아니라 속성 값으로 줄 때
            @property
            def GetHeadingString(self):
                return FakeHwp.GetHeadingString(self)
        r = self.run_write(self.fake(PropHeading), self.TWO_CHAPTERS)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["check"]["headings"]["checked"], r["check"]["headings"]["mismatch_count"]), (4, 0))
        (self.tmp / "out" / "doc.hwpx").unlink()

        class NoHeading(FakeHwp):
            def GetHeadingString(self):
                raise AttributeError("GetHeadingString")
        r = self.run_write(self.fake(NoHeading), self.TWO_CHAPTERS)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["check"]["headings"]["checked"], r["check"]["headings"]["unread"]), (0, 4))
        self.assertTrue([w for w in r["warnings"] if w.startswith("제목 4곳의 개요 번호를 읽지 못했다")], r["warnings"])
        (self.tmp / "out" / "doc.hwpx").unlink()

        class SlowHeading(FakeHwp):
            def GetHeadingString(self):
                raise hs.TimeoutKilled("GetHeadingString 이 넘겼다")
        with self.assertRaises(hs.TimeoutKilled):
            self.run_write(self.fake(SlowHeading))
        self.assertEqual(self.saves(), [])

        class SlowRestore(FakeHwp):                   # 제목을 다 읽은 뒤 캐럿을 되돌리다 시간초과 — 삼키지 않는다(D4-③-05)
            def GetHeadingString(self):
                self.read = getattr(self, "read", 0) + 1
                return FakeHwp.GetHeadingString(self)

            def MovePos(self, move_id, para, pos):
                if getattr(self, "read", 0) >= 3 and move_id == 0:
                    raise hs.TimeoutKilled("MovePos 가 넘겼다")
                return FakeHwp.MovePos(self, move_id, para, pos)
        with self.assertRaises(hs.TimeoutKilled):
            self.run_write(self.fake(SlowRestore))
        self.assertEqual(self.saves(), [])

    def test_main_keeps_text_check_when_hwp_fails(self):
        """main: 명세 검사(text_checks)는 한/글을 띄우기 전에 해 보고에 남는다 — 쓰는 중 한/글 오류로 끝나도 '## 경고'·JSON
        text_check 가 있다(검토 D2-②-04). 인용 오류(없는 절 제목)는 한/글을 띄우지 않고 명세 오류(종료코드 2)."""
        made = []

        class Broken(FakeHwp):
            def GetHeadingString(self):
                raise hs.TimeoutKilled("GetHeadingString 이 넘겼다")

        def factory(**kw):
            made.append(1)
            d, p, k, _ = make_env(self.fake(Broken))
            return self._orig(dispatch=d, pids=p, killer=k, sleep=lambda t: None, **kw)
        hs.HwpSession = factory
        spec = self.tmp / "spec.md"

        def main(*flags, stdout=None):                # 예외가 main 밖으로 새면 오류가 아니라 실패로(끝 코드여야 한다)
            with contextlib.redirect_stdout(stdout or io.StringIO()):
                try:
                    return wd.main([str(spec)] + list(flags))
                except Exception as e:                # noqa: BLE001
                    self.fail("main 밖으로 %s 가 샜다: %s" % (type(e).__name__, e))
        def report(name="doc"):                     # 보고가 없으면 읽기 오류(ERROR)가 아니라 실패로 — 음성 대조는
            p = self.tmp / "out" / (name + ".write_report.md")   # 대상 시험의 FAIL 줄만 센다
            self.assertTrue(p.is_file(), "보고가 없다: %s" % p.name)
            return p.read_text(encoding="utf-8")
        spec.write_text(SPEC.replace("끝 문단.", "9.9 적용범위 를 본다."), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = wd.main([str(spec)])
        self.assertEqual(code, hs.TimeoutKilled.code)
        rep = report()
        self.assertIn("FAIL: TimeoutKilled", rep)
        self.assertIn("## 경고", rep)
        self.assertIn("절 인용 1곳이", rep)
        self.assertIn('"text_check"', rep)
        n = len(made)
        spec.write_text(SPEC.replace("끝 문단.", "{{절:없는 절}} 을 본다."), encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(wd.main([str(spec)]), 2)
        self.assertIn("인용한 절 제목이 없다", out.getvalue())
        self.assertEqual(len(made), n)                                        # 한/글 세션을 만들지 않았다
        rep = report()   # 지난 보고가 남지 않는다(D3-②-03)
        self.assertIn("FAIL: SpecError: 인용한 절 제목이 없다", rep)
        spec.write_text(SPEC.replace("## 적용범위", "## {{절:개요}} 적용범위"), encoding="utf-8")   # parse_spec 오류도 같다
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wd.main([str(spec)]), 2)
        self.assertIn("FAIL: SpecError: 제목·캡션 안에는", report())
        spec.write_text(SPEC.replace("끝 문단.", "{{절:없는 절}} 을 본다."), encoding="utf-8")
        self.assertEqual(main("--no-pictures"), 2)                             # 그림 없이 실행은 그 보고 자리(.nopic)에(D4-③-06)
        self.assertIn("FAIL: SpecError", report("doc.nopic"))
        spec.write_text(SPEC.replace('"out": "out/doc.hwpx"', '"out": "out/other.txt"'), encoding="utf-8")
        self.assertEqual(main(), 2)
        self.assertFalse((self.tmp / "out" / "other.write_report.md").exists())   # .hwpx 가 아니면 보고 자리를 쓰지 않는다
        spec.write_bytes(SPEC.replace("끝 문단.", "끝.").encode("cp949"))        # 메모장 ANSI(CP949) 저장 꼴 — 끝 코드 2·FAIL
        out = io.StringIO()                                                       # 보고(D4-②-04)
        self.assertEqual(main(stdout=out), 2)
        self.assertIn("UTF-8 이 아니다", out.getvalue())
        self.assertIn("FAIL: SpecError: 명세가 UTF-8 이 아니다", report())
        spec.write_bytes(SPEC.replace('"out": "out/doc.hwpx"', '"out": "out/문서.hwpx"').encode("cp949"))
        self.assertEqual(main(), 2)                                               # 한글 out 도 CP949 로 보고 자리를 찾는다(D5-②-02)
        self.assertIn("FAIL: SpecError: 명세가 UTF-8 이 아니다", report("문서"))
        spec.write_bytes(SPEC.replace('"out": "out/doc.hwpx"', '"out": "out/@@.hwpx"').encode("utf-8").replace(b"@@", b"\xff\xfe"))
        self.assertEqual(main(), 2)                                               # 어느 쪽으로도 안 풀리는 out — 깨진 글자 경로에는
        self.assertEqual([x.name for x in (self.tmp / "out").iterdir() if "\ufffd" in x.name], [])   # 보고를 쓰지 않는다

        class Crash(FakeHwp):                         # 쓰는 중 한/글 RPC 가 끊긴 꼴(HwpError 가 아닌 예외) — 지난 OK 보고가 남지 않는다
            def Run(self, action):
                if action == "BreakPara":
                    raise RuntimeError("RPC 서버를 사용할 수 없다")
                return FakeHwp.Run(self, action)

        def crash_factory(**kw):
            d, p, k, _ = make_env(self.fake(Crash))
            return self._orig(dispatch=d, pids=p, killer=k, sleep=lambda t: None, **kw)
        hs.HwpSession = crash_factory
        spec.write_text(SPEC, encoding="utf-8")
        (self.tmp / "out" / "doc.write_report.md").write_text("- 결과 **OK**\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
            wd.main([str(spec)])
        self.assertIn("FAIL: 실행 중", report())   # (D5-②-03)
        self.assertIn('"text_check"', report())                              # 세션 앞에서 쓴 보고(명세 검사 포함)
        hs.HwpSession = factory
        for bad, why in ((('"keys": {"{{문서명}}"', '"keys": ["{{문서명}}"], "x": {"{{문서명}}"'), "keys 는"),   # 머리 꼴이 틀리면 traceback 이
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": "COMSAF 본문",'), "styles 는"),   # 아니라 명세 오류
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"본문": 3},'), "styles 는 {자리"),
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "table_style": 3,'), "table_style 는"),
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {lvl}"},'),
                          "styles.heading 은"),                                                       # (D7-②-03)
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {"},'),
                          "styles.heading 은"),                                                       # 괄호(ValueError)·
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {level[0]}"},'),
                          "styles.heading 은"),                                                       # 형 오류(TypeError)·
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {0}"},'),
                          "styles.heading 은"),                                                       # 번호 자리(IndexError)·
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {level.x}"},'),
                          "styles.heading 은"),                                                       # 속성(AttributeError)
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 1"},'),
                          "styles.heading 에 '{level}' 자리가 없다"),                                 # 자리 없음·이스케이프
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "styles": {"heading": "COMSAF 개요 {{level}}"},'),
                          "styles.heading 에 '{level}' 자리가 없다"),                                 # — 한 스타일(D8-①-01)
                         (('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "table_style": false,'), "table_style 는"),   # 거짓
                         # 값도 글자가 아니면 명세 오류 — null 만 없음(D8-③-03)
                         (('"template": "tpl/common.hwpx"', '"template": 3'), "template 는")):           # (D6-②-02)
            spec.write_text(SPEC.replace(*bad), encoding="utf-8")
            self.assertEqual(main(), 2, why)
            self.assertIn("FAIL: SpecError: 명세 json 의 " + why, report())
        try:                                                                      # table_style null 은 '표 서식 없음'(D7-②-N04)
            nul = wd.parse_spec(SPEC.replace('"out": "out/doc.hwpx",', '"out": "out/doc.hwpx", "table_style": null,'))[0]
        except wd.SpecError as e:
            self.fail("table_style null 을 명세 오류로: %s" % e)
        self.assertIsNone(nul["table_style"])
        for good in ("개요 {level}", "COMSAF 개요 {level:d}"):                    # '{level}' 자리가 있는 다른 이름은 받는다
            try:                                                                  # — 수준마다 다른 스타일(D9-①-01·D8F-01)
                g = wd.parse_spec(SPEC.replace('"out": "out/doc.hwpx",',
                                               '"out": "out/doc.hwpx", "styles": {"heading": "%s"},' % good))[0]
            except wd.SpecError as e:
                self.fail("바른 제목 스타일 %r 을 명세 오류로: %s" % (good, e))
            self.assertEqual(g["styles"]["heading"], good)
        spec.write_text(SPEC.replace("```json\n{", "```json\n[{").replace("\"x\"}}\n```", "\"x\"}}]\n```"), encoding="utf-8")
        self.assertEqual(main(), 2)                                               # 머리가 목록
        spec.write_text(SPEC, encoding="utf-8")
        for name in ("parse_spec", "plan"):                                       # 한/글 앞 예상 밖 예외도 지난 OK 보고가 남지 않는다
            (self.tmp / "out" / "doc.write_report.md").write_text("- 결과 **OK**\n", encoding="utf-8")   # — 명세를 읽은 곧바로
            with mock.patch.object(wd, name, side_effect=RuntimeError("멈췄다")):                         # (D6-②-02·D7-③-06)
                with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(RuntimeError):
                    wd.main([str(spec)])
            self.assertIn("FAIL: 실행 중", report(), name)
        outside = self.tmp / "elsewhere"                                          # out 이 저장소 밖(절대 경로)이면 보고도 쓰지
        spec.write_text(SPEC.replace('"out": "out/doc.hwpx"', '"out": "%s"' % (outside / "doc.hwpx").as_posix()), encoding="utf-8")
        self.assertEqual(main(), 2)                                               # 않는다 — 가드가 깨져도 시험 폴더 안(D3F-04)
        self.assertFalse(outside.exists())

    def test_written_and_checked(self):
        r = self.run_write(self.fake())
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["mismatch"], [])
        self.assertEqual(r["check"]["front_changed_count"], 0)
        self.assertEqual(r["check"]["root_paras"], [6, 6 + 10])               # 캡션은 문단이 아니다(P-049) — 항목 10
        self.assertEqual(r["check"]["captions"], {"written": 2, "mismatch": [], "warn": [], "warn_count": 0,
                                                  "newnum": 2, "newnum_inserted": 2, "newnum_failed": []})
        self.assertEqual(r["check"]["page"], {"body_first": [2, 2], "reads": [[2, 2], [2, 2]]})   # 흉내 쪽: 표지 구역 1쪽,
        # 본문 2쪽(쪽 새 번호 없음) — [KeyIndicator, CurrentPrintPage] 두 길이 같다
        self.assertEqual(r["keys_absent"], ["{{없는키}}"])
        self.assertEqual(r["keys_left"], {"{{문서번호}}": ["s0.p0"], "{{버전}}": ["s0.hd0"]})
        self.assertEqual([x["after"] for x in r["needs"]], ["적용범위", "적용범위"])
        self.assertTrue(r["save"]["protected"] and r["save"]["source_unchanged"])
        self.assertEqual(self.tpl.read_bytes(), self.src)                      # 템플릿은 그대로
        m = wd.hp.parse(self.f.docs["doc.hwpx"])
        tops = wd.top_paras(m)
        self.assertEqual([(b["text"], b.get("level")) for b in tops if b.get("level")],
                         [("개 요", 1), ("적용범위", 2), ("관련문서", 1)])
        t = [b for b in m["body"] if b["type"] == "table"][0]
        self.assertEqual(sorted((c["row"], c["col"], c["text"]) for c in t["cells"]),
                         [(0, 0, "이름"), (0, 1, "버전"), (1, 0, "가"), (1, 1, "1.0\n(시험)")])
        import re as _re                                                  # 칸 스타일: 머리 줄 05, 나머지 07 (HWPML 직접)
        cells = _re.findall(r'<CELL ColAddr="(\d)" RowAddr="(\d)"[^>]*><PARALIST><P ParaShape="\d+" Style="(\d+)"',
                            self.f.docs["doc.hwpx"])
        self.assertEqual({(r, c): STYLES[int(st)] for c, r, st in cells},
                         {("0", "0"): "05_도표내용_항목제목", ("0", "1"): "05_도표내용_항목제목",
                          ("1", "0"): "07_도표내용_본문혼합", ("1", "1"): "07_도표내용_본문혼합"})
        md = (self.tmp / r["md"]).read_text(encoding="utf-8")
        self.assertIn("{{문서번호}}", md)
        self.assertIn("※ 작성 필요: 운용 사이트 정보", md)
        self.assertIn("시험 과제 사용자지침서(v{{버전}})", md)

    def test_main_report(self):
        fake = self.fake()

        def factory(**kw):
            d, p, k, _ = make_env(fake)
            return self._orig(dispatch=d, pids=p, killer=k, sleep=lambda t: None, **kw)
        hs.HwpSession = factory
        spec = self.tmp / "spec.md"
        spec.write_text(SPEC, encoding="utf-8")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = wd.main([str(spec)])
        self.assertEqual(code, 0, out.getvalue())
        rep = (self.tmp / "out" / "doc.write_report.md").read_text(encoding="utf-8")
        self.assertIn("결과 **OK**", rep)
        self.assertTrue("· 본문 첫 쪽 번호(쓰기 전, 쓴 뒤) [2, 2]" in rep, "요약 줄 쪽 번호")
        self.assertIn("- `{{문서번호}}` — `s0.p0`", rep)
        self.assertIn("| 2 | 적용범위 | ※ 작성 필요: 운용 사이트 정보 |", rep)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(wd.main([str(spec)]), 2)                         # 출력이 이미 있으면 사전조건(--force 없음)

    # ------------------------------------------------------------------ 덮어 쓸까요? 자동 응답·글자 크기 (P-038)

    def test_msgbox_auto_yes_while_writing(self):
        """본문을 쓰는 동안만 메시지 상자 자동 응답(예) — 표 뒤 빈 문단에 스타일을 입힐 때 뜨는 '덮어 쓸까요?'가 기다리지 않게."""
        r = self.run_write(self.fake(self.Extra))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["msgbox_auto"])
        self.assertEqual(wd.MSGBOX_YES & 0x00011011, 0x00011011)                   # 확인·확인/취소·예/아니오/취소·예/아니오 → 예
        modes = [(i, c[1]) for i, c in enumerate(self.f.log) if c[0] == "SetMessageBoxMode"]
        self.assertEqual([m for _, m in modes], [wd.MSGBOX_YES, 0])                # 켜고, 원래 값(0)으로 되돌림
        styles = [i for i, c in enumerate(self.f.log) if c == ("Action", "Style")]
        self.assertTrue(modes[0][0] < styles[0] and styles[-1] < modes[1][0])        # 모든 스타일 입히기가 그 사이
        self.assertLess(modes[1][0], [i for i, c in enumerate(self.f.log) if c[0] == "SaveAs"][0])   # 저장 전에 되돌림

    def test_msgbox_restored_on_failure(self):
        class Stuck(FakeHwp):
            def GetPos(self):
                return (3, 0, 0)
        with self.assertRaises(api.EditFailed):
            self.run_write(self.fake(Stuck))
        self.assertEqual([c[1] for c in self.f.log if c[0] == "SetMessageBoxMode"], [wd.MSGBOX_YES, 0])

    def keep_format(self):
        """'덮어 쓸까요?'에 아니오(또는 자동 응답이 안 먹음): 표 뒤 빈 문단에 스타일을 몇 번 입혀도 그 문단 글자 모양(바탕글
        1000)이 남는다 — 같은 스타일 다시 입히기(F-109)로도 못 고치는 경우를 글자 크기 대조가 잡는지."""
        extra = self.Extra

        class KeepFormat(extra):
            def _table_create(self, rows, cols):
                ok = extra._table_create(self, rows, cols)
                self.keep_para = self.cell["para"] + 1                 # 한/글이 표 뒤에 둔 빈 문단
                return ok

            def _apply_style(self, idx):
                keep = self.cell is None and self.caret == getattr(self, "keep_para", None)
                ok = FakeHwp._apply_style(self, idx)
                if keep:
                    el = self._para_el(self.caret)
                    for tx in el.findall("TEXT"):
                        tx.set("CharShape", "0")
                    self._put_para(self.caret, el)
                return ok
        return KeepFormat

    def sized(self, cls=FakeHwp):
        return cls(docs={"common.hwpx": template_sized_hwpml()})

    def test_sizes_match_styles(self):
        r = self.run_write(self.sized(self.Extra))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["size_mismatch"], [])
        self.assertEqual(r["check"]["styles_changed"], [])
        self.assertFalse(any("글자 크기" in w or "스타일 정의" in w for w in r["warnings"]), r["warnings"])

    def test_style_definition_change_is_warned(self):
        """'예'가 문단이 아니라 스타일 정의를 바꾸는 뜻이었다면(U-24 미실측) — 정의가 템플릿과 달라진 스타일을 알린다."""
        extra = self.Extra

        class Redefine(extra):
            def _table_create(self, rows, cols):
                self.hwpml = self.hwpml.replace('Name="03_본문_내용" CharShape="1"', 'Name="03_본문_내용" CharShape="0"', 1)
                return extra._table_create(self, rows, cols)
        r = self.run_write(self.sized(Redefine))
        self.assertTrue(r["ok"], r.get("error"))                                  # 경고만 — 저장은 한다
        self.assertEqual(r["check"]["styles_changed"], ["03_본문_내용"])
        self.assertTrue(any("스타일 정의 1개가 템플릿과 달라졌다" in w for w in r["warnings"]), r["warnings"])

    def test_styles_changed_lists_added_and_removed(self):
        m0 = {"styledefs": [{"name": "가", "para": {}, "char": {"height": "1000"}}, {"name": "나", "para": {}, "char": {}}]}
        m1 = {"styledefs": [{"name": "가", "para": {}, "char": {"height": "1100"}}, {"name": "다", "para": {}, "char": {}}]}
        self.assertEqual(wd.styles_changed(m0, m1), ["가", "+다", "-나"])
        self.assertEqual(wd.styles_changed(m0, m0), [])

    def test_kept_format_after_table_is_warned(self):
        r = self.run_write(self.sized(self.keep_format()))
        self.assertTrue(r["ok"], r.get("error"))                                  # 경고만 — 저장은 한다
        self.assertEqual([x[1:4] for x in r["check"]["size_mismatch"]], [["14_도움말_파란색", ["1000"], "1050"]])
        self.assertTrue(any("글자 크기가 스타일과 다른 문단 1곳" in w for w in r["warnings"]), r["warnings"])

    # ------------------------------------------------------------------ 직접 글자 모양 (P-040, F-109)

    @staticmethod
    def style_rules():
        """실측 14.sum_step4.bat(10-12 17:22) 결과에서 추론한 흉내(F-109): 한/글은 문단 글자 모양이 그 문단 스타일과
        다르면(직접 서식) 다른 스타일을 입혀도 글자 모양을 남기고,
        같은 스타일을 다시 입힐 때만 '덮어 쓸까요?'를 묻는다(메시지 상자 '예'면 스타일 모양으로). 새 문단(BreakPara)은 앞 문단
        글자 모양을 잇고, 표를 만들면 표 뒤에 표 문단 스타일 + 다른 글자 모양(1000)의 빈 문단을 둔다."""
        class StyleRules(FakeHwp):
            prompts = ()

            def _table_create(self, rows, cols):
                ok = FakeHwp._table_create(self, rows, cols)
                anchor = self._para_el(self.cell["para"])
                e = self._top_paras()[self.cell["para"]][1]
                self.hwpml = self.hwpml[:e] + '<P ParaShape="%s" Style="%s"><TEXT CharShape="0"/></P>' % (
                    anchor.get("ParaShape", "0"), anchor.get("Style", "0")) + self.hwpml[e:]
                return ok

            def _apply_style(self, idx):
                if self.cell is not None or (self.selection and self.selection[0] == "text"):
                    return FakeHwp._apply_style(self, idx)
                el = self._para_el(self.caret)
                st = self._head_items(self.hwpml, "STYLE")
                cur = el.get("Style", "0")
                texts = el.findall("TEXT")
                now = texts[0].get("CharShape") if texts else None
                if now is None or now == self._attr(st.get(cur, ""), "CharShape"):
                    return FakeHwp._apply_style(self, idx)              # 직접 서식 없음 — 스타일 그대로
                if str(idx) == cur:                                     # 같은 스타일 다시 → '덮어 쓸까요?'
                    self.prompts = tuple(self.prompts) + (cur,)
                    return FakeHwp._apply_style(self, idx) if self.msgbox_mode & 0x10000 else True
                new = st.get(str(idx))
                if new is None:
                    return False
                el.set("Style", str(idx))
                el.set("ParaShape", self._attr(new, "ParaShape") or "0")
                self._put_para(self.caret, el)                          # 다른 스타일 → 글자 모양은 남는다
                return True

            def _break_inherit(self):
                texts = self._para_el(self.caret).findall("TEXT")
                cs = texts[-1].get("CharShape", "0") if texts else "0"
                FakeHwp._run_break(self)
                el = self._para_el(self.caret)
                for tx in el.findall("TEXT"):
                    tx.set("CharShape", cs)
                self._put_para(self.caret, el)

            _CARET_RUNS = dict(FakeHwp._CARET_RUNS, BreakPara=lambda h: h._break_inherit())
        return StyleRules

    def test_direct_format_cleared_by_same_style(self):
        """F-109: 이미 있던 문단(템플릿 빈 문단·표 뒤 빈 문단)에는 같은 스타일을 한 번 더 입혀 직접 글자 모양을 지운다."""
        r = self.run_write(self.style_rules()(docs={"common.hwpx": template_leftover_hwpml()}))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["reused_empty_para"])
        self.assertEqual(r["check"]["size_mismatch"], [])
        self.assertGreaterEqual(len(self.f.prompts), 2)                     # 템플릿 빈 문단 + 표 뒤 빈 문단 — 자동 '예'

    def test_direct_format_kept_without_reapply(self):
        """F-109 실측 재현(흉내가 맞는지): 다시 입히지 않으면 템플릿 빈 문단의 12pt 가 첫 항목부터 이어지고 표 뒤 자리 표시도 남는다."""
        orig = wd.apply_style_clean
        wd.apply_style_clean = lambda s, idx, name, new, clean=True: wd.apply_style(s, idx, name)
        try:
            r = self.run_write(self.style_rules()(docs={"common.hwpx": template_leftover_hwpml()}))
        finally:
            wd.apply_style_clean = orig
        self.assertTrue(r["ok"], r.get("error"))                                # 경고만
        bad = {x[0]: x[2] for x in r["check"]["size_mismatch"]}
        self.assertEqual(bad.get("s1.p1"), ["1200"])                           # 첫 항목(제목 '적용범위')
        self.assertIn(["1000"], bad.values())                                  # 표 뒤 빈 문단에 쓴 '그림 삽입 필요'(1050)

    # ------------------------------------------------------------------ 자리별 값·표지 글자 (P-037, D-036)

    def cover(self, cls=FakeHwp, **kw):
        return cls(docs={"common.hwpx": template_cover_hwpml()}, **kw)

    def test_each_values_by_place(self):
        """같은 키라도 자리마다 다른 값(표지 날짜·이력서 1행·2행), 결재란 검토자2 비우기, 양식 예시 글자 지우기."""
        r = self.run_write(self.cover(), EACH_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["front_changed_count"], 0)
        self.assertEqual(r["each"], {"{{발행일자}}": 3, "{{검토자}}": 2, "{{결재일자}}": 3, "V0.1": 1, "V0.2": 1,
                                     "ooo 기능 추가": 1})
        self.assertEqual(sum(1 for c in self.f.log if c == ("Action", "RepeatFind")), 11)
        self.assertEqual(r["keys_left"], {})
        m = wd.hp.parse(self.f.docs["doc.hwpx"])
        texts = [t for _, _, t in wd.hp.iter_locations(m)]
        self.assertIn("2026.10.", texts)
        self.assertIn("작성자 : 갑 일자 : 2026. 10.\n검토자1 : 을 일자 : 2026. 10.\n검토자2 :  일자 : ", texts)
        hist = [b for b in m["body"] if b["type"] == "table"][1]
        self.assertEqual(sorted((c["row"], c["col"], c["text"]) for c in hist["cells"] if c["row"]),
                         [(1, 0, "2026.10.15."), (1, 1, " Ver 1.0"), (1, 2, "신규 제정"), (2, 0, ""), (2, 1, ""), (2, 2, "")])
        self.assertIn('<CHAR> </CHAR>', self.f.docs["doc.hwpx"])          # 지운 ' V0.2' 칸: 공백만 — 파서는 빈 칸으로 본다
        self.assertIn("화면은 그림 1 과 같다.", texts)

    def test_each_count_mismatch_stops_before_edit(self):
        spec = EACH_SPEC.replace('["2026.10.", "2026.10.15.", ""]', '["2026.10.", "2026.10.15."]')
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(self.cover(), spec)
        self.assertIn("자리 3곳", str(e.exception))
        self.assertNotIn(("Action", "RepeatFind"), self.f.log)
        self.assertEqual(self.saves(), [])

    def test_each_not_found_not_saved(self):
        with self.assertRaises(api.EditFailed):
            self.run_write(self.cover(fail_actions=("RepeatFind",)), EACH_SPEC)
        self.assertEqual(self.saves(), [])

    def test_each_misplaced_is_caught(self):
        class Twice(FakeHwp):                                             # 찾은 자리에 값이 두 번 들어가면(가정 어긋남)
            def _find_insert(self, text):
                FakeHwp._find_insert(self, text)
                return FakeHwp._find_insert(self, text)
        self.assert_fails(self.run_write(self.cover(Twice), EACH_SPEC), "앞부분 글자")

    def test_each_header_skipped_by_find(self):
        """머리말의 키는 다시 찾기에 안 걸린다(가정) — 자리별 값은 본문만, 머리말은 AllReplace 로."""
        r = self.run_write(self.cover(), EACH_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertIn("시험 과제 사용자지침서(v1.0)", self.f.docs["doc.hwpx"])

    # ------------------------------------------------------------------ 음성대조

    def assert_fails(self, r, text):
        self.assertFalse(r["ok"])
        self.assertIn(text, r.get("error", ""))
        self.assertEqual(self.saves(), [])

    def test_text_not_inserted_is_caught(self):
        self.assert_fails(self.run_write(self.fake(fail_actions=("InsertText",))), "쓴 블록이 명세와 다르다")

    def test_cell_move_ignored_is_caught(self):
        f = self.fake()
        f.ignore = ("TableRightCell",)
        self.assert_fails(self.run_write(f), "쓴 블록이 명세와 다르다")

    def test_style_not_applied_is_caught(self):
        self.assert_fails(self.run_write(self.fake(fail_actions=("Style",))), "쓴 블록이 명세와 다르다")

    def test_front_change_is_caught(self):
        class Spill(FakeHwp):                                             # 쓰는 동안 표지 글자가 바뀌면
            def Run(self, name):
                out = FakeHwp.Run(self, name)
                if name == "BreakPara" and self.hwpml:
                    self.hwpml = self.hwpml.replace("<CHAR>사용자지침서</CHAR>", "<CHAR>사용자 지침서</CHAR>", 1)
                return out
        self.assert_fails(self.run_write(self.fake(Spill)), "앞부분 글자")

    def test_stuck_in_table_is_caught(self):
        class Stuck(FakeHwp):
            def GetPos(self):
                return (3, 0, 0)
        with self.assertRaises(api.EditFailed):
            self.run_write(self.fake(Stuck))
        self.assertEqual(self.saves(), [])

    class Extra(FakeHwp):
        """실측 P-027: 표를 만들면 한/글이 표 문단 뒤에 빈 문단을 하나 더 둔다."""
        def _table_create(self, rows, cols):
            ok = FakeHwp._table_create(self, rows, cols)
            e = self._top_paras()[self.cell["para"]][1]
            self.hwpml = self.hwpml[:e] + '<P ParaShape="0" Style="0"><TEXT CharShape="0"/></P>' + self.hwpml[e:]
            return ok

    def test_empty_paragraph_after_table_is_reused(self):
        r = self.run_write(self.fake(self.Extra))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(o["type"], o["extra"]) for o in r["objects"]],
                         [("table", True), ("picture", False)])               # GetPos: 표 문단 + 1 의 처음 (그림 = 자리 표시)
        self.assertEqual(r["check"]["empty_after_object"], [])                # 다음 항목을 그 빈 문단에 썼다
        self.assertEqual(r["check"]["root_paras"], [6, 6 + 10])

    def test_empty_after_table_tolerated_without_getpos(self):
        class Blind(self.Extra):
            def GetPos(self):
                raise AttributeError("GetPos")
        r = self.run_write(self.fake(Blind))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(len(r["check"]["empty_after_object"]), 1)
        self.assertEqual([(f["at"], f["kind"], f["error"]) for f in r["check"]["captions"]["newnum_failed"]],  # 자리를
                         [("표 1", "Table", "개체 문단 자리를 모른다(GetPos 실패)"),        # 모르면 새 번호를 넣지 않고
                          ("그림 1", "Figure", "개체 문단 자리를 모른다(GetPos 실패)")])    # 캡션 번호로 알린다(P-050)
        self.assertEqual((r["check"]["captions"]["newnum"], r["check"]["captions"]["newnum_inserted"]), (0, 0))
        self.assertTrue(any("빈 문단 1개" in w for w in r["warnings"]), r["warnings"])

    def test_unexpected_empty_paragraph_is_caught(self):
        class Gap(FakeHwp):                                               # 제목 뒤에 빈 문단이 끼면(글자 대조로는 안 보임)
            def _apply_style(self, idx):
                ok = FakeHwp._apply_style(self, idx)
                if str(idx) == str(STYLES.index("COMSAF 개요 2")):
                    e = self._top_paras()[self.caret][1]
                    self.hwpml = self.hwpml[:e] + '<P ParaShape="0" Style="0"><TEXT CharShape="0"/></P>' + self.hwpml[e:]
                return ok
        r = self.run_write(self.fake(Gap))
        self.assert_fails(r, "문단 배치가 명세와 다르다")
        self.assertEqual(r["check"]["mismatch"], [])
        self.assertIn(["s1.p2", "empty"], [list(x) for x in r["check"]["layout"]])

    PIC_SPEC = SPEC.replace("![로그인 화면](원본 s0.p3)", '![로그인 화면](img/a.png "100x50")')

    def pic(self):
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)

    def test_picture_inserted(self):
        self.pic()
        r = self.run_write(self.fake(), self.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["plan"]["pictures"], r["plan"]["figures"], r["check"]["pictures"]), (1, 0, 1))
        self.assertIn(("InsertPicture", "a.png", 1, 100.0, 50.0), self.f.log)
        self.assertEqual([x["text"] for x in r["needs"]], ["※ 작성 필요: 운용 사이트 정보"])   # 그림 자리 표시 없음
        m = wd.hp.parse(self.f.docs["doc.hwpx"])
        pic = [c for c in m["ctrls"] if c["tag"] == "PICTURE"]
        self.assertEqual(len(pic), 1)
        blocks = {b["id"]: b for b in wd.hp.iter_blocks(m["body"])}
        self.assertEqual([(blocks[x]["type"], blocks[x]["text"]) for x in pic[0]["blocks"]],
                         [("caption", "그림 1 로그인 화면")])                  # 캡션은 그림 개체의 한/글 캡션(P-049)
        ps = {b["id"]: b for b in wd.top_paras(m)}
        n = int(pic[0]["at"].split(".p")[1])
        self.assertEqual(ps["s1.p%d" % (n + 1)]["text"], "※ 작성 필요: 운용 사이트 정보")   # 캡션 글자 문단이 없다
        self.assertEqual([r_["kind"] for r_ in m["roots"] if r_["id"] == pic[0]["at"]], ["object"])
        caps = wd.written_captions(self.f.docs["doc.hwpx"], 5)
        self.assertEqual([(c["tag"], c["text"], c["style"], c["side"], c["num"]) for c in caps],
                         [("TABLE", "표 1 소프트웨어 목록", "04_도표그림_제목", "Top", ["Table"]),
                          ("PICTURE", "그림 1 로그인 화면", "04_도표그림_제목", "Bottom", ["Figure"])])
        self.assertEqual([o.get("caption", {}).get("moved") for o in r["objects"]], [True, True])

    def test_picture_placeholder_when_off_or_missing(self):
        self.pic()
        r = self.run_write(self.fake(), self.PIC_SPEC, pictures=False)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertIn("※ 그림 삽입 필요: 로그인 화면 (출처: img/a.png)", [x["text"] for x in r["needs"]])
        self.assertNotIn("InsertPicture", [c[0] for c in self.f.log])
        self.assertEqual(r["check"]["captions"]["written"], 1)                # 표 캡션만 한/글 캡션, 그림 캡션은 글자 문단
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.fake(), self.PIC_SPEC.replace("img/a.png", "img/none.png"))   # 파일 없음 → 자리 표시 그림
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["plan"]["pictures"], r["plan"]["figures"], r["check"]["pictures"]), (1, 1, 1))
        self.assertIn(("InsertPicture", wd.PLACEHOLDER.name, 1, 100.0, 50.0), self.f.log)   # 명세 크기 그대로
        self.assertIn("※ 그림 삽입 필요: 로그인 화면 (출처: img/none.png)", [x["text"] for x in r["needs"]])
        self.assertEqual(r["check"]["captions"]["written"], 2)
        self.assertEqual((r["plan"]["placeholders"], [o["placeholder"] for o in r["objects"] if o["type"] == "picture"]),
                         (1, [True]))                                    # 자리 표시 그림은 따로 센다(검토 P-049 D1-②-04)
        import datetime
        wd.write_report(r, self.tmp / "rep.md", datetime.datetime(2026, 10, 16))
        self.assertIn("· 그림 1(그중 자리 표시 그림 1) ·", (self.tmp / "rep.md").read_text(encoding="utf-8"))
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.fake(), self.PIC_SPEC)                    # 파일 있음 → 자리 표시 그림 아님
        self.assertEqual((r["plan"]["placeholders"], [o["placeholder"] for o in r["objects"] if o["type"] == "picture"]),
                         (0, [False]))

    def test_picture_failure_is_caught(self):
        self.pic()
        f = self.fake()
        f.picture_mode = "fail"
        with self.assertRaises(api.EditFailed):
            self.run_write(f, self.PIC_SPEC)
        self.assertEqual(self.saves(), [])
        f = self.fake()
        f.picture_mode = "ghost"                                          # 개체는 돌려주지만 문서에 없음 → 캡션을 못 단다
        with self.assertRaises(api.EditFailed) as e:
            self.run_write(f, self.PIC_SPEC)
        self.assertIn("캡션을 달지 못했다", str(e.exception))
        self.assertEqual(self.saves(), [])

        class Lost(FakeHwp):                                              # 쓴 뒤 그림이 사라지면(내보내기에서 다른 개체)
            def GetTextFile(self, fmt, opt):
                x = FakeHwp.GetTextFile(self, fmt, opt)
                return x.replace("<PICTURE>", "<OLE>").replace("</PICTURE>", "</OLE>") if self.saved == {} else x
        self.assert_fails(self.run_write(self.fake(Lost), self.PIC_SPEC), "그림 수 0 (기대 1)")

    def test_empty_paragraph_after_picture_is_reused(self):
        class PicExtra(FakeHwp):                                          # 그림 뒤에도 빈 문단이 생기는 경우(실측 전, P-029)
            def InsertPicture(self, *a):
                out = FakeHwp.InsertPicture(self, *a)
                e = self._top_paras()[self.caret][1]
                self.hwpml = self.hwpml[:e] + '<P ParaShape="0" Style="0"><TEXT CharShape="0"/></P>' + self.hwpml[e:]
                return out
        self.pic()
        r = self.run_write(self.fake(PicExtra), self.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(o["type"], o["extra"]) for o in r["objects"]], [("table", False), ("picture", True)])
        self.assertEqual(r["check"]["empty_after_object"], [])                # 다음 항목(작성 필요 메모)을 그 빈 문단에
        self.assertEqual(r["check"]["root_paras"], [6, 6 + 9])                # 그림 파일이 있어 메모·캡션 문단 없음(P-049)

    def test_template_with_body_is_refused(self):
        tpl = template_hwpml().replace("</SECTION></BODY>", P("본문 글") + "</SECTION></BODY>")
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(FakeHwp(docs={"common.hwpx": tpl}))
        self.assertIn("마지막 문단이 첫 장 제목", str(e.exception))
        tbl = ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><TABLE ColCount="1" RowCount="1"><ROW>'
               '<CELL ColAddr="0" RowAddr="0" RowSpan="1" ColSpan="1"><PARALIST>%s</PARALIST></CELL></ROW></TABLE>'
               '<CHAR/></TEXT></P>' % P("칸"))
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(FakeHwp(docs={"common.hwpx": template_hwpml().replace("</SECTION></BODY>",
                                                                              tbl + "</SECTION></BODY>")}))
        self.assertIn("첫 장 제목 뒤에 표", str(e.exception))

    def test_trailing_empty_paragraph_is_reused(self):
        """공통 템플릿은 본문을 지우고 남은 빈 문단이 제목 뒤에 있다(F-095 그릇) — 첫 항목을 그 문단에 쓴다."""
        tpl = template_hwpml().replace("</SECTION></BODY>", '<P ParaShape="0" Style="0"><TEXT CharShape="0"/></P>'
                                       "</SECTION></BODY>")
        r = self.run_write(FakeHwp(docs={"common.hwpx": tpl}))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["reused_empty_para"])
        self.assertEqual(r["check"]["root_paras"], [7, 7 + 10 - 1])
        ps = wd.top_paras(wd.hp.parse(self.f.docs["doc.hwpx"]))
        self.assertEqual([(b["id"], b["text"]) for b in ps[5:7]], [("s1.p0", "개 요"), ("s1.p1", "적용범위")])

    def test_template_without_matching_heading(self):
        with self.assertRaises(wd.SpecError):
            self.run_write(self.fake(), SPEC.replace("# 개요\n## 적용범위", "# 소개\n## 적용범위"))

    def test_missing_style_is_refused(self):
        spec = SPEC.replace('"keys"', '"styles": {"need": "없는 스타일"}, "keys"')
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(self.fake(), spec)
        self.assertIn("없는 스타일", str(e.exception))
        self.assertNotIn(("Run", "BreakPara"), self.f.log)                 # 쓰기 전에 거절 (반쯤 쓴 문서 없음)



# ---------------------------------------------------------------------- 표 서식 (P-040, D-042)

TS_SPEC = """# 표 서식 명세
```json
{"template": "tpl/common.hwpx", "out": "out/doc.hwpx", "table_style": "tpl/table_style.json",
 "keys": {"{{문서명}}": "사용자지침서", "{{문서영문명}}": "Software User Manual", "{{과제명}}": "시험 과제"}}
```
# 개요
## 적용범위
표: 소프트웨어 목록
| 이름 | 버전 |
|---|---|
| 가 | 1.0 |
| 나 | 2.0 |
표: 장비 목록
| 식별자 | 장비명 | 비고 |
|---|---|---|
| MBS | 유무인 복합 전장환경 모의기 | |
| TCS | 시험운용 통제 시스템 | 시험운용통제 PC 와 프로젝터 전원을 함께 다루는 긴 설명 글 |
끝 문단.
"""
K, N, GRAY = ["Solid", "0.4mm"], ["Solid", "0.12mm"], [214, 214, 214]
HEAD, CENTER, MIXED = "05_도표내용_항목제목", "06_도표내용_본문중앙", "07_도표내용_본문혼합"


def _cf(L, R, T, B, fill, style, header=False):
    return {"L": L, "R": R, "T": T, "B": B, "fill": fill, "style": style, "header": header}


def table_style_file():
    """참고 표 둘: '소프트웨어 목록'(3×2, 칸마다 — (1,1) 만 회색이라 자리별로는 못 만든다), '용어'(기본, 자리별·제목 셀)."""
    grid = [[_cf(K, N, K, K, GRAY, HEAD), _cf(N, K, K, K, GRAY, HEAD)],
            [_cf(K, N, K, N, None, CENTER), _cf(N, K, K, N, GRAY, MIXED)],
            [_cf(K, N, N, K, None, CENTER), _cf(N, K, N, K, None, MIXED)]]
    lines, fills, styles = wd.ts.classes_of(grid)
    return {"source": "참고.hwpx", "default": "용어", "alias": {},
            "tables": {"소프트웨어 목록": {"ref_id": "s2.t0", "size": [3, 2], "cells": grid, "classes": lines, "fills": fills,
                                       "styles": styles, "header_cells": False, "inside_margin": [538, 538, 0, 0],
                                       "col_ratio": [0.3, 0.7], "width_mm": 140.0},
                       "용어": {"ref_id": "s2.t7", "size": [11, 3], "cells": None,
                              "classes": {"top": K, "bottom": K, "left": K, "right": K, "inner_h": N, "inner_v": N,
                                          "head_bottom": K},
                              "fills": {"head_first": GRAY, "head": GRAY, "first": None, "body": None},
                              "styles": {"head_first": HEAD, "head": HEAD, "first": CENTER, "body": CENTER},
                              "header_cells": True, "inside_margin": [141, 141, 141, 141], "col_ratio": [0.1, 0.2, 0.7],
                              "width_mm": 147.0}}}


TS_MORE = """표: 비고 목록
| 가 | 나 | 다 |
| 라 | 마 | 바 |
표: 넷째 표
| 항목 | 값 |
|---|---|
| 하나 | 1 |
"""


class TestTableStyle(Base):
    def setUp(self):
        super().setUp()
        import json
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(table_style_file(), ensure_ascii=False),
                                                          encoding="utf-8")

    def doc_tables(self):
        x = self.f.docs["doc.hwpx"]
        root, _, elems = wd.ts.load(x)
        bfs = wd.ts.border_fills(root)
        _, _, style = wd.ts.shapes(root)
        out = []
        for tid, tbl, t in elems:
            if not tid.startswith("s1."):
                continue
            cells = {}
            for cell in tbl.iter("CELL"):
                p0 = cell.find("PARALIST/P")
                cells[(int(cell.get("RowAddr")), int(cell.get("ColAddr")))] = dict(
                    bfs.get(cell.get("BorderFill")) or {}, header=cell.get("Header"), width=cell.get("Width"),
                    style=style.get(p0.get("Style")), text="".join(cell.itertext()))
            im = tbl.find("INSIDEMARGIN")
            out.append({"id": tid, "cells": cells, "margin": [im.get(k) for k in ("Left", "Right", "Top", "Bottom")]})
        return out

    def plain(self, cls=FakeHwp, **kw):
        f = cls(docs={"common.hwpx": template_hwpml()}, **kw)
        f.strict_block = True                                  # 셀 블록을 풀지 않으면 오류(Cancel 확인)
        f.after_table_para = True                              # 실측 F-100: 표 뒤 빈 문단(다음 항목은 거기에)
        return f

    def test_applied_and_checked(self):
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["check"]["table_format"], r["check"]["table_format_failed"]), ([], []))
        self.assertEqual(r["table_style"]["table_width"], 43370)                     # 템플릿 쪽 설정으로 셈 = 실측 G1
        self.assertEqual([(x["label"], x["caption"], x["ref"], x["mode"]) for x in r["table_style"]["tables"]],
                         [("표 1", "소프트웨어 목록", "소프트웨어 목록", "exact"), ("표 2", "장비 목록", "용어", "class")])
        self.assertEqual([o["format"]["done"] for o in r["objects"]],
                         [{"center": True, "anchor_margin": None, "width": True, "border": True, "header": None, "margin": True,
                           "caption": True},
                          {"center": True, "anchor_margin": None, "width": True, "border": True, "header": True, "margin": True,
                           "caption": True}])
        self.assertEqual([x["inside_margin"] for x in r["table_style"]["tables"]],
                         [[538, 538, 500, 500], [141, 141, 500, 500]])          # 위·아래 = 칸 글자 크기 1000 의 반(P-048)
        t1, t2 = self.doc_tables()
        c = t1["cells"]                                                       # 칸마다 그대로(참고 표와 같은 3×2)
        self.assertEqual((c[0, 0]["L"], c[0, 0]["T"], c[0, 0]["R"], c[0, 0]["fill"]),
                         ("Solid 0.4mm", "Solid 0.4mm", "Solid 0.12mm", "rgb(214,214,214)"))
        self.assertEqual((c[1, 1]["fill"], c[2, 1]["fill"], c[1, 0]["style"], c[1, 1]["style"]),
                         ("rgb(214,214,214)", "없음", CENTER, MIXED))
        self.assertEqual(t1["margin"], ["538", "538", "500", "500"])             # 왼·오는 참고 표 값, 위·아래 반 칸
        metrics = wd.ts.style_metrics(wd.hp.parse(template_hwpml())["styledefs"])
        want = wd.ts.fit_table([["이름", "버전"], ["가", "1.0"], ["나", "2.0"]], [[HEAD, HEAD], [CENTER, MIXED], [CENTER, MIXED]],
                               metrics, 43370, 538 + 538)                  # 칸 글자 폭 + 공백 2칸 + 칸 안 여백(P-041)
        self.assertEqual((want["capped"], want["how"]), (False, "estimate"))
        self.assertEqual(r["objects"][0]["format"]["col_hu"], want["widths"])
        self.assertEqual([[int(c[r, k]["width"]) for k in range(2)] for r in range(3)], [want["widths"]] * 3)   # 모든 줄 같은 경계
        self.assertLess(sum(want["widths"]), 43370 // 2)                     # 짧은 글 표 — 본문 폭을 채우지 않는다
        self.assertEqual({v["header"] for v in c.values()}, {None})                # 제목 셀 없음 — 건드리지 않음
        c = t2["cells"]                                                       # 기본 서식 자리별(3×3)
        self.assertEqual([c[0, k]["header"] for k in range(3)], ["true"] * 3)
        self.assertEqual((c[0, 0]["B"], c[1, 1]["T"], c[1, 1]["B"], c[2, 2]["R"], c[2, 2]["B"]),
                         ("Solid 0.4mm", "Solid 0.4mm", "Solid 0.12mm", "Solid 0.4mm", "Solid 0.4mm"))
        self.assertEqual([c[1, k]["style"] for k in range(3)], [CENTER, CENTER, MIXED])   # 긴 글 칸만 본문혼합
        self.assertEqual(t2["margin"], ["141", "141", "500", "500"])
        w2 = r["objects"][1]["format"]["col_hu"]
        self.assertEqual([[int(c[r, k]["width"]) for k in range(3)] for r in range(3)], [w2] * 3)
        fit2 = r["objects"][1]["format"]["fit"]                               # 긴 설명 글 칸이 있어 본문 폭을 넘음
        self.assertEqual((fit2["capped"], sum(w2)), (True, 43370))
        self.assertEqual(w2[:2], fit2["need"][:2])                            # 짧은 칸은 줄바꿈 없는 너비 그대로
        self.assertLess(w2[2], fit2["need"][2])                               # 긴 글 칸만 줄어 줄바꿈
        self.assertEqual(r["check"]["align_mismatch"], [])

    def test_widths_at_creation_not_per_cell(self):
        """칸 너비는 표를 만들 때 ColWidth 로(값 = 칸 너비 - 칸 안 좌우 여백 1020) — 칸마다 너비를 바꾸지 않는다(검토 P-040 1).
        표 속성(안 여백)은 그 표 마지막 글자 뒤, 칸 테두리/배경은 그 칸 글자 뒤(PoC A1~A3 차례)."""
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertFalse([c for c in self.f.log if c[0] == "TableProperty" and "Width" in c[2]])
        made = [c[1:] for c in self.f.log if c[0] == "TableCreateWidth"]       # 표마다 만들기 값(표 너비, ColWidth)
        self.assertEqual(made, [(sum(o["format"]["col_hu"]), [w - wd.CELL_LR for w in o["format"]["col_hu"]])
                                for o in r["objects"]])                       # 표 너비 = 칸 너비 합(좁은 표는 본문 폭보다 좁게)
        self.assertLess(made[0][0], 43370)
        self.assertEqual(self.f.HParameterSet.HTableCreation.WidthType, 2)
        log = self.f.log
        creates = [i for i, c in enumerate(log) if c == ("Action", "TableCreate")]
        closes = [next(i for i in range(a, len(log)) if log[i] == ("Run", "CloseEx")) for a in creates]   # 칸 → 표 밖
        for a, b in zip(creates, closes):                                     # 표마다
            seg = log[a:b]
            last_text = max(i for i, c in enumerate(seg) if c == ("Action", "InsertText"))
            tprops = [i for i, c in enumerate(seg) if c[:2] == ("TableProperty", "table")]
            self.assertEqual(len(tprops), 1)
            self.assertGreater(tprops[0], last_text)                          # 안 여백은 마지막 칸 글자 뒤
        a, b = creates[0], closes[0]                                          # 표 1: 칸마다 글자 → 테두리 차례
        kinds = [c[1] for c in log[a:b] if c in (("Action", "InsertText"), ("Action", "CellBorderFill"))]
        self.assertEqual(kinds, ["InsertText", "CellBorderFill"] * 6)

    def test_text_safe_with_uneven_rows_fake(self):
        """검토 P-040 1 재현용 흉내: 셀 블록 너비는 그 칸만 바뀌고(G1), 아래 칸 이동은 위치로(G2), 첫 칸 왼쪽은 윗줄 끝으로(G3).
        칸마다 너비를 바꾸며 채우면 다음 줄 글자가 엉뚱한 칸에 들어갔다 — 지금은 너비를 만들 때 정해 글자가 제자리."""
        class Geo(FakeHwp):
            def _cell_move(self, dr, dc):
                el = self._para_el(self.cell["para"])
                tbl, _ = self._cell_ps(el)
                rows, cols = int(tbl.get("RowCount")), int(tbl.get("ColCount"))
                r, c = self.cell["r"], self.cell["c"]
                ws = lambda k: [int(x.get("Width")) for x in tbl.findall("ROW")[k].findall("CELL")]   # noqa: E731
                if dr == 1 and r + 1 < rows:
                    x0, acc, target = sum(ws(r)[:c]), 0, cols - 1
                    for k, w in enumerate(ws(r + 1)):
                        if acc <= x0 < acc + w:
                            target = k
                            break
                        acc += w
                    self.cell.update(r=r + 1, c=target, p=0)
                    return
                if dc < 0 and c == 0 and r > 0:
                    self.cell.update(r=r - 1, c=cols - 1, p=0)
                    return
                return FakeHwp._cell_move(self, dr, dc)
        r = self.run_write(self.plain(Geo), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["mismatch"], [])
        t1 = self.doc_tables()[0]["cells"]
        self.assertEqual([[t1[i, k]["text"] for k in range(2)] for i in range(3)], [["이름", "버전"], ["가", "1.0"], ["나", "2.0"]])

    def test_mismatch_is_warned(self):
        class NoBorder(FakeHwp):
            def _cell_border_fill(self, ps):                    # 실행은 됐다고 하고 아무것도 안 바꾼다
                return True
        r = self.run_write(self.plain(NoBorder), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))                                # 서식은 경고만 — 저장은 한다
        self.assertGreater(r["check"]["table_format_count"], 0)
        self.assertEqual({b["table"] for b in r["check"]["table_format"]}, {"표 1", "표 2"})
        self.assertTrue(any("표 서식이 계획과 다른 칸" in w for w in r["warnings"]), r["warnings"])

    def test_colwidth_meaning_differs_is_warned(self):
        """ColWidth 가 칸 안 여백을 뺀 값이 아니라 칸 너비라면(U-26 미실측) 칸이 1020 씩 좁다 — 대조가 너비를 알린다."""
        class CellMeaning(FakeHwp):
            colwidth_mode = "cell"
        r = self.run_write(self.plain(CellMeaning), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        what = {b["what"] for b in r["check"]["table_format"]}
        self.assertEqual(what, {"너비"})

    def test_failure_recorded_text_written(self):
        r = self.run_write(self.plain(fail_actions={"CellBorderFill"}), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["mismatch"], [])                            # 글자는 끝까지
        self.assertEqual([(f["table"], f["kind"], f["at"]) for f in r["check"]["table_format_failed"]],
                         [("표 1", "border", [0, 0]), ("표 2", "border", [0, 0])])
        self.assertEqual([o["format"]["done"]["border"] for o in r["objects"]], [False, False])
        self.assertEqual([o["format"]["done"]["width"] for o in r["objects"]], [True, True])   # 다른 종류는 그대로
        self.assertEqual(r["check"]["table_format"], [])                        # 실패한 종류는 대조하지 않는다(소음 없음)
        self.assertTrue(any("표 서식을 입히지 못한 곳 2 — 칸 테두리/배경: ['표 1', '표 2']" in w for w in r["warnings"]),
                        r["warnings"])

    def test_dialog_failure_keeps_borders_and_widths(self):
        """표/셀 속성(제목 셀·안 여백)이 실패해도 칸 너비(만들 때)와 테두리/배경은 입힌다 — 서식 종류마다 따로."""
        r = self.run_write(self.plain(fail_actions={"TablePropertyDialog"}), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(f["table"], f["kind"], f["at"]) for f in r["check"]["table_format_failed"]],
                         [("표 1", "margin", "표"), ("표 1", "caption", "표"), ("표 2", "header", [0, 0]),
                          ("표 2", "margin", "표"), ("표 2", "caption", "표")])        # 캡션 자리도 같은 동작(P-049)
        self.assertEqual([o["format"]["done"] for o in r["objects"]],
                         [{"center": True, "anchor_margin": None, "width": True, "border": True, "header": None, "margin": False,
                           "caption": False},
                          {"center": True, "anchor_margin": None, "width": True, "border": True, "header": False,
                           "margin": False, "caption": False}])
        self.assertEqual(r["check"]["table_format"], [])
        self.assertEqual((r["check"]["captions"]["mismatch"], r["check"]["captions"]["warn"]), ([], []))   # 실패한 자리는
        #                                                                     대조하지 않는다 — 캡션 글자·스타일은 맞다
        self.assertEqual(self.doc_tables()[0]["cells"][0, 0]["L"], "Solid 0.4mm")

    def test_width_creation_failure_falls_back(self):
        """칸 너비를 정해 만들기가 실패하면(ColWidth 배열 못 만듦) 예전처럼 만들고(같은 너비) 나머지 서식·글자는 그대로."""
        r = self.run_write(self.plain(fail_actions={"CreateItemArray"}), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(f["table"], f["kind"]) for f in r["check"]["table_format_failed"]],
                         [("표 1", "width"), ("표 2", "width")])
        self.assertEqual(sum(1 for c in self.f.log if c == ("Action", "TableCreate")), 2)   # 표마다 한 번만 만들었다
        self.assertEqual([o["format"]["col_hu"] for o in r["objects"]], [None, None])
        self.assertEqual(r["check"]["table_format"], [])
        self.assertEqual(self.doc_tables()[0]["cells"][0, 0]["width"], str(43370 // 2))

    def test_no_page_setup_no_widths(self):
        x = template_hwpml().replace(SECDEF_BODY, "<SECDEF/>")
        r = self.run_write(FakeHwp(docs={"common.hwpx": x}), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertIsNone(r["table_style"]["table_width"])
        self.assertEqual([o["format"]["done"]["width"] for o in r["objects"]], [None, None])
        self.assertTrue(any("쪽 설정" in w for w in r["warnings"]), r["warnings"])
        self.assertEqual(r["check"]["table_format"], [])

    def test_kind_switched_off_after_three_tables(self):
        """한 종류가 표 셋에서 실패하면 그 종류만 나머지 표에서 끈다 — 다른 종류는 계속(검토 P-040 2)."""
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")
        r = self.run_write(self.plain(fail_actions={"CellBorderFill"}), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["format"]["done"]["border"] for o in r["objects"]], [False, False, False, "off"])
        self.assertEqual([o["format"]["done"]["width"] for o in r["objects"]], [True] * 4)
        self.assertEqual(r["check"]["table_format_off"], {"칸 테두리/배경": "표 4"})
        self.assertEqual(sum(1 for c in self.f.log if c == ("Action", "CellBorderFill")), 3)   # 표 4 에서는 부르지 않음
        self.assertTrue(any("나머지 표에서 끈 서식: 칸 테두리/배경(표 4부터)" in w for w in r["warnings"]), r["warnings"])
        self.assertEqual(r["check"]["table_format"], [])

    def test_kind_not_switched_off_before_three(self):
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")
        r = self.run_write(self.plain(), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["table_format_off"], {})
        self.assertEqual([o["format"]["done"]["border"] for o in r["objects"]], [True] * 4)

    def test_no_header_line_keeps_first_row_body(self):
        """명세 표에 제목 줄(|---|)이 없으면 자리별 서식에서 첫 줄도 본문 — 제목 배경·스타일·제목 셀 없음(검토 P-040 5)."""
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")
        r = self.run_write(self.plain(), spec)
        self.assertTrue(r["ok"], r.get("error"))
        c = self.doc_tables()[2]["cells"]                                     # '비고 목록' 2×3, 제목 줄 없음 → 기본 '용어'
        self.assertEqual([c[0, k]["header"] for k in range(3)], [None] * 3)
        self.assertEqual({c[0, k]["fill"] for k in range(3)}, {"없음"})
        self.assertEqual([c[0, k]["style"] for k in range(3)], [CENTER] * 3)
        self.assertEqual((c[0, 0]["B"], c[1, 0]["T"]), ("Solid 0.12mm", "Solid 0.12mm"))   # 제목 줄 아래 굵은 선 없음
        c = self.doc_tables()[3]["cells"]                                     # '넷째 표' 제목 줄 있음
        self.assertEqual(([c[0, k]["header"] for k in range(2)], c[0, 0]["B"]), (["true"] * 2, "Solid 0.4mm"))

    def test_no_style_file_fit_and_center_only(self):
        """서식 파일이 없어도 칸 너비 맞춤·가운데 정렬은 한다(P-045, F-153 — P-041 지시를 모든 표에). 테두리·배경·제목 셀은
        손대지 않는다(한/글 기본). 안 여백은 위·아래만 칸 글자 크기 반, 왼·오는 한/글 기본 510(P-048 — 모든 표).
        칸 스타일은 예전처럼 제목 줄 05 · 나머지 07."""
        r = self.run_write(self.plain(), TS_SPEC.replace('"table_style": "tpl/table_style.json",', ""))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertFalse([c for c in self.f.log if c == ("Action", "CellBorderFill")])
        self.assertEqual([c for c in self.f.log if c[0] == "TableProperty"],
                         [("TableProperty", "table", ["CellMarginBottom", "CellMarginLeft", "CellMarginRight",
                                                      "CellMarginTop"])] * 2)   # 표/셀 속성은 안 여백만(셀 블록 없음)
        self.assertEqual((r["table_style"]["file"], r["table_style"]["table_width"]), (None, 43370))
        self.assertEqual([(x["mode"], x["ref"], x["inside_margin"]) for x in r["table_style"]["tables"]],
                         [("fit", None, [510, 510, 500, 500])] * 2)
        self.assertEqual([o["format"]["done"] for o in r["objects"]],
                         [{"center": True, "anchor_margin": None, "width": True, "border": None, "header": None,
                           "margin": True, "caption": True}] * 2)
        made = [c[1:] for c in self.f.log if c[0] == "TableCreateWidth"]
        self.assertEqual(made, [(sum(o["format"]["col_hu"]), [w - wd.CELL_LR for w in o["format"]["col_hu"]])
                                for o in r["objects"]])
        metrics = wd.ts.style_metrics(wd.hp.parse(template_hwpml())["styledefs"])
        want = wd.ts.fit_table([["이름", "버전"], ["가", "1.0"], ["나", "2.0"]], [[HEAD, HEAD], [MIXED, MIXED], [MIXED, MIXED]],
                               metrics, 43370, wd.ts.DEFAULT_INSIDE_LR)       # 안 여백은 한/글 기본(510+510)으로 셈
        self.assertEqual(r["objects"][0]["format"]["col_hu"], want["widths"])
        self.assertEqual(self.anchor_aligns(), ["Center", "Center"])
        self.assertEqual((r["check"]["table_format"], r["check"]["table_format_failed"]), ([], []))
        t1 = self.doc_tables()[0]
        self.assertEqual({(v.get("L"), v["header"]) for v in t1["cells"].values()}, {(None, None)})   # 테두리·제목 셀 그대로
        self.assertEqual(t1["margin"], ["510", "510", "500", "500"])             # 한/글 기본 141 → 반 칸(P-048)
        self.assertEqual([t1["cells"][0, 0]["style"], t1["cells"][1, 0]["style"]], [HEAD, MIXED])
        (self.tmp / "out" / "doc.hwpx").unlink()
        try:                                                                       # table_style null 도 서식 파일 없음 — 끝까지
            nul = self.run_write(self.plain(), TS_SPEC.replace('"table_style": "tpl/table_style.json",', '"table_style": null,'))
        except Exception as e:                                                     # noqa: BLE001 — 예외도 실패로(D8-③-01)
            self.fail("table_style null 에서 %s: %s" % (type(e).__name__, e))
        self.assertTrue(nul["ok"], nul.get("error"))
        self.assertEqual((nul["table_style"]["file"], nul["table_style"]["table_width"]), (None, 43370))

    def test_no_style_file_checks_and_warnings(self):
        """서식 파일이 없는 표도 쓴 뒤 대조(가운데 정렬)와 쪽 설정 경고를 한다(P-045)."""
        spec = TS_SPEC.replace('"table_style": "tpl/table_style.json",', "")
        f = self.plain()
        f.ignore = set(getattr(f, "ignore", ()) or ()) | {"ParagraphShapeAlignCenter"}
        r = self.run_write(f, spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(b["table"], b["what"]) for b in r["check"]["table_format"]],
                         [("표 1", "가운데 정렬"), ("표 2", "가운데 정렬")])
        self.assertTrue(any(w.startswith("표 서식이 계획과 다른 칸 2곳") for w in r["warnings"]), r["warnings"])
        (self.tmp / "out" / "doc.hwpx").unlink()
        x = template_hwpml().replace(SECDEF_BODY, "<SECDEF/>")
        r = self.run_write(FakeHwp(docs={"common.hwpx": x}), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["format"]["done"]["width"] for o in r["objects"]], [None, None])
        self.assertTrue(any("쪽 설정" in w for w in r["warnings"]), r["warnings"])

    def test_no_style_file_header_rows_and_style_names(self):
        """서식 파일이 없는 표의 칸 스타일: 제목 줄(|---|)이 없으면 첫 줄도 본문(td), 명세 styles 의 th/td 를 따른다(검토 P-045
        D1-③-01·04)."""
        spec = TS_SPEC.replace('"table_style": "tpl/table_style.json",', '"styles": {"td": "%s"},' % CENTER)
        r = self.run_write(self.plain(), spec.replace("끝 문단.\n", TS_MORE + "끝 문단.\n"))
        self.assertTrue(r["ok"], r.get("error"))
        t = self.doc_tables()
        self.assertEqual([t[0]["cells"][0, 0]["style"], t[0]["cells"][1, 0]["style"]], [HEAD, CENTER])
        self.assertEqual({t[2]["cells"][0, k]["style"] for k in range(3)}, {CENTER})       # '비고 목록' — 제목 줄 없음
        self.assertEqual([t[3]["cells"][0, 0]["style"], t[3]["cells"][1, 0]["style"]], [HEAD, CENTER])
        self.assertEqual(r["check"]["table_format"], [])

    def test_report_with_style_file_but_no_table(self):
        """서식 파일이 있으면 표가 없어도 보고에 표 서식 절(표 0개) — 서식 파일도 표도 없으면 절이 없다(P-040 과 같게)."""
        spec = TS_SPEC[:TS_SPEC.index("표: 소프트웨어 목록")] + "끝 문단.\n"
        r = self.run_write(self.plain(), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["table_style"]["file"], r["table_style"]["tables"]), ("tpl/table_style.json", []))
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.plain(), spec.replace('"table_style": "tpl/table_style.json",', ""))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertNotIn("table_style", r)

    def test_unmatched_table_fit_only(self):
        """서식 파일이 있어도 고를 서식이 없는 표(캡션이 없고 default 도 없음)는 칸 너비 맞춤·가운데만(P-045)."""
        import json
        sf = table_style_file()
        sf["default"] = None
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(x["mode"], x["ref"]) for x in r["table_style"]["tables"]],
                         [("exact", "소프트웨어 목록"), ("fit", None)])
        self.assertEqual(sum(1 for c in self.f.log if c == ("Action", "CellBorderFill")), 6)     # 표 1 칸 여섯만
        self.assertEqual([o["format"]["done"]["width"] for o in r["objects"]], [True, True])
        self.assertEqual(self.anchor_aligns(), ["Center", "Center"])
        self.assertEqual(r["check"]["table_format"], [])

    def test_shared_edges_keep_thicker_line(self):
        """참고 표의 맞닿은 변이 칸마다 다르면(참고본 표 6·7: 머리 줄 아래 0.4mm · 둘째 줄 위 0.15mm) 한/글은 나중에 입힌 칸
        값으로 덮는다(실측 P-045 — 흉내 shared_edges). 계획에서 굵은 선으로 맞춰 머리 줄 아래 0.4mm 가 남고 경고가 없다(F-155)."""
        import json
        sf = table_style_file()
        g = sf["tables"]["소프트웨어 목록"]["cells"]
        g[1][0]["T"] = g[1][1]["T"] = ["Solid", "0.15mm"]
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["tables"][0]["shared_edges"], 2)
        c = self.doc_tables()[0]["cells"]
        self.assertEqual([(c[0, k]["B"], c[1, k]["T"]) for k in range(2)], [("Solid 0.4mm", "Solid 0.4mm")] * 2)
        self.assertEqual(r["check"]["table_format"], [])

    def test_missing_style_file_refused(self):
        (self.tmp / "tpl" / "table_style.json").unlink()
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(self.plain(), TS_SPEC)
        self.assertIn("표 서식 파일이 없다", str(e.exception))

    def test_broken_style_file_refused(self):
        """JSON 이 깨졌거나 tables 가 없으면 손대기 전에 명세 오류(종료코드 2) — 추적 출력으로 끝나지 않게(검토 P-040 9)."""
        f = self.tmp / "tpl" / "table_style.json"
        for text, msg in (('{"tables": ', "표 서식 파일을 읽지 못했다"), ('{"default": "용어"}', "표 서식 파일이 맞지 않다")):
            f.write_text(text, encoding="utf-8")
            with self.assertRaises(wd.SpecError) as e:
                self.run_write(self.plain(), TS_SPEC)
            self.assertIn(msg, str(e.exception))
            self.assertFalse([c for c in self.f.log if c[0] == "Open"])           # 템플릿도 열지 않았다

    # ------------------------------------------------------------------ 칸 너비 맞춤·가운데 정렬 (P-041, D-044)

    def anchor_aligns(self):
        """쓴 문서에서 표마다 그 표가 든 문단의 정렬."""
        import xml.etree.ElementTree as ET
        x = self.f.docs["doc.hwpx"]
        root = ET.fromstring(re.sub(r"^\ufeff?\s*<\?xml[^>]*\?>", "", wd.hp.clean(x)[0], count=1))
        up = {c: p for p in root.iter() for c in p}
        aligns = {ps.get("Id"): ps.get("Align") for ps in root.iter("PARASHAPE")}
        return [aligns.get(up[up[t]].get("ParaShape")) for t in root.iter("TABLE")]

    def test_tables_centered(self):
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(self.anchor_aligns(), ["Center", "Center"])
        self.assertFalse([b for b in r["check"]["table_format"] if b["what"] == "가운데 정렬"])

    def test_center_not_applied_is_warned(self):
        """가운데 정렬(Run — 결과를 돌려주지 않음)이 먹지 않으면 쓴 뒤 대조가 알린다."""
        f = self.plain()
        f.ignore = set(getattr(f, "ignore", ()) or ()) | {"ParagraphShapeAlignCenter"}
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(b["table"], b["what"]) for b in r["check"]["table_format"] if b["what"] == "가운데 정렬"],
                         [("표 1", "가운데 정렬"), ("표 2", "가운데 정렬")])

    def test_wide_table_capped_short_columns_kept(self):
        """칸 글자가 길어 본문 폭을 넘는 표: 합 = 본문 폭, 짧은 칸은 필요한 너비 그대로, 긴 글 칸만 줄어 줄바꿈."""
        long_ = "가나다라마바사아자차카타파하 " * 6
        spec = TS_SPEC.replace("끝 문단.\n", "표: 긴 표\n| 번호 | 설명 |\n|---|---|\n| 1 | %s |\n끝 문단.\n" % long_)
        r = self.run_write(self.plain(), spec)
        self.assertTrue(r["ok"], r.get("error"))
        f = r["objects"][2]["format"]
        self.assertTrue(f["fit"]["capped"])
        self.assertEqual(sum(f["col_hu"]), 43370)
        self.assertEqual(f["col_hu"][0], f["fit"]["need"][0])
        self.assertLess(f["col_hu"][1], f["fit"]["need"][1])
        self.assertEqual(len(f["fit"]["maxmin"]), 2)                       # 다듬기 전 너비·표 높이(줄) 어림도 보고(P-041 2차)
        self.assertEqual(sorted(f["fit"]["lines"]), ["after", "before"])
        self.assertLessEqual(f["fit"]["lines"]["after"][0], f["fit"]["lines"]["before"][0])

    def test_measure_used_and_reported(self):
        """Windows 에서는 템플릿 스타일 글꼴로 글자 폭을 잰다 — 잰 폭이 너비에 쓰이고, 보고에 글꼴·잼 여부, 끝나면 닫는다."""
        class M:
            faces, closed = {}, False

            def __call__(self, text, face, bold=False):
                if face is None:
                    return None
                self.faces[face] = True
                return 0.5 * len(text)

            def close(self):
                M.closed = True
        cs = ('<CHARSHAPE Id="%d" Height="%d"><FONTID Hangul="0" Latin="0"/><RATIO Hangul="100" Latin="100"/>'
              '<CHARSPACING Hangul="0" Latin="0"/></CHARSHAPE>')
        x = template_hwpml().replace("<STYLELIST>", '<FACENAMELIST><FONTFACE Lang="Hangul" Count="1"><FONT Id="0" Name="한글체"/>'
                                     '</FONTFACE><FONTFACE Lang="Latin" Count="1"><FONT Id="0" Name="라틴체"/></FONTFACE>'
                                     '</FACENAMELIST><CHARSHAPELIST>%s%s</CHARSHAPELIST><STYLELIST>' % (cs % (0, 1000),
                                                                                                    cs % (1, 1200)), 1)
        x = re.sub(r'<STYLE Id="(\d+)" Name="', r'<STYLE Id="\1" CharShape="0" Name="', x)
        x = x.replace('CharShape="0" Name="%s"' % HEAD, 'CharShape="1" Name="%s"' % HEAD)   # 제목 칸 스타일만 12pt
        orig = wd.ts.gdi_measure
        wd.ts.gdi_measure = lambda: M()
        try:
            f = FakeHwp(docs={"common.hwpx": x})
            f.strict_block = True
            r = self.run_write(f, TS_SPEC)
        finally:
            wd.ts.gdi_measure = orig
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["measure"], "gdi")
        self.assertEqual({o["format"]["fit"]["how"] for o in r["objects"]}, {"gdi"})
        self.assertEqual(r["table_style"]["fonts"][HEAD]["measured"], {"한글체": True, "라틴체": True})
        self.assertTrue(M.closed)
        need = r["objects"][0]["format"]["fit"]["need"]       # 제목 '이름'(05, 12pt) 2글자 = 0.5em×2 — 공백 2칸도 12pt 로
        self.assertEqual(need[0], int(__import__("math").ceil(1200 * 1.02 + 2 * 600 + 1076)))

    def test_shared_edges_left_right(self):
        """좌우로 맞닿은 변도 계획에서 맞춘다 — 맞춤을 끄면 흉내(나중에 입힌 칸이 이김 — 좌우는 흉내의 가정)에서 왼 칸 오른쪽
        0.4mm 가 오른 칸 왼쪽 0.12mm 로 덮여 경고(검토 P-045 D1-③-05)."""
        import json
        sf = table_style_file()
        g = sf["tables"]["소프트웨어 목록"]["cells"]
        g[1][0]["R"] = K                                                       # (1,1) 왼쪽은 0.12mm 그대로
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["tables"][0]["shared_edges"], 1)
        c = self.doc_tables()[0]["cells"]
        self.assertEqual((c[1, 0]["R"], c[1, 1]["L"]), ("Solid 0.4mm", "Solid 0.4mm"))
        self.assertEqual(r["check"]["table_format"], [])
        (self.tmp / "out" / "doc.hwpx").unlink()
        orig = wd.ts.shared_edges
        wd.ts.shared_edges = lambda cells: 0
        try:
            r = self.run_write(self.plain(), TS_SPEC)
        finally:
            wd.ts.shared_edges = orig
        self.assertEqual([(b["at"], b["what"], b["got"]) for b in r["check"]["table_format"]],
                         [([1, 0], "R", "Solid 0.12mm")])

    def test_fake_shares_edge_with_unformatted_neighbour(self):
        """흉내: 칸 테두리를 입히면 아직 안 입힌 아래·오른쪽 이웃의 맞닿은 변도 바뀐다(실측 P-045 — 나중 칸이 위 칸 아래선을
        바꾼 것과 같은 동작의 앞쪽). 첫 칸만 입히고 나머지 칸은 실패하게 해 본다."""
        class FirstOnly(FakeHwp):
            def _cell_border_fill(self, ps):
                self.bf_calls = getattr(self, "bf_calls", 0) + 1
                return FakeHwp._cell_border_fill(self, ps) if self.bf_calls == 1 else False
        r = self.run_write(self.plain(FirstOnly), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        c = self.doc_tables()[0]["cells"]
        self.assertEqual((c[1, 0]["T"], c[0, 1]["L"]), ("Solid 0.4mm", "Solid 0.12mm"))   # (0,0) 의 아래·오른쪽 값
        self.assertEqual((c[1, 0]["B"], c[0, 1]["R"]), ("Solid 0.12mm", "Solid 0.12mm"))   # 이웃의 다른 변은 표 기본(실측 G1)
        self.assertNotIn("B", c[1, 1])                                         # 맞닿지 않은 칸은 그대로

    def test_shared_edge_missing_side_filled(self):
        """참고 칸 한쪽 변 값이 없으면(못 읽음) 다른 쪽 값을 두 칸에 — 값이 없는 칸을 나중에 입히면 그 변은 기본값(흉내: 실선
        0.12mm)으로 위 칸 아래선을 덮는다(검토 P-045 D1-②-04)."""
        import json
        sf = table_style_file()
        g = sf["tables"]["소프트웨어 목록"]["cells"]
        g[1][0]["T"] = None                                                    # 위 칸 (0,0) 아래는 0.4mm
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        c = self.doc_tables()[0]["cells"]
        self.assertEqual((c[0, 0]["B"], c[1, 0]["T"]), ("Solid 0.4mm", "Solid 0.4mm"))
        self.assertEqual(r["check"]["table_format"], [])

    def test_bold_style_fonts_reported(self):
        """진하게 칸 스타일도 잰 글꼴을 보고 measured 에 True 로 — GdiMeasure 는 진하게를 '글꼴 (진하게)' 키로 적는다(검토 P-045
        D1-②-02)."""
        class M:
            faces = {}

            def __call__(self, text, face, bold=False):
                self.faces["%s%s" % (face, " (진하게)" if bold else "")] = True
                return 0.5 * len(text)

            def close(self):
                pass
        cs = '<CHARSHAPE Id="0" Height="1000"><FONTID Hangul="0" Latin="0"/><BOLD/></CHARSHAPE>'
        x = template_hwpml().replace("<STYLELIST>", '<FACENAMELIST><FONTFACE Lang="Hangul" Count="1"><FONT Id="0" Name="한글체"/>'
                                     '</FONTFACE><FONTFACE Lang="Latin" Count="1"><FONT Id="0" Name="라틴체"/></FONTFACE>'
                                     '</FACENAMELIST><CHARSHAPELIST>%s</CHARSHAPELIST><STYLELIST>' % cs, 1)
        x = re.sub(r'<STYLE Id="(\d+)" Name="', r'<STYLE Id="\1" CharShape="0" Name="', x)
        orig = wd.ts.gdi_measure
        wd.ts.gdi_measure = lambda: M()
        try:
            f = FakeHwp(docs={"common.hwpx": x})
            f.strict_block = True
            r = self.run_write(f, TS_SPEC)
        finally:
            wd.ts.gdi_measure = orig
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["fonts"][HEAD]["measured"], {"라틴체": True, "한글체": True})

    def test_fake_reproduces_real_shared_edge_warning(self):
        """가짜 한/글의 맞닿은 변 흉내가 실측(10-14 15.sum_step5.bat — 표 6·7 '[0, k] B want Solid 0.4mm got Solid 0.15mm')을
        그대로 낸다: 계획에서 변을 맞추지 않으면(맞춤 끔) 머리 줄 아래가 둘째 줄 위 0.15mm 로 덮여 경고."""
        import json
        sf = table_style_file()
        g = sf["tables"]["소프트웨어 목록"]["cells"]
        g[1][0]["T"] = g[1][1]["T"] = ["Solid", "0.15mm"]
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        orig = wd.ts.shared_edges
        wd.ts.shared_edges = lambda cells: 0
        try:
            r = self.run_write(self.plain(), TS_SPEC)
        finally:
            wd.ts.shared_edges = orig
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(b["table"], b["at"], b["what"], b["want"], b["got"]) for b in r["check"]["table_format"]],
                         [("표 1", [0, k], "B", "Solid 0.4mm", "Solid 0.15mm") for k in range(2)])

    def test_language_fonts_reported(self):
        """보고에 칸 스타일의 언어별 글꼴·글꼴 종류·장평·자간·상대 크기(P-045) — 잰 글꼴은 measured(그 언어 글자가 없으면 None).
        '·'(언어 후보 여럿)는 기호 글꼴로도 잰다."""
        class M:
            faces = {}

            def __call__(self, text, face, bold=False):
                self.faces[face] = face != "한양신명조"                   # HFT 글꼴은 GDI 로 못 잰다(실측 P-045)
                return 0.5 * len(text) if self.faces[face] else None

            def close(self):
                pass
        langs = ("Hangul", "Latin", "Hanja", "Japanese", "Other", "Symbol", "User")
        faces = {"Hangul": ("한양신명조", "hft"), "Latin": ("라틴체", "ttf"), "Symbol": ("기호체", "ttf")}
        ff = "".join('<FONTFACE Lang="%s" Count="1"><FONT Id="0" Name="%s" Type="%s"/></FONTFACE>'
                     % ((k,) + faces.get(k, ("한양신명조", "hft"))) for k in langs)
        cs = ('<CHARSHAPE Id="0" Height="1000"><FONTID %s/><RATIO %s/><CHARSPACING %s/><RELSIZE %s/></CHARSHAPE>'
              % tuple(" ".join('%s="%s"' % (k, v(k)) for k in langs) for v in (
                  lambda k: 0, lambda k: 100 if k == "Latin" else 85, lambda k: -3, lambda k: 100)))
        x = template_hwpml().replace("<STYLELIST>", "<FACENAMELIST>%s</FACENAMELIST><CHARSHAPELIST>%s</CHARSHAPELIST>"
                                     "<STYLELIST>" % (ff, cs), 1)
        x = re.sub(r'<STYLE Id="(\d+)" Name="', r'<STYLE Id="\1" CharShape="0" Name="', x)
        spec = TS_SPEC.replace("| 가 | 1.0 |", "| 가·나 | 1.0 |")
        orig = wd.ts.gdi_measure
        wd.ts.gdi_measure = lambda: M()
        try:
            f = FakeHwp(docs={"common.hwpx": x})
            f.strict_block = True
            r = self.run_write(f, spec)
        finally:
            wd.ts.gdi_measure = orig
        self.assertTrue(r["ok"], r.get("error"))
        fonts = r["table_style"]["fonts"]
        self.assertEqual(fonts[CENTER]["slots"]["latin"], {"face": "라틴체", "type": "ttf", "ratio": 100.0, "spacing": -3.0,
                                                           "relsize": 100.0})
        self.assertEqual(fonts[CENTER]["slots"]["symbol"]["face"], "기호체")
        self.assertEqual({k: v["ratio"] for k, v in fonts[CENTER]["slots"].items() if k != "latin"},
                         {k: 85.0 for k in ("hangul", "hanja", "japanese", "other", "symbol", "user")})
        self.assertEqual(fonts[CENTER]["measured"], {"기호체": True, "라틴체": True, "한양신명조": False})
        self.assertEqual(r["table_style"]["measure"], "gdi")                    # 하나라도 글꼴로 잼

    def test_center_after_table_filled(self):
        """가운데 정렬은 표를 다 채우고 나온 뒤 표가 든 문단으로 가서(MovePos) 한다 — 칸과 표 뒤 빈 문단은 그 전에 생겨
        정렬을 이어받지 않는다(검토 P-041 M3)."""
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        log = self.f.log
        for o in r["objects"]:
            i = log.index(("MovePos", 0, o["anchor"][1], 0))
            self.assertEqual(log[i - 1], ("Run", "CloseEx"))
            self.assertEqual(log[i + 1], ("Run", "ParagraphShapeAlignCenter"))
        self.assertEqual([o["extra"] for o in r["objects"]], [True, True])    # 표 뒤 빈 문단에 다음 항목
        x = self.f.docs["doc.hwpx"]                                          # 칸·표 뒤 문단은 가운데 정렬 문단 모양이 아니다
        center_ids = set(re.findall(r'<PARASHAPE Id="(\d+)"[^>]*Align="Center"', x))
        cells = re.findall(r'<CELL[^>]*>.*?</CELL>', x, re.S)
        self.assertTrue(cells)
        self.assertFalse([cl for cl in cells if set(re.findall(r'ParaShape="(\d+)"', cl)) & center_ids])
        self.assertEqual(r["check"]["align_mismatch"], [])

    def test_anchor_margins_reset_and_cap(self):
        """표 문단 스타일(03)에 여백이 있으면 표 너비 상한에서 빼고, 가운데 정렬 뒤 그 문단 여백을 0 으로 한다(검토 P-041 M4)."""
        x = template_hwpml().replace('<PARASHAPE Id="0" HeadingType="None" Level="0"/>',
                                     '<PARASHAPE Id="0" HeadingType="None" Level="0"><PARAMARGIN Left="2000" Right="0" '
                                     'Indent="500"/></PARASHAPE>', 1)
        f = FakeHwp(docs={"common.hwpx": x})
        f.strict_block = True
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["anchor_style"], {"m_left": 2000, "m_right": 0, "m_indent": 500})
        self.assertEqual([o["format"]["avail"] for o in r["objects"]], [43370 - 2500] * 2)
        self.assertEqual([o["format"]["done"]["anchor_margin"] for o in r["objects"]], [True, True])
        ps = self.f.HParameterSet.HParaShape
        self.assertEqual((ps.LeftMargin, ps.RightMargin, ps.Indentation), (0, 0, 0))
        self.assertEqual(sum(1 for c in self.f.log if c == ("Action", "ParagraphShape")), 2)

    def test_anchor_margin_failures_keep_centering(self):
        """표 문단 여백 0(ParagraphShape — 항목 이름 실측 전)이 표 셋에서 실패해도 가운데 정렬은 계속한다 — 종류가 다르다."""
        x = template_hwpml().replace('<PARASHAPE Id="0" HeadingType="None" Level="0"/>',
                                     '<PARASHAPE Id="0" HeadingType="None" Level="0"><PARAMARGIN Left="2000" Right="0" '
                                     'Indent="0"/></PARASHAPE>', 1)
        f = FakeHwp(docs={"common.hwpx": x}, fail_actions={"ParagraphShape"})
        f.strict_block, f.after_table_para = True, True
        r = self.run_write(f, TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n"))
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["format"]["done"]["anchor_margin"] for o in r["objects"]], [False, False, False, "off"])
        self.assertEqual([o["format"]["done"]["center"] for o in r["objects"]], [True] * 4)

    def test_align_leak_is_warned(self):
        """한/글이 가운데 정렬을 표 뒤 문단까지 옮기고 스타일을 입혀도 남으면(흉내) 문단 정렬 대조가 알린다 — 대조군은 없음."""
        x = template_hwpml().replace('<PARASHAPE Id="0" HeadingType="None" Level="0"/>',
                                     '<PARASHAPE Id="0" HeadingType="None" Level="0" Align="Justify"/>'
                                     '<PARASHAPE Id="9" HeadingType="None" Level="0" Align="Center"/>', 1)
        cover = '<P ParaShape="0" Style="1"><TEXT CharShape="0"><CHAR>{{문서명}}'   # 표지 문단은 직접 가운데(템플릿 앞부분)
        self.assertIn(cover, x)
        x = x.replace(cover, cover.replace('ParaShape="0"', 'ParaShape="9"'), 1)   # — 쓴 문단이 아니라 대조하지 않는다(C14)

        class Leak(FakeHwp):
            leak = False

            def _table_create(self, rows, cols):                # 실측 F-100: 표 뒤 빈 문단
                ok = FakeHwp._table_create(self, rows, cols)
                a = self._para_el(self.cell["para"])
                e = self._top_paras()[self.cell["para"]][1]
                self.hwpml = self.hwpml[:e] + '<P ParaShape="%s" Style="%s"><TEXT CharShape="0"/></P>' % (
                    a.get("ParaShape", "0"), a.get("Style", "0")) + self.hwpml[e:]
                return ok

            def _run_align(self, align):
                FakeHwp._run_align(self, align)
                if self.leak and self.caret + 1 < len(self._top_paras()):          # 다음 문단까지(흉내)
                    self.caret += 1
                    FakeHwp._run_align(self, align)
                    self.caret -= 1

            def _apply_style(self, idx):
                ps = self._para_el(self.caret).get("ParaShape") if self.cell is None else None
                ok = FakeHwp._apply_style(self, idx)
                if self.leak and ps is not None and self._parashape_attrs(self.hwpml, ps).get("Align") == "Center":
                    el = self._para_el(self.caret)
                    el.set("ParaShape", ps)                    # 스타일을 입혀도 문단 모양이 남는 경우(흉내)
                    self._put_para(self.caret, el)
                return ok
        f = Leak(docs={"common.hwpx": x})
        f.strict_block = True
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["align_mismatch"], [])
        (self.tmp / "out" / "doc.hwpx").unlink()
        f = Leak(docs={"common.hwpx": x})
        f.strict_block, f.leak = True, True
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["check"]["align_mismatch"])
        self.assertEqual({a[2] for a in r["check"]["align_mismatch"]}, {"Center"})
        self.assertTrue(any("문단 정렬이 스타일과 다른 문단" in w for w in r["warnings"]), r["warnings"])

    def test_margin_off_uses_default_margins_for_widths(self):
        """안 여백이 표 셋에서 실패해 꺼지면 다음 표 칸 너비는 기본 안 여백(510+510)으로 센다 — 실제 칸 여백과 같게."""
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")
        r = self.run_write(self.plain(fail_actions={"TablePropertyDialog"}), spec)
        self.assertTrue(r["ok"], r.get("error"))
        o = r["objects"][3]
        self.assertEqual(o["format"]["done"]["margin"], "off")
        metrics = wd.ts.style_metrics(wd.hp.parse(template_hwpml())["styledefs"])
        want = wd.ts.fit_table([["항목", "값"], ["하나", "1"]], [[HEAD, HEAD], [CENTER, CENTER]], metrics, 43370,
                               wd.ts.DEFAULT_INSIDE_LR)
        self.assertEqual(o["format"]["fit"]["need"], want["need"])

    def test_center_failures_switch_off_and_never_abort(self):
        """가운데 정렬(MovePos)이 오류·실패해도 쓰기는 끝까지 — 표 셋에서 실패하면 넷째 표부터 하지 않는다."""
        class NoMove(FakeHwp):
            def MovePos(self, move_id, para, pos):
                if move_id == 0:
                    raise RuntimeError("fake: MovePos")
                return FakeHwp.MovePos(self, move_id, para, pos)
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")
        r = self.run_write(self.plain(NoMove), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["format"]["done"]["center"] for o in r["objects"]], [False, False, False, "off"])
        self.assertEqual(r["check"]["table_format_off"], {"가운데 정렬": "표 4"})
        self.assertFalse([b for b in r["check"]["table_format"] if b["what"] == "가운데 정렬"])   # 실패·꺼짐은 대조 안 함

    def test_fit_failure_falls_back(self):
        """너비 셈에서 오류가 나도(재기 오류 등) 쓰기를 멈추지 않고 예전처럼 만든다 — 실패로 남긴다(검토 P-041 M1)."""
        orig = wd.ts.fit_table
        wd.ts.fit_table = lambda *a, **k: 1 / 0
        try:
            r = self.run_write(self.plain(), TS_SPEC)
        finally:
            wd.ts.fit_table = orig
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(f["table"], f["kind"]) for f in r["check"]["table_format_failed"]], [("표 1", "width"), ("표 2", "width")])
        self.assertEqual([o["format"]["col_hu"] for o in r["objects"]], [None, None])

# ---------------------------------------------------------------------- 한/글 캡션 넣기 (P-049)

class TestCaptions(Base):
    """표·그림 캡션 = 한/글 '캡션 넣기'(ShapeObjAttachCaption) + 캡션 스타일 — 가짜는 hwpxlib 시험 파일 SimpleRectangle 의
    한/글 캡션 꼴('그림 ' + 자동 번호 + ' ', 자리 아래)을 흉내 낸다(실측 전 U-30)."""
    NOCAP = SPEC.replace("표: 소프트웨어 목록\n", "")                     # 캡션 없는 표

    def setUp(self):
        super().setUp()
        import json
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(table_style_file(), ensure_ascii=False),
                                                          encoding="utf-8")

    def plain(self, cls=FakeHwp, tpl=None, **kw):
        f = cls(docs={"common.hwpx": tpl or template_hwpml()}, **kw)
        f.strict_block = True
        f.after_table_para = True                              # 실측 F-100: 표 뒤 빈 문단
        return f

    def caps(self):
        return wd.written_captions(self.f.docs["doc.hwpx"], 5)

    def test_attached_styled_and_placed(self):
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(c["tag"], c["text"], c["style"], c["side"], c["num"]) for c in self.caps()],
                         [("TABLE", "표 1 소프트웨어 목록", "04_도표그림_제목", "Top", ["Table"]),
                          ("TABLE", "표 2 장비 목록", "04_도표그림_제목", "Top", ["Table"])])
        log = self.f.log
        self.assertEqual(sum(1 for c in log if c == ("Run", "ShapeObjAttachCaption")), 2)
        self.assertEqual([c for c in log if c[0] == "CaptionProperty"], [("CaptionProperty", "Top")] * 2)
        for a in [i for i, c in enumerate(log) if c == ("Run", "ShapeObjAttachCaption")]:   # 차례: 표 문단 처음 → 캡션 넣기 →
            seg = log[a - 1:a + 12]                                               # 캡션 끝 → 스타일 둘 → 제목 → 자리 → 나오기
            self.assertEqual(seg[0][:2], ("MovePos", 0))
            kinds = [c for c in seg if c[0] in ("Run", "Action") and c[1] != "TableCreate"]
            self.assertEqual(kinds[:7], [("Run", "ShapeObjAttachCaption"), ("Run", "MoveListEnd"), ("Action", "Style"),
                                         ("Action", "Style"), ("Action", "InsertText"), ("Action", "TablePropertyDialog"),
                                         ("Run", "CloseEx")])
        m = wd.hp.parse(self.f.docs["doc.hwpx"])
        self.assertFalse([b for b in wd.top_paras(m) if b["text"].startswith("표 ")])   # 캡션 글자 문단 없음
        self.assertEqual([t["caption"] for t in m["body"] if t["type"] == "table"], ["표 1 소프트웨어 목록", "표 2 장비 목록"])
        self.assertEqual(r["plan"]["captions"], 2)

    def test_not_attached_stops_without_saving(self):
        f = self.plain()
        f.ignore = {"ShapeObjAttachCaption"}                    # 캡션 넣기가 아무것도 안 하면(캐럿이 본문에 남음)
        with self.assertRaises(api.EditFailed) as e:
            self.run_write(f, TS_SPEC)
        self.assertIn("캡션을 달지 못했다", str(e.exception))
        self.assertEqual(self.saves(), [])

    def test_right_object_needs_move_to_anchor(self):
        """캐럿 오른쪽 개체에만 붙는 한/글이어도 — 표 문단 처음(표 바로 앞)으로 옮겨 부르므로 붙는다."""
        f = self.plain()
        f.caption_pick = "right"
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["caption"]["moved"] for o in r["objects"]], [True, True])

    def test_caret_at_caption_start_is_handled(self):
        f = self.plain()
        f.caption_mode = "start"                               # 새 캡션에서 캐럿이 처음이어도 제목은 끝에(MoveListEnd)
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([c["text"] for c in self.caps()], ["표 1 소프트웨어 목록", "표 2 장비 목록"])

    def test_text_mismatch_not_saved(self):
        f = self.plain()
        f.caption_mode = "notrail"                             # 한/글 캡션 끝에 빈칸이 없다면 '표 1소프트웨어 목록'
        r = self.run_write(f, TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다")
        self.assertEqual(r["check"]["captions"]["mismatch"][0]["what"], "캡션 글자")

    def assert_fails(self, r, text):
        self.assertFalse(r["ok"])
        self.assertIn(text, r.get("error", ""))
        self.assertEqual(self.saves(), [])

    def test_style_not_applied_not_saved(self):
        class NoStyle(FakeHwp):
            def _caption_action(self, name, ps):
                return True if name == "Style" else FakeHwp._caption_action(self, name, ps)
        r = self.run_write(self.plain(NoStyle), TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다")
        self.assertEqual({b["what"] for b in r["check"]["captions"]["mismatch"]}, {"캡션 스타일"})

    @staticmethod
    def front_captioned_table_tpl():
        """템플릿 앞부분(목차 앞)에 한/글 캡션 표가 하나 있는 꼴 — 그 표도 표 번호 1 을 쓴다."""
        cap = ('<SHAPEOBJECT><CAPTION Side="Top"><PARALIST><P ParaShape="0" Style="0"><TEXT CharShape="0"><CHAR>표 </CHAR>'
               '<AUTONUM Number="1" NumberType="Table"/><CHAR> 앞 표</CHAR></TEXT></P></PARALIST></CAPTION></SHAPEOBJECT>')
        return template_hwpml().replace(P("목     차", 1), _table([["앞 칸"]]).replace(
            '<TABLE ColCount="1" RowCount="1">', '<TABLE ColCount="1" RowCount="1">' + cap) + P("목     차", 1), 1)

    def test_front_object_offset_reset_by_new_number(self):
        """템플릿 앞부분 표가 표 번호를 쓰면 본문 표 번호가 밀린다 — 첫 캡션 표 앞 '새 번호로 시작'(표 1)이 되돌린다(P-050).
        음성 대조: 새 번호가 듣지 않으면(조판 없음) '표 2' 로 밀려 저장하지 않는다."""
        r = self.run_write(self.plain(tpl=self.front_captioned_table_tpl()), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([c["text"] for c in self.caps()], ["표 1 소프트웨어 목록", "표 2 장비 목록"])
        self.assertEqual([c["newnum"] for c in self.caps()], [[["Table", "1"]], []])
        self.assertEqual([o.get("newnum") for o in r["objects"]], [{"kind": "Table", "n": 1, "ok": True, "error": None}, None])
        self.assertEqual((r["plan"]["newnums"], r["check"]["captions"]["newnum"]), (1, 1))
        f = self.plain(tpl=self.front_captioned_table_tpl())
        f.newnum_mode = "ignore"
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(f, TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다")
        self.assertEqual([(b["want"], b["got"]) for b in r["check"]["captions"]["mismatch"]],
                         [("표 1 소프트웨어 목록", "표 2 소프트웨어 목록"), ("표 2 장비 목록", "표 3 장비 목록")])
        self.assertEqual([w["what"] for w in r["check"]["captions"]["warn"]], ["새 번호"])   # 조판이 문서에 없다
        self.assertEqual((r["check"]["captions"]["newnum"], r["check"]["captions"]["newnum_inserted"]), (0, 1))  # 문서에서
        # 센 수(0)와 동작이 True 를 돌려준 수(1)를 나눈다(검토 D1-②-02)

    @staticmethod
    def hidden_figure_tpl():
        """실측 F-168 꼴: 템플릿 처음 '새 번호로 시작'(그림 1) 뒤 표지 칸에 그림 번호를 쓰는 개체(캡션 없는 그림) — 그래서 본문
        첫 그림이 '그림 2'(17.sum_step7 PoC C1). 표 번호는 실측 템플릿처럼 본문 처음 새 번호(표 1)로 맞다. 원인 개체의 실제
        꼴은 PoC N0 이 잰다."""
        x = template_hwpml().replace(SECDEF_BODY, SECDEF_BODY + '<NEWNUM Number="1" NumberType="Table"/>', 1)
        x = x.replace(P("문서번호 : {{문서번호}}", pre="<SECDEF/>" + x[x.index("<HEADER"):x.index("</HEADER>") + 9]),
                      P("문서번호 : {{문서번호}}", pre='<SECDEF/>' + x[x.index("<HEADER"):x.index("</HEADER>") + 9]
                        + '<NEWNUM Number="1" NumberType="Figure"/>'), 1)
        logo = _table([["로고"]]).replace("<CHAR>로고</CHAR>", '<PICTURE><SHAPEOBJECT NumberingType="Figure"/></PICTURE>')
        return x.replace(P("{{과제명}}", 2), logo + P("{{과제명}}", 2), 1)

    def test_hidden_figure_in_template_reset(self):
        """F-168: 템플릿에 보이지 않는 그림 번호 개체가 있어도 첫 그림 앞 새 번호(그림 1)로 '그림 1'. 음성 대조: 새 번호가
        듣지 않으면 '그림 2' 라 저장하지 않는다(17.sum_step7 실측과 같은 꼴)."""
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        r = self.run_write(self.plain(tpl=self.hidden_figure_tpl()), TestWrite.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([c["text"] for c in self.caps()], ["표 1 소프트웨어 목록", "그림 1 로그인 화면"])
        self.assertEqual([c["newnum"] for c in self.caps()], [[["Table", "1"]], [["Figure", "1"]]])
        f = self.plain(tpl=self.hidden_figure_tpl())
        f.newnum_mode = "ignore"
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(f, TestWrite.PIC_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다(1곳)")
        self.assertEqual([(b["want"], b["got"]) for b in r["check"]["captions"]["mismatch"]],
                         [("그림 1 로그인 화면", "그림 2 로그인 화면")])

    UNCAPTIONED = TS_SPEC.replace("표: 장비 목록\n", "사이 문단.\n| 칸 |\n|---|\n| 캡션 없는 표 |\n표: 장비 목록\n")

    def test_uncaptioned_table_does_not_shift_numbers(self):
        """F-169: 캡션 없는 표도 한/글 표 번호를 쓴다(실측 PoC C5) — 그 뒤 첫 캡션 표 앞에 새 번호(그 명세 번호)를 넣어 빈 번호
        없이 '표 1'·'표 2'. 음성 대조: 새 번호가 듣지 않으면 둘째 캡션 표가 '표 3' 이라 저장하지 않는다."""
        items = wd.plan(wd.parse_spec(self.UNCAPTIONED)[1], wd.STYLES)
        self.assertEqual([(x["caption"], (x["cap"] or {}).get("newnum")) for x in items if x["type"] == "table"],
                         [("소프트웨어 목록", 1), (None, None), ("장비 목록", 2)])
        r = self.run_write(self.plain(), self.UNCAPTIONED)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(c["text"], c["newnum"]) for c in self.caps()],
                         [("표 1 소프트웨어 목록", [["Table", "1"]]), (None, []), ("표 2 장비 목록", [["Table", "2"]])])
        f = self.plain()
        f.newnum_mode = "ignore"
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(f, self.UNCAPTIONED)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다(1곳)")
        self.assertEqual([(b["want"], b["got"]) for b in r["check"]["captions"]["mismatch"]],
                         [("표 2 장비 목록", "표 3 장비 목록")])
        f = self.plain()
        f.fail_actions = {"NewNumber"}
        r = self.run_write(f, self.UNCAPTIONED)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다(1곳)")
        self.assertEqual([(x["at"], x["n"]) for x in r["check"]["captions"]["newnum_failed"]],   # 캡션 번호로 가리킨다 —
                         [("표 1", 1), ("표 2", 2)])                            # 캡션 없는 표까지 센 '표 3' 이 아니다(D1-①-01)
        self.assertTrue(any("넣지 못한 곳 2 — 표 1(Table 1: NewNumber 실패(False)), 표 2(Table 2:" in w
                            for w in r["warnings"]), r["warnings"])

    def test_new_number_plan(self):
        """새 번호 자리: 첫 그림(1), 첫 캡션 표(1), 캡션 없는 표 뒤 첫 캡션 표(그 번호) — 나머지는 이어 센다. 그림 없이 쓰면
        그림 캡션은 글자 문단이라 그림 새 번호가 없다. 캡션 없는 표가 맨 앞이어도 첫 캡션 표의 새 번호 하나로 된다."""
        spec = SPEC.replace("![로그인 화면](원본 s0.p3)", "![로그인 화면](원본 s0.p3)\n![둘째](원본 s0.p4)")
        spec = spec.replace("표: 소프트웨어 목록\n", "| 앞 |\n|---|\n| 캡션 없음 |\n\n표: 소프트웨어 목록\n")
        items = wd.plan(wd.parse_spec(spec)[1], wd.STYLES, pictures=True)
        self.assertEqual([(x["type"], x["cap"]["text"].split(" ")[1], x["cap"]["newnum"]) for x in items
                          if x["type"] != "para" and x.get("cap")],
                         [("table", "1", 1), ("picture", "1", 1), ("picture", "2", None)])
        self.assertEqual([x for x in items if x["type"] == "table" and not x.get("cap")][0]["caption"], None)
        flat = wd.plan(wd.parse_spec(spec)[1], wd.STYLES, pictures=False)
        self.assertEqual([x["type"] for x in flat if (x.get("cap") or {}).get("newnum")], ["table"])

    def test_new_number_after_caption_before_object(self):
        """한/글 호출 차례: 캡션 넣기 → … → CloseEx → 개체 문단 처음(MovePos) → NewNumber(GetDefault 먼저). 새 번호 조판은 개체
        바로 앞(문단 첫 단위) — 캡션 넣기가 새 번호 조판을 고르지 않게 캡션 뒤에 넣는다."""
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        r = self.run_write(self.plain(), TestWrite.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        log = self.f.log
        for o, kind in zip(r["objects"], ("Table", "Figure")):
            a = log.index(("NewNumber", kind, 1))
            close = max(i for i in range(a) if log[i] == ("Run", "CloseEx"))
            attach = max(i for i in range(close) if log[i] == ("Run", "ShapeObjAttachCaption"))
            self.assertEqual([c for c in log[close + 1:a] if c[0] in ("MovePos", "Action", "Run")],
                             [("MovePos", 0, o["anchor"][1], 0), ("Action", "NewNumber")])
            self.assertLess(attach, close)
        x = self.f.docs["doc.hwpx"]
        self.assertRegex(x, r'<TEXT CharShape="0"><NEWNUM Number="1" NumberType="Table" /><TABLE')
        self.assertRegex(x, r'<NEWNUM Number="1" NumberType="Figure" /><PICTURE')

    def test_new_number_failure_recorded_and_checked(self):
        """새 번호를 넣지 못해도(동작 False·MovePos 실패) 쓰기는 끝까지 — 실패로 남기고 번호는 쓴 뒤 캡션 대조가 본다: 앞부분에
        번호를 쓰는 개체가 없으면 저장, 있으면 저장하지 않는다(fail-closed)."""
        f = self.plain()
        f.fail_actions = {"NewNumber"}
        r = self.run_write(f, TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["captions"]["newnum_failed"],
                         [{"kind": "Table", "n": 1, "ok": False, "error": "NewNumber 실패(False)", "at": "표 1"}])
        self.assertTrue(any("'새 번호로 시작'을 넣지 못한 곳 1" in w for w in r["warnings"]), r["warnings"])
        self.assertEqual(r["check"]["captions"]["warn"], [])                    # 실패로 알린 곳은 '새 번호' 경고 없음
        self.assertEqual((r["check"]["captions"]["newnum"], r["check"]["captions"]["newnum_inserted"]), (0, 0))
        f = self.plain(tpl=self.front_captioned_table_tpl())
        f.fail_actions = {"NewNumber"}
        (self.tmp / "out" / "doc.hwpx").unlink()
        self.assert_fails(self.run_write(f, TS_SPEC), "표·그림 캡션이 명세와 다르다")

        class NoAutoNumType(FakeHwp):                         # U-31 이름이 틀린 한/글 꼴: pywin32 는 없는 메서드에 예외
            def AutoNumType(self, name):
                raise AttributeError("<unknown>.AutoNumType")
        r = self.run_write(self.plain(NoAutoNumType), TS_SPEC)                  # 번호가 원래 맞는 문서 — 경고하고 저장
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(x["at"], x["error"]) for x in r["check"]["captions"]["newnum_failed"]],
                         [("표 1", "NewNumber 오류 AttributeError: <unknown>.AutoNumType")])
        self.assertNotIn(("Action", "NewNumber"), self.f.log)                   # Execute 전에 멈췄다
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.plain(NoAutoNumType, tpl=self.front_captioned_table_tpl()), TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다")                       # 번호가 밀리는 문서 — 저장하지 않는다
        self.assertEqual(r["check"]["captions"]["mismatch"][0]["got"], "표 2 소프트웨어 목록")

        class NoMove(FakeHwp):
            def MovePos(self, move_id, para, pos):
                if move_id == 0 and any(c == ("Run", "CloseEx") for c in self.log[-3:]):   # 캡션에서 나온 뒤(새 번호 자리)만
                    self.log.append(("MovePos", 0, para, pos))
                    return False
                return FakeHwp.MovePos(self, move_id, para, pos)
        r = self.run_write(self.plain(NoMove, tpl=self.front_captioned_table_tpl()), TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다")
        self.assertIn("옮기지 못했다", r["check"]["captions"]["newnum_failed"][0]["error"])
        self.assertNotIn(("Action", "NewNumber"), self.f.log)                   # 자리를 못 잡으면 넣지 않는다

    def test_new_number_timeout_propagates(self):
        """시간초과(감시가 한/글을 죽임)는 새 번호 실패로 삼키지 않고 그대로 올린다 — 죽은 세션으로 쓰기를 잇지 않는다
        (MovePos·NewNumber 둘 다, 검토 P-050 D1-③-04)."""
        class SlowMove(FakeHwp):
            slow_done = False                                   # 한 번만 — 삼키면 쓰기가 끝까지 가서 저장한다

            def MovePos(self, move_id, para, pos):
                log = self.log                                  # 캡션에서 나온(CloseEx) 뒤 첫 MovePos = 새 번호 자리
                a = max((i for i, c in enumerate(log) if c == ("Run", "ShapeObjAttachCaption")), default=None)
                k = next((i for i in range(a, len(log)) if log[i] == ("Run", "CloseEx")), None) if a is not None else None
                if not self.slow_done and move_id == 0 and k is not None and not any(c[0] == "MovePos" for c in log[k:]):
                    self.slow_done = True
                    raise hs.TimeoutKilled("MovePos 가 넘겼다")
                return FakeHwp.MovePos(self, move_id, para, pos)

        class SlowNewNumber(FakeHwp):
            def AutoNumType(self, name):                       # NewNumber 호출(s.s.call 안)에서
                raise hs.TimeoutKilled("NewNumber 가 넘겼다")
        for cls, text in ((SlowMove, "MovePos"), (SlowNewNumber, "NewNumber")):
            with self.assertRaises(hs.TimeoutKilled) as e:
                self.run_write(self.plain(cls), TS_SPEC)
            self.assertIn(text, str(e.exception))
            self.assertEqual(self.saves(), [])

    def test_fake_numbers_every_object(self):
        """흉내 자동 번호(실측 P-050): 캡션과 관계없이 표·그림을 차례로 세고, 새 번호는 그 뒤 번호를 정하고, 번호 종류 None·
        머리말 안 개체·묶음(CONTAINER) 안 개체는 세지 않는다 — 묶음은 하나로 센다(검토 D1-①-04)."""
        cap = '<SHAPEOBJECT><CAPTION><PARALIST><P><TEXT><AUTONUM Number="0" NumberType="%s"/></TEXT></P></PARALIST></CAPTION></SHAPEOBJECT>'
        x = ('<HWPML><BODY><SECTION><P><TEXT><HEADER><PARALIST><P><TEXT><PICTURE/></TEXT></P></PARALIST></HEADER>'
             '<TABLE></TABLE><TABLE><SHAPEOBJECT NumberingType="None"/></TABLE><TABLE>%s</TABLE>'
             '<PICTURE>%s</PICTURE><NEWNUM Number="7" NumberType="Table"/><TABLE>%s</TABLE>'
             '<RECTANGLE><SHAPEOBJECT NumberingType="Figure"/></RECTANGLE>'
             '<CONTAINER><SHAPEOBJECT NumberingType="Figure"/><RECTANGLE><SHAPECOMPONENT/></RECTANGLE><ELLIPSE/></CONTAINER>'
             '<PICTURE>%s</PICTURE>'
             '</TEXT></P></SECTION></BODY></HWPML>' % (cap % "Table", cap % "Figure", cap % "Table", cap % "Figure"))
        f = FakeHwp(hwpml=x)
        f._renumber()
        self.assertEqual(re.findall(r'<AUTONUM Number="(\d+)" NumberType="(\w+)"', f.hwpml),
                         [("2", "Table"), ("1", "Figure"), ("7", "Table"), ("4", "Figure")])

    def test_side_not_moved_is_warned(self):
        class StaySide(FakeHwp):                                # 자리 바꾸기가 '됐다'고만 하고 그대로(아래)
            def _caption_action(self, name, ps):
                return True if name == "TablePropertyDialog" else FakeHwp._caption_action(self, name, ps)
        r = self.run_write(self.plain(StaySide), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))                # 자리는 서식 — 경고만, 저장한다
        self.assertEqual([(w["what"], w["want"], w["got"]) for w in r["check"]["captions"]["warn"]],
                         [("캡션 자리", "Top", "Bottom")] * 2)
        self.assertTrue(any("캡션 2곳이 계획과 다르다(캡션 자리 2)" in w for w in r["warnings"]), r["warnings"])

    def test_side_failure_switched_off_after_three(self):
        spec = TS_SPEC.replace("끝 문단.\n", TS_MORE + "끝 문단.\n")

        class NoSide(FakeHwp):
            def _caption_action(self, name, ps):
                if name == "TablePropertyDialog":
                    self.log.append(("CaptionProperty", "fail"))
                    return False
                return FakeHwp._caption_action(self, name, ps)
        r = self.run_write(self.plain(NoSide), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["format"]["done"]["caption"] for o in r["objects"]], [False, False, False, "off"])
        self.assertEqual(r["check"]["table_format_off"], {"캡션 자리": "표 4"})
        self.assertEqual(r["check"]["captions"]["warn"], [])     # 못 입힌 자리는 다시 알리지 않는다
        self.assertEqual(sum(1 for c in self.f.log if c[0] == "CaptionProperty"), 3)

    def test_picture_side_default_kept_and_checked(self):
        class TopDefault(FakeHwp):                              # 한/글이 그림 캡션 자리를 '위'로 기억하고 있으면
            def _attach_caption(self):
                FakeHwp._attach_caption(self)
                if self.caption:
                    el, cap, _ = self._caption_p()
                    cap.set("Side", "Top")
                    self._put_para(self.caption["para"], el)
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        r = self.run_write(self.plain(TopDefault), TestWrite.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(w["at"], w["what"], w["want"], w["got"]) for w in r["check"]["captions"]["warn"]],
                         [(self.caps()[1]["at"], "캡션 자리", "Bottom", "Top")])   # 표는 위로 옮겼고 그림만 알린다
        self.assertEqual(sum(1 for c in self.f.log if c[0] == "CaptionProperty"), 1)   # 그림에는 자리를 바꾸지 않는다

    def test_table_without_caption_has_none(self):
        r = self.run_write(self.plain(), self.NOCAP)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(c["tag"], c["text"]) for c in self.caps()], [("TABLE", None), ("PICTURE", "그림 1 로그인 화면")])
        self.assertEqual(r["objects"][0].get("caption"), None)
        self.assertEqual(r["objects"][0]["format"]["done"]["caption"], None)

    def test_placeholder_keeps_figure_numbers(self):
        """그림 파일이 없는 그림(자리 표시 그림) 뒤 그림도 명세 번호 그대로 — 본문 인용과 한/글 번호가 같다."""
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "b.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        spec = SPEC.replace("> 운용 사이트 정보\n", '![둘째 화면](img/b.png "50x30")\n화면은 {{그림:둘째 화면}} 이다.\n')
        r = self.run_write(self.plain(), spec)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([c["text"] for c in self.caps() if c["tag"] == "PICTURE"], ["그림 1 로그인 화면", "그림 2 둘째 화면"])
        self.assertIn("화면은 그림 2 이다.", [b["text"] for b in wd.top_paras(wd.hp.parse(self.f.docs["doc.hwpx"]))])
        self.assertEqual([o.get("path") for o in r["objects"] if o["type"] == "picture"], [str(wd.PLACEHOLDER), "img/b.png"])

    def test_missing_caption_style_refused(self):
        spec = TS_SPEC.replace('"keys"', '"styles": {"caption": "없는 캡션 스타일"}, "keys"')
        with self.assertRaises(wd.SpecError) as e:
            self.run_write(self.plain(), spec)
        self.assertIn("없는 캡션 스타일", str(e.exception))
        self.assertNotIn(("Run", "BreakPara"), self.f.log)                 # 쓰기 전에 거절

    @staticmethod
    def cap_rules():
        """한/글이 만든 캡션 문단 글자 모양이 직접 서식(옛 본문 12pt)이라면 — 본문 문단과 같은 F-109 규칙(흉내): 다른 스타일을
        입히면 글자 모양이 남고, 같은 스타일을 다시 입히면 스타일 모양으로."""
        class CapRules(FakeHwp):
            def _attach_caption(self):
                FakeHwp._attach_caption(self)
                if self.caption:
                    el, cap, p = self._caption_p()
                    for tx in p.findall("TEXT"):
                        tx.set("CharShape", "4")
                    self._put_para(self.caption["para"], el)

            def _caption_action(self, name, ps):
                if name == "Style":
                    el, cap, p = self._caption_p()
                    st = self._head_items(self.hwpml, "STYLE")
                    cur = p.get("Style", "0")
                    if p.find("TEXT").get("CharShape") != self._attr(st.get(cur, ""), "CharShape") \
                            and str(ps.HStyle.Apply) != cur:
                        p.set("Style", str(ps.HStyle.Apply))
                        self._put_para(self.caption["para"], el)
                        return True
                return FakeHwp._caption_action(self, name, ps)
        return CapRules

    def test_caption_direct_format_cleared(self):
        r = self.run_write(self.plain(self.cap_rules(), tpl=template_leftover_hwpml()), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["captions"]["warn"], [])               # 캡션 스타일 두 번 — 04 글자 크기(1100)
        orig = wd.apply_style_clean                                        # 음성 대조: 한 번만 입히면 12pt 가 남아 경고
        wd.apply_style_clean = lambda s, idx, name, new, clean=True: wd.apply_style(s, idx, name)
        try:
            (self.tmp / "out" / "doc.hwpx").unlink()
            r = self.run_write(self.plain(self.cap_rules(), tpl=template_leftover_hwpml()), TS_SPEC)
        finally:
            wd.apply_style_clean = orig
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual({(w["what"], w["want"], tuple(w["got"])) for w in r["check"]["captions"]["warn"]},
                         {("글자 크기", "1100", ("1200",))})

    def test_pad_uses_largest_cell_style_in_writer(self):
        """칸 안 여백 위·아래 = 그 표 칸 스타일 중 가장 큰 글자 크기의 반 — 제목 줄 05 가 13pt 면 650. 서식 파일이 있는 표·
        없는 표 모두(P-048, 검토 P-049 D1-③-02)."""
        tpl = template_sized_hwpml().replace("</CHARSHAPELIST>", '<CHARSHAPE Id="5" Height="1300"/></CHARSHAPELIST>', 1)
        tpl = re.sub(r'(<STYLE Id="%d" Name="05_도표내용_항목제목" CharShape=")\d+"' % STYLES.index("05_도표내용_항목제목"),
                     r'\g<1>5"', tpl)
        for spec in (TS_SPEC, TS_SPEC.replace('"table_style": "tpl/table_style.json",', "")):
            r = self.run_write(self.plain(tpl=tpl), spec)
            self.assertTrue(r["ok"], r.get("error"))
            self.assertEqual([x["inside_margin"][2:] for x in r["table_style"]["tables"]], [[650, 650]] * 2)
            self.assertEqual(r["check"]["table_format"], [])
            (self.tmp / "out" / "doc.hwpx").unlink()

    def test_picture_caption_direct_format_cleared(self):
        """그림 캡션도 캡션 스타일을 두 번 입혀 직접 글자 모양을 지운다(검토 P-049 D1-③-03)."""
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        r = self.run_write(self.plain(self.cap_rules(), tpl=template_leftover_hwpml()), TestWrite.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["captions"]["warn"], [])
        self.assertEqual([c["tag"] for c in self.caps()], ["TABLE", "PICTURE"])

    def test_movepos_false_attaches_at_caret(self):
        """개체 문단으로 못 옮기면(MovePos 가 예외 없이 False) 캐럿 자리(표 밖으로 나온 곳·그림 넣은 곳 — 개체 바로 뒤)에서
        캡션을 단다 — 기록 moved False(검토 P-049 D1-③-07)."""
        class NoMove(FakeHwp):
            def MovePos(self, move_id, para, pos):
                if move_id == 0:
                    self.log.append(("MovePos", 0, para, pos))
                    return False
                return FakeHwp.MovePos(self, move_id, para, pos)
        (self.tmp / "img").mkdir(exist_ok=True)
        (self.tmp / "img" / "a.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        r = self.run_write(self.plain(NoMove), TestWrite.PIC_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([o["caption"]["moved"] for o in r["objects"]], [False, False])
        self.assertEqual([c["text"] for c in self.caps()], ["표 1 소프트웨어 목록", "그림 1 로그인 화면"])

    @staticmethod
    def center_tpl():
        """캡션 스타일 04 의 문단 모양이 가운데 정렬인 템플릿."""
        k = STYLES.index("04_도표그림_제목")
        tpl = template_hwpml().replace('<PARASHAPE Id="0" HeadingType="None" Level="0"/>',
                                       '<PARASHAPE Id="0" HeadingType="None" Level="0"/>'
                                       '<PARASHAPE Id="9" HeadingType="None" Level="0" Align="Center"/>', 1)
        return tpl.replace('<STYLE Id="%d" Name="04_도표그림_제목" ParaShape="0"/>' % k,
                           '<STYLE Id="%d" Name="04_도표그림_제목" ParaShape="9"/>' % k, 1)

    class KeepPara(FakeHwp):                                    # 캡션 스타일이 문단 모양(정렬)을 남기면
        def _caption_action(self, name, ps):
            if name != "Style":
                return FakeHwp._caption_action(self, name, ps)
            old = self._caption_p()[2].get("ParaShape")
            ok = FakeHwp._caption_action(self, name, ps)
            el, _, p = self._caption_p()
            p.set("ParaShape", old)
            self._put_para(self.caption["para"], el)
            return ok

    def test_caption_alignment_checked(self):
        """캡션 문단 정렬이 캡션 스타일 정렬과 다르면 경고 — 글자 문단이던 캡션을 align_mismatch 가 보던 보호를 잇는다
        (검토 P-049 D1-③-01)."""
        tpl = self.center_tpl()
        r = self.run_write(self.plain(tpl=tpl), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["captions"]["warn"], [])
        self.assertEqual({c["align"] for c in self.caps()}, {"Center"})
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.plain(self.KeepPara, tpl=tpl), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual([(w["what"], w["want"], w["got"]) for w in r["check"]["captions"]["warn"]],
                         [("정렬", "Center", "Justify")] * 2)
        self.assertTrue(any("캡션 2곳이 계획과 다르다(정렬 2)" in w for w in r["warnings"]), r["warnings"])

    def test_places_counted_once(self):
        """보고의 '곳'은 캡션 수다 — 한 캡션에 문제가 둘이어도 한 곳으로 센다(검토 P-049 D1-②-05).
        경고는 자리와 정렬, 어긋남은 글자와 스타일이 같은 캡션 둘에 겹친다."""
        class StayKeep(self.KeepPara):                          # 자리 바꾸기가 '됐다'고만 하고 그대로(아래) + 정렬 남김
            def _caption_action(self, name, ps):
                return True if name == "TablePropertyDialog" else TestCaptions.KeepPara._caption_action(self, name, ps)
        r = self.run_write(self.plain(StayKeep, tpl=self.center_tpl()), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(len(r["check"]["captions"]["warn"]), 4)
        self.assertTrue(any("캡션 2곳이 계획과 다르다(캡션 자리 2, 정렬 2)" in w for w in r["warnings"]), r["warnings"])

        class NoStyle(FakeHwp):
            def _caption_action(self, name, ps):
                return True if name == "Style" else FakeHwp._caption_action(self, name, ps)
        f = self.plain(NoStyle)
        f.caption_mode = "notrail"                             # 글자도 다르다('표 1소프트웨어 목록')
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(f, TS_SPEC)
        self.assert_fails(r, "표·그림 캡션이 명세와 다르다(2곳)")
        self.assertEqual(sorted(b["what"] for b in r["check"]["captions"]["mismatch"]),
                         ["캡션 글자", "캡션 글자", "캡션 스타일", "캡션 스타일"])

    def test_hand_edited_margin_does_not_stop_writing(self):
        """서식 파일 안 여백을 손으로 '538.5' 로 고쳐도 쓰기를 멈추지 않는다 — 538(버림)로 입힌다(검토 P-049 D1-①-01).
        못 쓰는 값(NaN·음수)은 한/글 기본 510(D1F-02)."""
        import json
        sf = table_style_file()
        sf["tables"]["소프트웨어 목록"]["inside_margin"] = ["538.5", "538", "0", "0"]
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["tables"][0]["inside_margin"], [538, 538, 500, 500])
        self.assertEqual(r["check"]["table_format"], [])
        sf["tables"]["소프트웨어 목록"]["inside_margin"] = [float("nan"), -5, 0, 0]          # JSON NaN·음수(검토 P-049 D1F-02)
        (self.tmp / "tpl" / "table_style.json").write_text(json.dumps(sf, ensure_ascii=False), encoding="utf-8")
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.plain(), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["table_style"]["tables"][0]["inside_margin"], [510, 510, 500, 500])
        self.assertEqual(r["check"]["table_format"], [])

    def test_caption_check_rules(self):
        cap = {"text": "표 1 가", "title": "가", "style": "04", "side": "Top"}
        items = [{"type": "table", "cap": cap}, {"type": "picture", "cap": dict(cap, text="그림 1 나", side="Bottom")},
                 {"type": "table", "cap": None}, {"type": "para"}]
        good = [{"tag": "TABLE", "at": "a", "text": "표 1 가", "style": "04", "align": "Center", "side": "Top",
                 "num": ["Table"], "heights": ["1000"]},
                {"tag": "PICTURE", "at": "b", "text": "그림 1 나", "style": "04", "align": "Center", "side": "Bottom",
                 "num": ["Figure"], "heights": []},
                {"tag": "TABLE", "at": "c", "text": None}]
        d04 = {"04": {"height": "1000", "align": "Center"}}
        self.assertEqual(wd.caption_check(good, items, d04, {}), ([], []))
        bad, warn = wd.caption_check(good[:2], items, {}, {})
        self.assertEqual(bad, [{"what": "표·그림 수", "want": 3, "got": 2}])
        g = [dict(good[0], text="표 2 가", style="03"), dict(good[1], tag="TABLE"), dict(good[2], text="표 1 다")]
        bad, _ = wd.caption_check(g, items, {}, {})
        self.assertEqual([b["what"] for b in bad], ["캡션 글자", "캡션 스타일", "개체 종류", "캡션 글자"])
        g = [dict(good[0], side="Bottom", num=[], heights=["1100"], align="Justify"), good[1], good[2]]
        bad, warn = wd.caption_check(g, items, d04, {})
        self.assertEqual((bad, [w["what"] for w in warn]), ([], ["캡션 자리", "자동 번호", "글자 크기", "정렬"]))
        for done in (False, "off"):                               # 자리 입히기가 실패·꺼진 표는 자리를 보지 않는다
            _, warn = wd.caption_check(g, items, {}, {0: done})
            self.assertEqual([w["what"] for w in warn], ["자동 번호"])
        missing = [{"tag": "TABLE", "at": "a", "text": None}, good[1], good[2]]     # 계획엔 캡션, 쓴 표엔 없음
        bad, warn = wd.caption_check(missing, items, d04, {})
        self.assertEqual(([b["what"] for b in bad], warn), (["캡션 글자"], []))
        mixed = [dict(good[0], heights=["1000", "1200"]), good[1], good[2]]          # 반만 스타일 모양(직접 서식 섞임)
        _, warn = wd.caption_check(mixed, items, d04, {})
        self.assertEqual([(w["what"], w["got"]) for w in warn], [("글자 크기", ["1000", "1200"])])
        nn = [dict(items[0], cap=dict(cap, newnum=1)), items[1], items[2], items[3]]   # 계획한 새 번호(P-050)
        self.assertEqual([w["what"] for w in wd.caption_check(good, nn, d04, {})[1]], ["새 번호"])
        self.assertEqual(wd.caption_check([dict(good[0], newnum=[["Table", "1"]]), good[1], good[2]], nn, d04, {}), ([], []))
        self.assertEqual(wd.caption_check(good, nn, d04, {}, {0: False}), ([], []))     # 넣기 실패로 이미 알림
        self.assertEqual([w["want"] for w in wd.caption_check([dict(good[0], newnum=[["Figure", "1"]]), good[1], good[2]],
                                                               nn, d04, {})[1]], [["Table", "1"]])
        self.assertEqual([(w["what"], w["want"], w["got"]) for w in wd.caption_check(           # 같은 종류·다른 번호도
            [dict(good[0], newnum=[["Table", "5"]]), good[1], good[2]], nn, d04, {})[1]],      # 경고(검토 D1-①-02)
            [("새 번호", ["Table", "1"], [["Table", "5"]])])
        self.assertEqual(wd.newnum_found([dict(good[0], newnum=[["Table", "1"]]), good[1], good[2]], nn), 1)
        self.assertEqual(wd.newnum_found([dict(good[0], newnum=[["Table", "5"]]), good[1], good[2]], nn), 0)
        self.assertEqual(wd.newnum_found(good, nn), 0)

    def test_written_captions_only_top_objects_after_head(self):
        x = self.plain().docs["common.hwpx"]
        inner = _table([["칸"]]).replace('<TABLE ColCount="1" RowCount="1">', '<TABLE ColCount="1" RowCount="1">'
                                         '<SHAPEOBJECT><CAPTION Side="Top"><PARALIST><P ParaShape="0" Style="4"><TEXT '
                                         'CharShape="0"><CHAR>표 </CHAR><AUTONUM Number="9" NumberType="Table"/><CHAR> 안</CHAR>'
                                         '</TEXT></P></PARALIST></CAPTION></SHAPEOBJECT>')
        outer = _table([["바깥"]]).replace("<P ParaShape=\"0\" Style=\"0\"><TEXT CharShape=\"0\"><CHAR>바깥</CHAR></TEXT></P>",
                                           inner)
        x = x.replace("</SECTION></BODY>", outer + "</SECTION></BODY>")
        got = wd.written_captions(x, 5)
        self.assertEqual([(c["tag"], c["text"]) for c in got], [("TABLE", None)])   # 칸 안 표의 캡션은 보지 않는다
        self.assertEqual(wd.written_captions(x, 6), [])                              # 제목 뒤 문단만

    def test_written_captions_newnum_belongs_to_next_object(self):
        """새 번호는 같은 문단에서 바로 뒤 개체의 몫 — 한 문단에 개체 둘이면 앞 개체만, 개체 뒤 새 번호는 그 개체 몫이 아니다
        (검토 P-050 D1-②-06·D1-③-05). 다른 글자 덩어리(TEXT)에 나뉘어 있어도 문단 차례로 본다."""
        x = self.plain().docs["common.hwpx"]
        t = '<TABLE ColCount="1" RowCount="1"></TABLE>'
        two = '<P ParaShape="0" Style="0"><TEXT CharShape="0"><NEWNUM Number="1" NumberType="Table"/>%s%s</TEXT></P>' % (t, t)
        after = '<P ParaShape="0" Style="0"><TEXT CharShape="0">%s<NEWNUM Number="2" NumberType="Table"/></TEXT></P>' % t
        runs = ('<P ParaShape="0" Style="0"><TEXT CharShape="0"><NEWNUM Number="3" NumberType="Table"/></TEXT>'
                '<TEXT CharShape="1">%s</TEXT></P>' % t)
        got = wd.written_captions(x.replace("</SECTION></BODY>", two + after + runs + "</SECTION></BODY>"), 5)
        self.assertEqual([(c["at"], c["newnum"]) for c in got],
                         [("s1.p1", [["Table", "1"]]), ("s1.p1", []), ("s1.p2", []), ("s1.p3", [["Table", "3"]])])

    @staticmethod
    def page_newnum_tpl():
        """공통 템플릿 실측 꼴(R1): 본문 처음에 쪽 새 번호(쪽 1) — 본문 첫 쪽이 1."""
        return template_hwpml().replace(SECDEF_BODY, SECDEF_BODY + '<NEWNUM Number="1" NumberType="Page"/>', 1)

    def test_body_page_number_kept(self):
        """본문 첫 쪽 인쇄 번호를 쓰기 앞뒤로 견준다(P-050 검토 D1-②-01). 음성 대조: 같은 쪽 뒤 새 번호(종류 무관)가 쪽 새
        번호를 무효로 하는 한/글(pyhwpx 주의 3 을 종류 무관으로 읽은 꼴)이면 본문 첫 쪽이 1 → 2(쪽 새 번호 10 이면 10 → 2 — 줄어도)
        라 저장하지 않는다. 두 길(KeyIndicator·CurrentPrintPage) 중 하나만 읽혀도 그 값, 둘이 다르면(쪽 차례를 읽는 길) 못 읽음 —
        새 번호를 넣었으면 경고하고 저장한다(캡션 번호는 따로 대조, 검토 D2-②-01·D2-②-03·D2-③-03)."""
        r = self.run_write(self.plain(tpl=self.page_newnum_tpl()), TS_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["page"], {"body_first": [1, 1], "reads": [[1, 1], [1, 1]]})
        keys = [i for i, c in enumerate(self.f.log) if c == ("KeyIndicator",)]
        self.assertEqual([self.f.log[i - 1] for i in keys], [("MovePos", 0, 5, 0)] * 2)   # 본문 첫 문단 처음에서 읽는다
        self.assertLess(keys[0], self.f.log.index(("Run", "ShapeObjAttachCaption")))      # 쓰기 전 하나
        self.assertGreater(keys[1], max(i for i, c in enumerate(self.f.log) if c == ("Action", "NewNumber")))  # 쓴 뒤 하나
        for first, want in ((1, "본문 첫 쪽 번호가 1 → 2 로 바뀌었다 — 넣은 '새 번호로 시작' 1개가"),
                            (10, "본문 첫 쪽 번호가 10 → 2 로 바뀌었다")):
            f = self.plain(tpl=self.page_newnum_tpl().replace('<NEWNUM Number="1" NumberType="Page"/>',
                                                              '<NEWNUM Number="%d" NumberType="Page"/>' % first))
            f.page_newnum_rule = "last_on_page"
            out = self.tmp / "out" / "doc.hwpx"
            if out.exists():
                out.unlink()
            r = self.run_write(f, TS_SPEC)
            self.assert_fails(r, want)
            self.assertEqual(r["check"]["captions"]["mismatch"], [])          # 캡션 번호는 맞다 — 쪽 번호만 바뀌었다

        class IndexOnly(FakeHwp):                              # KeyIndicator 가 쪽 차례를 돌려주는 한/글(실측 전 — 다른 꼴)
            def KeyIndicator(self):
                k = list(FakeHwp.KeyIndicator(self))
                k[3] = self._pages()[min(self.caret, len(self._pages()) - 1)][1] + 1
                return tuple(k)
        for cls, mode, page, reads, warned in (
                (FakeHwp, "key", [1, 1], [[None, 1], [None, 1]], False),      # KeyIndicator 만 못 읽음 — 다른 길
                (FakeHwp, "both", [None, None], [[None, None], [None, None]], True),
                (IndexOnly, None, [None, None], [[2, 1], [2, 1]], True)):     # 두 길이 다르다 — 못 읽음(조용히 [2, 2] 아님)
            f = self.plain(cls, tpl=self.page_newnum_tpl())
            if mode in ("key", "both"):
                f.key_indicator_mode = "raise"
            if mode == "both":
                f.doc_info_mode = "raise"
            out = self.tmp / "out" / "doc.hwpx"
            if out.exists():
                out.unlink()
            r = self.run_write(f, TS_SPEC)
            self.assertTrue(r["ok"], r.get("error"))
            self.assertEqual(r["check"]["page"], {"body_first": page, "reads": reads}, (cls, mode))
            self.assertEqual(any("본문 첫 쪽 번호를 읽지 못했다" in w and "'새 번호로 시작' 1개를 넣었으니" in w
                                 for w in r["warnings"]), warned, r["warnings"])
        f = self.plain(tpl=self.page_newnum_tpl())                    # 새 번호를 하나도 넣지 않는 쓰기 — 못 읽어도 경고 없음
        f.key_indicator_mode, f.doc_info_mode = "raise", "raise"
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(f, self.NOCAP, pictures=False)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual((r["check"]["page"]["body_first"], r["check"]["captions"]["newnum_inserted"]), ([None, None], 0))
        self.assertFalse([w for w in r["warnings"] if "본문 첫 쪽" in w], r["warnings"])

    def test_page_reading_timeout_propagates(self):
        """쪽 번호 읽기(쓰기 앞·뒤)의 시간초과도 삼키지 않는다(검토 D2-③-02) — KeyIndicator·CurrentPrintPage 어느 쪽이든."""
        class SlowKey(FakeHwp):
            at = 1

            def KeyIndicator(self):
                self.n_key = getattr(self, "n_key", 0) + 1
                if self.n_key == self.at:
                    raise hs.TimeoutKilled("KeyIndicator 가 넘겼다")
                return FakeHwp.KeyIndicator(self)

        class SlowInfo(FakeHwp):
            @property
            def XHwpDocuments(self):
                raise hs.TimeoutKilled("CurrentPrintPage 가 넘겼다")
        class SlowPageMove(FakeHwp):                           # 쓰기 전 쪽 번호 읽기 자리(본문 첫 문단)로 옮길 때
            def MovePos(self, move_id, para, pos):
                if (move_id, para, pos) == (0, 5, 0) and ("KeyIndicator",) not in self.log:
                    raise hs.TimeoutKilled("MovePos 가 넘겼다")
                return FakeHwp.MovePos(self, move_id, para, pos)
        for cls, at, text in ((SlowKey, 1, "KeyIndicator"), (SlowKey, 2, "KeyIndicator"), (SlowInfo, None, "CurrentPrintPage"),
                              (SlowPageMove, None, "MovePos")):
            f = self.plain(cls)
            if at:
                f.at = at
            with self.assertRaises(hs.TimeoutKilled) as e:
                self.run_write(f, TS_SPEC)
            self.assertIn(text, str(e.exception))
            self.assertEqual(self.saves(), [])

    STRAY = TS_SPEC.replace("## 적용범위\n", "## 적용범위\n첫째 문단.\n둘째 문단.\n셋째 문단.\n넷째 문단.\n")

    def test_stray_new_number_refused(self):
        """NumType 이 듣지 않아 표 새 번호 대신 쪽 새 번호가 들어가면(U-31 다른 꼴) 캡션 번호가 맞아도 저장하지 않는다 —
        쪽 번호가 본문 중간에서 다시 시작하는 문서를 막는다(검토 D1F-N02). 표가 본문 둘째 쪽이라 본문 첫 쪽 번호는 그대로.
        템플릿 본문에 이미 있던 새 번호는 세지 않는다."""
        class PageKind(FakeHwp):
            def AutoNumType(self, name):
                return FakeHwp.AutoNumType(self, "Page")
        r = self.run_write(self.plain(PageKind), self.STRAY)
        self.assert_fails(r, "계획에 없는 '새 번호로 시작' 조판 [['Page', '1']]")
        self.assertEqual((r["check"]["captions"]["mismatch"], r["check"]["page"]["body_first"]), ([], [2, 2]))
        self.assertEqual(r["check"]["captions"]["newnum_stray"], [["Page", "1"]])
        self.assertEqual(wd.stray_newnums([("Page", "1")], [("Page", "1"), ("Table", "1")],
                                          [{"type": "table", "cap": {"newnum": 1}}]), [])     # 템플릿 것·계획한 것은 뺀다
        self.assertEqual(wd.stray_newnums([], [("Table", "1"), ("Table", "1")], [{"type": "table", "cap": {"newnum": 1}}]),
                         [["Table", "1"]])                                     # 계획보다 많아도
        r = self.run_write(self.plain(tpl=self.page_newnum_tpl()), self.STRAY)  # 템플릿 본문 처음의 쪽 새 번호는 그대로 둔다
        self.assertTrue(r["ok"], r.get("error"))
        self.assertNotIn("newnum_stray", r["check"]["captions"])
        left = template_hwpml().replace("</SECTION></BODY>", '<P ParaShape="0" Style="3"><TEXT CharShape="0"><NEWNUM '
                                        'Number="1" NumberType="Table"/></TEXT></P></SECTION></BODY>')  # 제목 뒤 빈 그릇에
        (self.tmp / "out" / "doc.hwpx").unlink()                         # 템플릿 새 번호(본문 지우기에서 남음) — 쓰기 전에
        r = self.run_write(self.plain(tpl=left), self.STRAY)               # 이미 있던 것은 빼고 센다(검토 D2F-02)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(r["reused_empty_para"])

        class DeepPage(FakeHwp):                               # 쪽 새 번호가 캡션 안(깊은 자리)에 생기는 한/글 — 깊이 무관하게
            def _new_number(self, ps):                         # 센다(검토 D2F-02)
                ok = FakeHwp._new_number(self, ps)
                s_, e_ = self._top_paras()[self.caret]
                k = self.hwpml.find("<CAPTION", s_, e_)
                k = self.hwpml.find("<TEXT", k, e_)
                k = self.hwpml.find(">", k) + 1
                self.hwpml = self.hwpml[:k] + '<NEWNUM Number="3" NumberType="Page"/>' + self.hwpml[k:]
                return ok
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(self.plain(DeepPage), self.STRAY)
        self.assert_fails(r, "계획에 없는 '새 번호로 시작' 조판 [['Page', '3']]")
        self.assertEqual(r["check"]["captions"]["mismatch"], [])

class TestCleanAndFront(Base):
    """F-109 다시 입히기와 메시지 상자 자동 응답, 앞부분 서식 대조 (P-040 검토 4·8)."""
    HEAD = TS_SPEC.split("# 개요")[0].replace('"table_style": "tpl/table_style.json",', "") + "# 개요\n"
    PARA_SPEC = HEAD + "## 적용범위\n본 문서는 시험용이다.\n## 관련문서\n끝 문단.\n"      # 이웃 항목 스타일이 늘 다르다
    BODY_FIRST = HEAD + "본 문서는 시험용이다.\n## 관련문서\n끝 문단.\n"                # 첫 항목이 남은 문단과 같은 03

    def test_no_reapply_without_auto_yes(self):
        """자동 응답을 못 켜면 같은 스타일 다시 입히기를 하지 않는다 — 다시 입히면 '덮어 쓸까요?' 창이 떠 기다린다."""
        rules = TestWrite.style_rules()

        class NoMsgbox(rules):
            def SetMessageBoxMode(self, mode):
                raise AttributeError("SetMessageBoxMode")

            def _apply_style(self, idx):
                n = len(self.prompts)
                ok = rules._apply_style(self, idx)
                if len(self.prompts) > n:
                    raise RuntimeError("fake: '스타일 모양으로 덮어 쓸까요?' 창이 떠 답을 기다린다")
                return ok
        r = self.run_write(NoMsgbox(docs={"common.hwpx": template_leftover_hwpml()}), self.PARA_SPEC)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertFalse(r["msgbox_auto"])
        self.assertTrue(any("메시지 상자 자동 응답을 켜지 못했다" in w for w in r["warnings"]), r["warnings"])

    def test_front_format_change_is_warned(self):
        """'예'가 쓴 문단 밖(같은 스타일의 표지 문단)까지 스타일 모양으로 바꾸면 앞부분 서식 대조가 알린다(U-24)."""
        rules = TestWrite.style_rules()
        cover = P("표지 본문 글", STYLES.index("03_본문_내용")).replace('CharShape="0"', 'CharShape="2"')
        x = template_leftover_hwpml().replace(P("목     차", 1), cover + P("목     차", 1), 1)

        class Wide(rules):
            def _apply_style(self, idx):
                n = len(self.prompts)
                ok = rules._apply_style(self, idx)
                if len(self.prompts) > n and self.msgbox_mode & 0x10000:      # '예' → 같은 스타일 문단 모두
                    cs = self._attr(self._head_items(self.hwpml, "STYLE").get(str(idx), ""), "CharShape")
                    self.hwpml = re.sub(r'(<P ParaShape="\d+" Style="%d"><TEXT CharShape=")\d+"' % idx,
                                        lambda m: m.group(1) + cs + '"', self.hwpml)
                return ok
        r = self.run_write(Wide(docs={"common.hwpx": x}), self.BODY_FIRST)
        self.assertTrue(r["ok"], r.get("error"))
        self.assertTrue(self.f.prompts)
        self.assertEqual([c[1:] for c in r["check"]["front_format_changed"]],
                         [[["03_본문_내용", ["1300"]], ["03_본문_내용", ["1100"]]]])
        self.assertTrue(any("앞부분(표지 등) 문단 1곳" in w for w in r["warnings"]), r["warnings"])
        (self.tmp / "out" / "doc.hwpx").unlink()
        r = self.run_write(rules(docs={"common.hwpx": x}), self.BODY_FIRST)       # 대조군: 쓴 문단만 — 경고 없음
        self.assertTrue(r["ok"], r.get("error"))
        self.assertEqual(r["check"]["front_format_changed"], [])


def fw_template_modeled(case, head):
    """시작점 머리 head(공통 템플릿 경로의 꼴만 바꾼 것) + 본문으로 가짜 쓰기 → checks.spec.template_modeled."""
    return case.fw(head + case.BODY)["checks"]["spec"]["template_modeled"]


class TestFakeWrite(unittest.TestCase):
    """doc-writer 스킬 1-5단계의 가짜 전체 쓰기 tools/doc-writer/fake_write.py (P-051, 검토 D1-②-01·D1-③-01)."""

    def test_fake_write_passes_non_sum_specs(self):
        """SUM 이 아닌 명세에서도 판정이 맞다 — 그림·표가 없는 시작점(new_doc_spec)과 캡션 없는 표·그림 자리가 든 시험 명세
        (probe_spec) 모두 all_ok, 음성 대조 newnum_ignored 는 fail-closed(거절하거나 바른 번호)."""
        import fake_write as fw
        for name in ("new_doc_spec.md", "probe_spec.md"):
            out = fw.run(HERE.parent / "samples" / name)
            self.assertTrue(out["all_ok"], (name, out["checks"]))
            self.assertEqual(set(out["checks"]["newnum_ignored"]), {"fail_closed"})     # SUM 꼴 기대는 선택일 때만
        self.assertTrue(fw.run(HERE.parent / "samples" / "probe_spec.md")["newnum_ignored"]["ok"] is False)  # 그림 → 거절
        try:                                                                       # table_style null 은 표 서식 없음 — 끝까지
            nul = self.fw(self.HEAD.replace('"document_templates/technical-report/table_style.json"', "null") + self.BODY)
        except Exception as e:                                                     # noqa: BLE001 — 예외도 실패로(D8-③-01)
            self.fail("table_style null 에서 %s: %s" % (type(e).__name__, e))
        self.assertTrue(nul["all_ok"], nul["checks"])

    def test_fake_write_catches_wrong_numbers_saved(self):
        """음성 대조 — 새 번호가 듣지 않는데 캡션 대조까지 꺼진 작성기(틀린 번호로 저장)는 newnum_ignored.fail_closed 가 거짓."""
        import fake_write as fw
        orig = wd.caption_check
        wd.caption_check = lambda *a, **k: ([], [])
        try:
            out = fw.run(HERE.parent / "samples" / "probe_spec.md")
        finally:
            wd.caption_check = orig
        self.assertTrue(out["newnum_ignored"]["ok"])
        self.assertFalse(out["checks"]["newnum_ignored"]["fail_closed"])
        self.assertFalse(out["all_ok"])

    BODY = ("# 개요\n## 적용범위\n본문은 {{표:목록}}·{{그림:화면}} 을 본다.\n표: 목록\n| 가 | 나 |\n|---|---|\n| 1 | 2 |\n"
            '![화면](output_docs/NEW/fig/a.png "60x30")\n# 둘\n## 둘의 절\n')      # 둘째 장의 하위 절 — 흉내 개요 번호 되돌림(D3-③-09)

    def setUp(self):
        """시작점 머리(```json 블록까지) — 시험을 읽을 때가 아니라 돌 때 읽는다(시작점이 바뀌어도 다른 시험은 그대로 돈다)."""
        t = (HERE.parent / "samples" / "new_doc_spec.md").read_text(encoding="utf-8")
        m = re.search(r"```json[ \t]*\r?\n.*?\r?\n```[ \t]*\r?\n", t, re.S)
        self.assertTrue(m, "시작점에 ```json 머리가 없다")
        self.HEAD = t[:m.end()] + "\n"

        # Reusable tests use a synthetic style map, never a source project's SUM file.
        import json
        import fake_write as fw
        import test_table_style as fixture
        import table_style as ts
        self.fixture_root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.fixture_root, ignore_errors=True)
        import legacy_template
        self.enterContext(mock.patch.object(fw, "template", legacy_template.template))
        profile_source = Path(wd.profiles.load_profile(root=wd.ROOT)["_path"]).parent
        shutil.copytree(profile_source, self.fixture_root / "document_templates" / "technical-report", dirs_exist_ok=True)
        old_root = fw.ROOT
        fw.ROOT = self.fixture_root
        self.addCleanup(setattr, fw, "ROOT", old_root)
        style = ts.from_poc(fixture.poc_report(fixture.ref_doc()), "synthetic.hwpx",
                            default="용어", sections=("s1.",))
        path = self.fixture_root / "output_docs" / "SUM" / "table_style.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(style, ensure_ascii=False), encoding="utf-8")

    def fw(self, spec=None, sum_negative=False):
        """시작점 머리 + 캡션 표 하나·그림 하나(--dummy) 명세로 가짜 쓰기."""
        import fake_write as fw
        d = Path(tempfile.mkdtemp())
        try:
            p = d / "spec.md"
            p.write_text(spec or self.HEAD + self.BODY, encoding="utf-8")
            return fw.run(p, dummy=True, sum_negative=sum_negative)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_fake_write_checks_catch_sabotage(self):
        """판정마다 그 판정을 거짓으로 만드는 작성기·명세를 넣으면 그 판정이 거짓이고 all_ok 도 거짓이다 — 판정을 늘 참으로 바꾸면
        이 시험이 알린다(검토 P-051 D2-③-02). 바꾸지 않은 작은 명세는 모두 참."""
        base = self.fw()
        self.assertTrue(base["all_ok"], base["checks"])
        h = base["pictures=True"]["headings"]                                            # 흉내 개요 번호 — 둘째 장의 하위
        self.assertEqual((h["checked"], h["mismatch_count"], h["samples"]), (4, 0, [["1", "1."], ["1.1", "1.1."]]))  # 절('2.1')까지
        cap0, plan0, wc0 = wd._caption, wd.plan, wd.written_captions
        bad_caption = lambda *a, **k: ([{"at": "s1.p1", "what": "캡션 글자", "want": "표 1 목록", "got": "표 2 목록"}], [])
        self.assertTrue(fw_template_modeled(self, self.HEAD.replace("document_templates/technical-report/template.package.zip",
                                                                    "document_templates\\\\technical-report\\\\template.package.zip")))

        def no_newnum(kind):                           # 그 종류(표·그림)의 첫 개체 앞 새 번호를 넣지 않는 작성기
            return lambda label, n, title, styles, side, newnum=None: cap0(label, n, title, styles, side,
                                                                           None if label == kind else newnum)

        def drop(pred):                                # 계획에서 항목을 빼는 작성기
            return lambda blocks, styles, pictures=False: [x for x in plan0(blocks, styles, pictures) if not pred(x, pictures)]
        lit = self.HEAD + self.BODY + "목록은 표 1 과 같다.\n"
        cases = [
            ("text_checks_clean", "pictures=True", lit, []),
            ("no_warnings", "pictures=True", lit, []),
            ("template_modeled", "spec", self.HEAD.replace("template.package", "다른_템플릿") + self.BODY, []),
            ("newnum_as_planned", "pictures=True", None, [("_caption", no_newnum("표"))]),
            ("numbers_in_order", "pictures=True", None, [("_caption", no_newnum("그림"))]),
            ("refs_resolved", "pictures=True", None,
             [("_refs", lambda blocks: (lambda text: wd.REF_RX.sub(lambda m: m.group(1) + " 9", text)))]),
            ("page_kept", "pictures=True", None,
             [("print_page", lambda s, para, reads=None: (reads.append([2, 2]) if reads is not None else None) or 2)]),
            ("sides", "pictures=True", None, [("_caption", lambda label, n, title, styles, side, newnum=None: cap0(
                label, n, title, styles, "Bottom" if side == "Top" else "Top", newnum))]),
            ("captions_clean", "pictures=True", None,
             [("caption_check", lambda *a, **k: ([], [{"at": "s1.p1", "what": "정렬", "want": "Center", "got": "Left"}]))]),
            ("plain_figure_captions", "pictures=False", None,
             [("plan", drop(lambda x, pics: not pics and x.get("style") == wd.STYLES["caption"]))]),
            ("plan_pictures_eq_spec", "pictures=True", None, [("plan", drop(lambda x, pics: pics and x["type"] == "picture"))]),
            ("numbers_in_order", "pictures=True", None, [("plan", drop(lambda x, pics: pics and x["type"] == "picture"))]),
            ("ok", "pictures=True", None, [("caption_check", bad_caption)]),          # 작성기가 거절한 쓰기(D2F-05)
            ("ok", "pictures=False", None, [("caption_check", bad_caption)]),
            ("margins_half_char", "pictures=True", None,                                # 칸 위·아래 여백이 글자 크기 절반이 아님
             [("ts.pad_margin", lambda margin, cells, metrics: [510, 510, 400, 400])]),
            ("captions_written_eq_plan", "pictures=True", None,                         # 계획한 캡션 하나가 쓴 문서에 없음
             [("written_captions", lambda x, broot: wc0(x, broot)[:-1])]),
        ]
        for check, group, spec, patches in cases:
            with contextlib.ExitStack() as st:
                for name, value in patches:
                    obj, attr = (wd.ts, name[3:]) if name.startswith("ts.") else (wd, name)
                    st.enter_context(mock.patch.object(obj, attr, value))
                out = self.fw(spec)
            with self.subTest(check=check):
                self.assertIs(out["checks"][group][check], False, out["checks"][group])
                self.assertFalse(out["all_ok"])
                self.assertTrue(base["checks"][group][check])

    def test_fake_write_sum_negative_expectations(self):
        """SUM 꼴 음성 대조 기대(--sum-negative-control: 거절·어긋난 곳 수 = 명세 그림 수·그림 +1·표 맞음·첫 어긋남 그림 1→2)가
        작은 명세에서도 맞고, 표 번호가 틀리는 흉내(템플릿 본문 처음의 표 새 번호를 뺌 — 앞부분 표 3개가 번호를 민다)에서는
        tables_right 가 거짓이다(검토 D2-③-02 F10)."""
        import fake_write as fw
        out = self.fw(sum_negative=True)
        self.assertTrue(out["all_ok"], out["checks"])
        self.assertEqual(set(out["checks"]["newnum_ignored"]), {"fail_closed", "refused", "places_eq_pictures",
                                                                "pictures_plus_one", "tables_right", "first_mismatch_like_step7"})
        tpl0 = fw.template
        with mock.patch.object(fw, "template", lambda: tpl0().replace('<NEWNUM Number="1" NumberType="Table"/>', "", 1)):
            out = self.fw(sum_negative=True)
        self.assertFalse(out["checks"]["newnum_ignored"]["tables_right"])
        self.assertTrue(out["checks"]["pictures=True"]["numbers_in_order"])      # 작성기 새 번호가 듣는 길은 그대로 맞다
        self.assertFalse(out["all_ok"])
        nopic = '<PICTURE><SHAPEOBJECT NumberingType="Figure"/></PICTURE>'           # 표지 그림이 없는 흉내 — 새 번호가 듣지
        with mock.patch.object(fw, "template", lambda: tpl0().replace(nopic, "", 1)):  # 않아도 그림 번호가 맞아 거절이 없다
            out = self.fw(sum_negative=True)
        c = out["checks"]["newnum_ignored"]
        self.assertEqual((c["fail_closed"], c["refused"], c["places_eq_pictures"], c["pictures_plus_one"],
                          c["first_mismatch_like_step7"], c["tables_right"]), (True, False, False, False, False, True))
        self.assertFalse(out["all_ok"])

    def test_fake_write_refuses_paths_outside(self):
        """명세 경로(template·table_style·그림)가 절대 경로·드라이브·'..' 이면 아무것도 쓰지 않고 거절한다 — 흉내 바이트가 저장소
        밖 파일을 덮던 꼴(검토 P-051 D2-②-01). main 은 결과 JSON(refused_path)을 남기고 종료코드 2. out 은 명세 오류로 막힌다."""
        import fake_write as fw
        d = Path(tempfile.mkdtemp())
        made = []

        def inside_d():                               # 가짜 쓰기 임시 폴더를 d/a/b 아래에 — 가드가 깨져도 '../../' 가 d 안(D2F-06)
            made.append(d / "a" / "b" / ("t%d" % len(made)))
            made[-1].mkdir(parents=True)
            return str(made[-1])
        try:
            st = contextlib.ExitStack()
            st.enter_context(mock.patch.object(fw.tempfile, "mkdtemp", inside_d))
            victim = d / "victim.hwpx"
            victim.write_bytes(b"real template")
            pic = d / "real.png"
            pic.write_bytes(b"real picture")
            specs = [self.HEAD.replace('"document_templates/technical-report/template.package.zip"', '"%s"' % victim.as_posix())
                     + self.BODY,
                     self.HEAD + self.BODY.replace("output_docs/NEW/fig/a.png", pic.as_posix()),
                     self.HEAD + self.BODY.replace("output_docs/NEW/fig/a.png", "../../escape.png"),
                     self.HEAD.replace('"document_templates/technical-report/table_style.json"', '"K:/other/table_style.json"') + self.BODY]
            with st:
                for spec in specs:
                    with self.subTest(spec=spec[-80:]):
                        with self.assertRaises(fw.PathRefused):
                            self.fw(spec)
            self.assertEqual((victim.read_bytes(), pic.read_bytes()), (b"real template", b"real picture"))
            self.assertTrue(made and not (d / "a" / "escape.png").exists())           # '../../escape.png' 를 쓰지 않았다
            p, res = d / "spec.md", d / "res.json"

            def main_rc():                                # 예외가 main 밖으로 새면 오류가 아니라 실패로 — 끝 코드 2 + JSON 이어야
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        return fw.main([str(p), str(res)])
                    except (fw.PathRefused, wd.SpecError) as e:
                        self.fail("main 밖으로 %s 가 샜다(끝 코드 2 + 결과 JSON 이어야): %s" % (type(e).__name__, e))
            p.write_text(specs[0], encoding="utf-8")
            self.assertEqual(main_rc(), 2)
            import json
            self.assertEqual(json.loads(res.read_text(encoding="utf-8"))["refused_path"], victim.as_posix())
            out_spec = self.HEAD.replace('"output_docs/NEW/NEW_문서.hwpx"', '"%s"' % (d / "o.hwpx").as_posix()) + self.BODY
            with self.assertRaises(wd.SpecError):
                self.fw(out_spec)
            p.write_text(out_spec, encoding="utf-8")                                   # main: 명세 오류도 끝 코드 2 + JSON
            self.assertEqual(main_rc(), 2)
            got = json.loads(res.read_text(encoding="utf-8"))
            self.assertTrue(got["all_ok"] is False and got["error"].startswith("명세 오류:"), got)
            self.assertFalse((d / "o.hwpx").exists())
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_fake_write_main_never_leaves_stale_pass(self):
        """main 은 결과 JSON 을 먼저 all_ok false 로 덮는다 — 없는 표 서식 파일·없는 명세·UTF-8 이 아닌 명세는 끝 코드 2 + error,
        그 밖 예외로 멈춰도 지난 실행의 all_ok true 가 남지 않는다(검토 P-051 D4-②-03)."""
        import fake_write as fw
        import json
        d = Path(tempfile.mkdtemp())
        res, p = d / "res.json", d / "spec.md"

        def main_rc(*argv):                           # 지난 실행이 통과였던 자리 — 예외가 새면 오류가 아니라 실패로
            res.write_text('{"tool": "doc-writer/fake_write", "all_ok": true}', encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                try:
                    return fw.main(list(argv))
                except Exception as e:                # noqa: BLE001
                    self.fail("main 밖으로 %s 가 샜다: %s" % (type(e).__name__, e))

        def result():
            return json.loads(res.read_text(encoding="utf-8-sig"))
        try:
            p.write_text(self.HEAD.replace('"document_templates/technical-report/table_style.json"', '"output_docs/NEW/없는_서식.json"') + self.BODY,
                         encoding="utf-8")
            self.assertEqual(main_rc(str(p), str(res), "--dummy"), 2)
            self.assertTrue(result()["all_ok"] is False and result()["error"].startswith("명세 오류(FileNotFoundError)"), result())
            self.assertEqual(main_rc(str(d / "없는.md"), str(res)), 2)
            self.assertIs(result()["all_ok"], False)
            p.write_bytes(b"\xb0\xa1" + (self.HEAD + self.BODY).encode("utf-8"))   # UTF-8 이 아닌 명세(메모장 ANSI 꼴)
            self.assertEqual(main_rc(str(p), str(res)), 2)
            self.assertIn("UnicodeDecodeError", result()["error"])
            for head, why in ((self.HEAD.replace('"output_docs/NEW/NEW_문서.hwpx"', '"document_templates/technical-report/template.package.zip"'),
                               "명세 오류:"),                                   # ZIP 템플릿은 .hwpx 출력 검사에서 거절
                              (self.HEAD.replace('"document_templates/technical-report/table_style.json"', '"output_docs/SUM"'), "명세 오류("),   # 폴더
                              (self.HEAD.replace('"keys": {}', '"keys": {"{{과제명}}": "{{문서명}} 과제", "{{문서명}}": "설명서"}'), "명세 오류(MapError)")):   # 키 값 안 키
                p.write_text(head + self.BODY, encoding="utf-8")
                self.assertEqual(main_rc(str(p), str(res), "--dummy"), 2, why)
                self.assertTrue(result()["all_ok"] is False and result()["error"].startswith(why), result())
            p.write_text(self.HEAD + self.BODY, encoding="utf-8")

            def raw_rc(*argv):                        # 결과 자리를 미리 채우지 않고 — 예외가 새면 실패로
                with contextlib.redirect_stdout(io.StringIO()):
                    try:
                        return fw.main(list(argv))
                    except Exception as e:            # noqa: BLE001
                        self.fail("main 밖으로 %s 가 샜다: %s" % (type(e).__name__, e))
            keep = {d / "tpl.hwpx": b"PK\x03\x04\xff\xfe real template", d / "style.json": b'{"tables": {}}',   # 명세 밖 입력(UTF-8
                    # 이 아닌 바이너리도 — D7-③-05)·표지 없는 판정 JSON
                    d / "step8.json": b'{"poc": {}, "writer": {}, "all_ok": true}',           # (all_ok 가 있어도 — D7-②-01)·다른
                    d / "neg.json": b'{"tool": "negative_controls", "all_caught": true}'}     # 도구 표지(D8-③-04)도 덮지 않는다
            for f, b in keep.items():
                f.write_bytes(b)
            (d / "sub").mkdir()
            for target in (p, d / "sub" / ".." / p.name, *keep, d):     # 명세(다른 철자도)·템플릿·표 서식·폴더 — 지난 결과가
                self.assertEqual(raw_rc(str(p), str(target)), 2, target)  # 아니면 끝 코드 2·아무것도 쓰지 않는다(D6-②-01)
            self.assertEqual(raw_rc(str(p), str(d / "없는 폴더" / "r.json")), 2)          # 결과 폴더 없음
            (d / "파일").write_text("x", encoding="utf-8")
            self.assertEqual(raw_rc(str(p), str(d / "파일" / "r.json")), 2)              # 결과 폴더 자리가 파일(D6-③-06)
            self.assertEqual(p.read_text(encoding="utf-8"), self.HEAD + self.BODY)
            self.assertEqual({f: f.read_bytes() for f in keep}, keep)
            p.write_text(self.HEAD.replace('"document_templates/technical-report/table_style.json"', '"output_docs/NEW/없는_서식.json"') + self.BODY,
                         encoding="utf-8")
            res.write_bytes(b"\xef\xbb\xbf" + '{"tool": "doc-writer/fake_write", "all_ok": true}'.encode("utf-8"))   # BOM 붙은 지난 결과(메모장 저장)는 지난 결과다(D6F-N02)
            self.assertEqual(raw_rc(str(p), str(res), "--dummy"), 2)
            self.assertTrue(str(result().get("error", "")).startswith("명세 오류(FileNotFoundError)"), result())
            p.write_text(self.HEAD + self.BODY, encoding="utf-8")
            for err in (RuntimeError("흉내가 멈췄다"), hs.TimeoutKilled("흉내 시간초과")):   # 명세 쪽이 아닌 오류는 그대로 올리고
                res.write_text('{"tool": "doc-writer/fake_write", "all_ok": true}', encoding="utf-8")   # 결과는 '실행 중' 거짓으로 남는다
                with mock.patch.object(fw, "run", side_effect=err):
                    with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(type(err)):
                        fw.main([str(p), str(res)])
                self.assertTrue(result()["all_ok"] is False and result()["error"].startswith("실행 중"), result())
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
