#!/usr/bin/env python3
"""hwpx-drm 파이썬 API (설계 IF-2, UF-05~09). 목표 3 작성 스킬이 import 한다.

    from hwpx_api import HwpxSession, load_map
    with HwpxSession(timeout=180) as s:
        s.open(path)                       # 실패 시 예외 (OpenFailed 등)
        doc = s.model()                    # 문서 모델 (hwpml_parse)
        r = s.fill({"과제명": "..."})      # {"filled":[..], "missing":[..], "mismatch":[..]}
        r = s.replace({"{{일자}}": "..."}) # 키별 전/후 건수와 남은 위치
        r = s.save()                       # <원본>_out.hwpx, {"protected":True, "reopen":True, ...}

쓰기 원칙
- 채우기는 필드(누름틀·셀 필드)로만 한다. PutFieldText 는 없는 이름을 조용히 무시하므로(C12) 먼저 FieldExist 로
  나누고, 넣은 뒤 같은 이름의 모든 필드를 GetFieldText 로 다시 읽어 맞춰 본다.
- 바꾸기는 AllReplace 1회/키. 전·후 건수는 HWPML 문서 모델(본문·셀·머리말·각주·메모 등 모든 위치)로 센다.
- 저장은 SaveAs(…, 'HWPX'). 기본은 원본을 두고 <원본>_out.hwpx. 문서 전체 XML 되넣기(SetTextFile)는 쓰지 않는다(F-033).
"""
import datetime
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import hwp_session as hs
import hwpml_parse as hp

SEP = "\x02"
# AllReplace 찾기 조건을 모두 명시한다 - GetDefault 는 사용자가 마지막으로 쓴 찾기 대화상자 설정을 줄 수 있다
REPLACE_OPTIONS = dict(MatchCase=1, AllWordForms=0, SeveralWords=0, UseWildCards=0, WholeWordOnly=0, AutoSpell=0,
                       ReplaceMode=1, IgnoreFindString=0, IgnoreReplaceString=0, FindRegExp=0, FindJaso=0,
                       HanjaFromHangul=0, FindStyle="", ReplaceStyle="", FindType=1)
_INST = re.compile(r"^(.*)\{\{(\d+)\}\}$")


class MapError(hs.HwpError):
    code = 2


class SaveFailed(hs.HwpError):
    code = 1

    def __init__(self, msg, rec=None):
        super().__init__(msg)
        self.rec = rec or {}


class EditFailed(hs.HwpError):
    code = 1


class PlaintextSaved(hs.HwpError):
    code = 3

    def __init__(self, msg, rec=None):
        super().__init__(msg)
        self.rec = rec or {}


# ------------------------------------------------------------------ UF-09 값 파일

def load_map(path):
    """값 JSON 또는 .md 안의 ```json 블록(여러 개면 합침) → {문자열: 문자열}. UTF-8, BOM 허용. 중복 키는 오류."""
    p = Path(path)
    if not p.exists():
        raise MapError("값 파일이 없다: %s" % p)
    raw = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".md":
        blocks = re.findall(r"```json[ \t]*\r?\n(.*?)\r?\n```", raw, re.S)
        if not blocks:
            raise MapError("%s 에 ```json 블록이 없다" % p.name)
    else:
        blocks = [raw]
    out = {}
    for i, b in enumerate(blocks):
        def hook(pairs):
            d = {}
            for k, v in pairs:
                if k in d:
                    raise MapError("중복 키: %r (%s 블록 %d)" % (k, p.name, i + 1))
                d[k] = v
            return d
        try:
            obj = json.loads(b, object_pairs_hook=hook, parse_int=str, parse_float=str)   # 1.10 은 "1.10" 그대로
        except json.JSONDecodeError as e:
            raise MapError("JSON 오류 (%s 블록 %d): %s" % (p.name, i + 1, e))
        if not isinstance(obj, dict):
            raise MapError("JSON 최상위는 {키: 값} 이어야 한다 (%s 블록 %d)" % (p.name, i + 1))
        for k, v in obj.items():
            if k in out:
                raise MapError("중복 키: %r (%s 블록 사이)" % (k, p.name))
            out[k] = check_value(k, v)
    if not out:
        raise MapError("값이 하나도 없다: %s" % p.name)
    return out


