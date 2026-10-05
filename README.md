# MySelfPay hosted review — v5

Full application candidate for Vercel with PostgreSQL persistence. Synthetic review only.

## What is included

The reviewed screens, shared classic/chat search, city corrections, comparisons, order samples, facility sources, simulated OSI request, synthetic sign-in, saved conversations, preferences, deletion, private mode, and tenant/member ownership checks remain. Both v4 wording fixes are included. No OCR, external AI, booking, payments or facility delivery is connected.

The local SQLite store is replaced by PostgreSQL when DATABASE_URL is supplied. The hosted handler refuses to use SQLite. HTTPS cookies include Secure, HttpOnly and SameSite=Strict. Login counters are database-backed. Conversation upserts enforce ownership in the SQL statement as well as in the prior lookup.

## Current deployment status

The database exists, but no app deployment or review URL has been created. The workspace network policy blocked CLI access to api.vercel.com. Complete the following commands on your computer. Live PostgreSQL and hosted checks remain required.

## Deployment steps

Use a NEW dedicated review database, not another app's database. Keep Vercel's existing deployment protection enabled; use its Share function for invited reviewers.

1. Extract this folder and open PowerShell in it. Install Python 3.10+ and Node.js if needed.
2. Run `npm install -g vercel`, then `vercel login`.
3. Run `vercel link`. Select the **1smarterinc's projects** team and create a new project named **myselfpay-review**. Use the current directory, framework Other, no custom build command.
4. The dedicated Neon database **myselfpay-review** has already been created in **1smarterinc's projects**, on the Free plan in Washington DC. Do not create another database. In Vercel Storage, open this database, choose **Connect to Project**, select the new **myselfpay-review** app project, and include **Preview**. Ensure DATABASE_URL is available for Preview. The database is not yet initialized.
5. Add a unique REVIEW_PASSWORD (at least 16 characters) with `vercel env add REVIEW_PASSWORD preview`. Do not use the old public demo password. This is one review password for four synthetic identities, not production account enrollment.
6. Run `vercel env pull .env.local --environment=preview` to get the configuration locally. Keep this file private.
7. Install dependencies: `py -3 -m pip install -r requirements.txt python-dotenv`.
8. Initialize from the environment file:

   `py -3 -c "from dotenv import load_dotenv; load_dotenv('.env.local'); from setup_hosted import setup; setup()"`

   Setup creates tables and seeds the reviewed directory only if no active batch exists. It does not copy your local SQLite histories. It does not change passwords of accounts already seeded; use the same password when rerunning setup.

9. Run `vercel deploy` for a protected preview. Do not use `--prod` for this review setup. The entry point automatically accepts VERCEL_URL and VERCEL_PROJECT_PRODUCTION_URL. If using an additional alias, add its exact hostname to APP_HOSTS and redeploy.
10. Open the generated URL and complete the checks below. From the Vercel deployment page, use **Share** to create a review link or invite the reviewers without disabling protection. Assign different synthetic accounts to different reviewers and provide the review password separately.

Accounts: alex.a@example.test and sam.a@example.test are plan-a; alex.b@example.test and jordan.b@example.test are plan-b. People using the same account share its history. There is no self-registration.

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

27 existing backend tests (SQLite), 6 hosted adapter/security unit checks, and 24 client workflow checks using stub transport passed. Python syntax checks passed. PostgreSQL integration, Vercel deployment, and live browser tests have NOT yet been completed. Hosted unit checks do not substitute for a live database test.

Developer checks: `py -3 -m unittest test_functional test_hosted -v`; `node test_ui.mjs`.

## Scope and operations

Use synthetic data only. Published provider evidence is unchanged and has not been freshly verified. This is a research directory, not a contracted network. No OSI price, payment, or availability guarantees.

Conversations expire after 90 days and are purged when history is accessed. Private content is processed but not persisted as conversations. Database provider backups follow that provider's retention; deleting a row is not immediate deletion from backups. No real member pilot is authorized by this package. No production legal/security compliance certification is implied.

The deterministic agent remains a limited demo. Hosting does not upgrade its clinical or language capabilities. Full production authentication, per-reviewer provisioning, distributed abuse controls beyond per-account login limits, scheduled retention cleanup, and monitoring are separate work.

To roll back code, redeploy a prior package. This version adds tables only; do not delete or restore a database as part of code rollback. To end the review, revoke sharing in Vercel and pause/remove the dedicated review deployment when authorized.
