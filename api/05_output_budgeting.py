"""
05_output_budgeting.py — Cap output tokens per task type.

Output tokens cost 5x more than input (Sonnet: $15/M vs $3/M).
Most tasks don't need 4K tokens of output. Setting explicit budgets
prevents runaway responses and cuts the most expensive line item.

Common budgets by task type:
  - Classification / extraction  : 50-100 tokens
  - Short answers / Q&A          : 256-512 tokens
  - Code snippets                : 512-1024 tokens
  - Full implementations         : 2048 tokens
  - Long-form writing            : 4096 tokens (default max)

Savings: 30-60% on output costs for typical workloads.

Run: python 05_output_budgeting.py
"""

import anthropic
import time

client = anthropic.Anthropic()

# Each task run twice: once with default max_tokens=4096, once with tight budget
TASKS = [
    {
        "prompt": "Is this sentiment positive or negative? 'The product exceeded my expectations.'",
        "type": "classification",
        "tight_budget": 20,
    },
    {
        "prompt": "What is the time complexity of binary search? Answer in one sentence.",
        "type": "short_qa",
        "tight_budget": 80,
    },
    {
        "prompt": "Write a Python function to check if a string is a palindrome.",
        "type": "code_snippet",
        "tight_budget": 300,
    },
    {
        "prompt": "Summarize the key difference between REST and GraphQL in 2-3 sentences.",
        "type": "summarization",
        "tight_budget": 120,
    },
]

MODEL = "claude-sonnet-4-6"
OUTPUT_RATE = 15.00  # $/M tokens


def compute_output_cost(tokens: int) -> float:
    return tokens * OUTPUT_RATE / 1_000_000


def run_output_budgeting():
    print("=" * 60)
    print("  Technique 4: Output Token Budgeting")
    print("=" * 60)
    print(f"  {'Task Type':<20} {'Budget':>8} {'Used':>8} {'Cost':>10} {'Saved':>10}")
    print(f"  {'─'*20} {'─'*8} {'─'*8} {'─'*10} {'─'*10}")

    total_baseline_cost = 0
    total_optimized_cost = 0

    for task in TASKS:
        # Baseline: no constraint (4096)
        r_baseline = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            messages=[{"role": "user", "content": task["prompt"]}],
        )
        baseline_output = r_baseline.usage.output_tokens
        baseline_cost = compute_output_cost(baseline_output)

        # Optimized: tight budget
        r_optimized = client.messages.create(
            model=MODEL,
            max_tokens=task["tight_budget"],
            messages=[{"role": "user", "content": task["prompt"]}],
        )
        optimized_output = r_optimized.usage.output_tokens
        optimized_cost = compute_output_cost(optimized_output)

        saved = baseline_cost - optimized_cost
        total_baseline_cost += baseline_cost
        total_optimized_cost += optimized_cost

        print(f"  {task['type']:<20} {task['tight_budget']:>8} {optimized_output:>8} "
              f"  ${optimized_cost:.5f}   -${saved:.5f}")

    total_saved = total_baseline_cost - total_optimized_cost
    savings_pct = (total_saved / total_baseline_cost * 100) if total_baseline_cost > 0 else 0

    print(f"\n  {'─'*60}")
    print(f"  Baseline output cost  : ${total_baseline_cost:.4f}")
    print(f"  Budgeted output cost  : ${total_optimized_cost:.4f}")
    print(f"  Savings               : ${total_saved:.4f}  ({savings_pct:.1f}%)")
    print()
    print("  Tip: Output tokens cost 5x more than input.")
    print("  A tight budget is the fastest single-line win.")
    print()

    return {
        "technique": "output_budgeting",
        "baseline_cost": total_baseline_cost,
        "optimized_cost": total_optimized_cost,
        "savings_pct": savings_pct,
    }


if __name__ == "__main__":
    run_output_budgeting()
