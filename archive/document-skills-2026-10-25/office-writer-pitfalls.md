# 쓰기 함정 목록

읽기와 달리 쓰기는 되돌릴 수 없다. 여기 적힌 것은 대부분 실측으로 잡은 것이다.

> PowerShell 이 나오는 항목은 원본·PS 판(D-014 로 삭제)에서 얻은 교훈이다. 현재 구현은 Python(pywin32)이다 —
> Python 판 함정은 아래 "Python(pywin32) 판"·"pywin32 인자 전달" 절에 있다.

## 되돌릴 수 없음을 전제로 설계한다

**원본을 덮어쓰지 않는 것이 기본이다.**
`-Out` 도 `-Overwrite` 도 없으면 `<원본>_out.<확장자>` 를 만든다. 사용자가 명시적으로
덮어쓰기를 요구하기 전에는 원본에 손대지 않는다.

**덮어쓸 때는 반드시 백업을 먼저 만든다.**
`<원본>.bak`, 이미 있으면 `.1.bak`, `.2.bak` 으로 번호를 올린다. 덮어쓰고 나서
"백업할 걸" 은 늦다.

**문서가 열려 있으면 시작하지 않는다.**
Office 는 문서를 열면 같은 폴더에 `~$이름` 잠금 파일을 만든다. 열린 문서를 COM 으로
저장하면 사용자가 편집 중이던 내용이 사라질 수 있다. 시작 전에 검사하고 중단한다.
잠금 파일 이름은 `~$` + 전체 이름인 경우와 `~$` + 앞 두 글자를 뺀 이름인 경우가 모두 있다.

## 보호 재적용은 보장되지 않는다 — 반드시 확인한다

허용 앱으로 저장하면 DRM 이 다시 걸리는 것이 보통이지만, **항상 그렇지는 않다.**
정책·확장자·저장 위치에 따라 평문으로 떨어질 수 있다.

보호가 다시 걸리지 않은 파일은 **원본과 같은 내용을 담은 무방비 사본**이다.
읽기 스킬의 덤프와 같은 성격의 위험이며, 이쪽은 정식 산출물로 보이기 때문에 더 오래 남는다.

저장 후 항상 확인한다.

```bash
python scripts/verify_protection.py "<저장한 파일>"
```

선두 바이트가 `PK..` 면 평문 OOXML, `BMS DocuRay` 같은 미상 매직이면 DRM 컨테이너다.

## PowerShell 문법

**배열 첨자 안에서 산술은 괄호로 묶는다.**
`$grid[$r + 1, $c]` 는 `$r + (1, $c)` 로 파싱된다. 쉼표가 `+` 보다 강하게 묶이기 때문에
정수에 배열을 더하려다 `op_Addition` 오류가 난다. `$grid[($r + 1), $c]` 로 쓴다.

**동적 속성 이름은 변수에 받아 쓴다.**
`$row.$($cols[$c])` 는 인덱스 표현식이 속성 이름으로 해석되지 않아 값이 통째로 빈다.
`$colName = $cols[$c]; $row.$colName` 으로 쓴다.

**스크립트를 UTF-8 BOM 으로 저장한다.**
BOM 이 없으면 Windows PowerShell 5.1 이 한글 리터럴을 ANSI 로 읽는다. 읽기에서는 검색이
0건이 되고, **쓰기에서는 엉뚱한 문자열로 치환된다.** 쓰기 쪽 피해가 훨씬 크다.

## COM 쓰기

**읽기 전용으로 열면 저장할 수 없다.**
`Workbooks.Open($path, 0, $true)` 의 세 번째 인자가 ReadOnly 다. 쓰기 모드에서는 `$false`.
Word 는 `Documents.Open($path, $false, $false, $false)`, PowerPoint 는
`Presentations.Open($path, $false, $false, $false)`.

**PowerPoint 는 `SaveCopyAs` 를 쓴다.**
`SaveAs` 는 열려 있는 프레젠테이션의 경로 자체를 바꾼다.

**Word 의 `SaveAs2` 는 2010 이상에서만 있다.** 없으면 `SaveAs` 로 물러난다.

**Excel 에 격자를 넣을 때는 `Range.Value2` 에 2차원 배열을 통째로 대입한다.**
셀 하나씩 쓰면 COM 왕복이 행x열 번이다. 읽을 때 `UsedRange.Value2` 를 한 번에 받는 것과
같은 원리이며, 쓰기 쪽이 더 느리다.

## 치환이 닿지 않는 곳

치환은 "전부 바뀌었다" 고 착각하기 쉽다. 실제로는 다음이 빠진다.

| 앱 | 안 닿는 곳 |
|---|---|
| Word | SmartArt. (수정본은 `StoryRanges` 로 본문·머리글·바닥글·각주·텍스트 상자를 모두 돈다) |
| PowerPoint | SmartArt 내부. 표·그룹은 재귀로 처리한다 |
| Excel | 수식이 만들어내는 값, 차트 제목, 도형 안의 글자 |

