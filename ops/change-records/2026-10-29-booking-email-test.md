# Gitesh appointment test record — DRAFT

User requested Gitesh Imaging Center / giteshpawar880@gmail.com as a test destination. Store one synthetic entry in an inactive test batch, accessible only through /api/booking-test and /#booking-test. Never publish it in active search or coverage counts. No account or medical data is stored.

SQL: ops/sql/20261029-booking-test.sql; verification: ops/sql/20261029-booking-test-verify.sql; recovery: ops/sql/20261029-booking-test-disable.sql. Exact commit and isolated Neon results will be recorded before live approval. No production SQL has been executed for this change.

Expected: active batch directory-email-20261029, 2900 entries and 57 offers unchanged; one test entry in separate batch. Rollback retires that test batch without deleting data. A fresh verified backup and owner approval of the concrete SQL are required by POLICY.md before live execution. Keep directory sync and Actions billing unchanged.

## Committed SQL and rehearsal evidence
SQL commit: bcb00bc70370c50079603c5f77dd24457c986ecd (all three SQL files above).
Project: late-grass-13270808. Isolated branch br-frosty-credit-b7kg7hpl, parent br-rapid-mouse-b7clh18t, created 2026-10-29T10:55:16Z, parent LSN 0/4EA8A00.
Exact committed insertion and verification succeeded: active batch directory-email-20261029, active entries 2900, active offers 57, test entries 1, test status test. Exact disable SQL and verification succeeded: test status retired, test entry retained, same active batch/counts. Production remains untouched.

Requested approval scope: the exact insertion, verification, and emergency disable SQL above on production; pre-write target/count verification and fresh backup creation/verification using ops/sql/backup-catalog-counts.sql. Preserve seven days. Do not publish the test batch or modify active directory/user data. Approval pending after presenting this concrete record.
