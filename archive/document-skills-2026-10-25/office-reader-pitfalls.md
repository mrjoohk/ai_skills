# 실전 함정 목록

전부 실제로 밟은 것들이다. 추측이 아니다.

> PowerShell 이 나오는 항목은 원본·PS 판(D-014 로 삭제)에서 얻은 교훈이다. 현재 구현은 Python(pywin32)이다 —
> Python 판 함정은 아래 "Python(pywin32) 판"·"pywin32 인자 전달" 절에 있다.

## 인코딩

**스크립트 파일은 UTF-8 BOM 으로 저장한다.**
Windows PowerShell 5.1 은 BOM 이 없는 UTF-8 파일을 ANSI(CP949)로 읽는다. 그러면 스크립트
안의 한글 리터럴이 깨지고, 키워드 매칭이 **에러 없이 0건**을 낸다. 가장 찾기 어려운 실패다.
PowerShell 7 은 BOM 없이도 UTF-8 로 읽으므로, 7에서 되던 게 5.1에서 안 되면 이걸 의심한다.

**cmd 의 `>` 리다이렉트를 쓰지 않는다.**

```
powershell -File x.ps1 > out.txt     # UTF-16LE + CP949 → 한글이 ?
powershell -File x.ps1 -LogFile out.txt   # 스크립트가 UTF-8 로 직접 쓴다
```

증상: 파일 선두가 `ff fe`(UTF-16LE BOM)이고 한글이 전부 `?`. `od -An -tx1 | head -1` 로 확인.

**출력 파일은 UTF8Encoding($true) 로 쓴다.**
`StreamWriter($path, $false, (New-Object System.Text.UTF8Encoding $true))`.
BOM 을 붙여야 Excel 이 CSV 를 열 때 한글을 UTF-8 로 인식한다. BOM 없으면 Excel 이 CP949 로
읽어 다시 깨진다.

## COM 성능

**`UsedRange.Value2` 를 한 번에 2D 배열로 받는다.**
셀마다 `$ws.Cells($r,$c).Value2` 를 호출하면 매번 프로세스 경계를 넘는다. 수천 셀에서
수십~수백 배 차이가 난다. 배열로 받으면 이후 루프는 순수 PowerShell 연산이다.

**단일 셀 UsedRange 는 배열이 아니라 스칼라를 반환한다.**
`$vals[$r,$c]` 가 예외를 던진다. `Rows.Count -eq 1 -and Columns.Count -eq 1` 을 먼저 분기한다.

**UsedRange 가 과대 잡힐 수 있다.**
서식만 남은 빈 셀 때문에 `1048576 x 16384` 같은 값이 나오는 문서가 있다. 상한(`MaxRows`/
`MaxCols`)을 두고, 잘랐으면 반드시 로그로 알린다 — 조용히 자르면 "전부 읽었다"로 오독된다.

## 호출하는 셸

**cmd.exe 에서 `-Param:$false` 를 쓰면 안 된다.**
cmd 는 `$false` 를 확장하지 않으므로 PowerShell 이 **문자열** `"$false"` 를 받는다.

```
Cannot convert value "System.String" to type "System.Boolean".
Boolean parameters accept only Boolean values and numbers, such as $True, $False, 1 or 0.
```

`[bool]` 파라미터를 cmd 에서 끄려면 `-Param 0` 을 쓰거나, 스크립트에 **`[switch]` 를 함께 두어야
한다.** 스위치는 값이 필요 없어 셸에 무관하게 동작한다. `[bool]` 만 노출하는 설계는
PowerShell 안에서만 편하고 cmd 사용자를 막는다.

## COM 수명 관리

**`finally` 에서 Close → Quit → ReleaseComObject 순서로 정리한다.**
예외로 중간에 빠져나가면 EXCEL.EXE 가 보이지 않는 채로 남는다. 반복 실행하면 계속 쌓여
메모리를 먹고, 나중에는 파일 잠금까지 일으킨다. 이미 쌓였으면 `taskkill /IM EXCEL.EXE /F`.

