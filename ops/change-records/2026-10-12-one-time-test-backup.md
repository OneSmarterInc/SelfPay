# October 12 one-time test-data backup

Status: PREPARED — live execution pending required Neon copy test or written waiver.

## Owner request

On 2026-10-12 (Asia/Kolkata), the owner corrected the earlier real-user statement:
"add todays data in md file the user is not real users", then requested:
"so do change and sva ethe todays backup".

This authorizes preparing a one-time backup of the owner-described test dataset
into private OneSmarterInc/MySelfPay_Backup. Classification is owner-provided,
not an independent review of every record. No real-data approval is inferred.

## Concrete change

Manual workflow input approved_test_backup_2026_10_12 enables a one-day exception
for non-guest accounts and conversations only on 2026-10-12 Asia/Kolkata.
The recent-correction stop condition still applies. Default and scheduled runs
retain the complete original guard. BACKUPS_ENABLED remains false.

Destination: private OneSmarterInc/MySelfPay_Backup, branch backup-2026-10-12,
one file database-2026-10-12.sql. Privacy is checked before export and upload.
Dedicated read-only role and TLS remain required. Session, login-limit and
guest-usage data remain excluded; their schemas are retained. Existing date
branches are never overwritten. No source database writes are performed.

## SQL and validation

No SQL is changed. Existing SQL files at commit
9ff7de313afe5641dc4ed54da021abe9fcbab893:
- ops/sql/backup-synthetic-check.sql
- ops/sql/backup-catalog-counts.sql

The export also retains its existing read-only role privilege check and
pg_export_snapshot() call. The guard, catalog counts and dump share one snapshot.
Local backup suite: 17 tests passed, including expiration, default denial and
recent-correction denial with the exception selected.

A separate Neon branch test of these operational checks is not yet recorded.
Under AGENTS.md and POLICY.md, the owner must explicitly waive that test in
writing if execution is to proceed without it. The request to save today's
backup is not recorded as such a waiver. No live export or restore success is
claimed. The earlier baseline branch remains retained.

## Risk and recovery

A mistaken test-data classification could place real data in the plain SQL file;
repository readers can read the dump. The exception expires after today.
On validation/export/publish failure, stop and report failure. The source is
read-only, so no source rollback is required. Do not overwrite an existing backup.
