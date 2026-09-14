#!/usr/bin/env python3
"""
Quick demo of all three workshop components:
1. Raw protocol (Block 0)
2. Strands pattern (Block A)
3. Judge system (Block C)
"""

import os
import sys
from pathlib import Path

# Load .env
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

print("=" * 70)
print("WORKSHOP DEMO")
print("=" * 70)
print()
print("This demo shows all three workshop blocks working:")
print("  1. Block 0: Raw tool-calling protocol")
print("  2. Block A: Strands agent pattern")
print("  3. Block C: Judge system")
print()
print("=" * 70)
input("Press Enter to start Block 0 (raw protocol)...")

# Block 0
print("\n" + "=" * 70)
print("BLOCK 0: RAW PROTOCOL")
print("=" * 70)
os.system("cd block0_raw && python3 raw_toolcall.py")

input("\nPress Enter to continue to Block A (Strands pattern)...")

# Block A
print("\n" + "=" * 70)
print("BLOCK A: STRANDS PATTERN")
print("=" * 70)
print("This will search HN and synthesize findings...")
print()
os.system("cd blockA_strands && python3 agent_strands.py")

input("\nPress Enter to test the Judge system...")

# Judge test
print("\n" + "=" * 70)
print("BLOCK C: JUDGE SYSTEM")
print("=" * 70)
print("Testing with a sample report...")
print()
os.system("cd blockC_capstone && python3 judge.py")

print("\n" + "=" * 70)
print("DEMO COMPLETE")
print("=" * 70)
print()
print("What you saw:")
print("  ✓ Raw tool-calling JSON (Block 0)")
print("  ✓ Strands agent with web research tools (Block A)")
print("  ✓ LLM-as-judge scoring reports (Block C)")
print()
print("Next steps:")
print("  - Try: cd blockC_capstone && python3 outer_loop_complete.py")
print("    (Full outer loop: agent + judge + retry with critique)")
print()
print("  - Read: README.md for full workshop details")
print("  - Explore: Modify tools, prompts, and rubrics")
print()
