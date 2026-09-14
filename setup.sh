#!/bin/bash
# Workshop setup script

set -e

echo "=========================================="
echo "Open the Hood Workshop - Setup"
echo "=========================================="
echo

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.11+"
    exit 1
fi
echo "✓ Python found: $(python3 --version)"

# Install dependencies
echo
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Check .env
echo
echo "Checking environment..."
if [ ! -f .env ]; then
    echo "⚠ .env file not found"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo
    echo "⚠ IMPORTANT: Edit .env and add your OPENROUTER_API_KEY"
    echo "Get your key at: https://openrouter.ai/keys"
else
    echo "✓ .env file exists"
fi

# Check API key
if grep -q "your_key_here" .env 2>/dev/null; then
    echo "⚠ WARNING: .env still has placeholder key"
    echo "   Edit .env and add your real OpenRouter API key"
else
    echo "✓ API key appears to be set"
fi

echo
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Make sure your OpenRouter API key is in .env"
echo "2. Run: cd block0_raw && python raw_toolcall.py"
echo "3. Check the README.md for full workshop flow"
echo
