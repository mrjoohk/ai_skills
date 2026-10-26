#!/usr/bin/env python3
"""평문 HWPX(ZIP) 문서의 그림을 문서 순서대로 꺼낸다 — 설명서의 화면 그림을 새 문서(SUM 등)에 옮겨 쓸 때.

    python tools\\doc-writer\\extract_figures.py <원본.hwpx> <출력 폴더> [--max-width 1600]

DRM(DocuRay) 문서와 ZIP 이 아닌 파일은 거절한다(종료코드 2) — 이 도구는 파일을 직접 읽으므로 DRM 을 풀지 않는다. DRM 문서의
그림은 한/글로 여는 `tools/hwpx-drm/scripts/hwpx_drm.py images`(브리지 `images`, D-062)로 꺼낸다.
출력: fig01.png … — Pillow 가 있으면 PNG 로 바꾸고 가로가 max-width 픽셀을 넘으면 비율대로 줄인다(없으면 원본 바이트 그대로),
      figures.json · figures.md — 번호, 캡션(앞의 '그림 N' 뺀 글), 문서에 놓인 크기(mm), 원본 그림 항목, 들어 있던 최상위 문단 번호.
출력 그림은 원본과 같은 평문이다 — 원본과 같은 보안 등급으로 다룬다.
"""
import argparse
import io
import json
import re
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HWPUNIT_PER_MM = 283.465


class Refused(Exception):
    pass


def _local(tag):
    return tag.rsplit("}", 1)[-1]


def _kids(el, name):
    return [c for c in el if _local(c.tag) == name]


def _first(el, name):
    return next((c for c in el.iter() if _local(c.tag) == name), None)


def open_plain_hwpx(path):
    head = Path(path).read_bytes()[:16]
    if head.startswith(b"BMS DocuRay"):
        raise Refused("DocuRay DRM 문서다 — 그림을 꺼내지 않는다(우회 금지). 한/글 안에서 옮기는 방법이 필요하다")
    if not head.startswith(b"PK"):
        raise Refused("평문 HWPX(ZIP)가 아니다: 선두 %r" % head[:8])
    return zipfile.ZipFile(path)


def caption_text(cap):
    """캡션 안 글자 — <t> 글자와 자동 번호(autoNum num)를 순서대로 잇는다."""
    out = []
    for el in cap.iter():
        name = _local(el.tag)
        if name == "t":
            out.append("".join(el.itertext()))
        elif name == "autoNum":
            out.append(el.get("num") or "")
    return re.sub(r"\s+", " ", "".join(out)).strip()


def figures(z):
    """문서 순서의 그림 목록 → [{n, caption, label, item, width_mm, height_mm, section, para}]."""
    items = {}
    if "Contents/content.hpf" in z.namelist():
        for el in ET.fromstring(z.read("Contents/content.hpf")).iter():
            if _local(el.tag) == "item" and el.get("id") and el.get("href"):
                items[el.get("id")] = el.get("href")
    secs = sorted((n for n in z.namelist() if re.fullmatch(r"Contents/section\d+\.xml", n)),
                  key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
    out = []
    for si, name in enumerate(secs):
        root = ET.fromstring(z.read(name))
        for pi, p in enumerate(_kids(root, "p")):
            for pic in (e for e in p.iter() if _local(e.tag) == "pic"):
                img = _first(pic, "img")
                ref = img.get("binaryItemIDRef") if img is not None else None
                sz = next((c for c in pic if _local(c.tag) == "curSz"), None)
                cap = _first(pic, "caption")
                label = caption_text(cap) if cap is not None else ""
                out.append({"n": len(out) + 1, "label": label,
                            "caption": re.sub(r"^그림\s*\d+\s*", "", label).strip(),
                            "item": items.get(ref) or next((n for n in z.namelist() if n.startswith("BinData/%s." % ref)),
                                                           None),
                            "width_mm": round(int(sz.get("width")) / HWPUNIT_PER_MM, 1) if sz is not None else None,
                            "height_mm": round(int(sz.get("height")) / HWPUNIT_PER_MM, 1) if sz is not None else None,
                            "section": si, "para": pi})
    return out


def save_image(data, dest_stem, max_width):
    """그림 바이트 → 파일. Pillow 가 있으면 PNG(가로 max_width 이하), 없으면 원본 그대로. → 파일 경로, 픽셀 크기."""
    try:
        from PIL import Image
    except ImportError:
        return None, None
    im = Image.open(io.BytesIO(data))
    im.load()
    if im.mode not in ("RGB", "RGBA", "L"):
        im = im.convert("RGBA" if "A" in im.mode else "RGB")
    if max_width and im.width > max_width:
        im = im.resize((max_width, round(im.height * max_width / im.width)), Image.LANCZOS)
    dest = dest_stem.with_suffix(".png")
    im.save(dest, "PNG", optimize=True)
    return dest, [im.width, im.height]


def extract(src, out_dir, max_width=1600, log=print):
    z = open_plain_hwpx(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    figs = figures(z)
    for f in figs:
        if not f["item"]:
            f["file"] = None
            continue
        data = z.read(f["item"])
        stem = out_dir / ("fig%02d" % f["n"])
        dest, px = save_image(data, stem, max_width)
        if dest is None:
            dest = stem.with_suffix(Path(f["item"]).suffix)
            dest.write_bytes(data)
        f["file"], f["pixels"] = dest.name, px
    (out_dir / "figures.json").write_text(json.dumps({"source": str(src), "figures": figs}, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    md = ["# 그림 목록 — %s" % Path(src).name, "",
          "> 평문 원본에서 꺼낸 그림이다. 원본과 같은 보안 등급으로 다룬다.", "",
          "| # | 파일 | 캡션 | 크기(mm) | 원본 항목 | 문단 |", "|---|---|---|---|---|---|"]
    md += ["| %d | %s | %s | %s×%s | %s | s%d.p%d |" % (f["n"], f.get("file"), f["caption"], f["width_mm"], f["height_mm"],
                                                    f["item"], f["section"], f["para"]) for f in figs]
    (out_dir / "figures.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    log("그림 %d개 → %s" % (len(figs), out_dir))
    return figs


def main(argv=None):
    from _console import configure_console
    configure_console()
    ap = argparse.ArgumentParser(description="평문 HWPX 의 그림을 문서 순서대로 꺼낸다 (DRM 문서는 거절)")
    ap.add_argument("src")
    ap.add_argument("out_dir")
    ap.add_argument("--max-width", type=int, default=1600)
    args = ap.parse_args(argv)
    try:
        extract(args.src, args.out_dir, args.max_width)
    except Refused as e:
        print("거절: %s — DRM 문서는 hwpx_drm.py images(브리지 images)로 꺼낸다(D-062)" % e)
        return 2
    except (OSError, zipfile.BadZipFile, ET.ParseError) as e:
        print("오류: %s" % e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
