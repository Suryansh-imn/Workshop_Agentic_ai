"""Shared configuration for the workshop."""

# Default model: OpenRouter's free meta-router
MODEL = "openrouter/free"

# Fallback model: a specific free model with tool-calling support
# This should be verified working before the workshop
FALLBACK_MODEL = "meta-llama/llama-3.1-8b-instruct:free"

# Iteration caps (for free models)
MAX_ITERATIONS = 10
TOOL_TIMEOUT = 60  # seconds
MAX_JUDGE_RETRIES = 3
