#!/usr/bin/env python3
"""문서 작성기 (목표 3 첫 판) — 템플릿(.hwpx) + 내용 명세(.md) → 문서(.hwpx).

    python tools\\doc-writer\\write_doc.py <명세.md> [--force] [--timeout 180]

명세(.md) = ```json 머리(template·out·keys) + 본문. 본문 문법 (한 줄 = 한 블록):
  # 제목 … ####### 제목      → 프로파일의 heading 1~7 (번호는 한/글 개요 자동 번호 — 글자에 쓰지 않는다)
  일반 줄                    → 프로파일의 para 스타일
  - 항목 / 두 칸 들여 - 항목   → '○ 항목' / '  - 항목' (03_본문_내용)
  표: 제목  다음 줄부터 | … |  → 한/글 표(첫 줄 = 머리 칸, 둘째 줄 |---| 구분) + 표 위 캡션 '표 N 제목'. 칸 안 <br> = 칸 안 문단
  ![제목](그림 파일 "가로x세로")  → 그림(04_도표그림_제목 문단, 문서에 포함, 크기 mm) + 그림 아래 캡션 '그림 N 제목'.
                             캡션은 한/글 '캡션 넣기'(자동 번호)로 달고 캡션 문단에 04_도표그림_제목(P-049, attach_caption).
                             파일이 없으면 '※ 그림 삽입 필요: 제목 (출처: …)'(14_도움말_파란색) 메모 + 자리 표시 그림(회색 상자,
                             PLACEHOLDER)에 같은 캡션 — 한/글 자동 번호가 명세 번호와 어긋나지 않게. --no-pictures 면 그림 없이
                             메모 + 캡션 글자 문단 '그림 N 제목'(04_도표그림_제목, 예전 꼴)
                             한/글은 캡션과 관계없이 표·그림을 모두 센다(실측 P-050). 그래서 본문 첫 그림·첫 캡션 표, 그리고
                             캡션 없는 표 뒤 첫 캡션 표가 든 문단 처음에 '새 번호로 시작'(NewNumber — 그 명세 번호)을 넣는다
                             (new_number) — 템플릿 앞부분 개체·캡션 없는 표가 본문 번호를 밀지 않게
  > 내용                     → '※ 작성 필요: 내용'(14_도움말_파란색) — 채운 뒤 지운다(D-016)
  <!-- … -->                → 명세 메모 (문서에 넣지 않음)
  {{그림:캡션}} · {{표:캡션}}  → 그 캡션의 번호 '그림 N' · '표 N' (본문·항목·메모·표 칸 글자 안, P-037). 없는 캡션·같은 캡션 둘은 명세 오류
  {{절:제목}}                → 그 절의 '번호 제목'(예 '4.3.4.1 모의 시작' — 명세 제목 차례로 센 번호, P-051). 없는 제목·같은 제목 둘·
                             수준을 건너뛴 제목은 명세 오류. 바로 뒤 단계 'a)'·범위 'a)~b)'·나열 'a)·b)'(조사 '의', 이음 ~·～·〜·∼·
                             -·–·—·부터 — '에서' 는 아니다, 나열 쉼표·가운뎃점·및·와·과)는 원소마다 그 절 바로 아래 단계 줄('N) …' —
                             번호 뒤 빈칸, 문단·항목. 띄어 쓴 나열·조사 머리 '4) 및 5)는'·'3) 의 결과' 는 아니다) 수와, 인용에 붙지 않은
                             범위 'a)~b)' 는 단계 줄이 있는 절의 문단·항목에서 그 절의 단계 수와 대조해 어긋나면 경고. 단계 하나 뒤가 또
                             절·글자 인용이면 나열 번호('1) {{절:가}} 2) {{절:나}}' — 조사 '의' 로 이었으면 단계), 그 밖의 글 나열은
                             단계로 읽는다(나열이면 인용 뒤에 쉼표). 글자로 쓴 절 번호('4.3.4.1 모의 시작'·
                             '4.3.4.1절'·'제3장' — 맞아도 낡을 수 있다)·인용 밖
                             글자 '표 N'·'표N'·'그림 N'(숫자에 붙은 세는 말 '표 3개'·'그림 2장'·'표 3가지' 빼고)·제목 수준 건너뜀도
                             경고(text_checks). 점 든 번호 뒤 글이 그 절 제목이 아닌 곳·이 문서에 없는 '3.1.1항'·낱말일 수 있는
                             '1.1절차'·인용 뒤에 떨어진 범위·캡션 안 글자 번호는 의심으로 알린다(고칠 것 아님 — 인용이 아니면
                             {{글자:…}} 로 감싸 두면 경고가 없어진다)
  {{글자:…}}                 → 그 글자 그대로, 검사 밖 — 다른 문서의 절 번호('{{글자:체계사양서 1.1 적용범위}}')처럼 이 문서 절과
                             번호·제목이 같은 글자 인용, 보통 글('{{글자:1.2 초}}'). 바로 뒤 단계('{{글자:…}}의 2)~5)')도 보지 않는다
  제목·캡션 안에는 {{…}} 인용을 쓰지 않는다(명세 오류 — 번호로 바꾸지 않는 자리)
json 머리(P-037, D-036):
  keys  {"{{키}}": 값}       → 템플릿 모든 자리(머리말·꼬리말 포함)를 그 값으로(AllReplace). 빈 값은 그대로 둔다
        {"{{키}}": [값, …]}  → 자리별 값: 템플릿 본문(표지·표 칸) 자리마다 문서 차례대로 — 값 수 = 자리 수.
                                '다시 찾기'로 하나씩 찾아 지우고 넣는다. 빈 값은 지우기, 키 자신은 그대로 두기
  front {"글자": 값 | [값, …]} → 표지 등 템플릿 글자(양식 예시)를 자리별 값과 같은 방식으로 바꾸거나 지운다(D-016)
  styles {자리: 스타일}      → 쓰는 스타일 이름 바꾸기(기본값은 선택한 profile의 styles). heading 은 '… {level}' 꼴
                                (수준 1~7 마다 다른 이름 — 수준 1·2 이름이 같으면 명세 오류, D8-①-01), 그 밖의 자리 para·item·need·
                                caption·th·td·anchor·figure. 이름은 템플릿에 있어야 한다
  table_style "서식.json"    → 표 서식(P-040, D-042): 참고 문서 표의 테두리·배경·제목 셀·안 여백·칸 스타일을
                                입힌다(table_style.py — 캡션으로 참고 표를 고르고, 없으면 default). 테두리/배경·제목 셀은
                                칸 글자 뒤, 안 여백은 마지막 칸 뒤. 칸 너비는 표를 만들 때 칸 글자 폭 + 공백 2칸 여유(본문 폭을
                                넘으면 긴 칸만 줄임)이고 표는 가운데 정렬(P-041, D-044). 쓴 뒤 칸마다 대조해 다르면 경고.
                                서식 파일이 없거나 고를 서식이 없는 표도 칸 너비 맞춤·가운데 정렬은 한다 — 테두리·제목 셀은
                                한/글 기본 그대로(P-045, fit_plan)
                                칸 안 여백 위·아래는 모든 표에서 칸 글자 크기의 절반(P-048, ts.pad_margin) — 왼·오는 참고 표 값
                                (서식 계획이 없는 표는 한/글 기본)
첫 제목은 템플릿 본문 첫 장 제목(공통 템플릿 '개 요')과 같아야 하고 그 문단을 그대로 쓴다 — 나머지는 문서 끝에 차례로 붙인다.

쓰고 나서 HWPML 로 확인한다: 앞부분(표지·이력서·목차·머리말·꼬리말)은 키 바꾸기 말고는 그대로, 붙인 블록의 글자·스타일·
표 칸 글자가 명세대로, 표·그림 캡션 글자(자동 번호 포함)·캡션 스타일이 명세대로(P-049), 최상위 문단 수 = 템플릿 + 붙인 블록
수, 본문 첫 쪽 인쇄 번호가 쓰기 전과 같음(P-050 — 새 번호가 템플릿 쪽 새 번호를 무효로 하지 않았나, print_page — 못 읽으면
경고만), 제목마다 한/글 개요 번호(GetHeadingString)의 숫자가 명세 제목 차례로 센 번호와 같음(P-051 — {{절:제목}} 인용에 쓴
번호, heading_check — 못 읽으면 경고만, {{절:}} 인용이 없는 명세는 숫자만 다르거나 번호 꼴이 숫자가 아니면 경고만 — 제목 수가
다르거나 번호 없는 제목('' · 글머리표처럼 번호 꼴 글자가 없음)이면 거절). 어긋나면 저장하지 않는다(종료코드 1).
남은 {{키}} 와 작성 필요 메모·그림 자리는 보고서(<출력>.write_report.md)의 '추가 내용 필요'로 모은다.
목차(차례)는 채우지 않는다 — 본문을 다 쓴 뒤 붙인다(D-017).

종료코드: 0 성공 / 1 확인 실패·저장 실패 / 2 명세 오류·사전조건 / 3 평문 저장 / 4 열기 실패 / 5 시간초과 / 6 COM 없음
"""
import argparse
import datetime
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path, PureWindowsPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "backends" / "hwp" / "scripts"))
sys.path.insert(0, str(ROOT / "tools" / "hwpx-drm" / "scripts"))
import hwp_session as hs        # noqa: E402
import hwpml_parse as hp        # noqa: E402
import hwpx_api as api          # noqa: E402
import render_md as rm          # noqa: E402
import table_style as ts        # noqa: E402
import template_profiles as profiles

KEY_RX = re.compile(r"\{\{[^{}]+\}\}")
TOP = re.compile(r"^s(\d+)\.p(\d+)$")
STYLES = profiles.resolve_styles(root=ROOT)
BULLETS = ("○ ", "  - ", "    · ")
NEED = "※ 작성 필요: %s"
FIGURE = "※ 그림 삽입 필요: %s (출처: %s)"
# 그림 파일이 없을 때 넣는 자리 표시 그림(회색 상자, P-049) — 캡션을 달 개체가 있어야 한/글 그림 자동 번호가 명세 번호와 같다
PLACEHOLDER = HERE / "assets" / "figure_placeholder.png"
PLACEHOLDER_MM = [80.0, 45.0]                                 # 명세에 크기가 없을 때 자리 표시 그림 크기(mm)
CAPTION_NUM = {"table": "Table", "picture": "Figure"}         # 캡션 자동 번호 종류(HWPML AUTONUM NumberType, 어휘 채취)
# ![제목](그림 파일 "가로x세로") — 파일이 있으면 그림을 넣고(크기 mm), 없거나 --no-pictures 면 '그림 삽입 필요' 자리 표시
FIG_RX = re.compile(r'^!\[([^\]]*)\]\(([^)"]*?)(?:\s+"(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)")?\)\s*$')
# {{그림:캡션}} → '그림 N' (P-037) · {{절:제목}} → '번호 제목' (P-051) · {{글자:…}} → 그 글자 그대로(검사 밖 — 다른 문서의 절 번호 등)
REF_RX = re.compile(r"\{\{(그림|표|절|글자):([^{}]+)\}\}")
# text_checks 글자 꼴(P-051). 빈칸은 줄바꿈 아닌 모든 빈칸(NBSP·전각 빈칸 — 검토 D4-①-02), 단계 번호는 네 자리까지(D4-①-07)
_SP = r"[^\S\r\n]"
_CONN = r"(?:[~～〜∼\-－–—]|부터)"                          # 범위 이음: 물결 넷·줄표 넷·'부터'(D3-①-01). '에서' 는 범위가 아니다
#                                                             ('4)에서 2)로 돌아간다' — 검토 D5-①-01)
_SEP = r"(?:[,·・ㆍ]|및|와|과)"                              # 나열: 쉼표·가운뎃점(·・ㆍ — 'ㆍ' 는 한글 입력기, D6-①-N04)·'및'·'와'·'과'
#                                                             (D4-①-01 — 쉼표는 범위가 아니다)
_ITEM = r"(\d{1,4})\)(?:%s*%s%s*(\d{1,4})\))?" % (_SP, _CONN, _SP)              # 단계 'a)' · 범위 'a)~b)'
# 단계 줄 '1) …' — 번호 뒤 빈칸('4)와 5)는'·'3)의 결과' 같은 문단 머리는 단계가 아니다 — D5-①-02). 띄어 쓴 범위·나열·조사 머리
# '7) ~ 7)'·'4) 및 5)는'·'4) 또는 5)는'·'4) 에서 2)로'·'3) 의 결과' 도 단계 줄이 아니다(D4-①-06·D6-①-01)
_STEP_HEAD = r"(?:%s|%s|또는|그리고|에서)" % (_CONN, _SEP)
STEP_RX = re.compile(r"^(\d{1,4})\)(?=%s)(?!%s*%s%s*\d{1,4}\))(?!%s*(?:의|와|과|에서)%s)" % (_SP, _SP, _STEP_HEAD, _SP, _SP, _SP))
STEPS_RX = re.compile(r"%s*(?:의%s*)?%s" % (_SP, _SP, _ITEM))   # 절 인용 바로 뒤(조사 '의' 앞뒤 빈칸 — D3F-N05) 첫 단계·범위
STEPS_MORE_RX = re.compile(r"%s*%s%s*%s" % (_SP, _SEP, _SP, _ITEM))   # 이어지는 나열 '·7)'·', 9)'·' 및 9)'(원소마다 대조)
RANGE_RX = re.compile(r"(?<![\d)])(\d{1,4})\)%s*%s%s*(\d{1,4})\)" % (_SP, _CONN, _SP))   # 인용에 붙지 않은 범위(D3-③-06)
SECNUM_RX = re.compile(r"(?<![\dA-Za-z.])(\d+(?:\.\d+)*)\.?%s+(?=\S)" % _SP)   # 글자 절 번호 후보 '4.3.4.1 '·'1.1. '
# 붙여 쓴 글자 절·장 번호 '4.3.4.1절'·'3.1항'·'제3장' — 인용이 뚜렷한 꼴(검토 D3-①-03). 뒤가 조사가 아닌 한글이면 낱말일 수
# 있다('1.1절차'·'3.1항목'·'제3장비' — D4-①-05) — 고칠 것이 아니라 의심(SECSUFFIX_TAIL 로 가른다)
SECSUFFIX_RX = re.compile(r"(?<![\dA-Za-z.])(?:(\d+(?:\.\d+)+)(?:절|항)|제(\d+)장)")
SECSUFFIX_TAIL = ("으로", "까지", "부터", "참조", "참고", "처럼", "보다", "마다", "은", "는", "이", "가", "을", "를", "의", "에", "과",
                  "와", "로", "도", "만", "및")
# 인용 밖 글자 번호 '표 3'·'표3' — 숫자에 붙은 세는 말('표 3개'·'그림 2장'·'표 3가지'·'표 4행')은 번호가 아니다(검토 D2-①-05·
# D3-①-05). 띄운 글('표 3 개요', '그림 2 장비 구성도' — 캡션·제목 첫 글자)과 조사 '가'('그림 2가 보여 준다')는 번호다(D3-③-01·
# D4-①-03 — 세는 말은 '가' 한 글자가 아니라 '가지')
LITERAL_RX = re.compile(r"(?<![가-힣A-Za-z0-9])(?:표|그림)%s*\d+(?!\d)(?![개장건종행열쪽줄칸점]|가지)" % _SP)
HANGUL_RX = re.compile(r"[가-힣]")
TEXT_CHECK_KINDS = ("section", "literal", "levels")         # text_checks 의 고칠 것(suspect·ranges 는 기록·경고만)
NONBODY = ("header", "footer", "footnote", "endnote")          # 자리별 값을 쓰지 않는 자리(다시 찾기 차례 미실측)
FIND_OPTIONS = dict(api.REPLACE_OPTIONS, ReplaceMode=0)       # 다시 찾기(RepeatFind) — 바꾸기 없이 찾기만
# 메시지 상자 자동 응답(SetMessageBoxMode): 확인 · 확인/취소의 확인 · 예/아니오/취소의 예 · 예/아니오의 예 (P-038).
# 본문을 쓰는 동안만 켠다 — 표 뒤 빈 문단(한/글이 만든 것)에 스타일을 입히면 '본문을 [스타일] 스타일 모양으로 덮어 쓸까요?'
MSGBOX_YES = 0x00000001 | 0x00000010 | 0x00001000 | 0x00010000
# 표 서식(P-040, D-042) 종류 — 종류마다 따로 입히고, 표 셋에서 실패한 종류는 나머지 표에서 끈다(검토 P-040 2)
FORMAT_KINDS = ("center", "anchor_margin", "width", "border", "header", "margin", "caption")
FORMAT_NAMES = {"center": "가운데 정렬", "anchor_margin": "표 문단 여백", "width": "칸 너비", "border": "칸 테두리/배경",
                "header": "제목 셀", "margin": "안 여백", "caption": "캡션 자리"}