그래서 치환 후에는 **읽기 스킬로 결과를 다시 읽어 확인한다.** 특히 남아 있으면 안 되는
플레이스홀더를 키워드로 검색해 0건인지 본다.

## 표현력은 파이썬이 낫다

PowerShell COM 으로 문서를 처음부터 짜는 것은 고통스럽다. 새 문서는 파이썬
(`python-docx` / `openpyxl` / `python-pptx`)으로 만들고, COM 은 **보호를 입히는 마지막 한 단계**로만
쓰는 편이 훨씬 낫다. 이 스킬의 `Protect` 모드가 그 단계다.

## P-003·P-005 실측에서 추가된 함정 (2026-10-01, DocuRay 환경)

**PowerPoint `TextRange.Replace` 는 첫 일치만 바꾼다.**
`A {{X}} B {{X}}` 가 `A 값 B {{X}}` 로 남았다 (F-002). 반환된 범위의 `Start` 에 넣은 값 길이를 더한 위치부터
남은 범위를 `Characters()` 로 잘라 다시 부른다. 위치는 매번 프레임 전체 범위를 새로 받아 계산한다.

**Word `Find.Execute` 의 ReplaceWith 는 255자 제한이다.**
300자 값에서 "문자열 매개 변수가 너무 깁니다"로 실행 전체가 실패하고 파일이 저장되지 않았다 (F-003).
`Find` 로 위치만 찾고 `Range.Text` 에 직접 넣은 뒤 `Collapse(0)` 으로 넘어간다.

**Excel 은 대입된 문자열을 키보드 입력처럼 해석한다.**
`001`→`1`, `1-2`→`46024`(날짜) 로 바뀌었다 (F-009). 평범한 10진수만 숫자로, 나머지는 `'` 접두 텍스트로 넣는다.
`Worksheets.Add()` 기본값은 활성 시트 **앞**이라 새 시트가 맨 앞에 생겼다 — `After` 에 마지막 시트를 준다.

**`Range.Replace` 의 반환값은 치환 건수가 아니다.**
시트×검색어마다 성공을 보고할 뿐이다 (F-008). 치환 전 `UsedRange.Formula` 에서 키를 포함한 셀 수를 센다.

**저장 형식 코드는 출력 확장자로 고른다.**
고정 코드(51/16/24)는 `.xlsm` 매크로를 버리고 `.xls/.doc/.ppt` 이름에 OOXML 을 썼다 (F-004).

**허용 앱이 저장하면 DocuRay 가 자동으로 보호를 건다 — 이 환경에서는.**
평문 신규 파일·DRM 문서의 새 경로 저장 모두 `BMS DocuRay` 로 나왔다 (P-005, 9/9). 그래도 환경이 바뀌면
보장되지 않으므로 저장 후 판정은 매번 한다 (F-007: 스크립트가 직접 판정, 평문이면 종료코드 3).

**PowerPoint 자기 경로 `SaveCopyAs` 는 된다.**
열린 프레젠테이션의 자기 경로로 덮어쓰기가 정상 저장됐다 (F-006 기각).

**`-Out` 상대 경로는 절대 경로로 바꾼다.**
COM 은 앱의 현재 폴더 기준으로, PowerShell 존재 검사는 셸의 현재 폴더 기준으로 해석한다 (F-027).

## Python(pywin32) 판에서 확인한 함정 (P-014)

**Excel `Range.Replace` 는 바뀐 셀을 다시 입력처럼 해석한다.**
`{{코드}}` 만 있던 셀을 `001` 로 바꾸면 숫자 1, `3-4` 는 날짜가 된다 — 텍스트 숫자를 숫자로 바꾸는 "`.`→`.` 치환"
요령과 같은 동작이다. 255자를 넘는 값은 실패한다 (F-048). `Find`/`FindNext` 로 셀만 찾고, 셀 텍스트를 파이썬에서
바꿔 수식이면 `Formula`, 아니면 fill 과 같은 규칙(`cell_input`)으로 `Value2` 에 넣는다.

**열기암호 파일은 대화상자로 영원히 멈춘다.** 가짜 `Password`/`PasswordDocument` 를 넘긴다 (F-049).
단, **자리 인자로** 넘겨야 Excel 에 닿는다 — 아래 F-085.

**시트 이름은 대소문자를 구분하지 않는다.** `--sheet data` 로 "Data" 가 있는데 새 시트를 만들면 이름 충돌로 실패한다 (F-054).

**Word 잠금 파일은 이름 길이에 따라 앞 한 글자만 바뀌기도 한다** (`~$구계획서초안.docx`). 세 후보를 모두 본다 (F-055).

**PowerPoint 위치는 UTF-16 단위다.** 재검색 위치는 `len(value.encode("utf-16-le")) // 2` 로 계산한다 (F-057).

**값에 키가 들어 있는 치환은 연결된 머리글·병합된 표 셀에서 한 번 더 감싸질 수 있다** (F-058, 보류 — 드묾).

