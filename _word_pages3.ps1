$path = "c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($path)

# Force print layout so page numbers are accurate
try {
  $doc.ActiveWindow.View.Type = 3
} catch {}
$doc.Repaginate() | Out-Null
Start-Sleep -Seconds 2

Write-Output ("TOTAL_PAGES=" + $doc.ComputeStatistics(2))

$targets = @(
  @{ Key = "CANDIDATE'S DECLARATION"; Match = "CANDIDATE'S DECLARATION"; Exact = $true },
  @{ Key = "CERTIFICATE"; Match = "CERTIFICATE"; Exact = $true },
  @{ Key = "ACKNOWLEDGEMENT"; Match = "ACKNOWLEDGEMENT"; Exact = $true },
  @{ Key = "ABSTRACT"; Match = "ABSTRACT"; Exact = $true },
  @{ Key = "CONTENTS"; Match = "CONTENTS"; Exact = $true },
  @{ Key = "List of Figures"; Match = "List of Figures"; Exact = $true },
  @{ Key = "List of Tables"; Match = "List of Tables"; Exact = $true },
  @{ Key = "CHAPTER 1: INTRODUCTION"; Match = "CHAPTER 1:"; Exact = $false },
  @{ Key = "CHAPTER 2: COMPANY INFRASTRUCTURE"; Match = "CHAPTER 2:"; Exact = $false },
  @{ Key = "CHAPTER 3: TRAINING ATTENDED"; Match = "CHAPTER 3:"; Exact = $false },
  @{ Key = "CHAPTER 4: SYSTEMS/PROJECT DEVELOPMENT"; Match = "CHAPTER 4:"; Exact = $false },
  @{ Key = "CHAPTER 5: RESULTS AND CONCLUSION"; Match = "CHAPTER 5:"; Exact = $false },
  @{ Key = "REFERENCES"; Match = "REFERENCES"; Exact = $true },
  @{ Key = "Fig. 4.1"; Match = "Fig. 4.1"; Exact = $false },
  @{ Key = "Fig. 4.2"; Match = "Fig. 4.2"; Exact = $false },
  @{ Key = "Fig. 4.3"; Match = "Fig. 4.3"; Exact = $false },
  @{ Key = "Fig. 4.4"; Match = "Fig. 4.4"; Exact = $false },
  @{ Key = "Table 4.1"; Match = "Table 4.1 Tools"; Exact = $false },
  @{ Key = "Table 4.2"; Match = "Table 4.2 GPIO"; Exact = $false }
)

foreach ($t in $targets) {
  $found = $false
  $count = $doc.Paragraphs.Count
  for ($i = 1; $i -le $count; $i++) {
    $p = $doc.Paragraphs.Item($i)
    $text = ($p.Range.Text -replace "[\r\a]", "").Trim()
    if ([string]::IsNullOrWhiteSpace($text)) { continue }

    $ok = $false
    if ($t.Exact) {
      $ok = ($text -eq $t.Match)
    } else {
      $ok = $text.StartsWith($t.Match)
    }
    # skip TOC dotted lines
    if ($ok -and $text.Contains("....")) { $ok = $false }
    if ($ok -and ($t.Key -like "List of*") -and $text -ne $t.Match) { $ok = $false }

    if ($ok) {
      # Expand range and query page in print view
      $rng = $p.Range
      $pg = $rng.Information(3)
      Write-Output ("{0}={1}" -f $t.Key, $pg)
      $found = $true
      break
    }
  }
  if (-not $found) {
    Write-Output ("{0}=NOTFOUND" -f $t.Key)
  }
}

# Also dump every Heading 1 with page for debugging
Write-Output "---HEADINGS---"
for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
  $p = $doc.Paragraphs.Item($i)
  $style = $p.Style.NameLocal
  if ($style -like "Heading 1*") {
    $text = ($p.Range.Text -replace "[\r\a]", "").Trim()
    if ($text.Length -gt 0) {
      $pg = $p.Range.Information(3)
      Write-Output ("H1_p{0}:{1}" -f $pg, $text.Substring(0, [Math]::Min(60, $text.Length)))
    }
  }
}

$doc.Close($false) | Out-Null
$word.Quit() | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