**대화상자를 띄우는 속성을 전부 끈다.**

```powershell
$app.Visible = $false
$app.DisplayAlerts = $false
$app.AskToUpdateLinks = $false   # 이걸 빼면 링크 있는 문서에서 영구 정지
$app.EnableEvents = $false       # 문서에 붙은 매크로 이벤트 차단
```

헤드리스에서 대화상자가 뜨면 클릭할 사람이 없어 무한 대기한다.

**PowerPoint 는 `Visible = $false` 를 거부하는 버전이 있다.**
`Presentations.Open(path, ReadOnly, Untitled, WithWindow)` 의 `WithWindow=$false` 로 대신한다.

**Word 의 `DisplayAlerts` 는 불리언이 아니라 열거형이다.** `0`(wdAlertsNone)을 넣는다.

## 데이터 구조

**병합셀은 좌상단에만 값이 있고 나머지는 `null` 이다.**
ICD·요구데이터 문서는 헤더가 2~3행에 걸쳐 병합돼 있는 경우가 많아, 그대로 CSV 로 뽑으면
빈 칸 투성이가 된다. `-FillMerged` 는 셀의 `MergeArea` 를 조회해 **실제 병합 영역의 좌상단 값만** 채운다.
열 방향 전방 채우기는 진짜 빈 칸에도 값을 지어내므로 쓰지 않는다 (F-013).

**시트명에 파일명 금지문자와 끝 공백이 들어간다.**
실제 사례: `#50010`, `표지 `(끝 공백), `ALE 임무제어 조종통제-ALE(FCC)#ddd2`.
`[\\/:*?"<>|]` 를 치환하고 `Trim()` 한다. `#` 은 파일명에 유효하므로 굳이 바꾸지 않는다.

**Word 문단 텍스트 끝에 `\r` 과 `\a` 가 붙는다.**
표 셀은 특히 `\r\a`(0x0D 0x07)로 끝난다. `-replace "[\r\a\x07]", ''` 로 제거한다.

## 출력 설계

**"조건이 맞을 때만 출력"하는 핸들러는 빈 화면을 낸다.**
2026-08-25 실측: Word 핸들러가 제목 스타일 문단만 출력하도록 짜여 있어서, 제목 스타일이
하나도 없는 문서에서 헤더만 찍고 본문을 한 줄도 보여주지 않았다. `-Preview` 를 줘도
그 경로에는 아무 효과가 없었다. 사용자는 "추출 실패"인지 "문서가 원래 비었는지" 구분할 수 없다.

핸들러마다 **무조건 실행되는 미리보기 경로**를 둔다. 조건부 출력(제목 목록, 매칭 결과)은
그 위에 얹는 것이지 대체하는 것이 아니다. 해당 항목이 0건이면 `(제목 스타일 문단 없음)`
처럼 0건임을 명시한다 — 아무것도 안 찍으면 버그와 구분되지 않는다.

**잘랐으면 반드시 몇 개를 잘랐는지 말한다.**
`문단 12줄` 이라 해놓고 5줄만 보여주면 문서에 5줄만 있는 것처럼 읽힌다.
`… (7줄 더). 전체를 보려면 -Preview 12 또는 -Dump` 를 붙인다.

## 도형 열거

**COM 은 도형을 z-order 로 준다. 위치순이 아니다.**
구성도·블록다이어그램을 그대로 뽑으면 라벨이 무작위 순서로 쏟아져 어느 박스 것인지 알 수 없다.
`Top`(10pt 단위로 반올림) → `Left` 로 정렬하면 읽기 순서에 가까워진다. 정확히 반올림 없이
정렬하면 2pt 차이로 어긋난 같은 줄 도형들이 갈라진다.

**텍스트 추출로 복원할 수 없는 것이 있다.**
다이어그램의 의미는 배치와 연결선에 있고, 스크린샷 안의 글자는 어떤 파서로도 안 읽힌다.
정렬은 완화일 뿐 해결이 아니다. PowerPoint 는 `Slide.Export(경로,'PNG',폭,높이)` 로
슬라이드를 그림으로 뽑을 수 있다 — 판독 품질을 결정적으로 바꾸는 것은 이쪽이다.

