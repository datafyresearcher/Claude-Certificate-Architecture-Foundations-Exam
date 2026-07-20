"""D1L10 answer key — Orchestrator-Worker: Isolation & Provenance.

Assembled solution for all four steps of D1/D1L10/README.md.
Run:  python orchestrator.py   (requires ANTHROPIC_API_KEY, anthropic, pydantic)
"""
import os
import sys
from pydantic import BaseModel
import anthropic

MODEL = "claude-sonnet-4-6"


class Finding(BaseModel):
    finding: str          # what the worker concluded
    source: str           # which evidence it used
    confidence: float     # 0.0 - 1.0


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

    # ---- Step 1: no context passed (subagents inherit nothing) ----
    print("=== Step 1: no context passed (subagents inherit nothing) ===")
    f = worker(
        task=("From the incident log evidence I gave you, identify the single anomaly "
              "and the exact time it started."),
        evidence=None,   # <- we 'know' the logs in the orchestrator, but pass nothing
    )
    print(f"  finding:    {f.finding}")
    print(f"  source:     {f.source}")
    print(f"  confidence: {f.confidence}")

    # ---- Step 2: explicit context passing + structured findings ----
    print("\n=== Step 2: explicit context passing ===")
    findings = {}
    for name in ("logs", "config_diff"):        # skip the empty one for now
        f = worker(TASKS[name], EVIDENCE[name])
        findings[name] = f
        print(f"  [{name}] ({f.confidence:.2f}) {f.finding}  <- source: {f.source}")

    # ---- Step 3: context isolation vs monolith ----
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

    # ---- Step 4: quarantine + provenance-preserving synthesis ----
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
