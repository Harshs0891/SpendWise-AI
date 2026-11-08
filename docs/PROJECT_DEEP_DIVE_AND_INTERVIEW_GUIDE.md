# SpendWise AI — Project Deep Dive & Interview Guide

> Repository: https://github.com/Harshs0891/SpendWise-AI  
> Audit baseline: main at c6e54428cbf244d9379161322554620b42153f8f  
> Purpose: implementation-grounded engineering reference and interview preparation.  
> Status labels: **Implemented** = present and wired; **Partially implemented** = code exists with limitations; **Not implemented** = no supporting implementation found in the inspected tree.

This guide is based on source files, database models, Alembic migrations, configuration, tests, and frontend wiring—not only README claims. It is a code-level review, not a penetration test, production certification, or proof of runtime behavior beyond the tests described.

## 1. Executive summary

SpendWise AI is a personal-finance web application. Users can create accounts, record income and expenses, organize transactions into categories, create monthly category budgets, transfer money between their own accounts, inspect analytics, import/export transactions as CSV, and ask natural-language questions about their financial data.

The architecture is a **modular monolith**:
- React + TypeScript + Vite frontend.
- FastAPI backend with mostly synchronous route handlers.
- PostgreSQL persistence through SQLAlchemy 2.x and Alembic.
- Gemini integration for conversational chat and controlled read-only financial tool calls.
- Deterministic Python services for financial calculations, spending insights, budget advice, and monthly reports.
- GitHub Actions for backend tests and frontend lint/build.

### Implementation status

| Capability | Status | Evidence / qualification |
|---|---|---|
| Registration, login, profile | Implemented | auth/users endpoints and services |
| Argon2 password hashing, JWT | Implemented | core/security.py, core/jwt.py, api/dependencies.py |
| Accounts and archive | Implemented | account endpoint/service/model |
| Income/expense transactions | Implemented | transaction endpoint/service/model |
| System/custom categories | Implemented | category service and seeder |
| Monthly budgets and progress | Implemented | budget service/model |
| Atomic paired-ledger transfers | Implemented | transfer service/model/migration |
| Dashboard analytics | Implemented | SQL aggregation in analytics service |
| CSV import/export | Implemented | validation, atomic insert, formula escaping |
| Gemini chat and conversations | Implemented | AI endpoint/chat/conversation services |
| Gemini read-only finance tools | Implemented | six tool declarations and allow-list dispatcher |
| Spending insights, budget advice, monthly report | Implemented | deterministic Python; not Gemini-generated |
| Frontend pages and API wiring | Implemented | React routes and feature modules |
| Backend automated tests | Partially implemented | unit/model/schema/core tests plus small PostgreSQL integration suite |
| Frontend automated tests | Not implemented in inspected tree | CI runs ESLint and build; no frontend test runner/test files found |
| Deployment manifests | Not implemented in inspected tree | no Dockerfile, compose, cloud or Kubernetes manifest found |
| Production observability | Partially implemented | AI timing logs; no metrics/tracing stack found |
| Rate limiting / quotas | Not implemented in inspected tree | no rate-limit middleware found |
| Recurring transactions, FX conversion, bank sync, OCR | Not implemented | no supporting implementation found |

## 2. Repository inventory

### Root
- .github/workflows/backend-ci.yml — Python 3.12 and PostgreSQL CI.
- .github/workflows/frontend-ci.yml — Node 22 lint/build CI.
- README.md — project overview and local setup.
- ENGINEERING_LOG.md — engineering progress notes.
- docs/PROJECT_BLUEPRINT.md — project blueprint.
- docs/API_MANUAL_TESTING.md — manual API test guide.

### Backend structure

    backend/
      .env.example, requirements.txt, alembic.ini
      alembic/env.py
      alembic/versions/
      app/main.py
      app/api/dependencies.py
      app/api/v1/endpoints/
      app/core/{config,jwt,security}.py
      app/db/{base,session,seed_categories}.py
      app/models/
      app/schemas/
      app/services/
      tests/

Responsibilities:
- api/v1/endpoints: HTTP routing, dependency injection, status mapping.
- schemas: Pydantic request/response validation and serialization.
- services: domain rules and database operations.
- models: SQLAlchemy table mappings and DB constraints.
- core: settings, password hashing, JWT.
- db: engine/session lifecycle, declarative base, seed data.
- alembic: versioned schema changes.

Services query SQLAlchemy directly. There is **no separate repository/DAO layer** in the inspected implementation. Call it a service-oriented layered modular monolith, not strict clean architecture or microservices.

### Frontend structure

    frontend/src/
      main.tsx, App.tsx
      components/{AppLayout,ProtectedRoute}.tsx
      features/{accounts,ai,auth,budgets,categories,csv,dashboard,transactions,transfers}/
      lib/api.ts
      pages/
      types/

App.tsx registers routes. ProtectedRoute guards private pages. AuthProvider restores the user after refresh. Feature API modules centralize Axios calls and TypeScript contracts. Pages render UI and use React Query for server state.

## 3. Product requirements and limitations

### Problem and target user
The application gives an individual a single place to record financial activity, monitor account balances and budgets, inspect cash flow, and query their own records. The data model is user-owned; it is not an organization/family finance system.

### Functional requirements implemented
1. Register and authenticate users.
2. Manage owned financial accounts.
3. Create/list/filter/paginate/update income and expense transactions.
4. Use shared system categories and user-owned custom categories.
5. Transfer money between two owned accounts with paired ledger entries.
6. Create and maintain monthly category budgets.
7. Calculate summaries, cash flow, category breakdown, recent transactions, and balances.
8. Import/export ordinary transactions through CSV.
9. Chat with Gemini using persisted conversations and approved read-only tools.
10. Generate deterministic spending insights, budget advice, and monthly reports.

### Non-functional properties evidenced by design
- Financial precision: Python Decimal and PostgreSQL NUMERIC(19,4).
- User isolation: authenticated user ID is passed to service queries.
- Integrity: foreign keys, checks, unique constraints, and DB transactions.
- Maintainability: domain-oriented modules.
- Input validation: Pydantic plus service-level reference checks.
- Transfer retry safety: user-scoped idempotency key.
- Usability: pagination and React Query caching.

Not evidenced: bank integrations, live synchronization, recurring scheduler, OCR, exchange-rate conversion, household accounts, production deployment, production SLA. Transfers explicitly permit overdrafts in the current implementation.

## 4. Technology stack and versions

Versions are from manifests/config. Frontend caret/tilde values are declared ranges; package-lock resolves exact versions.

| Layer | Technology | Declared version/config |
|---|---|---|
| Runtime | Python | 3.12 in CI |
| API | FastAPI | 0.162.0 |
| Validation | Pydantic | 2.14.2 |
| Settings | pydantic-settings | 2.16.2 |
| ORM | SQLAlchemy | 2.1.8 |
| Migrations | Alembic | 1.20.1 |
| PostgreSQL driver | psycopg[binary] | 3.3.8 |
| ASGI | Uvicorn | 0.54.0 |
| JWT | PyJWT | 2.15.1 |
| Password hashing | pwdlib[argon2] | 0.3.1 |
| Gemini SDK | google-genai | 3.0.0 |
| Tests | pytest | 9.2.0 |
| HTTP test client | httpx | 0.28.1 |
| UI | React / React DOM | ^19.3.1 |
| Language | TypeScript | ~6.0.3 |
| Build | Vite | ^8.3.6 |
| Styling | Tailwind CSS | ^4.3.5 |
| Routing | React Router DOM | ^7.18.5 |
| Server state | TanStack React Query | ^5.107.1 |
| HTTP | Axios | ^1.21.0 |
| Forms | React Hook Form | ^7.91.0 |
| Validation | Zod | ^4.6.7 |
| Charts | Recharts | ^3.10.1 |
| Icons | lucide-react | ^1.70.0 |
| CI | GitHub Actions | actions v6 |

**Configuration mismatch:** app/core/config.py defaults GEMINI_MODEL to gemini-3.8-flash, while backend/.env.example says gemini-3.5-flash-lite. README may contain the older value too. Verify the supported model ID and align code, example env, and docs.

## 5. Architecture

### High-level architecture

