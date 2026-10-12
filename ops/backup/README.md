# Daily encrypted dump branches

Current user instruction (12 October 2026) supersedes the earlier Blob destination: create one Git branch per day containing only that day's encrypted database dump.

Example: branch `backup-2026-10-12` contains exactly `database-2026-10-12.dump.age`. It is a parentless commit with no application files/history, README or extra manifest. The file is an age-encrypted PostgreSQL custom-format dump. Branch dates use Asia/Kolkata at backup start. Schedule: 02:30 UTC / 08:00 India daily; scheduler delays can occur. A rerun fails if that day's branch already exists, preserving the first successful backup. Failure never produces an empty backup branch. No automatic branch deletion is enabled.

## Activation still required
In GitHub environment `database-backups` configure:
- Secret BACKUP_DATABASE_URL: approved dedicated selfpay_backup_reader direct Neon connection with TLS.
- Variable BACKUP_EXPECTED_HOST: exact approved live direct host.
- Variable BACKUP_AGE_RECIPIENT: age public encryption key.
- Variable BACKUP_DATA_CLASS: synthetic, after confirming no real member data is present.

Generate the age key on the owner's machine with age-keygen and retain its private key in the owner's recovery vault, outside this repository. Only the public recipient goes into GitHub. New login/password setup requires secure operator entry, never chat. The read-only role preparation remains subject to the documented branch test, fresh backup and live SQL approval.

No Blob store/token or personal GitHub token is needed. The workflow uses its short-lived GITHUB_TOKEN with contents:write. Merge the reviewed workflow into the default branch, then set repository variable BACKUPS_ENABLED=true and manually dispatch the first run. Scheduled jobs require the default-branch workflow. Until credentials and key are supplied, this is prepared code, not a working daily backup.

## Recovery
Check out/download the single encrypted file from the desired date branch. On an authorized machine:
```sh
age -d -i /secure/backup-key.txt -o database.dump database-2026-10-12.dump.age
pg_restore --list database.dump
```
Restore only into a verified empty test database with PostgreSQL 18 pg_restore --exit-on-error --single-transaction --no-owner --no-acl, passing its connection securely through PGDATABASE. Verify catalog counts and record the result. This revised dump-only format has no separate manifest. Never restore directly to live as a test.

The isolated Neon PITR drill passed on 12 October; encrypted dump restoration is still unverified. This workflow does not automate monthly recovery.

## Limits and validation
Encrypted files must be under 95 MiB; larger dumps fail safely before branch creation. Git is not unlimited backup storage. Branch deletion does not guarantee immediate erasure of underlying Git objects. A different destination is required if strict deletion/large-file requirements arise.

Tests cover India date rollover, a real local parentless Git commit containing exactly one ciphertext fixture, and plaintext rejection. They do not claim a real live export/encryption/remote push succeeded. Previous Blob helper files are obsolete and unused by this workflow.
