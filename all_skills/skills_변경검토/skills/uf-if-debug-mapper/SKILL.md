---
name: uf-if-debug-mapper
description: "Maps UF/IF issues to code locations and generates a human-in-the-loop debugging plan."
user-invocable: true
allowed-tools: Read, Write
---

# UF/IF Debug Mapper

UF/IF 설계 기반으로 **어디를 디버깅해야 하는지**를 매핑하고, 구조적 트리아지 플랜을 생성하는 human-in-the-loop 스킬.

---

## Stop-the-Line Rule

오류/실패 발생 시 즉시 적용:

```
1. STOP  — 새 기능 추가 중단, 추측으로 변경하지 말 것
2. SAVE  — 에러 출력, 로그, 재현 단계를 먼저 보존
3. TRIAGE — 아래 5단계 체크리스트 순서대로 진행
4. FIX   — 근본 원인을 수정 (증상만 수정 금지)
5. GUARD — 재발 방지 테스트 추가 후 재개
```

**버그를 알고 있다고 생각해도 재현 먼저.** 추측 수정의 성공률은 70%. 나머지 30%는 더 많은 시간을 낭비한다.

---

## When to Use
- UF-chain/IF-layer 설계 완료 후 구현 전 디버깅 가이드가 필요할 때
- CI 실패/회귀 발생 시 "어디를 볼 것인지" 빠른 맵이 필요할 때
- 런타임 증상(OOM, 단위 오류, 루프 불안정, 네트워크 오류)에 대해 재현 가능한 트리아지 플랜이 필요할 때

## Inputs
- UF 목록 (예: UF-01..UF-27) 및/또는 IF 목록
- 모듈 레이아웃 (최상위 디렉토리)
- 에러 로그 / 스택 트레이스 (선택, 있으면 크게 도움)
- 런타임 제약 (예: 120 Hz 루프, VRAM ≤ 18GB)

---

## 5단계 트리아지 체크리스트

순서대로 진행. 단계를 건너뛰지 말 것.

### Step 1 — Reproduce (재현)

실패를 안정적으로 재현한다. 재현이 안 되면 수정 확신도 없다.

```
재현 가능?
├── YES → Step 2로
└── NO
    ├── 타이밍 의존? → 로그에 타임스탬프 추가, 지연 삽입으로 레이스 윈도우 확대
    ├── 환경 의존?  → 환경변수, 라이브러리 버전, 데이터 상태 비교
    ├── 상태 의존?  → 전역 변수/캐시/싱글톤 공유 여부 점검
    └── 랜덤 발생?  → 의심 위치에 방어 로그 추가 후 재발 대기
```

```bash
pytest tests/ -k "<failing_test>" -v          # 특정 테스트만 실행
pytest tests/ -k "<failing_test>" --runInBand  # 격리 실행 (순서 오염 배제)
```

### Step 2 — Localize (위치 특정)

UF/IF 체인에서 실패가 발생하는 레이어를 좁힌다.

```
어느 레이어?
├── UF 내부 로직  → UF 단위 테스트 실행, 입력/출력 타입 체크
├── UF→UF 경계  → I/O 계약 연속성 확인 (타입·형태·단위 불일치)
├── IF 통합 레이어 → IF-chain 테스트 실행, IF-acceptance 테스트 확인
├── 외부 의존성   → 연결성, API 변경, 속도 제한 점검
└── 테스트 자체   → 테스트가 잘못된 것은 아닌지 (false negative 가능성)
```

UF→Code 매핑 테이블로 실패 지점의 파일·함수 경로를 식별한다.

### Step 3 — Reduce (최소화)

최소 재현 케이스를 만든다:
- 관련 없는 코드/설정 제거
- 실패를 유발하는 최소 입력으로 축소
- 증상이 아닌 원인이 드러나도록 단순화

최소 재현 케이스가 있으면 근본 원인이 명확해진다.

### Step 4 — Fix Root Cause (근본 원인 수정)

**증상이 아닌 원인을 수정한다.**

```
증상 수정 (잘못된 방법):
  출력 값이 2배로 나옴 → 출력에서 /2 처리

근본 원인 수정 (올바른 방법):
  정규화 UF에서 스케일 팩터가 누적 적용됨 → UF 내부 로직 수정
```

"왜 이런 일이 발생했는가?"를 근본 원인에 도달할 때까지 반복해서 물어본다.

### Step 5 — Guard (재발 방지)

이 실패를 잡는 테스트를 추가한다:

```python
# 버그: UF-07에서 특정 입력 범위 밖의 값이 클램핑되지 않았음
def test_uf_07_clamp_out_of_range():
    result = uf_07_clamp(np.array([2.5, -0.3]))  # 범위 [0, 1] 초과
    assert np.all(result >= 0.0) and np.all(result <= 1.0)
```

이 테스트는 수정 전 FAIL, 수정 후 PASS여야 한다. 통과 후 uf-chain-validator 재실행.

---

## Output

`docs/uf_if_debug_map.md`를 생성한다. 포함 내용:

1. **UF→Code Mapping** — UF-ID별 파일 경로 + 함수 심볼
2. **IF→Code Mapping** — IF-ID별 통합 모듈 경로
3. **Symptom→Root Cause Table** — 증상별 가능한 근본 원인 (UF/IF 위치 포함)
4. **Debug Playbooks** — 단계별 실행 커맨드, 중단점, 로그 추가 지점
5. **Minimal-Fix Patterns** — 최소 diff 형태의 수정 제안
6. **Evidence Outputs** — 수집해야 할 리포트·로그·플롯 경로

## Token Saving Rules
- **path+symbol** 참조 우선 (예: `src/sar/bp.py::backproject()`). 전체 파일 붙여넣기 금지.
- 전체 로그는 `reports/`에 저장, 요약만 문서에 기록.
- 수정 제안은 diff 형태로 제공.

## MCP Integration (Optional)
- `mcp.filesystem`: 레포 구조 스캔 + 매핑 문서 생성
- `mcp.shell`: 재현 커맨드, 테스트, 최소 벤치마크 실행
- `mcp.github`: 이슈 생성, PR에 디버그 맵 코멘트

## Agent Orchestration
- **Agent-1 (Architect):** UF/IF 명세 + 레포 트리 기반 매핑 문서 생성/갱신
- **Agent-2 (Builder):** 매핑된 위치에 최소 수정 구현
- **Agent-3 (Verifier):** 테스트 + 증거 추가, CI 검증

See `references/reference.md` for the exact document template and `references/examples.md` for test prompts.
