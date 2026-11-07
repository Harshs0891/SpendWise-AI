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


## 2026-11-06 — Authentication milestone: registration, JWT login, and current user

### Objective
Complete and manually verify the first end-to-end authentication flow: register a user, authenticate with email/password, issue a JWT access token, and use it to retrieve the authenticated user's profile.

### Work completed
- [x] User registration at `POST /api/v1/auth/register`, with Pydantic validation and Argon2 password hashing.
- [x] JWT configuration and token creation/decoding utilities.
- [x] Login request/response schemas, login service, and `POST /api/v1/auth/login`.
- [x] Bearer-token extraction and `get_current_user` dependency.
- [x] Protected `GET /api/v1/users/me` endpoint.
- [x] Authentication and users routers registered in `backend/app/main.py`.
- [x] Application changes committed and pushed on `feat/user-registration`.

### Implementation and request flow
1. Registration validates the email/password input, normalizes the email, hashes the password using pwdlib's Argon2 implementation, and persists the user.
2. Login looks up the normalized email, verifies the submitted password against the stored hash, rejects inactive users, and creates a signed access token.
3. The JWT uses the configured HS256 algorithm, places the user's UUID in `sub`, and includes `iat` and `exp` claims.
4. The configured access-token lifetime is 30 minutes (1,800 seconds). The login response returns `access_token`, `token_type: bearer`, and `expires_in` in seconds.
5. `OAuth2PasswordBearer` extracts the bearer token. `get_current_user` validates/decodes it, parses the UUID subject, retrieves the user by primary key, and rejects missing or inactive users.
6. `GET /api/v1/users/me` obtains the user through `Depends(get_current_user)` and serializes it through `UserResponse`.

### Relevant files
- `backend/app/core/config.py` — JWT settings.
- `backend/app/core/jwt.py` — access-token creation and decoding.
- `backend/app/core/security.py` — Argon2 password hashing and verification.
- `backend/app/schemas/user.py` — registration, login, public user, and token schemas.
- `backend/app/services/auth_service.py` — registration business logic.
- `backend/app/services/login_service.py` — credential verification and token issuance.
- `backend/app/api/v1/endpoints/auth.py` — registration and login routes.
- `backend/app/api/dependencies.py` — current-user authentication dependency.
- `backend/app/api/v1/endpoints/users.py` — protected current-user route.
- `backend/app/main.py` — router registration.

### API surface
| Method | Endpoint | Authentication |
|---|---|---|
| GET | `/api/v1/health` | Public |
| POST | `/api/v1/auth/register` | Public |
| POST | `/api/v1/auth/login` | Public |
| GET | `/api/v1/users/me` | Bearer token required |

### Manual verification (Postman and local checks)
The user reported that the complete Postman flow worked as expected:
- Login with the registered demo account succeeded and returned an access-token response.
- Calling `GET /api/v1/users/me` with the bearer token succeeded and returned the logged-in user's profile.
- The profile response did not expose `password_hash`.
- Calling `GET /api/v1/users/me` without a bearer token returned `401 Unauthorized`.

Additional manual checks reported earlier:
- JWT generation and decoding succeeded.
- Decoded `sub` matched the original user UUID.
- `exp - iat` was 1,800 seconds.
- Settings loaded the HS256 algorithm and 30-minute expiry without printing the secret.
- Password hashing succeeded; correct-password verification returned true and incorrect-password verification returned false.
- The FastAPI application imported successfully and the users endpoint appeared in Swagger UI.

These are manual checks and user-reported results, not a formal automated test run. The successful Postman response bodies and raw request/response transcripts were not attached to the repository.

### Security, correctness, and remaining gaps
- Passwords are stored as Argon2 hashes; plaintext passwords and password hashes are excluded from public user responses.
- A generic invalid-credentials response reduces account-enumeration leakage.
- The current-user identity comes from the validated token, not a client-supplied user ID.
- Authentication is not authorization: every future finance query and mutation must independently enforce ownership using the authenticated user's ID.
- Refresh tokens, logout/revocation, token rotation, rate limiting, and issuer/audience policy are not implemented or verified yet.
- The access token is short-lived (30 minutes); production HTTPS and deliberate secure client-side token storage remain deployment concerns.

### Decisions and trade-offs
- HS256 is a simple symmetric signing choice for the current single-backend application; the signing secret must remain private and have a deliberate rotation strategy.
- UUID in the JWT subject is stable if the user's email changes.
- A short-lived access token limits the acceptance window for a stolen token but does not provide immediate revocation.
- Login business logic stays in a service layer; the router owns HTTP status and response behavior.
- A dedicated `UserResponse` schema prevents private ORM fields from leaking.

