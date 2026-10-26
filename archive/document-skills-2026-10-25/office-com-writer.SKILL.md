---
name: office-com-writer
description: >-
  (drmHWP 프로젝트 수정본, MS Office 전용) DocuRay DRM 환경에서 xlsx·docx·pptx를 Python(pywin32)으로 Excel/Word/PowerPoint COM을 구동해 만들고 고친다. 파이썬으로 만든 평문 산출물에 보호를 입히고(protect), DRM 템플릿의 플레이스홀더를 채우고(replace), 표 데이터를 시트에 써넣는다(fill). 저장 후 DocuRay 보호 여부를 스스로 판정한다. MANDATORY TRIGGERS: "DRM 때문에 저장이 안 돼", "문서를 못 고쳐", "템플릿 채워줘", "플레이스홀더 치환", "보고서 만들어서 저장해줘", "엑셀에 데이터 써넣어줘", "DRM 입혀줘", "보호 다시 걸어줘", "평문으로 저장됐어", "DocuRay 쓰기". 읽기는 office-com-reader 소관.
---

# Office COM Writer (MS Office 전용, Python 우선)

허용 앱(Excel/Word/PowerPoint)에게 저장을 시켜, 파이썬 라이브러리가 못 하는 두 가지를 한다 —
**DRM 문서 편집**과 **산출물에 보호 입히기**.

- 정본: `tools/office-com-writer/` (D-007). 원본 `reference/office-com-writer/` 는 기준선
- 구현: **`scripts/write_office_doc.py` (Python, pywin32)** — D-013. PowerShell 판은 D-014 로 삭제했다
  (원본 PS 스크립트는 `reference/` 에 기준선으로만 남는다)
- 한/글은 다루지 않는다 (다른 세션 소관)

## 0. 전제 — 쓰기는 되돌릴 수 없다

- **원본을 덮어쓰지 않는다.** `--out` 이 없으면 `<원본>_out.<확장자>`. 출력이 원본과 같으면 `--overwrite` 없이는 멈춘다
- **`--overwrite` 는 사용자가 명시했을 때만.** 그때도 `.bak` 을 먼저 만든다 (`--no-backup` 은 일회용 사본에만)
- **문서가 열려 있으면(`~$` 잠금 파일), PowerPoint 창이 떠 있으면 시작하지 않는다**
- **저장 후 DocuRay 보호 여부를 스크립트가 판정한다.** 보호되지 않았으면 종료코드 3
- `--out` 상대 경로는 현재 폴더 기준 절대 경로로 바꾼다
- 사전 조건 (COM 쓰기 기준 — Linux 세션은 §0-1): `python` + `pywin32` (없으면 `python -m pip install pywin32`)
- 열기암호 파일은 가짜 암호로 대화상자 대신 오류가 나게 한다. COM 메서드는 **자리 인자로만** 부른다 — 이름 인자 사이에
  빈 자리가 있으면 pywin32 가 그 뒤를 버린다 (F-085, `references/write-pitfalls.md`)

## 0-1. 세션 환경 — 먼저 어느 쪽인지 확인한다

이 스킬의 COM 스크립트는 **Windows 전용**이다 (`python -c "import win32com.client"` 로 판별. 읽기 스킬 §0-1 참조).

| 하려는 일 | Windows 세션 | Linux 세션 |
|---|---|---|
| 평문 xlsx·docx·pptx **만들기** (openpyxl 등) | 가능 | **가능** |
| 보호 입히기 `--mode protect` | 가능 | **불가** — Windows 에서 실행해야 한다 |
| 템플릿 채우기 `replace`·`fill` (DRM 템플릿) | 가능 | **불가** |
| 보호 여부 확인 `verify_protection.py` | 가능 | **가능** (서명 바이트만 본다) |

## 0-2. Linux 세션에서 DRM 산출물 만들기 (검증된 길)

> **Linux 세션이면 `office-drm-bridge`(같은 `.claude/skills/` 아래)를 먼저 쓴다. 세션 판별·체크리스트는 `.claude/skills/office-drm-bridge/references/session_environment.md`.** 사용자가 워커를 켜 두면 이 절의 수동 절차 없이 요청 파일로 처리된다. 워커가 꺼져 있을 때만 아래 수동 절차를 쓴다.

```
Linux: 평문 생성 → 검수/승인 → 사용자(Windows)가 cmd 에서 protect → Linux: verify_protection.py 로 확인 → 평문 사본 삭제
```

1. Linux 에서 openpyxl/python-docx/python-pptx 로 평문 산출물을 만들고 연결 폴더에 둔다.
2. 사용자가 Windows 명령 프롬프트에서 보호를 입힌다 (cmd 문법, `^` 줄바꿈):

```bat
python .claude\skills\office-com-writer\scripts\write_office_doc.py "K:\...\output_docs\X.xlsx" --mode protect ^
  --out "K:\...\output_docs\X_out.xlsx" --log "K:\...\output_docs\protect_log.md"
```

   `보호 확인: [보호됨] DocuRay 컨테이너` 가 나오면 성공(종료코드 0).
