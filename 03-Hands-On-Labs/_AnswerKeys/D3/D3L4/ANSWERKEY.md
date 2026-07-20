# D3L4 Answer Key — Memory Hierarchy Walk + Skill Triggering

This folder holds the **worked artifacts** from a completed run of the lab. Recreate them in the lab folder (`D3/D3L4/`) yourself; use these to compare.

## Artifacts

| File | Role |
|------|------|
| `CLAUDE.md` | Repo-root project memory — `"marker: PROJECT"` plus the `@import shared-conventions.md` line |
| `shared-conventions.md` | The imported shared file (loads at launch via `@import`) |
| `sub/CLAUDE.md` | Subdirectory memory — `"marker: SUBDIR"` (loads **on demand**) |
| `sub/example.txt` | A file to work on so the subdirectory memory triggers |
| `.claude/skills/release-runbook/SKILL.md` | The skill **after** the fix — precise, trigger-rich description |

(You also need `~/.claude/CLAUDE.md` with `"marker: USER"` — a user-level file that can't ship in this kit.)

## Expected observations

- **At startup (repo root):** `/memory` lists the user file and the project `CLAUDE.md` (with its import). Asking "which markers do you see?" returns USER and PROJECT — **not** SUBDIR.
- **After working on `sub/example.txt`:** the SUBDIR marker appears — subdirectory CLAUDE.md files load on demand when Claude reads files there, not at launch.
- **Import:** the snake_case convention from `shared-conventions.md` is visible in context at launch (imports expand at load time).
- **Skill triggering:** with the vague description ("helpful release information"), "prep the v2.1 release" does **not** load the skill. With the precise description in this key ("Use when preparing, tagging, or documenting a software release; covers changelog, version bump, tag, deploy checklist"), it triggers. Skills are routed by their frontmatter description — fix triggering by fixing the description.

## Success-criteria answers

- Load at startup: managed policy → user (`~/.claude/CLAUDE.md`) → project root `CLAUDE.md` (+ its `@imports`) (+ `CLAUDE.local.md` if present). On demand: subdirectory `CLAUDE.md` when working in that subdirectory; skills when their description matches the task.
- One-liner: memory is always-on guidance loaded by scope; skills are on-demand procedures loaded by description match.
