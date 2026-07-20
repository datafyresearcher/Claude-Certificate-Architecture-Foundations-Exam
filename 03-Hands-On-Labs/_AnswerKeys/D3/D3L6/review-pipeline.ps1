# review-pipeline.ps1 - Two-stage headless CI: generate then review in isolation
# Stage 1: Generate the module in one session
# Stage 2: Review in a FRESH session (no generation context)
# Exit 1 if any blocking findings are found

param(
    [string]$Spec = "Write a Python function process_batch(records) that filters active records and calculates average score. Save to src/generated.py",
    [string]$OutputFile = "src/generated.py"
)

$ts = Get-Date -Format "HHmmss"

Write-Host "=== STAGE 1: Generating code ===" -ForegroundColor Cyan

claude -p $Spec --output-format json > "pipeline-gen-$ts.jsonl"

$genResult = Get-Content "pipeline-gen-$ts.jsonl" |
ForEach-Object { $_ | ConvertFrom-Json } |
Where-Object { $_.type -eq "result" }

if ($genResult.is_error) {
    Write-Error "Generation failed: $($genResult.result)"
    exit 1
}

Write-Host "Generated. Cost: `$$($genResult.total_cost_usd) | Duration: $($genResult.duration_ms)ms"

if (-not (Test-Path $OutputFile)) {
    Write-Error "Expected output file $OutputFile was not created."
    exit 1
}

Write-Host "`n=== STAGE 2: Isolated review (fresh session, no generation context) ===" -ForegroundColor Cyan

$code = Get-Content $OutputFile -Raw

$reviewPrompt = @"
You are a code reviewer. Review the following Python code for bugs.
Respond ONLY with a JSON array. Each item must have:
  - "severity": either "blocking" or "warning"
  - "line": approximate line number
  - "description": clear description of the issue

Code to review:
$code
"@

claude -p $reviewPrompt --output-format json > "pipeline-review-$ts.jsonl"

$reviewResult = Get-Content "pipeline-review-$ts.jsonl" |
ForEach-Object { $_ | ConvertFrom-Json } |
Where-Object { $_.type -eq "result" }

if ($reviewResult.is_error) {
    Write-Error "Review failed: $($reviewResult.result)"
    exit 1
}

Write-Host "Review complete. Cost: `$$($reviewResult.total_cost_usd) | Duration: $($reviewResult.duration_ms)ms`n"

# Extract JSON array from response (Claude may wrap it in markdown fences)
$responseText = $reviewResult.result
$jsonMatch = [regex]::Match($responseText, '\[[\s\S]*\]')

if (-not $jsonMatch.Success) {
    Write-Warning "Could not parse structured JSON findings from review. Raw output:"
    Write-Host $responseText
    exit 0
}

$findings = $jsonMatch.Value | ConvertFrom-Json

Write-Host "=== FINDINGS ===" -ForegroundColor Yellow
$blockingCount = 0
foreach ($finding in $findings) {
    $color = if ($finding.severity -eq "blocking") { "Red" } else { "Yellow" }
    Write-Host "[$($finding.severity.ToUpper())] Line $($finding.line): $($finding.description)" -ForegroundColor $color
    if ($finding.severity -eq "blocking") { $blockingCount++ }
}

Write-Host "`nTotal findings: $($findings.Count) ($blockingCount blocking)" -ForegroundColor Cyan
Write-Host "Artifacts: pipeline-gen-$ts.jsonl, pipeline-review-$ts.jsonl"

if ($blockingCount -gt 0) {
    Write-Host "`nPIPELINE FAILED: $blockingCount blocking finding(s)." -ForegroundColor Red
    exit 1
}
else {
    Write-Host "`nPIPELINE PASSED: No blocking findings." -ForegroundColor Green
    exit 0
}