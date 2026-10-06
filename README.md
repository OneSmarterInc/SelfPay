# MySelfPay hosted review — v5

Full application candidate for Vercel with PostgreSQL persistence. Synthetic review only.

## What is included

The reviewed screens, shared classic/chat search, city corrections, comparisons, order samples, facility sources, simulated OSI request, synthetic sign-in, saved conversations, preferences, deletion, private mode, and tenant/member ownership checks remain. Both v4 wording fixes are included. No OCR, external AI, booking, payments or facility delivery is connected.

The local SQLite store is replaced by PostgreSQL when DATABASE_URL is supplied. The hosted handler refuses to use SQLite. HTTPS cookies include Secure, HttpOnly and SameSite=Strict. Login counters are database-backed and keyed by email+IP, IP and email, so one caller cannot lock another member out. The hosted cookie is `__Host-selfpay_session` and responses carry HSTS. Conversation upserts enforce ownership in the SQL statement as well as in the prior lookup.

## Current deployment status

The database exists, but no app deployment or review URL has been created. The workspace network policy blocked CLI access to api.vercel.com. Complete the following commands on your computer. Live PostgreSQL and hosted checks remain required.

## Deployment steps

Use a NEW dedicated review database, not another app's database. Keep Vercel's existing deployment protection enabled; use its Share function for invited reviewers.

1. Extract this folder and open PowerShell in it. Install Python 3.10+ and Node.js if needed.
2. Run `npm install -g vercel`, then `vercel login`.
3. Run `vercel link`. Select the **1smarterinc's projects** team and create a new project named **myselfpay-review**. Use the current directory, framework Other, no custom build command.
4. The dedicated Neon database **myselfpay-review** has already been created in **1smarterinc's projects**, on the Free plan in Washington DC. Do not create another database. In Vercel Storage, open this database, choose **Connect to Project**, select the new **myselfpay-review** app project, and include **Preview**. Ensure DATABASE_URL is available for Preview and is the **pooled** connection string (host contains `-pooler`). The app logs `SELFPAY_DB_WARNING` if it is given the direct endpoint. The database is not yet initialized.
5. Add a unique REVIEW_PASSWORD (at least 8 characters) with `vercel env add REVIEW_PASSWORD preview`. Do not use the old public demo password. This is one review password for four synthetic identities, not production account enrollment.
6. Run `vercel env pull .env.local --environment=preview` to get the configuration locally. Keep this file private.
7. Install dependencies: `py -3 -m pip install -r requirements.txt python-dotenv`.
8. Initialize from the environment file:

   `py -3 -c "from dotenv import load_dotenv; load_dotenv('.env.local'); from setup_hosted import setup; setup()"`

   Setup creates tables and seeds the reviewed directory only if no active batch exists. It does not copy your local SQLite histories. It does not change passwords of accounts already seeded; use the same password when rerunning setup.

9. Run `vercel deploy` for a protected preview. Do not use `--prod` for this review setup. The entry point automatically accepts VERCEL_URL and VERCEL_PROJECT_PRODUCTION_URL. If using an additional alias, add its exact hostname to APP_HOSTS and redeploy.
10. Open the generated URL and complete the checks below. From the Vercel deployment page, use **Share** to create a review link or invite the reviewers without disabling protection. Assign different synthetic accounts to different reviewers and provide the review password separately.

Accounts: alex.a@example.test and sam.a@example.test are plan-a; alex.b@example.test and jordan.b@example.test are plan-b. People using the same account share its history. Reviewers can also create personal review accounts (see below).

## Required live checks before sharing

- Sign in; secure cookie is present; refresh retains sign-in.
- Save a conversation, sign out, sign in again and resume it; confirm persistence after a new deployment.
- A second member and the other tenant cannot see the first member's history.
- Private searches do not add saved history; deleting history removes it from the app.
- City spelling confirmation, contrast distinctions, budget grouping, comparison and order sample match the reviewed local app.
- Unknown scope prices retain confirmation language. Source links open correctly.
- Request simulation sends nothing. No uploads or real personal/health information.
- Use the share link in a signed-out/incognito browser to check reviewer access.

## Validation performed

Functional tests (SQLite), hosted adapter/security unit checks, PostgreSQL integration tests and client workflow checks (stub transport) run in GitHub Actions on every push (`.github/workflows/tests.yml`). The PostgreSQL suite runs against a local throwaway database, not Neon. Vercel deployment and live browser tests are still manual.

Developer checks: `py -3 -m unittest test_functional test_hosted -v`; `node test_ui.mjs`. For PostgreSQL, set `TEST_DATABASE_URL` to a **throwaway** database (the suite drops and recreates tables) and run `py -3 -m unittest test_postgres -v`.

## Scope and operations

Use synthetic data only. Published provider evidence is unchanged and has not been freshly verified. This is a research directory, not a contracted network. No OSI price, payment, or availability guarantees.

Conversations expire after 90 days and are purged when history is accessed. Private content is processed but not persisted as conversations. Database provider backups follow that provider's retention; deleting a row is not immediate deletion from backups. No real member pilot is authorized by this package. No production legal/security compliance certification is implied.

The deterministic agent remains a limited demo. Hosting does not upgrade its clinical or language capabilities. Full production authentication, per-reviewer provisioning, distributed abuse controls beyond per-account login limits, scheduled retention cleanup, and monitoring are separate work.

To roll back code, redeploy a prior package. This version adds tables only; do not delete or restore a database as part of code rollback. To end the review, revoke sharing in Vercel and pause/remove the dedicated review deployment when authorized.

## Personal review accounts

The sign-in screen supports creating an account using a name, email and password (8–200 characters). Credentials are stored as salted PBKDF2-HMAC-SHA256 hashes at 600,000 iterations. Hashes created before this change (200,000 iterations) upgrade automatically at the member's next sign-in. Registering an email that already exists returns the same response as a new registration and does not change that account. Registration assigns the server-controlled `review` organization; clients cannot select a health-plan tenant. Existing demo accounts remain available. My account → Change password requires the current password and CSRF token, and invalidates all sessions for that member. No database migration is required.

Email ownership verification and self-service forgotten-password recovery are not connected. These are personal review accounts, not verified health-plan identities. Continue using synthetic search scenarios and no real medical documents. The REVIEW_PASSWORD environment variable seeds demo accounts only; it is not the password for newly registered accounts and changing it does not reset existing accounts.