FORMAT_OFF_AFTER = 3
BORDER_KEYS = ("L", "R", "T", "B", "fill")      # 칸 서식의 선·배경 — CellBorderFill 로 입힌다
CELL_LR = 1020          # 표를 만들 때 칸 안 왼쪽+오른쪽 여백(HWPUNIT) — 실측 G1 CellMarginLeft·Right 510. ColWidth 는 이를 뺀 값(U-26)


class SpecError(api.MapError):
    code = 2


# ------------------------------------------------------------------ 명세

def parse_spec(text):
    """명세 글 → (머리 dict, 블록 목록). 블록: heading(level,text) para item(level) need table(caption,rows,header) figure."""
    m = re.search(r"```json[ \t]*\r?\n(.*?)\r?\n```", text, re.S)
    if not m:
        raise SpecError("명세 첫머리에 ```json 블록(template·out·keys)이 없다")
    try:
        meta = json.loads(m.group(1))
    except ValueError as e:
        raise SpecError("명세 json 오류: %s" % e)
    if not isinstance(meta, dict):                              # 머리 꼴이 틀리면 traceback 이 아니라 명세 오류(끝 코드 2 — D6-②-02)
        raise SpecError("명세 json 머리는 {이름: 값} 이어야 한다")
    for k in ("template", "out"):
        if not meta.get(k):
            raise SpecError("명세 json 에 %s 가 없다" % k)
    for k in ("template", "out", "table_style", "profile"):                # null 은 '없음'(표 서식 없음 — 앞 판과 같게, D7-②-N04)
        if meta.get(k) is not None and not isinstance(meta[k], str):
            raise SpecError("명세 json 의 %s 는 경로 글자여야 한다: %r" % (k, meta[k]))
    if meta.get("protection", "preserve") not in ("preserve", "required"):
        raise SpecError("protection must be preserve or required")
    for k in ("keys", "styles"):
        if not isinstance(meta.get(k) or {}, dict):
            raise SpecError("명세 json 의 %s 는 {이름: 값} 이어야 한다" % k)
    if not all(isinstance(a, str) and isinstance(b, str) and b for a, b in (meta.get("styles") or {}).items()):
        raise SpecError("명세 json 의 styles 는 {자리: 스타일 이름} 글자여야 한다")
    try:                                                        # 제목 스타일의 '{level}' 자리 오타도 명세 오류(D7-②-03)
        dict(profiles.load_profile(meta.get("profile"), ROOT)["styles"], **(meta.get("styles") or {}))["heading"].format(level=1)
    except Exception as e:                                      # noqa: BLE001 — 자리 이름·괄호·형 오류 모두(KeyError·ValueError·
        raise SpecError("명세 json 의 styles.heading 은 '{level}' 자리만 쓴다: %r" % e)   # IndexError·AttributeError·TypeError)
    head_style = dict(profiles.load_profile(meta.get("profile"), ROOT)["styles"], **(meta.get("styles") or {}))["heading"]
    if head_style.format(level=1) == head_style.format(level=2):    # '{level}' 자리가 없다 — 모든 수준이 한 스타일(D8-①-01)
        raise SpecError("명세 json 의 styles.heading 에 '{level}' 자리가 없다(모든 제목이 한 스타일이 된다): %r" % head_style)
    if not str(meta["out"]).lower().endswith(".hwpx"):
        raise SpecError("out 은 .hwpx 여야 한다")
    if outside(meta["out"]):                                    # 저장 뒤 md 경로(ROOT 기준)를 못 셈(검토 P-051 D2-② 범위 밖)
        raise SpecError("out 은 저장소 안 상대 경로여야 한다(절대 경로·드라이브·'..' 안 됨): %r" % meta["out"])
    keys = meta.get("keys") or {}
    for k, v in keys.items():
        if not KEY_RX.fullmatch(k):
            raise SpecError("keys 의 이름은 {{키}} 꼴이어야 한다: %r" % k)
        _check_values("keys", k, v)
    front = meta.get("front") or {}
    if not isinstance(front, dict):
        raise SpecError("front 는 {찾을 글자: 값} 이어야 한다")
    for k, v in front.items():
        if not k or "{{" in k or "\n" in k or "\r" in k:
            raise SpecError("front 의 찾을 글자는 한 줄이고 {{키}} 를 담지 않는다: %r" % k)
        _check_values("front", k, v)
    body = re.sub(r"<!--.*?-->", "", text[m.end():], flags=re.S)
    lines = body.splitlines()
    blocks, caption, i = [], None, 0
    while i < len(lines):
        ln = lines[i].rstrip()
        i += 1
        if not ln.strip():
            continue
        h = re.match(r"^(#{1,7})[ \t]+(\S.*)$", ln)
        if h:
            blocks.append({"kind": "heading", "level": len(h.group(1)), "text": h.group(2).strip()})
        elif ln.startswith("표:"):
            caption = ln[2:].strip()
        elif ln.lstrip().startswith("|"):
            rows = [ln]
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append(lines[i].rstrip())
                i += 1
            blocks.append(parse_table(rows, caption))
            caption = None
            continue
        elif re.match(r"^\s*[-*][ \t]+\S", ln):
            ind = len(ln) - len(ln.lstrip())
            level = min(ind // 2, len(BULLETS) - 1)
            blocks.append({"kind": "item", "level": level, "text": re.sub(r"^\s*[-*][ \t]+", "", ln).strip()})
        elif ln.startswith(">"):
            blocks.append({"kind": "need", "text": ln[1:].strip()})
        elif FIG_RX.match(ln):
            f = FIG_RX.match(ln)
            size = [float(f.group(3)), float(f.group(4))] if f.group(3) else None
            if size and min(size) <= 0:                         # 0 mm 그림(자리 표시 그림 포함)은 명세 오류(검토 P-049 D1-①-02)
                raise SpecError("그림 크기는 0 보다 커야 한다: %s" % ln.strip())
            blocks.append({"kind": "figure", "caption": f.group(1).strip(), "source": f.group(2).strip(), "size": size})
        else:
            blocks.append({"kind": "para", "text": ln.strip()})
        if caption is not None and blocks and blocks[-1]["kind"] != "table" and not ln.startswith("표:"):
            raise SpecError("'표: %s' 다음 줄은 표(| … |)여야 한다" % caption)
    if caption is not None:
        raise SpecError("'표: %s' 뒤에 표가 없다" % caption)
    if not blocks or blocks[0]["kind"] != "heading" or blocks[0]["level"] != 1:
        raise SpecError("본문 첫 블록은 '# 제목'(템플릿 첫 장 제목)이어야 한다")
    for b in blocks:                                            # 제목·캡션 글자는 인용을 번호로 바꾸지 않고 그대로 쓴다(P-051)
        t = b["text"] if b["kind"] == "heading" else b.get("caption") if b["kind"] in ("table", "figure") else None
        if t and REF_RX.search(t):
            raise SpecError("제목·캡션 안에는 {{…}} 인용을 쓰지 않는다(번호로 바꾸지 않는 자리): %r" % t)
    return meta, blocks


def outside(p):
    """저장소 밖을 가리킬 수 있는 명세 경로인가 — 절대 경로·드라이브('K:')·'..'(Windows·POSIX 꼴 모두, P-051)."""
    w = PureWindowsPath(str(p))
    return Path(str(p)).is_absolute() or bool(w.drive or w.root) or ".." in w.parts


def _check_values(where, k, v):
    """값 = 문자열 또는 자리별 문자열 목록(비지 않음). 줄바꿈은 안 된다(AllReplace·InsertText 줄바꿈 미실측)."""
    vals = v if isinstance(v, list) else [v]
    if not vals or not all(isinstance(x, str) for x in vals):
        raise SpecError("%s 값은 문자열 또는 자리별 문자열 목록이어야 한다: %r" % (where, k))
    if any("\n" in x or "\r" in x for x in vals):
        raise SpecError("%s 값에 줄바꿈을 쓸 수 없다: %r" % (where, k))


def parse_table(rows, caption):
    def cells(r):
        r = r.strip()
        if r.startswith("|"):
            r = r[1:]
        if r.endswith("|"):
            r = r[:-1]
        return [c.strip().replace("<br>", "\n") for c in r.split("|")]
    grid = [cells(r) for r in rows]
    header = len(grid) > 1 and all(re.fullmatch(r":?-{3,}:?", c.replace("\n", "")) for c in grid[1])
    if header:
        grid = [grid[0]] + grid[2:]
    width = len(grid[0])
    if any(len(r) != width for r in grid):
        raise SpecError("표 줄마다 칸 수가 다르다: %s" % [len(r) for r in grid])
    return {"kind": "table", "caption": caption, "rows": grid, "header": header}


def plan(blocks, styles, pictures=False):
    """블록 → 쓸 항목(최상위 문단 하나씩): {"type": "para", "text", "style"} | {"type": "table", "rows", "header", "caption",
    "cap"} | {"type": "picture", "path", "size", "style", "cap"}. 첫 제목은 템플릿 문단을 쓰므로 빠진다. 표·그림 번호는 차례로
    매긴다. cap = 한/글 '캡션 넣기'로 달 캡션(P-049, _caption) — 표는 위, 그림은 아래. 캡션 없는 표는 cap None(번호 없음).
    cap["newnum"]: 그 개체 앞 '새 번호로 시작' — 첫 그림(1)·첫 캡션 표(1)·캡션 없는 표 뒤 첫 캡션 표(그 명세 번호). 한/글은
    캡션 없는 표·템플릿 앞부분 개체까지 번호를 세므로(실측 P-050 F-168·F-169) 명세 번호에 다시 맞춘다.
    pictures: 그림 파일(ROOT 기준)이 있으면 그림을 넣는다. 없으면 '그림 삽입 필요' 메모 + 자리 표시 그림(PLACEHOLDER)에 같은
    캡션 — 캡션을 달 개체가 없으면 한/글 자동 번호가 그 뒤 그림부터 명세 번호보다 하나씩 작아진다. pictures=False 면 그림 없이
    메모 + 캡션 글자 문단(한/글 그림 자동 번호를 쓰지 않으므로 번호가 어긋나지 않는다).
    글자 안 {{그림:캡션}} · {{표:캡션}} 은 그 번호로 바꾼다(P-037) — 앞에 그림·표가 늘어도 인용이 따라간다."""
    ref = _refs(blocks)
    out, nt, nf, reset_t = [], 0, 0, True        # reset_t: 다음 캡션 표 앞에 새 번호(첫 캡션 표 · 캡션 없는 표 뒤 — P-050)
    for b in blocks[1:]:
        k = b["kind"]
        if k == "heading":
            out.append({"type": "para", "text": b["text"], "style": styles["heading"].format(level=b["level"])})
        elif k == "para":
            out.append({"type": "para", "text": ref(b["text"]), "style": styles["para"]})
        elif k == "item":
            out.append({"type": "para", "text": BULLETS[b["level"]] + ref(b["text"]), "style": styles["item"]})
        elif k == "need":
            out.append({"type": "para", "text": NEED % ref(b["text"]), "style": styles["need"], "need": True})
        elif k == "figure":
            nf += 1
            src = b["source"]
            cap = _caption("그림", nf, b["caption"], styles, "Bottom", 1 if nf == 1 else None)
            if pictures and src and (ROOT / src).is_file():
                out.append({"type": "picture", "path": src, "size": b.get("size"), "style": styles["figure"], "cap": cap})
                continue
            out.append({"type": "para", "text": FIGURE % (b["caption"], src or "-"), "style": styles["need"],
                        "need": True, "figure": True})
            if pictures:
                if not PLACEHOLDER.is_file():
                    raise SpecError("그림 자리 표시 파일이 없다: %s" % PLACEHOLDER)
                out.append({"type": "picture", "path": str(PLACEHOLDER), "size": b.get("size") or list(PLACEHOLDER_MM),
                            "style": styles["figure"], "cap": cap, "placeholder": True})
            else:
                out.append({"type": "para", "text": cap["text"], "style": styles["caption"]})
        elif k == "table":
            cap = None
            if b["caption"]:
                nt += 1
                cap = _caption("표", nt, b["caption"], styles, "Top", nt if reset_t else None)
                reset_t = False
            else:                                              # 캡션 없는 표도 한/글 표 번호 하나를 쓴다(실측 P-050 C5)
                reset_t = True
            out.append({"type": "table", "rows": [[ref(c) for c in row] for row in b["rows"]], "header": b["header"],
                        "caption": b["caption"], "cap": cap})
    return out


def _caption(label, n, title, styles, side, newnum=None):
    """한/글 캡션 계획 — text = 쓴 뒤 캡션 글자 '표 N 제목'(한/글이 넣는 '표 '·자동 번호·빈칸 뒤에 제목), side = 자리
    (HWPML CAPTION Side: 표 위 Top · 그림 아래 Bottom — 지금까지 캡션 글자 문단의 자리와 같다). newnum = 그 개체 문단 처음에
    넣을 '새 번호로 시작' 번호(new_number — 본문 첫 그림·첫 캡션 표·캡션 없는 표 뒤 첫 캡션 표, P-050) 또는 None."""
    return {"text": "%s %d %s" % (label, n, title), "title": title, "style": styles["caption"], "side": side,
            "newnum": newnum}


def _refs(blocks):
    """캡션 → 번호(plan 과 같은 차례: 그림은 모두, 표는 캡션 있는 것만)·절 제목 → 번호(heading_numbers) → 글자 안 인용을
    바꾸는 함수. {{절:제목}} → '번호 제목'(P-051 — 앞에 절이 늘거나 줄어도 따라가고, 제목을 바꾸거나 지우면 명세 오류).
    {{글자:…}} → 안의 글자 그대로(검사 밖)."""
    nums, nf, nt = {"그림": {}, "표": {}, "절": {}}, 0, 0
    for b in blocks[1:]:
        if b["kind"] == "figure":
            nf += 1
            nums["그림"].setdefault(b["caption"], []).append(nf)
        elif b["kind"] == "table" and b["caption"]:
            nt += 1
            nums["표"].setdefault(b["caption"], []).append(nt)
    for n, t, _ in heading_numbers(blocks):
        nums["절"].setdefault(t, []).append(n)

    def sub(m):
        kind, cap = m.group(1), m.group(2).strip()
        if kind == "글자":                                      # 글자 그대로 — text_checks 가 보지 않는다(다른 문서의 절 번호 등, D2F-01)
            return m.group(2)
        got = nums[kind].get(cap)
        if kind == "절":
            if not got:
                raise SpecError("인용한 절 제목이 없다: %r" % cap)
            if len(got) > 1:
                raise SpecError("같은 제목의 절이 %d개(%s)라 인용이 모호하다: %r" % (len(got), "·".join(got), cap))
            if "0" in got[0].split("."):                        # 건너뛴 수준 — 한/글이 그 자리를 어떻게 세는지 미실측(D2-①-06)
                raise SpecError("수준을 건너뛴 제목이라 번호를 셀 수 없다: %r (%s)" % (cap, got[0]))
            return "%s %s" % (got[0], cap)
        if not got:
            raise SpecError("인용한 %s 캡션이 없다: %r" % (kind, cap))
        if len(got) > 1:
            raise SpecError("같은 캡션의 %s 이 %d개라 인용이 모호하다: %r" % (kind, len(got), cap))
        return "%s %d" % (kind, got[0])
    return lambda text: REF_RX.sub(sub, text)


def heading_numbers(blocks):
    """명세 제목 → 절 번호(첫 제목이 1, 수준마다 이어 세고 아래 수준은 0 부터) → [(번호 '4.3.4.1', 제목, 블록 차례)] (P-051).
    한/글 개요 자동 번호와 같은 셈이라고 본다 — 실측 P-029 [T1](U-17): 생성기가 COMSAF 개요로 바꾼 템플릿 제목(SRS 36·SDP 146)의
    GetHeadingString('1.1.' 꼴) 숫자가 차례로 센 양식 번호와 같았고, 공통 템플릿(SRS 바탕)의 개요 문단은 본문 첫 장 제목
    하나다(output_docs/templates/md/COMMON.md). 쓴 문서에서는 heading_check 가 제목마다 다시 읽어 견준다(U-32).
    수준을 건너뛴 제목은 그 자리가 0 이 된다('1.0.1') — 한/글이 어떻게 세는지 미실측이라 {{절:}} 인용은 명세 오류(_refs)."""
    out, cnt = [], [0] * 7
    for i, b in enumerate(blocks):
        if b["kind"] == "heading":
            lv = b["level"]
            cnt[lv - 1] += 1
            cnt[lv:] = [0] * (7 - lv)
            out.append((".".join(str(c) for c in cnt[:lv]), b["text"], i))
    return out


def _block_texts(b):
    """블록의 글자 — 표는 칸과 캡션(검토 D2-①-03), 그림은 캡션."""
    return [t for t, _ in _block_parts(b)]


def _block_parts(b):
    """블록의 글자와 자리 [(글자, 'text'|'cell'|'caption')] — 캡션은 인용({{…}})을 쓸 수 없는 자리라 따로 다룬다."""
    if b["kind"] == "table":
        return [(c, "cell") for row in b["rows"] for c in row] + ([(b["caption"], "caption")] if b.get("caption") else [])
    if b["kind"] == "figure":
        return [(b.get("caption") or "", "caption")]
    return [(b.get("text") or "", "text")]


def _section_steps(blocks, heads):
    """절 번호 → 그 절 바로 아래 단계 줄('N) …' 문단·항목 — 검토 D2-①-04)의 가장 큰 N. 하위 절의 단계는 세지 않고, 단계
    번호가 다시 1 부터 시작해도 가장 큰 N 이다(D2-③-05)."""
    steps, cur, numbers = {}, None, iter(n for n, _, _ in heads)
    for b in blocks:
        if b["kind"] == "heading":
            cur = next(numbers)
        elif b["kind"] in ("para", "item") and cur:
            m = STEP_RX.match(b["text"])
            if m:
                steps[cur] = max(steps.get(cur, 0), int(m.group(1)))
    return steps


def _step_items(text, pos):
    """text[pos:] 에 붙은 단계 글(조사 '의' 허용) → (단계 [(처음, 끝)], 끝 자리, 단계 하나뿐인가, 조사 '의' 로 이었나) 또는 None.
    'a)'·'a)~b)' 뒤에 쉼표·가운뎃점·'및'·'와'·'과' 로 잇는 나열도 읽는다 — 나열은 원소마다 대조한다(검토 D4-①-01 — '2)·7)·8)'·'3), 1)')."""
    m = STEPS_RX.match(text, pos)
    if not m:
        return None
    items, end, single = [(int(m.group(1)), int(m.group(2) or m.group(1)))], m.end(), m.group(2) is None
    joined = "의" in text[pos:m.start(1)]                      # '{{절:가}}의 9)' — 그 절의 단계라는 뜻이 글에 있다(D6-①-02)
    n = STEPS_MORE_RX.match(text, end)
    while n:
        items.append((int(n.group(1)), int(n.group(2) or n.group(1))))
        end, single = n.end(), False
        n = STEPS_MORE_RX.match(text, end)
    return items, end, single, joined


def _step_range(out, at, text, pos, steps, num, title, cite, by):
    """text[pos:] 에 붙은 단계·범위·나열(_step_items)을 그 절 단계 수와 대조한다(_range_check) → 단계 글의 끝 자리 또는 None
    (단계가 붙지 않음). 단계 하나 뒤가 또 절·글자 인용이면('1) {{절:가}} 2) {{절:나}}') 나열 번호다(D2F-04·D5-①-06 — 그림·표 인용이
    뒤에 오면 단계로 본다, D4-③-02). 조사 '의' 로 이은 단계('{{절:가}}의 9) {{글자:…}}')는 그 절의 단계다(D6-①-02). 그 밖의 문단 안
    나열('1) {{절:가}} 2) 화면 확인')은 단계로 읽는다 — 나열이면 인용 뒤에 쉼표를 둔다(나열 표시를 글로 가리던 판은 참 어긋남까지
    낮춰 걷어냈다 — D5-①-03·04)."""
    got = _step_items(text, pos)
    if not got:
        return None
    items, end, single, joined = got
    if single and not joined and text[end:].lstrip().startswith(("{{절:", "{{글자:")):
        return None
    c = cite + text[pos:end]                                   # 인용 글은 한 번만 만든다(원소마다 사본 — D7-①-03)
    for lo, hi in items:
        _range_check(out, at, lo, hi, steps, num, title, c, by)
    return end


def _range_check(out, at, lo, hi, steps, num, title, cite, by):
    """단계 범위 lo~hi 를 절 num 의 단계 수와 대조 — ranges 에 기록(by: ref {{절:}} 뒤 · literal 글자 절 번호 뒤 · local 인용에 붙지
    않아 그 글이 든 절)하고 어긋나면 section 에(1 ≤ lo ≤ hi ≤ 단계 수)."""
    n = steps.get(num, 0)
    out["ranges"].append({"at": at, "section": num, "title": title, "lo": lo, "hi": hi, "steps": n, "by": by})
    why = ("그 절에는 단계 줄이 없다" if not n else "단계는 1)부터" if lo < 1 else "단계 범위가 뒤집혔다" if hi < lo
           else "그 절의 단계는 %d)까지" % n if hi > n else None)
    if why and by == "local":
        why = "이 절(%s %s)의 단계 범위 — %s. 다른 절의 단계면 {{절:제목}} 바로 뒤에 쓴다" % (num, title, why)
    if why:
        out["section"].append({"at": at, "cite": cite, "why": why})


def text_checks(blocks):
    """명세 본문 글자 검사(P-051 — 작성기에서는 경고만. 저장소 명세는 단위 시험이 고칠 것 0곳을 요구한다).
    section: {{절:제목}} 바로 뒤 단계 'a)'·범위 'a)~b)'·나열 'a)·b)'(조사 '의', 이음 ~·～·〜·∼·-·–·—·부터 — '에서' 는 되돌아가기일 수
             있어 아니다 D5-①-01, 나열 쉼표·가운뎃점·및·와·과 — D3-①-01·D4-①-01)가 그 절 단계 줄('N) …', 번호 뒤 빈칸 — D5-①-02) 수
             안인가(원소마다 1 ≤ a ≤ b ≤ 단계 수), 인용에 붙지 않은 범위 'a)~b)' 가 그 글이 든 절의 단계 수 안인가(검토
             D3-③-06 — SUM 5.2.2 '2)~5)는'. 단계 줄이 있는 절의 문단·항목만 보고, 앞에
             인용·글자 절 번호가 있는 글의 범위는 어느 절의 것인지 몰라 의심 — D3F-02·D4-①-04), 그리고 글자로 쓴 절 번호 —
             '번호 + 있는 제목'(맞아도 앞에 절이 늘면 조용히 낡는다 — {{절:제목}} 으로), 번호가 그 제목의 번호가 아님(낡음),
             붙여 쓴 '4.3.4.1절'·'3.1항'·'제3장' 중 이 문서에 있는 번호이고 뒤가 조사·글자 끝인 것(D3-①-03·D4-①-05).
             문단 머리 목록 번호 '1. …' 는 보지 않는다(D3-①-05·D2F-N04). 인용 바로 뒤 '2)' 다음이 또 절·글자 인용이면 나열 번호다
             (D2F-04·D5-①-06 — 조사 '의' 로 이었으면 단계, D6-①-02). {{글자:…}} 안과 그 바로 뒤 단계는 보지 않는다(다른 문서의 절
             번호 — D2F-01·D4-①-04). 단계 줄에서 띄어 쓴 나열·조사 머리('4) 및 5)는'·'3) 의 결과')는 뺀다(D6-①-01).
    literal: 인용({{표:캡션}}·{{그림:캡션}}·{{절:제목}}) 밖에 글자로 쓴 '표 N'·'표N'·'그림 N'(D1-③-07) — 숫자에 붙은 세는 말
             (개·장·건·종·가지·행·열·쪽·줄·칸·점)은 빼고(D2-①-05·D3-①-05 — 띄운 '표 3 개요'·조사 '그림 2가' 는 번호, D3-③-01·D4-①-03).
    levels: 제목 수준 건너뜀('#' 다음 '###' — 번호에 0 이 든다, D2-①-06).
    suspect: 점 든 번호가 있는 절 번호인데 뒤 글(한글)이 그 절 제목이 아님 — 제목을 바꾼 뒤 낡은 글자 인용일 수도, '버전 2.1
             이상'·'1.5 초' 같은 보통 글일 수도 있어 고칠 것에 넣지 않는다(경고만, D3-①-02·D2F-01). 이 문서에 없는 '3.1.1항'
             (다른 문서의 절일 수 있다)·낱말일 수 있는 '1.1절차'·'제3장비'(D4-①-05)·인용 뒤에 떨어진 범위('{{절:가}}에서 2)~8)',
             D4-①-04)·캡션 안의 section·literal(캡션에는 인용을 쓸 수 없다 — D2F-N04)도 여기에. 고칠 것이 아니면 {{글자:…}} 로
             감싸 두면 경고가 없어진다(D4-②-02).
    ranges: 단계 범위 모두(by ref·literal·local — 기록. 절에 단계가 늘어 범위 끝이 낡는지는 시험이 고정해 본다, D1F-01).
    표 캡션·그림 캡션도 본다(D2-①-03). → {"section": [{"at": 블록 차례, "cite", "why"}], "literal": [{"at", "text"}],
    "levels": [{"at", "text", "why"}], "suspect": [{"at", "cite", "why"}],
    "ranges": [{"at", "section", "title", "lo", "hi", "steps", "by"}]}"""
    heads = heading_numbers(blocks)
    title_of = {n: t for n, t, _ in heads}
    num_of = {}
    for n, t, _ in heads:
        num_of.setdefault(t, []).append(n)
    steps = _section_steps(blocks, heads)
    titles = sorted(num_of, key=len, reverse=True)
    out = {"section": [], "literal": [], "levels": [], "suspect": [], "ranges": []}

    def scan(t, at, cur, sink, local):
        masked = REF_RX.sub(lambda r: "\x00" * len(r.group(0)), t)              # 인용 안 글자는 보지 않는다(같은 길이)
        used, cites = [], []                                            # 인용에 붙은 단계 글 [(처음, 끝)] · 인용이 시작하는 자리
        for r in REF_RX.finditer(t):
            if r.group(1) == "글자":                                    # 다른 문서 인용 — 바로 뒤 단계도 그 문서의 것(검사 밖, D4-①-04)
                cites.append(r.start())
                got = _step_items(t, r.end())
                if got:
                    used.append((r.end(), got[1]))
                continue
            if r.group(1) != "절":
                continue
            cites.append(r.start())
            got = num_of.get(r.group(2).strip())
            if got and len(got) == 1:                                   # 없는·같은 제목은 _refs(plan)가 명세 오류로 막는다
                e = _step_range(sink, at, t, r.end(), steps, got[0], r.group(2).strip(), r.group(0), "ref")
                if e:
                    used.append((r.end(), e))
        for m in SECNUM_RX.finditer(masked):
            num, rest = m.group(1), masked[m.end():]
            if m.start() == 0 and "." not in num and masked[m.end(1):m.end(1) + 1] == ".":
                continue                                                # 문단 머리 목록 번호 '1. …' 는 인용이 아니다(D3-①-05·D2F-N04)
            cited = next((x for x in titles if rest.startswith(x)), None)
            if num in title_of and rest.startswith(title_of[num]):
                title, why = title_of[num], "글자 절 번호 — {{절:%s}} 로 쓴다(다른 문서의 절이면 {{글자:…}})" % title_of[num]
            elif cited:
                title, why = cited, "%s — '%s' 는 %s" % ("그 번호의 절은 %r" % title_of[num] if num in title_of
                                                         else "없는 절 번호", cited, "·".join(num_of[cited]))
            elif "." in num and num in title_of and HANGUL_RX.match(rest):
                # 제목을 바꾼 뒤 낡은 글자 인용일 수도, '버전 2.1 이상'·'1.5 초'·다른 문서 '3.1.1 항' 같은 보통 글일 수도 있다 —
                # 고칠 것이 아니라 의심(경고만, D3-①-02·D2F-01)
                sink["suspect"].append({"at": at, "cite": t[m.start():m.end() + 12].strip(),
                                        "why": "그 번호의 절은 %r — 절 인용이면 {{절:제목}} 으로" % title_of[num]})
                cites.append(m.start())
                continue
            else:
                continue
            cites.append(m.start())
            end = m.end() + len(title)
            sink["section"].append({"at": at, "cite": t[m.start():end], "why": why})
            if title_of.get(num) == title:
                e = _step_range(sink, at, t, end, steps, num, title, t[m.start():end], "literal")
                if e:
                    used.append((end, e))
        for m in SECSUFFIX_RX.finditer(masked):                         # 붙여 쓴 '4.3.4.1절'·'제3장'(D3-①-03)
            num, rest = m.group(1) or m.group(2), masked[m.end():]
            word = bool(HANGUL_RX.match(rest)) and not rest.startswith(SECSUFFIX_TAIL)   # '1.1절차'·'제3장비'(D4-①-05)
            cites.append(m.start())
            if num in title_of and not word:
                sink["section"].append({"at": at, "cite": m.group(0),
                                        "why": "글자 절 번호 — {{절:%s}} 로 쓴다(다른 문서의 절이면 {{글자:…}})" % title_of[num]})
            elif num in title_of:
                sink["suspect"].append({"at": at, "cite": m.group(0) + rest[:2],
                                        "why": "뒤 글자와 한 낱말일 수 있다 — 절 인용이면 {{절:%s}} 로" % title_of[num]})
            else:                                                       # 이 문서에 없는 번호 — 다른 문서의 절일 수 있다
                sink["suspect"].append({"at": at, "cite": m.group(0),                    # 감싸면 경고가 없어진다(D5-②-07)
                                        "why": "이 문서에 없는 절 번호 — 다른 문서의 절이면 {{글자:…}} 로 감싼다"})
        for m in RANGE_RX.finditer(masked):                             # 인용에 붙지 않은 범위 — 그 글이 든 절(D3-③-06)
            if any(a <= m.start() < z for a, z in used):
                continue
            if any(c < m.start() for c in cites):                       # 앞에 인용·글자 절 번호 — 어느 절의 단계인지 모른다(D4-①-04)
                sink["suspect"].append({"at": at, "cite": m.group(0), "why": "인용 뒤에 떨어진 단계 범위 — 그 절의 단계면 "
                                        "{{절:제목}} 바로 뒤에(조사 '의'), 다른 문서의 단계면 {{글자:…}} 바로 뒤에 쓴다"})
            elif local and cur[0] and steps.get(cur[0]):                # 단계 줄이 있는 절의 문단·항목만 — 표 칸·메모·캡션·
                _range_check(sink, at, int(m.group(1)), int(m.group(2)), steps, cur[0], cur[1], m.group(0), "local")   # 단계 없는 절은 아니다(D3F-02)
        for m in LITERAL_RX.finditer(masked):
            sink["literal"].append({"at": at, "text": m.group(0)})

    prev, cur, numbered = 0, (None, None), iter(heads)
    for i, b in enumerate(blocks):
        if b["kind"] == "heading":
            if b["level"] > prev + 1:
                out["levels"].append({"at": i, "text": b["text"], "why": "수준 %d 다음에 %d" % (prev, b["level"])})
            prev, cur = b["level"], next(numbered)[:2]
            continue
        for t, part in _block_parts(b):
            if part != "caption":
                scan(t, i, cur, out, part == "text" and b["kind"] in ("para", "item"))
                continue
            cap = {"section": [], "literal": [], "suspect": [], "ranges": []}     # 캡션은 인용을 쓸 수 없는 자리 —
            scan(t, i, cur, cap, False)                                          # 고칠 것이 아니라 의심(검토 D2F-N04)
            out["ranges"] += cap["ranges"]
            out["suspect"] += cap["suspect"] + [
                {"at": i, "cite": x.get("cite") or x.get("text"), "why": "캡션 안 — %s" % x.get("why", "글자 표·그림 번호")}
                for x in cap["section"] + cap["literal"]]
    return out


def text_check_problems(tc):
    """text_checks 결과에서 고칠 것(section·literal·levels) — 비면 깨끗하다(ranges 는 기록만)."""
    return [dict(x, kind=k) for k in TEXT_CHECK_KINDS for x in (tc or {}).get(k, [])]


def text_check_warnings(tc):
    """text_checks 결과 → 보고 경고 줄(종류마다 한 줄, 앞 3곳의 인용 글과 까닭을 싣는다 — 검토 D2-③-03)."""
    fmt = {"section": "절 인용 %d곳이 명세 제목 차례와 맞지 않거나 글자 번호다 %s — {{절:제목}} 인용·단계 범위로 고친다(P-051)",
           "literal": "글자로 쓴 표·그림 번호 %d곳 %s — {{표:캡션}}·{{그림:캡션}} 인용으로 쓴다(P-051)",
           "levels": "제목 수준을 건너뛴 곳 %d %s — 그 절은 {{절:}} 로 인용할 수 없고 한/글 번호가 다를 수 있다(U-32)"}
    fmt["suspect"] = ("의심 %d곳 %s — 고칠 것이 아닐 수 있다: 절 인용이면 {{절:제목}} 으로 고치고, 인용이 아니면 {{글자:…}} 로 "
                      "감싸 둔다(이 경고가 없어진다 — 가짜 쓰기·실측 기대는 경고 0). 캡션 안이면 캡션 글을 바꾼다(D3-①-02·D4-②-02)")
    show = lambda x: "%s (%s)" % (x.get("cite") or x.get("text"), x["why"]) if "why" in x else x["text"]
    return [fmt[k] % (len(tc[k]), [show(x) for x in tc[k][:3]]) for k in TEXT_CHECK_KINDS + ("suspect",) if tc.get(k)]


# ------------------------------------------------------------------ 쓰기

def style_index(m):
    return {x["name"]: int(x["id"]) for x in m["styledefs"]}


def top_paras(m):
    return [b for b in m["body"] if b["type"] == "para" and TOP.match(b["id"])]


def root_of(m, bid):
    a, b = TOP.match(bid).groups()
    return sum(m["stats"]["section_paras"][:int(a)]) + int(b)


def _visible(t):
    """파서가 보는 글자 꼴 — 공백뿐인 문단(칸 안 줄)은 블록이 되지 않는다(hwpml_parse). 앞부분 대조는 이 꼴로 한다
    (P-037: 양식 예시 글자를 지운 칸에 공백만 남으면 그 문단이 모델에서 빠진다)."""
    return "\n".join(x for x in (t or "").split("\n") if x.strip())


def _norm(t):
    return re.sub(r"\s+", "", t or "")


def apply_style(s, idx, name):
    if name not in idx:
        raise SpecError("템플릿에 스타일이 없다: %s" % name)
    return s.s.action("Style", "Style", Apply=idx[name])


def insert_text(s, text):
    return s.s.action("InsertText", "InsertText", Text=text)


def get_pos(s):
    """(목록, 문단, 위치) — 목록 0 = 본문. 못 읽으면 None."""
    try:
        p = s.s.call("GetPos", lambda: s.hwp.GetPos())
        return tuple(p) if p is not None else None
    except hs.TimeoutKilled:
        raise
    except Exception:
        return None


def apply_style_clean(s, idx, name, new, clean=True):
    """스타일을 입힌다. 이미 있던 문단(new=False: 템플릿 본문 빈 문단·표 뒤 빈 문단)은 같은 스타일을 한 번 더(F-109).
    실측 14.sum_step4.bat(10-12 17:22) 결과에서 추론: 한/글은 다른 스타일을 입히면 문단의 직접 글자 모양을 남기고(템플릿 빈
    문단의 12pt 가 다음 문단들로 이어짐), 같은 스타일을 다시 입힐 때 '본문을 [스타일] 스타일 모양으로 덮어 쓸까요?'로 묻는다
    — 메시지 상자 자동 '예'(D-039)로 스타일 모양만 남긴다. 확인은 쓴 뒤 글자 크기 대조(size_mismatch).
    clean=False(자동 응답을 켜지 못함)면 다시 입히지 않는다 — 묻는 창이 떠 사람의 답을 기다리게 된다(검토 P-040 4)."""
    apply_style(s, idx, name)
    if not new and clean:
        apply_style(s, idx, name)


def append_para(s, idx, style, text, new=True, clean=True):
    s.s.run("MoveDocEnd")
    if new:                                                    # new=False: 문서 끝 빈 문단에 쓴다
        s.s.run("BreakPara")
    apply_style_clean(s, idx, style, new, clean)
    if text:
        insert_text(s, text)


def _end_after_object(s, anchor):
    """표·그림을 넣은 뒤 문서 끝으로 → (빈 문단이 새로 생겼나, 위치). 실측 P-027: 표를 만들면 한/글이 그 뒤에 빈 문단을
    하나 더 둔다 — 캐럿이 '개체 문단 + 1' 의 처음이면 그 빈 문단이다(다음 항목을 거기에 쓴다)."""
    s.s.run("MoveDocEnd")
    pos = get_pos(s)
    if pos is not None and pos[0] != 0:
        raise api.EditFailed("표·그림을 넣은 뒤 본문으로 나오지 못했다(GetPos %s)" % (pos,))
    extra = bool(anchor and pos and pos[1] == anchor[1] + 1 and pos[2] == 0)
    return extra, pos


def append_picture(s, idx, style, path, size, new=True, clean=True, caption=None):
    """문서 끝 새 문단에 그림 파일을 넣는다(문서에 포함, 크기 mm — 없으면 원래 크기). caption(plan 의 cap)이 있으면 한/글
    '캡션 넣기'로 캡션(P-049, attach_caption — 그림 캡션 자리는 한/글 기본 '아래' 그대로, 쓴 뒤 대조). cap["newnum"] 이
    있으면 캡션 뒤 그림 문단 처음에 '새 번호로 시작'(new_number, P-050). → (빈 문단 생김, 기록)."""
    s.s.run("MoveDocEnd")
    if new:
        s.s.run("BreakPara")
    apply_style_clean(s, idx, style, new, clean)
    anchor = get_pos(s)
    w, h = size or (0, 0)
    ctrl = s.s.call("InsertPicture", lambda: s.hwp.InsertPicture(str(ROOT / path), True, 1 if size else 0, False, False,
                                                                 0, w, h))
    if ctrl is None:
        raise api.EditFailed("그림 넣기 실패: %s" % path)
    got = attach_caption(s, idx, anchor, caption, clean) if caption else None
    newnum = new_number(s, anchor, CAPTION_NUM["picture"], caption["newnum"]) if caption and caption.get("newnum") else None
    extra, pos = _end_after_object(s, anchor)
    info = {"type": "picture", "path": path, "anchor": anchor, "end": pos, "extra": extra}
    if got:
        info["caption"] = {"pos": got["pos"], "moved": got["moved"]}
    if newnum:
        info["newnum"] = newnum
    return extra, info


def attach_caption(s, idx, anchor, cap, clean=True, in_caption=None):
    """표·그림에 한/글 '캡션 넣기'(ShapeObjAttachCaption)로 캡션을 단다(사용자 지시 P-049). 개체가 든 문단 처음(개체 바로
    앞 — MovePos moveMain, 표 가운데 정렬과 같은 길)에서 부르면 캐럿 오른쪽 개체에 붙는다(pyhwpx 설명: 캐럿 좌우에 개체가 있으면
    오른쪽 먼저). 새 캡션은 '그림 '·'표 ' + 자동 번호 + 빈칸이고 캐럿이 캡션 안으로 간다(hwpxlib 시험 파일 SimpleRectangle 의
    한/글 캡션 꼴) — 캡션 끝(MoveListEnd)에 제목을 넣고, 캡션 문단에 캡션 스타일을 입힌다(한/글이 만든 문단이라 같은 스타일
    두 번 — F-109). in_caption(): 캐럿이 캡션 안일 때 더 할 일(표: 캡션 자리 — caption_side). CloseEx 로 캡션에서 나온다.
    개체 문단으로 못 옮기면(앵커 없음·MovePos 실패) 캐럿 자리에서 부른다 — 표 밖으로 나온 곳·그림을 넣은 곳이라 개체 바로 뒤다.
    캡션 넣기 뒤 캐럿이 본문(목록 0)이면 캡션을 달지 못한 것 — 멈춘다. GetPos 를 못 읽으면 쓴 뒤 대조에 맡긴다.
    실측 17·18.sum_step7·8(U-30 해소). 쓴 뒤에도 캡션 글자(자동 번호 포함)·스타일·자리를 HWPML 로 대조한다(caption_check).
    → {"pos": 캡션 안 GetPos, "moved": 개체 문단 처음으로 옮겼나, "in_caption": in_caption 결과}."""
    moved = False
    if anchor:
        try:
            moved = bool(s.s.call("MovePos", s.hwp.MovePos, 0, anchor[1], 0))
        except hs.TimeoutKilled:
            raise
        except Exception:                                      # pywin32 com_error 등 — 캐럿 자리(개체 바로 뒤)에서
            moved = False
    s.s.run("ShapeObjAttachCaption")
    pos = get_pos(s)
    if pos is not None and pos[0] == 0:
        raise api.EditFailed("캡션 넣기 뒤 캐럿이 본문에 있다(GetPos %s) — 캡션을 달지 못했다: 캡션을 달 개체가 없거나"
                             "(그림·표 넣기가 듣지 않음) 캡션 넣기가 듣지 않았다(U-30)" % (pos,))
    s.s.run("MoveListEnd")
    apply_style_clean(s, idx, cap["style"], False, clean)
    if cap["title"]:
        insert_text(s, cap["title"])
    got = in_caption() if in_caption else None
    s.s.run("CloseEx")                                         # 캡션 → 본문(개체가 든 문단)
    return {"pos": pos, "moved": moved, "in_caption": got}


def caption_side(s, side):
    """캐럿이 캡션 안일 때 그 개체 캡션의 자리 — TablePropertyDialog 의 ShapeCaption.Side = SideType(side) (한컴 포럼
    '표 캡션' 답·pyhwpx move_all_caption 과 같은 꼴, 실측 U-30 해소 — 그림 캡션에는 부르지 않는다: PoC C6). side: 'Top' · 'Bottom'. → 실행 결과."""
    def fn():
        h = s.hwp
        ps = h.HParameterSet.HShapeObject
        h.HAction.GetDefault("TablePropertyDialog", ps.HSet)
        ps.ShapeCaption.Side = h.SideType(side)
        return bool(h.HAction.Execute("TablePropertyDialog", ps.HSet))
    return s.s.call("TablePropertyDialog:caption", fn)


def new_number(s, anchor, kind, n):
    """개체가 든 문단 처음(개체 바로 앞)에 한/글 '새 번호로 시작'(NewNumber — HAutoNum NumType = AutoNumType(kind),
    NewNumber = n; pyhwpx 1.7.2 new_number 와 같은 꼴, 실측 U-31 해소) — 그 개체 번호가 n 부터(P-050). kind: 'Figure'·'Table'.
    캡션을 단 뒤에 부른다 — 캡션 넣기는 캐럿 오른쪽 조판을 고르므로(pyhwpx 설명) 새 번호 조판이 개체 앞에 먼저 있으면 그것에
    붙을 수 있다. 못 넣으면(자리를 모름·MovePos 실패·동작 실패·오류) 실패로 남기고 쓰기를 잇는다 — 번호는 쓴 뒤 캡션 대조가
    보고, 어긋나면 저장하지 않는다(분석 문서 261016_1615 4.1 의 '바로 멈춘다'와 다른 까닭: 번호가 원래 맞는 문서까지 막지 않고,
    저장 판단은 한 곳(쓴 뒤 대조)에서 한다 — 검토 P-050 D1-①-N04).
    pyhwpx new_number 설명의 주의 셋(U-31 — 18.sum_step8 실측에서 본문 첫 쪽 번호 [1, 1] 그대로): 1. 쪽 번호가 정의되지 않은 문서에서는 듣지 않는다 — 공통 템플릿은 꼬리말
    쪽 번호와 본문 처음 쪽 새 번호가 있다. 2. 새 번호를 지정한 쪽과 그 뒤 모든 쪽이 영향을 받는다. 3. 넣을 때 캐럿 뒤(같은 쪽)에
    새 번호 조판이 있으면 넣은 조판은 무효 — 쪽 맨 뒤 새 번호만 듣는다. 3 이 종류를 가리지 않으면 본문 첫 쪽의 이 조판이 템플릿
    쪽 새 번호(본문 쪽 1)를 무효로 할 수 있어 write 가 본문 첫 쪽 인쇄 번호를 쓰기 앞뒤로 견준다(print_page, 검토 D1-②-01).
    → {"kind", "n", "ok", "error"}."""
    rec = {"kind": kind, "n": n, "ok": False, "error": None}
    if not anchor:
        rec["error"] = "개체 문단 자리를 모른다(GetPos 실패)"
        return rec
    try:
        moved = bool(s.s.call("MovePos", s.hwp.MovePos, 0, anchor[1], 0))
    except hs.TimeoutKilled:
        raise
    except Exception as e:                                     # pywin32 com_error 등
        moved, rec["error"] = False, "MovePos 오류 %s" % type(e).__name__
    if not moved:
        rec["error"] = rec["error"] or "개체 문단 처음으로 옮기지 못했다(MovePos 문단 %s)" % anchor[1]
        return rec

    def fn():
        h = s.hwp
        ps = h.HParameterSet.HAutoNum
        h.HAction.GetDefault("NewNumber", ps.HSet)
        ps.NumType = h.AutoNumType(kind)
        ps.NewNumber = n
        return bool(h.HAction.Execute("NewNumber", ps.HSet))
    try:
        rec["ok"] = bool(s.s.call("NewNumber", fn))
    except hs.TimeoutKilled:
        raise
    except Exception as e:                                     # AutoNumType·매개변수 이름이 다르면 여기(U-31)
        rec["error"] = "NewNumber 오류 %s: %s" % (type(e).__name__, e)
        return rec
    if not rec["ok"]:
        rec["error"] = "NewNumber 실패(False)"
    return rec


def print_page(s, para, reads=None):
    """본문 최상위 문단 para 처음의 인쇄 쪽 번호(새 번호 반영 — 꼬리말에 찍히는 번호). MovePos(moveMain) 뒤 두 길로 읽어
    견준다(U-31 — 18.sum_step8 PoC R1·N5 실측: 두 길 모두 새 번호를 반영한 인쇄 번호를 읽고 쓴 뒤 바로 바뀐다): 한/글 KeyIndicator 의 prnpageno — pyhwpx key_indicator 꼴 (succ, seccnt,
    secno, prnpageno, colno, line, pos, over, ctrlname) — 와 XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo
    .CurrentPrintPage(pyhwpx current_printpage: 새 번호를 반영한 종이의 쪽 번호). 둘이 다르면(한쪽이 쪽 차례를 읽는 꼴)
    None — 못 읽은 것으로 본다(검토 D2-②-01·D1F-N01). 하나만 읽히면 그 값. reads(목록)가 있으면 [KeyIndicator, CurrentPrintPage]
    를 덧붙인다. 못 읽으면 None (P-050, 검토 D1-②-01)."""
    try:
        moved = bool(s.s.call("MovePos", s.hwp.MovePos, 0, para, 0))
    except hs.TimeoutKilled:
        raise
    except Exception:                                          # pywin32 com_error
        moved = False
    got = [None, None]
    if moved:
        def key():
            k = s.hwp.KeyIndicator()
            return k[3] if isinstance(k, (tuple, list)) and len(k) > 3 and k[0] else None

        def cur():
            return s.hwp.XHwpDocuments.Active_XHwpDocument.XHwpDocumentInfo.CurrentPrintPage
        for i, (name, fn) in enumerate((("KeyIndicator", key), ("CurrentPrintPage", cur))):
            try:
                v = s.s.call(name, fn)
                got[i] = int(v) if isinstance(v, int) and not isinstance(v, bool) else None
            except hs.TimeoutKilled:
                raise
            except Exception:                                  # pywin32 com_error·없는 속성·꼴이 다른 결과
                got[i] = None
    if reads is not None:
        reads.append(got)
    vals = {v for v in got if v is not None}
    return vals.pop() if len(vals) == 1 else None


def uses_section_refs(blocks):
    """명세 본문에 {{절:제목}} 인용이 있는가 — 있으면 쓴 문서 글자에 명세 차례로 센 절 번호가 들어간다."""
    return any(r.group(1) == "절" for b in blocks if b["kind"] != "heading" for t in _block_texts(b) for r in REF_RX.finditer(t))


def heading_string(s, para):
    """최상위 문단 para 의 한/글 개요 번호 글자(GetHeadingString — 실측 P-029 [T1] U-17: '1.1.' 꼴, 템플릿 생성기
    build_templates.heading_string 과 같은 호출). MovePos(moveMain) 로 옮긴 뒤 읽는다. 못 읽으면 None."""
    try:
        if not s.s.call("MovePos", s.hwp.MovePos, 0, para, 0):
            return None

        def get():
            v = s.hwp.GetHeadingString                         # pywin32 늦은 바인딩: 메서드이거나(보통) 속성 값
            return v() if callable(v) else v
        v = s.s.call("GetHeadingString", get)
    except hs.TimeoutKilled:
        raise
    except Exception:                                          # pywin32 com_error·없는 메서드
        return None
    return None if v is None else str(v)


def written_headings(m, broot):
    """쓴 문서의 제목 문단(본문 첫 장 제목부터, 문단 모양 개요) → [(루트 번호, 글자)] — 문서 차례."""
    return [(root_of(m, b["id"]), b["text"]) for b in top_paras(m)
            if b.get("level_src") == "outline" and root_of(m, b["id"]) >= broot]


def heading_check(s, m, broot, blocks):
    """제목마다 한/글 개요 번호(heading_string)의 숫자가 명세 제목 차례로 센 번호(heading_numbers — {{절:}} 인용에 쓴 번호)와
    같은가(P-051, 검토 D2-②-02 → U-32). 쓴 제목 수가 명세와 다르면 그것도 어긋남. 다 읽은 뒤 캐럿을 본문 첫 장 제목으로
    되돌린다(저장 파일에 캐럿 자리가 남는다 — 검토 D3-②-02). → {"headings": [명세, 쓴 문서], "checked", "unread",
    "mismatch_count", "mismatch": 앞 10곳 [{"title", "want", "got"}](구조 어긋남 먼저), "structural": 제목 수 어긋남·번호 없는
    제목(GetHeadingString 이 번호 꼴 글자 없이 '' · '•' 를 줌)의 수(셈 가정이 아니라 쓴 문서가 틀린 것 — {{절:}} 인용이 없어도 저장
    거절, D4-②-01·D5F-01. 숫자가 아닌 번호 꼴 '가.'·'①'·'Ⅰ.' 은 번호가 있으니 여기 들지 않는다 — D5-②-01), "samples": 수준마다
    처음 읽은 제목 [번호, 읽은 글자](실측 한 번으로 수준별 번호 꼴이 남는다 — D3-②-04)}"""
    want, got = heading_numbers(blocks), written_headings(m, broot)
    bad = [{"title": "(제목 수)", "want": len(want), "got": len(got)}] if len(want) != len(got) else []
    out = {"headings": [len(want), len(got)], "checked": 0, "unread": 0, "samples": []}
    levels = set()
    for (n, title, _), (root, _) in zip(want, got):
        g = heading_string(s, root)
        if g is None:
            out["unread"] += 1
            continue
        out["checked"] += 1
        if n.count(".") not in levels:
            levels.add(n.count("."))
            out["samples"].append([n, g])
        if [int(x) for x in re.findall(r"\d+", g)] != [int(x) for x in n.split(".")]:
            bad.append({"title": title, "want": n, "got": g})
    if got:                                                    # 캐럿을 print_page 가 두었던 본문 첫 장 제목으로
        try:
            s.s.call("MovePos", s.hwp.MovePos, 0, broot, 0)
        except hs.TimeoutKilled:
            raise
        except Exception:                                      # 못 옮겨도 문서는 그대로 — 열 때 첫 화면 자리만 다르다
            pass
    out["samples"].sort(key=lambda x: x[0].count("."))
    count = 1 if len(want) != len(got) else 0                  # 제목 수 항목은 표지 글자가 아니라 자리(첫 항목)로 가른다(D6-②-04)
    struct = bad[:count] + [x for x in bad[count:] if not re.search(r"\w", str(x["got"]))]   # 번호 꼴 글자가 없다('' ·
    out.update(mismatch_count=len(bad), mismatch=(struct + [x for x in bad if x not in struct])[:10],   # '•' — 쓴 문서가 틀렸다,
               structural=len(struct))                         # D4-②-01·D5F-01). 구조 항목 먼저(D5-②-06)
    return out


def cell_border_fill(s, cf):
    """지금 칸(캐럿이 칸 안, 셀 블록 없이 — 실측 PoC A1)에 테두리 네 변·배경. cf = 칸 서식(table_style). → 실행 결과."""
    def fn():
        h = s.hwp
        ps = h.HParameterSet.HCellBorderFill
        h.HAction.GetDefault("CellBorderFill", ps.HSet)
        for k, name in (("L", "Left"), ("R", "Right"), ("T", "Top"), ("B", "Bottom")):
            v = cf.get(k)
            if v:
                setattr(ps, "BorderType" + name, h.HwpLineType(v[0]))
                setattr(ps, "BorderWidth" + name, h.HwpLineWidth(v[1]))
        if cf.get("fill"):
            fa = ps.FillAttr
            fa.type = h.BrushType("NullBrush|WinBrush")
            fa.WinBrushFaceColor = h.RGBColor(*cf["fill"])
            fa.WinBrushHatchColor = h.RGBColor(153, 153, 153)
            fa.WinBrushFaceStyle = h.HatchStyle("None")
            fa.WindowsBrush = 1
        return bool(h.HAction.Execute("CellBorderFill", ps.HSet))
    return s.s.call("CellBorderFill", fn)


def center_anchor(s, anchor):
    """표가 든 문단으로 가서(MovePos moveMain — 루트 문단 번호, 실측 U-15) 가운데 정렬(ParagraphShapeAlignCenter — 템플릿
    생성기가 쓰는 ParagraphShapeAlignRight 와 같은 계열) — 글자처럼 취급한 표는 그 문단 정렬을 따른다(사용자 지시 P-041,
    D-044). 표를 다 채운 뒤에 한다: 칸 문단과 한/글이 표 뒤에 둔 빈 문단은 그 전에 만들어져 이 정렬을 이어받지 않는다
    (검토 P-041 M3). Run 은 결과를 돌려주지 않는다 — 쓴 뒤 표가 든 문단 정렬을 대조한다(check_tables '가운데 정렬')."""
    if not anchor:
        return False
    if not s.s.call("MovePos", s.hwp.MovePos, 0, anchor[1], 0):
        return False
    s.s.run("ParagraphShapeAlignCenter")
    return True


def shift_any(fmt, styles):
    """표 문단 스타일(styles["anchor"])에 왼쪽·오른쪽 여백이나 첫 줄 들여쓰기가 있나 — 있으면 가운데가 치우친다."""
    am = (fmt.get("metrics") or {}).get(styles["anchor"]) or {}
    return any(am.get(k) for k in ("m_left", "m_right", "m_indent"))


def anchor_margins_zero(s):
    """캐럿 문단(표가 든 문단)의 왼쪽·오른쪽 여백·첫 줄 들여쓰기를 0 으로 — 표 문단 스타일에 여백이 있으면 가운데가 그만큼
    치우친다(검토 P-041 M4). ParagraphShape 동작(개요 수준 고치기에서 실측)의 여백 항목 이름은 실측 전(U-26) — 쓴 뒤 대조."""
    return s.s.action("ParagraphShape", "ParaShape", LeftMargin=0, RightMargin=0, Indentation=0)


def cell_style(cf, styles, header, r):
    """칸 스타일 — 서식 계획의 칸 스타일, 없으면 제목 줄 th / 나머지 td."""
    return cf["style"] if cf and cf.get("style") else styles["th"] if header and r == 0 else styles["td"]


def fit_plan(rows, header, styles):
    """서식 계획이 없는 표(명세에 표 서식 파일이 없거나 고를 서식이 없음)의 계획 — 칸 너비 맞춤·가운데 정렬만(P-045,
    F-153: P-041 지시 '칸마다 글자 + 빈칸 1~2칸, 가운데'를 모든 표에). 칸 스타일은 예전처럼 제목 줄 th / 나머지 td,
    테두리·배경·제목 셀은 칸에 값이 없어 입히지 않는다(한/글 기본 그대로). 안 여백은 write 가 모든 표에 넣는다 — 위·아래
    칸 글자 크기 반, 왼·오 한/글 기본(P-048, ts.pad_margin)."""
    return {"ref": None, "ref_id": None, "mode": "fit", "by_default": False, "inside_margin": None, "shared_edges": 0,
            "cells": [[{"style": cell_style(None, styles, header, r)} for _ in row] for r, row in enumerate(rows)]}


def cell_header(s):
    """지금 칸을 셀 블록(F5)으로 골라 제목 셀로(TablePropertyDialog ShapeTableCell.Header) — 실측 PoC A3 와 같은 차례:
    그 칸 글자를 쓴 뒤, 블록은 Cancel 로 늘 푼다. → 실행 결과."""
    def fn():
        h = s.hwp
        h.Run("TableCellBlock")
        try:
            ps = h.HParameterSet.HShapeObject
            h.HAction.GetDefault("TablePropertyDialog", ps.HSet)
            ps.ShapeTableCell.Header = 1
            return bool(h.HAction.Execute("TablePropertyDialog", ps.HSet))
        finally:
            h.Run("Cancel")
    return s.s.call("TablePropertyDialog:cell", fn)


def table_props(s, inside_margin=None):
    """캐럿이 칸 안(셀 블록 없이)일 때 표 속성: 안 여백 [왼, 오, 위, 아래](HWPUNIT) — 마지막 칸 뒤에 부른다(실측 PoC A3 가
    블록 없는 표 속성을 마지막 칸 뒤에 썼다, 검토 P-040 6). → (실행 결과, 표 너비 HWPUNIT)."""
    def fn():
        h = s.hwp
        ps = h.HParameterSet.HShapeObject
        h.HAction.GetDefault("TablePropertyDialog", ps.HSet)
        width = ps.Width
        if not inside_margin:
            return True, width
        ps.CellMarginLeft, ps.CellMarginRight, ps.CellMarginTop, ps.CellMarginBottom = [int(v) for v in inside_margin]
        return bool(h.HAction.Execute("TablePropertyDialog", ps.HSet)), width
    return s.s.call("TablePropertyDialog:table", fn)


def table_create(s, nr, nc, widths, total):
    """칸 너비를 정해 표를 만든다 — 임의 너비(WidthType=2), WidthValue = 표 너비, ColWidth = 칸마다 너비 - 칸 안 좌우 여백
    (한/글 매크로 기록·pyhwpx create_table 과 같은 꼴, 실측 전 U-26). 모든 줄의 칸 경계가 처음부터 같아 칸을 채우며 옮겨
    다닐 때 어긋나지 않는다(검토 P-040 1: 칸마다 너비를 바꾸며 채우면 줄마다 경계가 달라져 다음 줄 글자가 엉뚱한 칸에).
    Execute 가 마지막 호출 — 앞에서 실패하면 표는 생기지 않는다. → 실행 결과."""
    def fn():
        h = s.hwp
        ps = h.HParameterSet.HTableCreation
        h.HAction.GetDefault("TableCreate", ps.HSet)
        for k, v in (("Rows", nr), ("Cols", nc), ("WidthType", 2), ("HeightType", 0), ("WidthValue", int(total))):
            try:
                setattr(ps, k, v)
            except Exception:                                  # 속성 대입이 안 되는 항목은 SetItem (F-063, s.s.action 과 같게)
                ps.HSet.SetItem(k, v)
        try:
            ps.TableProperties.TreatAsChar = 1                 # 글자처럼 취급(문단 정렬을 따르게) — 기본값도 1(G1)
        except Exception:
            pass
        ps.CreateItemArray("ColWidth", nc)
        for i, w in enumerate(widths):
            ps.ColWidth.SetItem(i, max(int(w) - CELL_LR, 0))
        return bool(h.HAction.Execute("TableCreate", ps.HSet))
    return s.s.call("Action:TableCreate", fn)


def _format_try(fmt, kind, at, fn):
    """표 서식 한 가지 — 실패(False·오류)하면 기록하고 False. 시간초과는 그대로 올린다(한/글이 죽었다)."""
    what = FORMAT_NAMES[kind]
    try:
        if fn():
            return True
        err = "%s 실패(False)" % what
    except hs.TimeoutKilled:
        raise
    except Exception as e:                                     # pywin32 com_error 등 — 서식만 못 입혔다
        err = "%s: %s: %s" % (what, type(e).__name__, e)
    fmt["failed"].append({"table": fmt.get("label"), "n": fmt.get("n"), "kind": kind, "at": at, "error": err[:200]})
    return False


def append_table(s, idx, styles, rows, header, new=True, plan=None, fmt=None, clean=True, caption=None):
    """문서 끝 새 문단에 표를 만들고 칸을 차례로 채운다(첫 칸에서 오른쪽, 줄 끝에서 아래 → 왼쪽 끝). 표 밖으로 나온다.
    plan(table_style.plan_table)이 있으면 서식을 입힌다(P-040, D-042): 칸 너비는 표를 만들 때(table_create — 칸 글자 폭에
    맞춘 너비 table_style.fit_table, P-041), 칸 스타일은 글자 전, 테두리/배경(블록 없이 — A1)·제목 셀(셀 블록 — A3)은 그 칸
    글자를 쓴 뒤, 표 안 여백은 마지막 칸 뒤, 표가 든 문단 가운데 정렬(P-041)은 표 밖으로 나온 뒤. 종류마다 따로 — 하나가
    실패해도 글자와 다른 종류는 그대로 하고 실패는 fmt["failed"] 에 남긴다. fmt["off"] 에 든 종류는 하지 않는다.
    caption(plan 의 cap)이 있으면 가운데 정렬 뒤 한/글 '캡션 넣기'로 표 캡션(P-049, attach_caption) — 캡션 자리 '위'는 캡션
    안에서 caption_side(서식 종류 caption). cap["newnum"] 이 있으면 캡션 뒤 표 문단 처음에 '새 번호로 시작'(new_number, P-050).
    → (빈 문단 생김, 기록)."""
    s.s.run("MoveDocEnd")
    if new:
        s.s.run("BreakPara")
    apply_style_clean(s, idx, styles["anchor"], new, clean)
    nr, nc = len(rows), len(rows[0])
    on = plan is not None and fmt is not None
    done, col_hu, got, fit, cap = None, None, {}, None, None
    anchor = get_pos(s)
    if on:                       # 종류마다: True 입힘 · False 실패 · "off" 꺼짐 · None 입힐 것 없음
        off = fmt.get("off") or set()
        done = {k: ("off" if k in off else None) for k in FORMAT_KINDS}
        am = (fmt.get("metrics") or {}).get(styles["anchor"]) or {}     # 표 문단 스타일 여백(가운데가 치우침, 검토 P-041 M4)
        shift = am.get("m_left", 0) + am.get("m_right", 0) + am.get("m_indent", 0)   # 표 너비 상한에서 뺀다
        if done["width"] is None and fmt.get("total"):
            im = plan.get("inside_margin")
            lr = (im[0] + im[1]) if im and done["margin"] != "off" else ts.DEFAULT_INSIDE_LR
            cap = fmt["total"] - max(0, shift)

            def make():
                got["fit"] = ts.fit_table(rows, [[cell_style(plan["cells"][r][c], styles, header, r) for c in range(nc)]
                                                 for r in range(nr)], fmt.get("metrics") or {}, cap, lr, fmt.get("measure"))
                want = got["fit"]["widths"]
                return table_create(s, nr, nc, want, sum(want))
            done["width"] = _format_try(fmt, "width", "표", make)       # 너비 셈 오류도 여기서 — 예전처럼 만들기로
            fit = got.get("fit")
            col_hu = fit["widths"] if done["width"] else None
        if done["border"] is None and any(k in cf for row in plan["cells"] for cf in row for k in BORDER_KEYS):
            done["border"] = True                              # 칸 서식에 선·배경이 있을 때만(fit_plan 은 없음)
        if done["header"] is None and any(cf.get("header") for row in plan["cells"] for cf in row):
            done["header"] = True
    if col_hu is None and not s.s.action("TableCreate", "TableCreation", Rows=nr, Cols=nc, WidthType=0, HeightType=0):
        raise api.EditFailed("표 만들기(TableCreate %d×%d) 실패" % (nr, nc))
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            if c:
                s.s.run("TableRightCell")
            cf = plan["cells"][r][c] if plan is not None else None
            apply_style(s, idx, cell_style(cf, styles, header, r))
            for k, line in enumerate(text.split("\n")):
                if k:
                    s.s.run("BreakPara")
                if line:
                    insert_text(s, line)
            if on and done["border"] is True:
                done["border"] = _format_try(fmt, "border", [r, c], lambda: cell_border_fill(s, cf))
            if on and done["header"] is True and cf.get("header"):
                done["header"] = _format_try(fmt, "header", [r, c], lambda: cell_header(s))
        if r < nr - 1:
            s.s.run("TableLowerCell")
            for _ in range(nc - 1):
                s.s.run("TableLeftCell")
    if on and done["margin"] is None and plan.get("inside_margin"):
        def margin():
            ok, got["width"] = table_props(s, plan["inside_margin"])
            return ok
        done["margin"] = _format_try(fmt, "margin", "표", margin)
    s.s.run("CloseEx")                                         # 칸 → 표 밖(상위 목록)
    if on and done["center"] is None:                          # 표 밖에서 — 표가 든 문단 가운데 정렬(P-041)
        done["center"] = _format_try(fmt, "center", "표", lambda: center_anchor(s, anchor))
        if done["center"] and done["anchor_margin"] is None and shift_any(fmt, styles):
            done["anchor_margin"] = _format_try(fmt, "anchor_margin", "표", lambda: anchor_margins_zero(s))
    got_cap = None
    if caption:                                                # 표 캡션 — 한/글 '캡션 넣기'(P-049)
        side = None
        if on and done["caption"] is None:                     # 캡션 자리(위)는 캐럿이 캡션 안일 때
            def side():
                return _format_try(fmt, "caption", "표", lambda: caption_side(s, caption["side"]))
        got_cap = attach_caption(s, idx, anchor, caption, clean, side)
        if side:
            done["caption"] = got_cap["in_caption"]
    newnum = new_number(s, anchor, CAPTION_NUM["table"], caption["newnum"]) if caption and caption.get("newnum") else None
    extra, pos = _end_after_object(s, anchor)
    info = {"type": "table", "size": [nr, nc], "anchor": anchor, "end": pos, "extra": extra}
    if got_cap:
        info["caption"] = {"pos": got_cap["pos"], "moved": got_cap["moved"]}
    if newnum:
        info["newnum"] = newnum
    if plan is not None:
        info["format"] = {"ref": plan["ref"], "ref_id": plan.get("ref_id"), "mode": plan["mode"], "col_hu": col_hu,
                          "fit": {k: fit.get(k) for k in ("need", "word", "how", "capped", "maxmin", "lines")} if fit else None,
                          "avail": cap, "width_read": got.get("width"), "done": done}
    return extra, info


def expected_texts(model, keys, each=None):
    """템플릿 모든 글자 위치의 '기대 글자' — 자리별 값(each, 문서 차례)을 먼저, 그다음 키 값(긴 키 먼저 — hwpx-drm
    replace 와 같은 순서). 쓰기 순서(replace_each → AllReplace)와 같다."""
    out, used = {}, {f: 0 for f in (each or {})}
    order = sorted(keys, key=len, reverse=True)
    for loc, _, t in hp.iter_locations(model):
        for f, vals in (each or {}).items():
            if f in t:
                parts = t.split(f)
                t = parts[0]
                for part in parts[1:]:
                    t += vals[used[f]] + part
                    used[f] += 1
        for k in order:
            t = t.replace(k, keys[k])
        out[loc] = t
    return out


def plan_each(m, each, single=()):
    """자리별 값(D-036): {찾을 글자: 값 | [값, …]} → {찾을 글자: [자리마다 값]} (템플릿 m 기준 검사, 어긋나면 명세 오류).
    자리 = 템플릿 본문(표지·표 칸 포함) 글자의 문서 차례 — 머리말·꼬리말·주석에 있으면 안 된다(다시 찾기 미실측).
    찾을 글자끼리·AllReplace 키와 서로 포함하면 안 되고, 값에 다른 찾을 글자가 있으면 안 된다(뒤에서 다시 찾힌다).
    값이 찾을 글자 자신이면 그 자리는 그대로 둔다."""
    finds = list(each)
    for a in finds:
        for b in finds + list(single):
            if a != b and (a in b or b in a):
                raise SpecError("찾을 글자가 서로 겹친다: %r · %r" % (a, b))
    locs = list(hp.iter_locations(m))
    out = {}
    for f, v in each.items():
        hits = [(loc, kind, t.count(f)) for loc, kind, t in locs if f in t]
        outside = [loc for loc, kind, _ in hits if kind in NONBODY]
        if outside:
            raise SpecError("%r 가 머리말·꼬리말·주석에 있다 %s — 자리별 값은 본문 자리만 바꾼다" % (f, outside[:3]))
        n = sum(c for _, _, c in hits)
        if not n:
            raise SpecError("템플릿에 %r 가 없다" % f)
        vals = [v] * n if isinstance(v, str) else list(v)
        if len(vals) != n:
            raise SpecError("%r 자리 %d곳(%s)에 값 %d개 — 같아야 한다" % (f, n, ", ".join(x[0] for x in hits[:6]), len(vals)))
        for x in vals:
            other = [g for g in finds if g != f and g in x]
            if other:
                raise SpecError("%r 의 값에 다른 찾을 글자 %r 가 있다" % (f, other[0]))
            if f in x and x != f:
                raise SpecError("%r 의 값에 자기 글자가 섞여 있다 — 그대로 두려면 값을 %r 로" % (f, f))
        out[f] = vals
    return out


def msgbox_mode(s, mode):
    """한/글 메시지 상자 자동 응답을 mode 로 → 이전 값(되돌릴 때 쓴다). 못 바꾸면 None."""
    try:
        return s.s.call("SetMessageBoxMode", s.hwp.SetMessageBoxMode, mode)
    except hs.TimeoutKilled:
        raise
    except Exception:
        return None


def size_mismatch(m, broot):
    """쓴 최상위 문단 중 글자 크기가 그 스타일 정의와 다른 곳 → [[문단 ID, 스타일, 문단 크기들, 스타일 크기, 글자 앞]].
    표 뒤 빈 문단을 다시 쓸 때 '스타일 모양으로 덮어 쓸까요?'에 '아니오'가 되면 앞 칸의 글자 모양이 남는다(P-038)."""
    size = {d["name"]: (d.get("char") or {}).get("height") for d in m["styledefs"]}
    out = []
    for b in m["body"]:
        if b["type"] != "para" or not TOP.match(b["id"]) or root_of(m, b["id"]) <= broot:
            continue
        want = size.get(b.get("style"))
        if want and b.get("heights") and b["heights"] != [want]:
            out.append([b["id"], b.get("style"), b["heights"], want, b["text"][:30]])
    return out


def align_mismatch(m, broot):
    """쓴 최상위 문단 중 정렬이 그 스타일 정의와 다른 곳 → [[문단 ID, 스타일, 문단 정렬, 스타일 정렬, 글자 앞]].
    표가 든 문단을 가운데 정렬하면(P-041) 한/글이 표 뒤에 둔 빈 문단이 그 정렬을 이어받을 수 있다 — 다음 항목은 같은
    스타일 다시 입히기(F-109, 자동 '예')로 스타일 모양이 되지만, 남으면 여기서 알린다. 표가 든 문단은 글자가 없어 보지 않는다."""
    want = {d["name"]: (d.get("para") or {}).get("Align") or "Justify" for d in m["styledefs"]}
    out = []
    for b in m["body"]:
        if b["type"] != "para" or not TOP.match(b["id"]) or root_of(m, b["id"]) <= broot:
            continue
        w, a = want.get(b.get("style"), "Justify"), b.get("align") or "Justify"     # 정렬 값이 없으면 양쪽(한/글 기본)
        if a != w:
            out.append([b["id"], b.get("style"), a, w, b["text"][:30]])
    return out


def front_format_changed(m0, m, broot):
    """앞부분(본문 첫 장 제목 앞) 최상위 문단의 스타일·글자 크기가 쓰기 전(템플릿)과 다른 곳 → [[문단 ID, 전, 뒤]].
    '스타일 모양으로 덮어 쓸까요?'의 자동 '예'(D-039, F-109 다시 입히기)가 쓴 문단 밖(같은 스타일의 표지 문단 등)까지
    바꾸지 않았는지 본다(검토 P-040 8, U-24). 글자가 없는 문단(크기 없음)은 비교하지 않는다(키·양식 글자 지우기)."""
    def front(x):
        return {b["id"]: (b.get("style"), b.get("heights")) for b in x["body"]
                if b["type"] == "para" and TOP.match(b["id"]) and root_of(x, b["id"]) < broot}
    a, b = front(m0), front(m)
    return [[k, list(a[k]), list(b[k])] for k in a if k in b and a[k][1] and b[k][1] and a[k] != b[k]]


def _label_key(v):
    m = re.match(r"표 (\d+)$", str(v))
    return (0, int(m.group(1))) if m else (1, str(v))


def styles_changed(m0, m):
    """쓰기 전(템플릿)·뒤 스타일 정의(문단·글자 모양 값)가 다른 스타일 이름 — 더해진 것은 '+', 빠진 것은 '-' 를 붙인다.
    메시지 상자 자동 응답('예')이 스타일 정의를 바꾸지 않았는지 본다(P-038, U-24). 글자 모양은 언어별 값(langs —
    글꼴·글꼴 종류·장평·자간·상대 크기)까지 견준다(P-045)."""
    a = {d["name"]: (d["para"], d["char"]) for d in m0["styledefs"]}
    b = {d["name"]: (d["para"], d["char"]) for d in m["styledefs"]}
    return (sorted(n for n in a if n in b and a[n] != b[n]) + sorted("+" + n for n in b if n not in a)
            + sorted("-" + n for n in a if n not in b))


def find_forward(s):
    try:
        return s.s.call("FindDir", s.hwp.FindDir, "Forward")
    except hs.TimeoutKilled:
        raise
    except Exception:
        return 0


def replace_each(s, each):
    """자리별 값 쓰기(D-036): 찾을 글자마다 문서 처음에서 '다시 찾기'(앞으로)로 하나씩 찾아 지우고 값을 넣는다.
    → {찾을 글자: 자리 수}. 결과는 쓰기 뒤 앞부분 글자 대조(expected_texts)로 확인한다 — 어긋나면 저장하지 않는다.
    실측 전 가정(U-23): 찾으면 그 글자가 선택되고, Delete 가 선택을 지우고, 다음 찾기는 캐럿 뒤에서 이어진다."""
    fwd = find_forward(s)
    done = {}
    for f, vals in each.items():
        s.s.run("MoveDocBegin")
        for n, v in enumerate(vals):
            if not s.s.action("RepeatFind", "FindReplace", FindString=f, ReplaceString="", Direction=fwd,
                              IgnoreMessage=1, **FIND_OPTIONS):
                raise api.EditFailed("%r 의 %d번째 자리를 찾지 못했다(자리 %d곳 예상, U-23)" % (f, n + 1, len(vals)))
            s.s.run("Delete")
            if v:
                insert_text(s, v)
        done[f] = len(vals)
    return done


def written_blocks(m, broot):
    """첫 장 제목 뒤 본문 블록 → [{"type": "para", "text", "style"} | {"type": "table", "rows"}] (표 칸 글자 격자)."""
    out, after = [], False
    for b in m["body"]:
        if b["type"] == "para" and TOP.match(b["id"]):
            r = root_of(m, b["id"])
            if r == broot:
                after = True
                continue
            if r > broot:
                out.append({"type": "para", "id": b["id"], "text": b["text"], "style": b.get("style")})
        elif b["type"] == "table" and after:
            grid = [[""] * b["cols"] for _ in range(b["rows"])]
            for c in b["cells"]:
                if c["row"] < b["rows"] and c["col"] < b["cols"]:
                    grid[c["row"]][c["col"]] = c["text"]
            out.append({"type": "table", "id": b["id"], "rows": grid})
    return out


def compare_written(items, got):
    """명세 항목과 쓴 결과 → 어긋난 곳 목록."""
    bad = []
    for n in range(max(len(items), len(got))):
        want = items[n] if n < len(items) else None
        have = got[n] if n < len(got) else None
        if want is None or have is None or want["type"] != have["type"]:
            bad.append({"n": n, "want": (want or {}).get("text") or (want or {}).get("type"),
                        "got": (have or {}).get("text") or (have or {}).get("type")})
        elif want["type"] == "para" and (want["text"] != have["text"] or want["style"] != have["style"]):
            bad.append({"n": n, "id": have["id"], "want": [want["text"][:40], want["style"]],
                        "got": [have["text"][:40], have["style"]]})
        elif want["type"] == "table" and want["rows"] != have["rows"]:
            bad.append({"n": n, "id": have["id"], "want": want["rows"][:2], "got": have["rows"][:2]})
        if len(bad) >= 10:
            break
    return bad


def layout_check(m, broot, items):
    """첫 장 제목 뒤 최상위 문단 배치(글자·표·개체·빈 문단)를 쓸 항목과 맞춘다. 표·그림 바로 뒤 빈 문단 하나는 한/글이
    만드는 것이라 허용(쓴 항목으로 다시 쓰지 못했을 때). → (어긋난 곳, 허용한 빈 문단 ID, 배치 목록)."""
    tail = (m.get("roots") or [])[broot + 1:]
    seq, tolerated = [], []
    for i, r in enumerate(tail):
        if r["kind"] == "empty" and i and tail[i - 1]["kind"] in ("table", "object"):
            tolerated.append(r["id"])
            continue
        seq.append(r)
    want = [{"table": "table", "picture": "object"}.get(x["type"], "text") for x in items]
    bad = [{"n": n, "want": w, "got": (seq[n]["id"], seq[n]["kind"]) if n < len(seq) else None}
           for n, w in enumerate(want) if n >= len(seq) or seq[n]["kind"] != w][:5]
    if len(seq) > len(want):
        bad.append({"n": len(want), "want": None, "got": [(r["id"], r["kind"]) for r in seq[len(want):][:3]]})
    return bad, tolerated, [(r["id"], r["kind"]) for r in tail]


def written_captions(x, broot):
    """쓴 HWPML(x)의 첫 장 제목 뒤 최상위 문단에 든 표·그림(문서 차례) → [{"tag", "at": 문단 ID, "text": 캡션 글자 | None,
    "style", "align": 캡션 첫 문단 정렬, "side", "num": 자동 번호 종류들, "heights": 캡션 글자 크기들, "newnum": 같은 문단에서
    그 개체 앞에 든 '새 번호로 시작' [[종류, 번호], …]}] (P-049·P-050). 캡션 글자는 hwpml_parse 와 같은 꼴 — 자동 번호(AUTONUM)는
    한/글이 내보낸 그 번호 글자다."""
    x, _ = hp.clean(x)
    root = ET.fromstring(re.sub("^﻿?\\s*<\\?xml[^>]*\\?>", "", x, count=1))
    par = hp._Parser(root)
    out, k = [], -1
    body = root.find("BODY")
    for si, sec in enumerate(body.findall("SECTION") if body is not None else []):
        for pi, p in enumerate(sec.findall("P")):
            k += 1
            if k <= broot:
                continue
            nn = []                                        # 개체 앞 '새 번호로 시작' (P-050)
            for el in (e for t in p.findall("TEXT") for e in t if e.tag in ("TABLE", "PICTURE", "NEWNUM")):
                if el.tag == "NEWNUM":
                    nn.append([el.get("NumberType"), el.get("Number")])
                    continue
                rec = {"tag": el.tag, "at": "s%d.p%d" % (si, pi), "text": None, "newnum": nn}
                nn = []
                c = el.find("SHAPEOBJECT/CAPTION")
                pl = c.find("PARALIST") if c is not None else None
                if pl is not None:
                    ps = pl.findall("P")
                    rec.update(text=hp.flatten(par.parse_list(pl, "cap")), side=c.get("Side"),
                               style=par.styles.get(ps[0].get("Style")) if ps else None,
                               align=(par.aligns.get(ps[0].get("ParaShape")) or "Justify") if ps else None,
                               num=[a.get("NumberType") for a in pl.iter("AUTONUM")],
                               heights=sorted({par.heights.get(t.get("CharShape")) for q in ps for t in q.findall("TEXT")
                                               if "".join(t.itertext()).strip()} - {None}, key=hp._int))
                out.append(rec)
    return out


def _cap_label(cap):
    """캡션 계획 → '표 N'·'그림 N'(명세 번호 — 캡션 없는 표까지 센 표 서식 라벨과 다르다, 검토 P-050 D1-①-01)."""
    return " ".join(cap["text"].split(" ")[:2])


def newnum_found(caps, items):
    """계획한 '새 번호로 시작'(종류·번호)을 쓴 문서의 그 개체 앞(written_captions newnum)에서 찾은 수 — NewNumber 가 True 를
    돌려준 수가 아니라 문서에서 센 값(검토 P-050 D1-②-02)."""
    want = [x for x in items if x["type"] in ("table", "picture")]
    return sum(1 for w, g in zip(want, caps) if (w.get("cap") or {}).get("newnum") and g["tag"] == w["type"].upper()
               and [CAPTION_NUM[w["type"]], str(w["cap"]["newnum"])] in g.get("newnum", []))


def written_newnums(x, broot):
    """HWPML(x)의 첫 장 제목 뒤 최상위 문단 안 모든 '새 번호로 시작'(NEWNUM, 깊이 무관) → [(종류, 번호)] (P-050 D1F-N02)."""
    if not x:
        return []
    x, _ = hp.clean(x)
    root = ET.fromstring(re.sub("^\ufeff?\\s*<\\?xml[^>]*\\?>", "", x, count=1))
    out, k = [], -1
    body = root.find("BODY")
    for sec in body.findall("SECTION") if body is not None else []:
        for p in sec.findall("P"):
            k += 1
            if k > broot:
                out += [(e.get("NumberType"), e.get("Number")) for e in p.iter("NEWNUM")]
    return out


def stray_newnums(before, after, items):
    """쓰는 동안 생긴 새 번호(after − before) 가운데 계획(items 의 cap newnum)에 없는 것 → [[종류, 번호], …]. 작성기는 표·그림
    새 번호만 넣는다 — 다른 종류(쪽·각주…)나 다른 번호가 생겼으면 NumType·NewNumber 가 뜻대로 듣지 않은 것이라 저장하지
    않는다(쪽 번호가 본문 중간에서 다시 시작하는 문서를 막는다, 검토 P-050 D1F-N02)."""
    import collections
    want = collections.Counter((CAPTION_NUM[x["type"]], str(x["cap"]["newnum"])) for x in items
                               if x["type"] in ("table", "picture") and (x.get("cap") or {}).get("newnum"))
    extra = collections.Counter(after) - collections.Counter(before) - want
    return sorted([list(t) for t in extra.elements()], key=lambda t: (str(t[0]), str(t[1])))


def caption_check(caps, items, defs, side_done, newnum_done=None):
    """명세의 표·그림(차례)과 쓴 표·그림 캡션(written_captions)을 맞춘다(P-049) → (어긋남, 경고).
    어긋남(저장하지 않는다): 표·그림 수·종류, 캡션 글자(자동 번호 포함 — 본문 인용 '그림 N' 이 이 번호를 가리킨다), 캡션 스타일.
    경고: 캡션 자리(표 위·그림 아래), 자동 번호 종류, 계획한 '새 번호로 시작'이 개체 앞에 없음(P-050 — 번호가 맞으면 저장은 한다;
    넣기가 실패로 남은 곳(newnum_done: 항목 번호 → 결과 False)은 이미 알렸으므로 보지 않는다),
    캡션 글자 크기·정렬(defs: 스타일 이름 → {"height", "align"} 정의 값 —
    글자 문단이던 캡션을 size_mismatch·align_mismatch 가 보던 것과 같게, 검토 P-049 D1-③-01). 표 캡션 자리를 입히지 못한
    (False·꺼짐) 표는 자리를 보지 않는다 — 이미 '표 서식을 입히지 못한 곳'으로 알렸다(side_done: 항목 번호 → 결과)."""
    want = [(n, x) for n, x in enumerate(items) if x["type"] in ("table", "picture")]
    bad, warn = [], []
    if len(want) != len(caps):
        bad.append({"what": "표·그림 수", "want": len(want), "got": len(caps)})
    for (n, w), g in zip(want, caps):
        cap = w.get("cap")
        if g["tag"] != w["type"].upper():
            bad.append({"at": g["at"], "what": "개체 종류", "want": w["type"].upper(), "got": g["tag"]})
            continue
        if (cap or {}).get("text") != g["text"]:
            bad.append({"at": g["at"], "what": "캡션 글자", "want": (cap or {}).get("text"), "got": g["text"]})
        if not cap or g["text"] is None:
            continue
        if g["style"] != cap["style"]:
            bad.append({"at": g["at"], "what": "캡션 스타일", "want": cap["style"], "got": g["style"]})
        if g["side"] != cap["side"] and side_done.get(n) not in (False, "off"):
            warn.append({"at": g["at"], "what": "캡션 자리", "want": cap["side"], "got": g["side"]})
        if g["num"] != [CAPTION_NUM[w["type"]]]:
            warn.append({"at": g["at"], "what": "자동 번호", "want": [CAPTION_NUM[w["type"]]], "got": g["num"]})
        if cap.get("newnum") and (newnum_done or {}).get(n) is not False \
                and [CAPTION_NUM[w["type"]], str(cap["newnum"])] not in g.get("newnum", []):
            warn.append({"at": g["at"], "what": "새 번호", "want": [CAPTION_NUM[w["type"]], str(cap["newnum"])],
                         "got": g.get("newnum", [])})
        d = defs.get(cap["style"]) or {}
        if d.get("height") and g["heights"] and g["heights"] != [d["height"]]:
            warn.append({"at": g["at"], "what": "글자 크기", "want": d["height"], "got": g["heights"]})
        if d.get("align") and g.get("align") and g["align"] != d["align"]:
            warn.append({"at": g["at"], "what": "정렬", "want": d["align"], "got": g["align"]})
    return bad, warn


def write(s, meta, blocks, log=print, force=False, pictures=True):
    """명세대로 쓰고 확인해 저장한다 → 기록 dict (rec["ok"]). pictures=False: 그림 대신 '그림 삽입 필요' 자리 표시."""
    styles = profiles.resolve_styles(meta.get("profile"), meta.get("styles"), ROOT)
    tpl, out = ROOT / meta["template"], ROOT / meta["out"]
    rec = {"template": meta["template"], "out": meta["out"], "ok": False, "warnings": []}
    if not tpl.exists():
        raise hs.PreconditionError("템플릿이 없다: %s" % meta["template"])
    if out.resolve() == tpl.resolve():
        raise hs.PreconditionError("출력이 템플릿과 같다 — 템플릿은 저장하지 않는다")
    items = plan(blocks, styles, pictures)
    rec["text_check"] = text_checks(blocks)                     # 절 인용·글자 번호·수준 건너뜀(P-051 — 경고만)
    rec["warnings"] += text_check_warnings(rec["text_check"])
    tstyle, plans = None, [None] * len(items)
    if meta.get("table_style"):                                 # 표 서식 파일(P-040, D-042)
        tp = ROOT / meta["table_style"]
        if not tp.exists():
            raise SpecError("표 서식 파일이 없다: %s" % meta["table_style"])
        try:
            tstyle = json.loads(tp.read_text(encoding="utf-8"))
        except (ValueError, OSError) as e:                      # JSON·글자 꼴 오류 — 손대기 전에 명세 오류(검토 P-040 9)
            raise SpecError("표 서식 파일을 읽지 못했다: %s (%s)" % (meta["table_style"], e))
        bad = ts.validate(tstyle)
        if bad:
            raise SpecError("표 서식 파일이 맞지 않다: %s — %s" % (meta["table_style"], bad[:3]))
        plans = [ts.plan_table(tstyle, x.get("caption"), x["rows"], x.get("header", True)) if x["type"] == "table"
                 else None for x in items]
    plans = [fit_plan(x["rows"], x["header"], styles) if x["type"] == "table" and p is None else p
             for x, p in zip(items, plans)]                     # 서식 계획이 없는 표도 칸 너비 맞춤·가운데(P-045, F-153)
    fitting = tstyle is not None or any(plans)                 # 서식 파일이 있으면 표가 없어도 보고(P-040 과 같게)
    rec["plan"] = {"blocks": len(blocks), "items": len(items), "tables": sum(1 for x in items if x["type"] == "table"),
                   "pictures": sum(1 for x in items if x["type"] == "picture"),
                   "figures": sum(1 for x in items if x.get("figure")), "needs": sum(1 for x in items if x.get("need")),
                   "placeholders": sum(1 for x in items if x.get("placeholder")), "captions": sum(1 for x in items if x.get("cap")),
                   "newnums": sum(1 for x in items if x["type"] != "para" and (x.get("cap") or {}).get("newnum"))}
    s.open(tpl)
    m0 = s.model()
    tops = top_paras(m0)
    head = tops[-1] if tops else None
    if head is None or _norm(head["text"]) != _norm(blocks[0]["text"]) \
            or head.get("style") != styles["heading"].format(level=1):
        raise SpecError("템플릿 마지막 문단이 첫 장 제목(%s, %s)이 아니다: %r" % (
            blocks[0]["text"], styles["heading"].format(level=1), (head or {}).get("text")))
    broot = root_of(m0, head["id"])
    rec["body_root"] = broot
    after_head = [b["id"] for b in m0["body"][m0["body"].index(head) + 1:]]
    if after_head:
        raise SpecError("첫 장 제목 뒤에 표·개체가 있다 %s — 본문을 비운 템플릿이어야 한다" % after_head[:3])
    trailing = sum(m0["stats"]["section_paras"]) - 1 - broot   # 제목 뒤 빈 문단(공통 템플릿: 본문 지우기에서 남은 그릇)
    rec["reused_empty_para"] = trailing > 0
    nn0 = written_newnums(s.last_hwpml or "", broot)            # 템플릿 본문(제목 뒤)에 이미 있던 새 번호(D1F-N02)
    idx = style_index(m0)
    missing = sorted(({x["style"] for x in items if x["type"] != "table"} | {styles["th"], styles["td"], styles["anchor"]}
                      | {x["cap"]["style"] for x in items if x.get("cap")} | set(ts.styles_used(plans))) - set(idx))
    if missing:
        raise SpecError("템플릿에 없는 스타일 %s" % missing)
    keys = {k: v for k, v in (meta.get("keys") or {}).items() if isinstance(v, str) and v != ""}
    each = {k: v for k, v in (meta.get("keys") or {}).items() if isinstance(v, list)}
    each.update(meta.get("front") or {})
    each = plan_each(m0, each, keys)                             # 자리별 값 — 어긋나면 손대기 전에 명세 오류
    present = {k for k in keys if any(k in t for _, _, t in hp.iter_locations(m0))}
    rec["keys_absent"] = sorted(set(keys) - present)
    if rec["keys_absent"]:
        rec["warnings"].append("템플릿에 없는 키 %s — 넣지 않았다" % rec["keys_absent"])
    use = {k: keys[k] for k in present}
    expect = expected_texts(m0, use, each)
    if each:
        rec["each"] = replace_each(s, each)
    if use:
        r = s.replace(use)
        rec["replace"] = {k: {kk: v[kk] for kk in ("before", "after", "remaining")} for k, v in r.items()}
    reuse, rec["objects"] = bool(trailing), []                  # 첫 항목은 제목 뒤 빈 문단이 있으면 거기에
    fmt = {"failed": [], "off": set(), "off_at": {}, "total": None}
    if fitting:                                                 # 표가 있으면(서식 파일이 없어도 — P-045)
        fmt["total"] = ts.default_table_width(s.last_hwpml or "", int(TOP.match(head["id"]).group(1)))
        fmt["metrics"] = ts.style_metrics(m0["styledefs"])                # 칸 너비 맞춤(P-041): 칸 스타일 글자 모양
        fmt["measure"] = ts.gdi_measure()                                  # Windows: 글꼴로 글자 폭을 잰다 — 아니면 어림
        for n, x in enumerate(items):                           # 칸 안 여백 위·아래 = 칸 글자 크기 반 — 모든 표(P-048)
            if x["type"] == "table" and plans[n] is not None:
                plans[n]["inside_margin"] = ts.pad_margin(
                    plans[n].get("inside_margin"), [[cell_style(cf, styles, x["header"], r) for cf in row]
                                                    for r, row in enumerate(plans[n]["cells"])], fmt["metrics"])
        rec["table_style"] = {"file": meta.get("table_style"), "source": (tstyle or {}).get("source"),
                              "default": (tstyle or {}).get("default"),
                              "table_width": fmt["total"], "measure": "gdi" if fmt["measure"] else "estimate",
                              "tables": [{"n": n, "label": "표 %d" % k, "caption": x.get("caption"),
                                          "ref": (plans[n] or {}).get("ref"), "mode": (plans[n] or {}).get("mode"),
                                          "shared_edges": (plans[n] or {}).get("shared_edges"),
                                          "inside_margin": (plans[n] or {}).get("inside_margin")}
                                         for k, (n, x) in enumerate(((n, x) for n, x in enumerate(items)
                                                                     if x["type"] == "table"), 1)]}
    reads = []                                                  # 쪽 번호 두 길 [KeyIndicator, CurrentPrintPage] (D2-②-01)
    pages = [print_page(s, broot, reads)]                       # 본문 첫 쪽 인쇄 번호 — 쓴 뒤와 견준다(P-050 D1-②-01)
    old_mode = msgbox_mode(s, MSGBOX_YES)                       # 본문 쓰는 동안 '덮어 쓸까요?' → 예 (P-038, F-108)
    rec["msgbox_auto"] = clean = old_mode is not None           # 못 켜면 같은 스타일 다시 입히기(F-109)를 하지 않는다
    k_table = 0
    try:
        for n, it in enumerate(items):
            new, reuse = not reuse, False
            if it["type"] == "table":
                k_table += 1
                fmt["n"], fmt["label"] = n, "표 %d" % k_table
                for kind in FORMAT_KINDS:                       # 표 셋에서 실패한 종류는 나머지 표에서 끈다(종류마다)
                    if kind not in fmt["off"] and len({f["n"] for f in fmt["failed"]
                                                       if f["kind"] == kind}) >= FORMAT_OFF_AFTER:
                        fmt["off"].add(kind)
                        fmt["off_at"][kind] = fmt["label"]
                reuse, info = append_table(s, idx, styles, it["rows"], it["header"], new, plans[n], fmt, clean,
                                           it.get("cap"))
                rec["objects"].append(dict(info, n=n, label=fmt["label"]))
            elif it["type"] == "picture":
                reuse, info = append_picture(s, idx, it["style"], it["path"], it.get("size"), new, clean, it.get("cap"))
                rec["objects"].append(dict(info, n=n, placeholder=bool(it.get("placeholder"))))
            else:
                append_para(s, idx, it["style"], it["text"], new, clean)
            if (n + 1) % 50 == 0:
                log("  … %d/%d" % (n + 1, len(items)))
    finally:
        if old_mode is not None:
            try:
                msgbox_mode(s, old_mode)
            except hs.HwpError:
                pass
        if fmt.get("measure"):
            fmt["measure"].close()
    pages.append(print_page(s, broot, reads))
    s._model = None
    m = s.model(refresh=True)
    heads = heading_check(s, m, broot, blocks)                  # 제목마다 한/글 개요 번호 = 명세 차례({{절:}} 인용, P-051)
    texts = {loc: t for loc, _, t in hp.iter_locations(m)}
    front = {loc: {"want": expect[loc][:60], "got": (texts.get(loc) or "(사라짐)")[:60]}
             for loc in expect if _visible(texts.get(loc)) != _visible(expect[loc])}
    got = written_blocks(m, broot)
    bad = compare_written([x for x in items if x["type"] != "picture"], got)
    lbad, tolerated, layout = layout_check(m, broot, items)
    pics = [c["at"] for c in m["ctrls"] if c["tag"] == "PICTURE" and TOP.match(c["at"]) and root_of(m, c["at"]) > broot]
    roots = [sum(m0["stats"]["section_paras"]), sum(m["stats"]["section_paras"])]
    sizes = size_mismatch(m, broot)
    aligns = align_mismatch(m, broot)
    restyled = styles_changed(m0, m)
    front_fmt = front_format_changed(m0, m, broot)
    if fitting:                                                 # 칸 스타일 글자 모양·글꼴을 잼 여부(P-041) — 보고에
        used = sorted({cell_style(cf, styles, x["header"], r) for n, x in enumerate(items) if plans[n]
                       for r, row in enumerate(plans[n]["cells"]) for cf in row})
        faces = getattr(fmt.get("measure"), "faces", {}) or {}
        fonts = {}
        for k in used:                                          # 언어별 글꼴까지(P-045) — 그 언어 글자가 없으면 None
            mt = fmt["metrics"].get(k) or {}
            fs = {mt.get("hangul"), mt.get("latin")} | {v["face"] for v in (mt.get("slots") or {}).values()}
            bold = " (진하게)" if mt.get("bold") else ""         # GdiMeasure.faces 키 꼴(검토 P-045 D1-②-02)
            fonts[k] = dict(mt, measured={f: faces.get(f + bold) for f in sorted(f for f in fs if f)})
        rec["table_style"]["fonts"] = fonts
        rec["table_style"]["measure"] = "gdi" if any(faces.values()) else "estimate"   # 하나라도 글꼴로 잼(검토 L8)
        rec["table_style"]["anchor_style"] = {k: (fmt["metrics"].get(styles["anchor"]) or {}).get(k)
                                             for k in ("m_left", "m_right", "m_indent")}
    fmt_bad = []
    if fitting:                                                 # 표 서식 대조 — 쓴 표(차례)와 계획(P-040)
        wt = [b["id"] for b in got if b["type"] == "table"]
        objs = {o["n"]: o for o in rec["objects"] if o["type"] == "table"}
        pairs = []
        for k, n in enumerate(i for i, x in enumerate(items) if x["type"] == "table"):
            if plans[n] is not None and k < len(wt):
                f = objs.get(n, {}).get("format") or {}
                pairs.append((wt[k], dict(plans[n], col_hu=f.get("col_hu"), done=f.get("done"), center=True,
                                          anchor_reset=(f.get("done") or {}).get("anchor_margin") is True,
                                          label="표 %d" % (k + 1))))
        fmt_bad = ts.check_tables(s.last_hwpml, pairs) if pairs and s.last_hwpml else []
    caps = written_captions(s.last_hwpml, broot)               # 한/글 캡션 대조(P-049)
    cbad, cwarn = caption_check(caps, items, {d["name"]: {"height": (d.get("char") or {}).get("height"),
                                                          "align": (d.get("para") or {}).get("Align") or "Justify"}
                                              for d in m["styledefs"]},
                                {o["n"]: ((o.get("format") or {}).get("done") or {}).get("caption") for o in rec["objects"]},
                                {o["n"]: o["newnum"]["ok"] for o in rec["objects"] if o.get("newnum")})
    nfail = [dict(o["newnum"], at=_cap_label(items[o["n"]]["cap"])) for o in rec["objects"]   # 캡션 번호로(검토 D1-①-01)
             if o.get("newnum") and not o["newnum"]["ok"]]
    rec["check"] = {"front_changed": dict(sorted(front.items())[:10]), "front_changed_count": len(front),
                    "written": len(got), "mismatch": bad, "root_paras": roots, "layout_mismatch": lbad,
                    "empty_after_object": tolerated, "pictures": len(pics), "size_mismatch": sizes[:20],
                    "styles_changed": restyled, "front_format_changed": front_fmt[:20], "align_mismatch": aligns[:20],
                    "captions": {"written": sum(1 for c in caps if c["text"] is not None), "mismatch": cbad[:10],
                                 "warn": cwarn[:20], "warn_count": len(cwarn),
                                 "newnum": newnum_found(caps, items),           # 쓴 문서에서 찾은 계획 새 번호(D1-②-02)
                                 "newnum_inserted": sum(1 for o in rec["objects"] if (o.get("newnum") or {}).get("ok")),
                                 "newnum_failed": nfail[:10]},
                    "page": {"body_first": pages, "reads": reads},              # 본문 첫 쪽 인쇄 번호 [쓰기 전, 쓴 뒤]
                    "headings": heads}                                          # 제목 개요 번호 대조(P-051, U-32)
    if fitting:
        rec["check"]["table_format"] = fmt_bad[:30]
        rec["check"]["table_format_count"] = len(fmt_bad)
        rec["check"]["table_format_failed"] = fmt["failed"][:20]
        rec["check"]["table_format_failed_count"] = len(fmt["failed"])
        rec["check"]["table_format_off"] = {FORMAT_NAMES[k]: v for k, v in sorted(fmt["off_at"].items())}
    problems = []
    if front:
        problems.append("앞부분 글자 %d곳이 기대와 다르다 %s" % (len(front), list(front)[:3]))
    if bad:
        problems.append("쓴 블록이 명세와 다르다(%d곳 이상) %s" % (len(bad), bad[:2]))
    if lbad:
        problems.append("문단 배치가 명세와 다르다 %s" % lbad[:2])
        rec["check"]["layout"] = layout[:120]
    if len(pics) != rec["plan"]["pictures"]:
        problems.append("그림 수 %d (기대 %d)" % (len(pics), rec["plan"]["pictures"]))
    if cbad:
        problems.append("표·그림 캡션이 명세와 다르다(%d곳) %s" % (len({b.get("at") for b in cbad}), cbad[:2]))
    inserted = rec["check"]["captions"]["newnum_inserted"]
    if None not in pages and pages[0] != pages[1]:
        problems.append("본문 첫 쪽 번호가 %d → %d 로 바뀌었다 — %s" % (tuple(pages) + (
            "넣은 '새 번호로 시작' %d개가 템플릿의 쪽 새 번호를 무효로 했을 수 있다(pyhwpx 주의 3, U-31)" % inserted
            if inserted else "'새 번호로 시작'은 넣지 않았다(원인 미상)",)))
    if heads["mismatch_count"] and uses_section_refs(blocks):  # {{절:}} 인용이 있으면 문서 글자의 번호가 틀린다 — 저장 안 함
        problems.append("제목 개요 번호가 명세 차례와 다르다(%d곳) %s — {{절:}} 인용 번호가 틀린다(U-32)" % (
            heads["mismatch_count"], heads["mismatch"][:3]))
    elif heads["structural"]:                                  # 제목 수가 다르거나 번호 없는 제목 — 쓴 문서가 틀렸다(D4-②-01)
        problems.append("제목 개요 번호가 명세 차례와 다르다(%d곳) %s — 쓴 제목 수가 다르거나 번호 없는 제목이 있다(U-32)" % (
            heads["mismatch_count"], heads["mismatch"][:3]))
    elif heads["mismatch_count"]:                              # 인용이 없고 숫자만 다르다 — 문서 글자는 맞고 셈 가정만 틀림(D3-①-N01)
        rec["warnings"].append("제목 개요 번호가 명세 차례와 다르다(%d곳) %s — 이 명세에는 {{절:}} 인용이 없어 저장했다. "
                               "작성기의 절 번호 셈(heading_numbers — text_checks 도 쓴다)이 한/글과 다르다(U-32)" % (
                                   heads["mismatch_count"], heads["mismatch"][:3]))
    if heads["unread"]:
        rec["warnings"].append("제목 %d곳의 개요 번호를 읽지 못했다(GetHeadingString, U-32) — 화면에서 제목 번호와 {{절:}} 인용을 "
                               "확인" % heads["unread"])
    stray = stray_newnums(nn0, written_newnums(s.last_hwpml, broot), items)
    if stray:
        problems.append("계획에 없는 '새 번호로 시작' 조판 %s — 쪽·각주 번호가 바뀌었을 수 있다(NumType, U-31)" % stray[:5])
        rec["check"]["captions"]["newnum_stray"] = stray[:10]
    if cwarn:
        kinds = {}
        for w in cwarn:
            kinds[w["what"]] = kinds.get(w["what"], 0) + 1
        rec["warnings"].append("캡션 %d곳이 계획과 다르다(%s) — 예: %s (P-049)" % (
            len({w["at"] for w in cwarn}), ", ".join("%s %d" % kv for kv in kinds.items()), cwarn[0]))
    if nfail:
        rec["warnings"].append("'새 번호로 시작'을 넣지 못한 곳 %d — %s — 캡션 번호는 쓴 뒤 대조로 봤다(P-050, U-31)" % (
            len(nfail), ", ".join("%s(%s %d: %s)" % (f["at"], f["kind"], f["n"], f["error"]) for f in nfail[:3])))
    if None in pages and inserted:                              # 새 번호를 넣지 않았으면 바뀔 까닭이 없다(D2-②-03)
        rec["warnings"].append("본문 첫 쪽 번호를 읽지 못했다 %s(KeyIndicator·CurrentPrintPage %s, U-31) — '새 번호로 시작' "
                               "%d개를 넣었으니 쪽 번호가 그대로인지 화면에서 확인(P-050)" % (pages, reads, inserted))
    if tolerated:
        rec["warnings"].append("표·그림 뒤 빈 문단 %d개(한/글이 만든 것)가 남았다 — 화면에서 빈 줄 확인" % len(tolerated))
    if sizes:
        rec["warnings"].append("글자 크기가 스타일과 다른 문단 %d곳 %s — 표 뒤 문단이면 '스타일 모양으로 덮어 쓸까요?'가 "
                               "'아니오'로 된 흔적" % (len(sizes), [x[0] for x in sizes[:5]]))
    if aligns:
        rec["warnings"].append("문단 정렬이 스타일과 다른 문단 %d곳 %s — 표 가운데 정렬이 다음 문단에 남았을 수 있다(P-041)" % (
            len(aligns), [x[0] for x in aligns[:5]]))
    if not clean:
        rec["warnings"].append("메시지 상자 자동 응답을 켜지 못했다 — 이미 있던 문단에 스타일을 다시 입히지 않았다(F-109 조치 "
                               "건너뜀). 쓰는 중 '스타일 모양으로 덮어 쓸까요?' 창이 뜨면 '예'를 누른다")
    if fitting and not fmt["total"]:
        rec["warnings"].append("템플릿 본문 구역의 쪽 설정(용지·여백)을 읽지 못해 칸 너비는 입히지 않았다(같은 너비로 나뉨)")
    if fmt["failed"]:
        by_kind = {}
        for f in fmt["failed"]:
            by_kind.setdefault(FORMAT_NAMES[f["kind"]], []).append(f["table"])
        rec["warnings"].append("표 서식을 입히지 못한 곳 %d — %s — 글자는 썼다. 첫 오류: %s%s" % (
            len(fmt["failed"]), ", ".join("%s: %s" % (k, sorted(set(v), key=_label_key)) for k, v in by_kind.items()),
            fmt["failed"][0]["error"],
            " · 칸 너비는 계획한 안 여백으로 셌다 — 안 여백을 못 바꾼 표는 칸 글자가 줄바꿈될 수 있다(검토 P-041 L4)"
            if any(f["kind"] == "margin" for f in fmt["failed"]) else ""))
    if fmt["off_at"]:
        rec["warnings"].append("표 셋에서 실패해 나머지 표에서 끈 서식: %s" % ", ".join(
            "%s(%s부터)" % (FORMAT_NAMES[k], v) for k, v in sorted(fmt["off_at"].items())))
    if fmt_bad:
        rec["warnings"].append("표 서식이 계획과 다른 칸 %d곳 (%s) — 예: %s" % (
            len(fmt_bad), sorted({b["table"] for b in fmt_bad}, key=_label_key), fmt_bad[0]))
    if front_fmt:
        rec["warnings"].append("앞부분(표지 등) 문단 %d곳의 스타일·글자 크기가 템플릿과 달라졌다 %s — 메시지 상자 '예'가 쓴 문단 "
                               "밖까지 바꿨을 수 있다(U-24). 화면에서 확인" % (len(front_fmt), [x[0] for x in front_fmt[:5]]))
    if restyled:
        rec["warnings"].append("스타일 정의 %d개가 템플릿과 달라졌다 %s — 메시지 상자 자동 응답('예')이 정의를 바꿨을 수 있다"
                               "(U-24). 화면에서 그 스타일을 쓰는 문단을 확인" % (len(restyled), restyled[:5]))
    left = {}
    for loc, kind, t in hp.iter_locations(m):
        for k in KEY_RX.findall(t):
            left.setdefault(k, []).append(loc)
    rec["keys_left"] = {k: v[:6] for k, v in sorted(left.items())}
    rec["needs"] = [{"text": x["text"], "after": _nearest_heading(items, n, styles)} for n, x in enumerate(items) if x.get("need")]
    if problems:
        rec["error"] = "; ".join(problems)
        return rec
    try:
        sv = s.save(out=out, force=force, protection=meta.get("protection", "preserve"))
    except api.PlaintextSaved as e:
        rec["save"] = e.rec
        rec["error"] = "DRM 미적용으로 저장됐다(%s) — 이 파일은 반출 금지: %s" % (e.rec.get("head"), meta["out"])
        return rec
    rec["save"] = {k: sv.get(k) for k in ("out", "head", "protected", "reopen", "source_unchanged")}
    if not sv.get("reopen") or sv.get("source_unchanged") is False:
        rec["error"] = "저장 확인 실패 %s" % rec["save"]
        return rec
    s.open(out)
    tm = s.model()
    md_path = out.parent / "md" / (out.stem + ".md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    lines = rm.head(tm, "write", ["명세: `%s`" % meta.get("_spec"), "템플릿: `%s`" % meta["template"],
                                  "생성: `tools/doc-writer/write_doc.py`"]) \
        + rm.summary(tm) + rm.outline_lines(tm) + rm.body_lines(tm) + rm.objects_lines(tm) + rm.notes_lines(tm)
    md_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    rec["md"] = str(md_path.relative_to(ROOT).as_posix())
    rec["pages"] = s.page_count()
    s.s.clear()
    rec["ok"] = True
    return rec


