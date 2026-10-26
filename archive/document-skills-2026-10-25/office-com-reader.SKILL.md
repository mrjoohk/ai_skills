---
name: office-com-reader
description: >-
  (drmHWP 프로젝트 수정본, MS Office 전용) Windows에서 openpyxl/python-docx/python-pptx로 열리지 않는 xlsx·docx·pptx(DocuRay DRM 컨테이너, 레거시 포맷)를 판독한다. 포맷을 먼저 감지해 평문이면 파이썬 라이브러리로, DRM이면 Python(pywin32)으로 Excel/Word/PowerPoint COM을 구동해 읽는다. MANDATORY TRIGGERS: "BadZipFile", "File is not a zip file", "엑셀이 안 열려", "xlsx를 못 읽어", "DRM 걸린 문서", "암호화된 엑셀", "DocuRay", "문서보안 때문에 안 읽혀", "COM으로 읽어줘", "시트 목록만 보여줘", "ICD 문서 분석".
---

# Office COM Reader (MS Office 전용, Python 우선)

파이썬 라이브러리가 읽지 못하는 MS Office 문서를, 그 문서를 여는 것이 이미 허용된
애플리케이션(Excel/Word/PowerPoint)에게 열게 하고 COM(pywin32)으로 값만 받아온다.

- 정본: `tools/office-com-reader/` (D-007). 원본 `reference/office-com-reader/` 는 기준선
- 구현: **`scripts/read_office_doc.py` (Python, pywin32)** — D-013. PowerShell 판은 D-014 로 삭제했다
  (원본 PS 스크립트는 `reference/` 에 기준선으로만 남는다)
- 한/글은 다루지 않는다 (다른 세션 소관)

## 0. 전제

- **보안통제를 깨지 않는다.** 암호를 풀지 않고 키를 꺼내지 않는다. 허용 앱이 아니면 실패하는 것이 정상이다.
- **기본은 아무 파일도 만들지 않는다.** `--log` 는 화면 출력을, `--dump` 는 문서 전문을 `.md` 로 남긴다(D-002).
  `--dump` 는 DRM 원본의 평문 사본이므로 다 쓰면 지운다. PDF/PNG 는 만들지 않는다(D-003).
- **사전 조건** (COM 판독 기준 — Linux 세션은 §0-1): Windows, MS Office, DocuRay 클라이언트 로그인, `python` + `pywin32`
  (`python -c "import win32com.client"` 가 되어야 한다. 없으면 `python -m pip install pywin32`).

## 0-1. 세션 환경 — 먼저 어느 쪽인지 확인한다

이 스킬의 COM 스크립트는 **Windows 전용**이다. 세션이 어디서 도는지에 따라 쓸 수 있는 것이 다르다.

판별: `python -c "import win32com.client"` 가 되면 Windows 세션. `ModuleNotFoundError` 이거나 `uname` 이 Linux 면 Linux 세션
(Cowork 클라우드 세션의 `device_bash` 는 사용자 PC 가 아니라 Linux VM 이다).

| 하려는 일 | Windows 세션 | Linux 세션 |
|---|---|---|
| 포맷 판정 `probe_format.py` | 가능 | **가능** (순수 파이썬) |
| 보호 여부 `verify_protection.py` | 가능 | **가능** (서명 바이트만 본다) |
| 평문 xlsx·docx·pptx 읽기 | 가능 | 가능 (openpyxl 등) |
| **DRM 문서 읽기** `read_office_doc.py` | 가능 | **불가** — pywin32 없음, 종료코드 3 |
| DRM 문서 평문 내용을 얻는 길 | COM 판독 | 아래 §0-2 (사용자가 내보내기) |

**Linux 마운트에서 DRM 파일은 암호문(`BMS DocuRay`)으로 보인다.** `BadZipFile`, 빈 표, 깨진 글자는 손상이나 암호 문제가
아니라 정상이다. `probe_format.py` 로 `drm_container` 를 확인하고 멈춘다. Linux 에서 복호화를 시도하지 않는다.

## 0-2. Linux 세션에서 DRM 문서 내용을 얻는 법 (검증된 길)

> **Linux 세션이면 `office-drm-bridge`(같은 `.claude/skills/` 아래)를 먼저 쓴다. 세션 판별·체크리스트는 `.claude/skills/office-drm-bridge/references/session_environment.md`.** 사용자가 워커를 켜 두면 이 절의 수동 절차 없이 요청 파일로 처리된다. 워커가 꺼져 있을 때만 아래 수동 절차를 쓴다.

에이전트가 직접 열 수 없으므로 **허용 앱을 쥔 사람**이 평문 형식으로 내보낸다.

1. 사용자가 Excel/Word/PowerPoint 로 문서를 열고 **DRM 이 걸리지 않는 확장자**로 저장한다
   (Excel: `XML 스프레드시트 2003(.xml)`·`CSV`, 그 밖에는 `.md`·`.json`). 확장자 기준이므로 `.xlsx` 등으로 저장하면 다시 보호된다.
