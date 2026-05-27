"""
token_audit.py — Audit your CLAUDE.md and project files for token usage.

Usage:
    python token_audit.py                        # audit current directory
    python token_audit.py --claude-md path/to/CLAUDE.md
    python token_audit.py --compare before/ after/
    python token_audit.py --scan-dir ./myproject --top 20
"""

import argparse
import os
import sys
from pathlib import Path


def count_tokens_approx(text: str) -> int:
    """Approximate token count: ~4 chars per token (GPT/Claude heuristic)."""
    return max(1, len(text) // 4)


def token_cost(tokens: int, model: str = "sonnet") -> float:
    """Approximate cost per 1M input tokens (May 2026 pricing)."""
    rates = {
        "haiku":  0.80,
        "sonnet": 3.00,
        "opus":   15.00,
    }
    return (tokens / 1_000_000) * rates.get(model, 3.00)


def audit_file(path: str) -> dict:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="ignore")
        tokens = count_tokens_approx(text)
        return {"path": path, "tokens": tokens, "bytes": len(text.encode())}
    except Exception as e:
        return {"path": path, "tokens": 0, "bytes": 0, "error": str(e)}


def audit_claude_md(path: str) -> None:
    result = audit_file(path)
    tokens = result["tokens"]

    print(f"\n{'='*55}")
    print(f"  CLAUDE.md Token Audit")
    print(f"{'='*55}")
    print(f"  File      : {path}")
    print(f"  Tokens    : {tokens:,}")
    print(f"  Bytes     : {result['bytes']:,}")
    print()

    # Cost per session (CLAUDE.md loads every turn)
    turns_per_session = 20
    sessions_per_month = 100
    total_turns = turns_per_session * sessions_per_month
    monthly_tokens = tokens * total_turns

    print(f"  Cost projection (loaded every turn):")
    for model in ["haiku", "sonnet", "opus"]:
        monthly_cost = token_cost(monthly_tokens, model)
        print(f"    {model.capitalize():<8} {total_turns:,} turns/mo → ${monthly_cost:.2f}/mo")

    print()
    if tokens < 300:
        print("  ✓ Excellent — under 300 tokens")
    elif tokens < 500:
        print("  ✓ Good — under 500 tokens")
    elif tokens < 1000:
        print("  ⚠ Trim recommended — aim for <500 tokens")
    else:
        print("  ✗ Too large — significant savings available")
    print()


def compare_claude_mds(before_path: str, after_path: str) -> None:
    before = audit_file(before_path)
    after = audit_file(after_path)

    b_tokens = before["tokens"]
    a_tokens = after["tokens"]
    saved = b_tokens - a_tokens
    pct = (saved / b_tokens * 100) if b_tokens > 0 else 0

    turns_per_month = 2000  # 20 turns * 100 sessions
    monthly_saved = saved * turns_per_month

    print(f"\n{'='*55}")
    print(f"  CLAUDE.md Comparison")
    print(f"{'='*55}")
    print(f"  Before : {b_tokens:>6,} tokens  ({before_path})")
    print(f"  After  : {a_tokens:>6,} tokens  ({after_path})")
    print(f"  Saved  : {saved:>6,} tokens  ({pct:.1f}% reduction)")
    print()
    print(f"  Monthly savings (2,000 turns/mo):")
    for model in ["haiku", "sonnet", "opus"]:
        cost = token_cost(monthly_saved, model)
        print(f"    {model.capitalize():<8} save ${cost:.2f}/mo")
    print()


def scan_directory(root: str, top_n: int = 15, ignore_patterns: list = None) -> None:
    ignore_patterns = ignore_patterns or [
        "node_modules", ".git", "__pycache__", "dist", "build",
        ".venv", "venv", ".next", "coverage"
    ]

    results = []
    for path in Path(root).rglob("*"):
        if path.is_file():
            # Skip ignored directories
            if any(p in path.parts for p in ignore_patterns):
                continue
            # Skip binary/media files
            if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
                               ".mp4", ".pdf", ".zip", ".gz", ".bin", ".lock"}:
                continue
            result = audit_file(str(path))
            if result["tokens"] > 0:
                results.append(result)

    results.sort(key=lambda x: x["tokens"], reverse=True)
    total = sum(r["tokens"] for r in results)

    print(f"\n{'='*65}")
    print(f"  Directory Token Scan: {root}")
    print(f"{'='*65}")
    print(f"  {'File':<50} {'Tokens':>8}")
    print(f"  {'-'*50} {'-'*8}")

    for r in results[:top_n]:
        rel = os.path.relpath(r["path"], root)
        display = rel if len(rel) <= 50 else "..." + rel[-47:]
        print(f"  {display:<50} {r['tokens']:>8,}")

    print(f"  {'-'*50} {'-'*8}")
    print(f"  {'TOTAL (all files)':<50} {total:>8,}")
    print()
    print(f"  Top {top_n} shown of {len(results)} files")
    print(f"  Tip: Add high-token noise files to .claudeignore")
    print()


def main():
    parser = argparse.ArgumentParser(description="Audit Claude Code token usage")
    parser.add_argument("--claude-md", help="Path to CLAUDE.md to audit")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"),
                        help="Compare two CLAUDE.md files")
    parser.add_argument("--scan-dir", help="Scan directory for token usage")
    parser.add_argument("--top", type=int, default=15,
                        help="Show top N files in scan (default: 15)")
    args = parser.parse_args()

    if args.compare:
        compare_claude_mds(args.compare[0], args.compare[1])
    elif args.claude_md:
        audit_claude_md(args.claude_md)
    elif args.scan_dir:
        scan_directory(args.scan_dir, args.top)
    else:
        # Default: look for CLAUDE.md in current directory
        default = "CLAUDE.md"
        if os.path.exists(default):
            audit_claude_md(default)
        else:
            print("No CLAUDE.md found. Use --claude-md, --compare, or --scan-dir")
            parser.print_help()
            sys.exit(1)


if __name__ == "__main__":
    main()
