# Gitesh appointment test record — DRAFT

User requested Gitesh Imaging Center / giteshpawar880@gmail.com as a test destination. Store one synthetic entry in an inactive test batch, accessible only through /api/booking-test and /#booking-test. Never publish it in active search or coverage counts. No account or medical data is stored.

SQL: ops/sql/20261029-booking-test.sql; verification: ops/sql/20261029-booking-test-verify.sql; recovery: ops/sql/20261029-booking-test-disable.sql. Exact commit and isolated Neon results will be recorded before live approval. No production SQL has been executed for this change.

Expected: active batch directory-email-20261029, 2900 entries and 57 offers unchanged; one test entry in separate batch. Rollback retires that test batch without deleting data. A fresh verified backup and owner approval of the concrete SQL are required by POLICY.md before live execution. Keep directory sync and Actions billing unchanged.
