# compare-reviews.ps1 - Side-by-side comparison of self-review vs isolated review

param(
    [string]$SelfReview = "review-self.jsonl",
    [string]$IsolatedReview = "review-isolated.jsonl"
)

function Extract-Findings {
    param([string]$File, [string]$Label)

    if (-not (Test-Path $File)) {
        Write-Warning "$Label file not found: $File"
        return $null
    }

    $result = Get-Content $File |
    ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object { $_.type -eq "result" }

    return [PSCustomObject]@{
        Label     = $Label
        Text      = $result.result
        Cost      = $result.total_cost_usd
        Duration  = $result.duration_ms
        SessionId = $result.session_id
    }
}

$self = Extract-Findings -File $SelfReview     -Label "SELF-REVIEW (resumed session)"
$isolated = Extract-Findings -File $IsolatedReview -Label "ISOLATED REVIEW (fresh session)"

# Display each review
foreach ($review in @($self, $isolated)) {
    if ($null -eq $review) { continue }

    $color = if ($review.Label -match "SELF") { "Yellow" } else { "Cyan" }
    Write-Host "`n$("=" * 70)" -ForegroundColor $color
    Write-Host " $($review.Label)" -ForegroundColor $color
    Write-Host " Cost: `$$($review.Cost) | Duration: $($review.Duration)ms"
    Write-Host "$("=" * 70)" -ForegroundColor $color
    Write-Host $review.Text
}

# Attempt to count findings by extracting JSON arrays from both results
function Count-Findings {
    param([string]$Text)
    $match = [regex]::Match($Text, '\[[\s\S]*\]')
    if ($match.Success) {
        try {
            $findings = $match.Value | ConvertFrom-Json
            return $findings.Count
        }
        catch { return "parse error" }
    }
    # Fallback: count lines starting with a number or dash that look like findings
    return ($Text -split "`n" | Where-Object { $_ -match '^\s*[-\d]' }).Count
}

$selfCount = if ($self) { Count-Findings $self.Text }     else { "N/A" }
$isolatedCount = if ($isolated) { Count-Findings $isolated.Text } else { "N/A" }

Write-Host "`n$("=" * 70)" -ForegroundColor White
Write-Host " SUMMARY" -ForegroundColor White
Write-Host "$("=" * 70)" -ForegroundColor White
Write-Host " Self-review findings:     $selfCount" -ForegroundColor Yellow
Write-Host " Isolated review findings: $isolatedCount" -ForegroundColor Cyan

if ($selfCount -ne "N/A" -and $isolatedCount -ne "N/A" -and
    $selfCount -is [int] -and $isolatedCount -is [int]) {
    $diff = $isolatedCount - $selfCount
    if ($diff -gt 0) {
        Write-Host " Delta:                    +$diff more from isolated review" -ForegroundColor Green
        Write-Host "`n Observation: Isolated review found more issues, consistent"
        Write-Host " with the expectation that removing authorship context reduces bias." -ForegroundColor Green
    }
    elseif ($diff -lt 0) {
        Write-Host " Delta:                    $diff (self-review found more)" -ForegroundColor Red
        Write-Host "`n Observation: Self-review found more issues this time. Results can"
        Write-Host " vary per run. Try running both reviews again to see the trend." -ForegroundColor Red
    }
    else {
        Write-Host " Delta:                    0 (same count)" -ForegroundColor White
        Write-Host "`n Observation: Same finding count. Compare the content: isolated"
        Write-Host " reviews often catch different categories of issues." -ForegroundColor White
    }
}
Write-Host ""