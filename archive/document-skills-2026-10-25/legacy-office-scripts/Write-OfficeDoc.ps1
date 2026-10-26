<#
.SYNOPSIS
    DRM 환경에서 Office/한글 문서를 쓰고 고친다.

.DESCRIPTION
    파이썬 라이브러리는 DRM 문서를 열지 못하고, 파이썬이 만든 파일은 보호가 걸려 있지 않다.
    이 스크립트는 허용 앱(Excel/Word/PowerPoint/한글)에게 저장을 시켜 그 두 문제를 해결한다.

    쓰기는 되돌릴 수 없다. 그래서 기본 동작은 다음과 같다.
      - 원본을 덮어쓰지 않는다. -Out 을 주지 않으면 <원본>_out.<확장자> 를 만든다.
      - -Overwrite 는 명시적으로 줘야 하고, 그때도 .bak 을 먼저 만든다.
      - 문서가 열려 있으면(~$ 잠금 파일) 시작하지 않는다.
      - 저장 후 보호 여부를 반드시 확인해 보고한다.

    반드시 UTF-8 BOM 으로 저장할 것. BOM 이 없으면 Windows PowerShell 5.1 이
    한글 리터럴을 ANSI 로 읽어 치환이 조용히 실패한다.

.EXAMPLE
    # 파이썬이 만든 평문 산출물에 DRM 을 입힌다 (가장 자주 쓰는 모드)
    Write-OfficeDoc.ps1 -Mode Protect -Path "C:\out\보고서.docx" -Overwrite
.EXAMPLE
    # DRM 템플릿의 플레이스홀더를 채워 새 파일로 만든다
    Write-OfficeDoc.ps1 -Mode Replace -Path "C:\template.pptx" -MapFile map.json -Out "C:\결과.pptx"
.EXAMPLE
    # CSV 를 시트에 써넣는다
    Write-OfficeDoc.ps1 -Mode Fill -Path "C:\양식.xlsx" -DataFile data.csv -Sheet "Input" -Cell B3
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateSet('Protect', 'Replace', 'Fill')][string]$Mode,
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Out,
    [switch]$Overwrite,
    [string]$MapFile,
    [string]$DataFile,
    [string]$Sheet,
    [string]$Cell = 'A1',
    [switch]$NoBackup,
    [string]$LogFile
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$script:Log = $null
$script:Changes = 0

function Write-Out {
    param([string]$Text = '')
    Write-Host $Text
    if ($script:Log) { $script:Log.WriteLine($Text) }
}

function Test-DocumentLocked {
    <# Office 는 문서를 열면 같은 폴더에 ~$이름 잠금 파일을 만든다.
       열린 문서를 건드리면 저장이 실패하거나 사용자의 편집이 날아간다. #>
    param([string]$FullPath)
    $dir = Split-Path -Parent $FullPath
    $name = Split-Path -Leaf $FullPath
    foreach ($candidate in @("~`$$name", "~`$" + $name.Substring([Math]::Min(2, $name.Length)))) {
        if (Test-Path -LiteralPath (Join-Path $dir $candidate)) { return $true }
    }
    return $false
}

function Get-OutPath {
    param([string]$FullPath)
    if ($Out) { return $Out }
    if ($Overwrite) { return $FullPath }
    $dir = Split-Path -Parent $FullPath
    $base = [IO.Path]::GetFileNameWithoutExtension($FullPath)
    $ext = [IO.Path]::GetExtension($FullPath)
    return (Join-Path $dir ($base + '_out' + $ext))
}

function Backup-Original {
    param([string]$FullPath, [string]$OutPath)
    if ($OutPath -ne $FullPath) { return }          # 덮어쓰지 않으면 백업이 필요 없다
    if ($NoBackup) {
        Write-Out '  ! -NoBackup: 백업 없이 덮어쓴다'
        return
    }
    $bak = "$FullPath.bak"
    $i = 1
    while (Test-Path -LiteralPath $bak) { $bak = "$FullPath.$i.bak"; $i++ }
    Copy-Item -LiteralPath $FullPath -Destination $bak
    Write-Out "  백업: $(Split-Path -Leaf $bak)"
}

function Get-ReplacementMap {
    if (-not $MapFile) { throw '-Mode Replace 에는 -MapFile 이 필요하다 (JSON: {"찾을말":"바꿀말", …})' }
    if (-not (Test-Path -LiteralPath $MapFile)) { throw "MapFile 없음: $MapFile" }
    $json = Get-Content -LiteralPath $MapFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $map = @{}
    foreach ($p in $json.PSObject.Properties) { $map[$p.Name] = [string]$p.Value }
    if ($map.Count -eq 0) { throw 'MapFile 이 비어 있다' }
    return $map
}

