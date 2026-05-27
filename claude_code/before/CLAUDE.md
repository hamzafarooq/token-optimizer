# My Project — Claude Code Instructions

## Introduction and Background
Welcome to our project! This is a comprehensive guide for Claude to understand everything about how we work, our team's philosophy, our coding standards, our deployment processes, and everything else you might need to know. We believe in thorough documentation and want to make sure Claude has all the context it needs to help us effectively. This document will grow over time as we learn more about how to work together effectively.

## Team Information
- Lead Developer: John Smith (john@example.com, Slack: @johnsmith)
- Backend Developer: Sarah Johnson (sarah@example.com, Slack: @sarahj)
- Frontend Developer: Mike Chen (mike@example.com, Slack: @mikechen)
- DevOps: Lisa Park (lisa@example.com, Slack: @lisapark)
- Product Manager: Tom Wilson (tom@example.com, Slack: @tomwilson)
- QA Lead: Emma Davis (emma@example.com, Slack: @emmadavis)
- We use Jira for project management, Confluence for documentation, Slack for communication
- Standups are at 9am PST Monday through Friday
- Sprint planning is every two weeks on Monday
- Retrospectives are every two weeks on Friday
- The team is distributed across PST, EST, and GMT+1 timezones

## Project Overview
This is a full-stack web application built with React on the frontend and Node.js/Express on the backend. We use PostgreSQL for our primary database, Redis for caching, and Elasticsearch for search. The application serves approximately 100,000 monthly active users and processes around 1 million API requests per day. We have high availability requirements with 99.9% uptime SLA. The application handles sensitive user data including PII and financial information, so security is a top priority. We follow HIPAA guidelines for data handling and have regular security audits. The application was originally built in 2019 and has gone through several major refactors since then. We are currently on version 4.2.1.

## Technology Stack
### Frontend
- React 18.2 with TypeScript
- Redux Toolkit for state management
- React Query for server state
- Material UI v5 for components
- Vite for bundling
- Jest + React Testing Library for tests
- Storybook for component documentation
- ESLint + Prettier for code quality

### Backend
- Node.js 20 LTS with TypeScript
- Express.js framework
- Prisma ORM with PostgreSQL
- Redis for session storage and caching
- Bull for job queues
- Jest for unit tests
- Supertest for integration tests
- Winston for logging
- Sentry for error monitoring

### Infrastructure
- AWS ECS for container orchestration
- RDS PostgreSQL (db.r6g.2xlarge with read replicas)
- ElastiCache Redis (cache.r6g.xlarge)
- CloudFront CDN
- S3 for static assets and file storage
- Route 53 for DNS
- ACM for SSL certificates
- GitHub Actions for CI/CD
- Terraform for infrastructure as code
- DataDog for monitoring and alerting

## Coding Standards
### General Principles
- Write clean, readable code that other developers can understand
- Follow the DRY (Don't Repeat Yourself) principle
- Write self-documenting code with meaningful variable and function names
- Keep functions small and focused on a single responsibility
- Use meaningful commit messages following conventional commits format
- Always write tests for new functionality
- Code reviews are required for all PRs before merging
- We use trunk-based development with feature flags

### TypeScript Standards
- Always use strict TypeScript (no `any` types allowed without explicit justification)
- Define interfaces for all data structures
- Use enums for fixed sets of values
- Prefer `const` over `let`, never use `var`
- Use optional chaining (?.) and nullish coalescing (??) operators
- Export types separately from implementations

### React Standards
- Functional components only (no class components)
- Custom hooks for reusable logic
- Co-locate tests with components
- Use React.memo() for expensive renders
- Avoid prop drilling beyond 2 levels, use context or Redux
- File naming: PascalCase for components, camelCase for utilities

### Backend Standards
- RESTful API design following OpenAPI 3.0 spec
- All endpoints require authentication unless explicitly marked public
- Rate limiting on all public endpoints
- Request validation using Zod schemas
- Consistent error response format: `{ error: string, code: string, details?: object }`
- Always use transactions for multi-step database operations
- Never log sensitive data (PII, passwords, tokens)

## Git Workflow
1. Create feature branch from `main`: `git checkout -b feat/JIRA-123-description`
2. Make commits: `git commit -m "feat(scope): description"`
3. Push and create PR against `main`
4. PR requires 2 approvals + passing CI
5. Squash merge to keep history clean
6. Delete branch after merge

Commit types: feat, fix, docs, style, refactor, test, chore, perf

## Testing Requirements
- Unit test coverage minimum: 80%
- Integration tests for all API endpoints
- E2E tests for critical user flows (Playwright)
- Performance tests for high-traffic endpoints
- Security scans with Snyk in CI pipeline
- All tests must pass before PR can be merged

## Deployment Process
### Development Environment
- Auto-deploys on every push to `develop` branch
- URL: https://dev.example.com
- Uses development seeds and mock external services

### Staging Environment
- Deploys triggered manually or on PR merge to `staging`
- URL: https://staging.example.com
- Uses anonymized production data snapshots

### Production Environment
- Deploys require manual approval from Lead Developer
- Deploys happen during maintenance window: Tuesday/Thursday 2-4am PST
- URL: https://example.com
- Blue-green deployment strategy
- Automatic rollback on error rate > 1%

## Database Guidelines
- All schema changes via Prisma migrations
- Never modify migration files after they've been run in production
- Migrations must be backward compatible (additive changes only in a single deploy)
- Always add indexes for foreign keys and commonly queried fields
- Use database transactions for operations that modify multiple tables
- Soft deletes preferred over hard deletes for user-facing data
- Archive data older than 2 years to cold storage

## Security Guidelines
- All secrets in AWS Secrets Manager, never in code or environment files
- OWASP Top 10 compliance required
- SQL injection prevention via Prisma parameterized queries
- XSS prevention via React's built-in escaping + DOMPurify for HTML content
- CSRF tokens on all state-changing requests
- Authentication via JWT with 1-hour expiry + refresh tokens
- MFA required for admin accounts
- Penetration testing quarterly

## Common Tasks
### Adding a new API endpoint
1. Define schema in `src/schemas/`
2. Add route in `src/routes/`
3. Implement controller in `src/controllers/`
4. Add service logic in `src/services/`
5. Write unit and integration tests
6. Update OpenAPI spec
7. Add to Postman collection

### Adding a new React component
1. Create component file in appropriate `src/components/` subdirectory
2. Create test file alongside
3. Add to Storybook
4. Export from barrel file
5. Use in parent component

## Frequently Asked Questions
- Q: How do I reset the local database? A: Run `npm run db:reset`
- Q: How do I run just one test? A: Run `jest --testPathPattern=filename`
- Q: How do I see logs? A: Run `docker-compose logs -f app`
- Q: How do I update dependencies? A: Use `npm update` but always review changes
- Q: Where is the API documentation? A: At http://localhost:3000/api-docs in dev

## Notes for Claude
Please always follow our coding standards. Remember that this is a production application serving real users. Always think about performance, security, and maintainability. When in doubt, ask for clarification rather than making assumptions. We prefer explicit over implicit code. Always run tests before suggesting a solution is complete. Consider edge cases and error handling in all implementations.
