---
name: hwpx-drm
description: >-
  DocuRay DRM이 걸린 한/글 문서(.hwpx·.hwp)를 한/글(Hwp.exe) COM으로 열어 표·병합·필드·메모까지 읽어 .md로 남기고, 누름틀·셀 필드를 채우거나 자리표시를 바꿔 DRM이 유지된 .hwpx로 저장한다. 문서에 포함된 그림은 허용된 범위에서 평문 파일로 추출할 수 있다. Windows + 한컴오피스 + pywin32. MANDATORY TRIGGERS: "hwpx 읽어줘", "한글 문서 분석", "한/글 파일 열어줘", "DRM hwpx", "DocuRay hwpx", "hwpx가 안 열려", "BadZipFile hwpx", "템플릿 채워줘", "누름틀", "hwpx 수정", "한글 표 읽어줘", "계획서 양식 분석". Linux(Cowork) 세션에서는 직접 실행할 수 없고 office-drm-bridge 워커로 호출한다(§0-1).
---

# hwpx-drm — DRM 한/글 문서 읽기·쓰기

DRM 문서는 허용된 앱(한/글)만 연다. 이 스킬은 한/글에게 열게 하고(COM), 한/글이 내주는 문서 XML(HWPML)로
구조를 읽는다. 파이썬은 문서 파일 바이트를 직접 읽지 않는다(선두 16바이트 보호 판정 제외).

## 0. 전제 — 어기면 멈춘다

