# 쓰기 — 채우기·바꾸기·저장

## 어느 방법인가

| 문서 상태 | 방법 | 검증 |
|---|---|---|
| 채울 자리에 누름틀·셀 필드가 있다 (`fields` 표에 이름이 보인다) | `fill` | 같은 이름의 필드를 모두 다시 읽어 값 비교 |
| 필드는 없고 자리표시 글자(`{{과제명}}`, `○○○`)가 있다 | `replace` | 전·후 건수를 모든 위치에서 셈 |
| 둘 다 없다 | 범위 밖 | 사용자에게 알린다 (Phase 2: 필드 심기·행 추가) |

## 값 파일 (`--map`)

```json
{"과제명": "OOO 개발", "책임자": "홍길동", "개요": "첫 줄\n둘째 줄"}
```

- `.json` 또는 ```` ```json ```` 블록이 든 `.md`(블록 여러 개면 합침). UTF-8(BOM 허용)
- 값은 문자열. 숫자는 적힌 그대로 문자열이 된다(`1.10` → "1.10"). 참/거짓·중복 키·중첩 객체·`0x02` 문자는 오류(종료코드 2)
- fill 값의 `\n`은 문단 나눔으로 넣는다(한/글에는 `\r\n`으로 전달). replace 값에는 줄바꿈을 쓸 수 없다(아래)

## fill

```bat
python scripts\hwpx_drm.py fill "C:\...\양식.hwpx" --map "C:\...\값.md" [--out "C:\...\결과.hwpx"] [--force | --overwrite]
```

1. 키마다 `FieldExist` — 없는 키는 넣지 않고 `없는 필드`로 보고 (`PutFieldText`는 없는 이름을 **조용히 무시**한다, C12)
2. 있는 키를 한 번에 `PutFieldText` — 이름만 주면 **같은 이름의 필드 모두**에 같은 값이 들어간다
3. `GetFieldList(1,0)`로 `이름{{n}}`을 모두 구해 `GetFieldText`로 하나씩 다시 읽어 값 비교 → `불일치`
4. 저장(아래) 후 저장본을 다시 열어 한 번 더 비교 → 결과의 `after_reopen_mismatch`
5. 없는 키·불일치가 하나라도 있으면 종료코드 1 (채운 것은 저장된다 — 원본은 그대로)

글자 모양은 필드에 지정된 모양을 따른다(매뉴얼).

## replace

```bat
python scripts\hwpx_drm.py replace "C:\...\문서.hwpx" --map "C:\...\바꿀말.md"
```

0. 값 파일 검사 — 값 안에 **다른 키**가 있으면 연쇄 치환이 되므로 거부(2). 키·값에 줄바꿈이 있으면 거부(2, AllReplace의 줄바꿈 처리 미실측 — 여러 줄은 fill로)
1. 바꾸기 전 HWPML을 읽어 키마다 **모든 위치**(본문·셀·중첩 셀·머리말·꼬리말·각주·메모·글상자·캡션) 건수를 센다
2. **긴 키부터** `AllReplace` 1회씩 — `○○○`와 `○○○○`가 함께 있으면 `○○○○`를 먼저 바꾼다(짧은 키가 긴 키를 갉아먹지 않게). 0건 키는 부르지 않고 `(문서에 없음)` 경고
   - 찾기 조건은 모두 명시한다: 대소문자 구별, 정규식·아무개 문자·온전한 낱말·자소·여러 단어 끔, 확인창 없음, 문서 전체
   - 짧은 키의 `전` 건수에는 긴 키 안에 들어 있던 것도 세어진다
3. 다시 읽어 센다. 값 안에 자기 키가 들어 있는 경우(`{{A}}`→`x{{A}}`)는 기대 건수로 맞춰 본다
4. 기대보다 많이 남은 위치를 `남음 n: s0.hd0, …`로 보고하고 종료코드 1
5. 바뀐 것이 하나도 없으면 저장하지 않는다(종료코드 1)

`AllReplace`가 바꾸는 범위 (실측 E4, 한/글 13.0, 합성 DRM 문서 — `logs/P-017_evidence/E_summary.md`):

| 위치 | AllReplace 적용 |
|---|---|
| 본문 문단 | 바뀜 |
| 표 셀 · 중첩 표 셀 | 바뀜 |
| 머리말 · 꼬리말 | 바뀜 |
| 각주 | 바뀜 |
| 메모 내용 | **바뀜** — 메모(검토 의견 등) 안 같은 글자도 바뀐다 |
| 누름틀 안 글자 | 바뀜 (필드 값이 바뀐다) |
| 글상자 · 캡션 | 미실측 |

자리표시는 문서의 다른 곳(메모·안내문)에 없을 고유한 글자로 쓴다(예: `{{과제명}}`). `replace` 결과의 위치 ID로 바뀐 곳을 확인할 수 있다.

## 저장 정책 (fill·replace 공통)

| 옵션 | 출력 | 기존 파일 |
|---|---|---|
| (없음) | `<원본>_out.hwpx` (원본 옆) | 있으면 중단(2) |
| `--out <파일>` | 그 파일 | 있으면 중단(2) |
| `--force` | 위와 같음 | 지우고 저장 (덮어쓰기 대화상자 방지) |
| `--overwrite` | 원본 자리 | 먼저 `<원본>.bak` 복사(이미 있으면 시각 붙인 이름) → 임시 파일에 저장 → **보호(DOCURAY)·다시 열기·값 재확인이 모두 통과할 때만** 원본 자리로 교체. 하나라도 실패하면 원본은 그대로 두고 임시 파일·`.bak` 경로를 알린다 |

저장 순서: `SaveAs(경로, 'HWPX', '')` 반환 True 확인 → 출력 선두 판정(`BMS DocuRay`가 아니면 **종료코드 3**) →
문서 닫고 `Open(출력, 'HWPX')`로 다시 열기 → (fill) 값 재확인 → 닫기. `--out` 저장이면 원본 해시가 그대로인지도 본다.

- 출력은 항상 `.hwpx` 이름이다. `.hwp` 원본은 `--overwrite` 할 수 없다(이름만 hwp인 HWPX가 된다) — 기본 출력 `<이름>_out.hwpx`를 쓴다
- 한/글이 저장한 파일에는 DocuRay가 자동 적용된다(실측 C9). 평문이 나오면 그 파일을 쓰지 말고 사용자에게 알린다
- 저장 뒤 세션의 문서는 닫힌다. 이어서 더 고치려면 출력 파일을 다시 연다

## 사각지대·주의

- 표 줄 추가, 빈 칸에 필드 심기, 서식 변경, 그림 넣기 — 범위 밖(Phase 2)
- 같은 이름 필드에 **서로 다른 값**을 넣으려면 키를 `이름{{0}}`, `이름{{1}}`로 준다(매뉴얼 형식 — `FieldExist`가 이 형식을 받는지는 미실측). 재확인은 그 필드만
- 자리표시가 문단 경계를 넘으면(중간에 줄바꿈) 찾지 못한다
- 한/글이 이미 떠 있으면 시작하지 않는다(2). `--allow-running`은 사용자가 확인했을 때만 — 그때는 시간초과 감시가 꺼질 수 있다

## 파이썬 API

```python
from hwpx_api import HwpxSession, load_map
with HwpxSession(timeout=180) as s:
    s.open(r"C:\...\양식.hwpx")
    r = s.fill(load_map(r"C:\...\값.md"))      # {"filled":[...], "missing":[...], "mismatch":[...]}
    rec = s.save(verify_fields={k: v for k, v in load_map(r"C:\...\값.md").items() if k in r["filled"]})
    # rec: {"out", "head", "protected", "reopen", "after_reopen_mismatch", "source_unchanged"}
