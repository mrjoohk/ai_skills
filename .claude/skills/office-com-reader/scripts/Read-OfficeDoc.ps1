<#
.SYNOPSIS
    파이썬으로 열리지 않는 Office/한글 문서를 COM 으로 판독한다.

.DESCRIPTION
    문서보안(DRM) 솔루션이 허용 앱으로 등록해 둔 Office/한글 애플리케이션에게
    파일을 열게 하고 COM 으로 값을 받아온다. 암호를 해독하거나 키를 추출하지 않는다.
    허용 앱이 아니면 이 스크립트도 실패하며, 그것이 정상 동작이다.

    기본 동작은 어떤 파일도 만들지 않는 것이다. -Dump 를 줄 때만 평문이 디스크에 남는다.

    반드시 UTF-8 BOM 으로 저장할 것. BOM 이 없으면 Windows PowerShell 5.1 이
    한글 리터럴을 ANSI 로 읽어 키워드 매칭이 조용히 실패한다.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Read-OfficeDoc.ps1 -Path "C:\doc.xlsx"
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Read-OfficeDoc.ps1 -Path "C:\doc.xlsx" -Pattern "헬기,모기체"
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Read-OfficeDoc.ps1 -Path "C:\doc.xlsx" -Dump -OutDir "C:\out"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$Pattern,
    [string]$Sheet,
    [switch]$Dump,
    [string]$OutDir,
    [string]$LogFile,
    [int]$MaxRows = 5000,
    [int]$MaxCols = 200,
    [bool]$ExportImages = $true,   # pptx 슬라이드 PNG 내보내기. 끄려면 -ExportImages:$false
    [int]$ImageWidth = 1600,
    [switch]$FillMerged,
    [int]$Preview = 5
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }

$script:Log = $null
$script:Hits = 0
$script:Written = @()

function Write-Out {
    param([string]$Text = '')
    Write-Host $Text
    if ($script:Log) { $script:Log.WriteLine($Text) }
}

function New-Utf8Writer {
    param([string]$FilePath)
    New-Object System.IO.StreamWriter($FilePath, $false, (New-Object System.Text.UTF8Encoding $true))
}

