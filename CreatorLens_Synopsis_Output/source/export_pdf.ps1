# Export the synopsis to PDF with Microsoft Word in a separate, time-limited instance.
# Usage (from the project root):  powershell -ExecutionPolicy Bypass -File CreatorLens_Synopsis_Output\source\export_pdf.ps1
$folder = Split-Path -Parent $PSScriptRoot
$docx = Join-Path $folder "CreatorLens_Project_Synopsis.docx"
$pdf = Join-Path $folder "CreatorLens_Project_Synopsis.pdf"
$before = @(Get-Process WINWORD -ErrorAction SilentlyContinue | ForEach-Object { $_.Id })
$job = Start-Job -ArgumentList $docx, $pdf {
    param($docx, $pdf)
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($docx, $false, $true, $false)
    $document.Fields.Update() | Out-Null
    $pages = $document.ComputeStatistics(2)
    $document.SaveAs2([ref]$pdf, [ref]17)
    $document.Close([ref]$false)
    $word.Quit()
    "Exported $pdf ($pages pages)"
}
if (Wait-Job $job -Timeout 150) {
    Receive-Job $job
} else {
    "PDF export timed out."
    Get-Process WINWORD -ErrorAction SilentlyContinue | Where-Object { $before -notcontains $_.Id } | Stop-Process -Force
}
Remove-Job $job -Force
