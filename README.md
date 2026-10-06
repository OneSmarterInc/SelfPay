# MySelfPay — guest review app

Current review build: guest access plus the 6 October 2026 audit fixes.

## Member flow

Click **Sign in as guest** to enter without registration, email, or password.
The navigation changes to **Sign out**. Search, guided chat, comparison, provider
sources, saved conversations, preferences, deletion, and private mode are available.
Order scan, voice, and OSI facility requests remain simulations. No real medical
uploads, external AI, booking, payment, or facility delivery is connected.

Each guest receives a separate server-owned identity. The eight-hour session cookie
restores access on refresh. Signing out or losing/expiring the cookie means a new
guest cannot recover the old history. Signing out does not delete stored history.
Conversations expire 90 days after their last save and are hidden immediately on expiry;
provider backup retention is separate. Use synthetic information only.

Email/password HTTP endpoints return 410. Existing member records and the internal
password helpers remain for compatibility. Password hashes use 600,000 PBKDF2
iterations; legacy hashes upgrade if the internal credential login helper is used.
This does not re-enable credential login in the portal.

## Audit fixes integrated

- Hosted cookies use `__Host-selfpay_session`, Secure, HttpOnly, and SameSite=Strict.
- Hosted responses include HSTS; origin checks and CSRF protection remain active.
- Hosted rate limits use the existing `login_limits` database table. Guest creation
  is limited per client IP rather than one shared counter for all visitors.
- Internal parser/type errors are not echoed to visitors.
- PostgreSQL prepared statements are disabled for transaction-pooler compatibility.
- A direct Neon connection produces a warning; use the pooled `-pooler` URL.
- CI runs SQLite, hosted security, PostgreSQL integration, and client workflow tests.

Switching to the new cookie name signs existing hosted sessions out once. No account
or catalog deletion is required. The existing hosted setup already creates the
`login_limits` table; verify it exists if deploying to a database initialized by a
different process. Database schema/bootstrap remains an administrator operation.

## Preview deployment only

Use the existing Vercel project **myselfpay-review** in **1smarterincs-projects**.
Do not create another project. `vercel.json` sets `github.autoAlias` to `false` so
GitHub merges create previews without automatically assigning the production alias.
No production promotion is part of the audit merge.

For an already linked Windows checkout:

```powershell
cd D:\SelfPay
git pull origin main
npx vercel deploy
```

Open the new Preview URL. Do not use `--prod` or `vercel promote` for this review.
Keep DATABASE_URL and all secrets out of GitHub. Preview environment settings must
point at the dedicated review database. Do not initialize/reset a populated database
just to deploy UI or security changes. Initial bootstrap is in `setup_hosted.py`; no review password is required for guest access.

## Checks

```powershell
py -3 -m unittest test_functional test_hosted test_cleanup -v
node test_ui.mjs
```

PostgreSQL tests require TEST_DATABASE_URL pointing at a disposable test database:

```powershell
py -3 -m unittest test_postgres -v
```

**The PostgreSQL suite drops and recreates its tables. Never run it against the
review or production database.** GitHub Actions uses a throwaway local PostgreSQL
instance. Local client tests use a stub transport, not a real browser.

After deployment, verify guest entry, refresh, sign-out, independent guest histories,
private-mode non-persistence, comparison, and provider links. Old conversation text
is historical; resuming searches reads current published data.

## Provider data and scope

The catalog is read from the active published database batch. Starting research has
44 directory entries and 13 mapped offers; entries may represent networks or programs,
not individual facilities. Fixed prices, starting prices, ranges, and quote-required
listings must stay distinct. Stage and review source/mapping updates before publication.
No evidence was freshly reverified as part of this code audit.

No claims/benefit calculations or insurance-versus-cash promises. OSI does not
guarantee prices, payment, appointments, or eligibility. Real member rollout still
needs operational, privacy, retention, abuse-control, and integration review.

## Retention schedule and remaining setup

`cleanup.py` reports counts by default; `--apply` deletes expired conversations,
sessions and old rate-limit buckets in one transaction. Live records are preserved.
The daily GitHub Actions schedule (03:17 UTC) runs independently of Vercel Preview.
Set repository Actions secret `SELFPAY_CLEANUP_DATABASE_URL` to the dedicated review
database connection string, then manually run **Daily retention cleanup** first with
apply=false and review counts, then with apply=true. No secret is supplied by this
commit, so live scheduled cleanup is NOT yet verified. No secret value belongs in code.
The workflow fails visibly if configuration is missing.

Expired guest identities/preferences and correction reports do not yet have a agreed
retention policy. This cleanup deliberately does not delete those or existing members.
Backups have their own retention. Session expiry is enforced by queries regardless
of whether scheduled deletion has run.

The frontend is one module (`static/app.js`); the overriding `functional.js` and
obsolete local-memory history implementation have been removed. Existing synthetic
accounts are only seeded if REVIEW_PASSWORD is explicitly configured; there is no
hardcoded default. Guest setup needs no credential configuration.