function Import-DataGrid {
    <# CSV 를 2차원 배열로 읽는다. Excel 에는 셀 하나씩이 아니라 이 배열을 통째로 넣는다. #>
    if (-not $DataFile) { throw '-Mode Fill 에는 -DataFile 이 필요하다 (CSV)' }
    if (-not (Test-Path -LiteralPath $DataFile)) { throw "DataFile 없음: $DataFile" }

    $rowsIn = @(Import-Csv -LiteralPath $DataFile -Encoding UTF8)
    if ($rowsIn.Count -eq 0) { throw 'DataFile 에 데이터 행이 없다' }
    $cols = @($rowsIn[0].PSObject.Properties.Name)

    $grid = New-Object 'object[,]' ($rowsIn.Count + 1), $cols.Count
    for ($c = 0; $c -lt $cols.Count; $c++) { $grid[0, $c] = $cols[$c] }   # 헤더 행
    for ($r = 0; $r -lt $rowsIn.Count; $r++) {
        for ($c = 0; $c -lt $cols.Count; $c++) {
            # 두 가지를 조심한다.
            # 1) 첨자는 반드시 괄호로 묶는다. $grid[$r + 1, $c] 는 PowerShell 이
            #    $r + (1, $c) 로 읽어 배열 덧셈이 되고 op_Addition 오류가 난다.
            # 2) 열 이름은 변수에 받아 쓴다. .$($cols[$c]) 는 동적 속성으로 해석되지 않는다.
            $colName = $cols[$c]
            $grid[($r + 1), $c] = $rowsIn[$r].$colName
        }
    }
    return , $grid
}

# ---------------------------------------------------------------- Excel