### Interview checkpoint
1. **What are the three parts of a JWT?** Header, payload, and signature. The signature protects integrity/authenticity; it does not encrypt the payload.
2. **Does Base64URL encrypt JWT claims?** No. It is an encoding; anyone holding the token can decode its payload.
3. **Why use UUID in `sub`?** It is a stable user identifier that is independent of a mutable email address.
4. **What does `OAuth2PasswordBearer` do?** It extracts the bearer token and documents the security scheme; the application dependency performs token validation.
5. **Why fetch the user from the database after decoding the JWT?** The account may have been deleted or deactivated since token issuance.
6. **Authentication vs authorization?** Authentication establishes identity; authorization determines which resources that identity may access.
7. **Why use Argon2?** It is a password-hashing algorithm designed to make offline guessing expensive; stored hashes are verified, not decrypted.
8. **Why use one generic login error?** It avoids revealing whether an email is registered.
9. **Does JWT expiry immediately revoke a token?** No. The backend rejects it after expiry; immediate revocation requires additional server-side state or a token-version strategy.

### Planned / implemented / verified / deployed
- **Implemented:** registration, Argon2 password handling, JWT utility, login service/endpoint, bearer-token dependency, and protected current-user endpoint.
- **Manually verified:** token generation/decoding and lifetime; successful Postman login; authenticated `/users/me`; unauthenticated `/users/me` rejection; safe profile response.
- **Automated tests:** intentionally deferred until backend development is complete; no pytest suite was run for this milestone.
- **Deployed:** no deployment performed or verified.
- **Performance:** no performance metrics measured.

### Git references
- Branch: `feat/user-registration`
- `f47a71b` — `feat: implement user registration`
- `585e7cf` — `feat: implement JWT login authentication`
- `3da06f1` — `feat: add authenticated current user endpoint`

### Next session
1. Design the Accounts module's domain model and API before implementation.
2. Decide account-type and credit-card balance semantics explicitly.
3. Use PostgreSQL NUMERIC and Python Decimal for monetary values; keep currency explicit.
4. Enforce authenticated-user ownership on every account query and mutation.
5. Keep formal tests deferred until the backend implementation phase is complete.


## 2026-11-06 — Accounts, Categories, and Transactions backend modules

### Objective
Complete the core finance data APIs and verify the endpoints manually in Postman before moving to analytics or frontend work.

### Work completed
- [x] Accounts API: create, list, retrieve, update, and soft archive accounts.
- [x] Transactions API: create, list, retrieve, and PATCH transactions.
- [x] Categories API: create, list, retrieve, update, and delete categories, with shared system categories and user-owned custom categories.
- [x] Added a system-category seeder with 19 defaults (12 expense, 7 income).
- [x] Registered transaction and category routes; verified their presence in Swagger/OpenAPI.
- [x] Manually exercised the Accounts and Transactions endpoints in Postman. The user reported the tested flows and edge cases working.
- [x] User confirmed the Categories feature PR was merged.

### Implementation details

**Accounts**
- Account types: cash, bank, savings, wallet, credit_card.
- Account data includes currency, opening_balance, active status, and timestamps.
- Archive is soft deletion. Archived accounts are excluded from the active list and remain retrievable with is_active=false.
- All account access is scoped to the authenticated user.

**Transactions**
- Income/expense transaction records include account, optional category, amount, currency, description, merchant, transaction_date, notes, and timestamps.
- List endpoint supports type, account_id, category_id, start_date, end_date, limit, and offset; response includes items, total, limit, and offset.
- Service validates account ownership, active status, and currency equality. Optional category must be system/shared or user-owned and must match transaction kind.
- Amounts use PostgreSQL NUMERIC / Python Decimal semantics.
- No DELETE endpoint was added; financial-record reversal/audit policy remains a future design decision.

**Categories**
- System categories use user_id=NULL and is_system=true; custom categories are associated with their owner.
- Seeder inserts missing shared categories and is idempotent: first run inserted 19; second run inserted 0. Database counts reported 12 expense and 7 income categories.
- Category deletion is configured to set transaction category_id to NULL so the transaction itself remains.

### Manual verification reported

| Module | Checks and outcomes |
|---|---|
| Accounts | Create/list/get/update/archive; archived record hidden from active list; missing token returned 401; cross-user account lookup returned 404. User reported Postman checks passed. |
| Transactions | Create/get/list; type/account filters; pagination; invalid date range returned 422; PATCH updated amount, description, merchant, and notes. User reported checks passed. |
| Categories | System category list returned expected system metadata; custom Gym & Fitness category creation succeeded; user reported category checks working. Exact custom-delete and cross-user category-denial cases were previously not individually confirmed. |
| Seeder | First execution inserted 19; second inserted 0; grouped counts were 12 expense and 7 income. |

These are manual checks, not automated test-suite results. Automated tests remain intentionally deferred until backend feature development is complete. No deployment or performance benchmark is claimed.

### Representative development records
- Active account: `53ef8f22-c27a-4d51-acfe-0fc0b92b7a03`, SpendWise Primary Account, savings, INR.
- Transaction: `6ab2cdf5-2875-45e5-a09a-fb16f971e29c`, expense; amount was updated from INR 1,250.5000 to INR 1,500.0000 during PATCH verification.
- Custom category: `05fc6eb0-3081-45e7-8cd6-fe9d049b270c`, Gym & Fitness, expense.
- These are local development verification records, not production data.

