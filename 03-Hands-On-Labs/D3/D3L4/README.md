# D3L4 — Memory Hierarchy Walk + Skill Triggering

**Exam mapping:** CLAUDE.md hierarchy, `@import`, skills frontmatter and progressive disclosure
**Estimated time:** ~40 min
**Domain:** 3 — Claude Code Configuration & Workflows
**Tools required:** Claude Code CLI, git

---

## Folder Structure (as created in this lab)

```
D3L4/
├── CLAUDE.md                            <- repo-root memory (marker: PROJECT + @import)
├── shared-conventions.md                <- imported by CLAUDE.md via @import
├── sub/
│   └── CLAUDE.md                        <- subdirectory memory (marker: SUBDIR)
└── .claude/
    └── skills/
        └── release-runbook/
            └── SKILL.md                 <- skill definition (precise description)
```

> **Note:** The user-global memory at `~/.claude/CLAUDE.md` (marker: USER) is NOT in this folder — it lives in your home directory.

---

## Step 1 — Initialize the git repo

```powershell
cd D3L4
git init
```

---

## Step 2 — Plant markers at each memory level

### 2a. User-global marker (one-time, persists across all projects)
Open a terminal and run:
```powershell
Add-Content "$env:USERPROFILE\.claude\CLAUDE.md" "`nmarker: USER"
```

### 2b. Repo-root marker — already in `D3L4/CLAUDE.md`:
```
"marker: PROJECT"

@import shared-conventions.md
```

### 2c. Subdirectory marker — `D3L4/sub/CLAUDE.md`:
```powershell
New-Item -ItemType Directory -Force sub
Set-Content sub\CLAUDE.md "marker: SUBDIR"
```

### 2d. Shared conventions file — already in `D3L4/shared-conventions.md`:
```
convention: Always use snake_case for variable names.
```

---

## Step 3 — Open Claude Code and verify memory loading

```powershell
claude
```

Inside Claude Code, run:
```
/memory
```

Then ask:
```
Which markers do you see?
```

**Expected at repo root:**
- OK  `marker: USER` — loaded (global)
- OK  `marker: PROJECT` — loaded (repo root CLAUDE.md)
- OK  `convention: Always use snake_case...` — loaded (via @import)
- NOT `marker: SUBDIR` — NOT loaded yet

Now ask Claude to work inside sub/:
```
Please create a file sub/test.txt with some content
```

Ask again:
```
Which markers do you see now?
```

**Expected:** `marker: SUBDIR` is now visible — it loads on demand when Claude works in that subdirectory.

---

## Step 4 — Verify @import loads the shared conventions

Ask Claude:
```
What coding convention should I follow for variable names?
```

**Expected answer:** Claude responds with "snake_case" — confirming the `@import shared-conventions.md`
in CLAUDE.md was resolved and the shared file content was loaded.

---

## Step 5 — Skill: Vague description (SHOULD NOT trigger)

To reproduce the failure, temporarily edit SKILL.md to use a vague description:
```yaml
---
name: release-runbook
description: helpful release information
---
```

Then ask Claude:
```
prep the v2.1 release
```

**Expected:** Claude does NOT trigger the skill. It improvises or asks for clarification.
The description "helpful release information" is too vague to match the user's intent.

---

## Step 6 — Skill: Precise description (SHOULD trigger)

The current SKILL.md (`.claude/skills/release-runbook/SKILL.md`) already has the precise description:
```yaml
---
name: release-runbook
description: Use when preparing, tagging, or documenting a software release; covers changelog, version bump, tag, deploy checklist
---

## Release Runbook

1. Update CHANGELOG.md with all changes since last release
2. Bump version in pyproject.toml / package.json
3. Run `git tag -a v{version} -m "Release v{version}"`
4. Push tag: `git push origin v{version}`
5. Deploy to production using the CI pipeline
6. Announce in #releases Slack channel
```

Ask Claude again:
```
prep the v2.1 release
```

**Expected:** Claude NOW triggers the skill and walks through the runbook steps.

---

## Key Observations (Exam-Ready Notes)

Memory loading behavior:

| Memory file              | When it loads                                                    |
|--------------------------|------------------------------------------------------------------|
| ~/.claude/CLAUDE.md      | Always — at startup, for every project                           |
| <repo-root>/CLAUDE.md    | At startup, when Claude Code is opened in that repo              |
| sub/CLAUDE.md            | On demand — when Claude works on files in that subdirectory      |
| @import targets          | At the same time as the file that imports them                   |

Skill description quality:

| Description quality                          | Result                        |
|----------------------------------------------|-------------------------------|
| Vague ("helpful release information")        | Skill does NOT trigger        |
| Explicit ("Use when preparing a release...") | Skill triggers reliably       |

**Key exam point:** Claude uses semantic matching on skill descriptions. Explicit trigger phrases
("when preparing a release", "covers changelog, version bump, tag") are what make skills discoverable.

---

## Success Criteria

- [ ] You can state from observation which memory files load at startup vs on demand
- [ ] You saw the same skill fail to trigger with vague description and trigger with precise one
