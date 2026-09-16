#!/usr/bin/env python3
"""
Block 0: The Naked Protocol
Raw tool-calling round-trip with no framework.

This is the entire abstraction - everything else is ergonomics around this JSON.
"""

import os
import json
import requests
from openai import OpenAI
from pathlib import Path

# ============================================================================
# Setup: Load environment and OpenRouter via OpenAI SDK
# ============================================================================

# Load .env file if it exists
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file")
    print("Please create .env file with your OpenRouter API key")
    exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

MODEL = os.getenv("MODEL", "openrouter/free")

# ============================================================================
# Tool implementation
# ============================================================================

def fetch_url(url: str) -> str:
    """Fetch a URL and return its content."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return f"✓ {response.status_code} OK, {len(response.text)} bytes\n\n{response.text[:500]}..."
    except Exception as e:
        return f"✗ Error: {str(e)}"

# ============================================================================
# Tool schema (hand-written JSON Schema)
# ============================================================================

tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_url",
            "description": "Fetch a URL and return its content",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Tells the current time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"calculate",
            "description":"Evaluates a mathematical expression",
            "parameters":{
                "type":"object",
                "properties":{
                    "expression":{
                        "type":"string",
                        "description":"the mathematical expression to evaluate"
                    }
                },
                "required":["expression "]
            }
        }
    }
]

# ============================================================================
# The loop
# ============================================================================

def run_agent(task: str):
    """Run the agent loop: model proposes tools, we execute, repeat."""

    messages = [
        {"role": "user", "content": task}
    ]

    print(f"⏺ User: {task}\n")

    iteration = 0
    max_iterations = 10

    while iteration < max_iterations:
        iteration += 1

        # Call the model
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message

        # Check if the model wants to use a tool
        if message.tool_calls:
            print(f"⏺ Assistant proposes tool call:")

            # Process each tool call
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"  name: {function_name}")
                print(f"  args: {json.dumps(function_args)}")
                print()

                # Execute the tool
                if function_name == "fetch_url":
                    print(f"⏺ Executing...")
                    result = fetch_url(function_args["url"])
                    print(f"  ⎿ {result.split(chr(10))[0]}")  # First line only
                    print()
                elif function_name=="get_current_time":
                    print(f"- Finding time...")
                    result=get_current_time()
                    print(result)
                    print()
                elif function_name=="calculate":
                    print(f"- calculating...")
                    result=calculate(function_args["expression"])
                    print(result)
                    print()
                else:
                    result = f"Error: Unknown tool {function_name}"

                # Append assistant message and tool result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tool_call.model_dump()]
                })

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

            print("⏺ Tool result appended to messages\n")
            # Continue loop - model will see the result

        else:
            # Model responded with text, no tool call - we're done
            print(f"⏺ Assistant: {message.content}\n")
            break

    if iteration >= max_iterations:
        print(f"⚠ Reached max iterations ({max_iterations})")

# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    # Simple task to demonstrate the loop
    #task = "Fetch https://lakersnation.com/jj-redick-believes-lakers-luka-doncic-is-not-being-talked-about-enough/ tell me what you see"
    #task="tell me the current time"
    #task="my vacations start at 24 november, can you find out how many days are left?"
    task="what is 25+7"
    task = "Fetch https://www.coursera.org/in/articles/game-developer tell me what you see"

    print("=" * 70)
    print("BLOCK 0: THE NAKED PROTOCOL")
    print("=" * 70)
    print()

    run_agent(task)

    print("\n" + "=" * 70)
    print("EXERCISE: Add a second tool (e.g., 'get_current_time')")
    print("=" * 70)
