# Open the Hood: Agentic AI Internals Workshop

Build agent loops from scratch - raw protocol, Strands (Python), pi (TypeScript), and verifier-terminated outer loops. All on OpenRouter free models (₹0/token).

## Quick Start

### 1. Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy and edit .env file
cp .env.example .env
# Add your OPENROUTER_API_KEY
```

### 2. Get OpenRouter Key

1. Go to https://openrouter.ai/
2. Create account
3. Generate API key at https://openrouter.ai/keys
4. Optional: Add $10 credit (raises daily caps, still $0/token)

### 3. Test Your Setup

```bash
# Block 0: Raw protocol (no framework)
cd block0_raw
python raw_toolcall.py

# Block A: Strands Agents — real SDK (Python)
cd ../blockA_strands
python agent_strands.py

# Block C: Outer loop with judge
cd ../blockC_capstone
python outer_loop_complete.py
```

## Workshop Structure

### Block 0: The Naked Protocol (15 min)
**Files:** `block0_raw/`
- Raw tool-calling JSON
- OpenAI SDK + OpenRouter
- One tool, one task, visible loop
- **Exercise:** Add a second tool

### Block A: Strands Agents — real SDK (40 min)
**Files:** `blockA_strands/`
- Real `strands-agents` SDK (`pip install strands-agents`), pointed at OpenRouter
- `@tool` decorator (docstring + type hints → schema)
- `OpenAIModel` provider with `base_url` → OpenRouter
- `BeforeToolCallEvent` hook to show/veto tool calls; `callback_handler` streams text
- Web research agent (HN search + fetch + clean)
- **Run:** `python agent_strands.py`

### Block B: pi (TypeScript) — live demo
**Files:** `blockB_pi/`
- pi-agent-core: minimal TypeScript harness
- AgentTool + TypeBox schemas, `subscribe()` events, `onToolCall` guards
- Built live with Claude Code + Opus (no TypeScript expertise needed)

### Block C: The Outer Loop (20 min)
**Files:** `blockC_capstone/`
- Verifier-terminated loop
- LLM-as-judge (free model judges free model)
- Critique injection on retry
- Bounded retries (max 3)
- **Exercise:** Wrap your Block A agent in the judge loop

## What You'll Build

1. ✅ Raw tool-calling round-trip (35 lines of Python)
2. ✅ Strands-pattern agent with 3 web tools
3. ✅ Printing callback that observes every turn
4. ✅ Outer loop where judge decides "done"
5. ✅ Critique injection for retry guidance

## Cost

**₹0 per token** - everything uses `openrouter/free` meta-router.

Optional $10 OpenRouter credit raises daily request caps but stays free.

## Constraints You'll Hit (And Learn From)

- **Slow:** 30-60s per agent run (free model queuing)
- **Rate limits:** 200-500 requests/day per key
- **Weaker tool-calling:** Free models sometimes malform tool args
- **Solution:** Bounded retries, defensive parsing, schema checks first

These constraints teach **harness design under pressure** - techniques transfer to production cost budgets.

## File Tree

```
open-the-hood-workshop/
├── README.md (this file)
├── requirements.txt
├── .env.example
├── shared/
│   ├── config.py          # MODEL, caps, timeouts
│   └── endpoints.md       # HN Algolia API docs
├── block0_raw/
│   ├── raw_toolcall.py    # Complete, run this first
│   └── exercise.md
├── blockA_strands/
│   ├── tools.py           # fetch_url, clean_html, hn_search
│   ├── agent_strands.py   # Real Strands SDK → OpenRouter
│   └── README.md
├── blockB_pi/             # TODO: TypeScript version
└── blockC_capstone/
    ├── judge.py           # LLM-as-judge with defensive parsing
    ├── outer_loop_complete.py
    └── solutions/
```

## Troubleshooting

### "No API key found"
- Check `.env` file exists and has `OPENROUTER_API_KEY=sk-or-v1-...`
- Make sure you're running from the correct directory

### "Rate limited"
- Free models have caps (~200-500 req/day)
- Wait a few minutes or add $10 credit
- Switch to FALLBACK_MODEL in `shared/config.py`

### "Tool call malformed"
- Free models are weaker at tool-calling
- This is expected! Judge handles it gracefully
- Real lesson: defensive parsing matters

### Slow responses
- Free models queue behind paid traffic
- 30-60s per call is normal
- This teaches patience and bounded retries

## What's Next

After the workshop:
1. Try on paid models (faster, stronger tool-calling)
2. Add your own tools
3. Build your own judge rubric
4. Implement Block B (pi/TypeScript) yourself
5. Read the companion talk slides (`../workshop-slides.html`)

## Resources

- OpenRouter: https://openrouter.ai/docs
- HN Search API: https://hn.algolia.com/api
- Workshop slides: `../workshop-slides.html`
- Main talk: `../agentic-ai-talk-v4.html`

## Credits

Workshop by **Sathya Prakash P V S** (also known as Prakash P V S S)

Companion to "Demystifying Agentic AI Engineering" talk.
