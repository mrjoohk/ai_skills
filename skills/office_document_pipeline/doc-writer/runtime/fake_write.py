#!/usr/bin/env python3
"""Run content specifications through a synthetic COM model without starting HWP.

Usage: python tools/doc-writer/fake_write.py <spec.md> <report.json> [--dummy]
The selected profile binds template and model by SHA-256. Unknown or changed
templates produce template_modeled=false. All document writes stay in a temporary
directory. This checks authoring logic, not HWP application or layout compatibility.
--sum-negative-control is a legacy numbering stress-fixture option used in tests.
"""
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path, PureWindowsPath

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T = HERE / "tests"
MARK = "doc-writer/fake_write"                                 # 결과 JSON 표지 — 지난 가짜 쓰기 결과만 덮는다(검토 D7-②-01)
sys.path.insert(0, str(T))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "backends" / "hwp" / "tests"))
sys.path.insert(0, str(ROOT / "tools" / "hwpx-drm" / "tests"))
import write_doc as wd                      # noqa: E402
import hwp_session as hs                    # noqa: E402
import hwpx_api as api                      # noqa: E402
import table_style as ts                    # noqa: E402
import template_model
from fake_hwp import FakeHwp, make_env, DECL16   # noqa: E402


def template(profile=None):
    """Load the selected profile's simulation model; never open the document in COM."""
    data = wd.profiles.load_profile(profile, ROOT)
    return (Path(data["_path"]).parent / data["model_hwpml"]).read_text(encoding="utf-8")


COMMON = "document_templates/technical-report/template.package.zip"
PARASHAPE_RX = re.compile(r'<P\b[^>]*?\bParaShape="(\d+)"')


class PathRefused(Exception):
    """명세 경로가 저장소 밖을 가리킬 수 있다 — 가짜 쓰기는 임시 폴더 밖에 쓰지 않는다(검토 P-051 D2-②-01)."""


def inside(tmp, p):
    """명세 경로 p → 임시 폴더 tmp 안 경로. 절대 경로·드라이브·'..'(wd.outside) 이거나 풀어 보니 tmp 밖이면 PathRefused."""
    q = (tmp / p).resolve()
    if wd.outside(p) or tmp.resolve() not in q.parents:
        raise PathRefused(p)
    return q


class Extra(FakeHwp):
    """실측 P-027(F-100): 표를 만들면 한/글이 표 문단 뒤에 빈 문단을 하나 더 둔다 — 작성기는 거기에 다음 항목을 쓴다."""
    def GetHeadingString(self):
        """FakeHwp.GetHeadingString 과 같은 셈(개요 문단을 문서 처음부터 수준별로, '1.2.1.' 꼴) — 문서를 한 번만 훑어 쓴 HWPML 이
        바뀔 때까지 둔다(FakeHwp 판은 문단마다 문서를 다시 훑어 SUM 크기에서 느리다)."""
        if getattr(self, "_hs_doc", None) is not self.hwpml:
            shapes = {k: self._head_attrs(v) for k, v in self._head_items(self.hwpml, "PARASHAPE").items()}
            count, nums = [0] * 7, []
            for s_, _ in self._top_paras():
                ps = PARASHAPE_RX.match(self.hwpml, s_)
                a = shapes.get(ps.group(1) if ps else "0") or {}
                if a.get("HeadingType") != "Outline":
                    nums.append("")
                    continue
                lvl = int(a.get("Level", "0"))
                count[lvl] += 1
                count[lvl + 1:] = [0] * (6 - lvl)
                nums.append(".".join(str(n) for n in count[:lvl + 1]) + ".")
            self._hs_doc, self._hs_nums = self.hwpml, nums
        return self._hs_nums[self.caret] if self.caret < len(self._hs_nums) else ""

    def _table_create(self, rows, cols):
        ok = FakeHwp._table_create(self, rows, cols)
        a = self._para_el(self.cell["para"])
        e = self._top_paras()[self.cell["para"]][1]
        self.hwpml = self.hwpml[:e] + '<P ParaShape="%s" Style="%s"><TEXT CharShape="0"/></P>' % (
            a.get("ParaShape", "0"), a.get("Style", "0")) + self.hwpml[e:]
        return ok


