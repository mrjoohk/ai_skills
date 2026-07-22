#!/usr/bin/env python3
"""check_skill_sync.py — 스킬 사본 드리프트 검사 + 동기화 (P-8 대응).

정본(canon) 선언:
  - 모든 스킬의 정본은 all_skills/ 아래 카테고리 폴더 (우선순위 순서 참조)
  - .claude/skills/ 는 '설치본' — 정본에서 복사되어야 하며 직접 수정 금지
  - 파이프라인 폴더 간 공용 스킬 사본(req-elicitor 등)은 core 폴더가 정본

사용법:
  python scripts/check_skill_sync.py            # 검사만 (드리프트 리포트)
  python scripts/check_skill_sync.py --apply    # 정본 → 사본/설치본 동기화 실행

주의: context-engineering 은 파이프라인별로 의도적으로 다른 두 버전이 존재
(core=Claude 구현 체인, req_impl=코딩 에이전트 체인) — 동기화 대상에서 제외.
"""
import argparse
import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALL = ROOT / "all_skills"
INSTALLED = ROOT / ".claude" / "skills"

# 정본 탐색 우선순위 (같은 이름 스킬이 여러 폴더에 있으면 앞쪽이 정본)
CANON_PRIORITY = [
    "core-engineering_pipeline_skills",
    "specific_skills",
    "proposal_skills",
    "req_impl_review_pipeline_skills",
    "artifact_skills",
    "general_skills",
]

# 의도적 분기 — 동기화 제외 (사유 명시)
DIVERGENT_OK = {
    "context-engineering": "파이프라인별 의도적 분기 (core=Claude 구현 / req_impl=코딩 에이전트)",
}


def file_hash(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def dir_files(d: Path):
    return sorted(p for p in d.rglob("*") if p.is_file())


def dir_signature(d: Path):
    return {str(p.relative_to(d)): file_hash(p) for p in dir_files(d)}


def find_skills():
    """{skill_name: {category: dir_path}}"""
    skills = {}
    for cat in CANON_PRIORITY:
        cdir = ALL / cat
        if not cdir.is_dir():
            continue
        for sdir in sorted(cdir.iterdir()):
            if (sdir / "SKILL.md").is_file():
                skills.setdefault(sdir.name, {})[cat] = sdir
    return skills


def canon_of(copies: dict) -> Path:
    for cat in CANON_PRIORITY:
        if cat in copies:
            return copies[cat]
    raise RuntimeError("no canon")


def sync_dir(src: Path, dst: Path, apply: bool) -> bool:
    """src 내용을 dst로 복사(정확히 일치시킴). 반환: 차이 있었는지."""
    differs = dir_signature(src) != (dir_signature(dst) if dst.is_dir() else None)
    if differs and apply:
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    return differs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="정본 → 사본/설치본 복사 실행")
    args = ap.parse_args()

    skills = find_skills()
    drift_dup, drift_inst, skipped = [], [], []

    # 1) all_skills 내부 사본 드리프트
    for name, copies in skills.items():
        if len(copies) < 2:
            continue
        if name in DIVERGENT_OK:
            skipped.append((name, DIVERGENT_OK[name]))
            continue
        canon = canon_of(copies)
        for cat, d in copies.items():
            if d == canon:
                continue
            if sync_dir(canon, d, args.apply):
                drift_dup.append((name, cat, str(canon.relative_to(ROOT))))

    # 2) 설치본(.claude/skills) 드리프트
    if INSTALLED.is_dir():
        for name, copies in skills.items():
            canon = canon_of(copies)
            inst = INSTALLED / name
            if not inst.is_dir():
                drift_inst.append((name, "MISSING (미설치)", str(canon.relative_to(ROOT))))
                if args.apply:
                    shutil.copytree(canon, inst)
                continue
            if sync_dir(canon, inst, args.apply):
                drift_inst.append((name, "OUTDATED", str(canon.relative_to(ROOT))))
    else:
        print(f"[warn] 설치 폴더 없음: {INSTALLED}")

    # 리포트
    verb = "동기화됨" if args.apply else "드리프트 (검사만 — --apply 로 동기화)"
    print(f"\n== 폴더 간 사본 {verb}: {len(drift_dup)}건")
    for name, cat, canon in drift_dup:
        print(f"  - {name} @ {cat}  ← 정본: {canon}")
    print(f"\n== 설치본(.claude/skills) {verb}: {len(drift_inst)}건")
    for name, state, canon in drift_inst:
        print(f"  - {name} [{state}]  ← 정본: {canon}")
    print(f"\n== 의도적 분기(제외): {len(skipped)}건")
    for name, why in skipped:
        print(f"  - {name}: {why}")

    if not args.apply and (drift_dup or drift_inst):
        sys.exit(1)  # CI에서 드리프트를 실패로 처리 가능
    print("\nOK")


if __name__ == "__main__":
    main()
