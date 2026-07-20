# D2L13 Answer Key — Tool Definitions That Trigger Correctly

**Solution file:** `tool_design.py`.
Run `python tool_design.py` from this folder with `ANTHROPIC_API_KEY` set.

## Expected results

- **Step 1 (description drives triggering):** vague "Gets information." triggers inconsistently — it may fire on "capital of France" or miss the policy questions, and it varies run to run. The precise description fires on exactly the two internal-policy prompts and stays off the other three. Only the description changed.
- **Step 2 (tool_choice modes):** on "What is the capital of France?" —
  `auto` → no tool, answers "Paris"; `any` → forced pointless tool call (`stop_reason=tool_use`); `{type:"tool","name":"search_kb"}` → forces that tool; `none` → cannot call, answers in text.
- **Step 3 (strict):** without `strict` values *usually* stay in the enum (unlikely ≠ impossible); with `strict: true` a drifted value ("Billing", "tech", invented category) is **impossible** — the API constrains generation to the schema.

## Success-criteria answers

- **The description is the routing logic.** Prescribe the trigger condition ("Call this when…") *and* the negative boundary ("Do NOT call it for…"). Under/over-triggering is a description bug — fix it there, not in the surrounding prompt.
- **tool_choice values:** `auto` = model decides; `any` = some tool required; `{type:"tool",name}` = that tool required; `none` = tools forbidden. `disable_parallel_tool_use` caps at one call per response.
- **Two separate levers:** description governs *whether* the tool is called; `strict` + `enum` + `additionalProperties:false` governs *how the arguments come out*. A good tool needs both.