~~~mermaid
flowchart LR
    U[User] --> FE[React + TypeScript + Vite]
    FE -->|JSON + Bearer JWT| API[FastAPI v1]
    API --> AUTH[Auth dependency]
    API --> SVC[Domain services]
    SVC --> ORM[SQLAlchemy ORM]
    ORM --> DB[(PostgreSQL)]
    SVC --> FIN[Deterministic finance calculations]
    API --> AI[AI chat orchestration]
    AI --> REG[Read-only tool registry]
    REG --> FIN
    AI --> GEM[Google Gemini API]
    AI --> DB
    FE --> Q[React Query cache]
~~~

Request path: a page calls a feature API module; Axios attaches the session JWT; FastAPI resolves dependencies; endpoint validates request and calls service; service queries/updates SQLAlchemy models; PostgreSQL commits; Pydantic serializes; React Query updates/caches data.

### Backend components

~~~mermaid
flowchart TB
    ROUTES[FastAPI endpoint routers] --> DEPS[API dependencies]
    ROUTES --> SCHEMA[Pydantic schemas]
    ROUTES --> SERVICES[Domain services]
    DEPS --> JWT[JWT decoder]
    DEPS --> DBDEP[get_db]
    SERVICES --> MODELS[SQLAlchemy models]
    SERVICES --> DBDEP
    SERVICES --> ANALYTICS[Analytics service]
    SERVICES --> AITOOLS[AI finance tools]
    AITOOLS --> REGISTRY[AI tool registry]
    SESSION[Engine and SessionLocal] --> PG[(PostgreSQL)]
    DBDEP --> SESSION
    AIROUTE[AI endpoint] --> CHAT[AI chat service]
    CHAT --> GEMINI[Gemini provider client]
    CHAT --> CONV[Conversation service]
    CONV --> MODELS
~~~

### Frontend components

~~~mermaid
flowchart TB
    MAIN[main.tsx] --> QC[QueryClientProvider]
    QC --> BR[BrowserRouter]
    BR --> AUTH[AuthProvider]
    AUTH --> APP[App routes]
    APP --> PR[ProtectedRoute]
    PR --> LAYOUT[AppLayout]
    LAYOUT --> PAGES[Feature pages]
    PAGES --> HOOKS[React Query hooks]
    PAGES --> API[Feature API modules]
    API --> AXIOS[Shared Axios client]
    AXIOS --> FASTAPI[FastAPI /api/v1]
~~~

### Request lifecycle

~~~mermaid
sequenceDiagram
    participant User
    participant Page as React page
    participant Axios
    participant API as FastAPI
    participant Auth as get_current_user
    participant Service
    participant DB as PostgreSQL
    User->>Page: Submit action
    Page->>Axios: Feature API call
    Axios->>Axios: Add Bearer token from sessionStorage
    Axios->>API: HTTP request
    API->>Auth: Resolve current user
    Auth->>DB: Load user by JWT sub
    DB-->>Auth: User row
    Auth-->>API: current_user
    API->>Service: Validated data + current_user.id
    Service->>DB: SQLAlchemy query / transaction
    DB-->>Service: Rows / commit
    Service-->>API: Domain result
    API-->>Axios: JSON response
    Axios-->>Page: Typed response
    Page-->>User: Render updated UI
~~~

### Deployment topology: current vs proposed

Current repository supports local dev: Browser → Vite :5173 → Uvicorn :8000 → PostgreSQL; backend may call Gemini. No production hosting/deployment manifest was found. Do not present a production topology as implemented.

~~~mermaid
flowchart TB
    CLIENT[Browser / Mobile] --> EDGE[CDN + WAF + API Gateway]
    EDGE --> API[Stateless FastAPI replicas]
    API --> PG[(PostgreSQL primary)]
    API --> REDIS[(Redis cache / rate limits)]
    API --> JOBS[Durable job queue]
    JOBS --> WORKER[Background workers]
    WORKER --> OBJ[Object storage]
    API --> GEM[Gemini provider]
    PG --> REPLICA[(Read replica)]
    API --> OBS[Logs / metrics / traces]
    WORKER --> OBS
~~~

This is a **proposed scalable architecture**, not the current implementation.

## 6. Backend implementation

### Bootstrap — app/main.py
Creates FastAPI using configured title/version, adds CORS for localhost:5173 and 127.0.0.1:5173, mounts auth/users/accounts/transactions/categories/analytics/transfers/budgets/CSV/AI routers under /api/v1, and exposes GET /api/v1/health. Production origins need an explicit environment allow-list; do not enable wildcard origins with credentials.

### Configuration — app/core/config.py
Settings reads backend/.env, is case-insensitive, ignores extra keys, and is cached by get_settings(). Variables: APP_NAME, APP_VERSION, ENVIRONMENT, DEBUG, API_V1_PREFIX, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DATABASE_URL, GEMINI_API_KEY, GEMINI_MODEL. Gemini key is optional at app initialization; provider-backed chat fails with RuntimeError if absent.

### Database lifecycle — app/db/session.py
create_engine(settings.database_url, pool_pre_ping=True); SessionLocal uses autoflush=False and expire_on_commit=False. get_db yields a session and closes it in finally. Most endpoints use synchronous SQLAlchemy and normal def handlers; AI uses a synchronous Gemini call, which occupies a worker thread during provider latency.

### Authentication flow
Registration: POST /auth/register → UserCreate validation → register_user normalizes email → duplicate lookup → Argon2 hash → INSERT/commit/refresh → safe UserResponse.
Login: POST /auth/login or /auth/token → authenticate_user normalizes email and verifies Argon2 → create_access_token with sub, iat, exp.
Protected request: OAuth2PasswordBearer extracts token → get_current_user verifies signature/expiry → parses sub UUID → db.get(User, user_id) → rejects missing/inactive user → route receives current_user.

JWT is signed, not encrypted. The implementation has no refresh-token rotation, revocation/blacklist, server-side session, or server-side logout invalidation. Browser logout only removes the token from sessionStorage.

### Layering and patterns actually used
- FastAPI dependency injection for DB/current user.
- Service layer separating HTTP handlers from domain logic.
- Pydantic DTO-like request/response schemas.
- SQLAlchemy Session as unit-of-work.
- Explicit allow-list dispatch for AI tools.
- Soft account archival.
- User-scoped idempotency for transfers.

Not present as separate abstractions: repository/DAO layer, domain aggregate framework, event bus, CQRS, microservices, generic UnitOfWork class.

## 7. Database design

All primary keys are UUIDs. Money uses Numeric(19,4) and Decimal. Timestamps are timezone-aware; financial event dates use DATE.

### Entity reference

| Table | Important columns | Constraints / indexes | Purpose |
|---|---|---|---|
| users | id PK, email, password_hash, is_active, created_at, updated_at | unique email index | Identity |
| accounts | id, user_id FK, name, account_type, currency, opening_balance, is_active, timestamps | account type/currency checks; user and user+active indexes | Financial account |
| categories | id, nullable user_id FK, name, kind, icon, color, is_system, timestamps | kind check; user and user+kind indexes | Shared/custom category |
| transactions | id, user_id FK, account_id FK, nullable category_id FK, nullable transfer_id FK, type, amount, currency, description, merchant, date, notes, timestamps | type/positive amount/currency checks; user/date, user/account, user/category, transfer indexes | Ledger row |
| transfers | id, user_id FK, source_account_id FK, destination_account_id FK, amount, currency, description, date, idempotency_key, created_at | positive amount, currency, distinct account checks; unique user+key; user/date index | Transfer aggregate |
| budgets | id, user_id FK, category_id FK, amount, currency, period_start, alert_threshold, timestamps | positive amount, threshold 1..100, currency check; unique user/category/month/currency; user/period index | Monthly limit |
| ai_conversations | id, user_id FK, title, timestamps | user/updated index | Chat thread |
| ai_messages | id, conversation_id FK, role, content, JSON metadata, created_at | role check; conversation/created index | Chat message |

### ER diagram

