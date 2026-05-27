# Project Guide

## Stack
React 18 + TypeScript, Node/Express, PostgreSQL (Prisma), Redis, AWS ECS

## Standards
- TypeScript strict mode — no `any`
- Functional React components, custom hooks for reusable logic
- REST + Zod validation; error format: `{ error, code, details? }`
- Transactions for multi-table writes; never log PII

## Git
Branch: `feat/JIRA-123-desc` → squash merge to `main`; 2 approvals + CI required

## Tests
80% unit coverage minimum; integration tests for all endpoints; run `jest --testPathPattern=<file>` for single test

## DB
Prisma migrations only; additive changes per deploy; soft deletes for user data

## Secrets
AWS Secrets Manager — never in code or `.env`

## Environments
- Dev: auto-deploy on push to `develop`
- Staging: manual trigger or PR merge
- Prod: manual approval, Tue/Thu 2–4am PST, blue-green