2. 에이전트가 그 평문 파일을 Linux 에서 읽는다. XML 스프레드시트는 병합·서식·열 너비까지 복원된다.
3. **다 쓰면 평문 사본을 지운다.** 지울 권한이 없으면 지울 파일 목록을 사용자에게 알린다.

원칙: 이 길은 사용자가 DRM 해제본을 만드는 것이다. 문서 등급과 조직 보안 정책이 허용하는 범위에서만 요청한다.
열기암호 문서는 어떤 경로로도 에이전트가 암호를 입력하지 않는다 — 암호 창이 뜨면 취소하고 알린다.
화면 조작(computer use)으로 Excel 을 열어 읽는 방법도 있으나, 터미널은 클릭만 되고 입력이 안 되며 단계가 많아 비정기 용도에 한한다.

경로 대응: 연결 폴더는 Windows `K:\01.workspace\AI_workspace\hmumt_scheduler` ↔ Linux `$HOME/mnt/hmumt_scheduler`.

## 1. 포맷 먼저 — COM은 마지막 수단

```bat
python scripts\probe_format.py "<파일>"
```

`plain_ooxml` 이면 openpyxl / python-docx / python-pptx 로 바로 읽는다. `drm_container`(`BMS DocuRay`)면 §2.

## 2. COM 판독

```bat
rem 구조 + 미리보기 (파일 안 만듦)
python scripts\read_office_doc.py "C:\...\doc.xlsx" --log "C:\...\read.md"

rem 키워드 검색 — 위치와 문맥
python scripts\read_office_doc.py "C:\...\doc.xlsx" --pattern "헬기,모기체,Heli" --log "C:\...\search.md"

rem 문서 작성 자료로 쓸 전문 (.md, 평문 사본)
python scripts\read_office_doc.py "C:\...\doc.docx" --dump "C:\...\doc_full.md"
```

| 옵션 | 뜻 |
|---|---|
| `--pattern` | 쉼표 구분 키워드, 대소문자 무시. 한 텍스트에서 앞 키 하나만 센다 |
| `--sheet` | Excel. 이름 일부가 우선, 맞는 이름이 없고 숫자면 시트 순번. 0건이면 경고 |
| `--fill-merged` | Excel. 실제 병합 영역의 좌상단 값으로 채운다. 병합 있는 큰 시트에서 느리다 |
| `--preview` | 미리보기 줄 수 (기본 5) |
| `--max-rows` / `--max-cols` | 읽는 범위 상한 (기본 5000 / 200). 상한 안쪽만 COM 으로 가져온다 |
| `--log` | 화면 출력을 UTF-8 BOM `.md` 로도 남긴다. cmd `>` 리다이렉트 대신 쓴다 |
| `--dump` | 전문 `.md` — Excel 은 시트별 마크다운 표, Word 는 본문·표·머리글 등, PowerPoint 는 슬라이드별 텍스트·노트 |

**PowerPoint 파일은 PowerPoint 창을 모두 닫고 실행한다.** PowerPoint 는 단일 인스턴스라 화면에 창이
있으면 스크립트가 그 창에 붙었다가 함께 닫는다. 화면에 `PPTFrameClass` 창이 보이면 시작 전에 멈춘다(종료코드 1).
창 없이 남은 직전 자동화 프로세스는 막지 않는다.

## 3. 결과 해석

| 앱 | 요약 | 검색 좌표 |
|---|---|---|
| Excel | 시트 순번·이름·행×열·사용 범위(`C3:F5`) + 상단 행 | `시트!D5` — 시트 절대 주소, writer `--cell` 과 같은 표기 |
| Word | 제목 스타일 개요 + 본문 미리보기 + 본문 밖(머리글·바닥글·텍스트 상자·각주) | `본문 줄 N`(빈 줄 제외 순번) / `머리글`·`바닥글`·`텍스트 상자` … |
| PowerPoint | 슬라이드별 제목·텍스트 블록 수·노트 수 | `슬라이드 N` / `슬라이드 N 노트` |

- 날짜는 `2026-10-01`, 시각만 있는 셀은 `09:30:00`, 오류 셀은 `#N/A` 처럼 나온다.
- PowerPoint 도형은 위→아래, 왼→오른쪽(Top 10pt 단위)으로 정렬한다. 표·그룹·SmartArt·노트 포함.
  다이어그램의 의미(배치·연결선)는 텍스트로 복원되지 않는다.
- 잘랐으면 `… (N개 더)` 로 알린다. 0건이면 0건이라고 쓴다.

## 4. 실패했을 때

