# D2L15 Answer Key — MCP Integration

This lab runs in the Claude Code CLI, so the "solution" is the expected command transcript and artifacts.

## Expected command transcript

```powershell
# Step 1 — register a local stdio server (note the mandatory -- separator)
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"
claude mcp list          # -> filesystem: ... - ✓ Connected
# Windows fallback if it fails to connect:
#   claude mcp add filesystem -- cmd /c npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"

# Step 2/3 — in a session
/mcp                     # -> filesystem ✓ connected, tools listed as mcp__filesystem__*
# "list the files in the allowed directory and read notes.txt"
#   -> calls mcp__filesystem__list_directory, mcp__filesystem__read_text_file
# asking for C:\Windows\win.ini -> the SERVER refuses (server-enforced sandbox)

# Step 4 — project scope
claude mcp remove filesystem
claude mcp add --scope project filesystem -- npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"
Get-Content .\.mcp.json
```

## Expected `.mcp.json` (project scope)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "<absolute-path-to>/mcp-playground"]
    }
  }
}
```

For servers needing secrets, the committed file uses environment variable expansion — e.g. `"env": {"API_KEY": "${INTERNAL_API_KEY}"}` — each engineer sets the variable locally; the secret never enters version control.

## Success-criteria answers

- **Client/server model:** the host (Claude Code) runs an MCP client; servers expose **tools** (callable, named `mcp__<server>__<tool>`), **resources** (readable context, `@<server>:<uri>`), and **prompts** (`/mcp__<server>__<prompt>`). Transports: stdio (local subprocess), http/sse (remote).
- **Scopes:** local (default) → `~/.claude.json` under the project path, private to you+project; **project** → `.mcp.json` at repo root, committed, team-shared (trust prompt on first use); user → `~/.claude.json` top-level, all your projects, private. Precedence: local > project > user.
- **Auth:** remote servers use OAuth via `/mcp`; the token lives in the OS credential store, not the config file, and is **not** the service's REST API key.
- **Security boundary:** the *server* owns what it exposes (the allowed-directory sandbox proved this — Claude couldn't escape it).
