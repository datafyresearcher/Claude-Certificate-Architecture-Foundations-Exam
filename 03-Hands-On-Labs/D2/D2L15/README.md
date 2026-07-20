# D2L15 — MCP Integration

**Exam mapping:** MCP client/server model, connecting servers in Claude Code, tool naming, scopes, auth (Academy MCP courses)
**Estimated time:** ~40 min
**Domain:** 2 — Tool Design & MCP Integration (18%)
**Key concept:** MCP (Model Context Protocol) is a **client/server** standard: Claude Code is the **client (host)**; an **MCP server** exposes tools, resources, and prompts over a transport (stdio for local, HTTP/SSE for remote). You add servers with `claude mcp add`, they surface as tools named `mcp__<server>__<tool>`, and where the config is stored depends on the **scope** you choose.

> **How to use this lab:** this one runs in the **Claude Code CLI**, not Python. You'll stand up a real local MCP server, connect it, watch its tools appear in a session, use them, then explore scopes and auth. Commands are PowerShell (your environment).

---

## What you're proving

1. You can connect a local (stdio) MCP server to Claude Code and see its tools in a session.
2. MCP tools are namespaced `mcp__<server>__<tool>` and Claude calls them like any other tool.
3. `--scope` (local / project / user) decides *where* the server config persists and *who* sees it.
4. Remote servers authenticate via an OAuth flow in `/mcp`, and that token is **not** the service's REST API key.

---

## Facts to keep in front of you

- **Client/server split:** the **host** (Claude Code) runs an MCP **client** that connects to one or more MCP **servers**. Servers expose three things: **tools** (callable), **resources** (readable context, `@`-mentionable), and **prompts** (slash commands).
- **Transports:** `stdio` (local subprocess — default), `http` / `sse` (remote). Syntax: `claude mcp add [--transport stdio|http|sse] <name> [--] <command-or-url>`. The `--` separator is **mandatory for stdio** — everything after it is the server's launch command.
- **Tool naming:** `mcp__<server>__<tool>` (e.g. `mcp__filesystem__read_text_file`). Prompts surface as `/mcp__<server>__<prompt>`; resources as `@<server>:<uri>`.
- **Scopes & persistence:**
  - `--scope local` (default) → `~/.claude.json` under the project path; **this project, you only**.
  - `--scope project` → **`.mcp.json`** at the repo root; **committed, whole team** (teammates get a trust prompt on first use).
  - `--scope user` → `~/.claude.json` top-level; **all your projects, you only**.
- **Auth:** remote servers usually use **OAuth** (run it from `/mcp`), stored in your OS keychain/credential store — **not** in the config file. An MCP OAuth token ≠ the service's native API key.
- **`/mcp`** (inside a session) shows each server's status (connected / needs-auth / failed), tool counts, and the auth menu.

---

## Step 0 — Prereqs

MCP local servers here launch via `npx`, so you need Node.

```powershell
node -v      # any recent LTS is fine
npx -v
claude --version
```

Make a scratch directory with a file the server can read:

```powershell
# From D2/D2L15.
mkdir mcp-playground
Set-Content -Path .\mcp-playground\notes.txt -Value "hello from MCP - the anomaly began at 03:14 UTC on host db-7" -Encoding utf8
```

---

## Step 1 — Add a local (stdio) filesystem MCP server

The official filesystem server takes one or more **allowed directories** as arguments — it can only touch those paths.

```powershell
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"
```

Breakdown: `filesystem` = the server name (yours to choose; drives the `mcp__filesystem__*` prefix). `--` = the mandatory separator. `npx -y @modelcontextprotocol/server-filesystem <dir>` = the launch command; `-y` lets npx install without prompting; `<dir>` is the sandboxed root.

Confirm it's registered:

```powershell
claude mcp list
```

> **Windows npx caveat:** if `claude mcp list` shows the server as **failed to connect**, wrap the launcher in `cmd /c` so Windows resolves the `npx` shim:
> ```powershell
> claude mcp remove filesystem
> claude mcp add filesystem -- cmd /c npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"
> ```
> Also give npx time on first run — it downloads the package; if it times out, set `$env:MCP_TIMEOUT = "60000"` before launching `claude`.

---

## Step 2 — See the tools in a session

```powershell
claude
```

Inside the session:

```
/mcp
```

