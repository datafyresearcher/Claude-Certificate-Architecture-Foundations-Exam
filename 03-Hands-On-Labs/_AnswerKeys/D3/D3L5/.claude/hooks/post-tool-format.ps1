# PostToolUse hook — runs Black formatter on every edited Python file

$reader = New-Object System.IO.StreamReader([Console]::OpenStandardInput())
$rawInput = $reader.ReadToEnd()
$reader.Close()

$hookData = $rawInput | ConvertFrom-Json

$logFile = Join-Path $PSScriptRoot "hook-activity.log"
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
#$toolName = $hookData.tool_name

# Log every invocation
# Add-Content -Path $logFile -Value "[$timestamp] tool=$toolName path=$path"

# Uncomment for full debug output
Add-Content -Path $logFile -Value "[$timestamp] RAW: $rawInput"

$path = if ($hookData.tool_input.file_path) { $hookData.tool_input.file_path } elseif ($hookData.tool_input.path) { $hookData.tool_input.path } else { "" }

if ($path -match "\.py$") {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $logFile -Value "[$timestamp] FORMATTING: Running Black on $path"

    $blackCmd = Get-Command black -ErrorAction SilentlyContinue
    if (-not $blackCmd) {
        Add-Content -Path $logFile -Value "[$timestamp] ERROR: Black is not installed. Run: pip install black"
        exit 0
    }

    $blackOutput = & black $path 2>&1 | Out-String
    Add-Content -Path $logFile -Value "[$timestamp] Black output: $blackOutput"
    #Optional: Output JSON. With additionalContext, Claude receives a system reminder that the file was reformatted after its edit. 
    #Without it, Claude has no idea Black changed the file, and if it reads the file again later, it might be confused by formatting differences it didn't make.
    $result = @{
        hookSpecificOutput = @{
            hookEventName     = "PostToolUse"
            additionalContext = "Black formatter ran on $path. Output: $blackOutput"
        }
    }
    $result | ConvertTo-Json -Depth 5 -Compress
}

exit 0