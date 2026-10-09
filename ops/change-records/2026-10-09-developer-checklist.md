# Developer checklist completion evidence

User authorization: “do this remaing changes” after listing owner function/status capture, historical records, Preview protection, cleanup dry run, and quota reservation. Read-only capture only; no schema/catalog mutation authorized here. Earlier user-directed exception to Neon-copy testing persists for this work. No operator identity or historical approval will be invented.

SQL: ops/sql/capture-owner-evidence-2026-10-09.sql. Exact committed SQL: `6d7a441a3dd002efdf46a9de334f07eed0eb4ee0`. Query uses existing built-in PostgreSQL introspection and status function; no writes, secrets or member records.

Cleanup: manually run retention workflow with apply=false only. Do not trigger deletion.

Code: guest_agent now commits quota reservation before generation, outside the transaction lock. Rejected/expired sessions never invoke generation. Failed generation consumes the reserved attempt to prevent retry bypass. Tests cover reservation visibility, rejected calls, failed generation and existing concurrency limits.

Historical attribution may remain unresolved because publish_events does not store operator identity or approval. Fresh capture proves current state, not who performed earlier changes.

## Execution evidence

- Owner capture: 2026-10-09T12:20:02.57356+00:00, authenticated Vercel Storage Query, database role neondb_owner. SQL was committed and pinned before execution. No database writes performed in this capture.
- Current function body MD5: 4183e25660850bb8c572500b078f02d4, independently recomputed from pg_get_functiondef output.
- Current catalog: active batch 395c84be-d26d-5432-bddb-bff7c58c1200, 103 entries, 57 offers. Exact status is pasted into record 4.1; raw evidence and function definition are in ops/installed.
- Historical batch publication: publish_events row 5, 2026-10-08T07:54:16.523358+00:00, prior batch 51cbd230-d4a4-4e09-a580-06af8dc99776. Historical human operator and approval are not recorded there.
- Preview protection: project setting Require Log In enabled, Standard Protection selected, protecting all except production custom domains. No exception domains listed. Screenshot delivered to user. No protection settings changed.
- Combined requested test command: python -m unittest test_cleanup test_directory_sync -q — 54 tests passed.
- Quota tests plus cleanup/sync: 71 collected, passed with 8 PostgreSQL tests skipped locally. GitHub CI then passed SQLite, PostgreSQL, client and directory PostgreSQL tests: https://github.com/OneSmarterInc/SelfPay/actions/runs/37929252048 (commit 789478e6b4d644b9ada56c7498f83baefdf8f3c3).
- Manual retention dry run (apply unchecked/false): https://github.com/OneSmarterInc/SelfPay/actions/runs/37929614670 . Failed at Require dedicated database configuration. DATABASE_URL was empty; deletion and report steps were both skipped. Output: Configure SELFPAY_CLEANUP_DATABASE_URL for the dedicated review database. Exit code 1.
- GitHub Actions secret metadata confirms SELFPAY_CLEANUP_DATABASE_URL is absent from repository and environment secret lists. Only importer/directory secrets are listed. No secret values were read or copied. Do not substitute the owner/importer connection.

## Remaining owner actions

1. Configure repository Actions secret SELFPAY_CLEANUP_DATABASE_URL with the approved restricted selfpay_cleanup connection, entered securely outside chat. Then repeat the manual apply=false run and retain successful counts. No credential changes or live deletions were performed in this task.
2. Supply operator and original approver evidence for historical records 4.1–4.3, plus installation times for 4.2–4.3. Today's capture cannot reconstruct those facts.
3. Review PR #12 before merging; changes remain on fix/nearest-facility-checklist. No main push or production code deployment was performed.

Neon-copy testing was not represented as completed: the user explicitly requested direct Vercel Storage work instead of creating a copy. The exception is recorded, not treated as general repeal of future change-control policy.

