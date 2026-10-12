-- Catalog-only verification; valid on live and independent backup branches.
BEGIN TRANSACTION READ ONLY;
WITH active AS (SELECT value AS id FROM public.settings WHERE key='active_batch'),
e AS (SELECT payload::jsonb AS p FROM public.entries WHERE batch_id=(SELECT id FROM active))
SELECT (SELECT id FROM active) AS active_batch,
 (SELECT count(*) FROM e) AS entries,
 (SELECT count(*) FROM public.offers WHERE batch_id=(SELECT id FROM active)) AS offers,
 (SELECT count(*) FROM e WHERE jsonb_array_length(COALESCE(p->'locations','[]'::jsonb))>0) AS located_entries,
 (SELECT COALESCE(sum(jsonb_array_length(COALESCE(p->'locations','[]'::jsonb))),0) FROM e) AS locations,
 (SELECT count(*) FROM e WHERE p->>'location_type'='program') AS programs;
ROLLBACK;