```

예외: `PreconditionError`(2) `OpenFailed`(4) `TimeoutKilled`(5) `ComUnavailable`(6) `MapError`(2) `SaveFailed`(1) `PlaintextSaved`(3, `.rec`에 저장 기록) `EditFailed`(1).

API 전용 편집(명령 없음): `s.delete_before(루트 문단 번호)` — 본문 처음부터 그 문단 앞까지 지운다(양식 앞쪽 작성방법 표지 걷어내기, 목표 2).
루트 문단 번호는 구역을 이어 센다(실측 P-022). 남는 첫 문단은 지운 첫 문단의 그릇(스타일·머리말 등 조판 개체)에 끝 문단의 글자가
붙은 것이고, 끝 문단의 조판 개체는 사라진다(F-095) — 다음 구역 첫 문단을 끝으로 잡으면 그 구역 정의·꼬리말이 없어진다.
`s.clear_paras(처음, 끝)` — 두 문단 사이(포함)의 글자를 지우고 빈 문단 하나를 남긴다(다음 문단은 그대로). `s.delete_to_end(처음)` — 그 문단부터 문서 끝까지.
둘 다 실측 통과(P-024 2차 실행 — 공통 템플릿 목차 비우기·본문 지우기). 어느 것이든 지운 뒤 `s.model(refresh=True)` 로 첫 블록·남은 문단 수(`stats.section_paras` 합)·머리말·꼬리말을 확인하고, 어긋나면 저장하지 않는다.

캐럿 편집 — 실측 P-025 PoC(`tools/test_hwpx/hwpx_template_poc.py` → `_drmtest/template_poc/poc_report.md`). 지금은 템플릿 생성기
(`tools/doc-templates/build_templates.py` 서식 단계)에만 있고 API·명령은 없다. 바꾼 뒤에는 늘 HWPML 로 '바꾸기로 한 것만 바뀌었는지' 확인한다.

| 할 일 | 동작 | 실측 |
|---|---|---|
| 문단 앞 n 글자 지우기 | `MovePos(0,루트,0)` → `MovePos(7,0,0)`(문단 끝) → `MoveLeft`×(뒤 글자 수) → `MoveSelLeft`×n → `Delete` | S3·S4 통과 — 문단 앞에 조판 개체(구역 정의·머리말)가 있어도 된다. 지울 범위 **뒤**에 개체(책갈피 등)가 있으면 캐럿 칸 수가 달라질 수 있어(미실측) 모델의 `marks` 로 피한다 |
| 문단 스타일 | `Style` 동작 `Apply` = STYLE Id (`styledefs[].id`) | S3 |
| 문단 오른쪽 정렬 | `MovePos(0,루트,0)` → `MoveSelParaEnd` → `ParagraphShapeAlignRight` → `Cancel` | S4 |
| 다른 문서의 스타일 들이기 | 문서 끝 `MoveDocEnd`·`BreakPara` → `InsertFile`(KeepStyle=0, KeepSection=0) → 새 문단부터 `delete_to_end` → 앞 문단 끝에서 `MoveSelDocEnd`+`Delete` | S1 — 넣는 내용이 **쓰는** 스타일만 들어온다. 같은 이름은 이 문서 정의를 유지(KeepStyle=1 이면 '바탕글 사본1' 이 생긴다). 지운 뒤 글자·머리말·꼬리말·조판 개체·구역·그림 데이터·문서 정보가 그대로 |
| 쪽 번호 위치 끄기 | `HeadCtrl`→`Next` 에서 CtrlID `pgnp`, 루트 번호 `GetAnchorPos(2).Item("Para")` → `Properties` 를 받아 `DrawPos=0` 으로 다시 대입 | S5 |
| 개요 번호 글자 읽기 | `GetHeadingString()` (캐럿 문단) | 미실측 — P-025 빌드에서 처음 쓴다 |
| 다른 문서를 바탕으로 쓰기(전부 지우고 끼워 넣기) | `SelectAll`+`Delete` → `InsertFile` | S2 **실패** — 지워지지 않은 문단·조판 개체가 남고 문서 정보가 바탕 문서 것이 된다. 쓰지 않는다 |
