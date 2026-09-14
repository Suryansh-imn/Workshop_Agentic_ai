#!/usr/bin/env python3
"""
Block C: The Outer Loop (real Strands agent + LLM judge).

Verifier-terminated loop: the JUDGE decides "done", not the model.

  inner loop  = the Strands agent (model decides its own tool trajectory)
  outer loop  = ordinary Python: run agent -> judge -> inject critique -> retry
  termination = judge score >= 4, or MAX_JUDGE_RETRIES reached (then PARK)

This reuses the SAME real Strands agent from Block A (blockA_strands/agent_strands.py),
adding one extra @tool — save_report — so the agent writes its answer to disk where
the judge can score it.
"""

import os
import sys
from pathlib import Path

# --- load .env -------------------------------------------------------------
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ[key] = value

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from strands import tool

from judge import judge
from blockA_strands.agent_strands import build_agent
from shared.config import MODEL, FALLBACK_MODEL, MAX_JUDGE_RETRIES

REPORT_FILE = "report.md"


@tool
def save_report(content: str) -> str:
    """Save the finished research report to disk so it can be reviewed.

    Args:
        content: The full markdown report.
    """
    Path(REPORT_FILE).write_text(content)
    return f"✓ Saved {len(content)} chars to {REPORT_FILE}"


CAPSTONE_PROMPT = (
    "You are a web research assistant. Use hn_search to find recent Hacker News "
    "discussions, fetch_url to read them, and clean_html to extract text. "
    "Synthesize the key themes WITH links. When your report is complete, you MUST "
    "call save_report(content=...) with the full markdown report."
)


def build_capstone_agent(model_id: str):
    """Block A's real Strands agent + the save_report tool."""
    return build_agent(model_id, extra_tools=[save_report],
                        system_prompt=CAPSTONE_PROMPT)


def run_outer_loop(task: str):
    score = 0
    iteration = 0
    critique = ""

    print("=" * 70)
    print("OUTER LOOP: VERIFIER-TERMINATED (real Strands agent + judge)")
    print("=" * 70)

    # Start clean so a stale report can't be judged.
    Path(REPORT_FILE).unlink(missing_ok=True)

    while score < 4 and iteration < MAX_JUDGE_RETRIES:
        iteration += 1
        print(f"\n{'─' * 70}")
        print(f"⏺ Outer-loop iteration {iteration}/{MAX_JUDGE_RETRIES}")
        print("─" * 70)

        # Inject the judge's prior critique into the retry prompt.
        prompt = task
        if critique:
            prompt += (
                f"\n\n🔄 A reviewer scored your previous report {score}/5 and said: "
                f"\"{critique}\"\nProduce a NEW, improved report addressing this."
            )

        # --- inner loop: the real Strands agent runs its own tool trajectory ---
        agent = build_capstone_agent(MODEL)
        try:
            agent(prompt)
        except Exception as e:
            print(f"\n⚠ {MODEL} failed ({e}); retrying with {FALLBACK_MODEL}")
            agent = build_capstone_agent(FALLBACK_MODEL)
            agent(prompt)

        if not Path(REPORT_FILE).exists():
            print("\n  ⚠ Agent never called save_report — scoring empty. Critique will nudge it.")
            report = ""
        else:
            report = Path(REPORT_FILE).read_text()

        # --- verifier: the judge decides ---
        print("\n\n  ⚖  Judging report...")
        verdict = judge(report, REPORT_FILE)
        score = verdict.get("overall", 0)
        critique = verdict.get("critique", "")

        print(f"  📊 iteration {iteration} → score {score}/5")
        print(f"  💬 critique: {critique}")

    print("\n" + "=" * 70)
    if score >= 4:
        print(f"✓ Task COMPLETE — final score {score}/5 in {iteration} iteration(s)")
    else:
        print(f"⚠ Max retries reached. Final score {score}/5")
        print("❌ Task PARKED — escalate to human review")
    print("=" * 70)
    return score >= 4


def main():
    task = (
        "Research what people are saying about LangGraph on Hacker News recently.\n"
        "Your report should:\n"
        "1. Search HN for recent LangGraph discussions\n"
        "2. Read a couple of threads\n"
        "3. Identify 3-5 key themes\n"
        "4. Include at least 3 HN discussion links\n"
        "5. Synthesize — explain what the community thinks, don't just list\n"
        "Format as markdown."
    )

    success = run_outer_loop(task)

    if success and Path(REPORT_FILE).exists():
        print("\nFinal report:\n" + "=" * 70)
        print(Path(REPORT_FILE).read_text())
        print("=" * 70)


if __name__ == "__main__":
    main()
