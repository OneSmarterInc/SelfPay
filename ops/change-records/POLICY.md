# Live database change control
Effective 9 October 2026. Required by the project owner’s instructions.

## Mandatory rules
1. Do not execute any operational SQL against the live Neon database without a change record approved by Vikram first.
2. Commit every SQL file before live execution. The change record must identify its repository path and exact full commit SHA.
3. Test every proposed live change on a separate Neon branch copy first. Local SQLite, an unrelated PostgreSQL database, or a Vercel Preview sharing live Neon do not satisfy this requirement.

Read-only operational SELECT queries, dry runs, migrations, repairs, catalog publication, cleanup changes, role/grant changes and rollback scripts are included. There is no implied read-only or emergency exception. A request to prepare a change is not approval to execute that change.

This procedure governs developer/administrator operations and changes to automated database jobs. It does not instruct anyone to shut down the website or create a separate record for each normal member request. The approval scope for recurring operational jobs must be explicitly documented by Vikram; do not assume existing jobs are grandfathered in.

## Required sequence
1. Create a record from TEMPLATE.md; status DRAFT. Describe the target, purpose, risks and recovery.
2. Write SQL files for execution and verification (and rollback where applicable). Keep secrets and private data out of source control.
3. Commit SQL. Update the record with that exact commit SHA. A later record-only commit may reference the earlier SQL commit.
4. Verify a separate Neon branch copy and its endpoint. Record branch ID, parent, creation time and source state. Do not copy sensitive data to an unapproved destination.
5. Execute the exact committed SQL on the branch copy. Save sanitized results, assertions and rollback/recovery test evidence.
6. Present the concrete record, SQL commit and branch-test results to Vikram. Record his explicit approval evidence, scope and timestamp. Approval must exist before live SQL runs.
7. Immediately before live execution, verify the target and approved SQL version using approved procedures. If target state, SQL or scope changes, stop, retest and obtain renewed approval.
8. Authorized operator executes only the approved version. Record identity, UTC timestamp, result, approved verification output and recovery actions.
9. Close the record only when verification passes; otherwise mark FAILED/BLOCKED and follow the approved recovery plan.

Tests on a branch copy are mandatory but do not establish approval for live execution. Historical records 4.1–4.3 are retrospective evidence and cannot be used as advance approval.

## Pending historical evidence
Fresh live status() and pg_get_functiondef() queries in records 4.1 and 4.3 must follow this policy: committed query file, branch-copy test, and Vikram’s approval before execution. Leave pending until those steps are evidenced.

## Scope and enforcement
This is a repository operating policy, not a database permission barrier. A database owner may technically execute SQL outside it. Required-reviewer settings, identity mapping for Vikram, protected workflows and restricted credentials need separate configuration and verification before claiming technical enforcement.

Directory sync was manually disabled on 9 October 2026, with its enable variable observed unset. Keep it paused until an explicitly approved activation record covers the exact code/data, branch test and live operation. Do not delete roles, secrets or catalog data to implement this policy.

## Backup requirement (12 October 2026 implementation)
Vikram may waive the Neon copy test in writing. The waiver is quoted in the change record. A backup branch (section A of MySelfPay-backup-tasks.md) is still required. This is the only exception to the copy-test requirement above; it does not waive SQL review, change records or live approval.

Before every live write, create a data-and-schema branch from the verified live branch, named backup-YYYYMMDD-HHMM-<change> (UTC). Verify the backup catalog against live, record branch ID, parent, UTC creation time, exact query commit and counts. Use ops/sql/backup-catalog-counts.sql for independent branches: status() is live-target guarded. If creation or verification fails, stop; do not run the live write.

Retain backups for seven days; record any deletion. Never overwrite a backup with restore experiments. Daily exports must use the dedicated read-only role `selfpay_backup_reader`. Unencrypted SQL exports are permitted only while the synthetic-data checks in `ops/sql/backup-synthetic-check.sql` pass within the same snapshot as the dump. The only approved export destination is the private repository `OneSmarterInc/MySelfPay_Backup` (owner-selected name replacing SelfPay-backups). Verify repository privacy before export and before upload. Use a fine-grained `BACKUP_REPO_TOKEN` restricted to Contents read/write on that repository; the application workflow token has Contents read only.

Stop before pg_dump if any member has a tenant other than `guest`, any conversation exists, or any correction was created after 12 October 2026 (13 October 00:00 Asia/Kolkata). Print only the fixed non-synthetic-data stop message for this condition; never log records. Any real member data requires Vikram's written approval of a new destination and revised handling before exports resume. A `BACKUP_DATA_CLASS` variable alone is not evidence of synthetic data.

Exclude data (but preserve schema) for public.sessions, public.login_limits and public.guest_usage. Retain the newest 14 dated branches and the earliest available branch of each calendar month. Prune only validated parentless dump-only branches after a successful, verified upload; preserve other branches. Never overwrite an existing date branch. Restore a dump into an isolated Neon branch and test PITR monthly; record actual results, not just workflow configuration.


## Recorded one-day test-data exception

On 12 October 2026 at 19:34:50 Asia/Kolkata, Vikram explicitly waived the
branch test and approved that day's owner-classified test-data export to
MySelfPay_Backup. See 2026-10-12-one-time-test-backup.md for the exact quote,
failed structural preflight, scope and execution evidence. The manual exception
permits non-guest members and conversations only on 2026-10-12; the recent
corrections check, private destination, read-only role and exclusions remain.
This does not authorize recurring exceptions. BACKUPS_ENABLED remains false.