### Database and migration notes
- Tables: users, accounts, categories, transactions, alembic_version.
- Last applied Alembic revision reported: `5bf5efb87ed4`.
- No new migration was needed for category API routes or system-category seeding.
- Local PostgreSQL: 18.6; database spendwise_db; application role spendwise_user.

### Git references
- Accounts + Transactions implementation commit: `a31a37c5f0bad5d0480ea52e0c1c7b6641ebd234`.
- Categories implementation commit: `b877e977c124a19586378c9fa129f96e2de0c1c1`.
- Categories merge commit on main: `8f9bd6e876cc8d6b98c47b0f5230843e4e092dd9`.
- User confirmed the Categories PR was merged.
- Repository: https://github.com/Harshs0891/SpendWise-AI

### Decisions and trade-offs
- Keep finance operations in the backend service layer and scope every query by authenticated user.
- Use soft archive for accounts to preserve references and history.
- Keep shared system categories separate from user-owned custom categories.
- Preserve transactions when a category is deleted by nulling the category reference.
- Do not expose transaction deletion until reversal/audit semantics are defined.
- Do not aggregate balances across different currencies without an explicit exchange-rate conversion policy.

### Known gaps
- Exact custom-category DELETE and cross-user category-denial outcomes were not individually captured as separate confirmed results.
- Formal automated tests remain deferred by the user's requested workflow.
- Transfers, budgets, analytics, AI assistant, frontend, and deployment are not yet verified as implemented.
- Credit-card balance semantics must be decided before account-balance analytics are implemented.
- Local Git synchronization and creation of the next feature branch have not yet been confirmed.

### Learning and interview takeaways
- Soft deletion preserves historical references while changing active-resource visibility.
- Resource ownership must be checked for both primary records and nested account/category references.
- Currency equality is a guard against invalid cross-currency arithmetic.
- Database foreign-key actions can preserve transactions when optional category references are removed.
- An idempotent seeder is safe to rerun during setup.
- Manual Postman verification is useful for iterative development but does not replace automated regression coverage.

### Next session
1. Verify local Git state, sync main after the Categories merge, and create `feat/analytics-dashboard`.
2. Design analytics response contracts and currency-safe aggregation before implementation.
3. Decide how credit-card balances should be represented; do not mix unlike currencies or invent exchange rates.
4. Implement analytics schemas → service → endpoints → Swagger inspection → Postman verification.
5. Continue leaving `backend/tests/` untouched until the final automated-testing phase.


## 2026-11-06 — Analytics schemas and service layer


### Objective
Lay the analytics foundation for the dashboard while preserving currency correctness and the agreed credit-card debt convention.

### Implemented locally on `feat/analytics-dashboard`
- [x] Added analytics response schemas for summary, cash flow, category breakdown, recent transactions, and account balances.
- [x] Implemented `get_dashboard_summary()`: aggregates income, expenses, and net savings separately by currency.
- [x] Implemented `get_monthly_cash_flow()`: groups income and expenses by calendar month for one required currency.
- [x] Implemented `get_category_breakdown()`: aggregates expenses by category, includes uncategorized expenses, and calculates category percentages.
- [x] Implemented `get_recent_transactions()`: returns the latest user-scoped transactions with optional category names.
- [x] Implemented `get_account_balances()`: calculates balances for active user-owned accounts using the agreed asset/debt conventions.
- [x] Python compilation/import checks were run successfully; the user confirmed all five service functions imported successfully.

### Financial rules and design decisions
- Summary values remain grouped by currency; unlike currencies are never added together.
- Monthly cash flow and category breakdown require one selected currency.
- Monetary calculations use Python `Decimal` and database `NUMERIC(19,4)`.
- Date filters are inclusive.
- Normal account balance = opening balance + income − expenses.
- Credit-card debt = opening debt + expenses − payments/income; positive values represent outstanding debt.
- Credit-card payments are currently assumed to be represented as income against the card account. Transfers are not implemented, so this convention depends on consistent transaction recording.
- Analytics are calculated from existing Accounts and Transactions data; no new tables or migration were added.

### Verification classification
- **Passed:** Python compilation/import checks for the analytics service functions.
- **Not yet verified:** Actual SQL execution against PostgreSQL, analytics HTTP routes, Swagger behavior, and Postman responses.
- **Automated tests:** intentionally deferred until backend feature development is complete; `backend/tests/` remains untouched.
- **Frontend/deployment:** not started / not verified.

### Next session
1. Implement the five analytics GET endpoints and request parameter validation.
2. Register the analytics router and inspect the OpenAPI/Swagger output.
3. Start the API and manually verify each endpoint through Postman, including empty results, date filters, currency isolation, uncategorized expenses, and credit-card calculations.
4. Update the API manual testing log with actual outcomes.
5. Keep automated tests deferred until the final testing phase.

### Git status
- Feature branch: `feat/analytics-dashboard`.
- Whether the latest local analytics changes have been committed and pushed was not confirmed in this session; verify `git status`, commit, and push before treating the remote branch as synchronized.