**표·그룹·SmartArt 는 `HasTextFrame` 으로 안 잡힌다.**
표는 `Table.Cell(r,c).Shape.TextFrame`, 그룹은 `GroupItems` 재귀, SmartArt 는
`SmartArt.AllNodes`. 이 셋을 빼면 ICD·구성도 자료는 제목만 남는다.

## 성능

**Word 는 `Content.Text` 로 본문 전체를 한 번에 가져온다.**
`$doc.Paragraphs.Item($i)` 를 문단마다 호출하면 매번 COM 경계를 넘는다. Excel 의
`UsedRange.Value2` 와 같은 원리다. 스타일 정보가 필요할 때만 문단 개체를 순회하고,
그때도 상한을 둔다.

Word 의 `Content.Text` 는 문단 끝이 `\r`(0x0D), 표의 셀·행 끝이 `\a`(0x07)다.
`\r` 로 나누고 `\x07` 을 공백으로 바꾸면 표 셀이 한 줄로 합쳐진다.

## 판정

**매직 바이트로 먼저 판정한다. 확장자를 믿지 않는다.**
`.xlsx` 확장자를 달고 있어도 내용은 DRM 컨테이너(`BMS DocuRay…`)이거나 열기암호가 걸린
OLE2(`D0 CF 11 E0`)일 수 있다. 실제로 같은 폴더의 `.xlsx` 7개가 전부 DRM 컨테이너였다.

**`_nopw` 같은 파일명을 믿지 않는다.**
"열기암호 제거"와 "DRM 해제"는 다른 층이다. 열기암호만 지운 파일이 여전히 DRM 컨테이너인
경우가 있다 — 이때 파일명은 `nopw` 지만 파이썬으로는 못 읽는다.

**같은 파일이 환경에 따라 다르게 읽힌다.**
DRM 필터 드라이버가 있는 Windows 에서는 평문으로 보이고, 그 드라이버를 우회하는 경로
(네트워크 마운트, 컨테이너, 리눅스 VM)에서는 암호문으로 보인다. "예전엔 읽혔는데"는
파일이 바뀐 게 아니라 **읽는 위치가 바뀐 것**일 수 있다.

## 허용 앱

**파이썬은 대개 허용 앱이 아니다.**
DRM 은 앱 단위 허용 목록으로 동작한다. `python.exe` 로 열면 원본 암호문을 받고
`BadZipFile: File is not a zip file` 이 난다. Excel/Word/한글은 허용 앱이므로 열린다.
이건 우회가 아니라 정책이 허용한 경로다.

**허용 앱에서도 실패하면 거기서 멈춘다.**
`OPEN FAILED` 는 사용자에게 그 문서의 열람 권한이 없다는 뜻이다. 다른 방법을 찾지 말고
보안담당자에게 문의하도록 안내한다.

## 시각 산출물

**Excel 의 `PageSetup` 은 속성 하나마다 프린터 드라이버와 통신한다.**
37시트짜리 통합문서에 방향·배율을 지정하면 체감할 만큼 느려진다.
`$app.PrintCommunication = $false` 로 감싸면 수십 배 빨라진다. 설정이 끝나면 `$true` 로 되돌린다.

**PowerPoint 는 `SaveAs` 가 아니라 `SaveCopyAs` 를 쓴다.**
`SaveAs` 는 열려 있는 프레젠테이션의 경로 자체를 바꾼다. 읽기 전용으로 연 문서에 쓰면
의도치 않은 상태가 되므로, 사본만 남기는 `SaveCopyAs($path, 32)` 를 쓴다.

**PDF 가 PNG 보다 나은 경우가 많다.**
한 파일에 전 페이지가 들어가 페이지 범위로 골라 읽을 수 있고, 벡터라 표의 잔글씨가 살아 있다.
슬라이드처럼 한 장이 곧 한 그림인 경우에만 낱장 PNG 가 유리하다.