3. Linux 에서 `python3 .claude/skills/office-com-writer/scripts/verify_protection.py <결과>_out.xlsx` 로 `BMS DocuRay` 서명을 다시 확인한다.
4. **평문 원본은 DRM 밖의 사본이다.** 보호본을 확인한 뒤 지운다. 에이전트는 삭제 권한이 없으면 지울 파일을 알린다.

에이전트가 `protect` 를 대신 실행하려고 Windows 셸을 흉내 내거나 복호화·암호화를 시도하지 않는다.

## 1. 모드

| 상황 | 모드 |
|---|---|
| 파이썬으로 만든 문서에 DRM 을 입힌다 | `protect` |
| DRM 템플릿의 `{{항목}}` 자리를 채운다 | `replace` |
| CSV 표 데이터를 시트에 써넣는다 | `fill` (Excel 전용) |
| 문서를 처음부터 만든다 | python-docx / openpyxl / python-pptx 로 만들고 `protect` |

```bat
rem 평문 산출물에 보호 입히기
python scripts\write_office_doc.py "C:\...\보고서.docx" --mode protect --overwrite --log "C:\...\protect.md"

rem 템플릿 채우기
python scripts\write_office_doc.py "C:\...\양식.pptx" --mode replace --map "C:\...\map.md" ^
  --out "C:\...\결과.pptx" --log "C:\...\replace.md"

rem 시트에 데이터 써넣기 (양식에 머리글이 이미 있으면 --no-header)
python scripts\write_office_doc.py "C:\...\양식.xlsx" --mode fill --data "C:\...\data.md" ^
  --sheet "Input" --cell B3 --out "C:\...\결과.xlsx"
```

- 치환표(`--map`)는 **UTF-8 JSON 본문**이다. 확장자는 보지 않으므로 `.md` 에 넣어도 된다 (D-002).
  `{ "{{과제명}}": "헬리본 MUM-T", "{{일자}}": "2026-08-25" }`
- 데이터(`--data`)는 머리글 행이 있는 **CSV 본문**이다.

P-005 실측: 이 PC 의 DocuRay 는 **허용 앱이 저장한 평문 신규 파일에도 자동으로 보호를 건다**(U-3b).
DRM 문서를 새 경로로 저장해도 보호가 유지된다(U-3a).

## 2. 모드별 동작과 사각지대

| 앱 | replace 가 닿는 곳 | 닿지 않는 곳 |
|---|---|---|
| Excel | 모든 시트의 셀 값·수식. Excel `Find` 로 셀을 찾고 **파이썬에서 바꿔 써넣는다** | 차트 제목, 도형 안의 글자 |
| Word | 본문·표·머리글·바닥글(안의 텍스트 상자 포함)·각주·미주·메모·텍스트 상자. **값 길이 제한 없음** | SmartArt |
| PowerPoint | 텍스트 상자·표 셀·그룹 안 — **한 프레임 안의 모든 일치** | SmartArt |

- **Excel replace 는 `Range.Replace` 를 쓰지 않는다.** `Range.Replace` 는 바뀐 셀을 다시 입력처럼 해석해
  `{{코드}}`→`001` 이 숫자 1, `3-4` 가 날짜가 되고, 255자를 넘는 값은 실패한다 (F-048). 수식 셀은 `Formula` 로,
  나머지는 fill 과 같은 규칙으로 넣는다: 앞자리 0 없는 평범한 10진수만 숫자, 나머지는 텍스트
  (텍스트(@) 서식 셀은 그대로, 그 밖에는 `'` 접두 — `'` 는 셀 값에 남지 않는다).
- Word 는 `Find` 로 위치만 찾고 `Range.Text` 에 직접 넣는다 (`Find.Execute` ReplaceWith 255자 제한, F-003).
- PowerPoint `TextRange.Replace` 는 첫 일치만 바꾼다 — 바꾼 글자 뒤부터 다시 찾는다 (F-002).
- fill 은 새 시트를 **맨 뒤**에 만들고, 시트 이름은 대소문자를 구분하지 않는다.
- 저장 형식은 출력 확장자로 고른다 (`.xlsm`→52, `.docm`→13, `.pptm`→25 …).
- 같은 값에 키가 들어 있는 치환(`{{K}}`→`<{{K}}>`)은 연결된 머리글·병합된 표 셀에서 한 번 더 감싸질 수 있다 (F-058, 보류).

치환 뒤에는 **읽기 스킬로 다시 읽어** 남은 플레이스홀더가 0건인지 확인한다.

```bat
python ..\office-com-reader\scripts\read_office_doc.py "C:\...\결과.pptx" --pattern "{{" --log "C:\...\check.md"
```

## 3. 저장 후 보호 판정

```
보호 확인: [보호됨] DocuRay 컨테이너          → 종료코드 0
보호 확인: [평문 !!] 판정=plain|ole2|unknown   → 종료코드 3
```

