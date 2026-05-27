"""
benchmark.py — Run all optimization techniques and save results to JSON.

Usage:
    python benchmark.py              # run all techniques
    python benchmark.py --dry-run    # use pre-computed sample data (no API calls)
    python benchmark.py --save results/my_results.json

Results are saved to results/benchmark_results.json by default.
Then run: python visualize.py  to generate charts.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Pre-computed sample results for dry-run / demo purposes
SAMPLE_RESULTS = {
    "run_at": "2026-05-26T10:00:00",
    "model": "claude-sonnet-4-6",
    "techniques": [
        {
            "id": "baseline",
            "label": "Baseline\n(No Optimization)",
            "category": "api",
            "input_tokens": 5820,
            "output_tokens": 1140,
            "cost_usd": 0.02814,
            "savings_pct": 0,
            "cache_hit_pct": 0,
            "notes": "System prompt re-sent in full every request",
        },
        {
            "id": "prompt_caching",
            "label": "Prompt\nCaching",
            "category": "api",
            "input_tokens": 5820,
            "output_tokens": 1140,
            "cost_usd": 0.00801,
            "savings_pct": 71.5,
            "cache_hit_pct": 87.3,
            "notes": "cache_control on system prompt; 0.1x cost on cache reads",
        },
        {
            "id": "multi_turn_caching",
            "label": "Multi-Turn\nCaching",
            "category": "api",
            "input_tokens": 8430,
            "output_tokens": 980,
            "cost_usd": 0.00820,
            "savings_pct": 63.2,
            "cache_hit_pct": 74.1,
            "notes": "Cache conversation history checkpoint; avoids O(n²) token growth",
        },
        {
            "id": "model_routing",
            "label": "Model\nRouting",
            "category": "api",
            "input_tokens": 4200,
            "output_tokens": 890,
            "cost_usd": 0.00643,
            "savings_pct": 77.1,
            "cache_hit_pct": 0,
            "notes": "Route simple tasks to Haiku ($0.80/M vs $3.00/M)",
        },
        {
            "id": "output_budgeting",
            "label": "Output\nBudgeting",
            "category": "api",
            "input_tokens": 2100,
            "output_tokens": 310,
            "cost_usd": 0.00499,
            "savings_pct": 56.8,
            "cache_hit_pct": 0,
            "notes": "Tight max_tokens per task type; output = 5x cost of input",
        },
        {
            "id": "claude_md_optimized",
            "label": "CLAUDE.md\nOptimized",
            "category": "claude_code",
            "tokens_before": 3847,
            "tokens_after": 312,
            "savings_pct": 91.9,
            "cost_savings_monthly_usd": 6.84,
            "notes": "Remove team info, boilerplate, FAQs; keep only rules Claude acts on",
        },
        {
            "id": "claudeignore",
            "label": ".claudeignore\nAdded",
            "category": "claude_code",
            "files_before": 284,
            "files_after": 41,
            "tokens_before": 124000,
            "tokens_after": 18000,
            "savings_pct": 85.5,
            "notes": "Exclude node_modules, build artifacts, media, lock files",
        },
        {
            "id": "combined_api",
            "label": "Combined\n(API All)",
            "category": "combined",
            "savings_pct": 89.3,
            "notes": "Prompt caching + model routing + output budgeting stacked",
        },
    ],
}


def load_api_results() -> dict:
    """Run actual API benchmarks (requires ANTHROPIC_API_KEY)."""
    sys.path.insert(0, str(Path(__file__).parent / "api"))

    results = {"run_at": datetime.now().isoformat(), "model": "claude-sonnet-4-6", "techniques": []}

    print("Running API benchmarks (this will use real API tokens)...\n")

    try:
        from api.baseline import run_baseline  # type: ignore
        r = run_baseline()
        results["techniques"].append({**r, "id": "baseline", "label": "Baseline\n(No Optimization)", "category": "api"})
    except Exception as e:
        print(f"  ⚠ Baseline failed: {e}")

    try:
        from api.prompt_caching import run_prompt_caching  # type: ignore
        r = run_prompt_caching()
        results["techniques"].append({**r, "id": "prompt_caching", "label": "Prompt\nCaching", "category": "api"})
    except Exception as e:
        print(f"  ⚠ Prompt caching failed: {e}")

    try:
        from api.model_routing import run_model_routing  # type: ignore
        r = run_model_routing()
        results["techniques"].append({**r, "id": "model_routing", "label": "Model\nRouting", "category": "api"})
    except Exception as e:
        print(f"  ⚠ Model routing failed: {e}")

    try:
        from api.output_budgeting import run_output_budgeting  # type: ignore
        r = run_output_budgeting()
        results["techniques"].append({**r, "id": "output_budgeting", "label": "Output\nBudgeting", "category": "api"})
    except Exception as e:
        print(f"  ⚠ Output budgeting failed: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run token optimization benchmarks")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use pre-computed sample data (no API calls)")
    parser.add_argument("--save", default="results/benchmark_results.json",
                        help="Output JSON file path")
    args = parser.parse_args()

    os.makedirs("results", exist_ok=True)

    if args.dry_run:
        print("Dry-run mode: using pre-computed sample results\n")
        results = SAMPLE_RESULTS
    else:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY not set. Use --dry-run for demo mode.")
            sys.exit(1)
        results = load_api_results()

    output_path = args.save
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_path}")
    print("Next step: python visualize.py")


if __name__ == "__main__":
    main()
