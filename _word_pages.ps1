$path = "c:\Users\umesh\OneDrive\Desktop\report vinay sir.docx"
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open($path)
$doc.Repaginate() | Out-Null
$total = $doc.ComputeStatistics(2)
Write-Output "TOTAL_PAGES=$total"

$keys = @(
  "CANDIDATE'S DECLARATION",
  "CERTIFICATE",
  "ACKNOWLEDGEMENT",
  "ABSTRACT",
  "CONTENTS",
  "List of Figures",
  "List of Tables",
  "CHAPTER 1:",
  "CHAPTER 2:",
  "CHAPTER 3:",
  "CHAPTER 4:",
  "CHAPTER 5:",
  "REFERENCES",
  "Fig. 4.1",
  "Fig. 4.2",
  "Fig. 4.3",
  "Fig. 4.4",
  "Table 4.1",
  "Table 4.2"
)

foreach ($k in $keys) {
  $rng = $doc.Content
  $find = $rng.Find
  $find.ClearFormatting() | Out-Null
  $find.Text = $k
  $find.Forward = $true
  $find.Wrap = 0
  $ok = $find.Execute()
  if ($ok) {
    $pg = $rng.Information(3)
    Write-Output "$k=$pg"
  } else {
    Write-Output "$k=NOTFOUND"
  }
}

$doc.Close($false) | Out-Null
$word.Quit() | Out-Null
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($word) | Out-Null
