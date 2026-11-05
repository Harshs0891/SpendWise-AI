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

## 2026-11-04 — PostgreSQL persistence foundation

### Objective and actual work
Established the backend persistence foundation: PostgreSQL configuration, SQLAlchemy database/session infrastructure, the initial User ORM model, and the first Alembic migration.

- Added database URL configuration through Pydantic Settings and the backend environment file.
- Added a shared SQLAlchemy Declarative Base.
- Added a reusable Engine with pool_pre_ping=True, SessionLocal (autoflush=False, expire_on_commit=False), and get_db(), which closes the Session in a finally block.
- Added the User model with UUID primary key, unique indexed email, password_hash, is_active, created_at, and updated_at.
- Registered User metadata with Alembic and configured online/offline migration execution using application settings.
- Generated and applied revision 376b9e37233f (create users table).
- Used the native PostgreSQL service on Windows; Docker was not used for the database in this session.

### Files recorded in the latest implementation commit
- backend/app/core/config.py — Pydantic Settings and cached settings factory.
- backend/app/db/base.py — declarative Base.
- backend/app/db/session.py — Engine, SessionLocal, and get_db().
- backend/app/models/user.py — User ORM model.
- backend/app/models/__init__.py — User model export.
- backend/alembic/env.py — settings, metadata registration, and migration configuration.
- backend/alembic/versions/376b9e37233f_create_users_table.py — initial users migration.
- backend/alembic.ini — generated Alembic configuration with placeholder URL; env.py uses application settings.
- backend/requirements.txt — SQLAlchemy, Alembic, and psycopg dependencies.
- backend/.env.example — example environment configuration.
- backend/app/main.py — health endpoint now reads app settings.
The file list above is based on the GitHub diff for commit a55f7aa0a3fb9dec7b7c753643c52a91d6221fdf; no uncommitted local changes are claimed.

### Database/schema changes
Migration 376b9e37233f creates users with:
- id: UUID primary key, non-null.
- email: VARCHAR(255), non-null, unique index ix_users_email.
- password_hash: VARCHAR(255), non-null.
- is_active: BOOLEAN, non-null, server default true.
- created_at and updated_at: timezone-aware timestamps, non-null, server default now().
The alembic_version table records revision 376b9e37233f.

### Commands and verification

| Command/check | Result | Evidence |
|---|---|---|
| Install SQLAlchemy, Alembic, and psycopg dependencies | PASS | User reported successful installation; versions: SQLAlchemy 2.1.8, Alembic 1.20.1, psycopg 3.3.8. |
| alembic init alembic | PASS | User reported successful generation of Alembic files. |
| SQLAlchemy connection executing SELECT current_database() | PASS | User reported: Database connection successful: spendwise_db. |
| alembic upgrade head | PASS | User reported successful upgrade to 376b9e37233f. |
| psql table/schema/revision inspection | PASS | User reported expected users and alembic_version tables, columns, defaults, primary key, unique email index, and revision. |
| Formal database milestone pytest suite | NOT RUN | Intentionally deferred until backend feature development is complete. |
| API-level request exercising get_db() | NOT RUN | Not run/reported in this session. |
| Downgrade, rollback, concurrent-write checks | NOT RUN | Not verified in this session. |

The PASS outcomes above are user-reported; raw terminal transcripts were not attached to this repository update. No performance benchmarks were run.

### Design decisions and trade-offs
- Use SQLAlchemy 2.x declarative mappings and shared Base metadata for Alembic discovery.
- Reuse an Engine and Session factory instead of creating an Engine per request.
- Enable pool_pre_ping to detect stale pooled connections before use.
- Use NullPool for Alembic migration connections rather than the application's connection pool.
- Keep the database URL in environment-based settings; do not put real credentials in alembic.ini or source control.
- Use UUID identifiers and a database unique index for email uniqueness. Case-insensitive normalization/uniqueness remains undecided.
- Formal tests remain deferred by project decision. Manual database verification is not labelled as a formal test pass.

### Bugs, fixes, and remaining risks
- psql was initially unavailable in the VS Code terminal because PATH had not refreshed. Restarting the terminal resolved command discovery.
- The PostgreSQL role password required correction during local setup; the final credential is intentionally not recorded here.
- User.updated_at uses ORM-side onupdate=func.now(), while the migration only defines a database default. Direct SQL updates may not update this timestamp; decide whether a database trigger is needed.
- The current email unique index does not itself define a case-insensitive email policy.
- Registration, password hashing, login/session handling, rate limiting, and user ownership enforcement are not implemented yet.
- Service-level transaction commit/rollback conventions remain to be established.

### Learning and interview takeaways
- Engine manages connectivity/pooling; Session provides the ORM unit-of-work.
- Declarative models register tables in Base.metadata; Alembic needs model modules imported before autogeneration can detect them.
- A request-scoped Session must be closed reliably, including on exceptions.
- Alembic revisions version schema changes; alembic_version records the applied revision.
- A database unique index is the concurrency-safe guard against duplicate values; an application lookup alone cannot prevent racing inserts.
- ORM onupdate behavior differs from a database trigger.

### Next session
1. Add Pydantic registration request/response schemas; never expose password_hash.
2. Select a maintained password-hashing approach and implement the registration service with duplicate-email handling.
3. Add the registration route and wire it into FastAPI. Continue deferring formal tests as agreed, while recording any manual verification separately.

### Session outcome
- Implemented: database settings, SQLAlchemy Base/Engine/session dependency, User model, Alembic configuration, and initial migration.
- Manually verified: database connectivity, migration application, and resulting PostgreSQL schema (user-reported).
- Tested: formal database milestone tests NOT RUN.
- Deployed: NOT RUN; no deployment was performed or verified.
- Implementation reference: a55f7aa0a3fb9dec7b7c753643c52a91d6221fdf.
