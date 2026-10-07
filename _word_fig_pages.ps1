$path = "c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($path)
try { $doc.ActiveWindow.View.Type = 3 } catch {}
$doc.Repaginate() | Out-Null
Start-Sleep -Seconds 1
Write-Output ("TOTAL_PAGES=" + $doc.ComputeStatistics(2))

$caps = @(
  "Fig. 4.1 ESP32-CAM hardware concept used in the project",
  "Fig. 4.2 System architecture of the dog detection and alert system",
  "Fig. 4.3 Detection and relay-hold workflow",
  "Fig. 4.4 Monitoring UI concept with DETECT ZONE and dog bounding box",
  "Table 4.1 Tools and Technologies Used",
  "Table 4.2 GPIO Pin Mapping"
)

foreach ($c in $caps) {
  for ($i = 1; $i -le $doc.Paragraphs.Count; $i++) {
    $p = $doc.Paragraphs.Item($i)
    $t = ($p.Range.Text -replace "[\r\a]", "").Trim()
    if ($t.StartsWith($c) -or $t -eq $c -or ($c.StartsWith("Table 4.1") -and $t.StartsWith("Table 4.1")) -or ($c.StartsWith("Table 4.2") -and $t.StartsWith("Table 4.2"))) {
      if ($t.Contains("....")) { continue }
      Write-Output ("{0} => {1}" -f $c.Substring(0, [Math]::Min(40,$c.Length)), $p.Range.Information(3))
      break
    }
  }
}

$doc.Close($false) | Out-Null
$word.Quit() | Out-Null