def check_value(k, v):
    if isinstance(v, (dict, list, bool)):
        raise MapError("값은 문자열(또는 숫자)이어야 한다: %r" % k)
    v = "" if v is None else str(v)
    if SEP in k or SEP in v:
        raise MapError("키·값에 0x02 문자를 쓸 수 없다 (필드 구분자): %r" % k)
    if not k:
        raise MapError("빈 키")
    return v


def norm_nl(s):
    return (s or "").replace("\r\n", "\n").replace("\r", "\n")


def sha256(path):
    """원본 바이트(암호문 그대로)의 해시 - 원본이 바뀌지 않았는지 확인용. 복호화하지 않는다."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ------------------------------------------------------------------ 세션

class HwpxSession:
    def __init__(self, timeout=180, allow_running=False, log=None, session=None):
        self.s = session or hs.HwpSession(timeout=timeout, allow_running=allow_running, log=log)
        self.log = log or (lambda m: None)
        self.path = None
        self.head = None
        self._model = None
        self.last_hwpml = None                 # 마지막 모델의 HWPML 원문 — 모델에 없는 서식(표 테두리 등) 대조용 (P-040)
        self.timing = {}

    def __enter__(self):
        self.s.start()
        return self

    def __exit__(self, *exc):
        self.s.close()
        return False

    @property
    def hwp(self):
        return self.s.hwp

    # -------------------------------------------------------------- 읽기

    def open(self, path):
        p = Path(path).resolve()
        self.head = hs.head_kind(p) if p.exists() else None
        t = _now()
        self.s.open(p)
        self.timing["open"] = _since(t)
        self.path, self._model = p, None
        return True

    def model(self, refresh=False):
        if self._model is None or refresh:
            t = _now()
            x = self.s.export_hwpml()
            self.timing["export"] = _since(t)
            self.last_hwpml = x
            t = _now()
            m = hp.parse(x)
            self.timing["parse"] = _since(t)
            m["hwpml_chars"] = len(x)
            m["file"] = str(self.path) if self.path else None
            m["head"] = self.head
            m["hwp_version"] = self.s.version
            self._model = m
        return self._model

    def field_names(self, option, number=0):
        raw = str(self.s.call("GetFieldList", self.hwp.GetFieldList, number, option) or "")
        return [n for n in raw.split(SEP) if n]

    def fields(self):
        """UF-05: 문서 모델의 필드 + 한/글 GetFieldList(셀 1·누름틀 2·글상자 8) 대조."""
        m = self.model()
        com = {kind: self.field_names(opt) for kind, opt in (("cell", 1), ("clickhere", 2), ("textbox", 8))}
        rows = {}
        for f in m["fields"]:
            key = (f["name"], f["kind"])
            r = rows.setdefault(key, {"name": f["name"], "kind": f["kind"], "count": 0, "at": [], "values": []})
            r["count"] += 1
            r["at"].append(f["at"])
            r["values"].append(f.get("value", ""))
            for k in ("guide", "help", "command"):
                if f.get(k):
                    r.setdefault(k, f[k])
        known = {(f["name"], f["kind"]) for f in m["fields"]}
        com_only = []
        for kind, names in com.items():
            for n in sorted(set(names)):
                if (n, kind) not in known:
                    com_only.append({"name": n, "kind": kind, "count": names.count(n)})
                elif names.count(n) != rows[(n, kind)]["count"]:
                    rows[(n, kind)]["com_count"] = names.count(n)
        inputs = [r for r in rows.values() if r["kind"] in ("clickhere", "cell")]
        others = [r for r in rows.values() if r["kind"] not in ("clickhere", "cell")]
        return {"input": inputs + com_only, "other": others, "memos": len(m["memos"]), "com": com}

    # -------------------------------------------------------------- 쓰기

    def fill(self, mapping):
        """UF-06. 반환 {"filled":[키], "missing":[키], "mismatch":[{key, field, got}]}."""
        mapping = {k: check_value(k, v) for k, v in mapping.items()}
        exist = {k: bool(self.s.call("FieldExist", self.hwp.FieldExist, k)) for k in mapping}
        # 이름만 준 키(같은 이름 모두 채움)를 먼저, 이름{{n}} 키를 뒤에 - 개별 지정이 덮이지 않게
        present = sorted((k for k in mapping if exist[k]), key=lambda k: bool(_INST.match(k)))
        missing = [k for k in mapping if not exist[k]]
        if present:
            vals = [norm_nl(mapping[k]).replace("\n", "\r\n") for k in present]
            self.s.call("PutFieldText", self.hwp.PutFieldText, SEP.join(present), SEP.join(vals))
        mismatch = self.verify_fields({k: mapping[k] for k in present})
        self._model = None
        bad = {m["key"] for m in mismatch}
        return {"filled": [k for k in present if k not in bad], "missing": missing, "mismatch": mismatch}

    def verify_fields(self, mapping):
        """같은 이름의 필드를 모두(name{{n}}) 다시 읽어 값과 맞춘다. 줄바꿈은 \\n 으로 맞춰 비교."""
        if not mapping:
            return []
        inst = {}
        for n in self.field_names(0, number=1):              # hwpFieldNumber: 이름{{n}}
            mm = _INST.match(n)
            if mm:
                inst.setdefault(mm.group(1), []).append(n)
        explicit = {k for k in mapping if _INST.match(k)}    # 따로 지정한 필드는 이름만 준 키의 확인에서 뺀다
        out = []
        for k, v in mapping.items():
            for name in [n for n in inst.get(k) or [k] if n not in explicit]:
                got = str(self.s.call("GetFieldText", self.hwp.GetFieldText, name) or "")
                if norm_nl(got) != norm_nl(v):
                    out.append({"key": k, "field": name, "got": got[:200]})
        return out

    def delete_before(self, para_index):
        """본문 처음부터 루트 리스트의 para_index 번째 문단 앞까지 지운다. 양식 파일 앞쪽의 '작성방법' 표지처럼
        통째로 걷어낼 부분에 쓴다. para_index 는 구역을 이어 센 루트 리스트 번호다(실측 P-022: 구역을 넘어 지워짐,
        U-15). 지운 뒤 남는 첫 문단은 지운 첫 문단의 그릇(조판 개체 포함)에 para_index 문단의 글자가 붙은 것이다
        (F-095). 성공 여부는 호출자가 지운 뒤의 HWPML 로 반드시 확인한다(첫 문단·남은 문단 수)."""
        if para_index <= 0:
            return False
        self.s.call("MovePos", self.hwp.MovePos, 2, 0, 0)          # moveTopOfFile
        ok = bool(self.s.call("SelectText", self.hwp.SelectText, 0, 0, para_index, 0))
        if not ok:
            raise EditFailed("SelectText(0,0,%d,0) 실패" % para_index)
        self.s.run("Delete")
        self._model = None
        return True

    def _caret_to(self, root_para):
        ok = bool(self.s.call("MovePos", self.hwp.MovePos, 0, root_para, 0))      # moveMain: 루트 리스트 문단
        if not ok:
            raise EditFailed("MovePos(moveMain, %d, 0) 실패" % root_para)

    def clear_paras(self, first_root, last_root):
        """루트 문단 first~last(포함)의 글자를 지우고 빈 문단 하나만 남긴다 — 다음 문단(다른 구역의 첫 문단일 수 있다)은
        건드리지 않는다. 블록은 동작으로 잡는다: 처음 문단 시작 → 다음 문단 시작 ×(last-first) → 문단 끝. 실측 전(P-024).
        호출자가 HWPML 로 확인한다(문단 수가 last-first 만큼 줄고 다음 문단은 그대로)."""
        if last_root < first_root:
            return False
        self._caret_to(first_root)
        for _ in range(last_root - first_root):
            self.s.run("MoveSelNextParaBegin")
        self.s.run("MoveSelParaEnd")
        self.s.run("Delete")
        self._model = None
        return True

    def delete_to_end(self, start_root):
        """루트 문단 start_root 부터 문서 끝까지 지운다(빈 문단 하나가 남는다). 실측 전(P-024). 호출자가 HWPML 로 확인한다."""
        self._caret_to(start_root)
        self.s.run("MoveSelDocEnd")
        self.s.run("Delete")
        self._model = None
        return True

    def page_count(self):
        """현재 문서 쪽 수(한/글 PageCount 속성). 못 읽으면 None — 기록용."""
        try:
            return int(self.s.call("PageCount", lambda: self.hwp.PageCount))
        except hs.TimeoutKilled:
            raise
        except Exception:
            return None

    def find_dir_all(self):
        try:                                                 # PoC P7 과 같은 경로
            return self.s.call("FindDir", self.hwp.FindDir, "AllDoc")
        except hs.TimeoutKilled:
            raise
        except Exception:
            return 2

    def count_keys(self, keys, model=None):
        m = model or self.model(refresh=True)
        res = {k: {"count": 0, "at": {}} for k in keys}
        texts = []
        for loc, kind, text in hp.iter_locations(m):
            texts.append((loc, kind, text))
            for k in keys:
                n = text.count(k)
                if n:
                    res[k]["count"] += n
                    res[k]["at"][loc] = (kind, n)
        return res, texts

    def replace(self, mapping):
        """UF-07. 키마다 AllReplace 1회. 반환 {키: {before, after, expected_after, remaining, remaining_at, ret}}.

        - 긴 키부터 바꾼다: '○○○'와 '○○○○'가 같이 있으면 '○○○○'가 먼저 (짧은 키가 긴 키를 갉아먹지 않게)
        - 값 안에 다른 키가 들어 있으면 연쇄 치환이 되므로 거부한다(종료코드 2). 자기 키를 담는 것은 허용
        - 줄바꿈 값은 거부한다(AllReplace 의 줄바꿈 처리 미실측) - 여러 줄은 필드(fill)로
        """
        mapping = {k: check_value(k, v) for k, v in mapping.items()}
        for k, v in mapping.items():
            if "\n" in k or "\r" in k or "\n" in v or "\r" in v:
                raise MapError("replace 의 키·값에는 줄바꿈을 쓸 수 없다(미실측): %r - 여러 줄은 필드 채우기(fill)로" % k)
            other = [o for o in mapping if o != k and o in v]
            if other:
                raise MapError("값 안에 다른 키가 있어 연쇄 치환이 된다: %r 의 값에 %r - 값을 바꾸거나 두 번에 나눠 실행" % (k, other[0]))
        keys = sorted(mapping, key=len, reverse=True)        # 긴 키 먼저 (안정 정렬 - 같은 길이는 입력 순서)
        before, texts = self.count_keys(keys, self.model(refresh=True))
        expected = {loc: t for loc, _, t in texts}            # 같은 순서로 바꾼 '기대 결과'
        for k in keys:
            if before[k]["count"]:
                expected = {loc: t.replace(k, mapping[k]) for loc, t in expected.items()}
        rets = {}
        for k in keys:
            if before[k]["count"] == 0:
                continue
            rets[k] = self.s.action("AllReplace", "FindReplace", FindString=k, ReplaceString=mapping[k],
                                    Direction=self.find_dir_all(), IgnoreMessage=1, **REPLACE_OPTIONS)
        after, _ = self.count_keys(keys)
        out = {}
        for k in mapping:                                    # 보고는 입력 순서로
            exp = sum(t.count(k) for t in expected.values())
            remaining_at = {loc: kn for loc, kn in after[k]["at"].items()
                            if kn[1] > expected.get(loc, "").count(k)}
            out[k] = {"before": before[k]["count"], "after": after[k]["count"], "expected_after": exp,
                      "remaining": max(0, after[k]["count"] - exp), "remaining_at": remaining_at,
                      "ret": rets.get(k), "order": keys.index(k) + 1}
        self._model = None
        return out

    def save(self, out=None, overwrite=False, force=False, verify_fields=None):
        """UF-08. 기본 <원본>_out.hwpx. overwrite 면 .bak 을 만든 뒤 임시 파일에 저장하고,
        보호(DOCURAY)·다시 열기·값 재확인이 모두 통과해야 원본 자리로 바꿔 끼운다. 실패하면 원본은 그대로 둔다."""
        if self.path is None:
            raise hs.PreconditionError("열린 문서가 없다")
        src = self.path
        src_hash = sha256(src) if src.exists() else None
        rec = {"source": str(src)}
        if overwrite:
            if src.suffix.lower() != ".hwpx":                 # .hwp 이름에 HWPX 바이트를 쓰지 않는다 (F-005 의 반대)
                raise hs.PreconditionError("%s 원본은 덮어쓸 수 없다 - HWPX 로만 저장한다. --out <이름>.hwpx 를 쓴다" % src.suffix)
            target = src
            bak = _free_name(src.with_name(src.name + ".bak"))
            shutil.copy2(src, bak)                           # 암호문 바이트 복사 (복호화 아님)
            rec["backup"] = str(bak)
            dest = _free_name(src.with_name(src.stem + ".__hwpxdrm_tmp__.hwpx"))
        else:
            target = Path(out).resolve() if out else src.with_name(src.stem + "_out.hwpx")
            if target.suffix.lower() != ".hwpx":
                raise hs.PreconditionError("출력은 .hwpx 이름이어야 한다: %s" % target.name)
            if target == src:
                raise hs.PreconditionError("출력이 원본과 같다 - 덮어쓰려면 --overwrite")
            if target.exists():
                if not force:
                    raise hs.PreconditionError("출력 파일이 이미 있다: %s (--force 로 교체)" % target)
                target.unlink()                              # 덮어쓰기 대화상자 방지
            dest = target
        dest.parent.mkdir(parents=True, exist_ok=True)
        ok = bool(self.s.call("SaveAs", self.hwp.SaveAs, str(dest), "HWPX", ""))
        if not ok or not dest.exists():
            raise SaveFailed("SaveAs 실패 (반환 %s, 파일 %s): %s" % (ok, dest.exists(), dest))
        rec["head"] = hs.head_kind(dest)
        rec["protected"] = rec["head"] == "DOCURAY"
        self.s.clear()
        rec["reopen"] = bool(self.s.call("Open", self.hwp.Open, str(dest), "HWPX", ""))
        if rec["reopen"] and verify_fields:
            rec["after_reopen_mismatch"] = self.verify_fields(verify_fields)
        self.s.clear()
        self.path, self._model = None, None
        if overwrite:
            rec["temp"] = str(dest)
            problem = ("DRM 미적용(%s)" % rec["head"] if not rec["protected"] else
                       "다시 열기 실패" if not rec["reopen"] else
                       "다시 연 뒤 값 불일치" if rec.get("after_reopen_mismatch") else None)
            if problem:                                      # 원본은 건드리지 않는다
                rec["out"] = str(dest)
                msg = "%s - 원본은 그대로 두었다. 결과 임시 파일 %s, 원본 사본 %s" % (problem, dest, rec["backup"])
                if not rec["protected"]:
                    raise PlaintextSaved(msg + " (임시 파일은 평문 - 반출 금지)", rec)
                raise SaveFailed(msg, rec)
            try:
                os.replace(dest, target)
            except OSError as e:
                rec["out"] = str(dest)
                raise SaveFailed("원본 자리로 바꿔 끼우기 실패(%s). 결과는 %s, 원본 사본은 %s" % (e, dest, rec["backup"]), rec)
            rec["head"] = hs.head_kind(target)
            rec["protected"] = rec["head"] == "DOCURAY"
            del rec["temp"]
        rec["out"] = str(target)
        if not overwrite and src_hash:
            rec["source_unchanged"] = sha256(src) == src_hash
        if not rec["protected"]:
            raise PlaintextSaved("저장 결과가 DRM 미적용(%s): %s - 반출 금지, 보안 정책에 따라 처리한다" % (rec["head"], target),
                                 rec)
        return rec


def _free_name(p):
    if not p.exists():
        return p
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    q = p.with_name("%s.%s%s" % (p.stem, stamp, p.suffix))
    i = 1
    while q.exists():
        q = p.with_name("%s.%s_%d%s" % (p.stem, stamp, i, p.suffix))
        i += 1
    return q


def _now():
    import time
    return time.time()


def _since(t):
    import time
    return round(time.time() - t, 2)
