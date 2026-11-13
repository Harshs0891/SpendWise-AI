# SpendWise AI v1.0 — Free-tier deployment plan

This document describes the first public MVP deployment. Keep the current application architecture and deploy the existing frontend and backend without redesigning features.

## Target architecture

- **Frontend:** Vercel (free Hobby tier) for the Vite production build.
- **Backend:** Render web service (free tier, if currently available for the account/region).
- **Database:** Neon managed PostgreSQL (free plan initially).
- **AI:** Gemini API, configured only on the backend. Treat model/API usage as a separately metered dependency; do not assume unlimited free usage.

Free tiers can change, impose quotas, sleep or suspend inactive services, and may require account verification. Confirm current plan limits and billing requirements before creating resources. This is an MVP/demo hosting arrangement, not a high-availability production setup. In particular, a sleeping free backend can make the first request slow and is unsuitable for a service with uptime guarantees.

## 1. Create managed PostgreSQL

1. Create a Neon project and PostgreSQL database.
2. Select a region close to the backend hosting region where possible.
3. Copy the pooled or direct connection string from the provider dashboard. Prefer the provider-recommended connection string for the selected runtime.
4. Convert the URL scheme to the SQLAlchemy psycopg format used by this repository:
   `postgresql+psycopg://...`
5. Store it only as the backend `DATABASE_URL` secret.
6. Do not expose the database publicly beyond the provider's managed connection access.
7. Keep backups/exports of important test data. Free-tier retention and recovery features may be limited.

## 2. Deploy the backend

Create a Render Web Service connected to this GitHub repository.

- Root directory: `backend`
- Runtime: Python
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/v1/health`

Configure environment variables in the hosting dashboard:

| Variable | Value |
|---|---|
| `APP_NAME` | `SpendWise AI` |
| `APP_VERSION` | `1.0.0` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `API_V1_PREFIX` | `/api/v1` |
| `DATABASE_URL` | Neon SQLAlchemy psycopg URL |
| `SECRET_KEY` | Unique cryptographically random secret |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `CORS_ORIGINS` | JSON array containing the exact Vercel origin |
| `GEMINI_API_KEY` | Secret Gemini API key, or leave unset |
| `GEMINI_MODEL` | Model identifier supported by the configured Gemini API |

Generate a secret locally with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Do not commit secrets or put them in frontend variables. Do not use the sample `SECRET_KEY` from `.env.example`.

### Database migration

Before accepting user traffic, run the Alembic migration against the managed database:

```bash
python -m alembic upgrade head
```

Run this as a one-off release/deploy command from the backend environment with the production `DATABASE_URL`, or use the provider's supported pre-deploy command. Do not run schema creation or destructive test fixtures against production. Seed categories only if the seeder is confirmed idempotent and intended for the production database:

```bash
python -m app.db.seed_categories
```

## 3. Deploy the frontend

Create a Vercel project and import the repository.

- Framework preset: Vite
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Install command: `npm ci`

Set the frontend environment variable:

```dotenv
VITE_API_BASE_URL=https://YOUR-BACKEND-HOST/api/v1
```

Vite variables are embedded into the client bundle. Only the public API base URL belongs here; never put database credentials, Gemini keys, or JWT signing secrets in frontend variables.

If using client-side routes, verify that the host rewrites unknown paths to `index.html` so refreshes on routes such as `/transactions` work.

## 4. Configure CORS

After Vercel assigns the frontend domain, set the backend variable to a JSON array with the exact origin:

```json
["https://YOUR-FRONTEND-DOMAIN.vercel.app"]
```

Add a custom domain only if you actually configure it. Avoid wildcard origins, especially with credentials enabled. Redeploy/restart the backend after changing the variable.

## 5. Release verification

Run these checks against the deployed URLs:

1. Open the frontend over HTTPS.
2. Call `GET /api/v1/health` on the backend.
3. Confirm browser requests succeed and CORS does not block them.
4. Register a new test user and log in.
5. Create an account and verify it remains after logging out and back in.
6. Create income and expense transactions; compare dashboard totals.
7. Create a budget and verify its progress.
8. Transfer between two accounts and verify both ledger legs and resulting balances.
9. Test CSV import/export with a small test file.
10. Test AI only if a valid Gemini key is configured; confirm graceful failure if unavailable.
11. Verify one test user cannot read another test user's records.
12. Check backend logs for exceptions and database connection errors.
13. Confirm direct refresh on nested frontend routes works.
14. Confirm the database contains persistent data after a backend restart.

Use test data only for initial release verification. Do not enter real financial or personally identifying data into this early MVP until security, privacy, backup, and operational controls have been reviewed.

## 6. Known free-tier trade-offs

- Backend instances may sleep when idle; first request latency can be high.
- Provider quotas, storage, compute, egress, and inactivity policies can change.
- A free managed database is appropriate for an MVP test but should not be treated as a backup or availability guarantee.
- Gemini usage may incur charges or be rate-limited depending on account/model terms.
- No uptime SLA, multi-region failover, or managed observability is assumed.

Before sharing the app publicly, review each provider's current pricing, usage limits, region availability, account requirements, and data handling terms.

## 7. Deployment sequence and ownership

1. Merge this production-readiness branch only after local tests and approval.
2. Create Neon database and store connection string securely.
3. Deploy backend and run migrations.
4. Deploy frontend with the backend URL.
5. Set exact frontend origin in backend CORS configuration.
6. Complete the release verification checklist.
7. Tag the release as `v1.0.0` only after smoke tests pass.

## Rollback

- Revert the frontend deployment to the previous successful deployment in the hosting dashboard.
- Revert the backend deployment to the previous successful build if application code is faulty.
- Do not automatically downgrade the database schema during rollback. Review migration compatibility and restore from a known backup only with an explicit recovery plan.