| 증상 | 원인 | 대응 |
|---|---|---|
| `FAILED: pywin32 가 없다` (종료코드 3) | pywin32 미설치 | `python -m pip install pywin32`. 설치가 안 되면 멈추고 알린다 |
| `FAILED: … corrupted and unreadable` | 파일 손상 (P-005 실사례) | 탐색기에서 직접 열어 본다 |
| `FAILED: … 암호 …` | 열기암호 파일 — 대화상자 대신 오류로 끝낸다 | 암호를 아는 사람이 해제 |
| 암호 입력 창이 뜬다 | PowerPoint 열기암호(암호 인자 없음, F-087) 또는 암호 인자가 앱에 닿지 않음(F-085 회귀) | 아무것도 입력하지 말고 취소, 알린다 |
| `FAILED` / 권한 오류 | 허용 앱 아님·열람 권한 없음 | 우회하지 않는다 |
| `중단: PowerPoint 창이 열려 있다` | 단일 인스턴스 보호 | PowerPoint 를 닫고 재실행 |
| 프로세스 누적 | 이전 실행이 강제 종료됨 | `taskkill /IM EXCEL.EXE /F` (`WINWORD.EXE`, `POWERPNT.EXE`) |

종료코드: 0 완료 / 1 실패·지원하지 않는 형식·PowerPoint 창 열림 / 3 pywin32 없음.

## 5. 보안 기본값

세 앱 모두 `AutomationSecurity = 3`(매크로 강제 차단), 읽기 전용으로 연다. Excel 은 이벤트·링크 갱신을 끄고,
Excel·Word 는 가짜 열기암호를 넘겨 암호 대화상자 대신 오류가 나게 한다. PowerPoint 는 `DisplayAlerts = ppAlertsNone`.

COM 메서드는 **자리 인자로만** 부른다. pywin32 늦은 바인딩은 이름 인자 사이에 빈 자리가 있으면 그 뒤를 말없이 버린다 —
`Password=` 가 Excel 에 닿지 않아 암호 창이 떴다 (F-085). 건너뛸 자리는 `OMIT` 으로 채운다. 스크립트를 고칠 때도 지킨다
(가짜 COM 시험 `com_positional_only` 가 검사한다).

## 6. 검증 이력

| 일자 | 판 | 확인 | 증거 |
|---|---|---|---|
| 2026-10-01 (P-005) | 원본 PS | 실문서 `BOM.xlsx`, DRM 합성 3종 판독. F-014·F-015·F-017 결함 확인 | `logs/P-003_evidence/` |
| 2026-10-02 (P-010 실측) | 수정 PS | 좌표·날짜·병합·머리글·`-Sheet` 순번 실측 통과, `발표자료.pptx` 137슬라이드 판독 | `logs/P-010_evidence/V*.md` |
| 2026-10-02 (P-014) | **Python** | 가짜 COM 시험 42건 + 결함 되돌림 변이 14건 전부 검출, 당일 무맥락 검토 반영 | `logs/P-014_evidence/static_tests_py.md` |
| 2026-10-02 (P-015) | **Python 실측** | 실문서 `BOM.xlsx`·`발표자료.pptx`(137슬라이드, PS 판과 출력 동일), 좌표·날짜·병합·머리글·시트 순번, PowerPoint 연속 실행(거짓 거부 없음), `--dump` .md 통과 | `logs/P-014_evidence/` |
| 2026-10-02 (P-019) | Python 재시험 | 열기암호 xlsx 에서 **암호 입력 창이 떴다**(F3) — 이름 인자 `Password=` 가 버려지는 F-085. docx 는 즉시 오류(F4)였으나 오류 문구의 CR 로 `FAILED:` 가 가려짐(F-086). 자리 인자·한 줄 오류로 수정, 가짜 시험 51건(음성대조 6건 실패 확인). **실측 재시험 대기** | `logs/P-015_evidence/`, `review_docs/261002_1240_office_com_pw_retest_result.md` |
| 2026-10-02 (P-021) | **Python 실측** | 열기암호 xlsx·docx 읽기 즉시 오류(창 없음), 오류 한 줄, 인자 전달 탐침(이름 인자 버려짐 재현·자리 인자 동작), DRM xlsx·docx 회귀, 실문서 `BOM.xlsx`(P-014 와 출력 동일), Excel 이 만든 xlsm·xlsb·xls 판독 통과 → F-049·F-085·F-086 verified. Excel 오류의 HTML 이스케이프(F-088) 수정. PowerShell 판 삭제(D-014) | `logs/P-019_evidence/live/` |
| 2026-10-16 (P-119) | Linux 세션 경로 | Linux VM 에서 `probe_format.py`·`verify_protection.py` 동작 확인, COM 불가 확인. 사용자가 Excel 에서 내보낸 XML 스프레드시트를 Linux 에서 파싱해 양식 구조 복원(§0-2) | `review_docs/261016_1400_office_com_linux_bridge_review.md` |

상세 함정: `references/pitfalls.md`
