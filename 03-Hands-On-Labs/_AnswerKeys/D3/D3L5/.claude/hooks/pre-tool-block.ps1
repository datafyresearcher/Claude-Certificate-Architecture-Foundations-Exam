# PreToolUse hook — blocks any Edit/Write to infra/prod/
# Uses JSON output for richer control + logs all hook activity

# Read stdin via StreamReader (confirmed working on this machine)
$reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput())
$rawInput = $reader.ReadToEnd()
$reader.Close()

$hookData = $rawInput | ConvertFrom-Json

# Log setup
$logFile = Join-Path $PSScriptRoot "hook-activity.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$toolName = $hookData.tool_name

# Get the file path from tool_input
$path = if ($hookData.tool_input.file_path) { $hookData.tool_input.file_path } elseif ($hookData.tool_input.path) { $hookData.tool_input.path } else { "" }

$path = $path -replace '\\', '/'

# Log every invocation
# Add-Content -Path $logFile -Value "[$timestamp] tool=$toolName path=$path"

# Uncomment for full debug output
Add-Content -Path $logFile -Value "[$timestamp] RAW: $rawInput"

if ($path -match "infra/prod/") {
    Add-Content -Path $logFile -Value "[$timestamp] BLOCKED: $toolName on $path"

    $result = @{
        hookSpecificOutput = @{
            hookEventName            = "PreToolUse"
            permissionDecision       = "deny"
            permissionDecisionReason = "Modifications to infra/prod/ are prohibited. This is a hardcoded guardrail, not a prompt rule."
            additionalContext        = "The file $path is in the protected infra/prod/ directory. Suggest changes to infra/staging/ for testing, or ask the user to apply infra/prod/ changes manually."
        }
    }
    $result | ConvertTo-Json -Depth 5 -Compress
    exit 0

    # ── Exit code approach (alternative) ──
    # [Console]::Error.WriteLine("HOOK BLOCKED: Modifications to infra/prod/ are prohibited by PreToolUse hook. This is a hardcoded guardrail, not a prompt rule.")
    # exit 2
}

Add-Content -Path $logFile -Value "[$timestamp] ALLOWED: $toolName on $path"
exit 0