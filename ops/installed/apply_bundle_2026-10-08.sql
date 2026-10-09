-- Function body MD5 (pg_proc.prosrc): 4183e25660850bb8c572500b078f02d4
-- Historical evidence: user-supplied Pasted text(3).txt, supplied 2026-10-08.
-- Archived 2026-10-09; NOT a fresh database query or permission to execute.
-- MD5 identifies the function body, not this entire file.
CREATE OR REPLACE FUNCTION selfpay_directory_sync.apply_bundle(raw_document text, expected_active text, dry_run boolean DEFAULT true)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
<<guarded>>
DECLARE
  doc jsonb; src jsonb; entry jsonb; payload jsonb; content jsonb; fingerprints jsonb;
  payload_text text; content_text text; entry_name text; entry_key text;
  prior text; next_batch text; document_hash text; source_version bigint;
  exported_at timestamptz; checked_date date; old_count integer; new_count integer;
  offer_count integer; added integer; bootstrap boolean; result jsonb;
  seen_keys text[] := ARRAY[]::text[]; seen_names text[] := ARRAY[]::text[];
  required_keys text[] := ARRAY['row','name','area','states','entity','category','mri',
    'ct','other','coverage','notes','source','additional','checked'];
  latest selfpay_directory_sync.import_ledger%ROWTYPE;