**pywin32 동적 디스패치.** `DispatchEx` 로 새 인스턴스를 만들고 `dynamic.Dispatch(app._oleobj_)` 로 다시 감싸
makepy 캐시 유무와 무관하게 늦은 바인딩으로 쓴다. 매개변수 있는 속성(`Range.Value`, `Address`)은 인자 없이 읽힌다.
~~`Worksheets.Add(After=…)` 같은 이름 인자는 형식 정보가 있어 동작한다.~~ — **틀렸다.** 아래 F-085.

**`Worksheets.Add(After=…)` 의 After 가 pywin32 동적 디스패치에서 먹지 않았다 (F-060, P-014 V8r 실측).**
"시트 생성(맨 뒤)" 라고 출력했는데 새 시트는 맨 앞에 있었다. 가짜 COM 은 After 를 그대로 지켜 시험이 놓쳤다.
`Add()` 뒤에 기존 시트를 원래 순서대로 `sheet.Move(새시트)` 로 새 시트 앞에 옮긴다 — `Move` 의 첫 인자(Before)만
쓰므로 선택 인자 전달 방식에 기대지 않는다. 옮긴 뒤 `Index == Count` 를 확인하고, 아니면 경고를 낸다 (P-015 F1·F2 실측 통과).
교훈: 선택 인자를 이름으로 넘기는 호출은 가짜 시험이 아니라 실측으로 확인한다.

## pywin32 인자 전달 (P-019)

**COM 메서드에 이름 인자를 쓰지 않는다. 빈 자리가 있으면 그 뒤 인자가 말없이 버려진다 (F-085).**
동적 디스패치는 넘기지 않은 선택 인자를 `pythoncom.Missing` 으로 채우고(`client/build.py`
`MakeDispatchFuncMethod`, `bMakeClass=0` — 형식 정보에 기본값이 적힌 인자는 그 값으로 채워 빈 자리가 생기지 않는다.
`Find` 의 SearchDirection, PowerPoint `Open` 의 플래그 등), `PyIDispatch::InvokeTypes` 는 **첫 Missing 에서 인자 개수를
끊는다** (`src/PyIDispatch.cpp` "count until end or first param marked as Missing"). 오류도 경고도 없다. 그래서

| 호출 | 실제로 앱에 간 것 | 결과 |
|---|---|---|
| `Workbooks.Open(p, UpdateLinks=0, ReadOnly=True, Password=x)` | p, 0, True (Format 자리가 비어 Password 버려짐) | 열기암호 대화상자 — P-015 F3 |
| `Worksheets.Add(After=s)` | 없음 (Before 자리가 빔) | 맨 앞에 생성 — P-014 V8r (F-060) |
| `Cells.Find(What=w, LookIn=…, LookAt=…)` | w 만 (After 자리가 빔) | 직전 검색 설정을 씀 — 잠복 |
| `Documents.Open(p, ConfirmConversions=…, ReadOnly=…, AddToRecentFiles=…, PasswordDocument=x)` | 전부 (빈 자리 없음) | 정상 — P-015 F4 |

규칙: **자리 인자로만 부르고, 건너뛸 자리에는 `OMIT`(= `pythoncom.Empty`)을 넣는다.** `Empty` 는 인자 변환에서
`VT_ERROR/DISP_E_PARAMNOTFOUND`(= VBA 의 "생략")로 바뀐다 (`src/oleargs.cpp` `MakeObjToVariant`). makepy 생성 코드가
기본값으로 쓰는 값이다. `None` 은 `VT_NULL` 이라 생략이 아니고, `pythoncom.ArgNotFound` 는 매개변수 형식에 따라 다르게
변환돼 쓰지 않는다.
`Workbooks.Open(p, 0, False, OMIT, 가짜암호)`, `Cells.Find(w, OMIT, -4123, 2, 1, 1, False)`.
가짜 COM 시험은 `@latebound` 로 이 동작을 흉내 내고, `com_positional_only` 가 이름 인자 호출을 막는다.
실측 확인: `tools\test_office\probe_com_args.py` (빈 통합문서로 두 방식을 비교, 파일을 만들지 않는다).

**Office 오류 메시지에는 CR 이 섞여 있다 (F-086).** Word 는 `"…않습니다.\rWord(으)로 … \r(경로)"` 를 준다.
그대로 찍으면 콘솔에서 뒤 조각이 줄 앞을 덮어 `FAILED:` 가 사라진다. 공백 하나로 합쳐 한 줄로 낸다.

**Excel 오류 설명은 HTML 이스케이프돼 온다 (F-088, P-019 P1 실측).** `암호가 잘못되었습니다. &lt;Caps Lock&gt; 키가 …`.
`html.unescape` 뒤에 한 줄로 합친다.

**아직 대화상자가 뜰 수 있는 경로 (F-087, 보류).** PowerPoint 는 `Presentations.Open` 에 암호 인자가 없어 열기암호
pptx 에서 멈출 수 있다. 쓰기 예약 암호(Excel `WriteResPassword`, Word `WritePasswordDocument`)나 "읽기 전용 권장" 파일은
편집용으로 열 때 묻는다. 실물 시험 파일이 없어 아직 넣지 않았다 — 창이 뜨면 아무것도 입력하지 말고 취소한다.
