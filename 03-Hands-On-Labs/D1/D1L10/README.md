# D1L10 — Orchestrator–Worker: Isolation & Provenance

**Exam mapping:** multi-agent context passing, structured findings with source + confidence, quarantining failed workers (drill Q14; strategy sheet "Multi-agent")
**Estimated time:** ~45 min
**Domain:** 1 — Agentic Architecture & Orchestration (27%, highest weight)
**Key concept:** A subagent is a **separate conversation** — it inherits **nothing** from its parent. You must pass every fact it needs explicitly. In return you get **context isolation** (each worker's window stays small) and a clean handoff surface where **provenance** (source + confidence) and **quarantine** (failed workers walled off) are your job to preserve.

> **How to use this lab:** build it yourself, one step at a time. You'll watch a worker fail because it can't see what the orchestrator "knows," fix it with explicit context passing, then measure the isolation payoff and wire up provenance + quarantine.

---

## What you're proving

1. Subagents do **not** inherit parent context — a worker told to use "the evidence above" with nothing passed will hallucinate or stall.
2. Explicit context passing fixes it, and structured findings (`{finding, source, confidence}`) make the handoff auditable.
3. **Isolation**: each worker processes only its own slice, so per-worker input tokens stay small vs a monolith that carries everything at once.
4. A failed/low-confidence worker gets **quarantined** — walled off with its provenance — instead of leaking a null or garbage finding into the synthesis.

---

## Facts to keep in front of you

- **A subagent = a fresh `messages.create` / `messages.parse` call** with its own `messages` list. There is no shared memory, no inherited system prompt, no inherited history. "The parent knows X" means nothing to the worker unless X is in the worker's prompt.
- **Provenance is not automatic.** If you want to know *which* worker produced a claim and how sure it was, the worker must return it and you must carry it through synthesis.
- **Quarantine, don't drop.** A worker that errors or returns junk should be recorded as failed (with why), not silently omitted — silent omission reads as "clean result" when it isn't. (This is the exam's "quarantine failed subagent output" point.)
- **Model choice:** uses **structured outputs**, so `claude-sonnet-4-6` (or `claude-haiku-4-5`) — both supported and cheap. Not Sonnet 4.5 (not on the structured-outputs support list).

---

## Step 0 — Prereqs

```powershell
# From D1/D1L10.
$env:ANTHROPIC_API_KEY
python -c "import anthropic, pydantic; print('ok')"
New-Item -ItemType File orchestrator.py
```

---

## Step 1 — Prove subagents inherit nothing

Set up a worker as its own conversation, then call it as if it could see data the orchestrator holds — but pass none. Put this in `orchestrator.py`:

```python
import os
import sys
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"


class Finding(BaseModel):
    finding: str          # what the worker concluded
    source: str           # which evidence it used
    confidence: float     # 0.0 - 1.0


def worker(task: str, evidence: str | None) -> Finding:
    """A subagent. Its OWN fresh conversation — it sees ONLY what we pass in `evidence`."""
    content = task
    if evidence:
        content += f"\n\nEVIDENCE:\n{evidence}"
    resp = client.messages.parse(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": content}],
        output_format=Finding,
    )
    return resp.parsed_output


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: no context passed (subagents inherit nothing) ===")
    f = worker(
        task=("From the incident log evidence I gave you, identify the single anomaly "
              "and the exact time it started."),
        evidence=None,   # <- we 'know' the logs in the orchestrator, but pass nothing
    )
    print(f"  finding:    {f.finding}")
    print(f"  source:     {f.source}")
    print(f"  confidence: {f.confidence}")
```

Run it:

```powershell
python orchestrator.py
```

**What to look for — and record:**
- The worker cannot answer. Expect a finding like *"No evidence was provided"* / *"I don't have the logs"* with **low confidence** — or a confident-sounding **hallucination** with an invented time. Either outcome proves the point: **the worker never saw the orchestrator's data.** "The evidence I gave you" is meaningless across the process boundary.

---

## Step 2 — Fix with explicit context passing + structured findings

Now give each worker exactly the slice it needs, and fan out across three evidence blobs. Add the evidence and a dispatch loop:

```python
EVIDENCE = {
    "logs": ("2026-07-14 03:14:02Z host=db-7 disk_usage=100% action=writes_rejected; "
             "ingest latency 12ms -> 4200ms over 8 minutes."),
    "config_diff": ("commit a1b2c3 (21 days ago): log_rotation: enabled -> removed. "
                    "No rotation policy since."),
    "timeline": "",   # deliberately empty - used in Step 4 to trigger a quarantine
}

TASKS = {
    "logs": "Identify the anomaly and the exact time it started.",
    "config_diff": "Identify the configuration change most likely to cause a disk to fill.",
    "timeline": "Identify when the change was deployed relative to the incident.",
}
```

```python
    print("\n=== Step 2: explicit context passing ===")
    findings = {}
    for name in ("logs", "config_diff"):        # skip the empty one for now
        f = worker(TASKS[name], EVIDENCE[name])
        findings[name] = f
        print(f"  [{name}] ({f.confidence:.2f}) {f.finding}  <- source: {f.source}")
```

Run again:

```powershell
python orchestrator.py
```

**What to look for — and record:**
- Both workers now return real findings with **high confidence** and a `source` naming the evidence they used.
- Each worker only ever saw its own blob — it did not (and could not) peek at the others. That's the isolation you'll measure next.

---

## Step 3 — Measure the isolation payoff

Compare per-worker input size against a **monolith** that stuffs all evidence into one conversation. Add a token probe and a monolith call:

```python
    print("\n=== Step 3: context isolation vs monolith ===")

    def input_tokens(system, content):
        return client.messages.count_tokens(
            model=MODEL, messages=[{"role": "user", "content": content}]
        ).input_tokens

    for name in ("logs", "config_diff"):
        prompt = f"{TASKS[name]}\n\nEVIDENCE:\n{EVIDENCE[name]}"
        print(f"  worker[{name}] input_tokens: {input_tokens(None, prompt)}")

    monolith = "Analyze this incident end to end.\n\n" + "\n\n".join(
        f"{k.upper()}:\n{v}" for k, v in EVIDENCE.items()
    )
    print(f"  monolith    input_tokens: {input_tokens(None, monolith)}")
```

Run again:

```powershell
python orchestrator.py
```

**What to look for — and record:**
- Each worker's `input_tokens` reflects **only its own blob**; the monolith carries **all of them at once**.
- The gap is small here (tiny blobs), but the shape is the point: in a real 60-tool-call investigation, the monolith's window grows without bound while each isolated worker stays flat. Isolation is *the* reason to fan out — plus the orchestrator itself only ever sees short findings, not raw evidence, so its window stays clean.

> This is the D5L8 lesson from the *other* side: delegation bounds context by partitioning it across windows, where context editing bounds it by pruning within one window.

---

## Step 4 — Quarantine a failed worker, then synthesize with provenance

Wrap the worker so an error **or** a low-confidence result is quarantined (walled off, recorded), never silently dropped. The empty `timeline` evidence will trigger it. Add:

```python
    print("\n=== Step 4: quarantine + provenance-preserving synthesis ===")

    def safe_dispatch(name):
        try:
            f = worker(TASKS[name], EVIDENCE[name])
            if f.confidence < 0.5:
                return {"worker": name, "status": "quarantined",
                        "reason": f"low confidence ({f.confidence:.2f})", "finding": f.finding}
            return {"worker": name, "status": "ok", "finding": f.finding,
                    "source": f.source, "confidence": f.confidence}
        except Exception as e:
            return {"worker": name, "status": "quarantined", "reason": f"error: {e}"}

    results = [safe_dispatch(n) for n in TASKS]          # includes the empty 'timeline'
    ok = [r for r in results if r["status"] == "ok"]
    quarantined = [r for r in results if r["status"] == "quarantined"]

    # Orchestrator synthesizes ONLY from ok findings, and cites provenance.
    evidence_block = "\n".join(
        f"- {r['finding']} (source: {r['source']}, confidence: {r['confidence']:.2f})" for r in ok
    )
    synth = client.messages.create(
        model=MODEL, max_tokens=300,
        messages=[{"role": "user", "content":
            "You are the orchestrator. Using ONLY these verified findings, state the root "
            f"cause in 1-2 sentences. Cite the sources you relied on.\n\n{evidence_block}"}],
    )
    print("\n  VERIFIED FINDINGS:")
    for r in ok:
        print(f"    - ({r['confidence']:.2f}) {r['finding']}  [{r['source']}]")
    print("\n  QUARANTINED (excluded from synthesis, not dropped):")
    for r in quarantined:
        print(f"    - {r['worker']}: {r['reason']}")
    print("\n  ROOT CAUSE:")
    print("   ", next(b.text for b in synth.content if b.type == "text").strip())
```

Run the finished file:

```powershell
python orchestrator.py
```

**What to look for — and record:**
- The `timeline` worker is **quarantined** (low confidence from empty evidence) and appears in a separate list with its reason — **not** silently missing.
- The root-cause synthesis is built only from the verified findings and **cites its sources**. Provenance survived the handoff: you can trace every clause in the final answer back to a worker and its confidence.
- Flip it to see the failure mode: include the quarantined finding in `evidence_block` and watch a garbage/empty finding pollute the root cause with no way to tell it apart from real evidence.

---

## Key Observations to Record

| Step | What you proved |
|------|-----------------|
| Step 1 | A subagent is a separate conversation — it inherits no parent context; "the data I gave you" is empty across the boundary |
| Step 2 | Explicit context passing + a `{finding, source, confidence}` schema make each worker's output real and auditable |
| Step 3 | Isolation: per-worker windows carry only their slice; the monolith carries everything; the orchestrator sees only short findings |
| Step 4 | Failed/low-confidence workers are quarantined with a reason; synthesis uses only verified findings and cites provenance |

**Key exam points:**

- **Never assume inheritance.** Multi-agent context must be passed explicitly in the subagent's prompt — a subagent cannot see the orchestrator's messages, tools, or memory.
- **Structured findings with source + confidence** are the correct handoff shape; free-text findings lose provenance.
- **Quarantine failed subagent output**, don't drop it — silent omission looks like a clean result. A wrong answer here (the honeypot) is "just skip the ones that errored."
- **Isolation is the reason to use subagents:** each worker's attention and context window stay scoped; the orchestrator's window stays clean. Delegation partitions context across windows (vs context editing, which prunes within one).
- Provenance must **survive synthesis** — the final answer should be traceable to sources, not a blended paragraph of unattributed claims.

---

## Success Criteria

- [ ] Demonstrated no-inheritance (a worker fails/hallucinates with no context passed), then fixed it with explicit passing.
- [ ] Each worker returns a structured `{finding, source, confidence}`, and the final synthesis cites sources.
- [ ] A failing/low-confidence worker is quarantined with a recorded reason and excluded from synthesis — not silently dropped.
- [ ] You measured per-worker isolation vs a monolith and can explain why fanning out bounds context.
- [ ] You can state, in one sentence, why "skip the workers that errored" is the wrong answer and "quarantine with provenance" is right.
