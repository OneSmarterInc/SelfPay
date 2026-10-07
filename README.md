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
74 directory entries and 57 mapped offers; entries may represent networks or programs,
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

## October 5 provider directory update

The bundle contains 74 researched directory entries and 57 MRI/CT offers. All 44 previous entries are retained. New quote-required and facility-only estimate listings preserve their original wording and are not displayed as all-in fixed prices. Other imaging is visible in the directory, not enabled as a search modality. Location suggestions come from the published catalog; ZIP/distance matching remains unavailable.

To publish to the existing review database from Windows (DATABASE_URL in .env.local):

```powershell
cd D:\SelfPay
py -3 -m pip install -r requirements.txt python-dotenv
py -3 publish_directory.py
py -3 publish_directory.py --apply
```

The first command stages and validates; the second publishes only if all 74 entries and 57 mapped offers pass. Save the printed previous_batch identifier for rollback through core.publish. This does not reset guests, sessions, history or preferences. Use a dedicated Preview database: publishing to a database shared with Production changes its data too, even without promoting a deployment.

Review: Browse directory should show 74 entries. Search MRI / Knee / Dayton, OH for quote-required options; MRI / Knee / Seminole, FL for fixed contrast variants; MRI / Brain / Hilo, HI for the facility-only estimate wording and quote-required label. Hilo's brain offer must not appear for Knee.

### Global guest creation limits

New guest identities are limited across all IPs and workers sharing the database:
100 per UTC clock minute and 1,000 per UTC calendar day by default. Set positive
integer server variables GUEST_GLOBAL_PER_MINUTE / GUEST_GLOBAL_PER_DAY to adjust.
These are fixed windows, not rolling windows. The existing 20/minute per-IP
request limit remains. Existing guest sessions do not consume global admissions.
At capacity the API returns 429 with Retry-After and an explanation shown by the
existing sign-in error handler. Database errors fail closed.

One settings row (guest_creation_quota) holds both counters; row locking and guest
creation share a transaction, so concurrent workers cannot overshoot and failed
account creation does not consume quota. No schema migration, reset, or historical
member deletion is needed. Counters start at first use after deployment; they do
not retrospectively count accounts made before the feature. Do not delete the
quota settings row during retention cleanup. Environments sharing a database also
share these limits. Per-guest conversation storage limits are a separate control.

### Guest retention cleanup

The existing cleanup command and scheduled job now remove guest members only when no session has expires > cleanup time and no conversation has expires > cleanup time. Expired sessions/conversations are removed first, followed by eligible guests' preferences, corrections and member rows. Registered members are preserved. Pending correction reports belonging to deleted guests are deleted as requested.

Dry-run remains the default and reports guest_members, preferences and corrections counts as well as existing expiry counts. --apply performs deletion in one transaction. PostgreSQL table write locks (reads remain available) and SQLite BEGIN IMMEDIATE prevent concurrent writes from invalidating eligibility; run during a quiet period for larger databases. No schema migration is required. Scheduled execution still requires SELFPAY_CLEANUP_DATABASE_URL to be configured; a code merge alone does not establish successful scheduled operation. Backup retention is separate.
