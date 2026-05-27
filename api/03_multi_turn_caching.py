"""
03_multi_turn_caching.py — Cache growing conversation history.

Problem: In a multi-turn chat, each new message re-sends the entire history.
With 10 turns, turn 10 re-sends turns 1-9 in full — O(n²) token growth.

Solution: Place a cache_control checkpoint at the end of the conversation
history (before the new user message). Claude caches everything up to that
point, so only the new message is charged at full price.

Savings: 60-80% on long conversations.

Run: python 03_multi_turn_caching.py
"""

import anthropic
import time

client = anthropic.Anthropic()

SYSTEM = "You are a concise technical assistant. Answer in 2-3 sentences."

# Simulate a growing conversation (as would happen in a real chat session)
CONVERSATION_TURNS = [
    "What is a database index?",
    "What types of indexes exist in PostgreSQL?",
    "When should I use a partial index?",
    "How do I check if my queries are using indexes?",
    "What is index bloat and how do I fix it?",
]


def run_without_history_caching():
    """Standard approach: full history re-sent every turn."""
    messages = []
    total_input = 0
    total_output = 0
    start_all = time.time()

    print("  Without history caching:")
    for i, question in enumerate(CONVERSATION_TURNS, 1):
        messages.append({"role": "user", "content": question})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=SYSTEM,
            messages=messages,
        )

        answer = response.content[0].text
        messages.append({"role": "assistant", "content": answer})

        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        print(f"    Turn {i}: {response.usage.input_tokens:,} input tokens")

    cost = (total_input * 3.00 + total_output * 15.00) / 1_000_000
    print(f"    Total input: {total_input:,} | Cost: ${cost:.4f} | Time: {time.time()-start_all:.1f}s\n")
    return total_input, total_output, cost


def run_with_history_caching():
    """Optimized: cache the conversation history checkpoint before each new turn."""
    messages = []
    total_input = 0
    total_output = 0
    total_cache_read = 0
    start_all = time.time()

    print("  With history caching (cache_control on last assistant turn):")
    for i, question in enumerate(CONVERSATION_TURNS, 1):
        # Mark the last assistant message for caching before adding new user message
        if messages and messages[-1]["role"] == "assistant":
            last_assistant = messages[-1]
            if isinstance(last_assistant["content"], str):
                messages[-1] = {
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": last_assistant["content"],
                            "cache_control": {"type": "ephemeral"},
                        }
                    ],
                }

        messages.append({"role": "user", "content": question})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=SYSTEM,
            messages=messages,
        )

        answer = response.content[0].text
        # Store as plain string (cache_control applied on next iteration)
        messages.append({"role": "assistant", "content": answer})

        cache_read = getattr(response.usage, "cache_read_input_tokens", 0)
        total_input += response.usage.input_tokens
        total_output += response.usage.output_tokens
        total_cache_read += cache_read
        print(f"    Turn {i}: {response.usage.input_tokens:,} input ({cache_read:,} cached ✓)")

    cost = (
        (total_input - total_cache_read) * 3.00
        + total_cache_read * 3.00 * 0.10
        + total_output * 15.00
    ) / 1_000_000
    print(f"    Total input: {total_input:,} | Cache reads: {total_cache_read:,} | Cost: ${cost:.4f} | Time: {time.time()-start_all:.1f}s\n")
    return total_input, total_output, total_cache_read, cost


def run_multi_turn_comparison():
    print("=" * 60)
    print("  Technique 2: Multi-Turn Conversation Caching")
    print("=" * 60)
    print(f"  {len(CONVERSATION_TURNS)}-turn conversation about PostgreSQL indexing")
    print()

    b_input, b_output, b_cost = run_without_history_caching()
    c_input, c_output, c_cache_read, c_cost = run_with_history_caching()

    savings_pct = ((b_cost - c_cost) / b_cost * 100) if b_cost > 0 else 0
    print(f"  {'─'*50}")
    print(f"  Without caching cost : ${b_cost:.4f}")
    print(f"  With caching cost    : ${c_cost:.4f}")
    print(f"  Savings              : {savings_pct:.1f}%")
    print()
    print("  Note: savings grow with conversation length (O(n²) avoided)")
    print()

    return {
        "technique": "multi_turn_caching",
        "baseline_cost": b_cost,
        "optimized_cost": c_cost,
        "savings_pct": savings_pct,
        "cache_read_tokens": c_cache_read,
    }


if __name__ == "__main__":
    run_multi_turn_comparison()