**시각 산출물 생성 실패를 조용히 넘기지 않는다.**
그림이 안 나온 것과 원래 그림이 없는 문서는 출력만 봐서는 같다. 실패를 명시하고,
텍스트 추출 결과는 여전히 유효하다는 것도 함께 말한다.

## 경로

**사용자가 준 경로는 상대 경로일 수 있다. 문자열 연산 전에 절대 경로로 바꾼다.**
`-OutDir "logs\_migrate"` 처럼 상대 경로가 들어오면, 저장소 루트 길이만큼 잘라내는 계산에서
`startIndex cannot be larger than length of string` 로 터진다. 짧은 상대 경로에서 긴 절대
경로 길이만큼 자르려 하기 때문이다.

```powershell
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$Dir = (Resolve-Path -LiteralPath $Dir).Path   # 이후 계산은 전부 절대 경로 전제
```

`..` 이 섞인 경로(`../logs/_m2`)도 `Resolve-Path` 가 정규화한다.
길이 비교가 필요한 곳에는 `$Dir.Length -gt $Root.Length` 방어도 함께 둔다.

**같은 스크립트를 두 곳에 두지 않는다.**
경로를 옮겼으면 옛 사본을 반드시 치운다. 사용자는 자기가 쓰던 경로를 계속 쓰고, 그 경로의
파일만 낡은 채로 남으면 "고쳤는데 왜 그대로냐" 가 된다. 실제로 `tools\office-com-reader\`
바로 밑과 `scripts\` 밑에 두 벌이 남아 그 일이 일어났다.

## 산출물 관리

**덤프는 DRM 이 없는 평문이다.**
원본이 복사·반출 통제를 받고 있었다면, 덤프본은 그 통제 밖에 있다. 저장소에 커밋되지
않도록 `.gitignore` 에 등록하고, 분석이 끝나면 삭제한다.
`git check-ignore -v <파일>` 로 실제로 무시되는지 확인한다 — 등록했다고 믿지 말고 확인한다.

## P-003·P-005 실측에서 추가된 함정 (2026-10-01, DocuRay 환경)

**검색 좌표는 시트 절대 주소로 낸다.**
`UsedRange.Value2` 배열의 첨자는 UsedRange 기준이다. 사용 범위가 C3 에서 시작하면 실제 D5 가 `R3C2` 로
보고됐다 (F-014). `UsedRange.Row/Column` 을 더해 `시트!D5` 로 바꿔 writer 의 `-Cell` 과 맞춘다.

**`Value2` 는 날짜를 일련번호로 준다.**
2026-10-01 이 `46296` 으로 나왔다 (F-015). `Range.Value(10)` 은 DateTime 을 주므로 `yyyy-MM-dd` 로 바꾼다.

**Word `Content.Text` 는 본문 이야기만 준다.**
머리글·바닥글·텍스트 상자·각주는 빠진다 (F-017). `StoryRanges` 를 돌고 `NextStoryRange` 로 구역을 따라간다.
연결된 머리글은 구역마다 같은 글자가 반복되므로 (이야기, 글자) 쌍으로 중복을 지운다.

**PowerPoint 는 단일 인스턴스다.**
이미 떠 있는 PowerPoint 에 COM 이 붙고, `finally` 의 `Quit()` 이 사용자가 열어 둔 프레젠테이션까지 닫는다 (F-028).
시작 전에 `POWERPNT` 프로세스가 있으면 멈춘다. Excel·Word 는 새 인스턴스를 띄운다.

**`0x80070570` (corrupted and unreadable) 은 파일 문제였다.**
같은 경로로 합성 DRM pptx 는 열렸고, 실문서는 재설치 후 탐색기에서 정상으로 열렸다 (F-030).
COM 이 이 오류를 내면 먼저 탐색기에서 직접 열어 본다.

**COM 으로 띄운 Office 는 매크로가 허용된 상태다.**
`AutomationSecurity` 기본값이 `msoAutomationSecurityLow` 다. `3`(ForceDisable)으로 바꾸고 연다 (F-020).

## Python(pywin32) 판에서 확인한 함정 (P-014)

**콘솔 출력이 cp949 일 때 대체 출력이 다시 죽는다.**
`text.encode("utf-8","replace").decode("ascii","replace")` 는 한글을 U+FFFD 로 바꾸는데 U+FFFD 도 cp949 로 못 쓴다.
`–`·NBSP·기호가 든 문서를 파이프로 받으면 실행 전체가 실패했다 (F-050). 시작할 때
`sys.stdout.reconfigure(errors="replace")` 로 바꾸고, `--log` 는 화면 출력보다 먼저 쓴다.

**`UsedRange.Value` 를 통째로 받지 않는다.**
서식만 1048576행까지 잡힌 시트는 수천만 개 VARIANT 가 된다 (F-051). `--max-rows/--max-cols` 안쪽만
`ws.Range(ws.Cells(r0,c0), ws.Cells(r1,c1)).Value` 로 받는다.

**오류 셀은 정수 SCODE 로 온다.** `#N/A` → `-2146826246`. 숫자 셀은 float 로 오므로 int 는 오류 값으로 바꿔 쓴다.
시각만 있는 셀은 `1899-12-30 hh:mm:ss` 로 온다 (F-052).

