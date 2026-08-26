---
name: office-com-reader
description: Windows에서 openpyxl/python-docx로 열리지 않는 Office·한글 문서(DRM 컨테이너, 열기암호, 레거시 포맷)를 판독해 분석한다. 포맷을 먼저 감지해 평문이면 파이썬으로, DRM이면 Excel/Word/PowerPoint/한글 COM으로 읽는다. MANDATORY TRIGGERS: "BadZipFile", "File is not a zip file", "엑셀이 안 열려", "xlsx를 못 읽어", "DRM 걸린 문서", "암호화된 엑셀", "DocuRay", "문서보안 때문에 안 읽혀", "COM으로 읽어줘", "시트 목록만 보여줘", "hwp 읽어줘", "hwpx 분석", "한글 문서 분석", "ICD 문서 분석". 파이썬으로 스프레드시트·문서를 읽으려다 실패했을 때 반드시 이 스킬을 사용할 것.
---

# Office COM Reader

파이썬 라이브러리가 읽지 못하는 문서를, 그 문서를 여는 것이 이미 허용된
애플리케이션(Excel/Word/PowerPoint/한글)을 통해 판독한다.

## 0. 전제 — 건너뛰지 말 것

이 스킬은 **보안통제를 깨지 않는다.** 암호를 해독하지 않고, 키를 추출하지 않고,
DRM 필터 드라이버를 건드리지 않는다. 문서보안 솔루션이 **허용 앱으로 등록해 둔**
애플리케이션에게 파일을 열게 하고, COM으로 그 값을 받아올 뿐이다.
허용 앱이 아니면 이 스킬도 실패한다 — 그게 정상 동작이다.

그러나 **판독과 평문 영구화는 다르다.**

- 판독(앱으로 열어 읽기) = 사용자에게 이미 허용된 행위
- 평문 파일 생성 = DRM이 막으려던 바로 그것. 복사·메일·업로드가 자유로워진다

그래서 이 스킬의 **기본값은 파일을 만들지 않는 것**이다. `-Dump`는 명시적 옵트인이며,
쓸 때마다 무엇이 디스크에 남는지 사용자에게 알린다.

조직 규정상 "허용 앱으로 열람"과 "자동화 대량 추출"이 같은 범위인지는 사내 정책 문제다.
**Claude가 판단할 수 없다.** 대량 덤프 전에는 사용자에게 확인한다.

## 1. 포맷을 먼저 감지한다 — COM은 마지막 수단

COM은 느리고 Office 프로세스를 띄운다. 평문 파일에 쓸 이유가 없다.
**항상 이것부터 실행한다.**

```bash
python scripts/probe_format.py "<파일경로>"
```

출력은 `plain_ooxml` / `plain_hwpx` / `ole2_encrypted` / `ole2_legacy` / `hwp5` /
`drm_container` / `unknown` 중 하나와 권장 경로다.

| 매직 바이트 | 판정 | 조치 |
|---|---|---|
| `50 4B 03 04` + `[Content_Types].xml` | 평문 OOXML | **openpyxl / python-docx / python-pptx 직행** |
| `50 4B 03 04` + mimetype `application/hwp+zip` | 평문 HWPX | **`scripts/read_hwpx.py` 직행** |
| `D0 CF 11 E0` + `EncryptedPackage` 스트림 | 열기암호 OOXML | `msoffcrypto-tool` (암호 필요) |
| `D0 CF 11 E0` + `FileHeader` 스트림 | HWP 5.0 바이너리 | `pyhwp` / `olefile`, 실패 시 COM |
| `D0 CF 11 E0` (그 외) | 레거시 `.xls`/`.doc`/`.ppt` | COM |
| 그 외 (예: `BMS DocuRay`) | DRM 컨테이너 | **COM 경로** |

probe가 `plain_*`을 내면 COM을 쓰지 않는다.

## 2. HWPX — 대부분 COM이 필요 없다

`.hwpx`(한/글 2014+)는 OWPML 기반 **ZIP 컨테이너**다. DRM만 안 걸려 있으면
파이썬으로 바로 읽힌다.

```bash
python scripts/read_hwpx.py "<파일>"                       # 구조 + 미리보기
python scripts/read_hwpx.py "<파일>" --pattern 헬기,모기체    # 키워드 검색
python scripts/read_hwpx.py "<파일>" --dump out.txt         # 전문 (옵트인)
```

내부 구조: 본문은 `Contents/section0.xml`, `section1.xml`… 에 있고 텍스트는 `<hp:t>`,
표는 `<hp:tbl>` → `<hp:tr>` → `<hp:tc>`. 스크립트는 네임스페이스 접두사에 의존하지 않고
로컬명으로 매칭하므로 한/글 버전이 달라도 동작한다.

