# -*- coding: utf-8 -*-
"""office-drm-bridge 핵심 로직 (순수 파이썬 — Linux/Windows 모두에서 시험된다).

요청 JSON 을 검증하고, 고정된 연산을 기존 스크립트의 명령줄로 바꾸고, 결과를 기록한다.
백엔드는 파일 확장자로 고른다: doc-writer의 office-reader/writer · hwp.
임의 명령은 만들 수 없다.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import time

VERSION = "1.2"
ID_RE = re.compile(r"^\d{6}_\d{6}_[0-9a-f]{4}$")
CELL_RE = re.compile(r"^[A-Z]{1,3}[0-9]{1,7}$")
OFFICE_EXT = {".xlsx", ".xlsm", ".xlsb", ".xls", ".docx", ".docm", ".doc",
              ".pptx", ".pptm", ".ppt"}
OUT_DIRS = ("output_docs", "review_docs")          # protect/replace/fill 출력 허용 위치
BLOCKED_SRC_DIRS = (".git", "bridge")             # 입력으로 쓸 수 없는 위치
MAX_REQ_BYTES = 1000000
MAX_BODY_CHARS = 1000000
MAX_QUEUE = 20
TIMEOUT_SEC = 300
TOP_KEYS = {"id", "op", "path", "args", "reason", "plan_ref", "created"}
OFFICE_OPS = ("read", "search", "dump", "protect", "replace", "fill")
HWPX_OPS = ("inspect", "outline", "tables", "fields", "search", "verify", "fill", "replace", "insert", "figpack", "images")
OPS = ("read", "search", "dump", "protect", "replace", "fill", "purge",
       "inspect", "outline", "tables", "fields", "verify", "insert", "figpack", "images")       # 모든 백엔드 연산의 합집합
HWPX_EXT = {".hwpx", ".hwp"}
HWPX_OUT_EXT = {".hwpx"}                 # 한/글 쓰기 결과는 HWPX 로만 저장된다
HWPX_TIMEOUT_SEC = 900                   # 요청 전체. 한/글 COM 호출 하나는 HWPX_COM_TIMEOUT 에서 먼저 끊긴다
HWPX_COM_TIMEOUT = 120
SEARCH_MAX_AGE_SEC = 24 * 3600           # replace 가 근거로 삼는 search 의 최대 나이
IDENT_RE = re.compile(r"^[A-Za-z0-9_.]{1,64}$")
# insert: 현재 프로젝트의 끼워 넣기 도구만 실행한다.
INSERT_SCRIPT = ("tools", "doc-writer", "insert_doc.py")
FIGPACK_SCRIPT = ("tools", "doc-writer", "figure_pack.py")   # figpack(P-052): 출처 그림을 그림 하나짜리 보호 문서로 나눔
TOOL_OPS = ("insert", "figpack")                             # 작업 트리 도구를 부르는 연산 — 지문(insert_pin.json) 대조
ONLY_RE = re.compile(r"^\d{1,3}(,\d{1,3}){0,199}$")
# 블록 명세의 그림 줄 — 도구(insert_doc.parse_blocks)가 받는 꼴보다 좁게: 이 꼴이 아닌 '](hwpx:' 줄·'![' 줄은 거절(검토 D1-06)
INSERT_FIG_LINE = re.compile(r'^!\[[^\]]*\]\(hwpx:([^)"#\s][^)"#]*)#\d{1,3}(?:[ \t]+"\d+(?:\.\d+)?x\d+(?:\.\d+)?")?\)$')
SPEC_EXT = {".md"}
# insert 도구 코드는 작업 트리(tools/)에 있어 원격으로 고칠 수 있다 — 배포 bat 가 적은 지문과 같을 때만 실행한다(검토 D1-01)
INSERT_PIN = os.path.join(os.path.dirname(os.path.abspath(globals().get("__file__", "."))), "..", "insert_pin.json")
INSERT_PIN_DIRS = (("tools", "doc-writer"), ("tools", "hwpx-drm", "scripts"))
# insert 표준출력은 결과 줄·보고 경로만 — 실패 사유(문서 글자가 들어갈 수 있다)는 quarantine 의 보고에서 읽는다
STATUS_PREFIX_INSERT = ("OK —", "보고:", "경고:")

_CTRL_LINE = re.compile(r"[\x00-\x1f\x7f]")
_CTRL_BODY = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
STATUS_PREFIX = ("FAILED", "중단", "NOT FOUND", "DONE", "평문 덤프", "보호 확인",
                 "저장 완료", "output :", "mode   :")
# hwpx_drm.py 가 표준출력에 내는 상태 줄의 시작 (건수·위치 ID·사용자가 준 키만 담긴다. 본문은 .md 로만 나간다)
STATUS_PREFIX_HWPX = ("구역", "개요 문단", "표 ", "입력 필드", "'", "채움", "저장 ", "바뀐 것이",
                      "선두 ", "중단", "경고:", "만든 파일:", "그림 ")
HWPX_EXIT = {0: "성공",
             1: "검증 실패(없는 필드·남은 자리표시·표 없음·저장 실패)",
             2: "사전조건 위반(파일 없음·한/글 실행 중·출력 존재·값 파일 오류)",
             3: "저장 결과가 평문(DRM 미적용)",
             4: "열기 실패(권한 문제 — 우회하지 않고 보고한다)",
             5: "한/글 호출 시간 초과(이 실행의 Hwp.exe 만 종료됨)",
             6: "pywin32·COM 생성 실패"}

# op -> {인자: (종류, 한도…)}   종류: str(최대길이) int(최소,최대) bool cell out map csv
ARGS = {
    "read":    {"sheet": ("str", 64), "preview": ("int", 0, 200), "max_rows": ("int", 1, 50000),
                "max_cols": ("int", 1, 1000), "fill_merged": ("bool",)},
    "search":  {"pattern": ("str", 200, True), "sheet": ("str", 64), "max_rows": ("int", 1, 50000),
                "max_cols": ("int", 1, 1000), "fill_merged": ("bool",)},
    "dump":    {"sheet": ("str", 64), "max_rows": ("int", 1, 50000), "max_cols": ("int", 1, 1000),
                "fill_merged": ("bool",)},
    "protect": {"out": ("out",)},
    "replace": {"map": ("map", True), "out": ("out",)},
    "fill":    {"data": ("csv", True), "sheet": ("str", 64), "cell": ("cell",),
                "no_header": ("bool",), "out": ("out",)},
    "purge":   {"target_id": ("id", True)},
}


# 한/글 연산 -> {인자: (종류, 한도…)}. 같은 이름(search/fill/replace)이라도 오피스와 인자가 다르다.
HWPX_ARGS = {
    "inspect": {},
    "outline": {},
    "fields":  {},
    "verify":  {},
    "tables":  {"table": ("ident",)},
    "search":  {"pattern": ("str", 200, True)},
    "fill":    {"map": ("map", True), "out": ("out",)},
    # replace 는 메모·머리말·누름틀 값까지 바꾸므로 같은 파일의 성공한 search 가 먼저 있어야 한다
    "replace": {"map": ("map", True), "out": ("out",), "search_id": ("id", True)},
    # insert: 대상(path)의 제목 before 앞에 블록 명세(spec, 저장소 안 output_docs·review_docs 의 .md)를 끼워 새 파일(out)로
    "insert":  {"spec": ("str", 400, True), "before": ("str", 200, True), "out": ("out", True)},
    # figpack: 출처(path)의 그림 문단을 out_dir(output_docs·review_docs 아래 새 폴더)에 all.hwpx·figKK.hwpx 로(보호 문서)
    "figpack": {"out_dir": ("out", True), "only": ("str", 800)},
    # images: 문서에 포함된 그림을 out_dir(output_docs·review_docs 아래 새 폴더)에 평문 파일로
    "images":  {"out_dir": ("out", True)},
}

for _op in ("protect", "replace", "fill"):
    ARGS[_op]["protection"] = ("choice", "preserve", "required")
for _op in ("verify", "fill", "replace", "insert", "figpack"):
    HWPX_ARGS[_op]["protection"] = ("choice", "preserve", "required")


class Reject(Exception):
    pass


def _norm(p):
    return os.path.normcase(p)


def resolve_inside(root, p):
    """p 를 실경로로 풀어 root 안인지 검사한다 (.., 심볼릭 링크, 드라이브 변형 포함)."""
    if not isinstance(p, str) or not p or len(p) > 400 or _CTRL_LINE.search(p):
        raise Reject("경로 형식이 올바르지 않다")
    cand = p if os.path.isabs(p) else os.path.join(root, p)
    real = os.path.realpath(cand)
    r = os.path.realpath(root)
    try:
        inside = os.path.commonpath([_norm(real), _norm(r)]) == _norm(r)
    except ValueError:
        inside = False
    if not inside:
        raise Reject("저장소 밖 경로는 쓸 수 없다")
    return real


def _top_dir(root, real):
    rel = os.path.relpath(real, os.path.realpath(root))
    return _norm(rel.replace("\\", "/").split("/")[0])


def _check_str(name, v, maxlen, body=False):
    if not isinstance(v, str) or not v:
        raise Reject("%s: 비어 있지 않은 문자열이어야 한다" % name)
    if len(v) > maxlen:
        raise Reject("%s: 너무 길다(최대 %d)" % (name, maxlen))
    if (_CTRL_BODY if body else _CTRL_LINE).search(v):
        raise Reject("%s: 제어문자가 들어 있다" % name)


def _resolve_out(root, out, src_real, exts=None, default_ext=None):
    exts = exts or OFFICE_EXT
    stem, ext = os.path.splitext(os.path.basename(src_real))
    if out is None:
        out = "output_docs/%s_out%s" % (stem, default_ext or ext)
    real = resolve_inside(root, out)
    if os.path.splitext(real)[1].lower() not in exts:
        raise Reject("out: 허용되지 않은 확장자")
    if _top_dir(root, real) not in [_norm(d) for d in OUT_DIRS]:
        raise Reject("out: %s 아래에만 쓸 수 있다" % ", ".join(OUT_DIRS))
    if not os.path.isdir(os.path.dirname(real)):
        raise Reject("out: 폴더가 없다")
    if _norm(real) == _norm(src_real):
        raise Reject("out: 원본과 같다 (덮어쓰기는 지원하지 않는다)")
    if os.path.lexists(real):
        raise Reject("out: 이미 있다 (덮어쓰기는 지원하지 않는다)")
    return real


def backend_for(req, op):
    """연산과 확장자로 백엔드를 고른다. purge 는 파일이 없어 None."""
    if op == "purge":
        return None
    p = req.get("path")
    ext = os.path.splitext(p)[1].lower() if isinstance(p, str) else ""
    if ext in HWPX_EXT:
        if op not in HWPX_OPS:
            raise Reject("연산 %s 는 한/글 문서에 쓸 수 없다" % op)
        return "hwpx"
    if ext in OFFICE_EXT:
        if op not in OFFICE_OPS:
            raise Reject("연산 %s 는 오피스 문서에 쓸 수 없다" % op)
        return "office"
    # 확장자를 모르면 연산이 속한 쪽으로 보내 기존 오류(경로·확장자)가 나게 한다
    return "office" if op in OFFICE_OPS else "hwpx"


def split_patterns(text):
    """검색어 글 → 검색어 목록. 쉼표가 구분자, 검색어 안의 쉼표는 '\\,'('\\\\' = 역슬래시 하나), 그 밖의 역슬래시는 그대로,
    앞뒤 빈칸은 지우고 빈 검색어는 뺀다. hwpx-drm 의 hwpx_drm.split_patterns 와 같은 규칙(P-052 — 시험 TestRealCli 가 견준다)."""
    out, cur, i = [], [], 0
    while i < len(text):
        c = text[i]
        if c == "\\" and i + 1 < len(text) and text[i + 1] in ",\\":
            cur.append(text[i + 1])
            i += 2
            continue
        if c == ",":
            out.append("".join(cur))
            cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return [p for p in (x.strip() for x in out) if p]


def check_search_precondition(root, search_id, mapping, src_real):
    """hwpx replace 의 선행조건: 같은 파일(내용 해시 동일)에 대해, 이 키들을 모두 찾은 성공한 search 가 있어야 한다.
    AllReplace 가 메모·머리말·각주·누름틀 값까지 바꾸므로, 어디가 바뀔지 위치를 본 뒤에만 허용한다."""
    b = os.path.join(root, "bridge")
    try:
        with open(os.path.join(b, "done", search_id + ".json"), encoding="utf-8") as f:
            sreq = json.load(f)
        outp = os.path.join(b, "outbox", search_id + ".json")
        with open(outp, encoding="utf-8") as f:
            sres = json.load(f)
        age = time.time() - os.path.getmtime(outp)
    except (OSError, ValueError):
        raise Reject("search_id: 해당 search 요청·결과가 없다 — 같은 파일에 search 를 먼저 실행한다")
    if not isinstance(sreq, dict) or not isinstance(sres, dict) or sreq.get("op") != "search" \
            or sres.get("op") != "search" or sres.get("status") != "ok":
        raise Reject("search_id: 성공한 search 요청이 아니다")
    try:
        same = _norm(resolve_inside(root, sreq.get("path"))) == _norm(src_real)
    except Reject:
        same = False
    if not same:
        raise Reject("search_id: 다른 파일에 대한 search 다")
    if age > SEARCH_MAX_AGE_SEC:
        raise Reject("search_id: 24시간이 지난 search 다 — 다시 실행한다")
    a = sreq.get("args")
    pats = set(split_patterns(str(a.get("pattern", "") if isinstance(a, dict) else "")))
    missing = [k for k in mapping if k not in pats]
    if missing:
        raise Reject("search_id: search 하지 않은 키가 있다: %s" % ", ".join(missing[:5]))
    if sres.get("src_sha256") != sha256_of(src_real):
        raise Reject("search_id: search 이후 파일이 바뀌었다 — search 를 다시 실행한다")


def insert_fingerprint(root):
    """작성기와 HWP backend 코드 폴더(*.py)의 배포 지문."""
    return {"/".join(d): tree_sha(os.path.join(root, *d)) for d in INSERT_PIN_DIRS}


def check_insert(root, spec):
    """insert 선행조건 → (명세 실경로, 도구 실경로, 명세 글). 명세는 저장소 안 output_docs·review_docs 의 .md(UTF-8), 그 안의
    그림 줄은 좁은 꼴(INSERT_FIG_LINE)이고 출처는 저장소 안·bridge/·.git 밖의 .hwpx·.hwp 파일이어야 한다. 도구는 이 저장소의
    tools/doc-writer 이고, 도구 코드 지문이 배포 때 적은 값(insert_pin.json)과 같아야 한다."""
    real = resolve_inside(root, spec)
    if os.path.splitext(real)[1].lower() not in SPEC_EXT:
        raise Reject("spec: .md 만 쓸 수 있다")
    if _top_dir(root, real) not in [_norm(d) for d in OUT_DIRS]:
        raise Reject("spec: %s 아래 명세만 쓸 수 있다" % ", ".join(OUT_DIRS))
    if not os.path.isfile(real):
        raise Reject("spec: 파일이 없다")
    if os.path.getsize(real) > MAX_REQ_BYTES:
        raise Reject("spec: 너무 크다")
    try:
        with open(real, "rb") as f:
            text = f.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        raise Reject("spec: UTF-8 로 읽지 못했다")
    body = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    srcs = []
    for ln in body.splitlines():
        ln = ln.rstrip()
        if "](hwpx:" in ln or ln.lstrip().startswith("!["):
            g = INSERT_FIG_LINE.match(ln)
            if not g:
                raise Reject("spec 그림 줄 꼴이 틀렸다(줄 처음 '![캡션](hwpx:경로#번호 \"가로x세로\")', 경로에 '#' 없음)")
            srcs.append(g.group(1))
    for src in srcs:
        try:
            fig = resolve_inside(root, src.strip())
        except Reject:
            raise Reject("spec 그림 출처: 저장소 밖 경로는 쓸 수 없다")
        if os.path.splitext(fig)[1].lower() not in HWPX_EXT:
            raise Reject("spec 그림 출처: 허용되지 않은 확장자")
        if _top_dir(root, fig) in [_norm(d) for d in BLOCKED_SRC_DIRS]:
            raise Reject("spec 그림 출처: 이 위치의 파일은 입력으로 쓸 수 없다")
        if not os.path.isfile(fig):
            raise Reject("spec 그림 출처: 파일이 없다")
    return real, check_tool(root, INSERT_SCRIPT, "insert"), text


def check_tool(root, script, op):
    """작업 트리 도구 → 실경로. 그 도구가 이 저장소에 있고, 도구 코드 지문이 배포 때 적은 값(insert_pin.json)과 같아야 한다
    (검토 D1-01 — 원격으로 고친 코드를 워커가 실행하지 않게)."""
    tool = os.path.realpath(os.path.join(root, *script))
    if not os.path.isfile(tool):
        raise Reject("%s: 이 저장소에 %s 가 없다" % (op, "/".join(script)))
    try:
        with open(INSERT_PIN, encoding="utf-8") as f:
            pin = json.load(f)
    except (OSError, ValueError):
        raise Reject("%s: 배포 지문(insert_pin.json)이 없다 — 현재 도구 검토 후 지문을 기록한다" % op)
    if not isinstance(pin, dict) or pin.get("dirs") != insert_fingerprint(root):
        raise Reject("%s: 도구 코드가 배포 때와 다르다(insert_pin.json 지문) — 변경 검토 후 지문을 갱신한다" % op)
    return tool


def check_out_dir(root, out_dir):
    """figpack 출력 폴더 → 실경로: 저장소 안 output_docs·review_docs 아래, 아직 없는 새 폴더, 부모 폴더는 있음."""
    real = resolve_inside(root, out_dir)
    if _top_dir(root, real) not in [_norm(d) for d in OUT_DIRS] or _norm(real) in [
            _norm(os.path.join(os.path.realpath(root), d)) for d in OUT_DIRS]:
        raise Reject("out_dir: %s 아래 새 폴더만 쓸 수 있다" % ", ".join(OUT_DIRS))
    if os.path.lexists(real):
        raise Reject("out_dir: 이미 있다 (덮어쓰기는 지원하지 않는다)")
    if not os.path.isdir(os.path.dirname(real)):
        raise Reject("out_dir: 부모 폴더가 없다")
    return real


def validate_request(raw, name_id, root):
    """(req, plan) 반환. 문제가 있으면 Reject. raw 는 bytes."""
    if len(raw) > MAX_REQ_BYTES:
        raise Reject("요청이 너무 크다")
    try:
        req = json.loads(raw.decode("utf-8"))
    except Exception:
        raise Reject("요청이 UTF-8 JSON 이 아니다")
    if not isinstance(req, dict):
        raise Reject("요청은 JSON 객체여야 한다")
    extra = set(req) - TOP_KEYS
    if extra:
        raise Reject("알 수 없는 키: %s" % ", ".join(sorted(extra)))
    rid = req.get("id")
    if not isinstance(rid, str) or not ID_RE.match(rid) or rid != name_id:
        raise Reject("id 가 형식에 맞지 않거나 파일명과 다르다")
    op = req.get("op")
    if op not in OPS:
        raise Reject("알 수 없는 연산: %r" % (op,))
    backend = backend_for(req, op)
    _check_str("reason", req.get("reason"), 200)
    _check_str("plan_ref", req.get("plan_ref"), 300)
    args = req.get("args", {})
    if not isinstance(args, dict):
        raise Reject("args 는 객체여야 한다")
    spec = (HWPX_ARGS if backend == "hwpx" else ARGS)[op]
    unknown = set(args) - set(spec)
    if unknown:
        raise Reject("%s 에서 허용하지 않는 인자: %s" % (op, ", ".join(sorted(unknown))))
    clean = {}
    for name, s in spec.items():
        kind = s[0]
        required = s[-1] is True
        if name not in args:
            if required:
                raise Reject("%s: 필수 인자" % name)
            continue
        v = args[name]
        if kind == "str":
            _check_str(name, v, s[1])
        elif kind == "int":
            if isinstance(v, bool) or not isinstance(v, int) or not (s[1] <= v <= s[2]):
                raise Reject("%s: %d~%d 정수여야 한다" % (name, s[1], s[2]))
        elif kind == "bool":
            if not isinstance(v, bool):
                raise Reject("%s: true/false 여야 한다" % name)
        elif kind == "cell":
            if not isinstance(v, str) or not CELL_RE.match(v):
                raise Reject("cell: A1 형식이어야 한다")
        elif kind == "id":
            if not isinstance(v, str) or not ID_RE.match(v):
                raise Reject("%s: 요청 id 형식이어야 한다" % name)
        elif kind == "ident":
            if not isinstance(v, str) or not IDENT_RE.match(v):
                raise Reject("%s: 영문·숫자·점·밑줄 64자 이하여야 한다" % name)
        elif kind == "out":
            _check_str(name, v, 400)
        elif kind == "choice":
            if v not in s[1:]:
                raise Reject("%s: %s 중 하나여야 한다" % (name, ", ".join(s[1:])))
        elif kind == "map":
            if not isinstance(v, dict) or not v:
                raise Reject("map: 비어 있지 않은 객체여야 한다")
            for k, val in v.items():
                _check_str("map 키", k, 200, body=True)
                if not isinstance(val, str) or len(val) > 20000 or _CTRL_BODY.search(val):
                    raise Reject("map 값이 올바르지 않다")
            if len(json.dumps(v, ensure_ascii=False)) > MAX_BODY_CHARS:
                raise Reject("map 이 너무 크다")
        elif kind == "csv":
            _check_str(name, v, MAX_BODY_CHARS, body=True)
        clean[name] = v

    plan = {"op": op, "id": rid, "args": clean, "backend": backend}
    if op == "purge":
        if "path" in req:
            raise Reject("purge 에는 path 가 없다")
        return req, plan
    src = resolve_inside(root, req.get("path"))
    if os.path.splitext(src)[1].lower() not in (HWPX_EXT if backend == "hwpx" else OFFICE_EXT):
        raise Reject("path: 허용되지 않은 확장자")
    if _top_dir(root, src) in [_norm(d) for d in BLOCKED_SRC_DIRS]:
        raise Reject("path: 이 위치의 파일은 입력으로 쓸 수 없다")
    if not os.path.isfile(src):
        raise Reject("path: 파일이 없다")
    plan["src"] = src
    plan["protection_required"] = op == "protect" or clean.get("protection") == "required" or drm_signature(src) is True
    if backend == "hwpx":
        if op in ("fill", "replace", "insert"):
            plan["out"] = _resolve_out(root, clean.get("out"), src, HWPX_OUT_EXT, ".hwpx")
        if op == "insert":
            plan["spec"], plan["script"], plan["spec_text"] = check_insert(root, clean["spec"])
            body = re.sub(r"<!--.*?-->", "", plan["spec_text"], flags=re.S)
            for line in body.splitlines():
                match = INSERT_FIG_LINE.match(line.rstrip())
                if match and drm_signature(resolve_inside(root, match.group(1).strip())) is True:
                    plan["protection_required"] = True
        if op == "images":
            plan["out_dir"] = check_out_dir(root, clean["out_dir"])
        if op == "figpack":
            if "only" in clean and not ONLY_RE.match(clean["only"]):
                raise Reject("only: 쉼표로 구분한 그림 번호(빈칸 없이)여야 한다")
            plan["out_dir"] = check_out_dir(root, clean["out_dir"])
            plan["script"] = check_tool(root, FIGPACK_SCRIPT, "figpack")
        if op == "replace":
            check_search_precondition(root, clean["search_id"], clean["map"], src)
    elif op in ("protect", "replace", "fill"):
        plan["out"] = _resolve_out(root, clean.get("out"), src)
    return req, plan


def _qdir(root):
    return os.path.join(root, "bridge", "quarantine")


def _build_hwpx(plan, root, python, scripts):
    """한/글: hwpx_drm.py <명령> <파일> … 읽기 결과 .md 는 요청별 폴더(<id>_md)로 받는다
    (스크립트가 <파일이름>.<명령>.md 로 쓰므로 요청끼리 이름이 부딪히지 않게)."""
    op, rid, a = plan["op"], plan["id"], plan["args"]
    policy = "required" if plan.get("protection_required") else "preserve"
    q = _qdir(root)
    work = os.path.join(root, "bridge", "work")
    outbox = os.path.join(root, "bridge", "outbox")
    if op == "figpack":                                      # 보고(캡션 글이 들어 있다)는 quarantine 으로
        rep = os.path.join(q, "%s_pack_report.md" % rid)
        cmd = [python, plan["script"], plan["src"], "--out-dir=" + plan["out_dir"], "--report=" + rep,
               "--timeout=%d" % HWPX_COM_TIMEOUT, "--protection=" + policy] + (["--only=" + a["only"]] if "only" in a else [])
        return {"cmd": cmd, "pre": [], "cleanup": [], "outputs": [rep], "outputs_dirs": [plan["out_dir"]]}
    if op == "insert":                                       # 보고(넣은 글자가 들어 있다)는 quarantine 으로
        rep = os.path.join(q, "%s_insert_report.md" % rid)
        spec = os.path.join(work, "%s_spec.md" % rid)       # 검사한 글 그대로를 넘긴다(검사 뒤 명세가 바뀌어도 — D1-06)
        cmd = [python, plan["script"], plan["src"], "--spec=" + spec, "--before=" + a["before"],
               "--out=" + plan["out"], "--report=" + rep, "--timeout=%d" % HWPX_COM_TIMEOUT, "--protection=" + policy]
        return {"cmd": cmd, "pre": [(spec, plan["spec_text"])], "cleanup": [spec], "outputs": [rep, plan["out"]],
                "outputs_dirs": []}
    cmd = [python, scripts["hwpx"], op, plan["src"], "--timeout=%d" % HWPX_COM_TIMEOUT]
    if op in ("verify", "fill", "replace"):
        cmd.append("--protection=" + policy)
    pre, cleanup, outputs, dirs = [], [], [], []
    if op in ("fill", "replace", "images"):
        log = os.path.join(outbox, "%s.log.md" % rid)        # 건수·키 이름·파일 이름만 (본문 없음)
    else:
        log = os.path.join(q, "%s_hwpxlog.md" % rid)
    cmd.append("--log=" + log)
    outputs.append(log)
    if op in ("inspect", "outline", "tables", "fields", "search"):
        md_dir = os.path.join(q, "%s_md" % rid)
        cmd.append("--md-dir=" + md_dir)
        dirs.append(md_dir)
        if op == "search":
            cmd.append("--pattern=" + a["pattern"])
        if op == "tables" and "table" in a:
            cmd.append("--table=" + a["table"])
    elif op == "images":                                     # 평문 그림은 out_dir 에(D-062) — 목록 images.md 에 캡션 글
        cmd.append("--out-dir=" + plan["out_dir"])
        dirs.append(plan["out_dir"])
    elif op in ("fill", "replace"):
        m = os.path.join(work, "%s_map.json" % rid)
        pre.append((m, json.dumps(a["map"], ensure_ascii=False)))
        cleanup.append(m)
        cmd += ["--map=" + m, "--out=" + plan["out"]]
        outputs.append(plan["out"])
    return {"cmd": cmd, "pre": pre, "cleanup": cleanup, "outputs": outputs, "outputs_dirs": dirs}


def build_command(plan, root, python, scripts):
    """plan -> {'cmd':[...], 'pre':[(path,text)], 'cleanup':[path], 'outputs':[path]}"""
    if plan.get("backend") == "hwpx":
        return _build_hwpx(plan, root, python, scripts)
    op, rid, a = plan["op"], plan["id"], plan["args"]
    q = _qdir(root)
    work = os.path.join(root, "bridge", "work")
    outbox = os.path.join(root, "bridge", "outbox")
    cmd, pre, cleanup, outputs = [python], [], [], []
    if op in ("read", "search", "dump"):
        # dump 의 --log 와 --dump 는 서로 다른 파일이어야 한다(같으면 두 핸들이 한 파일을 덮어써 깨진다)
        log = os.path.join(q, "%s_%s.md" % (rid, "dumplog" if op == "dump" else op))
        cmd += [scripts["read"], plan["src"], "--log=" + log]
        outputs.append(log)
        if op == "search":
            cmd.append("--pattern=" + a["pattern"])
        if op == "read" and "preview" in a:
            cmd.append("--preview=%d" % a["preview"])
        for key, opt in (("max_rows", "--max-rows"), ("max_cols", "--max-cols")):
            if key in a:
                cmd.append("%s=%d" % (opt, a[key]))
        if "sheet" in a:
            cmd.append("--sheet=" + a["sheet"])
        if a.get("fill_merged"):
            cmd.append("--fill-merged")
        if op == "dump":
            dump = os.path.join(q, "%s_dump.md" % rid)
            cmd.append("--dump=" + dump)
            outputs.append(dump)
    elif op in ("protect", "replace", "fill"):
        log = os.path.join(outbox, "%s.log.md" % rid)
        cmd += [scripts["write"], plan["src"], "--mode=" + op, "--out=" + plan["out"], "--log=" + log]
        cmd.append("--protection=" + ("required" if plan.get("protection_required") else "preserve"))
        outputs += [plan["out"], log]
        if op == "replace":
            m = os.path.join(work, "%s_map.json" % rid)
            pre.append((m, json.dumps(a["map"], ensure_ascii=False)))
            cleanup.append(m)
            cmd.append("--map=" + m)
        if op == "fill":
            d = os.path.join(work, "%s_data.csv" % rid)
            pre.append((d, a["data"]))
            cleanup.append(d)
            cmd.append("--data=" + d)
            if "sheet" in a:
                cmd.append("--sheet=" + a["sheet"])
            if "cell" in a:
                cmd.append("--cell=" + a["cell"])
            if a.get("no_header"):
                cmd.append("--no-header")
    return {"cmd": cmd, "pre": pre, "cleanup": cleanup, "outputs": outputs}


def default_runner(cmd, timeout):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    try:
        p = subprocess.run(cmd, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return -9, "FAILED: 시간 초과(%d초) — 남은 EXCEL/WINWORD/POWERPNT/Hwp 프로세스를 확인한다" % timeout
    return p.returncode, p.stdout.decode("utf-8", "replace")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def drm_signature(path):
    try:
        with open(path, "rb") as f:
            return f.read(11) == b"BMS DocuRay"
    except OSError:
        return None


def known_document_signature(path, hwpx=False):
    """Accept only a protected container or a supported plain document container."""
    try:
        with open(path, "rb") as stream:
            head = stream.read(16)
        return head.startswith((b"BMS DocuRay", b"PK\x03\x04")) or (
            not hwpx and head.startswith(b"\xd0\xcf\x11\xe0"))
    except OSError:
        return False


def _rel(root, p):
    return os.path.relpath(p, os.path.realpath(root)).replace("\\", "/")


def safe_tail(text):
    """문서 내용이 outbox JSON 으로 새지 않게 상태 줄만 남긴다."""
    keep = [ln.strip() for ln in text.splitlines() if ln.strip().startswith(STATUS_PREFIX)]
    return "\n".join(keep[-12:])


def tree_sha(d):
    """백엔드 스크립트 폴더(*.py)의 지문 — 배포 사본이 실측 때와 달라졌는지 감사 기록으로 본다."""
    try:
        names = sorted(n for n in os.listdir(d) if n.endswith(".py"))
    except OSError:
        return None
    h = hashlib.sha256()
    for n in names:
        h.update(n.encode("utf-8") + b"\0")
        with open(os.path.join(d, n), "rb") as f:
            h.update(f.read())
    return h.hexdigest()[:16]


def safe_tail_hwpx(text, op=None):
    if op in TOOL_OPS:
        keep = [ln.strip()[:300] if ln.strip().startswith(STATUS_PREFIX_INSERT) else "FAIL — 사유는 quarantine 의 보고"
                for ln in text.splitlines() if ln.strip().startswith(STATUS_PREFIX_INSERT + ("FAIL",))]
        return "\n".join(keep[-20:])
    keep = [ln.strip()[:300] for ln in text.splitlines() if ln.strip().startswith(STATUS_PREFIX_HWPX)]
    return "\n".join(keep[-20:])


def _remove(p):
    if os.path.isdir(p) and not os.path.islink(p):
        shutil.rmtree(p)
    else:
        os.remove(p)


def _latest_mtime(p):
    t = os.path.getmtime(p)
    if os.path.isdir(p):
        for n in os.listdir(p):
            t = max(t, os.path.getmtime(os.path.join(p, n)))
    return t


def purge_target(root, target):
    removed = []
    for d in (_qdir(root), os.path.join(root, "bridge", "work")):
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if n.startswith(target + "_") and (os.path.isfile(p) or os.path.isdir(p)) and not os.path.islink(p):
                _remove(p)
                removed.append(_rel(root, p))
    return removed


def purge_old(root, hours, now=None):
    now = now or time.time()
    removed = []
    for d in (_qdir(root), os.path.join(root, "bridge", "work")):
        if not os.path.isdir(d):
            continue
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if (os.path.isfile(p) or os.path.isdir(p)) and not os.path.islink(p) \
                    and now - _latest_mtime(p) > hours * 3600:
                _remove(p)
                removed.append(_rel(root, p))
    return removed


def ensure_dirs(root):
    for d in ("inbox", "outbox", "quarantine", "work", "done"):
        os.makedirs(os.path.join(root, "bridge", d), exist_ok=True)


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def audit(root, rec):
    rec = dict(rec, ts=time.strftime("%Y-%m-%d %H:%M:%S"))
    with open(os.path.join(root, "bridge", "audit.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def handle_request(root, raw, name_id, python, scripts, runner=default_runner, confirm=None):
    """요청 1건을 처리해 결과 dict 를 돌려준다. 예외를 밖으로 내지 않는다."""
    res = {"id": name_id, "status": "rejected", "worker_version": VERSION,
           "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    req = None
    try:
        req, plan = validate_request(raw, name_id, root)
        res["op"] = plan["op"]
        res["path"] = req.get("path")
        if confirm is not None and not confirm(req, plan):
            res["status"] = "denied"
            res["notes"] = ["사용자가 워커 콘솔에서 거부했다"]
            return res
        if plan["op"] == "purge":
            res["removed"] = purge_target(root, plan["args"]["target_id"])
            res["outputs"] = []
            res["status"] = "ok"
            return res
        hwpx = plan.get("backend") == "hwpx"
        res["protection_required"] = plan.get("protection_required", False)
        if hwpx:
            res["src_sha256"] = sha256_of(plan["src"])            # replace 선행조건·변경 감지용
            res["backend_sha256"] = tree_sha(os.path.dirname(plan["script"] if plan["op"] in TOOL_OPS else scripts["hwpx"]))
            if plan["op"] == "insert":
                res["spec_sha256"] = hashlib.sha256(plan["spec_text"].encode("utf-8")).hexdigest()
        built = build_command(plan, root, python, scripts)
        for p, text in built["pre"]:
            with open(p, "w", encoding="utf-8", newline="") as f:
                f.write(text)
        try:
            rc, out = runner(built["cmd"], HWPX_TIMEOUT_SEC if hwpx else TIMEOUT_SEC)
        finally:
            for p in built["cleanup"]:
                if os.path.exists(p):
                    os.remove(p)
        res["exit_code"] = rc
        res["stdout_tail"] = safe_tail_hwpx(out, plan["op"]) if hwpx else safe_tail(out)
        moved = False
        if hwpx:
            res["exit_meaning"] = HWPX_EXIT.get(
                rc, "브리지 시간 초과 — 한/글(Hwp.exe)이 남았는지 확인한다" if rc == -9 else "알 수 없는 종료코드")
            if plan["op"] in ("fill", "replace", "insert") and os.path.isfile(plan["out"]):
                res["drm_signature"] = drm_signature(plan["out"])
                if plan["protection_required"] and res["drm_signature"] is not True:
                    moved = os.path.join(_qdir(root), "%s_plaintext_out.hwpx" % name_id)
                elif rc != 0 or not known_document_signature(plan["out"], hwpx=True):
                    moved = os.path.join(_qdir(root), "%s_unverified_out.hwpx" % name_id)
                if moved:
                    os.replace(plan["out"], moved)
            if plan["op"] == "figpack" and os.path.isdir(plan["out_dir"]):
                bad = []                                         # 평문·확인 안 된 꾸러미 파일은 output 에 두지 않는다
                for n in sorted(os.listdir(plan["out_dir"])):
                    p = os.path.join(plan["out_dir"], n)
                    if os.path.isfile(p) and ((plan["protection_required"] and drm_signature(p) is not True)
                                              or not known_document_signature(p, hwpx=True) or n.endswith(".unverified.hwpx")):
                        bad.append(p)
                res["drm_signature"] = all(drm_signature(os.path.join(plan["out_dir"], n)) is True
                                           for n in os.listdir(plan["out_dir"]) if n.endswith(".hwpx"))
                for i, p in enumerate(bad):
                    dst = os.path.join(_qdir(root), "%s_unverified_%d_%s" % (name_id, i, os.path.basename(p)))
                    os.replace(p, dst)
                    built["outputs"].append(dst)
                    moved = moved or dst
        elif plan["op"] in ("protect", "replace", "fill") and os.path.isfile(plan["out"]):
            res["drm_signature"] = drm_signature(plan["out"])
            if (plan["protection_required"] and res["drm_signature"] is not True) or rc != 0 or not known_document_signature(plan["out"]):
                suffix = "plaintext" if plan["protection_required"] and res["drm_signature"] is not True else "unverified"
                moved = os.path.join(_qdir(root), "%s_%s_out%s" % (name_id, suffix, os.path.splitext(plan["out"])[1]))
                os.replace(plan["out"], moved)
        outs = []
        for p in list(dict.fromkeys(built["outputs"] + ([moved] if moved else []))):
            if os.path.isfile(p):
                outs.append({"path": _rel(root, p), "bytes": os.path.getsize(p), "sha256": sha256_of(p)})
        for d in built.get("outputs_dirs", []):
            if os.path.isdir(d):
                for n in sorted(os.listdir(d)):
                    p = os.path.join(d, n)
                    if os.path.isfile(p):
                        outs.append({"path": _rel(root, p), "bytes": os.path.getsize(p), "sha256": sha256_of(p)})
        res["outputs"] = outs
        if moved:
            res["notes"] = ["결과가 보호본이 아니거나(평문 — 반출 금지) 실패한 실행이 남긴 확인 안 된 파일이어서 output 에서 "
                            "quarantine 으로 옮겼다 (24시간 뒤 자동 삭제)"]
            res["status"] = "error"
            return res
        if hwpx and plan["op"] in ("fill", "replace", "insert") and rc == 0 and not os.path.isfile(plan["out"]):
            res["notes"] = ["스크립트는 성공했으나 저장본이 없다"]
            res["status"] = "error"
            return res
        if plan["op"] in ("protect", "replace", "fill") and not hwpx:
            res["drm_signature"] = drm_signature(plan["out"])
            if rc == 0 and (not os.path.isfile(plan["out"]) or (plan["protection_required"] and res["drm_signature"] is not True)):
                res["notes"] = ["스크립트는 성공했으나 서명이 보호본이 아니다 — 평문 사본일 수 있다"]
                res["status"] = "error"
                return res
        res["status"] = "ok" if rc == 0 else "error"
    except Reject as e:
        res["status"] = "rejected"
        res["notes"] = [str(e)]
    except Exception as e:                       # 워커를 죽이지 않는다
        res["status"] = "error"
        res["notes"] = ["내부 오류: %s: %s" % (type(e).__name__, e)]
    finally:
        res["finished"] = time.strftime("%Y-%m-%d %H:%M:%S")
    return res