- **보안통제를 깨지 않는다.** 복호화·키 추출·우회 금지. 열기 실패(종료코드 4)는 권한 문제로 보고하고 끝낸다.
- **원본은 그대로 둔다.** 쓰기 결과는 `<원본>_out.hwpx`. 덮어쓰기는 사용자가 원할 때만 `--overwrite`(`.bak` 자동).
- **읽기 결과는 항상 `.md`로 남는다**(`--md-dir`, 기본 `hwpx_md\`). 이 .md는 **DRM 보호를 받지 않는 평문**이다 —
  원본과 같은 등급으로 다루고 밖으로 보내지 않는다. 사용자에게 어디에 남았는지 알린다.
- `images`는 평문 그림과 목록을 새 출력 폴더에 만든다. 원본 프로젝트의 과거 그림 추출 승인(D-062)을 현재 프로젝트의 승인으로 재사용하지 않는다. 현재 대화에서 허용된 범위를 확인한다.
- **한/글 창을 모두 닫고** 실행한다. 떠 있으면 종료코드 2(사용자가 편집 중인 문서를 보호). 사용자의 한/글을 죽이지 않는다.
- 준비 확인: `python -c "import win32com.client"` 성공 + 보안승인 모듈 등록(안 하면 열기·저장마다
  '접근 허용' 창이 떠 무인 실행이 멈춘다 — 프로젝트의 `tools\test_hwpx\3.setup_hwp_security_module.bat` 1회).

## 0-1. 세션 환경 — Linux 세션이면 브리지로 호출한다

이 스킬의 스크립트는 **Windows + 한/글 + pywin32** 에서만 돈다. `python -c "import win32com.client"` 가 안 되거나 `uname` 이 Linux 면
Linux 세션이다(Cowork 클라우드 세션의 `device_bash` 도 Linux VM). 그때는 **직접 실행하지 말고 `office-drm-bridge` 로 호출한다.**

- **필수 안내**: 설치된 `office-drm-bridge`의 `references/session_environment.md` — 세션 판별, 시작 전 체크리스트, 옵션 대응·노출하지 않는 옵션, `replace` 의 `search_id` 선행조건, 평문 `.md` 위치, 종료코드.
- 핵심: ① 워커가 켜져 있어야 한다(`bridge_client.py status`) ② 사용자가 한/글을 닫아 두어야 한다(떠 있으면 종료코드 2) ③ Linux 에서 DRM 파일은 암호문으로 보이며 복호화를 시도하지 않는다.
- 상세를 여기에 복제하지 않는다(단일 원본은 위 안내 파일). 브리지는 이 스킬의 스크립트를 수정하지 않고 호출만 한다.

## 1. 흐름

1. **읽기** — `inspect`로 문서 전체를 .md로 받고, 그 .md를 읽는다. 좁혀 볼 때 `outline`·`tables`·`fields`·`search`.
   → 명령·출력 형식·위치 ID: [references/read.md](references/read.md)
2. **쓰기 방법 고르기** (inspect .md의 `## 필드` 표를 본다)
   - 채울 자리에 **필드(누름틀·셀 필드)**가 있다 → `fill` (다시 읽어 검증되는 주 경로)
   - 필드는 없고 `{{과제명}}` 같은 **자리표시 글자**가 있다 → `replace`
   - 둘 다 없다(빈 표 칸 등) → 이 스킬 범위 밖. 사용자에게 알린다(필드 심기·행 추가는 Phase 2)
3. **값 파일** — `.json` 또는 ```` ```json ```` 블록이 든 `.md` ({키: 값}). 여러 줄 값 허용.
4. **쓰기** — `fill`/`replace`. 화면의 `없는 필드`·`남음`을 확인한다. 하나라도 있으면 종료코드 1.
   → 정책·검증·사각지대: [references/write.md](references/write.md)
5. **검증** — 출력 줄의 `선두 DOCURAY`·`다시 열기 True`·`원본 불변 True`. 필요하면 `inspect <출력>`으로 값을 다시 읽는다.
6. **보고** — 만든 파일(출력 hwpx, `.bak`, 결과 `.md`), 보호 판정, 채우지 못한 키·남은 자리표시.

## 2. 명령

작업 폴더(사용자 프로젝트)에서 실행한다 — 결과 .md가 `<작업 폴더>\hwpx_md\`에 생긴다(스킬 폴더 안에 평문이 쌓이지 않게).
`<스킬>`은 이 SKILL.md가 있는 폴더. 문서 경로는 절대경로·따옴표.

```bat
python "<스킬>\scripts\hwpx_drm.py" inspect "C:\...\문서.hwpx"
python "<스킬>\scripts\hwpx_drm.py" fill    "C:\...\문서.hwpx" --map "C:\...\값.md"
python "<스킬>\scripts\hwpx_drm.py" replace "C:\...\문서.hwpx" --map "C:\...\바꿀말.md"
python "<스킬>\scripts\hwpx_drm.py" verify  "C:\...\문서_out.hwpx"
python "<스킬>\scripts\hwpx_drm.py" images  "C:\...\문서.hwpx" --out-dir "C:\...\새_그림폴더"
```

`search --pattern`의 구분자는 쉼표다. 검색어 안의 쉼표는 `\,`, 역슬래시 자체는 `\\`로 쓴다.

공통 옵션: `--md-dir <폴더>` · `--log <기록.md>`(본문 없는 실행 기록) · `--timeout 180` · `--json`(읽기 결과 JSON).

## 3. 종료코드

| 코드 | 뜻 | 할 일 |
|---|---|---|
| 0 | 성공 | — |
| 1 | 검증 실패: 없는 필드, 남은 자리표시, 저장 실패, 파싱 실패, 예상 못 한 오류 | 화면의 키·위치 ID를 보고 원인 보고 |
| 2 | 사전조건: 파일 없음, 한/글 실행 중, 출력 이미 있음, 값 파일 오류(중복 키·연쇄 치환·replace 값 줄바꿈) | 사용자에게 한/글 닫기 요청 / `--force` / 값 파일 수정 |
| 3 | 저장 결과가 **평문**(DRM 미적용) | 즉시 사용자에게 알림. 반출 금지 |
| 4 | 열기 실패(권한·형식) | 우회하지 않는다. 권한 확인 요청 |
| 5 | 시간초과 — 이 실행이 띄운 한/글만 종료함 | `--timeout`을 늘려 한 번 더, 반복되면 보고 |
| 6 | pywin32·한/글 COM 없음 | `python -m pip install pywin32`, 한/글 설치·등록 확인 |

## 4. 하지 말 것

- 문서 전체 XML 되넣기(`SetTextFile`) — 서식 손실·비멱등 (F-033)
- `SaveAs(…, 'HWP')`로 `.hwpx` 저장 — 이름만 hwpx인 HWP 바이너리가 된다 (F-005). 이 스킬은 항상 `'HWPX'`
- 파이썬으로 `.hwpx`를 zip으로 열기 — DRM 암호문이다
- `HwpObject.Run(...)` 반환값으로 성공 판정 — 반환값이 없다(void). 결과 구조로 확인한다 (F-062)
