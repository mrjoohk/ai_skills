#!/usr/bin/env python3
"""그림 꾸러미 (P-052) — DRM 출처 문서를 한 번 열어 그림 문단만 남긴 보호 문서를 만들고, 그림마다 그 그림 하나만 든
보호 문서(fig01.hwpx …)로 나눠 둔다. 끼워 넣기(insert_doc.py)가 큰 출처 문서 전체 대신 그림 하나짜리 파일을 끼우게 해
자원을 아낀다. 그림을 PNG 등 평문 파일로 꺼내지 않는다(D-028) — 모든 결과는 한/글이 DocuRay 로 저장한 .hwpx 다.

    python tools\\doc-writer\\figure_pack.py <출처.hwpx> --out-dir <새 폴더> [--only 1,3] [--report <보고.md>] [--timeout 180]

1) 출처를 열어 그림만 든 최상위 문단(종류 object, PICTURE)을 문서 차례로 k = 1, 2, … 로 센다. 첫 문단(구역 정의가 든 문단)은
   그릇으로 남기고, 그림 문단 사이·뒤의 문단을 지운다(문단 끝에서 시작하는 선택 — PoC I1 과 같은 길, 실측 S1 문서 끝 지우기)
   → <폴더>/all.hwpx (첫 문단 + 그림 문단들).
2) all.hwpx 를 열 때마다 그림 k 하나만 남겨 <폴더>/figKK.hwpx 로 저장(--only 면 그 번호만).
쓴 뒤 대조(어긋나면 그 파일은 저장하지 않고 실패): 그림 수, 그림마다 캡션 제목·크기(mm)가 출처와 같음, DocuRay 저장·다시 열기·
출처 바뀌지 않음. 글자와 섞인 그림 문단·표 안 그림은 담지 않고 보고한다. 첫 문단이 그림인 출처는 거절(실측하지 않은 배치).
끼워 넣기 명세에서는 `![캡션](hwpx:<폴더>/figKK.hwpx#1)` 로 쓴다(꾸러미 파일 안의 첫 그림).
보고(<폴더>/../<폴더 이름>.pack_report.md 또는 --report): 번호·캡션 제목·크기·파일 — 캡션 글이 들어 있다(평문).

종료코드: 0 성공 / 1 대조 실패 / 2 사전조건(출처 없음·폴더 있음·첫 문단 그림·담을 그림 없음) / 3 평문 저장 / 4 열기 실패 / 5·6
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import insert_doc as ins        # noqa: E402  (write_doc·hwpx-drm 경로도 잡는다)
import hwp_session as hs        # noqa: E402
import hwpx_api as api          # noqa: E402
import render_md as rm          # noqa: E402

SIZE_TOL_MM = 0.2


class PackError(api.MapError):
    code = 2


def root_pictures(x):
    """HWPML → [루트 번호마다 [(캡션 제목, (가로 mm, 세로 mm))]] — 그 문단에 바로 든 그림. 캡션 제목은 캡션 글자에서 라벨
    '그림'·번호(AUTONUM, 글자에 없음)를 뺀 것(빈칸 지움)."""
    root = ins.wd_root(x)
    body = root.find("BODY")
    out = []
    for sec in (body.findall("SECTION") if body is not None else []):
        for p in sec.findall("P"):
            pics = []
            for pic in (e for t in p.findall("TEXT") for e in t if e.tag == "PICTURE"):
                cap = pic.find("SHAPEOBJECT/CAPTION")
                title = ""
                if cap is not None:
                    title = "".join((c.text or "") for c in cap.iter("CHAR"))
                    title = re.sub(r"^\s*그림", "", re.sub(r"\s+", "", title))
                sz = pic.find("SHAPEOBJECT/SIZE")
                size = (round(int(sz.get("Width")) / ins.MM, 1), round(int(sz.get("Height")) / ins.MM, 1)) \
                    if sz is not None and sz.get("Width", "").isdigit() else None
                pics.append((title, size))
            out.append(pics)
    return out


def packable(m, rp):
    """담을 그림 문단(루트 번호) 목록, 루트 문단에 든 그림 가운데 담지 않는 수 — 그림 하나만 든 문단(종류 object)만 담는다."""
    kinds = [r["kind"] for r in m["roots"]]
    keep = [i for i, pics in enumerate(rp) if len(pics) == 1 and i < len(kinds) and kinds[i] == "object"]
    return keep, sum(len(p) for p in rp) - len(keep)


def table_pictures(x, rp):
    """표·글상자 안 등 루트 문단에 바로 들지 않은 그림 수."""
    return len(re.findall(r"<PICTURE\b", ins.hp.clean(x)[0])) - sum(len(p) for p in rp)


def tail_delete(s, a, b):
    """루트 a 끝 → b 끝 선택해 지운다 = a+1..b 문단이 사라지고 a 는 그대로(PoC I1)."""
    if b <= a:
        return
    ins.move(s, a)
    ins.end_of_para(s)
    for _ in range(b - a):
        s.s.run("MoveSelNextParaBegin")
    s.s.run("MoveSelParaEnd")
    s.s.run("Delete")
    s._model = None


def delete_after(s, a):
    """루트 a 끝 → 문서 끝 선택해 지운다(실측 S1 — build_templates)."""
    ins.move(s, a)
    ins.end_of_para(s)
    s.s.run("MoveSelDocEnd")
    s.s.run("Delete")
    s._model = None


def keep_roots(s, keep):
    """첫 문단(0)과 keep(오름차순, 0 없음) 문단만 남긴다 — 뒤에서부터 지워 번호가 밀리지 않게."""
    last = len(s.model(refresh=True)["roots"]) - 1
    if keep[-1] < last:
        delete_after(s, keep[-1])
    anchors = [0] + keep
    for a, b in reversed(list(zip(anchors, anchors[1:]))):
        tail_delete(s, a, b - 1)


def check_saved(s, path, want):
    """저장한 파일을 다시 열어 그림(캡션 제목·크기) 목록이 want 와 같은지 → 문제 목록."""
    s.open(path)
    m = s.model(refresh=True)
    got = [p for pics in root_pictures(s.last_hwpml or "") for p in pics]
    s.s.clear()
    s.path, s._model = None, None
    probs = []
    if len(got) != len(want):
        probs.append("그림 수 %d (기대 %d)" % (len(got), len(want)))
    for i, ((t1, z1), (t2, z2)) in enumerate(zip(want, got), 1):
        if t1 != t2:
            probs.append("그림 %d 캡션 제목 다름" % i)
        if z1 and z2 and max(abs(z1[0] - z2[0]), abs(z1[1] - z2[1])) > SIZE_TOL_MM:
            probs.append("그림 %d 크기 %s → %s" % (i, z1, z2))
    if [r["kind"] for r in m["roots"]][1:] != ["object"] * len(want):
        probs.append("첫 문단 뒤가 그림 문단만이 아니다")
    return probs


def save_checked(s, out, want, rec, protection="preserve"):
    try:
        sv = s.save(out=out, protection=protection)
    except api.PlaintextSaved as e:
        rec["code"] = 3
        raise
    info = {k: sv.get(k) for k in ("out", "head", "protected", "reopen", "source_unchanged")}
    probs = [] if sv.get("reopen") and sv.get("source_unchanged") is not False else ["저장 확인 실패 %s" % info]
    probs += check_saved(s, out, want) if not probs else []
    if probs:
        bad = Path(out).with_name(Path(out).stem + ".unverified.hwpx")
        Path(out).replace(bad)
        info["moved_to"] = str(bad)
    return info, probs


def pack(s, src, out_dir, only=None, log=print, protection="preserve"):
    rec = {"source": str(src), "out_dir": str(out_dir), "ok": False, "files": [], "warnings": []}
    s.open(src)
    m = s.model()
    x = s.last_hwpml or ""
    rp = root_pictures(x)
    keep, skipped = packable(m, rp)
    inner = table_pictures(x, rp)
    if skipped or inner:
        rec["warnings"].append("담지 않은 그림 %d개(글자와 섞인 문단·한 문단에 그림 여럿·표 안 등)" % (skipped + inner))
    if not keep:
        raise PackError("담을 그림 문단(그림만 든 최상위 문단)이 없다")
    if keep[0] == 0:
        raise PackError("출처 첫 문단이 그림이다 — 첫 문단을 그릇으로 남기는 길만 실측했다")
    figs = [rp[i][0] for i in keep]
    rec["figures"] = [{"k": k, "title": t, "size_mm": z, "source_root": r}
                      for k, ((t, z), r) in enumerate(zip(figs, keep), 1)]
    sel = list(range(1, len(figs) + 1)) if not only else sorted(set(only))
    if [k for k in sel if not 1 <= k <= len(figs)]:
        raise PackError("--only 번호가 그림 수(%d) 밖이다: %s" % (len(figs), sel))
    out_dir.mkdir(parents=True)
    keep_roots(s, keep)
    allp = out_dir / "all.hwpx"
    info, probs = save_checked(s, allp, figs, rec, protection)
    rec["all"] = info
    if probs:
        rec["error"] = "all.hwpx: " + "; ".join(probs)
        return rec
    for k in sel:
        s.open(allp)
        n = len(figs)
        if k < n:
            delete_after(s, k)
        if k > 1:
            tail_delete(s, 0, k - 1)
        out = out_dir / ("fig%02d.hwpx" % k)
        info, probs = save_checked(s, out, [figs[k - 1]], rec, protection)
        rec["files"].append(dict(info, k=k, file=out.name))
        if probs:
            rec["error"] = "%s: %s" % (out.name, "; ".join(probs))
            return rec
    rec["ok"] = True
    return rec


def write_report(rec, path, started):
    md = ["# 그림 꾸러미 보고", "",
          "- 실행: %s · `tools/doc-writer/figure_pack.py`" % started.isoformat(timespec="seconds"),
          "- 출처 `%s` → 폴더 `%s` · 결과 **%s**" % (rec.get("source"), rec.get("out_dir"),
                                                "OK" if rec.get("ok") else "FAIL: " + rm.esc(rec.get("error", ""))), ""]
    if rec.get("warnings"):
        md += ["## 경고", ""] + ["- %s" % rm.esc(w) for w in rec["warnings"]] + [""]
    if rec.get("figures"):
        made = {f["k"]: f.get("file") for f in rec.get("files", [])}
        md += ["## 그림", "", "| k | 캡션 제목 | 크기(mm) | 출처 루트 | 파일 |", "|---|---|---|---|---|"]
        md += ["| %d | %s | %s | %s | %s |" % (f["k"], rm.esc(f["title"]), f["size_mm"], f["source_root"], made.get(f["k"], "-"))
               for f in rec["figures"]] + [""]
    md += ["## 자세히 (JSON)", "", "```json", json.dumps(rec, ensure_ascii=False, indent=1, default=str), "```", ""]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(md), encoding="utf-8")
    return path


def build_parser():
    ap = argparse.ArgumentParser(description="DRM 출처 문서의 그림 문단만 그림 하나짜리 보호 문서로 나눠 둔다")
    ap.add_argument("source")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--only", help="쉼표로 구분한 그림 번호(k) — 없으면 모두")
    ap.add_argument("--report")
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--protection", choices=("preserve", "required"), default="preserve")
    return ap


def main(argv=None):
    from _console import configure_console
    configure_console()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    args = build_parser().parse_args(argv)
    started = datetime.datetime.now()
    src, out_dir = Path(args.source).resolve(), Path(args.out_dir).resolve()
    report = Path(args.report) if args.report else out_dir.with_name(out_dir.name + ".pack_report.md")
    rec = {"source": str(src), "out_dir": str(out_dir), "ok": False,
           "error": "실행 중 — 이 보고가 남았으면 끝나지 않았다(콘솔의 오류를 본다)"}
    write_report(rec, report, started)
    code = 2
    try:
        if not src.is_file():
            raise PackError("출처가 없다: %s" % src)
        if out_dir.exists():
            raise PackError("출력 폴더가 이미 있다 — 덮어쓰지 않는다: %s" % out_dir)
        only = None
        if args.only:
            if not re.fullmatch(r"\s*\d{1,3}(\s*,\s*\d{1,3})*\s*", args.only):
                raise PackError("--only 는 쉼표로 구분한 번호다: %r" % args.only)
            only = [int(v) for v in args.only.split(",")]
        rec.pop("error")
        with api.HwpxSession(timeout=args.timeout, log=print) as s:
            rec = pack(s, src, out_dir, only, log=print, protection=args.protection)
            code = 0 if rec["ok"] else rec.get("code", 1)
    except api.PlaintextSaved as e:
        rec["error"] = "DRM 미적용으로 저장됐다 — 반출 금지: %s" % e
        code = 3
    except hs.HwpError as e:
        rec["error"] = "%s: %s" % (type(e).__name__, e)
        code = e.code
    print("%s — %s" % ("OK" if rec.get("ok") else "FAIL", rec.get("error", rec.get("out_dir"))))
    print("보고: %s" % write_report(rec, report, started))
    return code


if __name__ == "__main__":
    sys.exit(main())
