-- Read-only boolean checks, executed in the export snapshot before pg_dump.
-- "After Oct 12" means Oct 13 00:00 Asia/Kolkata (Oct 12 18:30 UTC).
-- created is Unix seconds, matching core.py and the PostgreSQL schema.
SELECT EXISTS (SELECT 1 FROM public.members WHERE tenant IS DISTINCT FROM 'guest'),
       EXISTS (SELECT 1 FROM public.conversations),
       EXISTS (SELECT 1 FROM public.corrections WHERE created >= 1791829800);