`.hwp`(5.0 바이너리)는 OLE2다. `BodyText/SectionN` 스트림이 raw deflate로 압축돼 있고
레코드 구조 파싱이 번거로우니 `pyhwp`(`hwp5txt`)를 먼저 시도하고, 실패하면 COM으로 간다.

## 3. COM 판독

`scripts/Read-OfficeDoc.ps1`을 Windows에서 실행한다. 확장자로 앱을 자동 판별한다 —
`.xlsx .xlsm .xls .xlsb`(Excel) · `.docx .doc .rtf`(Word) · `.pptx .ppt`(PowerPoint) ·
`.hwp .hwpx`(한글).

```powershell
# 구조 파악 — 아무 파일도 만들지 않음 (기본값)
powershell -ExecutionPolicy Bypass -File scripts\Read-OfficeDoc.ps1 -Path "C:\...\doc.xlsx"

# 키워드 검색 — 위치와 문맥만 출력
powershell -ExecutionPolicy Bypass -File scripts\Read-OfficeDoc.ps1 -Path "..." -Pattern "헬기,모기체,Heli"

# 전문 덤프 — 평문 파일 생성. 사용자 확인 후에만
powershell -ExecutionPolicy Bypass -File scripts\Read-OfficeDoc.ps1 -Path "..." -Dump -OutDir "...\extract"
```

주요 파라미터: `-Pattern`(쉼표 구분, 대소문자 무시) · `-Sheet`(이름/인덱스 필터) ·
`-MaxRows`/`-MaxCols`(과대 UsedRange 방어, 기본 5000/200) · `-FillMerged`(병합셀 전방 채우기) ·
`-LogFile`(UTF-8로 직접 기록) · `-OutDir`(기본: 원본 옆 `<파일명>_extract`)

## 4. 시각 산출물 — 텍스트만으로는 복원할 수 없는 것이 있다

다이어그램의 의미는 배치와 연결선에 있고, 스크린샷 안의 글자는 어떤 파서로도 안 읽힌다.
표의 병합 구조, 강조 색, 도형 그룹의 소속도 텍스트에는 남지 않는다.
그래서 **`-ExportImages` 는 기본으로 켜져 있다.** 네 형식 모두 시각 산출물을 만든다.

| 형식 | 산출물 | 방법 |
|---|---|---|
| Excel | `<이름>.pdf` | 시트마다 가로방향·가로 1페이지 맞춤 후 `ExportAsFixedFormat` |
| Word | `<이름>.pdf` | `ExportAsFixedFormat(…, 17)` |
| PowerPoint | `slide_01.png` … + `<이름>.pdf` | `Slide.Export` 낱장 + `SaveCopyAs(…, 32)` |
| 한/글 | `<이름>.pdf` | `SaveAs(…, 'PDF', '')` |

PDF 를 쓰는 이유: 한 파일에 전 페이지가 들어가 페이지 범위로 골라 읽을 수 있고, 벡터라
표의 잔글씨가 살아 있다. PowerPoint 만 PNG 를 함께 내는 것은 슬라이드가 곧 한 장의 그림이라
낱장으로 지목해 보기 편해서다 (`-ImageWidth`, 기본 1600px, 높이는 종횡비 계산).

**생성 실패는 반드시 보고한다.** 조용히 넘기면 "그림이 없는 문서"와 구분되지 않는다.
실패해도 텍스트 추출 결과는 그대로 유효하다.

시각 산출물도 DRM 없는 파일이므로, `-Dump` 없이 읽어도 출력 폴더가 만들어지고
경고 README·`.gitignore` 등록이 함께 적용된다. 끄려면 `-ExportImages:$false`.

### PowerPoint 도형은 위치순으로 정렬한다

COM 은 도형을 z-order(생성 순서)로 열거하므로, 그대로 뽑으면 구성도가 라벨 죽이 된다.
위→아래, 왼쪽→오른쪽으로 정렬하되 `Top` 을 10pt 단위로 뭉쳐 같은 줄 도형이 좌우로 이어지게 한다.
표·그룹·SmartArt 재귀 안에서도 같은 정렬이 적용된다. 다만 이것은 완화일 뿐 해결이 아니다 —
구조를 확인하려면 위의 그림을 본다.

### 출력을 파일로 받을 때 — cmd 리다이렉트 금지

```powershell
# 나쁨: UTF-16LE + CP949로 한글이 ? 가 된다
powershell -File Read-OfficeDoc.ps1 -Path "..." > out.txt

# 좋음
powershell -File Read-OfficeDoc.ps1 -Path "..." -LogFile out.txt
```

### 한/글 COM

DRM(DocuRay)이 걸린 `.hwpx`에서 실사용으로 확인됐다 (2026-08-25, 한컴오피스 설치 환경).

`RegisterModule("FilePathCheckDLL","FilePathCheckerModule")`이 **`$false`를 돌려줘도
`Open`은 성공할 수 있다.** 실제로 그런 환경이 확인됐으므로, 등록 실패를 이유로 중단하지
않는다 — 참고 문구만 출력하고 계속 진행한다.

