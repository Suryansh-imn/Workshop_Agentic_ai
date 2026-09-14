#!/bin/bash
# Test all workshop blocks

echo "=========================================="
echo "Testing Workshop Blocks"
echo "=========================================="
echo
echo "Make sure you've added OPENROUTER_API_KEY to .env first!"
echo
read -p "Press Enter to continue..."

# Test Block 0
echo
echo "=========================================="
echo "Block 0: Raw Protocol"
echo "=========================================="
cd block0_raw
python3 raw_toolcall.py
cd ..

# Wait
echo
read -p "Press Enter to test Block A (Strands)..."

# Test Block A
echo
echo "=========================================="
echo "Block A: Strands Pattern"
echo "=========================================="
cd blockA_strands
python3 agent_strands.py
cd ..

# Wait
echo
read -p "Press Enter to test Block C (Outer Loop with Judge)..."

# Test Block C
echo
echo "=========================================="
echo "Block C: Outer Loop + Judge"
echo "=========================================="
cd blockC_capstone
python3 outer_loop_complete.py
cd ..

echo
echo "=========================================="
echo "All tests complete!"
echo "=========================================="
