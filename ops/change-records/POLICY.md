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

Retain backups for seven days; record any deletion. Never overwrite a backup with restore experiments. Daily exports must use a dedicated read-only role, encryption and private storage outside Neon with fourteen-day retention. Before real member data, Vikram must approve the destination. Restore a dump into an isolated branch and test PITR monthly; record actual results, not just workflow configuration.