function Get-Keywords {
    if (-not $Pattern) { return @() }
    return @($Pattern -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

function Test-Hit {
    <# 키워드에 걸리면 위치와 문맥을 출력하고 $true 를 돌려준다. #>
    param([string]$Text, [string]$Where, [string[]]$Keys)
    if (-not $Keys -or [string]::IsNullOrEmpty($Text)) { return $false }
    foreach ($k in $Keys) {
        if ($Text.IndexOf($k, [StringComparison]::OrdinalIgnoreCase) -ge 0) {
            $snip = ($Text -replace '\s+', ' ')
            if ($snip.Length -gt 120) { $snip = $snip.Substring(0, 120) }
            Write-Out ("  [{0}] {1}  {2}" -f $k, $Where, $snip)
            $script:Hits++
            return $true
        }
    }
    return $false
}

function Get-SafeName {
    param([string]$Name)
    $safe = ($Name -replace '[\\/:*?"<>|]', '_').Trim()
    if (-not $safe) { $safe = 'unnamed' }
    return $safe
}

function Initialize-DumpDir {
    <# 덤프 폴더를 만들고 경고문과 .gitignore 등록을 함께 처리한다. #>
    param([string]$Dir, [string]$SourcePath)
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null

    $warn = Join-Path $Dir '_READ_ME_FIRST.txt'
    $lines = @(
        '이 폴더의 파일은 문서보안(DRM)이 적용된 원본에서 추출한 평문 사본이다.',
        '원본과 달리 복사, 메일 첨부, 외부 업로드가 아무 제약 없이 가능하다.',
        '',
        "원본 : $SourcePath",
        '',
        '- 분석이 끝나면 삭제한다.',
        '- 저장소에 커밋하지 않는다 (.gitignore 등록 여부를 확인할 것).',
        '- 외부로 반출하기 전에 사내 보안 규정을 확인한다.'
    )
    $w = New-Utf8Writer $warn
    foreach ($l in $lines) { $w.WriteLine($l) }
    $w.Close()

    # 상위로 올라가며 저장소 루트를 찾아 .gitignore 에 등록한다.
    $probe = Get-Item $Dir
    while ($probe -and -not (Test-Path (Join-Path $probe.FullName '.git'))) {
        $probe = $probe.Parent
    }
    if ($probe) {
        $gi = Join-Path $probe.FullName '.gitignore'
        $rel = $Dir.Substring($probe.FullName.Length).TrimStart('\', '/') -replace '\\', '/'
        $entry = "/$rel/"
        $existing = @()
        if (Test-Path $gi) { $existing = Get-Content $gi -Encoding UTF8 }
        if ($existing -notcontains $entry) {
            Add-Content -Path $gi -Value $entry -Encoding UTF8
            Write-Out "  .gitignore 에 등록: $entry"
        }
        else {
            Write-Out "  .gitignore 에 이미 등록됨: $entry"
        }
    }
    else {
        Write-Out '  경고: 상위에 git 저장소가 없어 .gitignore 등록을 건너뛴다.'
    }
}

function Write-VisualResult {
    <# 시각 산출물(PDF/PNG) 생성 결과를 한 줄로 보고한다.
       실패를 조용히 넘기면 "그림이 없는 문서"와 구분되지 않는다. #>
    param([string]$Path, [bool]$Ok, [string]$ErrMsg)
    if ($Ok) {
        $script:Written += $Path
        Write-Out ("  시각 산출물: {0}" -f (Split-Path -Leaf $Path))
    }
    else {
        Write-Out "  ! 시각 산출물 생성 실패: $ErrMsg"
        Write-Out "    (텍스트 추출은 위 결과대로 유효하다. 그림·서식은 확인할 수 없다)"
    }
}

function Get-VisualPath {
    param([string]$FullPath, [string]$Extension)
    return (Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($FullPath) + $Extension))
}

# ---------------------------------------------------------------- Excel

function Read-ExcelDoc {
    param([string]$FullPath, [string[]]$Keys)

    $app = New-Object -ComObject Excel.Application
    $app.Visible = $false
    $app.DisplayAlerts = $false
    $app.AskToUpdateLinks = $false
    $app.EnableEvents = $false
    $wb = $null
    try {
        $wb = $app.Workbooks.Open($FullPath, 0, $true)

        Write-Out '=== SHEETS ==='
        foreach ($ws in $wb.Worksheets) {
            $ur = $ws.UsedRange
            Write-Out ("  {0,-34} {1,7} rows x {2,4} cols" -f $ws.Name, $ur.Rows.Count, $ur.Columns.Count)
        }
        Write-Out ''

        foreach ($ws in $wb.Worksheets) {
            if ($Sheet -and $ws.Name -notlike "*$Sheet*") { continue }

            $ur = $ws.UsedRange
            $rows = [Math]::Min($ur.Rows.Count, $MaxRows)
            $cols = [Math]::Min($ur.Columns.Count, $MaxCols)
            if ($ur.Rows.Count -gt $MaxRows -or $ur.Columns.Count -gt $MaxCols) {
                Write-Out ("  ! {0}: {1}x{2} 중 {3}x{4} 만 읽는다 (-MaxRows/-MaxCols 로 조정)" -f `
                        $ws.Name, $ur.Rows.Count, $ur.Columns.Count, $rows, $cols)
            }

            # 셀별 COM 접근은 수십~수백 배 느리다. 반드시 한 번에 배열로 받는다.
            $vals = $ur.Value2
            if ($null -eq $vals) { continue }
            $single = ($ur.Rows.Count -eq 1 -and $ur.Columns.Count -eq 1)

            $writer = $null
            if ($Dump) {
                $csv = Join-Path $OutDir ((Get-SafeName $ws.Name) + '.csv')
                $writer = New-Utf8Writer $csv
                $script:Written += $csv
            }

            $lastSeen = New-Object 'string[]' ($cols + 1)
            $shown = 0
            for ($r = 1; $r -le $rows; $r++) {
                $line = New-Object System.Text.StringBuilder
                $rowText = New-Object System.Text.StringBuilder
                for ($c = 1; $c -le $cols; $c++) {
                    if ($single) { $v = $vals } else { $v = $vals[$r, $c] }
                    if ($null -eq $v) {
                        $s = ''
                        # 병합셀은 좌상단에만 값이 있고 나머지는 null 이다.
                        if ($FillMerged) { $s = $lastSeen[$c] }
                    }
                    else {
                        $s = [string]$v
                        $lastSeen[$c] = $s
                    }

                    if ($writer) {
                        if ($c -gt 1) { [void]$line.Append(',') }
                        [void]$line.Append('"' + ($s -replace '"', '""') + '"')
                    }
                    if ($s) { [void]$rowText.Append($s); [void]$rowText.Append(' ') }

                    if ($Keys.Count -gt 0) {
                        [void](Test-Hit -Text $s -Where ("{0}!R{1}C{2}" -f $ws.Name, $r, $c) -Keys $Keys)
                    }
                }
                if ($writer) { $writer.WriteLine($line.ToString()) }
                if ($Keys.Count -eq 0 -and -not $Dump -and $shown -lt $Preview) {
                    $t = ($rowText.ToString() -replace '\s+', ' ').Trim()
                    if ($t) {
                        if ($t.Length -gt 140) { $t = $t.Substring(0, 140) }
                        if ($shown -eq 0) { Write-Out ("--- {0} ---" -f $ws.Name) }
                        Write-Out "  $t"
                        $shown++
                    }
                }
            }
            if ($writer) {
                $writer.Close()
                Write-Out ("  덤프: {0}.csv  ({1} x {2})" -f (Get-SafeName $ws.Name), $rows, $cols)
            }
            if ($shown -gt 0) { Write-Out '' }
        }

        if ($ExportImages -and $OutDir) {
            $pdf = Get-VisualPath -FullPath $FullPath -Extension '.pdf'
            $ok = $false; $msg = ''
            try {
                # PageSetup 은 속성마다 프린터 드라이버와 통신해 극도로 느리다.
                # PrintCommunication 을 끄면 수십 배 빨라진다. 37시트에서 체감 차이가 크다.
                try { $app.PrintCommunication = $false } catch { }
                foreach ($ws in $wb.Worksheets) {
                    try {
                        $ps = $ws.PageSetup
                        $ps.Orientation = 2        # xlLandscape
                        $ps.Zoom = $false
                        $ps.FitToPagesWide = 1     # 가로를 한 페이지에 — ICD 표가 잘리지 않게
                        $ps.FitToPagesTall = $false
                    }
                    catch { }
                }
                try { $app.PrintCommunication = $true } catch { }

                $wb.ExportAsFixedFormat(0, $pdf)   # xlTypePDF
                $ok = Test-Path -LiteralPath $pdf
            }
            catch { $msg = $_.Exception.Message }
            Write-VisualResult -Path $pdf -Ok $ok -ErrMsg $msg
        }
    }
    finally {
        if ($wb) { try { $wb.Close($false) } catch { } }
        try { $app.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- Word

function Read-WordDoc {
    param([string]$FullPath, [string[]]$Keys)

    $app = New-Object -ComObject Word.Application
    $app.Visible = $false
    $app.DisplayAlerts = 0   # wdAlertsNone. 불리언이 아니라 열거형이다.
    $doc = $null
    try {
        # Open(FileName, ConfirmConversions, ReadOnly, AddToRecentFiles)
        $doc = $app.Documents.Open($FullPath, $false, $true, $false)

        $nPara = $doc.Paragraphs.Count
        $nTbl = $doc.Tables.Count
        Write-Out '=== WORD ==='
        Write-Out ("  문단 {0}개 · 표 {1}개 · 구역 {2}개" -f $nPara, $nTbl, $doc.Sections.Count)
        Write-Out ''

        # 본문 전체를 COM 호출 한 번으로 가져온다. 문단을 하나씩 도는 것보다 훨씬 빠르다.
        # Word 는 문단 끝을 \r 로, 표의 셀/행 끝을 \a(0x07) 로 표시한다.
        $raw = [string]$doc.Content.Text
        $lines = @($raw -split "`r") | ForEach-Object { ($_ -replace "[\x07]", ' ').Trim() }
        $body = @($lines | Where-Object { $_ })

        # 제목 스타일은 문단 개체를 통해서만 알 수 있다. 개수를 제한해 순회한다.
        $headCap = [Math]::Min($nPara, 1000)
        $heads = @()
        for ($i = 1; $i -le $headCap; $i++) {
            $para = $null
            try { $para = $doc.Paragraphs.Item($i) } catch { continue }
            $style = ''
            try { $style = [string]$para.Style.NameLocal } catch { }
            if ($style -match '제목|Heading|Title') {
                $t = ($para.Range.Text -replace "[\r\x07]", '').Trim()
                if ($t) {
                    if ($t.Length -gt 100) { $t = $t.Substring(0, 100) }
                    $heads += ("[{0}] {1}" -f $style, $t)
                }
            }
        }

        if ($Keys.Count -gt 0) {
            for ($i = 0; $i -lt $body.Count; $i++) {
                [void](Test-Hit -Text $body[$i] -Where ("문단 {0}" -f ($i + 1)) -Keys $Keys)
            }
        }
        else {
            Write-Out '--- 개요 (제목 스타일) ---'
            if ($heads.Count -eq 0) {
                Write-Out '  (제목 스타일 문단 없음)'
            }
            else {
                foreach ($h in $heads) { Write-Out "  $h" }
            }
            if ($nPara -gt $headCap) {
                Write-Out ("  … 앞 {0}문단만 스타일 검사" -f $headCap)
            }
            Write-Out ''
            # 제목이 하나도 없는 문서에서도 반드시 본문을 보여준다.
            Write-Out '--- 본문 미리보기 ---'
            if ($body.Count -eq 0) {
                Write-Out '  (본문 텍스트 없음 — 이미지/도형만 있는 문서일 수 있다)'
            }
            $show = [Math]::Min($body.Count, $Preview)
            for ($i = 0; $i -lt $show; $i++) {
                $t = $body[$i]
                if ($t.Length -gt 140) { $t = $t.Substring(0, 140) }
                Write-Out "  $t"
            }
            if ($body.Count -gt $show) {
                Write-Out ("  … ({0}개 더). 전체를 보려면 -Preview {1} 또는 -Dump" -f ($body.Count - $show), $body.Count)
            }
        }

        if ($Dump) {
            $out = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($FullPath) + '.txt')
            $writer = New-Utf8Writer $out
            foreach ($l in $body) { $writer.WriteLine($l) }
            for ($t = 1; $t -le $nTbl; $t++) {
                $tbl = $doc.Tables.Item($t)
                $writer.WriteLine("--- 표 $t ---")
                for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                    $cells = @()
                    for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                        $cellText = ''
                        try { $cellText = ($tbl.Cell($r, $c).Range.Text -replace "[\r\x07]", '').Trim() } catch { }
                        $cells += $cellText
                    }
                    $writer.WriteLine(($cells -join ' | '))
                }
            }
            $writer.Close()
            $script:Written += $out
            Write-Out ''
            Write-Out "  덤프: $out"
        }

        if ($ExportImages -and $OutDir) {
            $pdf = Get-VisualPath -FullPath $FullPath -Extension '.pdf'
            $ok = $false; $msg = ''
            try {
                $doc.ExportAsFixedFormat($pdf, 17)   # wdExportFormatPDF
                $ok = Test-Path -LiteralPath $pdf
            }
            catch { $msg = $_.Exception.Message }
            Write-VisualResult -Path $pdf -Ok $ok -ErrMsg $msg
        }
    }
    finally {
        if ($doc) { try { $doc.Close(0) } catch { } }
        try { $app.Quit(0) } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- PowerPoint

function Get-ShapeTexts {
    <# 슬라이드 도형에서 텍스트를 모은다.
       평범한 텍스트 상자만 훑으면 표·그룹·SmartArt 안의 내용이 통째로 빠진다.
       ICD·구성도 자료는 내용의 대부분이 거기 들어 있다. #>
    param($Shapes, [int]$Depth = 0)

    $out = @()
    if ($Depth -gt 6) { return $out }

    # 도형은 z-order(생성 순서)대로 열거된다. 그대로 뽑으면 구성도가 뒤죽박죽이 된다.
    # 위 -> 아래, 왼쪽 -> 오른쪽으로 정렬한다. Top 은 10pt 단위로 뭉쳐
    # 같은 줄에 놓인 도형들이 좌우 순서로 이어지게 한다.
    $ordered = @($Shapes)
    try {
        $ordered = $ordered | Sort-Object `
            @{ Expression = { $v = 99999.0; try { $v = [double]$_.Top } catch { }; [Math]::Round($v / 10.0) } }, `
            @{ Expression = { $v = 99999.0; try { $v = [double]$_.Left } catch { }; $v } }
    }
    catch { $ordered = @($Shapes) }

    foreach ($shape in $ordered) {
        $type = 0
        try { $type = [int]$shape.Type } catch { }

        # msoGroup = 6. 하위 도형은 상위 열거에 안 잡히므로 재귀한다.
        if ($type -eq 6) {
            try { $out += Get-ShapeTexts -Shapes $shape.GroupItems -Depth ($Depth + 1) } catch { }
            continue
        }

        # 표는 TextFrame 이 없다. Table.Cell 로 따로 훑는다.
        $hasTable = $false
        try { $hasTable = ($shape.HasTable -eq -1) } catch { }
        if ($hasTable) {
            try {
                $tbl = $shape.Table
                for ($r = 1; $r -le $tbl.Rows.Count; $r++) {
                    $cells = @()
                    for ($c = 1; $c -le $tbl.Columns.Count; $c++) {
                        $ct = ''
                        try { $ct = [string]$tbl.Cell($r, $c).Shape.TextFrame.TextRange.Text } catch { }
                        $cells += (($ct -replace '[\r\v\n]', ' ') -replace '\s+', ' ').Trim()
                    }
                    $out += ('| ' + ($cells -join ' | ') + ' |')
                }
            }
            catch { }
            continue
        }

        # SmartArt 도 TextFrame 으로는 안 잡힌다.
        $hasSmart = $false
        try { $hasSmart = ($shape.HasSmartArt -eq -1) } catch { }
        if ($hasSmart) {
            try {
                foreach ($node in $shape.SmartArt.AllNodes) {
                    $nt = ''
                    try { $nt = [string]$node.TextFrame2.TextRange.Text } catch { }
                    if ($nt.Trim()) { $out += $nt.Trim() }
                }
            }
            catch { }
            continue
        }

        $hasText = $false
        try { $hasText = ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) } catch { }
        if ($hasText) {
            try { $out += [string]$shape.TextFrame.TextRange.Text } catch { }
        }
    }
    return $out
}

function Read-PowerPointDoc {
    param([string]$FullPath, [string[]]$Keys)

    # PowerPoint 는 Visible=$false 를 거부하는 버전이 있어 창 없이 여는 쪽으로 우회한다.
    $app = New-Object -ComObject PowerPoint.Application
    $pres = $null
    try {
        # Open(FileName, ReadOnly, Untitled, WithWindow)
        $pres = $app.Presentations.Open($FullPath, $true, $false, $false)

        $n = $pres.Slides.Count
        Write-Out '=== SLIDES ==='
        Write-Out ("  슬라이드 {0}개" -f $n)
        Write-Out ''

        $writer = $null
        if ($Dump) {
            $out = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($FullPath) + '.txt')
            $writer = New-Utf8Writer $out
            $script:Written += $out
        }

        for ($i = 1; $i -le $n; $i++) {
            $slide = $pres.Slides.Item($i)

            $texts = @()
            try { $texts = @(Get-ShapeTexts -Shapes $slide.Shapes) } catch { }
            # 줄바꿈 정규화: PowerPoint 는 문단을 \r, 강제개행을 \v 로 쓴다.
            $texts = @($texts | ForEach-Object { ($_ -replace '[\r\v]', "`n") } | Where-Object { $_.Trim() })

            $notes = @()
            try {
                foreach ($ns in $slide.NotesPage.Shapes) {
                    $ok = $false
                    try { $ok = ($ns.HasTextFrame -eq -1 -and $ns.TextFrame.HasText -eq -1) } catch { }
                    if ($ok) {
                        $nt = [string]$ns.TextFrame.TextRange.Text
                        if ($nt.Trim()) { $notes += ($nt -replace '[\r\v]', "`n") }
                    }
                }
            }
            catch { }

            $title = ''
            if ($texts.Count -gt 0) { $title = (($texts[0] -replace '\s+', ' ')).Trim() }
            if ($title.Length -gt 80) { $title = $title.Substring(0, 80) }

            if ($Keys.Count -eq 0 -and -not $Dump) {
                Write-Out ("  {0,3}. {1}   (텍스트 {2}블록{3})" -f $i, $title, $texts.Count, `
                    $(if ($notes.Count -gt 0) { ", 노트 $($notes.Count)" } else { '' }))
            }

            if ($writer) {
                $writer.WriteLine("===== 슬라이드 $i =====")
                foreach ($t in $texts) { $writer.WriteLine($t.Trim()) }
                if ($notes.Count -gt 0) {
                    $writer.WriteLine('--- 발표자 노트 ---')
                    foreach ($t in $notes) { $writer.WriteLine($t.Trim()) }
                }
                $writer.WriteLine('')
            }

            if ($Keys.Count -gt 0) {
                foreach ($t in $texts) {
                    [void](Test-Hit -Text $t -Where ("슬라이드 {0}" -f $i) -Keys $Keys)
                }
                foreach ($t in $notes) {
                    [void](Test-Hit -Text $t -Where ("슬라이드 {0} 노트" -f $i) -Keys $Keys)
                }
            }
        }

        if ($writer) {
            $writer.Close()
            Write-Out "  덤프 완료 (표·그룹·SmartArt·발표자 노트 포함)"
        }

        if ($ExportImages -and $OutDir) {
            # 슬라이드를 그림으로 내보낸다. 다이어그램·스크린샷은 텍스트로 복원할 수 없으므로
            # 이것이 비DRM 경로와의 가장 큰 격차를 메운다.
            $pxW = $ImageWidth
            $pxH = [int][Math]::Round($ImageWidth * 9.0 / 16.0)
            try {
                $sw = [double]$pres.PageSetup.SlideWidth
                $sh = [double]$pres.PageSetup.SlideHeight
                if ($sw -gt 0) { $pxH = [int][Math]::Round($ImageWidth * ($sh / $sw)) }
            }
            catch { }

            $okCount = 0
            $failFirst = ''
            for ($i = 1; $i -le $n; $i++) {
                $png = Join-Path $OutDir ("slide_{0:D2}.png" -f $i)
                try {
                    $pres.Slides.Item($i).Export($png, 'PNG', $pxW, $pxH)
                    $script:Written += $png
                    $okCount++
                }
                catch {
                    if (-not $failFirst) { $failFirst = $_.Exception.Message }
                }
            }
            Write-Out ("  PNG {0}/{1}장 ({2}x{3})" -f $okCount, $n, $pxW, $pxH)
            if ($okCount -lt $n) {
                Write-Out "  ! 일부 실패: $failFirst"
            }

            # PDF 도 한 부 남긴다. 슬라이드가 많을 때 PNG 를 낱장으로 여는 것보다 훑기 쉽다.
            $pdf = Get-VisualPath -FullPath $FullPath -Extension '.pdf'
            $okPdf = $false; $msgPdf = ''
            try {
                # SaveCopyAs 는 열려 있는 프레젠테이션의 경로를 바꾸지 않는다. SaveAs 를 쓰면 안 된다.
                $pres.SaveCopyAs($pdf, 32)   # ppSaveAsPDF
                $okPdf = Test-Path -LiteralPath $pdf
            }
            catch { $msgPdf = $_.Exception.Message }
            Write-VisualResult -Path $pdf -Ok $okPdf -ErrMsg $msgPdf
        }
    }
    finally {
        if ($pres) { try { $pres.Close() } catch { } }
        try { $app.Quit() } catch { }
        try { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) } catch { }
    }
}

# ---------------------------------------------------------------- 한/글

function Read-HwpDoc {
    param([string]$FullPath, [string[]]$Keys)

    Write-Out '=== HWP ==='

    $hwp = $null
    try {
        $hwp = New-Object -ComObject HWPFrame.HwpObject
    }
    catch {
        Write-Out "  한/글이 설치되어 있지 않거나 COM 등록이 안 됐다: $($_.Exception.Message)"
        Write-Out '  .hwpx 라면 DRM 이 없을 수 있다 — read_hwpx.py 를 먼저 시도한다.'
        return
    }

    try {
        # 이것이 없으면 파일을 열 때마다 보안 경고 대화상자가 뜬다.
        # 모듈이 레지스트리에 등록돼 있지 않으면 실패하며, 그때는 사람이 클릭해야 한다.
        # 반환값을 반드시 삼킨다. 그냥 호출하면 True/False 가 출력에 섞인다.
        # 등록에 실패($false)해도 Open 이 되는 환경이 있으므로 중단하지 않고 계속한다.
        $registered = $false
        try { $registered = [bool]$hwp.RegisterModule('FilePathCheckDLL', 'FilePathCheckerModule') }
        catch { $registered = $false }
        if (-not $registered) {
            Write-Out '  참고: FilePathCheckerModule 미등록. 보안 대화상자가 뜨면 수동으로 허용한다.'
            Write-Out '        (미등록이어도 열리는 환경이 있다 — 아래에서 실제 결과를 확인할 것)'
        }

        $opened = $false
        try { $opened = [bool]$hwp.Open($FullPath, '', '') } catch { $opened = $false }
        if (-not $opened) {
            Write-Out '  OPEN FAILED — 열람 권한이 없거나 지원되지 않는 형식이다.'
            return
        }

        $text = [string]$hwp.GetTextFile('TEXT', '')
        $lines = @($text -split '\r?\n')
        Write-Out ("  문단 {0}줄" -f $lines.Count)
        Write-Out ''

        if ($Dump) {
            $out = Join-Path $OutDir ([IO.Path]::GetFileNameWithoutExtension($FullPath) + '.txt')
            $w = New-Utf8Writer $out
            $w.Write($text)
            $w.Close()
            $script:Written += $out
            Write-Out "  덤프: $out"
        }

        if ($ExportImages -and $OutDir) {
            $pdf = Get-VisualPath -FullPath $FullPath -Extension '.pdf'
            $ok = $false; $msg = ''
            try {
                [void]$hwp.SaveAs($pdf, 'PDF', '')
                $ok = Test-Path -LiteralPath $pdf
                if (-not $ok) { $msg = 'SaveAs 는 성공했다고 하는데 파일이 없다. 한/글 버전이 PDF 저장을 지원하지 않을 수 있다.' }
            }
            catch { $msg = $_.Exception.Message }
            Write-VisualResult -Path $pdf -Ok $ok -ErrMsg $msg
        }

        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ($Keys.Count -gt 0) {
                [void](Test-Hit -Text $line -Where ("줄 {0}" -f ($i + 1)) -Keys $Keys)
            }
            elseif ($i -lt $Preview -and $line.Trim()) {
                Write-Out ("  {0}" -f $line.Trim())
            }
        }
        if ($Keys.Count -eq 0 -and $lines.Count -gt $Preview) {
            Write-Out ("  … ({0}줄 더). 전체를 보려면 -Preview {1} 또는 -Dump" -f ($lines.Count - $Preview), $lines.Count)
        }
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

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "NOT FOUND: $Path"
    exit 1
}
$full = (Resolve-Path -LiteralPath $Path).Path
$ext = [IO.Path]::GetExtension($full).ToLowerInvariant()

if ($LogFile) { $script:Log = New-Utf8Writer $LogFile }

try {
    Write-Out "source : $full"
    $keys = Get-Keywords
    if ($keys.Count -gt 0) { Write-Out ("pattern: {0}" -f ($keys -join ', ')) }

    $needsOutDir = $Dump -or $ExportImages
    if ($needsOutDir) {
        if (-not $OutDir) {
            $OutDir = Join-Path (Split-Path -Parent $full) ([IO.Path]::GetFileNameWithoutExtension($full) + '_extract')
        }
        Write-Out ''
        if ($Dump) {
            Write-Out '*** -Dump: 평문 파일이 디스크에 남는다. 원본이 DRM 문서라면 취급에 주의할 것. ***'
        }
        else {
            Write-Out '*** -ExportImages(기본 켜짐): 시각 산출물(PDF/PNG)이 디스크에 남는다. 끄려면 -ExportImages:$false ***'
        }
        Initialize-DumpDir -Dir $OutDir -SourcePath $full
    }
    Write-Out ''

    switch -Regex ($ext) {
        '^\.(xlsx|xlsm|xlsb|xltx|xls)$' { Read-ExcelDoc      -FullPath $full -Keys $keys }
        '^\.(docx|doc|rtf|dotx)$' { Read-WordDoc       -FullPath $full -Keys $keys }
        '^\.(pptx|ppt|potx)$' { Read-PowerPointDoc -FullPath $full -Keys $keys }
        '^\.(hwp|hwpx)$' { Read-HwpDoc        -FullPath $full -Keys $keys }
        default {
            Write-Out "지원하지 않는 확장자: $ext"
            Write-Out 'probe_format.py 로 실제 포맷을 먼저 확인한다.'
        }
    }

    if ($keys.Count -gt 0) { Write-Out "`n총 $script:Hits 건 매칭" }
    if ($script:Written.Count -gt 0) {
        Write-Out ''
        Write-Out ("평문 산출물 {0}개: {1}" -f $script:Written.Count, $OutDir)
        Write-Out '분석이 끝나면 삭제한다.'
    }
    Write-Out 'DONE'
}
catch {
    Write-Out "FAILED: $($_.Exception.Message)"
    Write-Out '허용 앱이 아니거나 열람 권한이 없을 수 있다. 우회를 시도하지 말고 보안담당자에게 문의한다.'
    exit 1
}
finally {
    if ($script:Log) { $script:Log.Close() }
}
