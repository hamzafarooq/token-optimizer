"""
04_model_routing.py — Route tasks to cheaper models based on complexity.

Key insight: Not every task needs Sonnet or Opus.
- Simple tasks (classify, extract, summarize short text): Haiku ($0.80/M input)
- Complex tasks (code generation, reasoning, long-form): Sonnet ($3.00/M input)
- Research/analysis tasks: Opus ($15.00/M input)

Savings: 70-90% on simple tasks routed to Haiku.

Strategy: Use a fast classifier (Haiku itself) to route, then call the right model.

Run: python 04_model_routing.py
"""

import anthropic
import time

client = anthropic.Anthropic()

PRICING = {
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00, "name": "Haiku"},
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "name": "Sonnet"},
    "claude-opus-4-7": {"input": 15.00, "output": 75.00, "name": "Opus"},
}

# Mix of simple and complex tasks
TASKS = [
    {"prompt": "Classify this as positive/negative: 'The API is fast and reliable.'",
     "expected_model": "haiku", "type": "classification"},
    {"prompt": "Extract all email addresses from: 'Contact us at support@example.com or sales@example.com'",
     "expected_model": "haiku", "type": "extraction"},
    {"prompt": "What is the capital of France?",
     "expected_model": "haiku", "type": "simple_qa"},
    {"prompt": "Write a Python async context manager that retries failed HTTP requests with exponential backoff, handles rate limiting (429), and supports custom retry predicates.",
     "expected_model": "sonnet", "type": "code_generation"},
    {"prompt": "Explain the CAP theorem and its implications for distributed database design, with concrete examples of how MongoDB, Cassandra, and DynamoDB make different tradeoffs.",
     "expected_model": "sonnet", "type": "technical_explanation"},
    {"prompt": "Summarize in one sentence: 'Paris is the capital of France.'",
     "expected_model": "haiku", "type": "summarization"},
]

ROUTER_SYSTEM = """Classify the complexity of the following task. Respond with ONLY one word:
- "haiku" — simple tasks: classify, extract, lookup, short summarize, yes/no
- "sonnet" — complex tasks: code generation, reasoning, long-form writing, analysis
- "opus" — research tasks: deep analysis, multi-step reasoning, creative writing"""


def classify_task(prompt: str) -> str:
    """Use Haiku to route tasks — fast and cheap."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=10,
        system=ROUTER_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    label = response.content[0].text.strip().lower()
    if "haiku" in label:
        return "claude-haiku-4-5-20251001"
    elif "opus" in label:
        return "claude-opus-4-7"
    return "claude-sonnet-4-6"


def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, PRICING["claude-sonnet-4-6"])
    return (input_tokens * p["input"] + output_tokens * p["output"]) / 1_000_000


def run_without_routing():
    """All tasks on Sonnet — typical default."""
    total_cost = 0
    print("  Without routing (all Sonnet):")
    for task in TASKS:
        r = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": task["prompt"]}],
        )
        cost = compute_cost("claude-sonnet-4-6", r.usage.input_tokens, r.usage.output_tokens)
        total_cost += cost
        print(f"    [{task['type']:<22}] Sonnet  ${cost:.5f}")
    print(f"    Total: ${total_cost:.4f}\n")
    return total_cost


def run_with_routing():
    """Route each task to the appropriate model."""
    total_cost = 0
    routing_cost = 0
    print("  With intelligent routing:")
    for task in TASKS:
        # Step 1: classify (Haiku, very cheap)
        routed_model = classify_task(task["prompt"])
        routing_cost += compute_cost("claude-haiku-4-5-20251001", 50, 5)  # approx classifier cost

        # Step 2: run on routed model
        r = client.messages.create(
            model=routed_model,
            max_tokens=512,
            messages=[{"role": "user", "content": task["prompt"]}],
        )
        task_cost = compute_cost(routed_model, r.usage.input_tokens, r.usage.output_tokens)
        total_cost += task_cost
        model_name = PRICING[routed_model]["name"]
        marker = "✓" if model_name.lower() == task["expected_model"] else "≈"
        print(f"    [{task['type']:<22}] {model_name:<7} ${task_cost:.5f} {marker}")

    total_with_routing = total_cost + routing_cost
    print(f"    Routing overhead: ${routing_cost:.5f}")
    print(f"    Total: ${total_with_routing:.4f}\n")
    return total_with_routing


def run_model_routing():
    print("=" * 60)
    print("  Technique 3: Intelligent Model Routing")
    print("=" * 60)
    print(f"  {len(TASKS)} tasks — mix of simple and complex")
    print()

    baseline_cost = run_without_routing()
    optimized_cost = run_with_routing()

    savings_pct = ((baseline_cost - optimized_cost) / baseline_cost * 100) if baseline_cost > 0 else 0
    print(f"  {'─'*50}")
    print(f"  All-Sonnet cost   : ${baseline_cost:.4f}")
    print(f"  Routed cost       : ${optimized_cost:.4f}")
    print(f"  Savings           : {savings_pct:.1f}%")
    print()
    print("  At scale: simple tasks are often 60-70% of volume")
    print("  Routing them to Haiku = 73% cost reduction on that slice")
    print()

    return {
        "technique": "model_routing",
        "baseline_cost": baseline_cost,
        "optimized_cost": optimized_cost,
        "savings_pct": savings_pct,
    }


if __name__ == "__main__":
    run_model_routing()
