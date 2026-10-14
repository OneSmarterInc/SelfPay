# Remove identified legacy test rows — October 14, 2026

Status: DRAFT — NOT APPROVED, NOT EXECUTED. Daily backups remain disabled.

Requested by MySelfPay-dev-tasks-2026-10-14.md section C. This record lists IDs only.
Source: already-existing October 12 snapshot, app-repo commit 63071bc9f7b756cef4a2ba7a44fdcbbf87177939.
No fresh live SQL was run. Snapshot IDs are evidence of October 12 state, not current state.

## Proposed scope

### conversations

- ae0db782-c14a-4058-a90d-1fc35f089808
- 45dc013c-7da4-4912-8c3f-2a17baf3b210
- bff688e0-cc2c-40f4-98db-3b3fa9403d17
- 3e703856-c363-4a12-980b-5109ef7f552a
- d7e2f4f2-3c65-497f-906a-6892e73a0325
- ff737275-12ff-4489-9411-72300492f6f2

### corrections

- cfb1605f7d3a9e0c6ab8e451

### members

- f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51
- 12dca885-1548-43d2-b219-46d04095c26e
- 24651e6b-7cf9-43b5-8b90-6a521679c6a7
- bcd03d50-9604-43a7-be0b-5f1ec5594794

### preferences

- f8f89ee1-66e7-4e42-a848-ca3d6e4f5c51

## Exact change and gates

SQL: `ops/sql/remove-test-members-2026-10-14.sql`; full SQL commit: 4b9fd22e30062c815ea8f4d613ce428eee484146.
The transaction locks related tables, requires exact counts and expected IDs, refuses
additional session/guest-usage dependencies, deletes only the listed rows, and
rolls back unless the synthetic guard passes. No names, emails, password hashes or
message content are emitted. Unknown related data requires a revised review.

Required before execution under POLICY.md: current target verification through an
approved procedure; data-and-schema backup branch and count verification; separate
Neon-copy test or explicit owner waiver; owner approval of the exact committed SQL.
None of those execution gates is claimed complete. No PostgreSQL execution test
has been performed locally. This draft must not be executed as-is without those gates.

Recovery: use the independently verified pre-write backup; the October 12 dump
alone is not a current recovery point. Data deletion is permanent on the live branch.
After approved execution, run committed `ops/sql/backup-synthetic-check.sql` and
record all three false results. Enable recurring exports only after approved
activation covers the recurring job and snapshot guard. Never bypass the guard.