BEGIN
  PERFORM selfpay_directory_sync.check_target();
  IF dry_run IS NULL OR expected_active IS NULL OR expected_active = '' THEN
    RAISE EXCEPTION 'directory sync: explicit expected active batch and dry-run flag required';
  END IF;
  IF raw_document IS NULL OR pg_catalog.octet_length(raw_document) > 5242880 THEN
    RAISE EXCEPTION 'directory sync: missing or oversized document';
  END IF;
  IF NOT selfpay_directory_sync.unique_json_keys(raw_document::json) THEN
    RAISE EXCEPTION 'directory sync: duplicate JSON object keys rejected';
  END IF;
  doc := raw_document::jsonb;
  IF pg_catalog.jsonb_typeof(doc) IS DISTINCT FROM 'object'
     OR doc - ARRAY['schema_version','source','target','entries'] <> '{}'::jsonb
     OR NOT doc ?& ARRAY['schema_version','source','target','entries']
     OR doc->'schema_version' IS DISTINCT FROM '1'::jsonb THEN
    RAISE EXCEPTION 'directory sync: invalid document schema; offers are never accepted';
  END IF;
  IF pg_catalog.jsonb_typeof(doc->'target') IS DISTINCT FROM 'object'
     OR doc->'target' IS DISTINCT FROM '{"database":"neondb","neon_branch_id":"br-rapid-mouse-b7clh18t"}'::jsonb THEN
    RAISE EXCEPTION 'directory sync: wrong document target';
  END IF;
  src := doc->'source';
  IF pg_catalog.jsonb_typeof(src) IS DISTINCT FROM 'object'
     OR src - ARRAY['library_file_id','version','sha256','exported_at'] <> '{}'::jsonb
     OR NOT src ?& ARRAY['library_file_id','version','sha256','exported_at']
     OR src->>'library_file_id' IS DISTINCT FROM 'libfile_8ba8491c8ff881918ed4868c0ee43465'
     OR pg_catalog.jsonb_typeof(src->'version') IS DISTINCT FROM 'number'
     OR src->>'version' !~ '^[0-9]+$'
     OR pg_catalog.jsonb_typeof(src->'sha256') IS DISTINCT FROM 'string'
     OR src->>'sha256' !~ '^[0-9a-f]{64}$'
     OR pg_catalog.jsonb_typeof(src->'exported_at') IS DISTINCT FROM 'string'
     OR src->>'exported_at' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?Z$' THEN
    RAISE EXCEPTION 'directory sync: invalid source provenance';
  END IF;
  source_version := (src->>'version')::bigint;
  exported_at := (src->>'exported_at')::timestamptz;
  IF source_version < 7 OR exported_at < pg_catalog.clock_timestamp() - interval '48 hours'
     OR exported_at > pg_catalog.clock_timestamp() + interval '5 minutes' THEN
    RAISE EXCEPTION 'directory sync: source version or export freshness rejected';
  END IF;
  IF pg_catalog.jsonb_typeof(doc->'entries') IS DISTINCT FROM 'array' THEN
    RAISE EXCEPTION 'directory sync: entries must be an array';
  END IF;
  new_count := pg_catalog.jsonb_array_length(doc->'entries');
  IF new_count < 93 OR new_count > 10000 THEN
    RAISE EXCEPTION 'directory sync: entry count outside guarded bounds';
  END IF;
  document_hash := pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(raw_document, 'UTF8')), 'hex');

  -- Lock before reading the current pointer. Table locks prevent legacy writes
  -- to any catalog rows between validation and copying; readers stay available.
  -- The same fixed order is used by every importer; a competing legacy publish
  -- may be aborted by PostgreSQL deadlock detection, never partially applied.
  PERFORM pg_catalog.pg_advisory_xact_lock(734512, 20261007);
  LOCK TABLE public.entries, public.offers IN SHARE MODE;
  SELECT value INTO prior FROM public.settings WHERE key = 'active_batch' FOR UPDATE;
  IF prior IS NULL OR prior IS DISTINCT FROM expected_active THEN
    RAISE EXCEPTION 'directory sync: active batch changed (compare-and-swap mismatch)';
  END IF;
  SELECT * INTO latest FROM selfpay_directory_sync.import_ledger ORDER BY sequence_id DESC LIMIT 1;
  bootstrap := NOT FOUND;
  IF bootstrap AND prior = 'b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4' THEN
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
  ELSE
    IF prior <> latest.batch_id THEN
      RAISE EXCEPTION 'directory sync: active pointer left the import chain; administrator review required';
    END IF;
    IF source_version < latest.source_version THEN
      RAISE EXCEPTION 'directory sync: source version rollback rejected';
    END IF;
    IF source_version = latest.source_version AND src->>'sha256' <> latest.source_sha256 THEN
      RAISE EXCEPTION 'directory sync: same version has different workbook hash';
    END IF;
  END IF;
  fingerprints := selfpay_directory_sync.catalog_fingerprints(prior);
  IF NOT bootstrap AND (fingerprints->>'offer_fingerprint' <> latest.offer_fingerprint
      OR fingerprints->>'entry_fingerprint' <> latest.entry_fingerprint) THEN
    RAISE EXCEPTION 'directory sync: current catalog fingerprint changed outside the import chain';
  END IF;
  SELECT count(*) INTO old_count FROM public.entries WHERE batch_id = prior;
  SELECT count(*) INTO offer_count FROM public.offers WHERE batch_id = prior;
  IF old_count < 93 OR offer_count <> 13 THEN
    RAISE EXCEPTION 'directory sync: current catalog entry/offer count changed unexpectedly';
  END IF;
  IF EXISTS (SELECT FROM public.offers o LEFT JOIN public.entries e
      ON e.batch_id = o.batch_id AND e.entry_key = o.entry_key
      WHERE o.batch_id = prior AND (e.entry_key IS NULL OR
        o.payload::jsonb->>'entry_hash' IS DISTINCT FROM e.content_hash)) THEN
    RAISE EXCEPTION 'directory sync: existing offer mapping source hash mismatch';
  END IF;

  FOR entry IN SELECT value FROM pg_catalog.jsonb_array_elements(doc->'entries') LOOP
    IF pg_catalog.jsonb_typeof(entry) IS DISTINCT FROM 'object'
       OR entry - ARRAY['entry_key','content_hash','payload','content'] <> '{}'::jsonb
       OR NOT entry ?& ARRAY['entry_key','content_hash','payload','content']
       OR pg_catalog.jsonb_typeof(entry->'entry_key') IS DISTINCT FROM 'string'
       OR entry->>'entry_key' !~ '^[0-9a-f]{64}$'
       OR pg_catalog.jsonb_typeof(entry->'content_hash') IS DISTINCT FROM 'string'
       OR entry->>'content_hash' !~ '^[0-9a-f]{64}$'
       OR pg_catalog.jsonb_typeof(entry->'payload') IS DISTINCT FROM 'string'
       OR pg_catalog.jsonb_typeof(entry->'content') IS DISTINCT FROM 'string' THEN
      RAISE EXCEPTION 'directory sync: invalid entry envelope';
    END IF;
    payload_text := entry->>'payload'; content_text := entry->>'content';
    payload := payload_text::jsonb; content := content_text::jsonb;
    IF pg_catalog.jsonb_typeof(payload) IS DISTINCT FROM 'object'
       OR NOT payload ?& required_keys OR payload - required_keys <> '{}'::jsonb
       OR EXISTS (SELECT FROM pg_catalog.jsonb_each(payload) p
          WHERE pg_catalog.jsonb_typeof(p.value) <> 'string')
       OR content IS DISTINCT FROM payload - 'row'
       OR payload_text IS DISTINCT FROM selfpay_directory_sync.canonical_strings(payload)
       OR content_text IS DISTINCT FROM selfpay_directory_sync.canonical_strings(content) THEN
      RAISE EXCEPTION 'directory sync: noncanonical or invalid string-only entry payload';
    END IF;
    entry_name := payload->>'name'; entry_key := entry->>'entry_key';
    IF entry_name = '' OR entry_name <> pg_catalog.btrim(entry_name,
        U&'\0009\000A\000B\000C\000D\001C\001D\001E\001F\0020\0085\00A0\1680\2000\2001\2002\2003\2004\2005\2006\2007\2008\2009\200A\2028\2029\202F\205F\3000')
       OR entry_key <> pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
         pg_catalog.to_jsonb(entry_name)::text, 'UTF8')), 'hex')
       OR entry->>'content_hash' <> pg_catalog.encode(pg_catalog.sha256(
         pg_catalog.convert_to(content_text, 'UTF8')), 'hex') THEN
      RAISE EXCEPTION 'directory sync: name or normalized hash mismatch';
    END IF;
    IF entry_key = ANY(seen_keys) OR entry_name = ANY(seen_names) THEN
      RAISE EXCEPTION 'directory sync: duplicate entry key or name';
    END IF;
    seen_keys := pg_catalog.array_append(seen_keys, entry_key);
    seen_names := pg_catalog.array_append(seen_names, entry_name);
    IF EXISTS (SELECT FROM public.entries e WHERE e.batch_id = prior AND e.entry_key = guarded.entry_key) THEN
      IF NOT EXISTS (SELECT FROM public.entries e WHERE e.batch_id = prior AND e.entry_key = guarded.entry_key
          AND e.content_hash = entry->>'content_hash' AND e.payload = payload_text) THEN
        RAISE EXCEPTION 'directory sync: existing entries must remain byte-for-byte unchanged';
      END IF;
    ELSE
      IF payload->>'source' !~ '^https://[^[:space:]/?#@]+([/?#][^[:space:]]*)?$'
         OR payload->>'checked' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}( [0-9]{2}:[0-9]{2}:[0-9]{2})?$' THEN
        RAISE EXCEPTION 'directory sync: new entry needs HTTPS source and verification date';
      END IF;
      checked_date := pg_catalog.substring(payload->>'checked', 1, 10)::date;
      IF (payload->>'checked')::timestamp AT TIME ZONE 'UTC' > pg_catalog.clock_timestamp() THEN
        RAISE EXCEPTION 'directory sync: future verification date rejected';
      END IF;
    END IF;
  END LOOP;
  IF EXISTS (SELECT FROM public.entries e WHERE e.batch_id = prior AND NOT e.entry_key = ANY(seen_keys)) THEN
    RAISE EXCEPTION 'directory sync: removing existing entries is forbidden';
  END IF;
  added := new_count - old_count;
  IF bootstrap AND added <> 0 THEN
    RAISE EXCEPTION 'directory sync: first apply must exactly match the reviewed catalog';
  END IF;
  IF NOT bootstrap AND source_version = latest.source_version AND added <> 0 THEN
    RAISE EXCEPTION 'directory sync: entries changed without a new source version';
  END IF;
  next_batch := CASE WHEN added = 0 THEN prior ELSE 'directory-' || document_hash END;
  result := pg_catalog.jsonb_build_object('dry_run', dry_run, 'unchanged', added = 0,
    'active_batch', CASE WHEN dry_run THEN prior ELSE next_batch END,
    'previous_batch', prior, 'entry_count', new_count, 'offer_count', offer_count,
    'added', added, 'changed', 0, 'removed', 0, 'source_version', source_version,
    'document_hash', document_hash, 'bootstrap', bootstrap);
  IF dry_run THEN RETURN result; END IF;
  IF EXISTS (SELECT FROM selfpay_directory_sync.import_ledger l WHERE l.document_hash = guarded.document_hash) THEN
    RETURN result || pg_catalog.jsonb_build_object('idempotent', true);
  END IF;
  IF added > 0 THEN
    -- Deliberately separate from legacy digest({entries,mappings}). This digest
    -- includes every byte of the reviewed export envelope and its provenance.
    INSERT INTO public.batches(id, content_hash, source_name, created, status, report)
      VALUES(next_batch, document_hash, 'directory-library-v' || source_version,
        EXTRACT(epoch FROM pg_catalog.clock_timestamp()), 'published', result::text);
    INSERT INTO public.entries(batch_id, entry_key, content_hash, payload)
      SELECT next_batch, e.entry_key, e.content_hash, e.payload FROM public.entries e WHERE e.batch_id = prior;
    INSERT INTO public.entries(batch_id, entry_key, content_hash, payload)
      SELECT next_batch, x.value->>'entry_key', x.value->>'content_hash', x.value->>'payload'
      FROM pg_catalog.jsonb_array_elements(doc->'entries') x
      WHERE NOT EXISTS (SELECT FROM public.entries e WHERE e.batch_id = prior AND e.entry_key = x.value->>'entry_key');
    INSERT INTO public.offers(batch_id, id, entry_key, amount_cents, max_cents, price_type, payload)
      SELECT next_batch, o.id, o.entry_key, o.amount_cents, o.max_cents, o.price_type, o.payload
      FROM public.offers o WHERE o.batch_id = prior;
    UPDATE public.settings SET value = next_batch WHERE key = 'active_batch' AND value = prior;
    IF NOT FOUND THEN RAISE EXCEPTION 'directory sync: compare-and-swap failed'; END IF;
    INSERT INTO public.publish_events(batch_id, previous_batch, created, action)
      VALUES(next_batch, prior, EXTRACT(epoch FROM pg_catalog.clock_timestamp()), 'directory_sync');
  END IF;
  INSERT INTO selfpay_directory_sync.import_ledger(document_hash, library_file_id, source_version,
    source_sha256, exported_at, previous_batch, batch_id, added, offer_fingerprint, entry_fingerprint, raw_document)
    VALUES(document_hash, src->>'library_file_id', source_version, src->>'sha256', exported_at,
      prior, next_batch, added, fingerprints->>'offer_fingerprint',
      selfpay_directory_sync.catalog_fingerprints(next_batch)->>'entry_fingerprint', raw_document);
  RETURN result || pg_catalog.jsonb_build_object('idempotent', false);
END
$function$
