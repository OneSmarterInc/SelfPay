# October 27 directory import — preflight

Status: DRAFT; live approval pending. No live SQL executed.

User requested adding uploaded workbook data. Add-only scope: preserve all existing records and offers; no deletion or overwrite. Automatic directory sync remains paused.

Workbook SHA256: 2d2c707cbe103642c7f0a86151b0f844cccda896ebc979c04cf18370e85e1ea3.
Workbook: 182 entries; no duplicate case-insensitive names.
Compared only with existing isolated branch br-falling-violet-b7u7wu0m (test-directory-import-20261018), parent br-rapid-mouse-b7clh18t, copied 2026-10-18T09:30:09Z. 152 active entries; 30 new candidates. This is NOT a fresh live comparison.
Two existing records differ: Compass Peak Imaging and Nashville Healthcare Diagnostic Imaging; excluded from add-only updates.

Target project: late-grass-13270808, database neondb, live branch br-rapid-mouse-b7clh18t.

Requested next approval: execute ONLY ops/sql/20261027-directory-inventory.sql against live to compare public directory payloads and hashes. This SELECT does not access members, sessions, credentials, or conversations. Exact SQL commit and isolated test evidence will be appended after commit/testing.

No write SQL is approved. Import SQL, location/offer mapping review, current-copy rehearsal, backup creation/verification and final live write approval remain pending. New workbook prices are source text, not automatically validated offers. Keep production, Vercel, website code, and billing unchanged.

## Committed preflight and test evidence
SQL commit: 3ab59c43ffd50e82c5ea4dd26e94eb51d0d045d6
Exact committed SELECT tested on br-falling-violet-b7u7wu0m on 2026-10-27; succeeded, 152 rows returned. No writes performed. Test branch is historical and cannot prove current live contents.
Live approval remains PENDING. Approval requested only for the exact read-only directory inventory SQL above; it does not authorize publication.

## Owner response and live comparison — 2026-10-27
Owner replied: "you have approval add data in database". The previously presented read-only SQL was executed against the specified live branch. It returned 152 rows in directory-additions-20261018. All 30 candidate names are absent. No live writes have occurred.

## Exact write package and successful rehearsal
SQL commit: e84c57dc34416344f9dbd5fc2ba5f80de3c9f6f7
- ops/sql/20261027-directory-apply.sql
- ops/sql/20261027-directory-verify.sql
- ops/sql/20261027-directory-rollback.sql

Fresh isolated copy: br-broad-block-b7rhjuck (test-directory-import-20261027), parent br-rapid-mouse-b7clh18t, created 2026-10-27T16:57:42Z, source LSN 0/3EE2CB8. Existing Neon organization reports plan free. No billing settings changed. First create attempt specifying suspend interval was rejected; retry with account defaults succeeded.

Exact apply SQL succeeded on the copy. Verification: active batch directory-additions-20261027; 182 entries; 57 offers; changed_existing=0; missing_or_changed_offers=0. Exact rollback SQL then succeeded. Committed inventory query confirmed active batch directory-additions-20261018 with 152 entries. Test import batch retained for audit; no rows deleted.

Scope limitation: new listings retain complete workbook text, sources and dates but have unresolved coordinates and no new comparable price-offer mappings. Existing 57 mapped offers remain unchanged. Add-only scope excludes the two changed existing records.

Status: TESTED; waiting for approval of this now-concrete SQL commit before live write, as POLICY.md requires approval after branch testing. Immediately before any live write, create and independently verify a seven-day backup branch under policy; abort if backup fails or live baseline differs. Automatic directory sync stays paused; no website/Vercel/billing changes.

## Live execution approval
2026-10-27: owner replied "update in production" after presentation of tested SQL commit e84c57dc34416344f9dbd5fc2ba5f80de3c9f6f7. Approved scope: exact add-only import and verification, with required backup check and guarded rollback on failure. Execution pending backup verification.

## Production execution completed — 2026-10-27
Status: COMPLETED; database verification passed.
Recovery backup: br-fragrant-frog-b7nxnggh, name backup-20261027-1701-directory-import; parent br-rapid-mouse-b7clh18t; created 2026-10-27T17:02:27Z; parent LSN 0/3EE3390. Retain at least through 2026-11-03T17:02:27Z. No automatic deletion scheduled.
The committed ops/sql/backup-catalog-counts.sql was tested on the isolated copy and executed on live and backup as separate statements in a transaction (comments excluded). Both matched: active directory-additions-20261018, 152 entries, 57 offers, 145 located entries, 179 locations, 7 programs. Initial tool attempts rejected multiple prepared statements / a comment split; no mutations occurred in those checks.
Executed exact approved apply SQL from e84c57dc34416344f9dbd5fc2ba5f80de3c9f6f7 against late-grass-13270808 / br-rapid-mouse-b7clh18t / neondb using authorized Neon tool. Transaction succeeded.
Exact approved verification returned: active directory-additions-20261027; entries 182; offers 57; changed_existing 0; missing_or_changed_offers 0.
30 directory listings added. Prior batch retained. Existing records and offers unchanged. No new mapped price offers or coordinates added. No application code, Vercel deployment, credentials, billing, GitHub Actions budget or sync activation changed. Database verified; no physical mobile-device test performed.
