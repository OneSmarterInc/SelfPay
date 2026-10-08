-- One-time administrator migration. No catalog rows or permissions are changed.
-- Allows only the exact reviewed recovery bundle in dry-run mode.
-- Fails closed if the installed function or database snapshot has changed.
BEGIN;
SET LOCAL search_path = pg_catalog;
SET LOCAL lock_timeout = '10s';
DO $repair$
DECLARE definition text; source text; snapshot jsonb;
BEGIN
  PERFORM selfpay_directory_sync.check_target();
  PERFORM pg_catalog.pg_advisory_xact_lock(734512, 20261007);
  LOCK TABLE public.entries, public.offers IN SHARE MODE;
  PERFORM value FROM public.settings WHERE key = 'active_batch' FOR UPDATE;
  snapshot := selfpay_directory_sync.status();
  IF snapshot->>'active_batch' IS DISTINCT FROM 'b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4'
     OR snapshot->>'entry_fingerprint' IS DISTINCT FROM 'dfafa355ca7c65ceb1dc743eccb25f6fcc9efa11e124004e90db168794b99b03'
     OR snapshot->>'offer_fingerprint' IS DISTINCT FROM '2a3b5859b77acfcd406614c7d2f3c49d2a4d9877edd2ea4c957067c0956976cd'
     OR snapshot->>'entry_count' IS DISTINCT FROM '99'
     OR snapshot->>'offer_count' IS DISTINCT FROM '13'
     OR snapshot->'source' IS DISTINCT FROM 'null'::jsonb THEN
    RAISE EXCEPTION 'directory repair: current snapshot differs from reviewed snapshot';
  END IF;
  SELECT p.prosrc, pg_catalog.pg_get_functiondef(p.oid)
    INTO source, definition FROM pg_catalog.pg_proc p
    WHERE p.oid = 'selfpay_directory_sync.apply_bundle(text,text,boolean)'::regprocedure;
  IF pg_catalog.md5(source) IS DISTINCT FROM '70f1d03162f796d53ea896783c2fe8f3' THEN
    RAISE EXCEPTION 'directory repair: installed function differs from reviewed definition';
  END IF;
  definition := pg_catalog.replace(definition, $old$  IF bootstrap THEN
    IF prior <> '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f' THEN
      RAISE EXCEPTION 'directory sync: bootstrap requires the reviewed active batch';
    END IF;
    IF (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) ORDER BY e.entry_key)::text, '[]'))
          FROM public.entries e WHERE e.batch_id = prior) <> 'be0290bd19eff19066766e8644245122'
       OR (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o) ORDER BY o.id)::text, '[]'))
          FROM public.offers o WHERE o.batch_id = prior) <> '711a7c77b51e6107e7d7326229366a4b' THEN
      RAISE EXCEPTION 'directory sync: reviewed bootstrap full-row fingerprint mismatch';
    END IF;
$old$, $new$  IF bootstrap AND prior = 'b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4' THEN
    -- Reviewed recovery snapshot only. This is not workbook provenance approval.
    IF dry_run IS DISTINCT FROM true THEN
      RAISE EXCEPTION 'directory sync: reviewed recovery snapshot is dry-run only';
    END IF;
    IF document_hash IS DISTINCT FROM '12465eed327e464e8f022085e8e1e427dd13d3d7206234c2fa275d94e3a08b51'
       OR selfpay_directory_sync.catalog_fingerprints(prior) IS DISTINCT FROM
          '{"entry_fingerprint":"dfafa355ca7c65ceb1dc743eccb25f6fcc9efa11e124004e90db168794b99b03","offer_fingerprint":"2a3b5859b77acfcd406614c7d2f3c49d2a4d9877edd2ea4c957067c0956976cd"}'::jsonb
       OR (SELECT count(*) FROM public.entries WHERE batch_id = prior) <> 99
       OR (SELECT count(*) FROM public.offers WHERE batch_id = prior) <> 13 THEN
      RAISE EXCEPTION 'directory sync: reviewed recovery snapshot mismatch';
    END IF;
  ELSIF bootstrap THEN
    IF prior <> '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f' THEN
      RAISE EXCEPTION 'directory sync: bootstrap requires the reviewed active batch';
    END IF;
    IF (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) ORDER BY e.entry_key)::text, '[]'))
          FROM public.entries e WHERE e.batch_id = prior) <> 'be0290bd19eff19066766e8644245122'
       OR (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o) ORDER BY o.id)::text, '[]'))
          FROM public.offers o WHERE o.batch_id = prior) <> '711a7c77b51e6107e7d7326229366a4b' THEN
      RAISE EXCEPTION 'directory sync: reviewed bootstrap full-row fingerprint mismatch';
    END IF;
$new$);
  EXECUTE definition;
END
$repair$;
DO $verify_repair$
DECLARE before_state jsonb; outcome jsonb; reviewed_document text;
BEGIN
  before_state := selfpay_directory_sync.status();
  SELECT '{"entries":[' || pg_catalog.string_agg(
    selfpay_directory_sync.canonical_strings(pg_catalog.jsonb_build_object(
      'content', selfpay_directory_sync.canonical_strings(e.payload::jsonb - 'row'),
      'content_hash', e.content_hash, 'entry_key', e.entry_key, 'payload', e.payload)),
    ',' ORDER BY e.entry_key COLLATE "C") || '],"schema_version":1,"source":{"exported_at":"2026-10-07T10:28:42Z","library_file_id":"libfile_8ba8491c8ff881918ed4868c0ee43465","sha256":"e60778bb503442e40ce035fdf70958db65ca1d710ce0279b06c2bcea8bd42a96","version":7},"target":{"database":"neondb","neon_branch_id":"br-rapid-mouse-b7clh18t"}}' || pg_catalog.chr(10)
    INTO reviewed_document
    FROM public.entries e WHERE e.batch_id = 'b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4';
  outcome := selfpay_directory_sync.apply_bundle(reviewed_document, 'b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4', true);
  IF outcome->>'dry_run' IS DISTINCT FROM 'true'
     OR outcome->>'entry_count' IS DISTINCT FROM '99'
     OR outcome->>'offer_count' IS DISTINCT FROM '13'
     OR outcome->>'added' IS DISTINCT FROM '0'
     OR selfpay_directory_sync.status() IS DISTINCT FROM before_state THEN
    RAISE EXCEPTION 'directory repair: dry-run verification failed';
  END IF;
END
$verify_repair$;
COMMIT;
SELECT 'Dry-run repair installed and verified; publishing remains blocked' AS result;
