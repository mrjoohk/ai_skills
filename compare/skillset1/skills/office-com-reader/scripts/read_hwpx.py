#!/usr/bin/env python3
"""HWPX(한/글 2014+, OWPML) 문서를 COM 없이 읽는다.

HWPX 는 ZIP 컨테이너이므로 DRM 만 걸려 있지 않으면 파이썬으로 바로 읽힌다.
DRM 이 걸려 있으면 probe_format.py 가 drm_container 로 판정하며, 그때는
Read-OfficeDoc.ps1 (한/글 COM) 로 가야 한다.

    python read_hwpx.py <파일>                     # 구조 + 미리보기
    python read_hwpx.py <파일> --pattern 헬기,모기체  # 키워드 검색
    python read_hwpx.py <파일> --dump out.txt       # 전문 (평문 파일이 남는다)

네임스페이스 접두사(hp:, hs: …)는 한/글 버전마다 달라질 수 있으므로
로컬명으로만 매칭한다.
"""
import argparse
import re
import sys
import zipfile
import xml.etree.ElementTree as ET


def local(tag):
    """'{ns}p' -> 'p'."""
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _runs(el, skip_tables=True):
    """el 아래 <t> 런의 텍스트를 모은다. 기본적으로 표 내부는 건너뛴다."""
    out = []

    def rec(node):
        for child in node:
            name = local(child.tag)
            if skip_tables and name == "tbl":
                continue
            if name == "t":
                out.append("".join(child.itertext()))
            else:
                rec(child)

    rec(el)
    return "".join(out)


def _cell_text(tc):
    return " ".join(_runs(tc, skip_tables=False).split())


def _parse_table(tbl):
    rows = []
    for tr in tbl.iter():
        if local(tr.tag) != "tr":
            continue
        cells = [_cell_text(tc) for tc in tr if local(tc.tag) == "tc"]
        if cells:
            rows.append(cells)
    return rows


def _walk(el, blocks):
    """문서 순서대로 ('para', 문자열) / ('table', 행리스트) 를 수집한다."""
    for child in el:
        name = local(child.tag)
        if name == "tbl":
            blocks.append(("table", _parse_table(child)))
        elif name == "p":
            text = _runs(child).strip()
            if text:
                blocks.append(("para", text))
            _tables_only(child, blocks)
        else:
            _walk(child, blocks)


def _tables_only(el, blocks):
    for child in el:
        if local(child.tag) == "tbl":
            blocks.append(("table", _parse_table(child)))
        else:
            _tables_only(child, blocks)


def _section_key(name):
    m = re.search(r"section(\d+)", name)
    return int(m.group(1)) if m else 0


def read(path):
    """[(구역명, [블록…])] 반환."""
    with zipfile.ZipFile(path) as z:
        names = sorted(
            (n for n in z.namelist() if re.search(r"Contents/section\d+\.xml$", n)),
            key=_section_key,
        )
        if not names:
            raise SystemExit(
                "Contents/section*.xml 이 없다 — HWPX 가 아니거나 구조가 다르다.\n"
                "probe_format.py 로 포맷을 먼저 확인한다."
            )
        sections = []
        for name in names:
            root = ET.fromstring(z.read(name))
            blocks = []
            _walk(root, blocks)
            sections.append((name, blocks))
        return sections


def render(blocks):
    lines = []
    for kind, payload in blocks:
        if kind == "para":
            lines.append(payload)
        else:
            for row in payload:
                lines.append(" | ".join(row))
            lines.append("")
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description="HWPX 판독")
    ap.add_argument("path")
    ap.add_argument("--pattern", help="쉼표로 구분한 키워드 (대소문자 무시)")
    ap.add_argument("--dump", metavar="OUT", help="전문을 UTF-8 텍스트로 저장 (평문이 남는다)")
    ap.add_argument("--preview", type=int, default=15, help="구역별 미리보기 줄 수")
    args = ap.parse_args(argv)

    sections = read(args.path)

    total_p = sum(sum(1 for k, _ in b if k == "para") for _, b in sections)
    total_t = sum(sum(1 for k, _ in b if k == "table") for _, b in sections)
    print(f"{args.path}")
    print(f"  구역 {len(sections)}개 · 문단 {total_p}개 · 표 {total_t}개\n")

    if args.pattern:
        keys = [k.strip() for k in args.pattern.split(",") if k.strip()]
        hits = 0
        for name, blocks in sections:
            for i, (kind, payload) in enumerate(blocks):
                texts = [payload] if kind == "para" else [
                    " | ".join(r) for r in payload
                ]
                for j, text in enumerate(texts):
                    for key in keys:
                        if key.lower() in text.lower():
                            where = f"{name}#{i}" + (f".{j}" if kind == "table" else "")
                            snip = " ".join(text.split())[:120]
                            print(f"  [{key}] {where}  {snip}")
                            hits += 1
                            break
        print(f"\n총 {hits}건 매칭")
        return 0

    for name, blocks in sections:
        print(f"--- {name} ---")
        for line in render(blocks)[: args.preview]:
            print(f"  {line}")
        if len(render(blocks)) > args.preview:
            print(f"  … ({len(render(blocks)) - args.preview}줄 더)")
        print()

    if args.dump:
        with open(args.dump, "w", encoding="utf-8") as f:
            for name, blocks in sections:
                f.write(f"===== {name} =====\n")
                f.write("\n".join(render(blocks)))
                f.write("\n\n")
        print(f"평문 저장: {args.dump}  ← DRM 이 걸려 있던 문서라면 취급에 주의한다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
