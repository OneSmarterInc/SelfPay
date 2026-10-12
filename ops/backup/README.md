# Daily SQL dump branches

The user's latest instruction on 12 October 2026 explicitly removes encryption. This supersedes earlier age/Blob setup instructions for daily Git backups.

Branch `backup-YYYY-MM-DD` contains only `database-YYYY-MM-DD.sql`, an unencrypted PostgreSQL plain SQL dump. Each branch has a parentless commit with no application files/history. It exports all accessible database schema and data without table filters. Ownership and ACL restoration are excluded; server-level roles, passwords and files outside this database are not included. Export failure prevents publication.

Date uses India time at job start; scheduled daily at 08:00 IST. Existing date branches are never overwritten. No automated deletion is enabled. Repository readers can read the entire dump.

## Setup still pending
GitHub environment `database-backups`:
- Secret BACKUP_DATABASE_URL: dedicated selfpay_backup_reader direct Neon URL with TLS.
- Variable BACKUP_EXPECTED_HOST: exact approved direct live host.
- Variable BACKUP_DATA_CLASS: synthetic, after confirming data classification.

Set repository variable BACKUPS_ENABLED=true only after credentials, access review and successful first test. Workflow must be merged onto the default branch for the daily schedule. No encryption key, Blob store or personal GitHub token is required; the workflow uses GITHUB_TOKEN.

## Restore
Use PostgreSQL 18 psql against a verified empty test database:
```sh
psql -X --set=ON_ERROR_STOP=1 --single-transaction --file=database-2026-10-12.sql
```
Supply the target through secure PG* environment variables. Verify counts and record actual results. Never use live for a restore test.

## Validation and status
Local tests cover date rollover, parentless one-file branch construction and invalid-dump rejection. Dumps must be under 95 MiB and have PostgreSQL header/completion markers; these markers are structural checks, not proof of recoverability. End-to-end export and SQL restore have not run. Prior Neon PITR test is separate and passed. Old Blob helper files are unused. Today's real Git dump branch is still pending a working direct database connection.
