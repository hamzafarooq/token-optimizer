---
name: token-optimizer
description: Audit and reduce Claude API and Claude Code token usage. Covers CLAUDE.md bloat, .claudeignore setup, model routing (Haiku for simple tasks), prompt caching, and output budgeting. Use when user asks to reduce token costs, audit CLAUDE.md size, optimize Claude API usage, or mentions "token optimizer".
---

# Token Optimizer

Reference repo: `/Github/token-optimizer` — benchmarks, before/after examples, and runnable scripts.

## Workflows

### 1. Audit CLAUDE.md

Run the built-in auditor:

```bash
cd /Github/token-optimizer
conda activate token-optimizer
python claude_code/token_audit.py --claude-md /path/to/CLAUDE.md
```

Or audit the current directory's CLAUDE.md:

```bash
python claude_code/token_audit.py
```

**Target thresholds:**
- < 300 tokens — excellent
- 300–500 tokens — good
- 500–1000 tokens — trim recommended
- 1000+ tokens — significant savings available (aim for 90%+ reduction)

**Optimization rules for CLAUDE.md:**
- Remove prose explanations — use bullet points
- No examples in CLAUDE.md — examples belong in separate files
- Remove anything derivable from the code (file structure, patterns)
- No history, rationale, or "why" commentary — just rules Claude acts on
- Merge related items; cut redundant reminders

See `claude_code/before/CLAUDE.md` (3,847 tokens) vs `claude_code/after/CLAUDE.md` (312 tokens) for a concrete example.

---

### 2. Scan directory for token-heavy files

```bash
python claude_code/token_audit.py --scan-dir ./myproject --top 20
```

Everything in the top list that isn't directly needed for coding tasks is a `.claudeignore` candidate.

**Add `.claudeignore` to the project root** — copy from `claude_code/claudeignore.example`. Common wins:
- `node_modules/`, `.venv/`, `__pycache__/`
- `dist/`, `build/`, `.next/`
- `*.lock`, `package-lock.json`
- `*.csv`, `data/`, `fixtures/large/`
- `*.png`, `*.jpg`, `*.pdf`
- `coverage/`, `**/__snapshots__/`

---

### 3. API: Prompt caching

Add `cache_control` breakpoints to expensive static content. Order matters — cache the longest-lived content first.

```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[
        {"type": "text", "text": static_system_prompt,
         "cache_control": {"type": "ephemeral"}},
    ],
    messages=[...]
)
```

See `api/02_prompt_caching.py` and `api/03_multi_turn_caching.py`. Saves 71% on system prompts, 63% on multi-turn conversations.

---

### 4. API: Model routing

Route to Haiku for simple tasks, Sonnet/Opus only when needed.

```python
ROUTER_SYSTEM = """Classify the task. Respond with ONLY: haiku / sonnet / opus
- haiku: classify, extract, lookup, short summarize, yes/no
- sonnet: code generation, reasoning, long-form writing
- opus: deep analysis, multi-step reasoning"""

def route(prompt):
    model = classify_task(prompt)  # Haiku call, ~$0.001
    return call_model(model, prompt)
```

See `api/04_model_routing.py`. Saves 77% on tasks routable to Haiku.

---

### 5. API: Output budgeting

Cap `max_tokens` per task type — most responses use far fewer tokens than the default ceiling.

```python
TOKEN_BUDGETS = {
    "classification": 10,
    "extraction": 150,
    "summarization": 250,
    "code": 800,
    "analysis": 500,
}
response = client.messages.create(max_tokens=TOKEN_BUDGETS[task_type], ...)
```

See `api/05_output_budgeting.py`. Saves 57% on output tokens.

---

### 6. Run full benchmark

```bash
cd /Github/token-optimizer
conda activate token-optimizer

# Dry-run (no API key needed)
python benchmark.py --dry-run

# Live run (~$0.10)
python benchmark.py

# Dashboard
python visualize.py
open dashboard/index.html
```

---

## Combined savings reference

| Technique | Savings |
|---|---|
| Optimized CLAUDE.md | 91.9% |
| .claudeignore | 85.5% |
| Model routing (Haiku) | 77.1% |
| System prompt caching | 71.5% |
| Multi-turn caching | 63.2% |
| Output budgeting | 56.8% |
| **All API techniques** | **89.3%** |
