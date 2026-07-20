# D3L6 — Headless CI with Generator/Reviewer Isolation

**Exam mapping:** `-p` flag, `--output-format json`, session isolation for review
**Estimated time:** ~45 min
**Domain:** 3 - Claude Code Configuration & Workflows
**Key concept:** Same-session self-review is biased; isolated headless review finds more bugs

---

## Folder Structure

```
D3L6/
├── src/
│   ├── module.py               <- Step 1: planted bugs (bare except + swallowed exception)
│   └── generated.py            <- Step 3: Claude-generated module (created during lab)
├── review-output.jsonl         <- Step 2: raw JSONL from headless review (auto-created)
├── review-self.jsonl           <- Step 3: resumed-session self-review output
├── review-isolated.jsonl       <- Step 4: fresh isolated review output
├── compare-reviews.ps1         <- Step 5: side-by-side comparison script
└── review-pipeline.ps1         <- Step 6: two-stage headless CI script
```

---

## Step 1 — Seed the repo with two planted bugs

Create `src/module.py` with two intentional bugs (a worked copy lives in `../../_AnswerKeys/D3/D3L6/src/`):

```python
# src/module.py - intentionally buggy for Lab 6

def find_first_duplicate(items):
    """Return the first item that appears more than once.
    BUG 1 (bare except): uses a try/except pattern that silently masks errors.
    """
    try:
        seen = set()
        for item in items:
            if item in seen:
                return item
            seen.add(item)
    except:                            # <- BUG: bare except swallows TypeError on unhashable items
        pass
    return None


def load_config(filepath):
    """Load JSON config from a file.
    BUG 2 (swallowed exception): errors are silently ignored, returns None
    with no way for the caller to distinguish 'missing file' from 'bad JSON'
    from 'permission denied'.
    """
    try:
        with open(filepath) as f:
            import json
            return json.load(f)
    except:                            # <- BUG: bare except swallows all errors
        pass
    return None
```

> **Note on bug design:** Both bugs use bare `except:` clauses that swallow errors silently.
> This is a common production anti-pattern that reviewers should catch: the caller has no
> way to distinguish between a valid empty result and a masked failure. A good review should
> flag the bare excepts and recommend catching specific exception types.

---

## Step 2 — Run headless review and inspect the JSON envelope

Run the review and save output to a file:

```powershell
claude -p "Review src/module.py for bugs. Report as JSON array with fields: severity, line_number, description." --output-format json > review-output.jsonl
```

The output is **JSON Lines (JSONL)**: multiple JSON objects, one per line.
Inspect the file to understand the envelope structure:

```powershell
# Pretty-print all lines to understand the structure
Get-Content review-output.jsonl | ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }
```

**Expected envelope structure on the final "result" line:**
```json
{
  "type": "result",
  "subtype": "success",
  "total_cost_usd": 0.003,
  "is_error": false,
  "duration_ms": 2100,
  "result": "...[Claude response here]...",
  "session_id": "..."
}
```

Extract just the result line:
```powershell
Get-Content review-output.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.type -eq "result" } |
  ConvertTo-Json -Depth 5
```

You should see both bugs identified in the result text.

---

## Step 3 — Demonstrate self-review bias (same session, then resumed headless)

The goal is to produce a **parseable** self-review output where Claude still has
its generation context (authorship bias). This requires two parts: an interactive
session to generate the code, then a **resumed** headless session to capture
the self-review as JSONL.

### Part A: Generate code interactively

Start a new interactive session:
```powershell
claude
```

Ask Claude to write a module:
```
Write a Python function process_batch(records) that:
- Filters records where the "status" field equals "active"
- Calculates the average of the "score" field for those records
- Returns a dict with keys: count, average, max_score
Make it production-quality. Save it to src/generated.py
```

Verify the file was created, then **exit the session** (Ctrl+C or type `/exit`).

> **Why exit first?** We want the self-review as parseable JSONL, which requires
> headless mode (`-p`). But we also need the generation context preserved. The
> `--continue` flag solves this: it resumes the most recent session in the current
> directory with the full conversation history intact.

### Part B: Resumed headless self-review

Immediately after exiting (before running any other `claude` command in this directory):

```powershell
claude -c -p "Review the code you just wrote in src/generated.py for bugs. List every issue you find as a JSON array with fields: severity, description." --output-format json > review-self.jsonl
```

The `-c` (`--continue`) flag resumes the session from Part A. Claude sees the full
generation conversation: the spec you gave it, its reasoning, its tool calls, and the
code it produced. This is a true self-review with authorship context.

Verify the output:
```powershell
Get-Content review-self.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.type -eq "result" } |
  Select-Object -ExpandProperty result
```

> **Key detail:** `--continue` loads the most recent session for the current directory.
> If you accidentally run another `claude` or `claude -p` command between Part A and
> Part B, that new session becomes the most recent one and `--continue` will resume
> the wrong session. If you need to run other commands in between, capture the
> session_id from Part A and use `--resume <session_id>` instead.

---

## Step 4 — Fresh isolated review (no generation context)

Run a completely fresh headless session. No `--continue`, no `--resume`:

```powershell
$code = Get-Content src/generated.py -Raw

claude -p "You are a code reviewer with no prior context about this code. Review the following Python module for bugs, edge cases, and production issues. List every issue as a JSON array with fields: severity, description.`n`n$code" --output-format json > review-isolated.jsonl
```

This session has zero knowledge of the generation conversation. Claude approaches
the code as a pure reviewer with no authorship stake.

Verify:
```powershell
Get-Content review-isolated.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.type -eq "result" } |
  Select-Object -ExpandProperty result
```

---

## Step 5 — Compare self-review vs isolated review

Raw JSONL output is hard to compare side by side. Create `compare-reviews.ps1` to
extract findings from both files and present a structured summary:

```powershell
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
        Label      = $Label
        Text       = $result.result
        Cost       = $result.total_cost_usd
        Duration   = $result.duration_ms
        SessionId  = $result.session_id
    }
}

$self     = Extract-Findings -File $SelfReview     -Label "SELF-REVIEW (resumed session)"
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
        } catch { return "parse error" }
    }
    # Fallback: count lines starting with a number or dash that look like findings
    return ($Text -split "`n" | Where-Object { $_ -match '^\s*[-\d]' }).Count
}

$selfCount     = if ($self)     { Count-Findings $self.Text }     else { "N/A" }
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
    } elseif ($diff -lt 0) {
        Write-Host " Delta:                    $diff (self-review found more)" -ForegroundColor Red
        Write-Host "`n Observation: Self-review found more issues this time. Results can"
        Write-Host " vary per run. Try running both reviews again to see the trend." -ForegroundColor Red
    } else {
        Write-Host " Delta:                    0 (same count)" -ForegroundColor White
        Write-Host "`n Observation: Same finding count. Compare the content: isolated"
        Write-Host " reviews often catch different categories of issues." -ForegroundColor White
    }
}
Write-Host ""
```

Run the comparison:
```powershell
.\compare-reviews.ps1
```

> **What to look for beyond counts:** Even when finding counts are similar, compare the
> *types* of issues found. Self-reviews tend to surface style and naming suggestions
> (low-risk, doesn't challenge the author's design). Isolated reviews more often flag
> logic errors, missing edge cases, and unhandled exceptions (higher-risk, challenges
> assumptions the author took for granted).

---

## Step 6 — Two-stage pipeline script

Create `review-pipeline.ps1` that generates code in one session and reviews it in
a completely separate session, then gates on blocking findings:

```powershell
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
} else {
    Write-Host "`nPIPELINE PASSED: No blocking findings." -ForegroundColor Green
    exit 0
}
```

Run it:
```powershell
.\review-pipeline.ps1
Write-Host "Exit code: $LASTEXITCODE"
```

Each run saves timestamped JSONL files so you can inspect the full envelope after the fact.

---

## Useful JSONL Inspection Commands

```powershell
# List all message types in a JSONL file
Get-Content review-output.jsonl | ForEach-Object { ($_ | ConvertFrom-Json).type }

# Full pretty-print of every line
Get-Content review-output.jsonl | ForEach-Object { $_ | ConvertFrom-Json | ConvertTo-Json -Depth 10 }

# Just the result text
Get-Content review-output.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.type -eq "result" } |
  Select-Object -ExpandProperty result

# Cost and duration summary
Get-Content review-output.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Where-Object { $_.type -eq "result" } |
  Select-Object total_cost_usd, duration_ms, is_error
```

---

## Key Observations to Record

| Step | What you are proving |
|------|----------------------|
| Step 2 | `--output-format json` produces JSONL; the `result` field holds the response; no transcript scraping needed |
| Step 3 | `--continue` resumes a session headlessly with full conversation history; self-review with generation context produces fewer/softer findings |
| Step 4 | A fresh `claude -p` (no `--continue`, no `--resume`) starts an isolated session with zero prior context |
| Step 5 | Isolated review typically surfaces more findings and/or higher-severity issues than self-review |
| Step 6 | Two separate `claude -p` calls (generate, then review) achieve session isolation in CI; `exit 1` on blocking findings wires directly into pipelines |

**Key exam points:**

- `claude -p` always creates a **new session** unless `--continue` or `--resume` is specified
- Self-review bias: Claude has generation context (its reasoning, its design choices) and tends toward fewer, softer findings
- Isolated review: no authorship context, pure reviewer perspective, more thorough
- `--continue` resumes the most recent session in the current directory; `--resume <id>` targets a specific session
- The JSONL envelope wraps every headless response; the `type: "result"` line contains cost, duration, session_id, and the response text

---

## Success Criteria

- [ ] You parsed `--output-format json` output using `ConvertFrom-Json` without transcript scraping
- [ ] You used `--continue` to resume a generation session for self-review (not a fresh `claude -p`)
- [ ] You documented finding count and type differences between self-review and isolated review
- [ ] Your pipeline script exits with code 1 when blocking findings are present
- [ ] You have JSONL files saved showing the full envelope structure
- [ ] You can explain why `claude -p` without `--continue`/`--resume` is isolated (new session, no prior context)