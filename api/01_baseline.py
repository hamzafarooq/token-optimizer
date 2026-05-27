"""
01_baseline.py — No optimizations. This is what most people start with.

Shows the true cost of an unoptimized Claude API call:
- Large system prompt sent in full every request
- No caching
- Full model (Sonnet) for every task regardless of complexity
- No output token limits

Run: python 01_baseline.py
"""

import anthropic
import time

client = anthropic.Anthropic()

# Simulates a real-world large system prompt (1,800+ tokens)
SYSTEM_PROMPT = """
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


def run_baseline():
    total_input = 0
    total_output = 0
    total_time = 0

    print("=" * 55)
    print("  Baseline — No Optimizations")
    print("=" * 55)

    for i, question in enumerate(QUESTIONS, 1):
        start = time.time()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": question}],
        )
        elapsed = time.time() - start

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_input += input_tokens
        total_output += output_tokens
        total_time += elapsed

        print(f"\n  Request {i}: {question[:50]}...")
        print(f"    Input tokens  : {input_tokens:,}")
        print(f"    Output tokens : {output_tokens:,}")
        print(f"    Latency       : {elapsed:.2f}s")
        print(f"    Cache hit     : None (no caching configured)")

    cost = (total_input * 3.00 + total_output * 15.00) / 1_000_000
    print(f"\n  {'─'*45}")
    print(f"  Total input tokens : {total_input:,}")
    print(f"  Total output tokens: {total_output:,}")
    print(f"  Total time         : {total_time:.2f}s")
    print(f"  Estimated cost     : ${cost:.4f}")
    print(f"  Cache savings      : $0.00 (0%)")
    print()

    return {
        "technique": "baseline",
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cost_usd": cost,
        "time_s": total_time,
        "cache_savings_pct": 0,
    }


if __name__ == "__main__":
    result = run_baseline()
    print(f"  Result: {result}")
