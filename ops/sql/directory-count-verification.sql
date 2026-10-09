-- DRAFT: copy test and approved change record required before live execution.
-- Catalog only; no member, session or preference content.
BEGIN TRANSACTION READ ONLY;
SELECT selfpay_directory_sync.status();
SELECT id, source_name, created, status, report FROM batches
WHERE id = (SELECT value FROM settings WHERE key = 'active_batch');
SELECT id, entry_key, price_type FROM offers
WHERE batch_id = (SELECT value FROM settings WHERE key = 'active_batch')
ORDER BY id;
ROLLBACK;
