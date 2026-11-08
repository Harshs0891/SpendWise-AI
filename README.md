# SpendWise AI

**An AI-powered personal finance management platform** for recording income and expenses, managing financial accounts and budgets, analyzing cash flow, and asking natural-language questions about personal financial activity.

SpendWise combines deterministic financial calculations with a Gemini-powered assistant. PostgreSQL is the source of truth for financial records; the language model helps users explore and understand their data rather than inventing balances or totals.

> **Project status:** Active development. The repository includes a React frontend, FastAPI backend, PostgreSQL persistence, Alembic migrations, automated backend tests, and GitHub Actions quality checks.

## Contents

- [Overview and features](#overview-and-features)
- [Architecture](#architecture)
- [Technology stack and versions](#technology-stack-and-versions)
- [Repository structure](#repository-structure)
- [Local setup (Windows PowerShell)](#local-setup-windows-powershell)
- [Environment variables](#environment-variables)
- [Database migrations and seeding](#database-migrations-and-seeding)
- [API overview](#api-overview)
- [Testing and CI](#testing-and-ci)
- [Security](#security)
- [Documentation and troubleshooting](#documentation-and-troubleshooting)

---

## Overview and features

SpendWise AI helps individuals understand their finances through a single application.

### Authentication and user identity
- Register with an email address and password.
- Log in and receive a JWT access token.
- Retrieve the authenticated user's profile.
- Passwords are hashed before persistence.
- Protected endpoints resolve the current user from the Bearer token.
- Financial records are scoped to their owner.

### Financial accounts
- Create, list, retrieve, update, and archive accounts.
- Supported types include cash, bank, savings, wallet, and credit card.
- Store currency and opening balance for each account.
- Calculate balances from opening balance and relevant financial activity.
- Validate ownership before account operations.

### Income and expense transactions
- Record income and expenses against owned accounts.
- Store amount, currency, date, description, merchant, category, and notes.
- Filter by transaction type, account, category, and date range.
- Paginate transaction history.
- Validate positive amounts, account ownership, and currency consistency.
- Keep transfer ledger entries separate from ordinary income and expense analytics.

### Categories
- Shared system categories for common income and expense types.
- User-created custom categories.
- Category kind, icon, and color metadata.
- Filter categories by income or expense.
- System categories cannot be modified or deleted by users.
- An idempotent seeder inserts missing defaults.

### Account transfers
- Move money between two accounts owned by the same user.
- Require different source and destination accounts.
- Reject cross-currency transfers in the current implementation.
- Persist a transfer with paired debit and credit ledger entries atomically.
- Require an Idempotency-Key header to prevent duplicate transfers on retries.
- List and retrieve transfer records.
- Exclude internal transfer legs from ordinary income and expense totals while including them in account balances.

### Budgets
- Create monthly budgets for expense categories.
- Configure amount, currency, period start, and alert threshold.
- List budgets with calculated spending progress.
- Retrieve, update, and delete budgets.
- Review spent amount and budget progress.
- Ask the AI budget advisor for recommendations.

### Dashboard and analytics
- Income, expenses, and net savings summary.
- Monthly cash-flow information.
- Category-wise expense breakdown.
- Recent transactions.
- Account balances.
- Optional date-range and currency filtering where supported.
- User-scoped analytics; transfers are not counted as income or expenses.

### CSV import and export
- Export a user's transactions as CSV.
- Import transactions from a CSV file.
- Validate file extension and UTF-8 encoding.
- Enforce a 5 MB upload limit.
- Return row-level validation errors for invalid input.

### SpendWise AI
The backend integrates Google's Gemini using the Google Gen AI Python SDK.

Current capabilities include:
- Natural-language finance chat.
- Conversation history, detail, and deletion.
- Spending insights for a reference month and optional currency.
- Smart budget advice.
- Monthly financial reports.
- Finance tools that retrieve relevant data from the application.

AI routes require authentication and scope data to the current user. Financial calculations remain in deterministic backend services. A valid Gemini API key is needed for provider-backed chat; core finance features can run without it.

### Frontend screens

| Screen | Purpose |
|---|---|
| Register / Login | Account creation and authentication |
| Dashboard | Financial summary, charts, recent activity, account balances |
| Accounts | Manage financial accounts |
| Transactions | Record and review income and expenses |
| Transfers | Move funds and review transfer history |
| Budgets | Manage monthly budgets |
| Spending Insights | Explore spending patterns |
| Budget Advisor | Review budget recommendations |
| Monthly Report | View monthly financial reports |
| CSV Management | Import and export transactions |
| AI Assistant | Chat with SpendWise AI and manage conversations |

---

## Architecture

SpendWise is a **modular monolith**. The React application communicates with a versioned FastAPI REST API. FastAPI handles request validation, authentication, application services, and database access. PostgreSQL stores canonical financial data.

### High-level architecture

~~~mermaid
flowchart TD
    USER[User / Browser]
    subgraph FRONTEND[Frontend - React + TypeScript]
        PAGES[Pages and UI Components]
        FEATURES[Feature API Modules]
        HTTP[Shared Axios Client]
        PAGES --> FEATURES --> HTTP
    end
    subgraph BACKEND[Backend - FastAPI]
        ROUTERS[API Routers]
        AUTH[JWT Authentication / User Scope]
        SCHEMAS[Pydantic Schemas]
        SERVICES[Application Services]
        MODELS[SQLAlchemy Models]
        ROUTERS --> AUTH
        ROUTERS --> SCHEMAS
        ROUTERS --> SERVICES
        SERVICES --> MODELS
    end
    DB[(PostgreSQL)]
    GEMINI[Google Gemini API]
    USER --> PAGES
    HTTP -->|JSON over HTTP| ROUTERS
    MODELS --> DB
    SERVICES -->|AI requests| GEMINI
~~~

### Backend request lifecycle

1. A page invokes a feature-specific frontend API module.
2. The shared Axios client sends the HTTP request to the configured API base URL.
3. The Axios request interceptor attaches the saved JWT as a Bearer token when present.
4. FastAPI routes the request to the matching endpoint.
5. Authentication dependencies validate the token and resolve the current user for protected routes.
6. Pydantic validates request data and shapes response data.
7. Service functions apply business rules, ownership checks, and transaction boundaries.
8. SQLAlchemy reads or writes PostgreSQL records.
9. FastAPI returns a JSON response or an appropriate HTTP error.

### Backend layers

| Layer | Location | Responsibility |
|---|---|---|
| Application composition | backend/app/main.py | FastAPI app, middleware, router registration, health endpoint |
| API routers | backend/app/api/v1/endpoints/ | HTTP paths, methods, dependencies, response codes |
| API dependencies | backend/app/api/dependencies.py | Authentication and current-user resolution |
| Schemas | backend/app/schemas/ | Pydantic request and response validation |
| Services | backend/app/services/ | Business rules and use-case orchestration |
| Models | backend/app/models/ | SQLAlchemy entities and relationships |
| Database | backend/app/db/ | Engine, sessions, metadata, category seeding |
| Core | backend/app/core/ | Settings, JWT, password security |
| Migrations | backend/alembic/ | Versioned schema changes |

### Frontend layers

- **Pages:** route-level screens such as Dashboard, Transactions, Accounts, Budgets, Transfers, and AI Assistant.
- **Components:** shared layout and protected-route components.
- **Features:** API clients and types grouped by accounts, auth, budgets, categories, CSV, dashboard, transactions, transfers, and AI.
- **Shared library:** Axios client configuration and request interceptor.
- **Types:** frontend data and authentication types.

### Data model

| Entity | Responsibility |
|---|---|
| User | Identity, email, password hash, ownership |
| Account | Financial account, type, currency, opening balance |
| Category | Shared system category or user-owned category |
| Transaction | Income/expense record with account, category, amount, and date |
| Transfer | Account movement linked to paired ledger entries |
| Budget | Monthly category budget and alert threshold |
| AIConversation | User-owned AI conversation |
| AIMessage | Message belonging to a conversation |

Money is stored using decimal database columns. Balances and analytics are derived by backend services rather than trusted from client-side calculations.

---

## Technology stack and versions

Versions are taken from repository manifests and CI configuration. Frontend versions with a caret (^) are declared compatible ranges; package-lock.json resolves the exact installed versions.

### Runtime and infrastructure

| Technology | Version / configuration | Usage |
|---|---|---|
| Python | 3.12 | Backend runtime and CI |
| Node.js | 22 | Frontend CI runtime; use Node 22 locally |
| npm | Bundled with Node.js | Frontend package manager |
| PostgreSQL | 16 | Relational database and CI service |
| GitHub Actions | Ubuntu latest runner | Continuous integration |

### Backend dependencies

| Package | Pinned version | Usage |
|---|---:|---|
| FastAPI | 0.162.0 | REST API framework |
| Pydantic | 2.14.2 | Request/response validation |
| pydantic-settings | 2.16.2 | Environment configuration |
| SQLAlchemy | 2.1.8 | ORM and database sessions |
| Alembic | 1.20.1 | Schema migrations |
| psycopg[binary] | 3.3.8 | PostgreSQL driver |
| uvicorn | 0.54.0 | ASGI server |
| PyJWT | 2.15.1 | JWT creation and validation |
| pwdlib[argon2] | 0.3.1 | Password hashing |
| python-multipart | 0.0.20 | Multipart CSV uploads |
| google-genai | 3.0.0 | Gemini integration |
| pytest | 9.2.0 | Automated tests |
| HTTPX | 0.28.1 | Test HTTP client |

The complete pinned backend dependency list is in [backend/requirements.txt](backend/requirements.txt).

### Frontend dependencies

| Package | Declared version | Usage |
|---|---:|---|
| React | ^19.3.1 | UI library |
| React DOM | ^19.3.1 | Browser rendering |
| TypeScript | ~6.0.3 | Static typing |
| Vite | ^8.3.6 | Dev server and build |
| Tailwind CSS | ^4.3.5 | Styling |
| @tailwindcss/vite | ^4.3.5 | Tailwind/Vite integration |
| React Router DOM | ^7.18.5 | Client-side routing |
| @tanstack/react-query | ^5.107.1 | Server state and queries |
| Axios | ^1.21.0 | HTTP client |
| React Hook Form | ^7.91.0 | Form state |
| Zod | ^4.6.7 | Schema validation |
| Recharts | ^3.10.1 | Dashboard charts |
| lucide-react | ^1.70.0 | Icons |
| ESLint | ^10.14.0 | Linting |

See [frontend/package.json](frontend/package.json) and [frontend/package-lock.json](frontend/package-lock.json) for the full frontend dependency set.

---

## Repository structure

~~~text
SpendWise-AI/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
├── backend/
│   ├── alembic/
│   │   └── versions/             # Database migrations
│   ├── app/
│   │   ├── api/
│   │   │   ├── dependencies.py
│   │   │   └── v1/endpoints/     # FastAPI routers
│   │   ├── core/                 # Settings, JWT, security
│   │   ├── db/                   # Engine, sessions, category seeder
│   │   ├── models/               # SQLAlchemy models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic and AI services
│   │   └── main.py
│   ├── tests/
│   │   ├── api_integration_test.py
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
├── docs/
│   ├── API_MANUAL_TESTING.md
│   └── PROJECT_BLUEPRINT.md
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── features/
│   │   ├── lib/
│   │   ├── pages/
│   │   └── types/
│   ├── .env.example
│   ├── package.json
│   └── package-lock.json
├── ENGINEERING_LOG.md
└── README.md
~~~

---

## Local setup (Windows PowerShell)

These steps target Windows 10/11 and PowerShell. The recommended local setup runs PostgreSQL 16 in Docker Desktop while running FastAPI and Vite directly on Windows.

### 1. Prerequisites

Install Git, Python 3.12, Node.js 22 LTS, Docker Desktop, and VS Code (or another editor).

Verify the tools in PowerShell:

~~~powershell
git --version
py -3.12 --version
node --version
npm --version
docker --version
docker compose version
~~~

Start Docker Desktop and verify the Docker engine:

~~~powershell
docker info
~~~

### 2. Clone the repository

~~~powershell
cd D:\Desktop\Projects
git clone https://github.com/Harshs0891/SpendWise-AI.git
cd SpendWise-AI
~~~

If you already have a local clone:

~~~powershell
cd D:\Desktop\Projects\SpendWise-AI
git switch main
git pull origin main
~~~

### 3. Start PostgreSQL with Docker

Generate a local-only database password. This value is generated on your machine and should not be committed:

~~~powershell
$env:SPENDWISE_DB_PASSWORD = (python -c "import secrets; print(secrets.token_hex(24))")
~~~

Start PostgreSQL 16:

~~~powershell
docker run --name spendwise-postgres --env POSTGRES_USER=spendwise_user --env POSTGRES_PASSWORD=$env:SPENDWISE_DB_PASSWORD --env POSTGRES_DB=spendwise_db --publish 5432:5432 --detach postgres:16
~~~

Wait for PostgreSQL to become ready:

~~~powershell
docker exec spendwise-postgres pg_isready -U spendwise_user -d spendwise_db
~~~

Create a separate database for integration tests. The test fixture creates and drops tables, so it must never use your normal development database:

~~~powershell
docker exec spendwise-postgres createdb -U spendwise_user spendwise_test
~~~

Useful container commands:

~~~powershell
# Check container status
docker ps

# View database logs
docker logs spendwise-postgres

# Stop and restart the database
docker stop spendwise-postgres
docker start spendwise-postgres
~~~

The commands above store database data in the container's writable layer. For long-term local data, use a named Docker volume and back up important data before removing a container.

### 4. Configure and run the backend

Open a PowerShell terminal at the repository root:

~~~powershell
cd D:\Desktop\Projects\SpendWise-AI\backend
~~~

Create and activate a Python 3.12 virtual environment:

~~~powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
~~~

If PowerShell blocks activation, allow scripts for this terminal session only:

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
~~~

Upgrade pip and install all pinned backend dependencies:

~~~powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

Create the local backend environment file:

~~~powershell
Copy-Item .env.example .env
notepad .env
~~~

Set the values in backend/.env:

~~~dotenv
APP_NAME=SpendWise AI
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true
API_V1_PREFIX=/api/v1

DATABASE_URL=postgresql+psycopg://spendwise_user:PASTE_YOUR_LOCAL_DB_PASSWORD@localhost:5432/spendwise_db

SECRET_KEY=PASTE_A_GENERATED_SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

GEMINI_API_KEY=
GEMINI_MODEL=gemini-3.5-flash-lite
~~~

Generate a strong application signing key:

~~~powershell
python -c "import secrets; print(secrets.token_hex(32))"
~~~

Paste the generated value into SECRET_KEY in backend/.env. Set DATABASE_URL to the password generated in step 3. The generated hexadecimal password avoids URL-reserved characters in the connection string.

To enable the Gemini-powered assistant, create an API key in Google AI Studio and set GEMINI_API_KEY in backend/.env. Keep it private. Core finance features can run without a Gemini key.

**Never commit backend/.env.** It contains local credentials and is excluded from source control.

### 5. Create the database schema and seed categories

Keep the backend virtual environment activated and run these commands from the backend directory:

~~~powershell
python -m alembic upgrade head
python -m app.db.seed_categories
~~~

The seeder is idempotent: it inserts missing system categories without duplicating existing ones.

Verify the migration state:

~~~powershell
python -m alembic current
python -m alembic heads
~~~

### 6. Configure and run the frontend

Open a **second PowerShell terminal** at the repository root. Keep the backend terminal open.

~~~powershell
cd D:\Desktop\Projects\SpendWise-AI\frontend
~~~

Create the frontend environment file:

~~~powershell
Copy-Item .env.example .env
notepad .env
~~~

Set the API base URL:

~~~dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
~~~

Install the exact dependency versions recorded in package-lock.json:

~~~powershell
npm ci
~~~

Start the Vite development server:

~~~powershell
npm run dev
~~~

Open the URL printed by Vite, normally http://localhost:5173.

### 7. Start the backend server

In the first terminal, from the backend directory with the virtual environment activated:

~~~powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
~~~

The backend should now be available at http://127.0.0.1:8000.

### 8. Verify the application

From another PowerShell terminal:

~~~powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
~~~

Expected response:

~~~json
{
  "status": "healthy",
  "application": "SpendWise AI",
  "environment": "development"
}
~~~

Useful URLs:

- Frontend: http://localhost:5173
- Backend health: http://127.0.0.1:8000/api/v1/health
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI schema: http://127.0.0.1:8000/openapi.json

Verify a complete user workflow:

1. Register a user.
2. Log in.
3. Create a bank or cash account.
4. Add an income or expense transaction.
5. Confirm the transaction appears in history.
6. Check dashboard totals and account balance.
7. Create a category budget and inspect progress.
8. Create a second account and test a transfer.
9. If Gemini is configured, ask the AI Assistant a question about your financial activity.

**Keep both servers running:** FastAPI on port 8000 and Vite on port 5173.

---

## Environment variables

### Backend: backend/.env

| Variable | Required | Description |
|---|---|---|
| APP_NAME | No | Application name; defaults to SpendWise AI |
| APP_VERSION | No | Application version; defaults to 0.1.0 |
| ENVIRONMENT | No | Runtime environment; development locally |
| DEBUG | No | Debug setting |
| API_V1_PREFIX | No | API prefix; normally /api/v1 |
| DATABASE_URL | Yes | SQLAlchemy PostgreSQL connection URL |
| SECRET_KEY | Yes | Secret used to sign JWTs |
| ALGORITHM | No | JWT algorithm; defaults to HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | No | JWT lifetime in minutes |
| GEMINI_API_KEY | No for core finance features | Google Gemini API key |
| GEMINI_MODEL | No | Gemini model identifier |

### Frontend: frontend/.env

| Variable | Required | Description |
|---|---|---|
| VITE_API_BASE_URL | Yes | Backend URL including /api/v1 |

Only public configuration belongs in Vite variables. Never place private API keys, database credentials, or JWT signing secrets in frontend environment variables.

---

## Database migrations and seeding

Run commands from the backend directory with the virtual environment activated.

~~~powershell
# Apply pending migrations
python -m alembic upgrade head

# Show current database revision
python -m alembic current

# Show migration heads
python -m alembic heads

# Show migration history
python -m alembic history

# Generate a migration after changing SQLAlchemy models
python -m alembic revision --autogenerate -m "describe_schema_change"

# Roll back one migration (use carefully)
python -m alembic downgrade -1

# Seed default system categories
python -m app.db.seed_categories
~~~

Always review autogenerated migrations before applying them. Do not edit an already-applied migration to change an existing schema; create a new migration instead.

---

## API overview

All routes are versioned under /api/v1. Consult Swagger UI at /docs for exact request and response schemas.

| Route group | Base path | Purpose |
|---|---|---|
| Health | /api/v1/health | Application health |
| Authentication | /api/v1/auth | Register, login, OAuth2-compatible token |
| Users | /api/v1/users | Current user profile |
| Accounts | /api/v1/accounts | Create, list, retrieve, update, archive accounts |
| Transactions | /api/v1/transactions | Create, list, retrieve, update transactions |
| Categories | /api/v1/categories | List and manage categories |
| Transfers | /api/v1/transfers | Create, list, retrieve transfers |
| Budgets | /api/v1/budgets | Create, list, retrieve, update, delete budgets |
| Analytics | /api/v1/analytics | Summary, cash flow, category breakdown, recent activity, balances |
| CSV | /api/v1/transactions/csv | Import and export transactions |
| AI | /api/v1/ai | Chat, conversations, spending insights, budget advice, monthly reports |

Protected endpoints expect a JWT in the Authorization header:

~~~http
Authorization: Bearer <access_token>
~~~

### Register

~~~http
POST http://127.0.0.1:8000/api/v1/auth/register
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "choose-a-strong-password"
}
~~~

### Login

~~~http
POST http://127.0.0.1:8000/api/v1/auth/login
Content-Type: application/json

{
  "email": "you@example.com",
  "password": "your-password"
}
~~~

The login response contains an access token. Send it as a Bearer token to protected routes.

### Transfer idempotency

Transfer creation requires an Idempotency-Key header. Use a new unique key for each new logical transfer and reuse that key only when retrying the same request.

~~~http
POST http://127.0.0.1:8000/api/v1/transfers
Authorization: Bearer <access_token>
Idempotency-Key: <unique-request-key>
Content-Type: application/json
~~~

---

## Testing and CI

### Backend unit tests

From backend with the virtual environment activated and local environment configured:

~~~powershell
python -m pytest -v --ignore=tests/api_integration_test.py
~~~

### Backend PostgreSQL API integration tests

Integration tests require a dedicated PostgreSQL database and ENVIRONMENT=testing. The fixture creates and drops its test schema. **Never point these tests at your development database or production database.**

The Docker setup above creates the separate spendwise_test database. Run in a fresh PowerShell terminal:

~~~powershell
cd D:\Desktop\Projects\SpendWise-AI\backend
.\.venv\Scripts\Activate.ps1

$env:ENVIRONMENT = "testing"
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
$env:DATABASE_URL = "postgresql+psycopg://spendwise_user:$($env:SPENDWISE_DB_PASSWORD)@localhost:5432/spendwise_test"

python -m pytest -v tests/api_integration_test.py
~~~

The fixture verifies that ENVIRONMENT is testing and that the configured database dialect is PostgreSQL. Each test runs inside an outer transaction and rolls back its data.

Clear the process-level overrides after testing:

~~~powershell
Remove-Item Env:ENVIRONMENT
Remove-Item Env:SECRET_KEY
Remove-Item Env:DATABASE_URL
~~~

If you use a new terminal, set the variables again. They are not automatically carried between PowerShell processes.

### Frontend checks

Run from frontend:

~~~powershell
# ESLint
npm run lint

# TypeScript check and production build
npm run build

# Preview the production build locally
npm run preview
~~~

### GitHub Actions

The repository has two workflows that run on pull requests targeting main and pushes to main.

**Backend CI** — .github/workflows/backend-ci.yml
- Python 3.12.
- Disposable PostgreSQL 16 service.
- Installs backend/requirements.txt.
- Runs unit tests with the normal development default.
- Runs API integration tests in a separate process with ENVIRONMENT=testing and the dedicated CI database.

**Frontend CI** — .github/workflows/frontend-ci.yml
- Node.js 22.
- Installs packages with npm ci.
- Runs ESLint.
- Runs TypeScript checks and the Vite production build.

Check the GitHub Actions tab for the latest run status. Lint/build checks are not a substitute for browser-level end-to-end tests; Playwright coverage can be added as a future enhancement.

---

## Security

- Never commit backend/.env, frontend/.env, database passwords, Gemini API keys, or JWT signing keys.
- Keep secrets in environment variables or an approved secret manager.
- Use a strong, unique SECRET_KEY outside local development.
- Use HTTPS and production-grade database authentication when deploying.
- Do not expose PostgreSQL directly to the public internet.
- Do not use PostgreSQL trust authentication outside an isolated disposable test environment.
- Keep integration tests pointed at a dedicated test database; the fixture drops its test schema.
- Scope financial reads and writes to the authenticated user.
- Validate financial operations in backend services; do not trust AI output to perform arithmetic or mutate financial records.
- Rotate any genuine credential that has been exposed, even if it is later removed from Git history.

---

## Documentation and troubleshooting

### Project documentation

- [Project Blueprint](docs/PROJECT_BLUEPRINT.md) — product scope, architecture, and implementation direction.
- [API Manual Testing Log](docs/API_MANUAL_TESTING.md) — manually executed API scenarios and recorded results.
- [Backend dependencies](backend/requirements.txt)
- [Frontend dependencies](frontend/package.json)
- [Backend CI](.github/workflows/backend-ci.yml)
- [Frontend CI](.github/workflows/frontend-ci.yml)

### PostgreSQL connection refused

Check Docker Desktop and the PostgreSQL container:

~~~powershell
docker ps
docker logs spendwise-postgres
docker exec spendwise-postgres pg_isready -U spendwise_user -d spendwise_db
~~~

Confirm DATABASE_URL uses port 5432, the correct database name, and the password generated for the container.

### Port 5432 is already in use

Another PostgreSQL instance may be running. Stop that service or map another host port (for example, 5433:5432) and update DATABASE_URL to use port 5433.

### Backend module not found

Confirm the virtual environment is active, dependencies are installed, and commands run from backend:

~~~powershell
python -m pip install -r requirements.txt
python -c "import fastapi, sqlalchemy; print('Backend imports OK')"
~~~

### PowerShell blocks virtual environment activation

~~~powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
~~~

### Frontend cannot reach the backend

- Confirm FastAPI is running at http://127.0.0.1:8000.
- Confirm frontend/.env contains VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1.
- Restart Vite after changing .env because Vite reads environment variables at startup.
- Check the browser console and backend terminal for CORS or API errors.

### Alembic cannot connect

Check backend/.env, verify the database exists, then run:

~~~powershell
python -m alembic current
python -m alembic upgrade head
~~~

### Integration tests refuse to run

The integration fixture requires ENVIRONMENT=testing and PostgreSQL. Check the current process values:

~~~powershell
$env:ENVIRONMENT
$env:DATABASE_URL
~~~

Use the dedicated spendwise_test database, not spendwise_db.

---

## Contributing

1. Create a feature branch from main.
2. Keep changes focused and add tests for behavior changes.
3. Run backend tests and frontend lint/build locally.
4. Update documentation when architecture, configuration, or workflows change.
5. Open a pull request targeting main and wait for required checks.

~~~powershell
git switch main
git pull origin main
git switch -c feat/your-feature-name

# After making and testing changes
git add .
git commit -m "feat: describe your change"
git push -u origin feat/your-feature-name
~~~

## License

No LICENSE file is currently present in the repository. Unless a license is added, all rights remain with the copyright holder and reuse is not automatically granted.
