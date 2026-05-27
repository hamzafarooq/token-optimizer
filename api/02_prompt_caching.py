"""
02_prompt_caching.py — System prompt caching with cache_control breakpoints.

Key insight: Cache reads cost 10% of standard input price.
The system prompt (same across all requests) only needs to be processed once.

Savings formula:
  - First request: 1.25x write cost (worth it after just 2 reads)
  - Subsequent requests: 0.1x read cost = 90% savings on system prompt tokens

Requirements:
  - Minimum 1,024 tokens for Sonnet to cache (system prompt qualifies)
  - Same prefix bytes must be sent (no dynamic injection into system prompt)
  - Cache TTL: 5 minutes by default

Run: python 02_prompt_caching.py
"""

import anthropic
import time

client = anthropic.Anthropic()

# Same large system prompt — but now with cache_control
SYSTEM_PROMPT_CACHED = """
You are an expert AI assistant for a software development team. You help developers
write clean, maintainable code following best practices. You are knowledgeable about
Python, JavaScript, TypeScript, React, Node.js, PostgreSQL, Redis, AWS, Docker, and
Kubernetes. You follow SOLID principles, write comprehensive tests, and always consider
security and performance implications. You provide thorough explanations and examples.

## Code Standards
- Python: PEP 8, type hints, docstrings for all public functions
- JavaScript/TypeScript: ESLint, Prettier, strict TypeScript
- Always write unit tests with pytest or Jest
- Use meaningful variable names; avoid abbreviations
- Handle errors explicitly; never swallow exceptions
- Log errors with context, never log sensitive data
- Use environment variables for configuration
- Validate all inputs at system boundaries

## Security Requirements
- Parameterized queries only — no string interpolation in SQL
- Sanitize HTML output to prevent XSS
- Validate file uploads: type, size, content
- Rate limit all public endpoints
- Use HTTPS everywhere; reject plain HTTP
- Store passwords with bcrypt (min 12 rounds)
- JWT expiry: 1 hour access, 7 day refresh
- Rotate secrets on suspected compromise

## Architecture Principles
- Single responsibility principle: one reason to change
- Dependency injection over global state
- Repository pattern for data access
- Service layer for business logic
- Controller layer for HTTP concerns only
- Event-driven for async workflows
- Circuit breakers for external service calls
- Graceful degradation when dependencies fail

## Testing Standards
- Unit tests: mock all external dependencies
- Integration tests: real database, mock external APIs
- E2E tests: full stack, real services
- Minimum 80% code coverage
- Test file naming: test_<module>.py or <module>.test.ts
- Arrange-Act-Assert pattern
- One assertion per test (prefer)
- Never skip tests in CI

## Database Guidelines
- Migrations only — never ALTER in production console
- Always add indexes for FK columns and filter columns
- Use connection pooling (PgBouncer or similar)
- Soft deletes with deleted_at timestamp
- Audit columns: created_at, updated_at, created_by
- Transactions for multi-table writes
- Explain analyze before shipping complex queries
- Row-level security for multi-tenant data

## Deployment & Operations
- 12-factor app principles
- Health check endpoints: /health and /ready
- Structured JSON logging
- Distributed tracing with OpenTelemetry
- SLO-based alerting (not just raw metrics)
- Runbooks for all PagerDuty alerts
- Blue-green deployments; never in-place
- Rollback plan required before any deploy

## API Design
- RESTful with OpenAPI 3.0 spec
- Versioning via URL prefix: /v1/, /v2/
- Consistent error format: {error, code, details}
- Pagination on all list endpoints
- Idempotency keys for mutations
- HATEOAS links for discoverability
- 429 with Retry-After on rate limit
- Request IDs in all responses
""".strip()

QUESTIONS = [
    "How do I write a Python function to parse a CSV file safely?",
    "What's the best way to handle database connection pooling?",
    "How should I structure error handling in my Express API?",
]


def run_prompt_caching():
    total_input = 0
    total_output = 0
    total_cache_write = 0
    total_cache_read = 0
    total_time = 0

    print("=" * 55)
    print("  Technique 1: System Prompt Caching")
    print("=" * 55)
    print("  cache_control added to system prompt block")
    print("  First request writes cache; subsequent reads hit it")
    print()

    for i, question in enumerate(QUESTIONS, 1):
        start = time.time()

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT_CACHED,
                    "cache_control": {"type": "ephemeral"},  # <-- THE KEY CHANGE
                }
            ],
            messages=[{"role": "user", "content": question}],
        )

        elapsed = time.time() - start
        usage = response.usage

        cache_write = getattr(usage, "cache_creation_input_tokens", 0)
        cache_read = getattr(usage, "cache_read_input_tokens", 0)
        uncached = usage.input_tokens - cache_read

        total_input += usage.input_tokens
        total_output += usage.output_tokens
        total_cache_write += cache_write
        total_cache_read += cache_read
        total_time += elapsed

        print(f"  Request {i}: {question[:50]}...")
        print(f"    Input tokens  : {usage.input_tokens:,} total")
        print(f"      Cache write : {cache_write:,}  (1.25x cost)")
        print(f"      Cache read  : {cache_read:,}  (0.1x cost ✓)")
        print(f"      Uncached    : {uncached:,}  (1x cost)")
        print(f"    Output tokens : {usage.output_tokens:,}")
        print(f"    Latency       : {elapsed:.2f}s")

    # Cost calculation: cached reads cost 0.1x, writes cost 1.25x
    # Uncached tokens = total_input - total_cache_read - total_cache_write
    uncached_input = total_input - total_cache_read - total_cache_write
    cost = (
        (uncached_input * 3.00)
        + (total_cache_write * 3.00 * 1.25)
        + (total_cache_read * 3.00 * 0.10)
        + (total_output * 15.00)
    ) / 1_000_000

    baseline_cost = (total_input * 3.00 + total_output * 15.00) / 1_000_000
    savings_pct = ((baseline_cost - cost) / baseline_cost * 100) if baseline_cost > 0 else 0

    print(f"\n  {'─'*45}")
    print(f"  Total input tokens : {total_input:,}")
    print(f"  Cache writes       : {total_cache_write:,}")
    print(f"  Cache reads        : {total_cache_read:,}")
    print(f"  Cache hit rate     : {total_cache_read / max(total_input, 1) * 100:.1f}%")
    print(f"  Total time         : {total_time:.2f}s")
    print(f"  Estimated cost     : ${cost:.4f}")
    print(f"  vs baseline cost   : ${baseline_cost:.4f}")
    print(f"  Savings            : {savings_pct:.1f}%")
    print()
    print("  Rule of thumb: savings compound — more requests = higher hit rate")
    print()

    return {
        "technique": "prompt_caching",
        "input_tokens": total_input,
        "cache_read_tokens": total_cache_read,
        "cache_write_tokens": total_cache_write,
        "output_tokens": total_output,
        "cost_usd": cost,
        "time_s": total_time,
        "cache_hit_rate_pct": total_cache_read / max(total_input, 1) * 100,
        "savings_vs_baseline_pct": savings_pct,
    }


if __name__ == "__main__":
    result = run_prompt_caching()
