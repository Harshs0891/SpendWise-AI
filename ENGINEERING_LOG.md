# SpendWise AI — Engineering Log

> Chronological record of engineering work actually performed. Do not record plans as completed work. Include commit/PR references when available.

## Project metadata

- Repository: https://github.com/Harshs0891/SpendWise-AI
- Default branch: main
- Architecture direction: modular monolith
- Primary stack: Python, FastAPI, PostgreSQL, SQLAlchemy, React, TypeScript, GenAI
- Master specification: [docs/PROJECT_BLUEPRINT.md](docs/PROJECT_BLUEPRINT.md)

## 2026-11-03 — Initial project documentation

### Repository inspection
- Repository access verified after GitHub permissions were granted.
- Repository visibility: private.
- Default branch: main.
- Repository was empty at the time of inspection (GitHub Contents API returned “This repository is empty”).

### Changes
- Added `docs/PROJECT_BLUEPRINT.md`: product vision, feature scope, technology choices, modular-monolith architecture, data model, API outline, financial correctness/security, testing strategy, four-week roadmap, definition of done, and interview documentation policy.
- Added `ENGINEERING_LOG.md`: this chronological engineering record.

### Verification
- Repository metadata and push permission were verified.
- File creation commits are the source of truth for the documentation commit SHAs.
- No application code, automated tests, or deployment have been implemented or verified in this session.

### Decisions
- Start with a modular monolith rather than microservices.
- Use Decimal / PostgreSQL NUMERIC for all money values.
- Keep financial calculations deterministic and separate from LLM generation.
- AI tools must be allowlisted, user-scoped and validated in backend code.
- Use atomic database transactions for transfers.
- Defer Redis, background workers, vector databases, and other infrastructure until justified.

### Next actions
1. Initialize backend FastAPI project and local PostgreSQL environment.
2. Add SQLAlchemy session management and Alembic migrations.
3. Implement user authentication and ownership enforcement.
4. Add account/category/transaction models and tests.
5. Update Notion Progress Tracker and Interview Ready after each verified milestone.
