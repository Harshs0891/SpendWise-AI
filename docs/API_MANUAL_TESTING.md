# SpendWise AI — API Manual Testing Log

> Record manual API checks actually executed by the developer in Postman. These are not automated test results. Keep secrets, bearer tokens, and database credentials out of this file.

## Environment

- Date: 2026-11-07
- Feature branch: `feat/atomic-transfers`
- API base URL: `http://127.0.0.1:8000`
- API prefix: `/api/v1`
- Database: local PostgreSQL database `spendwise_db`
- Authentication: existing user Bearer token (never store the token here)

## Atomic transfers — manual verification

### Test data

| Resource | ID / details |
|---|---|
| User | `df674e14-6782-4f98-a39d-a2703c108e3c` |
| Primary INR account | `53ef8f22-c27a-4d51-acfe-0fc0b92b7a03`, opening balance INR 50,000 |
| Wallet INR account | `3ee740e9-0e21-4eb0-8aa0-5243015025c8`, opening balance INR 10,000 |
| Temporary USD test account | `292b9e9f-4a44-40aa-bbe9-b7bda67a460f`, opening balance USD 1,000 |
| Successful transfer | `c560e9ad-985b-4d50-9fba-46a16dfb7046`, INR 500 |
| Transfer debit transaction | `72c6d861-d1a6-4d69-9067-60472620f227` |
| Transfer credit transaction | `c2eddfa8-065c-4f18-be70-1f285a04e412` |
| Existing ordinary expense | `6ab2cdf5-2875-45e5-a09a-fb16f971e29c`, INR 30 grocery expense |

### Results

| # | Request / scenario | Expected | Observed | Result |
|---:|---|---|---|---|
| 1 | `POST /api/v1/transfers` — create INR 500 transfer | Successful response with transfer and linked ledger IDs | HTTP success; transfer ID `c560e9ad-985b-4d50-9fba-46a16dfb7046`; debit and credit IDs returned | PASS |
| 2 | Repeat same POST with same idempotency key and same payload | Original transfer returned; no duplicate movement | Same transfer, debit, and credit IDs returned | PASS |
| 3 | Reuse idempotency key with amount changed from 500 to 700 | HTTP 400 conflict | HTTP 400: `Idempotency-Key was already used with a different request.` | PASS |
| 4 | Same source and destination account | HTTP 400 validation error | HTTP 400: `Source and destination accounts must be different.` | PASS |
| 5 | Non-existent source account | HTTP 400 invalid/unavailable account | HTTP 400: `One or both accounts were not found, are inactive, or do not belong to you.` | PASS |
| 6 | INR source to USD destination | HTTP 400 currency validation error | HTTP 400: `Transfers between accounts with different currencies are not supported.` | PASS |
| 7 | `GET /api/v1/transfers` | Successful list containing the valid transfer only | Returned exactly one transfer; rejected requests created no transfer records | PASS |
| 8 | `GET /api/v1/transfers/{transfer_id}` | Successful detail response for the valid transfer | Returned expected transfer and linked ledger IDs | PASS |
| 9 | `GET /api/v1/transactions` | Transfer ledger rows hidden from ordinary transaction list | Returned ordinary INR 30 grocery expense only; transfer rows absent | PASS |
| 10 | `GET /api/v1/analytics/summary` | Transfer legs excluded from income/expense totals | INR income 0, expenses 30, net savings -30 | PASS |
| 11 | `GET /api/v1/analytics/monthly-cashflow` | Transfer legs excluded from monthly cash flow | November 2026 income 0, expenses 30 | PASS |
| 12 | `GET /api/v1/analytics/category-breakdown?currency=INR` | Transfer legs excluded from expense categories | Total expenses 30; Uncategorized 30 (100%) | PASS |
| 13 | `GET /api/v1/analytics/recent-transactions` | Transfer ledger rows hidden | Returned ordinary INR 30 grocery expense only | PASS |
| 14 | `GET /api/v1/analytics/account-balances` before/after idempotent retry | Both transfer legs included in account balances; retry does not move balances again | Primary INR account 49,470; INR wallet 10,500, unchanged after retry | PASS |

All results above were manually executed and reported by the developer in Postman on 2026-11-07. They are not automated test-suite results.

### Balance reconciliation

- Primary INR account: INR 50,000 opening − INR 30 ordinary expense − INR 500 transfer debit = INR 49,470.
- Wallet INR account: INR 10,000 opening + INR 500 transfer credit = INR 10,500.
- Combined same-currency asset balances: INR 59,970. The only net reduction from the initial INR 60,000 was the pre-existing INR 30 grocery expense.
- Retrying the original request with the same idempotency key returned the original IDs and did not change either balance.

### Verification status and limitations

- Python compile/import checks: PASS (developer-reported).
- FastAPI OpenAPI route inspection: PASS; create/list/detail transfer routes appeared.
- Alembic migration: PASS; revision `8c2f4a91d6e0` applied locally and reported as head.
- Postman manual checks: 14 scenarios above PASS.
- Automated tests: NOT RUN by project workflow; `backend/tests/` intentionally untouched.
- Not separately verified: cross-user transfer access, inactive-account rejection as a distinct case, injected database failure/rollback, concurrent idempotency race, pagination edge cases, and insufficient-funds handling.
- Deployment and performance testing: NOT RUN.

### Temporary test data cleanup

