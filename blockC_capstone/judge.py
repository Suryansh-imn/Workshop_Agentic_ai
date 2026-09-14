"""
Block C: The Judge System

An LLM-as-judge that scores research reports.
Uses openrouter/free with defensive parsing.
"""

import os
import json
import re
from openai import OpenAI
from typing import Dict
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value


def judge(report: str, report_file: str = "report.md") -> Dict[str, any]:
    """
    Judge a research report using an LLM.

    Args:
        report: The report text to judge
        report_file: Path to check for file existence

    Returns:
        dict with keys: overall (1-5), critique (str)
    """

    # Sanity check first (no LLM cost)
    if len(report) < 100:
        return {
            "overall": 1,
            "critique": "Report too short - less than 100 characters"
        }

    if not os.path.exists(report_file):
        return {
            "overall": 1,
            "critique": "Report file not found"
        }

    # Check for links
    link_count = len(re.findall(r'https?://[^\s]+', report))
    if link_count < 2:
        return {
            "overall": 2,
            "critique": f"Only {link_count} links found - need at least 3 HN discussion links"
        }

    # Now use LLM judge
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    model = os.getenv("MODEL", "openrouter/free")

    rubric = """Score this Hacker News research report on a scale of 1-5.

Rubric:
- Completeness (1-5): Did it answer the question fully?
- Grounding (1-5): Are claims backed by specific sources?
- Links (1-5): At least 3 HN discussion links included?
- Synthesis (1-5): Does it identify themes, not just list items?

Overall score: Average of the above, rounded.

Return your verdict as JSON:
{
  "completeness": <1-5>,
  "grounding": <1-5>,
  "links": <1-5>,
  "synthesis": <1-5>,
  "overall": <1-5>,
  "critique": "<one sentence on how to improve>"
}
"""

    prompt = f"{rubric}\n\nReport to score:\n\n{report}"

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            response_format={"type": "json_object"} if "gpt" not in model else None
        )

        content = response.choices[0].message.content

        # Defensive parsing
        verdict = parse_json_defensively(content)

        # Ensure we have overall and critique
        if "overall" not in verdict:
            verdict["overall"] = 3  # Default to middle
        if "critique" not in verdict:
            verdict["critique"] = "No specific critique provided"

        return verdict

    except Exception as e:
        print(f"⚠ Judge error: {e}")
        # Degrade gracefully
        return {
            "overall": 1,
            "critique": f"Judge failed: {str(e)}"
        }


def parse_json_defensively(text: str) -> Dict:
    """Parse JSON with defensive handling of markdown fences, etc."""

    # Strip markdown code fences
    text = re.sub(r'^```json\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*', '', text, flags=re.MULTILINE)
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        match = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass

        # Give up
        return {
            "overall": 1,
            "critique": "Failed to parse judge output"
        }


# ============================================================================
# Test harness
# ============================================================================

if __name__ == "__main__":
    # Test with a sample report
    sample_report = """
# LangGraph Discussion Summary

Based on recent Hacker News discussions:

## Key Themes

1. **Complexity vs Power** - Multiple threads debate whether LangGraph's
   state machine approach is too complex for simple agentic workflows.
   Discussion: https://news.ycombinator.com/item?id=123456

2. **Determinism** - Users appreciate having control over workflow topology
   rather than letting the LLM decide everything.
   Discussion: https://news.ycombinator.com/item?id=123457

3. **Resume/Checkpointing** - The built-in checkpointing for long-running
   workflows is frequently cited as a killer feature.
   Discussion: https://news.ycombinator.com/item?id=123458

## Sources
- https://news.ycombinator.com/item?id=123456
- https://news.ycombinator.com/item?id=123457
- https://news.ycombinator.com/item?id=123458
- https://blog.langchain.dev/langgraph-example
"""

    # Write test report
    with open("report.md", "w") as f:
        f.write(sample_report)

    print("Testing judge with sample report...")
    print()

    verdict = judge(sample_report)

    print("Verdict:")
    print(json.dumps(verdict, indent=2))
    print()
    print(f"Overall: {verdict['overall']}/5")
    print(f"Critique: {verdict['critique']}")