**What to look for — and record:**
- `filesystem` listed as **✓ connected** with a tool count (read/write/list/search file tools).
- The tools are named `mcp__filesystem__...` (e.g. `mcp__filesystem__read_text_file`, `mcp__filesystem__list_directory`). Note the `mcp__<server>__<tool>` shape — that's the exam's naming convention.

---

## Step 3 — Use the server

Still in the session, ask Claude to use it:

```
Using the filesystem server, list the files in the allowed directory and read notes.txt back to me.
```

**What to look for — and record:**
- Claude calls `mcp__filesystem__list_directory` and `mcp__filesystem__read_text_file` (you'll see the tool calls), and returns the contents of `notes.txt`.
- Try to make it read something **outside** the allowed dir (e.g. `C:\Windows\win.ini`) — the server refuses. The sandbox is enforced by the *server*, not by Claude. That's the MCP security model: the server owns what it exposes.

---

## Step 4 — Scopes: where the config lives

Remove and re-add at **project** scope, then inspect the file it writes:

```powershell
# exit the session first (Ctrl+C), then:
claude mcp remove filesystem
claude mcp add --scope project filesystem -- npx -y @modelcontextprotocol/server-filesystem "$PWD\mcp-playground"
```

Now look at the generated `.mcp.json` at the folder root:

```powershell
Get-Content .\.mcp.json
```

**What to look for — and record:**
- `.mcp.json` contains a `mcpServers` entry with the command/args — this is the **committed, team-shared** form. Teammates who clone the repo get a **trust prompt** before it connects.
- Contrast the three scopes in your notes:
  - **local** (default) → `~/.claude.json`, private to you + this project.
  - **project** → `.mcp.json`, shared via version control.
  - **user** → `~/.claude.json` top-level, all your projects, private to you.
- Precedence when the same name exists in more than one: local > project > user.

---

## Step 5 (optional) — A remote server + OAuth

If you want to see the auth flow (no secret to hand-manage):

```powershell
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp
claude
```

Inside the session:

```
/mcp
```

Select the server → **Authenticate** → a browser opens for OAuth → return to the session.

**What to look for — and record:**
- Before auth, `/mcp` shows **! needs authentication**; after, **✓ connected**.
- The OAuth token is stored in your OS credential store, **not** in `.mcp.json`/`~/.claude.json`. And it's an **MCP** OAuth credential — distinct from that service's REST API key. (Env-var secrets for servers that use them go in the config as `${VAR}` expansions, resolved from your environment — never hard-code them.)

Clean up when done:

```powershell
claude mcp remove sentry
claude mcp remove filesystem            # (project scope) or --scope local if you re-added it there
```

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1–2 | `claude mcp add <name> -- <launch cmd>` registers a stdio server; `/mcp` shows it connected with `mcp__<server>__*` tools |
| Step 3 | Claude calls MCP tools like any other; the server (not Claude) enforces what's exposed (sandboxed dir) |
| Step 4 | `--scope` decides persistence: local (`~/.claude.json`, private) / project (`.mcp.json`, committed) / user (all projects) |
| Step 5 | Remote servers auth via OAuth in `/mcp`; token lives in the keychain, and MCP auth ≠ the service's REST API key |

**Key exam points:**

- MCP is **client/server**: the host (Claude Code) runs the client; servers expose **tools, resources, and prompts**. Transports: stdio (local), http/sse (remote).
- Tools are namespaced **`mcp__<server>__<tool>`**; prompts are `/mcp__<server>__<prompt>`; resources are `@<server>:<uri>`.
- **Scope controls sharing/persistence**: project scope writes `.mcp.json` (team, version-controlled, trust-prompted); local/user live in `~/.claude.json` (private).
- Remote auth is **OAuth via `/mcp`**, stored outside the config; an MCP token is not the same credential as the service's API key.
- The **server** owns its security boundary (allowed paths, scopes) — connecting a server grants Claude exactly what that server chooses to expose.

---

## Success Criteria

- [ ] A local MCP server shows **connected** in `/mcp` with tools named `mcp__<server>__<tool>`, and you invoked at least one (listed/read a file).
- [ ] You saw the server refuse a path outside its allowed directory (server-enforced sandbox).
- [ ] You inspected `.mcp.json` from `--scope project` and can state where each of the three scopes persists and who sees it.
- [ ] You can explain the client/server model, the `mcp__` naming convention, and why MCP OAuth ≠ a REST API key.
