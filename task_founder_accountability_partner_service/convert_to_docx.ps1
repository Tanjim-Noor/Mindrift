$files = @{
    "executive_summary.md" = "Executive Summary.docx";
    "full_report.md" = "Full Report.docx";
    "buyer_personas_and_decision_journey.md" = "Buyer Personas & Decision Journey.docx";
    "buyer_psychology_deep_dive.md" = "Buyer Psychology Deep-Dive.docx";
    "pricing_psychology.md" = "Pricing Psychology & Willingness-to-Pay Guidance.docx"
}

$word = New-Object -ComObject Word.Application
$word.Visible = $false
$failure = $false

foreach ($mdFile in $files.Keys) {
    if (Test-Path $mdFile) {
        try {
            # Open MD file as text
            $doc = $word.Documents.Open((Get-Item $mdFile).FullName)
            $docxPath = Join-Path (Get-Location) $files[$mdFile]
            
            # Save as DOCX (16 = wdFormatDocumentDefault)
            $doc.SaveAs([ref]$docxPath, [ref]16)
            $doc.Close()
            Write-Host "Created: $docxPath"
        } catch {
            Write-Error "Failed to convert $mdFile : $_"
            $failure = $true
        }
    } else {
        Write-Warning "File not found: $mdFile"
    }
}

$word.Quit()
if ($failure) { exit 1 }