The USD test account was created solely to verify cross-currency rejection. Its archive/deletion has not yet been confirmed. Clean it up through the Accounts API if supported, or retain it explicitly as a local development fixture. Do not mistake this test account for production data.

## Future entries

Append new endpoint checks under a dated heading. Record request method/path, relevant non-secret input, expected behavior, observed status/body summary, and PASS/FAIL/NOT RUN. Never include access tokens, passwords, or database credentials.


## Monthly budgets — manual verification (2026-11-07)

### Test data

| Resource | ID / details |
|---|---|
| User | `df674e14-6782-4f98-a39d-a2703c108e3c` |
| Expense category | Food & Dining — `d00f8f01-2447-410e-8f76-22313d8f63a3` |
| Created budget | `a225984f-9655-4de3-9a3f-90b045f44487` |
| Period | 2026-11-01 through 2026-11-30 |
| Initial amount / threshold | INR 10,000 / 80% |
| Updated amount / threshold | INR 12,000 / 75% |

### Results

| # | Request / scenario | Expected | Observed | Result |
|---:|---|---|---|---|
| 1 | `POST /api/v1/budgets` — create November Food & Dining budget | Create a budget with computed period end and progress | Returned budget ID `a225984f-9655-4de3-9a3f-90b045f44487`; category Food & Dining; period end 2026-11-30; spent 0; remaining 10,000; utilization 0.00%; status `on_track` | PASS |
| 2 | `GET /api/v1/budgets` — list budgets | Include the newly created budget and total count | Returned the created budget in `items`; `total: 1` | PASS |
| 3 | `GET /api/v1/budgets/{budget_id}` — retrieve by ID | Return the matching budget and progress | Returned the expected budget ID, category, period, amount, and progress values | PASS |
| 4 | `PATCH /api/v1/budgets/{budget_id}` — update amount and alert threshold | Update only supplied fields and recalculate progress | Amount changed to INR 12,000; threshold changed to 75%; remaining 12,000; utilization 0.00%; status `on_track`; `updated_at` changed | PASS |
| 5 | `DELETE /api/v1/budgets/{budget_id}` — delete budget | Remove the budget | Developer confirmed deletion; follow-up `GET /api/v1/budgets` returned `items: []` and `total: 0` | PASS |

The developer manually executed all five budget endpoint checks in Postman on 2026-11-07 and supplied the observed response bodies. Exact HTTP status codes were not captured in the shared results, so they are intentionally not recorded here.

### Verification status and limitations

- Python compilation: PASS (developer-reported).
- FastAPI OpenAPI route inspection: PASS; all five budget operations appeared.
- Alembic migration: PASS; revision `a91d3c7e4b20` applied locally and reported as head.
- Postman manual CRUD checks: 5 endpoint scenarios PASS.
- Automated tests: NOT RUN by project workflow; `backend/tests/` intentionally untouched.
- Spending threshold transitions, category/currency/month filtering, invalid input cases, duplicate budget handling, and cross-user access were not separately verified in this manual session.
- Deployment and performance testing: NOT RUN.


### Additional budget edge cases and live spending checks (2026-11-07)

| # | Request / scenario | Expected | Observed | Result |
|---:|---|---|---|---|
| 6 | `POST /api/v1/budgets` with `amount: "0"` | Reject non-positive amount during request validation | Response detail reported `greater_than`, location `body.amount`, message `Input should be greater than 0` | PASS |
| 7 | `POST /api/v1/budgets` with `alert_threshold: 101` | Reject threshold above 100 during request validation | Response detail reported `less_than_equal`, location `body.alert_threshold`, message `Input should be less than or equal to 100` | PASS |
| 8 | Create a second budget with the same user, category, month, and currency | Reject duplicate budget and preserve the existing record | First request created budget `0b96f4bb-2420-4f98-960e-b2b1051d9797`; repeating the same request returned `A budget already exists for this category, month, and currency.` | PASS |
| 9 | Create an INR 12,000 Food & Dining expense dated 2026-11-07, then retrieve the November budget | Recalculate spending from matching ordinary expense transactions; at 80% utilization status is warning | Transaction `178b1b1f-8a7e-4a8b-96af-7fde27709a8c` was created. Budget response showed spent INR 12,000; remaining INR 3,000; utilization 80.00%; status `warning` | PASS |
| 10 | Add a further INR 3,000 matching expense and retrieve the same budget | At 100% utilization status is exceeded | Follow-up budget response showed spent INR 15,000; remaining INR 0; utilization 100.00%; status `exceeded`. The second transaction's response/ID was not included in the shared results | PASS (progress result observed) |

The invalid-input and duplicate responses were shared without their Postman status-code display; status codes are therefore not asserted in this log. The final exceeded-state response confirms the aggregate spending result, but the second transaction response itself was not supplied.

### Updated verification status and remaining gaps

- Budget CRUD endpoints: 5/5 manual scenarios PASS.
- Budget input validation: zero amount and threshold above 100 rejected as expected.
- Duplicate budget check: repeated same-key business dimensions rejected as expected.
- Dynamic progress: 80% produced `warning`; 100% produced `exceeded`.
- Automated tests: NOT RUN; `backend/tests/` remains intentionally untouched.
- Still not separately verified: cross-user budget access, custom category belonging to another user, income-category rejection, currency/month list filters, period boundary inclusion/exclusion, transfer-ledger exclusion from budget spending, overspending above 100%, and concurrent duplicate-creation race handling.
