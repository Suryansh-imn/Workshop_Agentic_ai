#!/bin/bash
# Non-interactive demo - runs all blocks in sequence

echo "======================================================================"
echo "                   WORKSHOP DEMO - ALL BLOCKS"
echo "======================================================================"
echo
echo "This demo runs all three workshop blocks in sequence:"
echo "  1. Block 0: Raw tool-calling protocol"
echo "  2. Block A: Strands agent (HN research)"
echo "  3. Block C: Judge system"
echo
echo "======================================================================"
echo

# Block 0
echo "======================================================================"
echo "BLOCK 0: RAW PROTOCOL"
echo "======================================================================"
cd block0_raw
python3 raw_toolcall.py
cd ..
echo
echo "✅ Block 0 complete - Raw protocol demonstrated"
echo

# Block A
echo "======================================================================"
echo "BLOCK A: STRANDS AGENT PATTERN"
echo "======================================================================"
cd blockA_strands
python3 agent_strands.py
cd ..
echo
echo "✅ Block A complete - Strands agent synthesized HN research"
echo

# Block C
echo "======================================================================"
echo "BLOCK C: JUDGE SYSTEM"
echo "======================================================================"
cd blockC_capstone
python3 judge.py
cd ..
echo
echo "✅ Block C complete - Judge scored report"
echo

echo "======================================================================"
echo "                        DEMO COMPLETE! ✅"
echo "======================================================================"
echo
echo "What you saw:"
echo "  ✅ Raw tool-calling JSON (Block 0)"
echo "  ✅ Strands agent with web research tools (Block A)"
echo "  ✅ LLM-as-judge scoring reports (Block C)"
echo
echo "Next: Try the outer loop (agent + judge + retry)"
echo "  cd blockC_capstone && python3 outer_loop_complete.py"
echo
