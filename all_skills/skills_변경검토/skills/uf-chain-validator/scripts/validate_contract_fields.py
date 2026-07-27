#!/usr/bin/env python3
"""
validate_contract_fields.py — Gate 1 기계화: IF 계약 struct 필드 ↔ 코드 타입 선언 대조 (2026-07-27)

설계 문서의 계약 필드 열거(예: if_list.md `state: struct, {pos ECEF m, ...}`)가 코드의 대응
struct 선언에 필드 단위로 존재하는지 검사한다 (언어 불문 텍스트 대조).
새 IF 계약을 검증하려면 CONTRACTS 표에 매핑·별칭을 등록한다.

Usage: python validate_contract_fields.py [repo_root]
Exit:  0 전건 충족 / 1 누락 필드 존재
"""
import re
import sys
from pathlib import Path

CONTRACTS = [
    {
        "id": "IF-01.state",
        "doc": "rd/if_list.md",
        "doc_pattern": r"state:\s*struct,\s*\{([^}]*)\}",
        "code": "include/hfsim/types.hpp",
        "code_struct": "State",
        # 계약 필드 첫 토큰 → 코드 필드 별칭(하나라도 있으면 충족)
        "aliases": {
            "pos": ["pos_ecef"],
            "vel": ["vel_ned"],
            "att": ["att"],
            "rate": ["rate_body", "rate"],
            "mach": ["mach"],
            "aoa": ["aoa"],
        },
    },
]


def struct_body(text: str, name: str) -> str:
    m = re.search(rf"struct\s+{name}\s*\{{", text)
    if not m:
        return ""
    i, depth, j = m.end(), 1, m.end()
    while j < len(text) and depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[i:j]


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    fail = 0
    for c in CONTRACTS:
        doc_text = (root / c["doc"]).read_text(encoding="utf-8")
        m = re.search(c["doc_pattern"], doc_text)
        if not m:
            print(f"[{c['id']}] FAIL — 계약 패턴을 {c['doc']}에서 찾지 못함")
            fail = 1
            continue
        fields = [f.strip().split()[0].rstrip(",") for f in m.group(1).split(",") if f.strip()]
        body = struct_body((root / c["code"]).read_text(encoding="utf-8"), c["code_struct"])
        if not body:
            print(f"[{c['id']}] FAIL — struct {c['code_struct']} 를 {c['code']}에서 찾지 못함")
            fail = 1
            continue
        missing = []
        for f in fields:
            aliases = c["aliases"].get(f, [f])
            if not any(re.search(rf"\b{re.escape(a)}\b", body) for a in aliases):
                missing.append(f"{f} (별칭 {aliases})")
        if missing:
            print(f"[{c['id']}] FAIL — 계약 {len(fields)}필드 중 누락: " + ", ".join(missing))
            fail = 1
        else:
            print(f"[{c['id']}] OK — 계약 {len(fields)}필드 전부 {c['code']}::{c['code_struct']}에 존재")
    sys.exit(fail)


if __name__ == "__main__":
    main()