def _nearest_heading(items, n, styles=None):
    for x in reversed(items[:n]):
        if x["type"] == "para" and profiles.heading_level(x.get("style"), styles or STYLES):
            return x["text"]
    return "(첫 장)"


def write_report(rec, path, started):
    md = ["# 문서 작성 보고", "",
          "- 실행: %s · `tools/doc-writer/write_doc.py` · 명세 `%s`" % (started.isoformat(timespec="seconds"), rec.get("spec")),
          "- 템플릿 `%s` → 출력 `%s` · 결과 **%s**" % (rec.get("template"), rec.get("out"),
                                                  "OK" if rec.get("ok") else "FAIL: " + rm.esc(rec.get("error", ""))),
          "- 블록 %s · 표 %s · 그림 %s(그중 자리 표시 그림 %s) · 그림 자리 %s · 작성 필요 메모 %s · 캡션 %s(새 번호 %s) · 쪽 %s"
          " · 본문 첫 쪽 번호(쓰기 전, 쓴 뒤) %s"
          % tuple([(rec.get("plan") or {}).get(k, "-") for k in ("items", "tables", "pictures", "placeholders", "figures",
                                                                 "needs", "captions", "newnums")]
              + [rec.get("pages", "-"), ((rec.get("check") or {}).get("page") or {}).get("body_first", "-")]),
          ""]
    if rec.get("warnings"):
        md += ["## 경고", ""] + ["- %s" % rm.esc(w) for w in rec["warnings"]] + [""]
    md += ["## 추가 내용 필요", "", "### 값이 없는 키 (표지·머리말·꼬리말 등)", ""]
    md += ["- `%s` — %s" % (k, ", ".join("`%s`" % x for x in v)) for k, v in (rec.get("keys_left") or {}).items()] or ["- 없음"]
    md += ["", "### 본문 (작성 필요 메모·그림 자리, 파란 도움말 글자)", "", "| # | 절 | 내용 |", "|---|---|---|"]
    md += ["| %d | %s | %s |" % (i, rm.esc(x["after"]), rm.esc(x["text"])) for i, x in enumerate(rec.get("needs") or [], 1)]
    md += ["", "## 자세히 (JSON)", "", "```json", json.dumps(rec, ensure_ascii=False, indent=1, default=str), "```", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def _spec_head(text):
    """명세 글의 json 머리 → dict — out 이 저장소 안 상대 경로 .hwpx 일 때만(명세 오류 보고 자리, 저장소 밖에는 쓰지 않는다).
    못 읽으면 None."""
    try:
        m = re.search(r"```json[ \t]*\r?\n(.*?)\r?\n```", text, re.S)
        head = json.loads(m.group(1)) if m else None
    except ValueError:
        return None
    o = head.get("out") if isinstance(head, dict) else None
    return head if isinstance(o, str) and o.lower().endswith(".hwpx") and not outside(o) else None


def _spec_fail_report(text, spec, suffix, started, error):
    """한/글 앞에서 멈춘 명세 오류 — 그 보고 자리에 FAIL 보고를 쓴다(지난 실행 보고가 OK 로 남지 않게, 검토 D3-②-03). json 머리의
    out 이 저장소 안 .hwpx 일 때만(_spec_head), 깨진 글자(U+FFFD — UTF-8 이 아닌 명세)가 든 경로면 쓰지 않는다(D4-②-04).
    → 쓴 보고 경로 또는 None."""
    head = _spec_head(text)
    if not head or "\ufffd" in head["out"]:
        return None
    o = ROOT / head["out"]
    rec = {"spec": spec.as_posix(), "template": head.get("template"), "out": head["out"], "ok": False, "error": error}
    return write_report(rec, o.with_name(o.stem + suffix), started)


def main(argv=None):
    from _console import configure_console
    configure_console()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    ap = argparse.ArgumentParser(description="템플릿 + 내용 명세(.md) → 문서(.hwpx)")
    ap.add_argument("spec")
    ap.add_argument("--force", action="store_true", help="출력 파일이 있으면 교체")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--no-pictures", action="store_true", help="그림 파일을 넣지 않고 '그림 삽입 필요' 자리 표시만")
    args = ap.parse_args(argv)
    started = datetime.datetime.now()
    spec = Path(args.spec)
    suffix = (".nopic" if args.no_pictures else "") + ".write_report.md"
    try:
        raw = spec.read_bytes()
    except OSError as e:
        print("명세 오류: %s" % e)
        return 2
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as e:                             # 메모장 ANSI(CP949) 저장 등 — 끝 코드 2(검토 D4-②-04)
        err = "명세가 UTF-8 이 아니다(%s) — 명세는 UTF-8(BOM 가능)로 저장한다" % e
        print("명세 오류: %s" % err)
        try:                                                    # 보고 자리(out)는 메모장 ANSI 의 한국어 코드 페이지로 찾는다 —
            guess = raw.decode("cp949")                         # 한글 out 도 맞는 자리에(D5-②-02). 못 풀면 깨진 글자 그대로(쓰지 않음)
        except UnicodeDecodeError:
            guess = raw.decode("utf-8", "replace")
        rep = _spec_fail_report(guess, spec, suffix, started, "SpecError: %s" % err)
        if rep:
            print("보고: %s" % rep)
        return 2
    # 보고 자리를 알면 곧바로 'FAIL: 실행 중' 으로 — 명세 검사·계획에서 예상 밖 예외로 멈춰도 지난 OK 보고가 남지 않는다(D6-②-02)
    _spec_fail_report(text, spec, suffix, started, "실행 중 — 이 보고가 남았으면 작성기가 끝나지 않았다(콘솔의 오류를 본다)")
    try:
        meta, blocks = parse_spec(text)
        meta["_spec"] = spec.as_posix()
        plan(blocks, profiles.resolve_styles(meta.get("profile"), meta.get("styles"), ROOT), pictures=not args.no_pictures)   # 인용·그림 자리 표시 —
    except SpecError as e:                                      # 한/글을 띄우기 전에 명세 오류(P-051)
        print("명세 오류: %s" % e)
        rep = _spec_fail_report(text, spec, suffix, started, "SpecError: %s" % e)   # 지난 실행 보고가 OK 로 남지 않게(D3-②-03)
        if rep:
            print("보고: %s" % rep)
        return 2
    out = ROOT / meta["out"]
    report = out.with_name(out.stem + suffix)
    tc = text_checks(blocks)                                    # 한/글 오류로 끝나도 보고에 남는다(검토 D2-②-04)
    rec = {"spec": spec.as_posix(), "template": meta["template"], "out": meta["out"], "ok": False, "text_check": tc,
           "warnings": text_check_warnings(tc)}
    code = 1
    write_report(dict(rec, error="실행 중 — 이 보고가 남았으면 작성기가 끝나지 않았다(콘솔의 오류를 본다)"), report, started)   # D5-②-03
    try:
        with api.HwpxSession(timeout=args.timeout, log=print) as s:
            rec = write(s, meta, blocks, log=print, force=args.force, pictures=not args.no_pictures)
            rec["spec"] = spec.as_posix()
            code = 0 if rec["ok"] else 1
    except hs.HwpError as e:
        rec["error"] = "%s: %s" % (type(e).__name__, e)
        code = e.code
    print("%s — %s" % ("OK" if rec.get("ok") else "FAIL", rec.get("error", meta["out"])))
    print("보고: %s" % write_report(rec, report, started))
    return code


if __name__ == "__main__":
    sys.exit(main())