`[평문 !!]` 이면 사용자에게 **반드시 알린다.** 여러 파일은 `python scripts\verify_protection.py <파일…>`
(`BMS DocuRay` 서명만 보호됨, 열기암호·모르는 서명은 판정불가로 종료코드 1).
전제: python.exe 가 DocuRay 허용 앱이 아니어서 암호문을 그대로 읽는다 (P-010 V9 로 확인).

## 4. 실패했을 때

| 증상 | 원인 | 대응 |
|---|---|---|
| `중단: 문서가 열려 있다` | `~$` 잠금 파일 | 문서를 닫고 재실행 |
| `중단: PowerPoint 창이 열려 있다` | 단일 인스턴스 보호 | PowerPoint 를 닫고 재실행 |
| `중단: 출력 경로가 원본과 같다` / `출력 파일이 이미 있다` | 덮어쓰기 방지 | 다른 `--out`, 또는 사용자 확인 후 `--overwrite` |
| `FAILED: … 저장할 수 없는 출력 확장자` | 앱과 출력 확장자 불일치 | `--out` 확장자 확인 |
| `FAILED: … 암호 …` | 열기암호 파일 (대화상자 대신 오류) | 암호를 아는 사람이 해제 후 재실행 |
| 암호 입력 창이 뜬다 | 암호 인자가 앱에 닿지 않음 (F-085 회귀) 또는 쓰기 예약 암호 (F-087) | 아무것도 입력하지 말고 취소, 알린다 |
| `FAILED` / 권한 오류 | 편집 권한 없음 | 우회하지 않는다 |
| `[평문 !!]`, 종료코드 3 | DRM 재적용 실패 | 사용자에게 알리고, 필요 없으면 삭제 |
| `FAILED: pywin32 가 없다`, 종료코드 3 | pywin32 미설치 | `python -m pip install pywin32`. 설치가 안 되면 멈추고 알린다 |

종료코드: 0 저장·보호 확인 / 1 실패·중단 / 3 보호 확인 실패 또는 pywin32 없음.
상세: `references/write-pitfalls.md`

## 5. 검증 이력

| 일자 | 판 | 확인 | 증거 |
|---|---|---|---|
| 2026-10-01 (P-005) | 원본 PS | protect·replace·fill 저장, 결과물 9/9 DocuRay. F-002·F-003·F-009 결함 확인 | `logs/P-003_evidence/` |
| 2026-10-02 (P-010 실측) | 수정 PS | Word 300자·머리글, Excel 건수·fill 형변환·시트 순서, 자체 보호 판정, 안전장치 통과 | `logs/P-010_evidence/V*.md` |
| 2026-10-02 (P-014) | **Python** | 가짜 COM 시험 42건 + 결함 되돌림 변이 14건 전부 검출, 당일 무맥락 검토 11건 반영 | `logs/P-014_evidence/static_tests_py.md` |
| 2026-10-02 (P-015) | **Python 실측** | protect·replace(PPT 전체·Word 300자·Excel `001` 유지)·자체 보호 판정·안전장치 통과, 결과물 8/8 DocuRay. fill 새 시트가 맨 앞에 생기는 F-060 발견 → `Move` 방식으로 수정, **F1·F2 재시험 대기** | `logs/P-014_evidence/`, `review_docs/261002_1055_office_com_python_live_result.md` |
| 2026-10-02 (P-019) | Python 재시험 | **fill 새 시트 맨 뒤 실측 통과**(F1·F2, F-060 verified). 열기암호 xlsx 에서 암호 창 — 원인은 이름 인자 `Password=` 가 버려지는 F-085 (`Cells.Find` 의 LookAt 등도 같은 이유로 잠복). 자리 인자 + `OMIT` 으로 수정, 가짜 시험 51건(음성대조 6건 실패). **실측 재시험 대기** | `logs/P-015_evidence/`, `review_docs/261002_1240_office_com_pw_retest_result.md` |
| 2026-10-02 (P-021) | **Python 실측** | 열기암호 xlsx·docx 쓰기 즉시 오류·출력 없음, DRM xlsx·docx 치환·재판독, Excel 로 xlsm·xlsb·xls 저장·보호 통과 → F-049·F-085·F-086 verified. F-088 수정. PowerShell 판 삭제(D-014) | `logs/P-019_evidence/live/` |
| 2026-10-16 (P-119) | Linux 세션 경로 | openpyxl 로 만든 평문 xlsx 를 사용자가 cmd 로 `protect` → `[보호됨] DocuRay 컨테이너`(종료코드 0), Linux `verify_protection.py` 가 `BMS DocuRay` 서명 확인 (§0-2) | `output_docs/protect_log.md` |

## 6. 마무리 체크

- 어떤 파일이 어디에 만들어졌는지 (원본은 그대로인지)
- "보호 확인" 줄 — 보호됨인지 평문인지
- replace 였다면 읽기 스킬로 검산했는지
- `.bak` 을 만들었다면 그 경로와, 확인 후 지워도 된다는 안내
