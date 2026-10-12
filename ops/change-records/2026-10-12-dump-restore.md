# October 12 SQL-dump restore preparation

Status: READY FOR RESTORE CREDENTIAL; actual restore unperformed.

The owner requested completion of the remaining developer tasks. This record
covers only a disposable Neon target and the existing approved private dump.
No live database SQL or production deployment is authorized by this record.

## Immutable source

Repository OneSmarterInc/MySelfPay_Backup, branch backup-2026-10-12,
commit 892343ff15544204a5fab6fecb7369f255af35f9, file database-2026-10-12.sql.
The workflow requires this exact commit, a parentless history and exactly one
dated SQL file. It verifies repository privacy before download and never uploads
the dump as an Actions artifact or prints its rows.

## Target created October 12

- Project late-grass-13270808 / myselfpay-review, PostgreSQL 18.
- Branch dump-restore-20261012 / br-lively-recipe-b7948zn5.
- Parent main / br-rapid-mouse-b7clh18t; independent clone.
- Created 2026-10-12 14:25:39Z (19:55:39 Asia/Kolkata).
- Auto-expires 2026-10-13 14:25:39Z; this is a disposable test, not the retained baseline.
- Compute ep-rough-sky-b78gwt56; direct host
  ep-rough-sky-b78gwt56.c-13.us-east-1.aws.neon.tech.
- New database restore_20261012, owner neondb_owner, visibly created on this
  branch. The existing cloned neondb is not the restore target.
- Schema-only creation failed because Neon reports a legacy web-access role.
  No role was changed. A normal branch plus a new database avoids deleting data.

## Execution and verification

Save the target-only connection URL as RESTORE_DATABASE_URL in SelfPay's
database-backups environment. Use the direct endpoint and restore_20261012,
with TLS; never use the live URL or the read-only backup role. Do not place the
credential in this record. If the branch expires, create and verify a new
disposable target and update the workflow inputs and secret.

Run Verify SQL backup restore from main with the source and target inputs above.
The verifier checks the server's branch ID, rejects live/pooled endpoints,
requires zero non-system tables, restores transactionally, compares all six
catalog fields against the dump snapshot, and checks sessions, login_limits and
guest_usage exist with zero rows. Failures are redacted; no data is deleted to
force a retry. Record the actual run and results here before claiming success.

Monthly restore/PITR testing still needs target provisioning and credentials.
The manual workflow alone is not a monthly schedule or a successful drill.
Retain baseline br-gentle-moon-b74wdsig until at least 2026-10-19 08:46:32Z.
Review old test-branch dependencies after that time before any cleanup.
