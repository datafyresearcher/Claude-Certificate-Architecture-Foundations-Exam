# CCA-F Practice Tests

This file catalogs all 25 practice tests (Claude Certified Architect Foundations v2.0). Each test contains 60 multiple-choice questions on the Google Forms platform.

## Test Links

| # | Link | Q1 Topic |
|---|------|----------|
| 1 | [https://bit.ly/3RccpEO](https://bit.ly/3RccpEO) | Developer Productivity - Review quality |
| 2 | [https://bit.ly/4gCfsQZ](https://bit.ly/4gCfsQZ) | Customer Support - Recovery decisions |
| 3 | [https://tinyurl.com/5da2m4k4](https://tinyurl.com/5da2m4k4) | High-volume receipt extraction reliability |
| 4 | [https://tinyurl.com/33fnrpma](https://tinyurl.com/33fnrpma) | Stop reason identification |
| 5 | [https://tinyurl.com/2xa3f9ub](https://tinyurl.com/2xa3f9ub) | Token Counting & Budget Management |
| 6 | [https://tinyurl.com/5xna2cv2](https://tinyurl.com/5xna2cv2) | Undoing Claude Code changes |
| 7 | [https://tinyurl.com/4kfwpe54](https://tinyurl.com/4kfwpe54) | Memory/conventions inconsistency diagnostic |
| 8 | [https://tinyurl.com/yeypxpsz](https://tinyurl.com/yeypxpsz) | Multi-agent Manager task reassignment |
| 9 | [https://tinyurl.com/5cjthtke](https://tinyurl.com/5cjthtke) | Account disambiguation fix |
| 10 | [https://tinyurl.com/s3xtmk5t](https://tinyurl.com/s3xtmk5t) | SubagentStart/SubagentStop hooks purpose |
| 11 | [https://tinyurl.com/23zt766m](https://tinyurl.com/23zt766m) | MCP tool design - send_email prevention |
| 12 | [https://tinyurl.com/4b7uwcmd](https://tinyurl.com/4b7uwcmd) | Prompt design - SQL INSERT generation |
| 13 | [https://tinyurl.com/5et9mptp](https://tinyurl.com/5et9mptp) | API documentation generation fix |
| 14 | [https://tinyurl.com/yabejjxt](https://tinyurl.com/yabejjxt) | Long-running analysis contradiction cause |
| 15 | [https://tinyurl.com/4akcskjx](https://tinyurl.com/4akcskjx) | CI/CD workflow configuration balance |
| 16 | [https://tinyurl.com/5ykahf5c](https://tinyurl.com/5ykahf5c) | Scratchpad for exact facts preservation |
| 17 | [https://tinyurl.com/44vb2a5m](https://tinyurl.com/44vb2a5m) | Tool-definition descriptions for selection reliability |
| 18 | [https://tinyurl.com/3nhap9ws](https://tinyurl.com/3nhap9ws) | Slash command structured output via tool_use |
| 19 | [https://tinyurl.com/ejwvzbvz](https://tinyurl.com/ejwvzbvz) | Messages API loop - stop_reason vs text sentinel |
| 20 | [https://tinyurl.com/55682zj8](https://tinyurl.com/55682zj8) | Messages API loop - text sentinel root cause |
| 21 | [https://tinyurl.com/yc36mwf3](https://tinyurl.com/yc36mwf3) | Messages API - missing tool_result blocks |
| 22 | [https://tinyurl.com/2fk3dm3z](https://tinyurl.com/2fk3dm3z) | Messages API loop - natural-language sentinel |
| 23 | [https://tinyurl.com/bda7a5bp](https://tinyurl.com/bda7a5bp) | Messages API loop - reply length sentinel |
| 24 | [https://tinyurl.com/mtuaer5w](https://tinyurl.com/mtuaer5w) | Messages API loop - stop_reason correct fix |
| 25 | [https://tinyurl.com/8v3u2w5t](https://tinyurl.com/8v3u2w5t) | Multi-agent scheduling - atomic find_and_book |

## Question 1 Preview from Each Test

### Test 1 — Developer Productivity with Claude

**Scenario:** You are building developer productivity tools using the Claude Agent SDK. The agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate code, and automate repetitive tasks. It uses built-in tools (Read, Write, Bash, Grep, Glob) and integrates with MCP servers.

Your team added a CI step that reviews code produced by an internal Claude-powered scaffolding workflow. The review job currently resumes the same named Claude session that generated the branch, then asks it to critique the resulting pull request. Human reviewers report that the automated review misses subtle design issues and often defends choices made during generation. What change would most improve review quality?

- A: Run the review in a separate Claude Code invocation with the PR diff, repository context, and review criteria only.
- B: Keep the existing session but add instructions requiring Claude to challenge its prior assumptions before approving changes.
- C: Ask the generating session to perform three consecutive review passes and report only issues found twice.
- D: Resume the generation session after tests complete, then provide failing logs before requesting final review feedback.

---

### Test 2 — Customer Support Resolution Agent

**Scenario:** You are building a customer support resolution agent using the Claude Agent SDK. The agent handles high-ambiguity requests like returns, billing disputes, and account issues. It has access to backend systems through MCP tools (get_customer, lookup_order, process_refund, escalate_to_human). Your target is 80%+ first-contact resolution while knowing when to escalate.

Pilot logs show that `process_refund` returns the same short failure text for processor timeouts, expired refund windows, missing staff permissions, and malformed amounts. The agent responds inconsistently: it retries policy denials, escalates simple input mistakes, and gives customers vague explanations when permission is missing. What change would most directly improve the agent's recovery decisions?

- A: Configure the agent to retry every failed tool call three times before escalating unresolved requests to a human.
- B: Update each MCP tool to return categorized failures with retryability and customer-safe guidance tailored to the specific backend condition.
- C: Replace process_refund with separate tools for timeouts, policy denials, permission issues, and invalid input cases.
- D: Add prompt instructions telling the agent to infer failure causes from customer wording and conversation sentiment.

---

### Test 3 — High-Volume Receipt Extraction

You are extracting line items from thousands of physical receipts. Some receipts are blurry or have handwritten notes. Which architectural choice most improves the reliability of this high-volume pipeline?

- A: Implement a 'Validation-Retry' loop that uses a schema validator to catch malformed JSON and feeds the error back to Claude.
- B: Use the 'Message Batches API' to save 50% on the cost of the failed attempts.
- C: Switch to 'Claude 3 Opus' for every receipt to ensure maximum intelligence.
- D: Increase the 'temperature' to 0.7 to allow the model to 'guess' the blurry text more creatively.

---

### Test 4 — Stop Reason

Which 'stop reason' indicates that the model has successfully completed its task and has nothing more to say?

- A: max tokens
- B: end turn
- C: stop sequence
- D: tool use

---

### Test 5 — Token Counting & Budget Management

Which architectural component is responsible for 'Token Counting' and 'Budget Management' in the Claude Agent SDK?

- A: The MCP Server.
- B: The System Prompt.
- C: The Monitor class.
- D: The User Message.

---

### Test 6 — Undoing Claude Code Changes

What is the most efficient way to 'Undo' the last 3 changes Claude Code made?

- A: Delete the 'CLAUDE.md' file.
- B: Use 'git checkout' or 'git revert' via the terminal.
- C: Tell Claude 'Please undo'.
- D: Restart with the '--fresh' flag.

---

### Test 7 — Conventions Inconsistency

A new engineer on the team reports that Claude Code is not following the project's API naming conventions during code generation, even though other engineers on the same repository see the conventions applied correctly. What is the most effective first diagnostic step to identify the cause of this inconsistency?

- A: Ask the engineer to run the /memory command to verify which memory files are currently loaded in their session
- B: Add the API naming conventions as inline comments in every source file so Claude Code reads them directly
- C: Move all project configuration from .claude/rules/ into a single root-level CLAUDE.md to simplify the file structure
- D: Reinstall Claude Code on the engineer's machine to clear any corrupted cached configurations

---

### Test 8 — Multi-Agent Manager Task Reassignment

A multi-agent research system uses a 'Manager' to coordinate 10 subagents. You notice the Manager frequently gets confused and re-assigns the same sub-task multiple times. Which architectural fix is most effective?

- A: Increase the 'temperature' of the Manager.
- B: Add more subagents to reduce the Manager's cognitive load.
- C: Instruct the Manager to maintain a 'Task Board' file and read it at the start of every turn.
- D: Use 'Claude 3 Haiku' for the Manager to save on token costs.

---

### Test 9 — Account Disambiguation

lookup_customer returns 3 accounts for 'James Wilson.' Your agent picks the most recently active one. In 4% of cases this selects the wrong account and causes incorrect refunds. What is the correct fix?

- A: Flag all multi-match cases for human review before the agent processes them.
- B: Improve the selection heuristic to combine recent activity, account age, and order count.
- C: Set a minimum confidence threshold and only proceed when one account is 95% likely to be correct.
- D: Ask the customer for a disambiguating identifier (email, phone, or order number) before proceeding.

---

### Test 10 — SubagentStart/SubagentStop Hooks

SubagentStart and SubagentStop hooks are configured in a multi-agent Developer Productivity system. What is their primary purpose?

- A: They allow subagents to communicate directly with each other without going through the coordinator.
- B: They provide subagents with read access to the full coordinator context window on spawn.
- C: They automatically retry failed subagents after a 5-second delay without coordinator involvement.
- D: They fire when subagents are spawned and complete, enabling the coordinator to track lifecycle events.

---

### Test 11 — MCP send_email Tool Design

Your MCP server exposes a tool called send_email. During testing, the model sends emails to wrong recipients. Which MCP tool design change best prevents this?

- A: Set tool_choice to none to disable the tool during testing and re-enable it only in production.
- B: Add a recipient_validation: true flag to the tool schema so the MCP server double-checks recipient addresses.
- C: Rename the tool to send_email_with_confirmation to signal the model that confirmation is required.
- D: Add a required to_address_confirmation parameter and a dry_run mode that previews the send without executing.

---

### Test 12 — SQL INSERT Prompt Design

A prompt asks Claude to generate SQL INSERT statements from a CSV. The model sometimes generates CREATE TABLE statements instead. What prompt change most directly prevents this?

- A: Use a structured output schema with an inserts field that is an array of INSERT statement strings.
- B: Provide a few-shot example showing CSV input and the corresponding INSERT statements as output.
- C: Add chain-of-thought steps asking Claude to verify the output type before finalising.
- D: Add 'generate only INSERT statements, never CREATE TABLE' to the system prompt.

---

### Test 13 — API Documentation Generation

A prompt asks Claude to generate API documentation from code. The output is technically accurate but too brief. Adding 'be more detailed' doesn't improve it. What is a more effective fix?

- A: Add chain-of-thought steps asking Claude to identify all parameters before writing the documentation.
- B: Switch to a larger model — documentation tasks benefit significantly from larger model capacity.
- C: Provide 5 few-shot examples of well-documented APIs to demonstrate the expected documentation depth.
- D: Specify the exact sections required: description, parameters (name, type, description each), returns, and examples.

---

### Test 14 — Long-Running Analysis Contradiction

A developer's long-running analysis agent produces conclusions that contradict the agent's own earlier statements in the same session. What is the most likely cause?

- A: The model is experiencing reasoning degradation due to running too many tool calls in the session.
- B: The model's temperature increases over long sessions, producing increasingly inconsistent outputs.
- C: The agent's context window contains so much accumulated content that early conclusions receive insufficient attention.
- D: Earlier statements were written to a scratchpad the model is no longer reading in later turns.

---

### Test 15 — CI/CD Workflow Configuration

**Scenario:** You are integrating Claude Code into your CI/CD pipeline. The system runs automated code reviews, generates test cases, and provides feedback on pull requests. You need to design prompts that provide actionable feedback and minimize false positives.

Your pull request review job has become noisy after teams added security audit steps, release-note checks, dependency migration guidance, and test generation procedures to the repository's main Claude instructions. Simple documentation-only PRs now receive irrelevant warnings, while specialized jobs still need the detailed procedures when explicitly run. What configuration approach best balances consistency with focused context?

- A: Consolidate every CI checklist into root CLAUDE.md so each automated review receives identical instructions for maximum consistency.
- B: Store workflow instructions in user-scoped skills on the CI runner, updating them manually when jobs change.
- C: Keep universal review principles in project CLAUDE.md, and move specialized CI workflows into project skills invoked by relevant jobs.
- D: Duplicate the complete workflow prompt inside each CI command, avoiding shared Claude Code configuration files entirely.

---

### Test 16 — Exact Facts Preservation

**Scenario:** You are building developer productivity tools using the Claude Agent SDK. The agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate code, and automate repetitive tasks. It uses the built-in tools (Read, Write, Bash, Grep, Glob) and integrates with Model Context Protocol (MCP) servers.

During a month-long exploration of a legacy billing module, the agent's running summaries start changing exact requirements such as "refund retry limit is 3," "SLA is 99.95%," "migration cutoff is 2026-06-30," and "support promised no customer-visible schema changes" into phrases like "limited retries," "high availability," "upcoming cutoff," and "avoid disruptive changes." What change should this team make to reduce the risk of incorrect follow-up edits?

- A: Rewrite summaries to favor broad intent over exact constants so the agent has fewer details to track.
- B: Enable prompt caching for the long system prompt and continue summarizing older turns into concise prose.
- C: Maintain a structured scratchpad of exact facts that is updated separately from compacted conversation history.
- D: Increase the amount of raw tool output kept in context and summarize only after the window is nearly full.

---

### Test 17 — Tool Selection Reliability

A university library's multi-agent research system routes tasks to MCP-backed web search and document analysis subagents. During evaluation, the coordinator often sends literature-review tasks to the web search subagent when the user asked for analysis of uploaded PDFs, and sends web-currentness tasks to the document analysis subagent. The tool implementations work correctly once called. Which tool-definition change should this team make first to improve selection reliability?

- A: Rewrite each tool definition with detailed descriptions covering use cases, non-use cases, inputs, returned data, and caveats.
- B: Rename each tool with shorter service-prefixed names while leaving the current descriptions and schemas unchanged.
- C: Add request examples inside JSON Schema field descriptions for web queries, PDF analysis, and citation searches.
- D: Force each research turn through the model API to call one available tool before returning results to the coordinator.

---

### Test 18 — Slash Command Structured Output

You are using Claude Code to accelerate software development. Your team uses it for code generation, refactoring, debugging, and documentation. You need to integrate it into your development workflow with custom slash commands, CLAUDE.md configurations, and understand when to use plan mode vs direct execution.

The /release-note command sends a pull request diff to Claude and needs a typed object containing fields such as title, risk_level, testing_summary, and breaking_change. The prototype asks Claude to return JSON and then parses the assistant text, but failures occur when Claude includes commentary before the JSON. Which implementation change best improves reliability while preserving a schema-based extraction contract?

- A: Store the release note schema in CLAUDE.md, ask the slash command to follow it, and parse the final assistant text.
- B: Declare a client extraction tool with an input_schema for the release note fields, require that tool call, and read the tool_use input object.
- C: Keep the text JSON prompt, prefill the assistant with an opening brace, and parse the first balanced object from the assistant text.
- D: Execute a local extraction function after Claude requests the tool, send a tool_result, and parse the follow-up assistant text.

---

### Test 19 — Messages API Loop (stop_reason vs text sentinel)

A developer builds a customer-support agent on the Messages API. After each API response, the code checks whether the reply text ends with a period followed by the word 'Complete'. If so, it stops the loop; otherwise it resends the message. The agent frequently stalls mid-task because tool calls are never executed. What is the root cause of this behaviour?

- A: The system prompt is too short to instruct the model to terminate the loop reliably.
- B: The model is returning tool_use blocks that exceed the maximum token limit for the response.
- C: The loop does not inspect stop_reason, so it never detects tool_use turns and never appends tool_result blocks.
- D: The tool definitions are missing required fields, causing the model to skip tool calls silently.

---

### Test 20 — Messages API Loop (text sentinel root cause)

A developer builds a recipe-suggestion agent on the Messages API. After each API call the loop checks whether the response text contains the phrase 'Final Answer:' and exits if found. In testing, tool calls are silently skipped and the loop exits early when the model uses that phrase conversationally. Which statement best identifies the root cause?

- A: The system prompt does not include explicit instructions telling the model when to use each tool, so the model defaults to generating text instead of calling tools.
- B: The model requires tool_choice set to any on every turn to ensure it continues calling tools rather than producing conversational text responses.
- C: Setting a maximum of five iterations would prevent early exits because the loop would always run to completion before checking for the sentinel phrase.
- D: The loop is driven by a text sentinel instead of stop_reason, so tool_use turns are missed and end_turn turns may be incorrectly handled when the phrase appears.

---

### Test 21 — Messages API (missing tool_result blocks)

A data-enrichment agent built on the Messages API calls external APIs to fill missing fields in a database record. After each API response, the agent appends only the assistant message to conversation history and resends, omitting the tool_result blocks. The model sometimes repeats the same tool calls on every iteration. What is the root cause of this behaviour?

- A: The agent is not setting tool_choice to auto, which causes the model to ignore its previous tool selections and restart.
- B: Without tool_result blocks in the conversation, the model has no record of what calls were made or what they returned, so it re-requests the same tools.
- C: The model requires a separate summarisation step to compress tool outputs before it can continue enriching the record correctly.
- D: The agent should cap the loop at a fixed number of iterations so repeated tool calls are prevented from running more than once.

---

### Test 22 — Messages API Loop (natural-language sentinel)

A developer builds a customer-support agent using the Messages API. After each API call the loop checks whether the response text begins with 'FINAL:' and stops when that prefix appears. In production, the agent sometimes halts mid-task when the model uses that phrase in an intermediate sentence, and sometimes never halts when the model phrases its conclusion differently. What is the root cause?

- A: The system prompt is missing an explicit instruction telling the model to emit FINAL: only once, at the very end of its last message.
- B: The loop termination relies on a natural-language sentinel instead of stop_reason, so it cannot reliably detect when the model has truly finished calling tools.
- C: The model's temperature is too high, causing phrasing to vary across turns so the sentinel phrase appears at unpredictable positions.
- D: The loop needs a hard cap of ten iterations to guarantee termination when the sentinel phrase never appears in the model's output.

---

### Test 23 — Messages API Loop (reply length sentinel)

A developer builds a web-scraping agent on the Messages API. Their loop examines each assistant reply and stops when the reply length drops below 50 characters, assuming short replies signal completion. In testing, the agent terminates mid-scrape and misses tool results. What is the root cause of this failure?

- A: The loop uses reply length as a completion signal instead of inspecting stop_reason, so tool_use turns with brief assistant messages are incorrectly treated as termination.
- B: The loop does not set tool_choice to any, so the model sometimes answers from memory rather than invoking the scraping tool on each request.
- C: The system prompt lacks explicit instructions telling the model to produce longer replies on tool-call turns so the length threshold is never reached.
- D: The agent appends tool_result blocks after the wrong message in the history, causing the model to re-request tools that were already completed.

---

### Test 24 — Messages API Loop (stop_reason correct fix)

A developer writes an agentic loop on the Messages API. After each response, the loop inspects the model's text for a closing signature — three asterisks (***) — and terminates when that pattern appears. In production, the agent stops unexpectedly mid-task when the model uses three asterisks inside a code block, and some runs never terminate because the model phrases its conclusion without the pattern. Which loop-control approach correctly fixes the root cause?

- A: Inspect stop_reason after each API response: loop while it equals tool_use and exit when it equals end_turn.
- B: Set tool_choice to any so the model must call a tool on every turn, removing ambiguous text completions.
- C: Add a hard cap of ten iterations so the loop terminates even when the sentinel text never appears.
- D: Parse the last paragraph and treat any concluding sentence as a reliable signal that the task is done.

---

### Test 25 — Multi-Agent Scheduling (atomic find_and_book)

**Scenario:** Multi-Agent Research System — A scheduling agent uses one tool to retrieve available slots and another to book a slot. Many bookings fail because the slot becomes unavailable between those two calls. How should these tools be redesigned?

- A: Keep both tools and add retry instructions to the system prompt.
- B: Add a hold_slot tool that temporarily reserves the slot between lookup and booking.
- C: Make book_appointment return richer failure details and alternative slots.
- D: Combine them into a single find_and_book operation that atomically checks availability and books, returning confirmation or alternatives.