~~~mermaid
erDiagram
    USERS ||--o{ ACCOUNTS : owns
    USERS ||--o{ CATEGORIES : creates
    USERS ||--o{ TRANSACTIONS : records
    USERS ||--o{ TRANSFERS : initiates
    USERS ||--o{ BUDGETS : sets
    USERS ||--o{ AI_CONVERSATIONS : starts
    ACCOUNTS ||--o{ TRANSACTIONS : affects
    CATEGORIES o|--o{ TRANSACTIONS : classifies
    CATEGORIES ||--o{ BUDGETS : limits
    TRANSFERS ||--o{ TRANSACTIONS : ledger_legs
    AI_CONVERSATIONS ||--o{ AI_MESSAGES : contains
    USERS {
      uuid id PK
      varchar email UK
      varchar password_hash
      boolean is_active
    }
    ACCOUNTS {
      uuid id PK
      uuid user_id FK
      varchar name
      varchar account_type
      varchar currency
      numeric opening_balance
      boolean is_active
    }
    CATEGORIES {
      uuid id PK
      uuid user_id FK "nullable for system"
      varchar name
      varchar kind
      boolean is_system
    }
    TRANSACTIONS {
      uuid id PK
      uuid user_id FK
      uuid account_id FK
      uuid category_id FK "nullable"
      uuid transfer_id FK "nullable"
      varchar type
      numeric amount
      varchar currency
      date transaction_date
    }
    TRANSFERS {
      uuid id PK
      uuid user_id FK
      uuid source_account_id FK
      uuid destination_account_id FK
      numeric amount
      varchar currency
      varchar idempotency_key
    }
    BUDGETS {
      uuid id PK
      uuid user_id FK
      uuid category_id FK
      numeric amount
      varchar currency
      date period_start
      integer alert_threshold
    }
    AI_CONVERSATIONS {
      uuid id PK
      uuid user_id FK
      varchar title
      timestamptz created_at
      timestamptz updated_at
    }
    AI_MESSAGES {
      uuid id PK
      uuid conversation_id FK
      varchar role
      text content
      json metadata
    }
~~~

System categories have user_id NULL and is_system=true. Transfer has separate source and destination account FKs; its two ledger entries reference transfer_id.

### Constraints and deletion behavior
- UUIDs are opaque identifiers, not authorization.
- Email uniqueness enforced in DB as well as pre-check.
- Account type, category kind, transaction type, positive amounts, currency length, budget threshold, and transfer distinct-account rules are DB checks.
- Transfer idempotency uniqueness is scoped to user.
- Budget uniqueness includes currency.
- Transaction category FK uses ON DELETE SET NULL, preserving historical transaction if category is deleted.
- Account FK uses ON DELETE RESTRICT; API archives rather than deletes accounts.
- User-owned records generally cascade on user deletion.
- AI messages cascade when conversation is deleted.

### Financial semantics
Transaction amounts are always positive; type controls sign. Normal account balance = opening balance + income − expenses. Credit card debt = opening debt + expenses − payments/income. Dashboard totals group by currency; different currencies are never added. Transfer legs affect account balances but are excluded from income/expense totals and budget spend. FX conversion is not implemented. Transfer service permits overdrafts.

### Example SQL

~~~sql
SELECT currency,
       SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) AS income,
       SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) AS expenses
FROM transactions
WHERE user_id = :user_id
  AND transfer_id IS NULL
  AND transaction_date BETWEEN :start_date AND :end_date
GROUP BY currency;
~~~

### SQLAlchemy and Alembic
Models inherit from app.db.base.Base and use Mapped/mapped_column. Services use select(), db.scalar(), db.scalars(), db.execute(). Response schemas use ConfigDict(from_attributes=True). Alembic env imports Base.metadata and model package.

Migration chain:
1. 376b9e37233f — users.
2. 606398c9dbcb — accounts.
3. 5af3e2a737db — categories.
4. 07c7b909df14 — transactions.
5. 5bf5efb87ed4 — remove redundant transaction user index.
6. 8c2f4a91d6e0 — transfers and transaction transfer_id.
7. a91d3c7e4b20 — budgets.
8. 509bd5f6eb4d — AI conversations/messages.

Apply with python -m alembic upgrade head. Do not use create_all as production migration strategy; the integration-test fixture uses it only for an isolated disposable schema.

## 8. API reference

All routes are prefixed /api/v1. Protected routes require Authorization: Bearer <access_token>. Pydantic validates request bodies.

### Auth/users
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /auth/register | No | Register user (201) |
| POST | /auth/login | No | JSON login |
| POST | /auth/token | No | OAuth2 form login for Swagger |
| GET | /users/me | Yes | Current profile |
| GET | /health | No | Health status |

### Accounts
| Method | Path | Purpose |
|---|---|---|
| POST | /accounts | Create |
| GET | /accounts?active_only=true | List |
| GET | /accounts/{account_id} | Retrieve owned account |
| PATCH | /accounts/{account_id} | Update name |
| DELETE | /accounts/{account_id} | Archive (204) |

### Transactions
| Method | Path | Purpose |
|---|---|---|
| POST | /transactions | Create income/expense |
| GET | /transactions | List/filter/paginate |
| GET | /transactions/{transaction_id} | Retrieve ordinary transaction |
| PATCH | /transactions/{transaction_id} | Partial update |

List filters: type (income/expense), account_id, category_id, start_date, end_date, limit (1..100, default 20), offset (>=0, default 0). Date start cannot exceed end. Transfer legs are excluded.

### Categories
| Method | Path | Purpose |
|---|---|---|
| POST | /categories | Create custom category |
| GET | /categories?kind=expense&include_system=true | List |
| GET | /categories/{category_id} | Own or system category |
| PATCH | /categories/{category_id} | Update custom category |
| DELETE | /categories/{category_id} | Delete custom category (204) |

### Transfers
| Method | Path | Purpose |
|---|---|---|
| POST | /transfers | Create transfer and two ledger legs |
| GET | /transfers?limit=20&offset=0 | List |
| GET | /transfers/{transfer_id} | Retrieve |

POST requires Idempotency-Key header, 1–100 chars. Same key/same payload returns original; same key/different payload is rejected.

### Budgets
| Method | Path | Purpose |
|---|---|---|
| POST | /budgets | Create monthly budget |
| GET | /budgets?period_start=YYYY-MM-01&currency=INR | List with progress |
| GET | /budgets/{budget_id} | Retrieve |
| PATCH | /budgets/{budget_id} | Update amount/threshold |
| DELETE | /budgets/{budget_id} | Delete (204) |

### Analytics
| Method | Path | Purpose |
|---|---|---|
| GET | /analytics/summary | Income, expenses, savings grouped by currency |
| GET | /analytics/cash-flow?currency=INR | Monthly cash flow |
| GET | /analytics/category-breakdown?currency=INR | Expense breakdown |
| GET | /analytics/recent-transactions?limit=10 | Recent ordinary transactions |
| GET | /analytics/account-balances | Calculated balances |

### CSV
| Method | Path | Purpose |
|---|---|---|
| GET | /transactions/csv/export | Download filtered CSV |
| POST | /transactions/csv/import | Upload CSV |

Import checks .csv extension, 5 MiB cap, UTF-8/BOM, required columns account_id/type/amount/currency/description/transaction_date, optional id/category_id/merchant/notes. Invalid rows reject the entire file; up to 100 row errors are returned. The optional id header is accepted but not used to preserve IDs.

### AI
| Method | Path | Purpose |
|---|---|---|
| POST | /ai/chat | Send message, optional conversation ID |
| GET | /ai/conversations | List own conversations |
| GET | /ai/conversations/{id} | Get own conversation/messages |
| DELETE | /ai/conversations/{id} | Delete own conversation |
| GET | /ai/insights/spending | Deterministic monthly insights |
| GET | /ai/advisor/budget | Deterministic budget advice |
| GET | /ai/reports/monthly | Deterministic monthly report |

Chat request example:
~~~json
{
  "message": "Where did most of my money go this month?",
  "conversation_id": null
}
~~~

Response includes conversation_id, message_id, response, and tools_used.

### Status codes
200 success; 201 created; 204 deleted/archived; 400 business-rule rejection; 401 missing/invalid auth; 404 missing or non-owned resource; 409 duplicate registration; 413 oversized CSV; 422 schema/date/row validation; 502/503 AI provider/processing failure.

## 9. End-to-end workflows

### Registration and login

~~~mermaid
sequenceDiagram
    participant FE as Register/Login page
    participant API as auth.py
    participant S as auth_service/login_service
    participant H as Argon2
    participant DB as PostgreSQL
    FE->>API: POST /auth/register
    API->>S: register_user(UserCreate)
    S->>S: normalize email and check duplicate
    S->>H: hash_password
    S->>DB: INSERT and COMMIT
    DB-->>FE: safe UserResponse
    FE->>API: POST /auth/login
    API->>S: authenticate_user
    S->>DB: SELECT user by email
    S->>H: verify_password
    S->>S: create_access_token
    S-->>FE: access token + expiry
    FE->>FE: save token in sessionStorage
    FE->>API: GET /users/me
    API-->>FE: UserResponse
~~~

### Create expense
1. Transactions page calls transactionApi.create().
2. Axios attaches JWT.
3. POST /transactions validates TransactionCreate.
4. Endpoint supplies current_user.id, not client owner ID.
5. create_transaction() checks account ownership/active state, currency, category visibility, and category kind.
6. It inserts Transaction and commits.
7. TransactionResponse serializes the ORM row.

### Transfer workflow

~~~mermaid
sequenceDiagram
    participant FE as Transfer page
    participant API as transfers.py
    participant S as transfer_service
    participant DB as PostgreSQL
    FE->>API: POST /transfers + Idempotency-Key
    API->>S: create_transfer(user, payload, key)
    S->>DB: Find existing user/key
    alt Same request already committed
        DB-->>S: Existing transfer
        S-->>FE: Existing result
    else New transfer
        S->>DB: Lock owned active accounts in sorted order
        S->>S: Validate account/currency rules
        S->>DB: Insert transfer
        S->>DB: Insert expense debit + income credit
        S->>DB: COMMIT
        S-->>FE: Transfer and ledger IDs
    end
~~~

Transfer and both ledger legs are inserted in one transaction. Account rows are locked in sorted UUID order to serialize competing transfers and reduce deadlocks. The DB unique constraint handles concurrent idempotency races.

**Frontend caveat:** TransferApi.create() generates crypto.randomUUID() inside each invocation. A client retry that calls the function again uses a new key, so retries across calls are not idempotent. Generate once per logical submission and reuse until outcome is known.

### Budget progress
create_budget() validates an accessible expense category and duplicate user/category/month/currency. _to_progress() sums the user's ordinary expenses for category/currency/month, excluding transfer legs. remaining = budget - spent; utilization uses Decimal. Status: exceeded at >=100%, warning at configured threshold, otherwise on_track.

### CSV import
1. Endpoint validates extension and reads at most 5 MiB + 1 byte.
2. Decodes UTF-8 with BOM support.
3. Service validates headers, duplicate columns, missing/unknown columns, row widths and blanks.
4. Each row is validated by TransactionCreate and reference checks.
5. All rows are accumulated; any invalid row rejects entire import.
6. Valid rows inserted in one add_all/commit.
This is all-or-nothing import. For very large files, use staging/batched processing.

### AI chat

~~~mermaid
sequenceDiagram
    participant FE as AiAssistant.tsx
    participant API as ai.py
    participant CHAT as ai_chat_service
    participant DB as PostgreSQL
    participant G as Gemini
    participant REG as ai_tool_registry
    participant FIN as ai_finance_tools/analytics
    FE->>API: POST /ai/chat + JWT
    API->>CHAT: send_chat_message(user, text, conversation)
    CHAT->>DB: Create/load owned conversation
    CHAT->>DB: Save user message
    CHAT->>DB: Load chronological history
    CHAT->>G: generate_content + system instruction + tools
    G-->>CHAT: Text or function call
    alt Tool requested
        CHAT->>REG: execute_finance_tool(name,args,user)
        REG->>REG: Validate allow-list and arguments
        REG->>FIN: Execute approved read-only function
        FIN->>DB: User-scoped SQL queries
        DB-->>FIN: Financial data
        FIN-->>REG: JSON-safe result
        REG-->>CHAT: Tool result
        CHAT->>G: Function response
        G-->>CHAT: Final answer or next tool call
    end
    CHAT->>DB: Save assistant response and tools_used
    CHAT-->>FE: Response and message IDs
~~~

The tool loop is capped at five Gemini rounds. Automatic SDK execution is disabled; backend dispatches explicitly. Only six read-only tools are available. Authenticated user_id is injected by backend and is not a model argument.

## 10. AI / GenAI architecture

### Implemented
- Gemini client cached with lru_cache in gemini_service.py.
- Model ID comes from settings.
- System instruction asks model to use tools for factual financial data, not invent figures, and not claim write operations.
- Six tools: get_financial_overview, get_spending_by_category, get_monthly_cash_flow, get_budget_status, get_recent_transactions, get_account_balances.
- Dispatcher validates tool names and exact allowed argument keys; validates date strings, currency and bounded limits.
- Tool functions reuse deterministic analytics/budget services.
- Conversation/message history persists in PostgreSQL.
- Tool usage metadata saved with assistant messages.
- Logs include Gemini call, tool, and total durations.
- AI endpoint maps provider 503 to 503 and other provider/runtime errors to 502.

### Concepts and implementation status

| Concept | Meaning | SpendWise status |
|---|---|---|
| LLM | Model generating natural language | Gemini integrated |
| Prompt engineering | Instructions shaping model behavior | System instruction exists |
| Function calling | Model requests structured backend function | Implemented |
| Tool orchestration | Backend validates, runs, returns tool result | Implemented; max 5 rounds |
| RAG | Retrieve document chunks/embeddings to ground generation | Not found; no vector store/embedding pipeline |
| Autonomous agent | Broad planning/action loop, potentially write actions | Do not describe current read-only assistant this way |

### Risks and improvements
- System prompt is not a security boundary. Enforcement is the allow-list, validation, read-only functions, and owner-scoped services.
- Financial data is sent to external Gemini when a tool result is passed back. Add privacy disclosure, data minimization, retention policy, and provider review.
- No rate limit, per-user token budget, concurrency cap, circuit breaker, explicit exponential backoff, or provider response cache found.
- User message is committed before Gemini call; provider failure may leave an unanswered user message.
- Some provider error output uses print; use structured redacted logging.
- History loads up to 100 messages; long threads need token-budget truncation/summarization.
- Synchronous Gemini call occupies a worker thread during latency.

## 11. Security audit

This is a code review, not a penetration test.

| Finding | Severity | Evidence / impact | Recommendation |
|---|---|---|---|
| JWT in sessionStorage | Medium | lib/api.ts and AuthContext; injected JS can read it | Prefer HttpOnly Secure SameSite cookies with CSRF controls, or harden CSP/XSS |
| No refresh/revocation | Medium | Only signed expiring access token | Add refresh rotation/revocation or short token strategy |
| debug defaults true | Medium | core/config.py | Require DEBUG=false in production |
| CORS hardcoded local origins | Deployment blocker | main.py | Environment allow-list for exact origins |
| No rate limiting | Medium | no middleware found | Per-IP/per-user limits, especially auth/CSV/AI |
| Gemini external data disclosure | High privacy concern | Tool results sent to provider | Minimize fields, disclose processing, review provider terms |
| Prompt injection | Medium | System instruction alone insufficient | Adversarial tests and strict server-side controls |
| Transfer key changes on retry | Medium correctness | TransferApi generates new UUID each call | Stable key per logical submission |
| Ownership integrity relies partly on services | Medium defense-in-depth | FKs don't always enforce same-owner relationship | Composite unique/FK constraints where practical |
| Provider errors printed | Low/Medium | ai.py prints provider message | Structured redacted logger |
| No Gemini quotas | Medium | Up to 5 tool rounds per request | User quotas, token budgets, concurrency limits |

### Positive controls
- Argon2 password hashing.
- JWT signature/expiry validation and inactive-user rejection.
- Safe user response excludes password hash.
- Resource queries generally include resource ID and user ID.
- Account/category/currency/type validation.
- DB constraints for important invariants.
- Transfer idempotency uniqueness and row locks.
- CSV size/encoding/row validation and atomic insert.
- CSV export escapes formula-like cells.
- AI tools read-only, allow-listed, and user-scoped.

### Ownership isolation
Never accept owner ID from request or Gemini. Route passes current_user.id to service. Transaction/account lookups filter by both resource ID and user ID. Category queries permit own custom category or shared system category. Conversation lookup checks conversation ID and user ID before loading messages.

Defense-in-depth gap: foreign keys ensure referenced rows exist but do not always ensure transaction.user_id matches account owner. Service checks enforce this today; composite constraints can move more of the invariant into PostgreSQL.

## 12. Performance, scalability, and trade-offs

### Current choices
- SQL aggregates for summaries, cash flow, category breakdown, and balances.
- Indexes for user/date, user/account, user/category, active accounts, budget month, conversation updates, and message chronology.
- Limit/offset pagination for transaction/transfer history.
- React Query caches dashboard sections.
- Gemini client cached per process.
- Transfer account rows locked in deterministic order.

### Bottlenecks
1. Budget progress N+1: list_budgets calls _to_progress per budget; each loads category and sums transactions. Batch aggregate by category/currency/month.
2. Offset pagination becomes expensive for deep pages; use keyset pagination by transaction_date/created_at/id.
3. Spending insights call multiple current/previous summary and category queries; consolidate where possible.
4. Account balance query aggregates transaction rows; precompute only after measuring and maintaining ledger correctness.
5. Synchronous provider call occupies a worker; consider async provider or durable worker for long reports.
6. No analytics cache; Redis can cache user/filter-scoped aggregates with write invalidation.
7. SQLAlchemy pool defaults are used except pool_pre_ping; tune by worker count and DB capacity.
8. No backpressure/rate quotas for Gemini or database-intensive endpoints.

### Scale path
| Scale | Suggested approach |
|---|---|
| 100 users | Current monolith, managed PostgreSQL, backups, structured logs |
| 10k | Query plans, indexes, keyset pagination, pool sizing, rate limits, selective cache |
| 100k | Background workers, queue, read replicas if analytics requires them, metrics/traces |
| 1m | Partition/archive based on measured access patterns, stateless API replicas, robust DR, dedicated read models |

Do not add Kafka/Celery/Redis/microservices just to make the design look advanced. Add them when measured throughput, durability, or isolation requirements justify them.

## 13. Testing audit

### Existing infrastructure
- pytest and FastAPI TestClient.
- Model/schema/core tests.
- PostgreSQL API integration fixture.
- Integration tests require ENVIRONMENT=testing and PostgreSQL; fixture rejects other environments/dialects.
- Fixture creates tables, opens outer transaction, uses create_savepoint for application commits, then rolls back and drops tables.
- Backend CI runs unit tests separately from PostgreSQL API integration tests.
- Frontend CI runs npm ci, npm run lint, npm run build.

### Coverage found
| Area | Existing evidence | Gaps |
|---|---|---|
| Config | default/env tests | production required values |
| JWT | subject/expiry, invalid signature, expired token | malformed claims/algorithm/inactive route |
| Password | hash/verify | policy/timing |
| Models | user/account/category/transaction/transfer/budget | DB cascade/FK integration |
| Schemas | multiple validation tests | complete API contract |
| API | register/login/profile, account scope, transaction create/list/validation | transfers, budgets, categories, CSV, analytics, AI |
| Services | small CSV helper tests | transfer races, budget, analytics, AI |
| Frontend | lint/build | component/hook/API/E2E tests |
| AI | no dedicated AI test modules found | mocked Gemini, tool validation, ownership, provider errors |

### Recommended matrix
- Unit: every service branch, Decimal edge cases, budget threshold and leap-year boundaries, malformed CSV.
- Integration: transfer atomicity, same/different payload idempotency, concurrent duplicate key, row locks, rollback on ledger failure.
- Authorization: user A cannot access user B's accounts/transactions/categories/budgets/transfers/conversations.
- AI: unknown tool, extra argument, invalid date/currency/limit, provider 503, empty response, max rounds, cross-user conversation.
- Frontend: auth restoration, protected routes, transfer retry key stability, query invalidation, loading/error states.
- E2E: register → login → account → transaction → budget → dashboard → transfer → CSV → AI.
- Security: CSV formula payloads, oversized files, malicious prompts, XSS/CSP, rate limits.

## 14. LLD and SOLID

### Responsibilities
| Module / class | Responsibility |
|---|---|
| Settings | Typed environment configuration |
| Base | SQLAlchemy declarative metadata |
| User/Account/Category/Transaction/Transfer/Budget/AIConversation/AIMessage | Persistence entities |
| Pydantic schemas | Request/response contracts |
| get_db | Per-request DB session lifecycle |
| get_current_user | JWT authentication and user resolution |
| Endpoint functions | HTTP contract and status mapping |
| Domain services | Business rules and persistence |
| get_gemini_client | Provider client creation |
| send_chat_message | Chat orchestration and tool loop |
| execute_finance_tool | Tool allow-list and argument validation |
| ai_finance_tools | Bridge to deterministic finance services |

### SOLID assessment
- **Single Responsibility:** generally followed at module level; chat orchestration and CSV import functions are relatively broad.
- **Open/Closed:** explicit tool registry is safe but uses conditional dispatch; typed handler map could be easier to extend.
- **Liskov:** no significant inheritance hierarchy beyond ORM/Pydantic bases; don't claim this as a key feature.
- **Interface Segregation:** feature-specific frontend API modules and focused service functions help.
- **Dependency Inversion:** FastAPI injects DB/current user, but services depend directly on concrete SQLAlchemy Session and models; no repository interface abstraction.

### Design trade-offs
Direct ORM in services is simple but couples logic to SQLAlchemy. Sync DB/provider calls simplify implementation but limit concurrency during slow I/O. Modular monolith avoids distributed operational complexity but cannot independently deploy modules. Read-only AI reduces risk but cannot create/update financial records. Decimal/Numeric is correct for money; separate currencies avoid false aggregation but don't enable FX. Account archive preserves history; deleting a category can set historical category_id to NULL.

## 15. Interview preparation — 80 questions and answers

Use the answers as a structure, then point to actual source. Be candid about limitations; do not claim features not implemented.

### A. Project introduction and architecture (10)

**1. What is SpendWise AI?**  
A personal-finance app for accounts, income/expense transactions, budgets, transfers, analytics, CSV workflows, and Gemini-assisted natural-language analysis. PostgreSQL is financial source of truth; AI is read-only interpretation.  
Follow-up: Which features use LLM? Chat; insights/advice/reports are deterministic.

**2. Why build it?**  
To combine full-stack work with financial correctness and controlled GenAI integration: auth, relational modeling, transactions, analytics, file validation, and provider orchestration.  
Follow-up: Hardest problem? Explain atomic transfer semantics or user-scoped AI tools.

**3. Describe architecture.**  
React/TypeScript SPA calls FastAPI REST endpoints. Dependencies resolve identity and DB sessions; services implement rules; SQLAlchemy persists to PostgreSQL. AI calls Gemini and dispatches approved tools into deterministic services.  
Follow-up: Microservices? No, modular monolith.

**4. Why modular monolith?**  
The domain is cohesive and independent deployment is not yet required. Modules provide separation without distributed transactions or deployment complexity.  
Follow-up: When split? Distinct scaling, team ownership, reliability boundaries, or release cadence.

**5. What is the source of truth?**  
PostgreSQL records; deterministic services calculate totals. Gemini receives tool results but does not own authoritative amounts.  
Follow-up: Why not trust LLM arithmetic? Probabilistic output is unsuitable for financial calculations.

**6. Walk through an API request.**  
Axios attaches JWT; FastAPI validates schema/dependencies; JWT dependency loads user; endpoint calls service; service queries/commits via SQLAlchemy; Pydantic serializes; React Query refreshes UI.  
Follow-up: Where should business validation live? Service and DB constraints.

**7. How is frontend organized?**  
App.tsx routes; ProtectedRoute guards private screens; AuthProvider shares auth state; feature folders hold API clients/types; pages render UI; React Query manages server state.  
Follow-up: Why feature API modules? Reuse, typed contracts, centralized URLs.

**8. Main entities?**  
User, Account, Category, Transaction, Transfer, Budget, AIConversation, AIMessage. Transfer is an aggregate linked to debit/credit ledger legs.  
Follow-up: Why separate Transfer and Transaction? Transfer-specific idempotency/source/destination plus ledger accounting.

**9. Strongest engineering decisions?**  
Decimal/Numeric, user-scoped queries, DB constraints, atomic transfers, idempotency, row locks, read-only AI tools.  
Follow-up: First improvement? Stable frontend retry key and transfer integration tests.

**10. What is not implemented?**  
No recurring scheduler, bank sync, FX conversion, OCR, frontend test suite, deployment manifests, rate limits, or full observability stack.  
Follow-up: How avoid overclaiming? Separate current code from roadmap.

### B. Python and FastAPI (10)

**11. Why FastAPI?**  
Typed signatures, Pydantic, dependency injection, OpenAPI, sync/async support. Fits schema-driven Python APIs.  
Follow-up: Alternatives? Django REST Framework or Flask.

**12. What does Depends do?**  
Resolves dependencies before route execution. SpendWise uses it for DB sessions and current user.  
Follow-up: Can tests override it? Yes, conftest overrides get_db.

**13. Why separate Pydantic schemas from ORM models?**  
Schemas define allowed inputs/outputs independently from persistence. UserResponse excludes password_hash.  
Follow-up: from_attributes? Pydantic reads ORM attributes.

**14. Why service layer?**  
Keeps domain rules outside HTTP handlers and allows reuse by routes and AI tools.  
Follow-up: Is there repository layer? No, services query SQLAlchemy directly.

**15. Sync vs async endpoints?**  
Sync def routes run in FastAPI's threadpool; async routes should await nonblocking I/O. Most DB/Gemini code is synchronous; CSV file read is async.  
Follow-up: Convert all? Only with async DB/provider clients and measured need.

**16. How does validation work?**  
FastAPI parses request into Pydantic types and returns 422 on invalid data. TransactionCreate validates positive Decimal, literal type, currency and description.  
Follow-up: Where validate ownership? Service/database, not Pydantic.

**17. Configuration management?**  
Settings loads env/.env via pydantic-settings; get_settings is cached. Secrets aren't request fields.  
Follow-up: Test config? Instantiate Settings with _env_file=None and monkeypatch env.

**18. What does middleware do here?**  
CORS controls browser cross-origin access; main.py configures local frontend origins.  
Follow-up: Is CORS auth? No.

**19. Error mapping?**  
Services raise ValueError for business failures; routes map to HTTP statuses; Pydantic handles 422; AI provider errors map to 502/503.  
Follow-up: Improvement? Typed domain exceptions and centralized handlers.

**20. Add background work?**  
FastAPI BackgroundTasks for simple noncritical work; durable/retryable reports/imports need queue + worker and persisted job state.  
Follow-up: Why not BackgroundTasks for critical jobs? Process-bound, not durable distributed queue.

### C. Database and PostgreSQL (10)

**21. Why PostgreSQL over MongoDB?**  
Strong relationships, foreign keys, unique/check constraints, and atomic multi-row transfers fit relational DBs.  
Follow-up: When Mongo? Flexible document-centric data with fewer relational invariants.

**22. Why Decimal and NUMERIC?**  
Binary floats cannot represent many decimal fractions exactly. Decimal + Numeric(19,4) preserves money precision.  
Follow-up: Integer minor units? Viable alternative, but currency minor-unit scales vary.

**23. Explain ACID.**  
Atomicity, Consistency, Isolation, Durability. Transfer uses atomic commit so transfer plus both ledger legs persist together or roll back.  
Follow-up: Is idempotency ACID? No, it is application-level retry behavior.

**24. What is FK?**  
Constraint requiring referenced row exists. SpendWise uses FKs with CASCADE, RESTRICT, SET NULL behaviors.  
Follow-up: Does FK guarantee same-user ownership? Not alone.

**25. Why indexes?**  
Support user/date, user/account, user/category, active account, budget period, and conversation/message queries.  
Follow-up: Index downside? Storage and slower writes.

**26. Composite index?**  
Index over multiple columns; (user_id, transaction_date) supports user-scoped date filtering. Order matters due to leftmost-prefix behavior.  
Follow-up: Is reversed order same? Not necessarily.

**27. SQLAlchemy transaction?**  
Session stages changes; commit flushes and commits; failed transaction needs rollback before reuse. Services commit and rollback on exceptions.  
Follow-up: Flush? Sends pending SQL without commit.

**28. Row-level lock?**  
SELECT FOR UPDATE locks selected rows until transaction ends. Transfer locks account rows in sorted UUID order.  
Follow-up: Risks? Deadlocks, lock waits, contention.

**29. Normalization?**  
Separate users/accounts/categories/transactions/budgets/conversations reduce duplicated data and update anomalies.  
Follow-up: Category name in response? Joined at query time, not duplicated in transaction.

**30. Investigate slow query?**  
Capture SQL/timing, EXPLAIN ANALYZE BUFFERS, inspect estimates/indexes/sorts/selectivity, then tune based on evidence.  
Follow-up: N+1 budget query? Batch aggregate by category/currency/month.

### D. SQLAlchemy and Alembic (8)

**31. What is SQLAlchemy ORM?**  
Maps Python classes to tables and manages identity/session plus SQL expression construction. Models use Mapped/mapped_column.  
Follow-up: ORM vs raw SQL? Productivity vs specialized query control.

**32. What is Session?**  
Unit-of-work and identity map tracking ORM objects and transaction state. get_db yields one per request.  
Follow-up: Thread-safe? No, one session per request/task/thread.

**33. SQLAlchemy 2.x select?**  
Unified SQL expression API. Services execute with scalar/scalars/execute.  
Follow-up: scalar vs scalars? One scalar result vs scalar values iterator.

**34. What does Alembic do?**  
Tracks schema changes as ordered migration revisions with upgrade/downgrade. env.py loads Base metadata and DB URL.  
Follow-up: Use create_all in production? No.

**35. What is autogenerate?**  
Compares ORM metadata to DB and proposes migration operations; generated migrations need review and cannot infer all data intent.  
Follow-up: CI improvement? Upgrade empty PostgreSQL to head.

**36. Why expire_on_commit=False?**  
Prevents ORM attributes expiring after commit, easing serialization.  
Follow-up: Trade-off? Potential stale in-memory objects if reused too long.

**37. Why pool_pre_ping?**  
Tests pooled connection liveness before use.  
Follow-up: Does it tune pool size? No.

**38. ON DELETE SET NULL?**  
Transaction survives category deletion while category association becomes null.  
Follow-up: Why RESTRICT accounts? Prevent deletion while ledger rows refer to account.

### E. Authentication and security (8)

**39. How JWT works here?**  
Login verifies Argon2 hash, signs token with user UUID in sub plus iat/exp; protected requests verify and load user.  
Follow-up: Is JWT encrypted? No, signed/readable.

**40. Why Argon2?**  
Memory-hard password hashing makes offline guessing expensive. pwdlib recommended configuration is used.  
Follow-up: Why not SHA-256? Too fast for password storage.

**41. Prevent cross-user access?**  
Derive user ID from JWT, never request; filter resource queries by owner; return 404 for missing/non-owned resources.  
Follow-up: DB defense? Composite FKs.

**42. Protect passwords?**  
Hash before persistence, verify with password-hash library, never expose hash in response.  
Follow-up: Never log credentials or put them in JWT.

**43. Token expiry?**  
Default 30 minutes; exp generated in UTC. No refresh/revocation in current source.  
Follow-up: Revocation? Short access token + rotating refresh token store/denylist.

**44. CSRF vs XSS?**  
CSRF tricks browser into authenticated request; XSS runs script in app origin. sessionStorage token is readable by injected JS.  
Follow-up: Cookie auth? HttpOnly/Secure/SameSite plus CSRF protection.

**45. SQL injection prevention?**  
SQLAlchemy expression values are parameterized. Avoid string-concatenating untrusted SQL.  
Follow-up: Raw SQL safe automatically? No; bind parameters.

**46. Secure AI assistant?**  
Read-only allow-list, strict argument validation, server-injected user ID, owner-scoped queries, tool round limits, rate limits, data minimization, adversarial tests.  
Follow-up: Is system prompt sufficient? No.

### F. REST API and backend engineering (8)

**47. Why API versioning?**  
/api/v1 provides stable contract and allows future breaking v2.  
Follow-up: What needs version? Breaking payload/behavior changes.

**48. PUT vs PATCH?**  
PUT replaces resource; PATCH changes supplied fields. SpendWise uses PATCH schemas and exclude_unset.  
Follow-up: Omitted vs null? Omitted means unchanged; null may clear optional field or be rejected.

**49. Pagination?**  
Transactions/transfers use limit/offset and total metadata; limits bounded.  
Follow-up: Scale deep pages? Keyset pagination.

**50. Prevent duplicate transfers?**  
Client sends Idempotency-Key; DB unique constraint scopes by user; same key/same body replays; different body rejects.  
Follow-up: Why DB constraint? Protects concurrent race.

**51. Transfer consistency?**  
One DB transaction inserts transfer aggregate and debit/credit ledger rows; locks account rows; exceptions rollback.  
Follow-up: Crash before commit? PostgreSQL rolls back uncommitted work.

**52. Exclude transfer legs from spending?**  
Moving existing money is neither income nor expense; counting both legs inflates totals. Analytics/budgets filter transfer_id IS NULL.  
Follow-up: Include in account balance? Yes.

**53. CSV import atomic?**  
Validate all rows first; any invalid row rejects all; otherwise add_all and commit once.  
Follow-up: Large files? Staging table or bounded background batches.

**54. API error design?**  
Stable error schema and typed domain exceptions; avoid exposing stack traces/provider internals. Current route-level ValueError mapping is repetitive.  
Follow-up: Improvement? Custom exceptions and global handlers.

### G. GenAI, Gemini and tool calling (10)

**55. LLM role?**  
Natural-language response and deciding when to request declared finance tool. It does not own DB or authoritative calculations.  
Follow-up: Why deterministic data? Accuracy/reproducibility.

**56. How function calling works?**  
Gemini returns structured tool name/arguments; SpendWise disables auto-execution, validates, executes approved Python function, returns result.  
Follow-up: Does Gemini call Python directly? No.

**57. Which tools?**  
Overview, category spend, monthly cash flow, budget status, recent transactions, account balances; all read-only.  
Follow-up: Add tool? Declaration + dispatcher + scoped implementation + tests.

**58. How AI retrieves user data?**  
Model requests tool; backend injects authenticated UUID; tool reuses deterministic services; SQL returns user-scoped data; JSON-safe result returns to Gemini.  
Follow-up: Can model choose another user ID? No argument accepted.

**59. How chat history stored?**  
AIConversation belongs to user; AIMessage belongs to conversation with role/content/metadata. History loads chronologically into Gemini Content.  
Follow-up: Ownership? Conversation query filters ID and user ID before messages.

**60. Is this RAG?**  
No. It uses structured function calling, not embeddings/vector search/document chunks.  
Follow-up: When RAG? Unstructured documents or policy knowledge.

**61. Prompt injection?**  
Untrusted content tries to override instructions or trigger unsafe behavior. System prompt is not security; tool allow-list, validation, read-only scope and user checks are.  
Follow-up: If write tools added? Explicit confirmation, narrow permissions, audit, idempotency.

**62. Gemini errors?**  
503 provider mapped to 503; other API/runtime failures to 502. Durations logged.  
Follow-up: Missing? Timeouts, retry/backoff, circuit breaker, quotas.

**63. Reduce Gemini cost?**  
Bound history/message size, summarize older turns, avoid redundant tool calls, cache safe deterministic results, set token budgets, rate-limit, log usage.  
Follow-up: Cache keys? Include user and filters; invalidate on writes.

**64. Reduce hallucinations?**  
Use tools for financial facts, deterministic calculations, structured outputs, instructions not to invent, uncertainty when data absent.  
Follow-up: Eliminate hallucinations? No, still verify.

### H. System design and scalability (10)

**65. Handle 10k concurrent users?**  
Profile, run stateless API replicas, size DB pool, rate-limit, keyset paginate, cache expensive reads, move long jobs to workers.  
Follow-up: Add Kafka immediately? No, complexity needs justification.

**66. Add Redis?**  
Rate-limit store, short-lived cache, coordination. Keys include user/filter; invalidate on financial writes.  
Follow-up: Redis source of truth? No, PostgreSQL remains authoritative.

**67. Add recurring transactions?**  
Recurrence rule table, scheduler worker, next_run, unique occurrence/idempotency key, execution status, one transaction per occurrence.  
Follow-up: Missed runs? Catch-up window and idempotent execution.

**68. Multi-currency?**  
Current app separates currencies but doesn't convert. Add FX provider/rate timestamp/base currency/original amount/converted amount and explicit rate policy.  
Follow-up: Which rate? Transaction-date or report-date, documented.

**69. Notifications?**  
Persist outbox event with business transaction; async worker sends email/push; retry idempotently and track delivery.  
Follow-up: Why outbox? Avoid DB commit succeeding while publish fails.

**70. Scale analytics?**  
Optimize SQL first; indexes, cache, then materialized views/read replicas or analytics store if workload warrants.  
Follow-up: Keep aggregates correct? Reconciliation and invalidation/rebuild.

**71. One million transactions?**  
Keyset pagination, profiling, bulk import optimization, archive/partition only when query pattern justifies, backup/restore.  
Follow-up: Partition trade-offs? Operational complexity and unique/FK implications.

**72. Avoid double spend under concurrency?**  
Stable idempotency key + DB unique constraint; lock accounts; if enforcing available balance, check under lock then commit atomically. Current code permits overdraft.  
Follow-up: Lock order? Reduces deadlock cycles.

**73. Background reports?**  
Persist job, enqueue via outbox/queue, worker generates report, object storage, status/download endpoint.  
Follow-up: Worker crash? Lease/visibility timeout and idempotent retry.

**74. Audit logs?**  
Append-only actor/action/resource/timestamp/correlation ID/safe diff; restrict mutation and redact secrets.  
Follow-up: Is app log enough? No, durable queryable audit table needed.

### I. Testing, debugging and trade-offs (6)

**75. Integration test isolation?**  
Requires ENVIRONMENT=testing and PostgreSQL; creates tables; outer transaction plus savepoints contains application commits; rollback and drop after.  
Follow-up: Why separate DB? Avoid destroying dev/prod data.

**76. What CI verifies?**  
Backend pytest unit suite + PostgreSQL API integration suite; frontend ESLint + TypeScript/Vite build.  
Follow-up: Browser E2E? Not currently.

**77. Test transfer idempotency?**  
Same key/body yields same transfer and no extra ledger rows; different body rejects; parallel same-key yields one record; injected failure leaves no partial rows.  
Follow-up: Race guard? DB unique constraint.

**78. Test AI without Gemini?**  
Unit-test dispatcher/tool functions; mock client for orchestration; assert args, user scope, error paths, round limit, persistence.  
Follow-up: Why not live provider in CI? Cost, nondeterminism, latency, secrets.

**79. What redesign first?**  
Stable transfer retry key, transfer/AI integration tests, frontend tests, production settings and rate limits.  
Follow-up: Why? Correctness/security and proving critical workflows.

**80. Biggest trade-off?**  
A simple modular monolith and deterministic finance logic over distributed infrastructure. It suits current scope; synchronous provider calls, N+1 budget progress, limited tests, and missing production operations become constraints as usage grows.  
Follow-up: Evidence to redesign? Latency, queue depth, DB saturation, spend, error rates.

## 16. Resume optimization

### One-line introduction
SpendWise AI is a full-stack personal-finance platform with account and transaction management, category budgets, atomic internal transfers, analytics, CSV workflows, and a Gemini-powered read-only financial assistant.

### Resume bullets — choose only claims you can defend
- Built a full-stack finance platform using React, TypeScript, FastAPI, and PostgreSQL, supporting JWT authentication, accounts, transactions, budgets, analytics, and CSV workflows.
- Implemented atomic account transfers using paired ledger entries, row-level locking, and user-scoped idempotency keys to prevent duplicate transfer records.
- Integrated Gemini function calling with six allow-listed read-only financial tools, routing user-scoped queries to deterministic analytics and budget services.
- Added GitHub Actions CI for backend pytest (including PostgreSQL integration tests) and frontend lint/type-check/build validation.

ATS keywords: Python, FastAPI, React, TypeScript, PostgreSQL, SQLAlchemy, Alembic, REST API, JWT, Argon2, Pydantic, Gemini API, Function Calling, Tool Orchestration, Financial Analytics, ACID Transactions, Idempotency, Row-Level Locking, CSV Processing, pytest, GitHub Actions, CI.

### 30-second explanation
“I built SpendWise AI, a full-stack personal finance application. Users manage accounts, record income and expenses, create budgets, transfer money between accounts, and view analytics. The backend is FastAPI with PostgreSQL and SQLAlchemy. A key engineering feature is atomic transfers using paired ledger entries, row locks, and idempotency keys. I also integrated Gemini with read-only tools so it can answer questions using actual user-scoped financial data rather than inventing totals.”

### 60-second explanation
“SpendWise AI is a modular-monolith finance platform. The React/TypeScript frontend communicates with versioned FastAPI endpoints. The backend uses Pydantic for contracts, SQLAlchemy for persistence, and Alembic for migrations. Authentication uses Argon2 password hashing and signed JWT access tokens. Transactions use Decimal and PostgreSQL Numeric to preserve precision. For transfers, I model a transfer separately and create linked debit and credit ledger rows in one transaction, locking the two accounts and enforcing a per-user idempotency key. Gemini can request one of six read-only finance tools; the backend validates the tool and arguments, injects the authenticated user ID, calls deterministic analytics services, and returns results to Gemini. The project has backend and frontend CI checks.”

For a two-minute explanation: start with problem/product, explain architecture, deep-dive transfer consistency, explain AI safety, then testing and limitations. Do not claim bank integration, production users, autonomous financial actions, or RAG.

## 17. Engineering trade-offs

1. PostgreSQL vs MongoDB: relational integrity/atomic writes vs document flexibility.
2. UUID vs integer IDs: opaque identifiers vs smaller indexes/sequential keys.
3. Decimal vs float: financial precision vs floating-point speed.
4. Modular monolith vs microservices: simple deployment/transactions vs independent scaling.
5. Sync vs async DB: simpler ORM vs nonblocking I/O.
6. JWT vs server sessions: stateless verification vs revocation/session control.
7. SessionStorage vs HttpOnly cookie: SPA convenience vs JS isolation/CSRF considerations.
8. Soft archive vs hard delete: history preservation vs storage/cleanup.
9. Transfer aggregate + ledger legs: explicit transfer semantics vs one-row simplicity.
10. Idempotency key vs payload heuristic: explicit request identity vs ambiguous dedupe.
11. Row locks vs optimistic concurrency: serialization vs version conflicts.
12. Offset vs keyset pagination: page-number simplicity vs deep-page performance.
13. SQL aggregation vs Python: DB efficiency vs application flexibility.
14. Gemini tools vs prompt context: structured authoritative data vs fewer round trips.
15. Read-only AI vs write-enabled agent: reduced risk vs limited automation.
16. Deterministic insights vs LLM metrics: reproducibility vs narrative flexibility.
17. All-or-nothing CSV vs partial import: consistency vs salvage valid rows.
18. Single-currency reporting vs FX conversion: no false aggregation vs broader reports.

For each, explain current choice, benefit, cost, and condition to change.

## 18. Future feature roadmap

| Feature | Design required | Complexity | Priority |
|---|---|---:|---|
| Recurring transactions | Recurrence rule, scheduler/worker, occurrence idempotency | High | P1 |
| FX conversion | Rate source, timestamp policy, base currency, converted amount | High | P1 |
| Receipt OCR | Upload/storage, OCR, human confirmation | High | P2 |
| Bank statement import | Parser/mapping, duplicate detection, reconciliation | High | P2 |
| Forecasting | Historical aggregates, baseline, uncertainty | Medium/High | P2 |
| Anomaly detection | Explainable baselines and feedback | Medium | P2 |
| PDF report | Deterministic report DTO + renderer | Medium | P2 |
| Redis | Cache/rate-limit store with user-scoped keys | Medium | P1/P2 |
| Worker queue | Durable job/outbox + retries | High | P1 |
| Audit logs | Append-only actor/action/resource records | Medium | P1 |
| Observability | Structured logs, metrics, traces, alerts | Medium | P1 |
| Deployment | Docker, managed DB, secrets, TLS, CI/CD | Medium | P0 before public release |
| Backups | Automated snapshots + restore drills | Medium | P0 before production |

### Recurring transaction model sketch

~~~text
recurring_rules
- id UUID PK
- user_id FK
- account_id FK
- category_id nullable FK
- type, amount NUMERIC(19,4), currency, description
- frequency, next_run_at, timezone, is_active
- created_at, updated_at

recurring_executions
- id UUID PK
- rule_id FK
- scheduled_for
- transaction_id FK
- idempotency_key UNIQUE
- status, attempted_at
~~~

Worker should claim due schedules safely, create transaction and execution record in one DB transaction, and advance next_run_at only on successful commit.

## 19. Local setup and verification

Follow README's Windows PowerShell instructions.

### PostgreSQL with Docker

~~~powershell
$env:SPENDWISE_DB_PASSWORD = (python -c "import secrets; print(secrets.token_hex(24))")
docker run --name spendwise-postgres --env POSTGRES_USER=spendwise_user --env POSTGRES_PASSWORD=$env:SPENDWISE_DB_PASSWORD --env POSTGRES_DB=spendwise_db --publish 5432:5432 --detach postgres:16
docker exec spendwise-postgres pg_isready -U spendwise_user -d spendwise_db
docker exec spendwise-postgres createdb -U spendwise_user spendwise_test
~~~

### Backend

~~~powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: DATABASE_URL and SECRET_KEY; add GEMINI_API_KEY for chat
python -m alembic upgrade head
python -m app.db.seed_categories
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

### Frontend

~~~powershell
cd frontend
Copy-Item .env.example .env
npm ci
npm run dev
~~~

Frontend env: VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1

### Tests

Backend unit tests:
~~~powershell
cd backend
python -m pytest -v --ignore=tests/api_integration_test.py
~~~

Integration tests require separate disposable PostgreSQL DB:
~~~powershell
$env:ENVIRONMENT = "testing"
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
$env:DATABASE_URL = "postgresql+psycopg://spendwise_user:$($env:SPENDWISE_DB_PASSWORD)@localhost:5432/spendwise_test"
python -m pytest -v tests/api_integration_test.py
~~~

Never point integration tests at development/production data; fixture creates and drops tables.

Frontend:
~~~powershell
npm run lint
npm run build
npm run preview
~~~

Health: http://127.0.0.1:8000/api/v1/health  
Swagger: http://127.0.0.1:8000/docs

## 20. Learning resources

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- SQLAlchemy: https://docs.sqlalchemy.org/en/20/
- Alembic: https://alembic.sqlalchemy.org/
- PostgreSQL: https://www.postgresql.org/docs/
- PyJWT: https://pyjwt.readthedocs.io/
- OWASP Cheat Sheets: https://cheatsheetseries.owasp.org/
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/docs/
- TanStack Query: https://tanstack.com/query/latest/docs/framework/react/overview
- Vite: https://vite.dev/guide/
- Google Gen AI SDK: https://googleapis.github.io/python-genai/
- Gemini function calling: https://ai.google.dev/gemini-api/docs/function-calling
- GitHub Actions: https://docs.github.com/actions

## 21. Glossary

| Term | Meaning |
|---|---|
| ACID | Atomicity, Consistency, Isolation, Durability |
| Alembic revision | Versioned schema change |
| Argon2 | Memory-hard password hashing algorithm |
| Bearer token | Credential sent in Authorization header |
| CORS | Browser cross-origin request policy |
| DTO | Data Transfer Object |
| FK | Foreign key |
| Idempotency | Repeating a logical request does not duplicate its effect |
| JWT | Signed token containing claims |
| Ledger | Record of financial movements |
| LLM | Large Language Model |
| ORM | Object-Relational Mapper |
| Pydantic | Python validation/serialization library |
| RAG | Retrieval-Augmented Generation |
| Row lock | Database lock on selected row(s) |
| SQL injection | Query manipulation through untrusted input |
| Tool calling | Model requests structured function execution |
| Unit of work | Changes committed or rolled back together |
| UUID | Universally Unique Identifier |

## 22. Final interview checklist

- [ ] Explain request lifecycle from React to PostgreSQL.
- [ ] Draw ER diagram and explain each FK.
- [ ] Explain Decimal/Numeric choice.
- [ ] Walk through transfer atomicity, row locks, idempotency, rollback.
- [ ] Explain how user identity reaches each service and AI tool.
- [ ] Distinguish Gemini function calling from RAG and autonomous agents.
- [ ] Separate deterministic analytics from Gemini interactions.
- [ ] Know exactly what tests and CI run.
- [ ] Be candid about missing frontend tests, deployment, rate limits, and observability.
- [ ] Fix Gemini model configuration mismatch.
- [ ] Fix stable transfer idempotency key on frontend.
- [ ] Add transfer concurrency and AI authorization integration tests.
- [ ] Verify dependency versions and model IDs before quoting them.

**Interview rule:** claim only what current code and tests demonstrate. Explaining a limitation and proposing a sensible fix is a strong engineering answer.
