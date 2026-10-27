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
