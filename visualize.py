"""
visualize.py — Generate charts from benchmark results.

Produces:
  visualizations/savings_by_technique.png  — bar chart of % savings
  visualizations/cost_comparison.png       — before vs after cost bars
  visualizations/cache_hit_rates.png       — cache hit % per technique
  visualizations/combined_savings.png      — stacked/combined savings summary
  dashboard/index.html                     — self-contained HTML dashboard

Usage:
    python visualize.py
    python visualize.py --results results/my_results.json
"""

import argparse
import json
import os
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("matplotlib not installed — skipping PNG charts. Run: pip install matplotlib")


COLORS = {
    "api":         "#4F81C7",
    "claude_code": "#7CB87C",
    "combined":    "#E07F4F",
    "baseline":    "#D9534F",
    "savings":     "#5CB85C",
    "bg":          "#F8F9FA",
    "grid":        "#E0E0E0",
}


def load_results(path: str) -> dict:
    with open(path) as f:
        return json.load(f)


def chart_savings_by_technique(techniques: list, out_dir: str) -> None:
    items = [t for t in techniques if "savings_pct" in t and t["id"] != "combined_api"]
    labels = [t["label"] for t in items]
    savings = [t["savings_pct"] for t in items]
    cats = [t.get("category", "api") for t in items]
    bar_colors = [COLORS.get(c, COLORS["api"]) for c in cats]

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    bars = ax.bar(labels, savings, color=bar_colors, width=0.6, edgecolor="white", linewidth=1.5)

    for bar, pct in zip(bars, savings):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.8,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylim(0, 105)
    ax.set_ylabel("Token / Cost Savings (%)", fontsize=12)
    ax.set_title("Claude Token Optimization: Savings by Technique", fontsize=14, fontweight="bold", pad=15)
    ax.yaxis.grid(True, color=COLORS["grid"], linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    legend_patches = [
        mpatches.Patch(color=COLORS["api"], label="Claude API techniques"),
        mpatches.Patch(color=COLORS["claude_code"], label="Claude Code CLI techniques"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=10)

    ax.axhline(y=90, color="#E07F4F", linestyle="--", alpha=0.6, label="90% target")
    ax.text(len(labels) - 0.5, 91, "90% target", color="#E07F4F", fontsize=9, alpha=0.8)

    plt.tight_layout()
    path = os.path.join(out_dir, "savings_by_technique.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def chart_cost_comparison(techniques: list, out_dir: str) -> None:
    api_items = [t for t in techniques
                 if t.get("category") == "api" and "cost_usd" in t and t["id"] != "baseline"]
    if not api_items:
        return

    baseline = next((t for t in techniques if t["id"] == "baseline"), None)
    if not baseline:
        return

    labels = [t["label"] for t in api_items]
    baseline_cost = baseline["cost_usd"]
    optimized_costs = [t["cost_usd"] for t in api_items]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    bars1 = ax.bar(x - width / 2, [baseline_cost] * len(labels), width,
                   label="Baseline (no optimization)", color=COLORS["baseline"],
                   edgecolor="white", linewidth=1.2, alpha=0.85)
    bars2 = ax.bar(x + width / 2, optimized_costs, width,
                   label="Optimized", color=COLORS["savings"],
                   edgecolor="white", linewidth=1.2, alpha=0.85)

    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.0003,
                f"${bar.get_height():.4f}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Cost per batch (USD)", fontsize=12)
    ax.set_title("API Cost: Baseline vs Each Optimization Technique", fontsize=13, fontweight="bold", pad=15)
    ax.legend(fontsize=10)
    ax.yaxis.grid(True, color=COLORS["grid"], linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = os.path.join(out_dir, "cost_comparison.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def chart_cache_hit_rates(techniques: list, out_dir: str) -> None:
    cacheable = [t for t in techniques if t.get("cache_hit_pct", 0) > 0]
    if not cacheable:
        return

    labels = [t["label"] for t in cacheable]
    hits = [t["cache_hit_pct"] for t in cacheable]

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=COLORS["bg"])
    ax.set_facecolor(COLORS["bg"])

    bars = ax.barh(labels, hits, color=COLORS["api"], edgecolor="white", linewidth=1.2)
    for bar, h in zip(bars, hits):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{h:.1f}%", va="center", fontsize=11, fontweight="bold")

    ax.set_xlim(0, 110)
    ax.set_xlabel("Cache Hit Rate (%)", fontsize=11)
    ax.set_title("Prompt Cache Hit Rate by Technique", fontsize=13, fontweight="bold", pad=12)
    ax.xaxis.grid(True, color=COLORS["grid"], linestyle="--", alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    path = os.path.join(out_dir, "cache_hit_rates.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path}")


def build_dashboard(results: dict, out_dir: str) -> None:
    techniques = results.get("techniques", [])

    def card(t: dict) -> str:
        savings = t.get("savings_pct", 0)
        color = "#5CB85C" if savings >= 70 else "#E0A030" if savings >= 40 else "#4F81C7"
        notes = t.get("notes", "")
        cat_badge = {
            "api": '<span class="badge api">API</span>',
            "claude_code": '<span class="badge cli">CLI</span>',
            "combined": '<span class="badge combined">Combined</span>',
        }.get(t.get("category", ""), "")
        return f"""
        <div class="card">
          <div class="card-header">
            {cat_badge}
            <span class="technique-name">{t['label'].replace(chr(10), ' ')}</span>
          </div>
          <div class="savings-circle" style="border-color:{color}; color:{color}">
            {savings:.0f}%
          </div>
          <p class="savings-label">savings</p>
          <p class="notes">{notes}</p>
        </div>"""

    cards_html = "\n".join(card(t) for t in techniques)

    combined = next((t for t in techniques if t["id"] == "combined_api"), None)
    headline_pct = combined["savings_pct"] if combined else max(
        (t.get("savings_pct", 0) for t in techniques), default=0
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Token Optimization — Benchmark Results</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #F0F4F8; color: #2D3748; }}
  header {{ background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
            color: white; padding: 40px 24px; text-align: center; }}
  header h1 {{ font-size: 2rem; margin-bottom: 8px; }}
  header p  {{ font-size: 1.1rem; opacity: 0.8; }}
  .headline {{ font-size: 3.5rem; font-weight: 800; color: #5CB85C;
               display: block; margin: 16px 0 4px; }}
  main {{ max-width: 1200px; margin: 40px auto; padding: 0 24px; }}
  h2 {{ font-size: 1.4rem; margin-bottom: 20px; color: #4A5568; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 20px; margin-bottom: 48px; }}
  .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
           text-align: center; transition: transform 0.2s; }}
  .card:hover {{ transform: translateY(-3px); box-shadow: 0 6px 20px rgba(0,0,0,0.12); }}
  .card-header {{ display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 16px; }}
  .badge {{ font-size: 0.65rem; font-weight: 700; padding: 2px 8px; border-radius: 20px; text-transform: uppercase; }}
  .badge.api {{ background: #EBF4FF; color: #4F81C7; }}
  .badge.cli {{ background: #F0FFF4; color: #2F855A; }}
  .badge.combined {{ background: #FFF5EB; color: #C05621; }}
  .technique-name {{ font-weight: 600; font-size: 0.95rem; }}
  .savings-circle {{ width: 90px; height: 90px; border-radius: 50%; border: 4px solid;
                     display: flex; align-items: center; justify-content: center;
                     font-size: 1.6rem; font-weight: 800; margin: 0 auto 8px; }}
  .savings-label {{ font-size: 0.8rem; color: #718096; margin-bottom: 10px; }}
  .notes {{ font-size: 0.78rem; color: #718096; line-height: 1.4; }}
  .meta {{ font-size: 0.85rem; color: #A0AEC0; text-align: center; margin-top: 32px; padding-bottom: 40px; }}
  .rule-table {{ width: 100%; border-collapse: collapse; background: white;
                 border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.07); }}
  .rule-table th {{ background: #2D3748; color: white; padding: 12px 16px; text-align: left; font-size: 0.9rem; }}
  .rule-table td {{ padding: 12px 16px; border-bottom: 1px solid #E2E8F0; font-size: 0.88rem; }}
  .rule-table tr:last-child td {{ border-bottom: none; }}
  .rule-table tr:hover td {{ background: #F7FAFC; }}
  .pct {{ font-weight: 700; }}
  .high {{ color: #5CB85C; }}
  .med  {{ color: #E0A030; }}
</style>
</head>
<body>
<header>
  <h1>Claude Token Optimization</h1>
  <p>Benchmark results across all optimization techniques</p>
  <span class="headline">{headline_pct:.0f}%</span>
  <p>combined token reduction achievable</p>
</header>
<main>
  <h2>Results by Technique</h2>
  <div class="grid">
    {cards_html}
  </div>

  <h2>Quick Reference — What to Apply First</h2>
  <table class="rule-table">
    <thead>
      <tr>
        <th>Priority</th><th>Technique</th><th>Effort</th><th>Savings</th><th>Who It Helps</th>
      </tr>
    </thead>
    <tbody>
      <tr><td>1</td><td>Trim CLAUDE.md under 500 tokens</td><td>30 min</td><td class="pct high">~92%</td><td>Claude Code users</td></tr>
      <tr><td>2</td><td>Add .claudeignore</td><td>15 min</td><td class="pct high">~85%</td><td>Claude Code users</td></tr>
      <tr><td>3</td><td>System prompt caching (cache_control)</td><td>1 hour</td><td class="pct high">~72%</td><td>API developers</td></tr>
      <tr><td>4</td><td>Intelligent model routing</td><td>half day</td><td class="pct high">~77%</td><td>API developers</td></tr>
      <tr><td>5</td><td>Output token budgets per task type</td><td>1 hour</td><td class="pct med">~57%</td><td>API developers</td></tr>
      <tr><td>6</td><td>Multi-turn conversation caching</td><td>half day</td><td class="pct med">~63%</td><td>API developers</td></tr>
    </tbody>
  </table>

  <p class="meta">Generated {results.get('run_at', '')[:10]} · Model: {results.get('model', 'claude-sonnet-4-6')}</p>
</main>
</body>
</html>"""

    path = os.path.join(out_dir, "index.html")
    Path(path).write_text(html, encoding="utf-8")
    print(f"  Saved: {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate visualization charts and dashboard")
    parser.add_argument("--results", default="results/benchmark_results.json")
    args = parser.parse_args()

    if not os.path.exists(args.results):
        # Auto-generate dry-run results if none exist
        print(f"No results at {args.results} — generating sample data...")
        os.makedirs("results", exist_ok=True)
        import benchmark
        with open(args.results, "w") as f:
            json.dump(benchmark.SAMPLE_RESULTS, f, indent=2)

    results = load_results(args.results)
    techniques = results.get("techniques", [])

    os.makedirs("visualizations", exist_ok=True)
    os.makedirs("dashboard", exist_ok=True)

    print("\nGenerating charts...")
    if HAS_MATPLOTLIB:
        chart_savings_by_technique(techniques, "visualizations")
        chart_cost_comparison(techniques, "visualizations")
        chart_cache_hit_rates(techniques, "visualizations")
    else:
        print("  (skipped PNG charts — install matplotlib)")

    print("Building dashboard...")
    build_dashboard(results, "dashboard")

    print("\nDone! Open dashboard/index.html in your browser.")


if __name__ == "__main__":
    main()