등록 실패 + 보안 대화상자가 실제로 뜨는 환경이라면 사람이 클릭해야 하므로 자동화는 멈춘다.
그때는 대화형으로 한 번 허용하고 진행 여부를 확인한다.

주의: `RegisterModule`과 `Open`의 반환값을 삼키지 않으면 `True`/`False`가 출력에 섞여
판독 결과처럼 보인다. `[bool]` 캐스팅으로 변수에 받는다.

## 5. 결과 해석

- **Summary**: 네 핸들러 모두 **무조건 본문 미리보기를 출력한다** — Excel은 시트별
  `행 x 열` + 상단 행, Word는 제목 목록 + 본문 미리보기, PowerPoint는 슬라이드별 제목,
  한글은 줄 수 + 앞부분. 제목이 0건이면 0건이라고 명시한다.
  잘렸으면 `… (N개 더)` 로 알린다 — 조용히 자르지 않는다
- **Search**: `시트!R{행}C{열}` / `슬라이드 N` / `문단 N` 좌표와 매칭 문맥 120자
- **Dump**: 시트당 CSV 1개(UTF-8 BOM), 문서형은 텍스트 1개. 출력 폴더에
  `_READ_ME_FIRST.txt` 경고문을 함께 쓰고 상위 저장소 `.gitignore`에 폴더를 등록한다

덤프한 CSV에는 병합셀 때문에 빈 칸(`""`)이 많다. 헤더가 여러 행에 걸친 ICD·요구데이터
문서에서 특히 흔하므로, 열 의미를 확정하기 전에 원본 상단 10행을 눈으로 확인한다.

## 6. 실패했을 때

| 증상 | 원인 | 대응 |
|---|---|---|
| `OPEN FAILED` / 권한 오류 | 해당 앱도 허용 앱이 아니거나 열람 권한 없음 | 보안담당자 반출 승인. 우회 시도하지 말 것 |
| 응답 없이 멈춤 | 대화상자(링크 업데이트, 복구, 한글 보안경고) | Excel/Word/PPT는 스크립트가 억제. 한글은 §3 참고 |
| 한글이 `?` | cmd `>` 리다이렉트 | `-LogFile` 사용 |
| 키워드 매칭 0건인데 있어야 함 | 스크립트가 BOM 없이 저장돼 한글 리터럴이 깨짐 | UTF-8 **BOM**으로 재저장 |
| 프로세스 누적 | 이전 실행이 예외로 종료 | `taskkill /IM EXCEL.EXE /F` (`HWP.EXE`, `WINWORD.EXE`) 후 재실행 |

상세 함정 목록: `references/pitfalls.md`

## 7. 검증 이력

2026-08-25, Windows + 한컴오피스 + MS Office, DocuRay DRM 환경에서 실측.

| 경로 | 확인 내용 |
|---|---|
| `probe_format.py` | DRM(xlsx·hwpx·docx·pptx), 열기암호 OLE2, 평문 OOXML 6종 정확 판정 |
| Excel COM | 37시트 추출, 시트명 `#50010`·끝공백 처리 포함 |
| Word COM | 문단 6개 추출. `Content.Text` 일괄 읽기 |
| PowerPoint COM | 슬라이드 3개, 도형 텍스트 추출 |
| 한/글 COM | DRM `.hwpx` 12줄 추출, 원본 대조 완료 |
| `read_hwpx.py` | 비DRM hwpx 문단·표·검색·덤프 |
| PowerPoint 그림 | DRM 29슬라이드 → PNG 29/29장 (1600x1200, 4:3 종횡비 자동) |
| 도형 위치 정렬 | 중첩 그룹·10pt 뭉침 목 테스트 |
| 안전장치 | 덤프 폴더 생성 → `.gitignore` 등록 → `git check-ignore` 로 확인, 재실행 시 중복 없음 |

**미검증**: Excel·Word·한/글의 PDF 내보내기는 아직 실물로 돌려본 적이 없다.
`Write-VisualResult` 가 실패를 명시적으로 보고하므로, 처음 쓸 때 그 줄을 확인한다.

실측에서 잡은 버그 3건은 전부 **"돌아가는데 결과를 오독하게 만드는"** 종류였다 —
COM 반환값이 출력에 섞임, 잘랐는데 고지 없음, 조건 미충족 시 침묵.
새 핸들러를 추가하면 반드시 실물로 한 번 돌리고 원본과 대조한다.

## 8. 마무리 체크

덤프를 생성했다면 사용자에게 **반드시** 알린다:

- 어떤 경로에 몇 개의 평문 파일이 생겼는지
- `.gitignore` 등록 여부 (`git check-ignore -v <파일>` 로 확인)
- 더 필요 없으면 삭제를 권한다

분석이 끝났는데 덤프가 남아 있으면 정리 여부를 묻는다.