function Invoke-Excel {
    param([string]$FullPath, [string]$OutPath)

    $app = New-Object -ComObject Excel.Application
    $app.Visible = $false
    $app.DisplayAlerts = $false
    $app.AskToUpdateLinks = $false
    $app.EnableEvents = $false
    $wb = $null
    try {
        $wb = $app.Workbooks.Open($FullPath, 0, $false)   # ReadOnly = $false : 쓰기 모드

        if ($Mode -eq 'Replace') {
            $map = Get-ReplacementMap
            foreach ($ws in $wb.Worksheets) {
                foreach ($key in $map.Keys) {
                    # Replace(What, Replacement, LookAt=xlPart(2), SearchOrder=xlByRows(1), MatchCase)
                    if ($ws.Cells.Replace($key, $map[$key], 2, 1, $false)) { $script:Changes++ }
                }
            }
            Write-Out "  치환 적용: 시트x검색어 기준 $script:Changes 건 성공 보고"
        }
        elseif ($Mode -eq 'Fill') {
            $grid = Import-DataGrid
            $rows = $grid.GetLength(0); $cols = $grid.GetLength(1)

            $ws = $null
            if ($Sheet) {
                foreach ($w in $wb.Worksheets) { if ($w.Name -eq $Sheet) { $ws = $w; break } }
                if (-not $ws) {
                    $ws = $wb.Worksheets.Add()
                    $ws.Name = $Sheet
                    Write-Out "  시트 생성: $Sheet"
                }
            }
            else { $ws = $wb.Worksheets.Item(1) }

            $start = $ws.Range($Cell)
            $target = $ws.Range($start, $start.Offset($rows - 1, $cols - 1))
            # 셀 하나씩 쓰면 COM 왕복이 rows*cols 번이다. 배열을 통째로 넣는다.
            $target.Value2 = $grid
            $script:Changes = $rows * $cols
            Write-Out ("  기록: {0}!{1} 에 {2}행 x {3}열" -f $ws.Name, $Cell, $rows, $cols)
        }

        $wb.SaveAs($OutPath, 51)   # xlOpenXMLWorkbook
    }
    finally {
        if ($wb) { try { $wb.Close($false) } catch { } }
        try { $app.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- Word

function Invoke-Word {
    param([string]$FullPath, [string]$OutPath)

    $app = New-Object -ComObject Word.Application
    $app.Visible = $false
    $app.DisplayAlerts = 0
    $doc = $null
    try {
        $doc = $app.Documents.Open($FullPath, $false, $false, $false)   # ReadOnly = $false

        if ($Mode -eq 'Replace') {
            $map = Get-ReplacementMap
            foreach ($key in $map.Keys) {
                # 본문
                $find = $doc.Content.Find
                $find.ClearFormatting()
                $find.Replacement.ClearFormatting()
                # Execute(Find, MatchCase, MatchWholeWord, MatchWildcards, MatchSoundsLike,
                #         MatchAllWordForms, Forward, Wrap=wdFindContinue(1), Format,
                #         ReplaceWith, Replace=wdReplaceAll(2))
                if ($find.Execute($key, $false, $false, $false, $false, $false, $true, 1, $false, $map[$key], 2)) {
                    $script:Changes++
                }
                # 머리글·바닥글은 Content 에 안 잡힌다. 구역마다 따로 돌아야 한다.
                foreach ($sec in $doc.Sections) {
                    foreach ($hf in @($sec.Headers, $sec.Footers)) {
                        foreach ($part in $hf) {
                            try {
                                $f2 = $part.Range.Find
                                $f2.ClearFormatting()
                                $f2.Replacement.ClearFormatting()
                                if ($f2.Execute($key, $false, $false, $false, $false, $false, $true, 1, $false, $map[$key], 2)) {
                                    $script:Changes++
                                }
                            }
                            catch { }
                        }
                    }
                }
            }
            Write-Out "  치환 적용: $script:Changes 건 성공 보고"
            Write-Out '  ! 텍스트 상자·도형 안의 글자는 Find 로 잡히지 않는다. 결과를 눈으로 확인할 것'
        }
        elseif ($Mode -eq 'Fill') {
            throw '-Mode Fill 은 Excel 전용이다. Word 는 Replace 를 쓴다.'
        }

        try { $doc.SaveAs2($OutPath, 16) }   # wdFormatDocumentDefault
        catch { $doc.SaveAs($OutPath, 16) }  # SaveAs2 가 없는 구버전
    }
    finally {
        if ($doc) { try { $doc.Close(0) } catch { } }
        try { $app.Quit(0) } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- PowerPoint

function Invoke-ShapeReplace {
    <# 도형 트리를 재귀로 훑으며 치환한다.
       표·그룹 안의 글자는 최상위 열거로는 닿지 않는다. #>
    param($Shapes, [hashtable]$Map, [int]$Depth = 0)
    if ($Depth -gt 6) { return }

    foreach ($shape in $Shapes) {
        $type = 0
        try { $type = [int]$shape.Type } catch { }

        if ($type -eq 6) {   # msoGroup
            try { Invoke-ShapeReplace -Shapes $shape.GroupItems -Map $Map -Depth ($Depth + 1) } catch { }
            continue
        }

        $hasTable = $false
        try { $hasTable = ($shape.HasTable -eq -1) } catch { }
        if ($hasTable) {
            try {
                $tbl = $shape.Table
                for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                    for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                        $tr = $tbl.Cell($r, $c).Shape.TextFrame.TextRange
                        foreach ($k in $Map.Keys) {
                            $found = $tr.Replace($k, $Map[$k])
                            if ($found) { $script:Changes++ }
                        }
                    }
                }
            }
            catch { }
            continue
        }

        $hasText = $false
        try { $hasText = ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) } catch { }
        if ($hasText) {
            try {
                $tr = $shape.TextFrame.TextRange
                foreach ($k in $Map.Keys) {
                    $found = $tr.Replace($k, $Map[$k])
                    if ($found) { $script:Changes++ }
                }
            }
            catch { }
        }
    }
}

function Invoke-PowerPoint {
    param([string]$FullPath, [string]$OutPath)

    $app = New-Object -ComObject PowerPoint.Application
    $pres = $null
    try {
        # ReadOnly = $false, WithWindow = $false
        $pres = $app.Presentations.Open($FullPath, $false, $false, $false)

        if ($Mode -eq 'Replace') {
            $map = Get-ReplacementMap
            for ($i = 1; $i -le $pres.Slides.Count; $i++) {
                $slide = $pres.Slides.Item($i)
                Invoke-ShapeReplace -Shapes $slide.Shapes -Map $map
            }
            Write-Out "  치환 적용: $script:Changes 건 (표·그룹 포함)"
            Write-Out '  ! SmartArt 안의 글자는 치환되지 않는다'
        }
        elseif ($Mode -eq 'Fill') {
            throw '-Mode Fill 은 Excel 전용이다.'
        }

        # SaveCopyAs 는 열린 프레젠테이션의 경로를 바꾸지 않는다.
        $pres.SaveCopyAs($OutPath, 24)   # ppSaveAsOpenXMLPresentation
    }
    finally {
        if ($pres) { try { $pres.Close() } catch { } }
        try { $app.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- 한/글

function Invoke-Hwp {
    param([string]$FullPath, [string]$OutPath)

    $hwp = $null
    try { $hwp = New-Object -ComObject HWPFrame.HwpObject }
    catch { throw "한/글이 설치되어 있지 않거나 COM 등록이 안 됐다: $($_.Exception.Message)" }

    try {
        $registered = $false
        try { $registered = [bool]$hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule') } catch { }
        if (-not $registered) {
            Write-Out '  참고: FilePathCheckerModule 미등록. 보안 대화상자가 뜨면 수동으로 허용한다.'
        }

        $opened = $false
        try { $opened = [bool]$hwp.Open($FullPath, '', '') } catch { }
        if (-not $opened) { throw 'OPEN FAILED — 열람/편집 권한이 없다' }

        if ($Mode -eq 'Replace') {
            throw '한/글 치환은 이 스킬에서 지원하지 않는다. HAction 기반이라 별도 검증이 필요하다. Protect 만 쓴다.'
        }
        if ($Mode -eq 'Fill') { throw '-Mode Fill 은 Excel 전용이다.' }

        [void]$hwp.SaveAs($OutPath, 'HWP', '')
    }
    finally {
        if ($hwp) {
            try { $hwp.Clear(1) } catch { }
            try { $hwp.Quit() } catch { }
            try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($hwp) } catch { }
        }
    }
}

# ---------------------------------------------------------------- main

if (-not (Test-Path -LiteralPath $Path)) { Write-Host "NOT FOUND: $Path"; exit 1 }
$full = (Resolve-Path -LiteralPath $Path).Path
$ext = [IO.Path]::GetExtension($full).ToLowerInvariant()

if ($LogFile) { $script:Log = New-Object System.IO.StreamWriter($LogFile, $false, (New-Object System.Text.UTF8Encoding $true)) }

try {
    Write-Out "mode   : $Mode"
    Write-Out "source : $full"

    if (Test-DocumentLocked -FullPath $full) {
        Write-Out ''
        Write-Out '중단: 문서가 열려 있다 (~$ 잠금 파일 발견).'
        Write-Out '해당 문서를 닫고 다시 실행한다. 열린 채로 저장하면 편집 내용이 사라질 수 있다.'
        exit 1
    }

    $outPath = Get-OutPath -FullPath $full
    Write-Out "output : $outPath"

    if ($outPath -eq $full) {
        Write-Out ''
        Write-Out '*** 원본을 덮어쓴다 ***'
        Backup-Original -FullPath $full -OutPath $outPath
    }
    elseif ((Test-Path -LiteralPath $outPath) -and -not $Overwrite) {
        Write-Out ''
        Write-Out "중단: 출력 파일이 이미 있다. 다른 -Out 을 주거나 -Overwrite 를 명시한다."
        exit 1
    }
    Write-Out ''

    switch -Regex ($ext) {
        '^\.(xlsx|xlsm|xls|xltx)$' { Invoke-Excel      -FullPath $full -OutPath $outPath }
        '^\.(docx|doc|dotx|rtf)$' { Invoke-Word       -FullPath $full -OutPath $outPath }
        '^\.(pptx|ppt|potx)$' { Invoke-PowerPoint -FullPath $full -OutPath $outPath }
        '^\.(hwp|hwpx)$' { Invoke-Hwp        -FullPath $full -OutPath $outPath }
        default { throw "지원하지 않는 확장자: $ext" }
    }

    if (-not (Test-Path -LiteralPath $outPath)) { throw '저장이 끝났다는데 출력 파일이 없다' }
    Write-Out "저장 완료: $outPath"
    Write-Out ''
    Write-Out '다음: 보호 여부를 반드시 확인한다'
    Write-Out "  python verify_protection.py `"$outPath`""
    Write-Out 'DRM 이 다시 걸리지 않았다면 그 파일은 원본과 같은 내용을 담은 무방비 사본이다.'
    Write-Out 'DONE'
}
catch {
    Write-Out "FAILED: $($_.Exception.Message)"
    Write-Out '원본은 변경되지 않았을 가능성이 높지만, 덮어쓰기 모드였다면 .bak 을 확인한다.'
    exit 1
}
finally {
    if ($script:Log) { $script:Log.Close() }
}
