# Block A: Strands Agents (real SDK)

## Overview

This block uses the **real Strands Agents SDK** (`pip install strands-agents`,
AWS's model-driven agent framework), pointed at OpenRouter. Strands wraps the raw
tool-calling protocol from Block 0 with:

- `@tool` decorator — a function's docstring + type hints become the JSON schema
- The event loop — the SDK calls the model, routes tool calls, appends results, re-calls
- `hooks` — lifecycle events (e.g. `BeforeToolCallEvent`) to observe or veto tool calls
- `callback_handler` — streams assistant text as it's generated
- Provider abstraction — `OpenAIModel` / `BedrockModel` / others, same Agent code
- Emergent topology — the model decides its own trajectory

## Files

- `tools.py` — plain implementations of `fetch_url`, `clean_html`, `hn_search`
- `agent_strands.py` — the real Strands agent (run this)

## Running

```bash
cd blockA_strands
python agent_strands.py
```

You should see the loop stream, tool call by tool call:

```
======================================================================
BLOCK A: STRANDS AGENTS (real SDK → OpenRouter)
======================================================================

⏺ Task: What are people saying about LangGraph on Hacker News recently? ...

  ⏺ hn_search(query='LangGraph', days_back=14)
  ⏺ fetch_url(url='https://news.ycombinator.com/item?id=49335595')
  ⏺ clean_html(html='...')

## LangGraph on Hacker News (Past 2 Weeks)
...synthesis streams here, with links...

======================================================================
PROBES
======================================================================
messages in context : 14
```

## How it wires to OpenRouter

Strands defaults to AWS Bedrock. To use any OpenAI-compatible endpoint
(OpenRouter, OpenAI, a local gateway), use `OpenAIModel` with `client_args`:

```python
from strands import Agent, tool
from strands.models.openai import OpenAIModel

model = OpenAIModel(
    client_args={
        "api_key": os.environ["OPENROUTER_API_KEY"],
        "base_url": "https://openrouter.ai/api/v1",
    },
    model_id="openrouter/free",
)

agent = Agent(model=model, tools=[hn_search, fetch_url, clean_html])
result = agent("What are people saying about LangGraph on HN?")
```

## Two ways to observe the loop

1. **Hook (clean, once per call, full args)** — used for the `⏺ tool(...)` lines:

   ```python
   from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent

   class ToolPrinter(HookProvider):
       def register_hooks(self, registry: HookRegistry, **_):
           registry.add_callback(BeforeToolCallEvent, self._on_tool)
       def _on_tool(self, event: BeforeToolCallEvent):
           print(event.tool_use["name"], event.tool_use["input"])
   ```

   `BeforeToolCallEvent` is also where you'd **veto** a call (`event.cancel_tool = ...`) —
   that's the same idea as pi's `onToolCall` guard in Block B.

2. **callback_handler (streaming text)** — prints assistant tokens as they arrive.

## Free-model wrinkle (a teaching moment)

Free models on OpenRouter emit "reasoning" tokens that the Chat Completions API
can't replay on the next turn, so Strands logs:
`reasoningContent is not supported in multi-turn conversations...`
It's benign — we quiet the `strands` logger. On a stronger model it won't appear.