def want_newnums(blocks, pics):
    """명세 블록 → 작성기가 넣어야 할 새 번호 [[개체 태그, [[종류, 번호]]]] — 작성기 plan 과 따로 같은 규칙을 센다: 첫 그림(그림
    넣기일 때) 그림 1 · 첫 캡션 표 표 1 · 캡션 없는 표 뒤 첫 캡션 표 그 명세 번호."""
    out, nt, after_plain, fig = [], 0, True, False
    for b in blocks[1:]:
        if b["kind"] == "table" and b["caption"]:
            nt += 1
            if after_plain:
                out.append(["TABLE", [["Table", str(nt)]]])
            after_plain = False
        elif b["kind"] == "table":
            after_plain = True
        elif b["kind"] == "figure" and pics and not fig:
            fig = True
            out.append(["PICTURE", [["Figure", "1"]]])
    return out


def caption_numbers(caps):
    nums = {"TABLE": [], "PICTURE": []}
    for c in caps:
        m = re.match(r"(표|그림) (\d+) ", c["text"] or "")
        if m:
            nums[c["tag"]].append(int(m.group(2)))
    return nums


def run(spec_path, dummy=False, sum_negative=False):
    """명세 파일 → 판정 dict(out["all_ok"]). 쓰기는 임시 폴더(작성기 ROOT 를 잠시 바꿈) — 저장소는 건드리지 않는다. 명세 경로가
    저장소 밖을 가리킬 수 있으면 아무것도 쓰기 전에 PathRefused."""
    spec = Path(spec_path).read_text(encoding="utf-8-sig")
    meta, blocks = wd.parse_spec(spec)
    figs = [b for b in blocks if b["kind"] == "figure"]
    profile = wd.profiles.load_profile(meta.get("profile"), ROOT)
    profile_dir = Path(profile["_path"]).parent
    template_source = ROOT / PureWindowsPath(meta["template"]).as_posix()
    modeled = (not wd.outside(meta["template"]) and template_source.is_file()
               and hashlib.sha256(template_source.read_bytes()).hexdigest() == profile.get("template_sha256")
               and hashlib.sha256((profile_dir / profile["model_hwpml"]).read_bytes()).hexdigest() == profile.get("model_sha256"))
    styles = wd.profiles.resolve_styles(meta.get("profile"), meta.get("styles"), ROOT)
    modeled = modeled and styles == profile["styles"]
    model_check = (template_model.compare_model(template_source, profile_dir / profile["model_hwpml"])
                   if modeled else {"passed": False, "reason": "Template/model hash binding or style mapping differs"})
    modeled = modeled and model_check["passed"]
    tmp = Path(tempfile.mkdtemp())
    old_root = wd.ROOT
    try:
        paths = [meta["template"], meta["out"]] + ([meta["table_style"]] if meta.get("table_style") else []) \
            + [b["source"] for b in figs if b["source"]]
        for p_ in paths:                       # 먼저 모두 본다 — 하나라도 밖이면 아무것도 쓰지 않는다
            inside(tmp, p_)
        tpl = inside(tmp, meta["template"])
        tpl.parent.mkdir(parents=True, exist_ok=True)
        tpl.write_bytes(b"BMS DocuRay\x03\x01" + b"\x00" * 40)
        if meta.get("table_style"):
            q = inside(tmp, meta["table_style"])
            q.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / meta["table_style"], q)
        dummies = []
        for b in figs:                         # 저장소에 있는 그림만 흉내 파일로(--dummy 면 .png 출처 모두) — 없는 출처는 자리 표시
            if b["source"] and ((ROOT / b["source"]).is_file() or (dummy and b["source"].lower().endswith(".png"))):
                q = inside(tmp, b["source"])
                q.parent.mkdir(parents=True, exist_ok=True)
                q.write_bytes(b"\x89PNG")
                dummies.append(b["source"])
        # Copy only the selected preset; the simulation never mutates source resources.
        profile_target = tmp / "document_templates" / profile["id"]
        shutil.copytree(profile_dir, profile_target, dirs_exist_ok=True)
        sim_meta = dict(meta, profile=str(profile_target / "profile.json"))
        wd.ROOT = tmp
        out = {"spec": Path(spec_path).as_posix(), "dummy_all_png": dummy, "figure_files": len(dummies),
               "sum_negative_control": sum_negative, "model_check": model_check,
               "checks": {"spec": {"template_modeled": modeled}}}   # '\\' 꼴도(D2F-N03)
        tpl_hwpml = template() if not meta.get("profile") or meta.get("profile") == "technical-report" else template(meta["profile"])
        modes = ((True, "ok"), (False, "ok"), (True, "ignore"))
        for pics, mode in modes:
            f = Extra(docs={tpl.name: tpl_hwpml})
            f.newnum_mode = mode
            f.strict_block = True                  # 셀 블록을 풀지 않고 글자·칸 이동하면 오류(Cancel 확인)
            d, p, k, _ = make_env(f)
            t0 = time.time()
            with api.HwpxSession(session=hs.HwpSession(dispatch=d, pids=p, killer=k, sleep=lambda t: None)) as s:
                r = wd.write(s, sim_meta, blocks, log=lambda m: None, force=True, pictures=pics)
                last = s.last_hwpml                   # 쓴 뒤 대조에 쓴 HWPML(저장을 거절해도 남는다)
            x = f.docs.get(Path(meta["out"]).name) if r["ok"] else last
            m = wd.hp.parse(x)
            broot = r["body_root"]   # 흉내 템플릿: 앞 구역 문단 수 = 본문 첫 장 제목 루트 번호
            caps = wd.written_captions(x, broot)
            nums = caption_numbers(caps)
            _, _, elems = ts.load(x)
            margins = [[ts.hp._int(t_.find("INSIDEMARGIN").get(k_)) for k_ in ("Left", "Right", "Top", "Bottom")]
                       for tid, t_, _ in elems if tid.count(".") == 1 and int(tid.split(".")[0][1:]) == len(m["stats"]["section_paras"]) - 1]
            planned = [t_["inside_margin"] for t_ in (r.get("table_style") or {}).get("tables", [])]
            refs = sorted({(kind, int(n)) for b in wd.top_paras(m) for kind, n in re.findall(r"(그림|표) (\d+)", b["text"])})
            plain_fig = [b["text"] for b in wd.top_paras(m) if b.get("style") == styles["caption"]]
            have = ({("표", n) for n in nums["TABLE"]} | {("그림", n) for n in nums["PICTURE"]}
                    | {("그림", int(re.match(r"그림 (\d+) ", t_).group(1))) for t_ in plain_fig if re.match(r"그림 (\d+) ", t_)})
            key = "pictures=%s" % pics if mode == "ok" else "newnum_ignored"
            out[key] = {"ok": r["ok"], "error": r.get("error"), "plan": r["plan"], "warnings": r["warnings"],
                        "captions_check": r["check"]["captions"], "needs": len(r["needs"]), "sec": round(time.time() - t0, 1),
                        "caption_numbers": nums, "refs_in_text": len(refs), "refs_missing": [list(x_) for x_ in refs if x_ not in have],
                        "inside_margins": margins, "planned_margins": planned, "text_check": r.get("text_check"),
                        "newnum_written": [[c["tag"], c["newnum"]] for c in caps if c["newnum"]], "page": r["check"].get("page"),
                        "headings": r["check"].get("headings")}
            want_fig = list(range(1, len(figs) + 1)) if pics else []    # 명세 그림 블록에서 센다(작성기 plan 이 아니라 — D2-③-01)
            want_tab = list(range(1, sum(1 for b in blocks if b["kind"] == "table" and b["caption"]) + 1))
            in_order = nums["TABLE"] == want_tab and nums["PICTURE"] == want_fig
            if mode == "ignore":
                c = {"fail_closed": r["ok"] is False or (in_order and not r["check"]["captions"]["mismatch"])}
                if sum_negative:                   # SUM 꼴 전용 기대(17.sum_step7 [W2] 실측과 같은 꼴)
                    bad = r["check"]["captions"]["mismatch"]
                    c.update({"refused": r["ok"] is False,
                              "places_eq_pictures": "표·그림 캡션이 명세와 다르다(%d곳)" % len(figs) in (r.get("error") or ""),
                              "pictures_plus_one": nums["PICTURE"] == [n + 1 for n in want_fig],
                              "tables_right": nums["TABLE"] == want_tab,
                              "first_mismatch_like_step7": bool(bad) and bad[0]["want"].replace("그림 1 ", "그림 2 ", 1) == bad[0]["got"]})
                out["checks"][key] = c
                continue
            want_nn = want_newnums(blocks, pics)
            out["checks"][key] = {
                "ok": r["ok"] is True,
                "no_warnings": not r["warnings"],
                "captions_clean": not r["check"]["captions"]["mismatch"] and not r["check"]["captions"]["warn"],
                "captions_written_eq_plan": r["check"]["captions"]["written"] == r["plan"]["captions"],
                "sides": all(c_["side"] == ("Top" if c_["tag"] == "TABLE" else "Bottom") for c_ in caps if c_["text"]),
                "numbers_in_order": in_order,
                "plan_pictures_eq_spec": r["plan"]["pictures"] == len(want_fig),
                "plain_figure_captions": len(plain_fig) == (0 if pics else len(figs)),
                "refs_resolved": not out[key]["refs_missing"],
                "margins_half_char": margins == planned and all(mg[2:] == [500, 500] for mg in margins),
                "newnum_as_planned": sorted(out[key]["newnum_written"]) == sorted(want_nn)
                                     and r["check"]["captions"]["newnum"] == r["check"]["captions"]["newnum_inserted"]
                                     == len(want_nn) == r["plan"]["newnums"],
                "page_kept": r["check"]["page"] == {"body_first": [1, 1], "reads": [[1, 1], [1, 1]]},
                "text_checks_clean": r.get("text_check") is not None and not wd.text_check_problems(r["text_check"]),
            }
            o = tmp / meta["out"]
            if o.exists():
                o.unlink()
        out["all_ok"] = all(v for c in out["checks"].values() for v in c.values())
        return out
    finally:
        wd.ROOT = old_root
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv=None):
    from _console import configure_console
    configure_console()
    argv = sys.argv[1:] if argv is None else argv
    flags = {a for a in argv if a.startswith("--")}
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2 or flags - {"--dummy", "--sum-negative-control"}:
        print(__doc__)
        return 2
    res = Path(args[1])

    def dump(o):
        res.write_text(json.dumps(dict({"tool": MARK}, **o), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if res.exists():                                           # 덮는 것은 지난 가짜 쓰기 결과(표지 tool)뿐 — 명세·템플릿·표 서식·
        try:                                                   # 실측 판정 JSON 을 결과 자리로 준 오타가 그 파일을 지우지 않게
            old = json.loads(res.read_text(encoding="utf-8-sig"))   # (검토 D5-②-08·D6-②-01·D7-②-01, BOM 은 메모장 저장 — D6F-N02)
        except (OSError, ValueError):                          # 폴더·글자가 아닌 파일·JSON 아님
            old = None
        if not (isinstance(old, dict) and old.get("tool") == MARK):
            print("결과 자리에 가짜 쓰기 결과가 아닌 것이 있다 — 덮지 않는다(다른 경로를 준다): %s" % args[1])
            return 2
    try:                                                       # 지난 실행의 all_ok true 가 남지 않게 먼저 덮는다(검토 D4-②-03)
        dump({"spec": Path(args[0]).as_posix(), "all_ok": False, "error": "실행 중 — 이 줄이 남았으면 가짜 쓰기가 끝나지 않았다"})
    except OSError as e:                                       # 결과 자리를 못 쓴다(폴더 없음 등) — 끝 코드 2(D5-③-06)
        print("결과 JSON 을 쓰지 못했다: %s" % e)
        return 2
    try:
        out = run(args[0], dummy="--dummy" in flags, sum_negative="--sum-negative-control" in flags)
    except (PathRefused, OSError, UnicodeDecodeError, hs.HwpError) as e:
        # 아무것도 쓰지 않았다 — 결과 JSON 은 남긴다(종료코드 2 = 명세 쪽: 경로·명세 오류·키 값 안 키·출력이 템플릿·없는 파일·
        # UTF-8 아님 — 작성기 종료코드 2 와 같은 갈래 hs.HwpError code 2, D5-②-04). 명세 쪽이 아닌 흉내 오류는 그대로 올린다
        if isinstance(e, hs.HwpError) and e.code != 2:
            raise
        out = {"spec": Path(args[0]).as_posix(), "all_ok": False}
        if isinstance(e, PathRefused):
            out.update(refused_path=str(e), error="명세 경로가 저장소 밖을 가리킬 수 있다(절대 경로·드라이브·'..') — 가짜 쓰기는 "
                                                  "저장소 안 상대 경로만: %s" % e)
        elif isinstance(e, wd.SpecError):
            out["error"] = "명세 오류: %s" % e
        else:
            out["error"] = "명세 오류(%s): %s" % (type(e).__name__, e)
        dump(out)
        print(out["error"])
        return 2
    dump(out)
    print("all_ok", out["all_ok"], json.dumps(out["checks"], ensure_ascii=False))
    return 0 if out["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