**열기암호 파일은 대화상자로 영원히 멈춘다.**
가짜 암호를 넘기면 대화상자 대신 오류가 난다. 암호 없는 파일(DocuRay 보호 포함)에는 무시된다 (F-049).
단 **자리 인자로** 넘긴다 — `Workbooks.Open(p, 0, True, OMIT, 가짜)`, `Documents.Open(p, False, True, False, 가짜)`.
이름 인자 `Workbooks.Open(p, UpdateLinks=0, ReadOnly=True, Password=가짜)` 는 Format 자리가 비어 Password 가
Excel 에 닿지 않았고, P-015 F3 에서 암호 입력 창이 떴다 (F-085).

## pywin32 인자 전달 (P-019)

**COM 메서드에 이름 인자를 쓰지 않는다. 빈 자리가 있으면 그 뒤 인자가 말없이 버려진다 (F-085).**
동적 디스패치는 넘기지 않은 선택 인자를 `pythoncom.Missing` 으로 채우고, `PyIDispatch::InvokeTypes` 는 첫 Missing 에서
인자 개수를 끊는다. 오류도 경고도 없다. 자리 인자로만 부르고, 건너뛸 자리에 `OMIT`(= `pythoncom.Empty`, 앱에는
"생략"으로 전달)을 넣는다. 상세 표는 `office-com-writer/references/write-pitfalls.md` 같은 절.

**Office 오류 메시지의 CR 은 콘솔에서 줄 앞을 덮어쓴다 (F-086).** `FAILED:` 줄은 공백으로 합쳐 한 줄로 낸다.

**Excel 오류 설명은 HTML 이스케이프돼 온다 (F-088, P-019 P1 실측).** `암호가 잘못되었습니다. &lt;Caps Lock&gt; 키가 …`.
`html.unescape` 뒤에 한 줄로 합친다.

**PowerPoint 열기암호 파일은 아직 멈출 수 있다 (F-087, 보류).** `Presentations.Open` 에는 암호 인자가 없다.
암호 창이 뜨면 아무것도 입력하지 말고 취소한다.

**`safe(app.Quit)` 는 속성 조회가 `safe` 밖에서 일어난다.** Office 가 죽어 있으면 `finally` 에서 원래 오류를 덮는다.
`safe(lambda: app.Quit())` 로 쓴다 (F-053).

**PowerPoint 실행 중 판정은 프로세스가 아니라 보이는 창으로.**
직전 자동화가 닫은 POWERPNT 는 5초 넘게 남는다 — 프로세스 유무로 막으면 거짓 거부가 난다 (F-046, P-010 V5r).
`win32gui.EnumWindows` 로 `PPTFrameClass` 이면서 보이는 창만 본다. 열거 중 창이 닫히는 경쟁은 예외를 삼킨다 (F-059).
