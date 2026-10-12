# October 12 SQL-dump restore preparation

Status: BLOCKED — saved restore URL targets live; refused before connection.

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

## Execution result — October 12, 2026

The owner saved RESTORE_DATABASE_URL at approximately 20:08 Asia/Kolkata and
reported done. Its presence was verified without reading its value.

- Run 38264664733 on main ba4edd504d9cf4d2692fdca23bcd35a54102f0b4 downloaded
  and verified the immutable dump; restore failed with the original redacted error.
- Run 38265000429 on 97a26c40390b2312832899dec5a2812298f5f221 isolated the
  failure to endpoint/TLS validation, before the connection stage.
- Run https://github.com/OneSmarterInc/SelfPay/actions/runs/38265344349,
  job 114865992886, code 5d700b665a891f77e5c304e2724b525449aa1d8d,
  reported at 2026-10-12T14:46:50.8024856Z:
  `Restore configuration: Live database endpoint refused`.
- The immutable source validation passed each time. No database connection or
  SQL restore was attempted by the diagnostic runs. No live write occurred.
- Temporary runner dump cleanup succeeded. No dump artifact was uploaded.

Next action: replace RESTORE_DATABASE_URL using the connection for branch
br-lively-recipe-b7948zn5 / dump-restore-20261012, database restore_20261012,
direct host ep-rough-sky-b78gwt56.c-13.us-east-1.aws.neon.tech, TLS enabled.
The user must securely enter/save the credential; never put it in this record.
Do not change expected target inputs to match a live URL or weaken the guard.
Re-run only after the correct disposable target credential is saved.

## Repository access verified

GitHub Manage access for private OneSmarterInc/MySelfPay_Backup showed zero
collaborators after secure owner reauthentication on October 12. Owner-only
human access is confirmed; no developer was invited. Token's repository-only
permission scope remains unverified.
