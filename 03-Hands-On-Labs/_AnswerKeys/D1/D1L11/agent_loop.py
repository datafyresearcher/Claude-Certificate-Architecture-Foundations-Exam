"""D1L11 answer key — The Agent Loop Done Right.

Assembled solution for all four steps of D1/D1L11/README.md.
`run()` takes a `serialize` flag so Step 4 needs no manual edit.
Run:  python agent_loop.py   (requires ANTHROPIC_API_KEY, anthropic)
"""
import os
import sys
import anthropic

MODEL = "claude-sonnet-4-6"

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city. Call this when the user asks about weather.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "get_population",
        "description": "Get the population of a city. Call this when the user asks about population or size.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
]

WEATHER = {"paris": "18°C, cloudy", "tokyo": "24°C, clear", "cairo": "33°C, sunny"}
POP = {"paris": "2.1M", "tokyo": "13.9M", "cairo": "10.0M"}


def execute(name, args):
    city = args.get("city", "").strip().lower()
    if name == "get_weather":
        return WEATHER.get(city, "unknown")
    if name == "get_population":
        return POP.get(city, "unknown")
    return f"unknown tool {name}"


def run(user_msg, max_iters=10, serialize=False):
    """The CORRECT loop: stop_reason primary, iteration cap as loud backstop only."""
    messages = [{"role": "user", "content": user_msg}]
    kwargs = {}
    if serialize:  # Step 4: force one tool_use per response
        kwargs["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}
    for i in range(1, max_iters + 1):
        resp = client.messages.create(
            model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages, **kwargs,
        )
        print(f"  turn {i}: stop_reason={resp.stop_reason}")

        if resp.stop_reason == "end_turn":
            return next((b.text for b in resp.content if b.type == "text"), "")

        if resp.stop_reason == "pause_turn":          # server-tool pause; resume by re-sending
            messages.append({"role": "assistant", "content": resp.content})
            continue

        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    result = execute(block.name, block.input)
                    print(f"           tool_use: {block.name}({block.input}) -> {result}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,     # MUST match the tool_use block's id
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        # max_tokens / refusal / anything else: terminal for this simple loop
        return f"[stopped on {resp.stop_reason}]"

    return "[hit iteration backstop — investigate, don't treat as normal]"


def run_nl_parse(user_msg, max_iters=6):
    """ANTI-PATTERN (Step 2a): terminate by scanning the model's prose."""
    messages = [{"role": "user", "content": user_msg}]
    for i in range(1, max_iters + 1):
        resp = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages)
        text = " ".join(b.text for b in resp.content if b.type == "text").lower()
        print(f"  turn {i}: stop_reason={resp.stop_reason} | text_has_'done'={'done' in text or 'here' in text}")

        # ANTI-PATTERN: decide termination from prose, ignoring stop_reason
        if "done" in text or "here" in text or "the weather" in text:
            return "[stopped because text looked final]"

        # still have to advance tools or we deadlock
        if resp.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": resp.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": b.id, "content": execute(b.name, b.input)}
                for b in resp.content if b.type == "tool_use"]})
    return "[ran to cap without a text match]"


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Set ANTHROPIC_API_KEY first.")
    client = anthropic.Anthropic()

    print("=== Step 1: canonical stop_reason-driven loop ===")
    print("ANSWER:", run("What's the weather in Paris?"))

    print("\n=== Step 2a: NL-parse termination (anti-pattern) ===")
    print("RESULT:", run_nl_parse("What's the weather in Paris?"))

    print("\n=== Step 2b: iteration cap as the stop mechanism ===")
    print("RESULT:", run("Compare the weather AND population of Paris and Tokyo.", max_iters=1))

    print("\n=== Step 3: same task, correct loop ===")
    print("ANSWER:", run("Compare the weather AND population of Paris and Tokyo."))

    print("\n=== Step 4: parallel (default) vs serialized ===")
    print("-- parallel (count the tool_use lines under turn 1):")
    run("Compare the weather AND population of Paris and Tokyo.")
    print("-- serialized (disable_parallel_tool_use=True — one tool_use per turn):")
    run("Compare the weather AND population of Paris and Tokyo.", serialize=True)
