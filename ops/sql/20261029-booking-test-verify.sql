SELECT (SELECT value FROM public.settings WHERE key='active_batch') AS active_batch,
(SELECT count(*) FROM public.entries WHERE batch_id=(SELECT value FROM public.settings WHERE key='active_batch')) AS active_entries,
(SELECT count(*) FROM public.offers WHERE batch_id=(SELECT value FROM public.settings WHERE key='active_batch')) AS active_offers,
(SELECT count(*) FROM public.entries WHERE batch_id='booking-test-20261029' AND entry_key='gitesh-test' AND (payload::jsonb->>'test_only')::boolean) AS test_entries,
(SELECT status FROM public.batches WHERE id='booking-test-20261029') AS test_status;
