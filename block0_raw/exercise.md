# Block 0 Exercise

## What you just saw

The entire agent abstraction in ~100 lines:
1. **Tool schema** (hand-written JSON Schema)
2. **Model proposes tool call** (returns structured JSON)
3. **Execute the tool** (your code)
4. **Append result to messages** (as a "tool" role message)
5. **Call model again** - it sees the result, continues or stops

## Your turn

Add a second tool to the system. Suggestions:

### Option 1: get_current_time
```python
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
```

### Option 2: calculate
```python
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression)  # NEVER do this in production!
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"
```

### Steps:
1. Define the function
2. Add its JSON Schema to the `tools` list
3. Add a handler in the tool execution block
4. Test with a new task that uses both tools

### What you'll learn

Both Strands and pi wrap this exact flow. The frameworks give you:
- Automatic schema generation (from docstrings or TypeBox)
- Cleaner execution dispatch
- Event observation
- Error recovery

But the wire format is **this**.
