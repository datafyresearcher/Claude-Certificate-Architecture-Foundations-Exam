# Official Resources Index

## Certification

- [CCA-F certification page](https://anthropic.skilljar.com/claude-certified-architect-foundations-certification) — Exam Guide PDF, terms and conditions, exam policy, and practice exam
- [Exam access request](https://anthropic.skilljar.com/claude-certified-architect-foundations-access-request)

## Anthropic Academy (Free Courses)

- [Course catalog](https://anthropic.skilljar.com/)
- [Introduction to Model Context Protocol](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [MCP: Advanced Topics](https://anthropic.skilljar.com/model-context-protocol-advanced-topics)
- [Introduction to Agent Skills](https://anthropic.skilljar.com/introduction-to-agent-skills)
- [Introduction to Subagents](https://anthropic.skilljar.com/introduction-to-subagents)
- **Building with the Claude API** and **Claude Code in Action** — find both in the [course catalog](https://anthropic.skilljar.com/).

## Docs by Domain

### D1: Agentic Architecture & Orchestration

- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — workflows vs. agents and the five workflow patterns, including orchestrator-workers
- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — orchestrator-worker in production, subagent prompt completeness, checkpoints/state persistence, and resume-on-error
- [Tool use overview](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) — the agent loop, `stop_reason`, and parallel tool use
- [Subagents in Claude Code](https://code.claude.com/docs/en/sub-agents) — context isolation, tool restrictions, and spawning
- [Subagents in the Agent SDK](https://code.claude.com/docs/en/agent-sdk/subagents) — `AgentDefinition` parameters and coordinator wiring

### D2: Tool Design & MCP Integration

- [Tool use overview](https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview) — descriptions, `tool_choice`, and strict mode
- [MCP in Claude Code](https://code.claude.com/docs/en/mcp) — local/project/user scopes, environment-variable expansion, `/mcp`, and authentication
- [Model Context Protocol documentation](https://modelcontextprotocol.io/) — client/server model and tools vs. resources vs. prompts

### D3: Claude Code Configuration & Workflows

- [Claude Code overview](https://docs.claude.com/en/docs/claude-code/overview)
- [Extend Claude Code](https://code.claude.com/docs/en/features-overview) — when to use `CLAUDE.md` vs. rules, Skills, subagents, hooks, and MCP
- [Memory / CLAUDE.md](https://code.claude.com/docs/en/memory) — hierarchy, imports, and `.claude/rules/` with path globs
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Skills](https://code.claude.com/docs/en/skills)
- [Slash commands](https://code.claude.com/docs/en/slash-commands)
- [Settings and permissions](https://code.claude.com/docs/en/settings)
- [Permission modes](https://code.claude.com/docs/en/permission-modes) — including plan mode
- [Subagents](https://code.claude.com/docs/en/sub-agents)
- [MCP in Claude Code](https://code.claude.com/docs/en/mcp)
- [CLI reference](https://code.claude.com/docs/en/cli-reference) — `-p`, `--output-format json`, `--resume`, `--bare`, and `--tools` vs. `--allowedTools`
- [Headless / programmatic use](https://code.claude.com/docs/en/headless) — bare mode, JSON output, and auto-approving tools
- [Tools reference](https://code.claude.com/docs/en/tools-reference) — choosing between Grep, Glob, Read, and Bash
- [Common workflows](https://code.claude.com/docs/en/common-workflows) — codebase exploration, plan mode, refactoring, and testing
- [Sessions](https://code.claude.com/docs/en/sessions) — `--continue`, `--resume`, and session scope rules
- [Code review](https://code.claude.com/docs/en/code-review) — automated pull-request review configuration
- [GitHub Actions](https://code.claude.com/docs/en/github-actions)

### D4: Prompt Engineering & Structured Output

- [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) — `output_config.format`, strict tools, incompatibilities, optional/nullable fields, and enums
- [Console prompting tools](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-tools) — generator, improver, and evaluation tools

### D5: Context Management & Reliability

- [Context editing](https://platform.claude.com/docs/en/build-with-claude/context-editing) — tool-result clearing, thinking clearing, and compaction
- [Batch processing](https://docs.claude.com/en/docs/build-with-claude/batch-processing)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

## Interactive / Hands-On (Official)

- [Anthropic courses notebooks](https://github.com/anthropics/courses) — including the interactive prompt engineering tutorial
- [Anthropic Cookbook](https://github.com/anthropics/anthropic-cookbook)

If a `code.claude.com` slug moves, start from the [Claude Code documentation index](https://code.claude.com/docs/llms.txt), which enumerates every page.
