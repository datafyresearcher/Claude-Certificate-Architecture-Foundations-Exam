<p align="center">
  <img src="assets/cca-f-study-journey.png" alt="CCA-F study journey from checklist through domains, drills, labs, practice tests, and exam day" width="100%">
</p>

# CCA-F Study Guide

A complete, self-contained preparation kit for the **Claude Certified Architect – Foundations (CCA-F)** exam, covering all five domains through official references, interactive drills, hands-on labs, practice tests, and a guided final review.

> [!NOTE]
> This is an independent study repository. It is not affiliated with or endorsed by Anthropic.

| Exam format | Details |
| --- | --- |
| Questions | 60 scenario-based questions |
| Time limit | 120 minutes |
| Passing score | 720 |
| Domains | 5 |

## Start Here

1. Open **[CCAF-Study-Checklist.xlsx](CCAF-Study-Checklist.xlsx)**.
2. In the **Checklist** tab, work from P0 orientation through all five domains and final preparation, top to bottom.
3. Update only the **Status**, **Date done**, and **Notes** columns.
4. Use the **Dashboard** tab to track progress by phase and domain automatically.
5. Follow the resource links in the checklist to open the relevant documentation, Academy courses, interactive drill, and hands-on labs.

## Exam Blueprint

| Priority | Domain | Weight | Primary practice |
| ---: | --- | ---: | --- |
| 1 | D1 — Agentic Architecture & Orchestration | 27% | Agent loops, orchestration, delegation, hooks, and recovery |
| 2 | D3 — Claude Code Configuration & Workflows | 20% | `CLAUDE.md`, rules, Skills, subagents, permissions, and CI/CD |
| 3 | D4 — Prompt Engineering & Structured Output | 20% | Explicit criteria, few-shot prompting, schemas, validation, and review |
| 4 | D2 — Tool Design & MCP Integration | 18% | Tool contracts, errors, distribution, MCP configuration, and built-in tools |
| 5 | D5 — Context Management & Reliability | 15% | Context preservation, escalation, provenance, and human review |

## Local Resources

### ⭐ Udemy Practice Tests — 25 Practice Sets

The **[Udemy Practice Tests index](06-Practice-Tests/udemy-practice-tests.md)** is one of the most important local resources in this repository. It contains **25 practice tests** for building question volume, recognizing recurring architecture patterns, strengthening elimination skills, and exposing weak domains before exam day.

Use the collection deliberately:

1. Take an early test cold to establish a baseline.
2. Review every incorrect answer and map the gap to D1–D5.
3. Return to the official documentation and complete the related lab.
4. Retake with reasoning: explain why the correct option is best and why each distractor fails.
5. Reserve several unseen tests for timed, closed-note final practice.

> [!IMPORTANT]
> Practice-test volume builds pattern recognition, but the live Anthropic documentation remains the source of truth. Do not memorize answers without understanding the underlying architectural trade-offs.

## Folder Map

| Resource | Purpose |
| --- | --- |
| [`CCAF-Study-Checklist.xlsx`](CCAF-Study-Checklist.xlsx) | Master checklist and progress dashboard |
| [`01-Official-Resources/`](01-Official-Resources/offcial-links.md) | Official Anthropic exam guide, documentation, and Academy links for all five domains |
| [`02-Interactive-Drills/`](02-Interactive-Drills/cca-f-honeypot-drills.html) | 25-scenario honeypot drill; open the HTML in a browser and filter by domain |
| [`03-Hands-On-Labs/`](03-Hands-On-Labs/domain-labs.md) | 15 hands-on labs organized across D1–D5 |
| [`03-Hands-On-Labs/_AnswerKeys/`](03-Hands-On-Labs/_AnswerKeys/README.md) | Worked solutions and reference outputs; attempt each lab before opening its answer key |
| [`04-Community-Resources/`](04-Community-Resources/community-links.md) | Unofficial preparation sites and guides, with cautions about documentation drift |
| [`05-Exam-Day/`](05-Exam-Day/exam-strategy.md) | One-page strategy and terminology review for the final 24 hours |
| [`06-Practice-Tests/`](06-Practice-Tests/udemy-practice-tests.md) | Index of 25 Udemy practice tests for question volume and timed preparation |

## Suggested Study Path

```text
Orient
  → Baseline drill
  → Official documentation
  → Hands-on labs
  → Re-drill weak domains
  → 25-test practice bank
  → Official practice exam
  → Exam-day one-pager
```

For each domain, use the same learning loop:

1. **Diagnose** — answer drill or practice questions before reviewing notes.
2. **Study** — read the current official documentation for the missed concepts.
3. **Build** — complete the corresponding hands-on lab.
4. **Explain** — state the architectural trade-off and why competing options are weaker.
5. **Retest** — repeat the drill under time pressure and track the result in the checklist.

The checklist encodes this sequence with time estimates, so use it as the master plan rather than studying folders at random.

## Ground Rules

- **The live documentation wins.** When unofficial material—including community guides, articles, or training repositories—disagrees with current documentation, follow the documentation. The exam is written against it.
- **Do the labs.** The exam is scenario-based and rewards applied architectural judgment; passive reading alone does not build that judgment.
- **Use answer keys after an attempt.** Open them when you have completed the exercise or are genuinely stuck, not as a substitute for practice.
- **Review distractors.** The exam tests discrimination between plausible options, so understanding why an answer is wrong matters as much as knowing the correct one.
- **Protect exam integrity.** Use this repository for preparation only. Follow all certification rules during the protected exam, including restrictions on notes, AI tools, external assistance, and reference material.

## Final Readiness Check

You are approaching exam readiness when you can:

- distinguish workflows from autonomous agents and choose an orchestration pattern;
- design narrow tools with useful descriptions, schemas, and structured failures;
- select the correct Claude Code configuration layer for a team workflow;
- produce reliable structured output with validation and retry boundaries;
- preserve context, provenance, partial results, and escalation signals;
- explain why each distractor in a scenario is weaker than the selected answer;
- complete timed practice without relying on memorized question wording.
