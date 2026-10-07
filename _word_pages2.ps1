$path = "c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($path)
$doc.Repaginate() | Out-Null
Write-Output ("TOTAL_PAGES=" + $doc.ComputeStatistics(2))

# Walk paragraphs; record first exact/startswith hits with page numbers
$wanted = [ordered]@{
  "CANDIDATE'S DECLARATION" = $null
  "CERTIFICATE" = $null
  "ACKNOWLEDGEMENT" = $null
  "ABSTRACT" = $null
  "CONTENTS" = $null
  "List of Figures" = $null
  "List of Tables" = $null
  "CHAPTER 1: INTRODUCTION" = $null
  "CHAPTER 2: COMPANY INFRASTRUCTURE" = $null
  "CHAPTER 3: TRAINING ATTENDED" = $null
  "CHAPTER 4: SYSTEMS/PROJECT DEVELOPMENT" = $null
  "CHAPTER 5: RESULTS AND CONCLUSION" = $null
  "REFERENCES" = $null
  "Fig. 4.1" = $null
  "Fig. 4.2" = $null
  "Fig. 4.3" = $null
  "Fig. 4.4" = $null
  "Table 4.1" = $null
  "Table 4.2" = $null
}

$count = $doc.Paragraphs.Count
for ($i = 1; $i -le $count; $i++) {
  $p = $doc.Paragraphs.Item($i)
  $t = ($p.Range.Text -replace "[\r\a]", "").Trim()
  if ([string]::IsNullOrWhiteSpace($t)) { continue }
  $pg = $p.Range.Information(3)
  foreach ($k in @($wanted.Keys)) {
    if ($null -ne $wanted[$k]) { continue }
    if ($t -eq $k -or $t.StartsWith($k)) {
      # For List of Figures/Tables: skip TOC dotted lines
      if (($k -eq "List of Figures" -or $k -eq "List of Tables") -and $t.Contains(".")) {
        if ($t -ne $k) { continue }
      }
      $wanted[$k] = $pg
    }
  }
}

foreach ($k in $wanted.Keys) {
  Write-Output ("$k=" + $wanted[$k])
}

$doc.Close($false) | Out-Null
$word.Quit() | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
