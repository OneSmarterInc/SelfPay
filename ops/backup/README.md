# Encrypted daily backups — setup pending

The workflow is prepared, not activated or proven. Neon console access does not give GitHub Actions a database credential or private Blob token. PR #15 must be merged before scheduled runs execute.

## Configure before activation

1. Create a **dedicated private Vercel Blob store** for synthetic backups outside Neon. Do not reuse a public uploads store. Record store ID, owner and region in the change record. No destination has been provisioned or approved for real member data.
2. Create a dedicated `selfpay_backup_reader` login in `neondb`, with only CONNECT and read access (PostgreSQL's `pg_read_all_data` role is suitable after reviewing schema/RLS requirements). No ownership, write grants, role administration, BYPASSRLS or schema creation. Audit inherited/PUBLIC privileges. Use a new verified backup, committed exact SQL, branch test and owner approval for role changes; this document is not execution approval. Set the password securely outside chat.
3. Create the `database-backups` GitHub environment. Add secrets `BACKUP_DATABASE_URL` (direct, non-pooler connection for that reader with TLS) and `BLOB_READ_WRITE_TOKEN` (only the dedicated private store). Set environment variables `BACKUP_EXPECTED_HOST` (approved direct live host), `BACKUP_DATA_CLASS=synthetic`, `BACKUP_AGE_RECIPIENT` (age public key).
4. Generate an age key with `age-keygen` on an authorized operator's machine. Retain the private key in the owner's secure recovery vault; never commit it or put it into this export workflow. Prove the key can decrypt a test before relying on it.
5. Approve recurring read-only exports and 14-day deletions under POLICY.md. Set repository variable `BACKUPS_ENABLED=true` only after configuration, synthetic-only attestation and review. Manual dispatch first; inspect successful encrypted upload and read-back verification. Daily schedule: 02:30 UTC / 08:00 India.

Missing configuration fails the run; a disabled workflow is not a successful backup. GitHub run failures must be monitored by the owner. Plaintext exists only in a restricted temporary directory and is removed on completion/failure; no dump is published as an Actions artifact. Database and SDK error detail is suppressed to avoid leaking credentials. Failed upload/verification never initiates retention cleanup. Cleanup is restricted to the job's exact namespace and server upload age; service outages may delay deletion beyond 14 days and require follow-up.

## Monthly recovery procedure (not yet executed)

On the first working day each month, use the prior night's successful object from the private store. Record object pathname, UTC upload time and checksum. Download privately, decrypt using `age -d -i <private-key-file>`, and extract the two expected files (`database.dump`, `manifest.json`) into a private temporary directory. Validate the dump SHA-256 against the encrypted manifest.

Create a new isolated Neon branch for the drill. Verify its ID and endpoint differ from both live and retained backups. Restore into an empty test database using PostgreSQL 18 `pg_restore --exit-on-error --single-transaction --no-owner --no-acl`; provide the target connection through secure environment variables, not command-line literals. Do not use `--clean` against a nonempty/live database. Some Neon-managed schemas/extensions may require documented handling: fail and investigate, never ignore restore errors.

Run `ops/sql/backup-catalog-counts.sql` on the restored database and compare every value with `manifest.json`, which shares the dump's exported snapshot. Record actual results and recovery duration. Today's changing live counts are not the baseline for yesterday's dump.

Separately test Neon point-in-time restore on a disposable test branch: record a restore point, make a uniquely named test marker on that branch only, restore that same test branch to the recorded point, confirm the marker disappeared and catalog counts remain correct. Never rewind live or a retained backup for a drill.

Record both tests in `ops/change-records`, including failure details. Monthly automation is pending secure restore credentials and an approved recovery runner; this runbook alone does not schedule or prove it. The first dump cannot be called "last night's" until one exists from the previous night.

## Branch retention

Keep pre-change backups seven days. Record branch name, ID, UTC creation, verified counts and scheduled deletion time. Delete only the exact expired backup after checking dependencies and recording the deletion. Current baseline `br-gentle-moon-b74wdsig` has no automatic expiry; earliest cleanup is 2026-10-19T08:46:32Z. No branch deletion has been scheduled by these files.

## Validation and limitations

Local syntax checks and retention boundary tests are available. PostgreSQL/age integration tests have not been run in this environment. End-to-end export, private upload and dump restore remain unverified until the configured workflow and recovery drill succeed. Logical dumps omit cluster roles and are not continuous PITR; record required roles/extensions separately when planning a full service recovery.
