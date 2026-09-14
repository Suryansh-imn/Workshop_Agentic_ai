#!/usr/bin/env python3
"""
Block A: Strands Agents — the REAL SDK.

Uses the actual `strands-agents` package (https://pypi.org/project/strands-agents/),
pointed at OpenRouter via its OpenAI-compatible model provider.

    pip install strands-agents

Strands is AWS's model-driven agent SDK. Its default provider is Bedrock, but it
ships an OpenAI-compatible provider (`strands.models.openai.OpenAIModel`) that takes
any base_url — so we point it straight at OpenRouter.

What the harness does for you here:
  - @tool turns a plain Python function (docstring + type hints) into a JSON schema
  - the event loop calls the model, routes tool calls, appends results, re-calls
  - callback_handler streams every event (tool call, text, completion) to stdout
"""

import os
import sys
import logging
from pathlib import Path

# --- load .env -------------------------------------------------------------
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value

_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, ".."))  # repo root (for `shared`)
sys.path.insert(0, _HERE)                       # this dir (for `tools`)

# Free models on OpenRouter emit reasoning tokens the Chat Completions API
# can't replay; Strands logs a warning each turn. Silence it — it's benign.
logging.getLogger("strands").setLevel(logging.ERROR)

from strands import Agent, tool
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent
from strands.models.openai import OpenAIModel

from shared.config import MODEL, FALLBACK_MODEL
from transcript import TranscriptRecorder
import tools as raw_tools


# --- tools: wrap the shared implementations with @tool ---------------------
# @tool reads the docstring + type hints to build the JSON schema the model sees.

@tool
def hn_search(query: str, days_back: int = 7) -> str:
    """Search Hacker News for recent stories matching a query.

    Args:
        query: The search term (e.g. "LangGraph").
        days_back: How many days back to look. Defaults to 7.
    """
    return raw_tools.hn_search(query, days_back)


@tool
def fetch_url(url: str) -> str:
    """Fetch a URL over HTTP and return the raw response body.

    Args:
        url: The absolute URL to fetch.
    """
    return raw_tools.fetch_url(url)


@tool
def clean_html(html: str) -> str:
    """Strip tags from an HTML string and return readable text (max 6000 chars).

    Args:
        html: Raw HTML to clean.
    """
    return raw_tools.clean_html(html)


# --- make the loop visible --------------------------------------------------
# Two channels of observability, both first-class in Strands:
#   1. A hook on BeforeToolCallEvent — fires once per tool call with the FULL,
#      parsed arguments. This is the clean way to show "the model called X(...)".
#      (It's also exactly where you'd VETO a call — see Block B's guard.)
#   2. callback_handler — streams assistant text chunks so the final synthesis
#      prints live as the model writes it.

class ToolPrinter(HookProvider):
    """Prints each tool call as the harness routes it."""

    def register_hooks(self, registry: HookRegistry, **_):
        registry.add_callback(BeforeToolCallEvent, self._on_tool)

    def _on_tool(self, event: BeforeToolCallEvent):
        tool_use = event.tool_use
        name = tool_use.get("name", "?")
        args = tool_use.get("input", {})
        arg_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
        print(f"\n  ⏺ {name}({arg_str})")


def text_stream(**kwargs):
    """callback_handler: stream assistant text to stdout as it's generated."""
    if kwargs.get("data"):
        print(kwargs["data"], end="", flush=True)


def build_agent(model_id: str, extra_tools: list | None = None,
                system_prompt: str | None = None,
                extra_hooks: list | None = None) -> Agent:
    """Construct a Strands Agent wired to OpenRouter.

    Args:
        model_id: OpenRouter model id (e.g. "openrouter/free").
        extra_tools: additional @tool functions to register (e.g. save_report
            in Block C). Composed with the three web-research tools.
        system_prompt: override the default research prompt.
        extra_hooks: extra HookProviders (e.g. a TranscriptRecorder) to attach
            alongside the tool printer.
    """
    model = OpenAIModel(
        client_args={
            "api_key": os.environ["OPENROUTER_API_KEY"],
            "base_url": "https://openrouter.ai/api/v1",
        },
        model_id=model_id,
    )

    return Agent(
        model=model,
        tools=[hn_search, fetch_url, clean_html, *(extra_tools or [])],
        system_prompt=system_prompt or (
            "You are a web research assistant. Use hn_search to find recent "
            "Hacker News discussions, fetch_url to read them, and clean_html to "
            "extract text. Then synthesize the key themes with links. Be concise."
        ),
        hooks=[ToolPrinter(), *(extra_hooks or [])],
        callback_handler=text_stream,
    )


def main():
    print("=" * 70)
    print("BLOCK A: STRANDS AGENTS (real SDK → OpenRouter)")
    print("=" * 70)

    task = (
        "What are people saying about LangGraph on Hacker News recently? "
        "Search, read a couple of discussions, and summarize the key themes "
        "with links."
    )
    print(f"\n⏺ Task: {task}\n")

    # Record every model request/response so we can render an HTML transcript.
    recorder = TranscriptRecorder(task=task, model_id=MODEL)

    model_id = MODEL
    try:
        agent = build_agent(model_id, extra_hooks=[recorder])
        result = agent(task)
    except Exception as e:
        print(f"\n⚠ {model_id} failed ({e}). Retrying with fallback {FALLBACK_MODEL}...")
        recorder.model_id = FALLBACK_MODEL
        agent = build_agent(FALLBACK_MODEL, extra_hooks=[recorder])
        result = agent(task)

    out = os.path.join(_HERE, "transcript.html")
    recorder.to_html(out)

    print("\n\n" + "=" * 70)
    print("PROBES")
    print("=" * 70)
    print(f"messages in context : {len(agent.messages)}")
    print(f"📄 Full model transcript written to: {out}")
    print("   Open it in a browser to see every request/response, turn by turn.")


if __name__ == "__main__":
    main()
