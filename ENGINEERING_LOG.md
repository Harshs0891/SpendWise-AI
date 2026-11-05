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


## 2026-11-05 — User registration foundation

### Objective and actual work
Implemented the first user-registration flow locally: request/response validation, Argon2id password hashing, a registration service, a FastAPI authentication router, and manual PostgreSQL verification.

### Files implemented in the local working tree
The user shared the implementation for review in this session. The following paths were part of the feature work; a GitHub application-code commit was not supplied or verified as part of this documentation update.

- `backend/app/schemas/__init__.py` — package marker/comment for API schemas.
- `backend/app/schemas/user.py` — `UserCreate` validates email with `EmailStr` and constrains password length to 8–128 characters; `UserResponse` exposes UUID, email, active status, and timestamps, using `ConfigDict(from_attributes=True)`. Password and password_hash are intentionally excluded.
- `backend/app/core/security.py` — creates a reusable `PasswordHash.recommended()` hasher from pwdlib and exposes `hash_password()` and `verify_password()`.
- `backend/app/services/__init__.py` — services package marker.
- `backend/app/services/auth_service.py` — normalizes email with strip/lower, checks for an existing user, hashes the password, creates the User ORM object, commits, refreshes, and rolls back on an IntegrityError. The service's database unique index remains the final duplicate guard.
- `backend/app/api/v1/endpoints/__init__.py` — endpoint package marker.
- `backend/app/api/v1/endpoints/auth.py` — exposes `POST /auth/register`, injects `get_db`, delegates to the service, returns `UserResponse`, configures HTTP 201, and maps the service's duplicate-email `ValueError` to HTTP 409.
- `backend/app/main.py` — includes the authentication router under the configured API prefix while retaining the health endpoint.
- `backend/requirements.txt` — user reported pinning `email-validator` and `pwdlib==0.3.1`; the exact email-validator version was not included in the session evidence.

### Architecture and request flow
1. FastAPI receives `POST /api/v1/auth/register`.
2. Pydantic validates the request using `UserCreate`; invalid email/password shape is rejected at the API boundary.
3. FastAPI injects a request-scoped SQLAlchemy Session through `Depends(get_db)`.
4. The router delegates to `register_user()` in the service layer.
5. The service canonicalizes the email for this registration path, checks for an existing row, and hashes the submitted password with pwdlib's recommended Argon2id configuration.
6. The service creates a User ORM instance and persists it in PostgreSQL.
7. The router returns the ORM object through `UserResponse`, which filters out password fields.

### Data and security details
- No schema migration was needed; the existing users table already contains UUID id, unique indexed email, password_hash, is_active, created_at, and updated_at.
- The observed stored hash used the Argon2id format (`$argon2id$v=19$m=65536,t=3,p=4$...`). The full hash and submitted password are intentionally omitted from this log.
- The response schema deliberately excludes both plaintext password and password_hash.
- Email is stripped and lowercased in the registration service. The existing PostgreSQL unique index is case-sensitive; normalization is currently enforced by this application path, not by a database-level case-insensitive index or CITEXT type.
- The initial existence lookup improves the ordinary duplicate-email response, but it cannot prevent concurrent requests from racing. PostgreSQL's unique index is the final integrity guard.
- The shared service code includes rollback on IntegrityError. The exact final implementation that maps a PostgreSQL unique-index violation from a concurrent race to a duplicate-email business error was not re-shared/verified in this session; do not claim that race path is fully verified.
- The API router maps a service-level ValueError to HTTP 409. Other database integrity errors should not be mislabeled as duplicate email.
- Password hashing is intentionally performed before persistence; plaintext passwords must never be stored or logged.

### Dependencies and key implementation choices
- `email-validator` enables Pydantic `EmailStr` validation.
- `pwdlib==0.3.1` with the Argon2 extra supplies the password-hashing implementation.
- `PasswordHash.recommended()` avoids hand-rolling salt and Argon2 parameter handling.
- Request and response schemas are separate so input-only secrets cannot leak in output.
- Router/service separation keeps HTTP status handling out of business logic.

### Manual verification reported by the user
| Check | Result | Evidence / classification |
|---|---|---|
| Password hash generation | PASS | User ran a Python one-liner; hash generated was truthy. |
| Correct password verification | PASS | User-reported output: True. |
| Incorrect password verification | PASS | User-reported output: False. |
| Duplicate registration response | PASS | User shared response body: `{"detail":"An account with this email already exists."}`; router code configures HTTP 409 for the service ValueError. |
| Successful user persistence | PASS | User shared a PostgreSQL row with UUID, demo email, Argon2id hash prefix, and is_active=true. Full hash omitted. |
| Successful registration response body/status | NOT CAPTURED | The database row proves persistence; the actual HTTP 201 response was not included in the supplied evidence. |
| Concurrent duplicate registration race | NOT VERIFIED | Unique index exists and rollback handling was added, but a concurrent-request scenario was not run/reported. |
| Formal pytest suite | NOT RUN | Intentionally deferred until backend development is complete, per the user's instruction. |
| Deployment | NOT RUN | No deployment performed or verified. |

The checks above are user-reported manual verification, not a formal automated test pass. No performance metrics were measured.

### Known gaps and next work
- Verify the final local source for all feature files and commit the application implementation separately from documentation.
- Capture the successful HTTP 201 response and verify the response contains no password fields.
- Verify precise handling of a concurrent unique-index violation and confirm the SQLAlchemy Session is rolled back.
- Decide whether case-insensitive email uniqueness should be enforced at the database level (for example, normalized stored values with a matching uniqueness policy or a functional unique index).
- Login, token/session issuance, current-user endpoint, password reset, email verification, rate limiting, and user-scoped finance authorization remain unimplemented.
- Formal tests remain deferred until backend feature development is complete.

### Learning and interview takeaways
- Pydantic request schemas validate external input; response schemas define the public API contract.
- `from_attributes=True` lets Pydantic serialize SQLAlchemy ORM attributes.
- Argon2id is a password-hashing algorithm, not reversible encryption; verification checks a candidate password against the encoded hash.
- FastAPI dependency injection supplies a request-scoped database Session.
- Services own business logic; routers translate service outcomes into HTTP responses.
- A pre-insert SELECT is not concurrency-safe by itself; a database unique constraint is authoritative.
- A failed SQLAlchemy transaction must be rolled back before the Session can be reused.
- HTTP 201 indicates successful resource creation; HTTP 409 represents a request conflict.

### Session outcome
- Implemented locally (user-shared code reviewed): Pydantic schemas, Argon2 password helper, registration service, registration router, and router wiring.
- Manually verified (user-reported): password hashing/verification, duplicate-email response, and persisted PostgreSQL user row containing an Argon2id hash.
- Tested: formal pytest suite NOT RUN, by project decision.
- Deployed: NOT RUN.
- GitHub application-code commit: not supplied or verified in this documentation-only update.
