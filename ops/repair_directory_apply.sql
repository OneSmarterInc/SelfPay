-- MANUAL ADMINISTRATOR REVIEW AND EXECUTION ONLY. Never run from the app/CI.
-- One prepared statement for Vercel Query; its DO block is fully atomic.
-- Repairs only apply_bundle, without recreating roles, schema, tables, or data.
-- Target: Neon project late-grass-13270808 (documentary), branch
-- br-rapid-mouse-b7clh18t (verified), database neondb, caller neondb_owner.
-- Exact reviewed function block comes from ops/directory_sync.sql, SHA256
-- d612ff80a99e0102b5f17eb7ba59eb5e932bb4d3dc58b8c7b264cc512f0ba2aa.
-- Only CREATE FUNCTION becomes CREATE OR REPLACE FUNCTION; body is unchanged.
-- Accepted installed prosrc SHA256:
-- 9092aefd2bc6e60858b646c9163728d5510086f003d90052288dfacdb74a15f9
-- Repaired prosrc SHA256:
-- bf710be762cfcc0c3eb95a7692032d27eadc05f5e202a30dcca5ef1fac794b61
-- An already-correct function is a no-op only at the same verified baseline.
-- The administrator's temporary INHERIT-only owner grant is revoked before
-- success; its automatic ADMIN-only membership is preserved exactly.
-- No password, credential, importer grant, or permanent membership is changed.
-- Any exception, including final validation, rolls back the entire statement.
DO $directory_apply_repair$
DECLARE
  function_oid oid; owner_oid oid; importer_oid oid; admin_oid oid;
  body_hash text; function_before jsonb; functions_before jsonb;
  roles_before jsonb; memberships_before jsonb; privileges_before jsonb;
  previous_search_path text; previous_lock_timeout text;
BEGIN
  previous_search_path := pg_catalog.current_setting('search_path');
  previous_lock_timeout := pg_catalog.current_setting('lock_timeout');
  PERFORM pg_catalog.set_config('search_path', 'pg_catalog', true);
  PERFORM pg_catalog.set_config('lock_timeout', '10s', true);

  IF pg_catalog.current_database() <> 'neondb'
     OR pg_catalog.current_setting('neon.branch_id', true)
        IS DISTINCT FROM 'br-rapid-mouse-b7clh18t' THEN
    RAISE EXCEPTION 'directory repair: wrong database or Neon branch';
  END IF;
  SELECT r.oid INTO admin_oid FROM pg_catalog.pg_roles r
    WHERE r.rolname = 'neondb_owner' AND NOT r.rolsuper
      AND r.rolcreaterole AND r.rolinherit;
  IF CURRENT_USER <> 'neondb_owner' OR SESSION_USER <> 'neondb_owner'
     OR admin_oid IS NULL OR (SELECT d.datdba FROM pg_catalog.pg_database d
         WHERE d.datname = pg_catalog.current_database()) IS DISTINCT FROM admin_oid THEN
    RAISE EXCEPTION 'directory repair: expected nonsuperuser INHERIT/CREATEROLE database owner';
  END IF;
  SELECT r.oid INTO owner_oid FROM pg_catalog.pg_roles r
    WHERE r.rolname = 'selfpay_directory_owner' AND NOT r.rolcanlogin
      AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole
      AND NOT r.rolinherit AND NOT r.rolreplication AND NOT r.rolbypassrls;
  SELECT r.oid INTO importer_oid FROM pg_catalog.pg_roles r
    WHERE r.rolname = 'selfpay_directory_importer' AND r.rolcanlogin
      AND NOT r.rolsuper AND NOT r.rolcreatedb AND NOT r.rolcreaterole
      AND NOT r.rolinherit AND NOT r.rolreplication AND NOT r.rolbypassrls;
  IF owner_oid IS NULL OR importer_oid IS NULL THEN
    RAISE EXCEPTION 'directory repair: unexpected owner/importer role attributes';
  END IF;
  IF (SELECT count(*) FROM pg_catalog.pg_auth_members m
      WHERE m.roleid IN (owner_oid, importer_oid) OR m.member IN (owner_oid, importer_oid)) <> 2
     OR (SELECT count(*) FROM pg_catalog.pg_auth_members m
      WHERE m.roleid IN (owner_oid, importer_oid) AND m.member = admin_oid
        AND m.admin_option AND NOT m.inherit_option AND NOT m.set_option
        AND m.grantor <> admin_oid) <> 2 THEN
    RAISE EXCEPTION 'directory repair: expected automatic ADMIN-only memberships';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_namespace n
      WHERE n.nspname = 'selfpay_directory_sync' AND n.nspowner = owner_oid
        AND n.nspacl::text = '{selfpay_directory_owner=UC/selfpay_directory_owner,selfpay_directory_importer=U/selfpay_directory_owner}') THEN
    RAISE EXCEPTION 'directory repair: unexpected schema owner or permissions';
  END IF;
  SELECT p.oid, (pg_catalog.to_jsonb(p) - 'prosrc' - 'proargdefaults') ||
    pg_catalog.jsonb_build_object('argument_defaults', pg_catalog.pg_get_expr(p.proargdefaults, 0)),
    pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p.prosrc, 'UTF8')), 'hex')
    INTO function_oid, function_before, body_hash
    FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'selfpay_directory_sync' AND p.proname = 'apply_bundle'
      AND p.proargtypes = '25 25 16'::pg_catalog.oidvector;
  IF function_oid IS NULL OR NOT EXISTS (SELECT FROM pg_catalog.pg_proc p
      WHERE p.oid = function_oid AND p.proowner = owner_oid AND p.prosecdef
        AND p.proconfig = ARRAY['search_path=pg_catalog']::text[]
        AND p.prorettype = 'pg_catalog.jsonb'::pg_catalog.regtype
        AND p.prolang = (SELECT l.oid FROM pg_catalog.pg_language l WHERE l.lanname = 'plpgsql')
        AND p.prokind = 'f' AND p.provolatile = 'v' AND p.proparallel = 'u'
        AND NOT p.proleakproof AND NOT p.proisstrict AND NOT p.proretset
        AND p.pronargs = 3 AND p.pronargdefaults = 1
        AND p.proargnames = ARRAY['raw_document','expected_active','dry_run']::text[]
        AND p.proallargtypes IS NULL AND p.proargmodes IS NULL
        AND pg_catalog.pg_get_expr(p.proargdefaults, 0) = 'true'
        AND p.proacl::text = '{selfpay_directory_owner=X/selfpay_directory_owner,selfpay_directory_importer=X/selfpay_directory_owner}') THEN
    RAISE EXCEPTION 'directory repair: unexpected apply_bundle signature, owner, configuration, or permissions';
  END IF;
  IF body_hash NOT IN ('9092aefd2bc6e60858b646c9163728d5510086f003d90052288dfacdb74a15f9',
      'bf710be762cfcc0c3eb95a7692032d27eadc05f5e202a30dcca5ef1fac794b61') THEN
    RAISE EXCEPTION 'directory repair: unknown apply_bundle body; inspect rather than overwrite';
  END IF;

  -- Snapshot catalogs before the sole temporary grant. No credential fields
  -- are read. These snapshots enforce preservation, not new privileges.
  SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) - 'rolpassword' ORDER BY r.oid)
    INTO roles_before FROM pg_catalog.pg_roles r;
  SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(m) ORDER BY m.roleid,m.member,m.grantor), '[]'::jsonb)
    INTO memberships_before FROM pg_catalog.pg_auth_members m;
  SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(p) ORDER BY p.oid)
    INTO functions_before FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'selfpay_directory_sync' AND p.oid <> function_oid;
  SELECT pg_catalog.jsonb_build_object(
    'schemas', (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(n) ORDER BY n.oid) FROM pg_catalog.pg_namespace n),
    'relations', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(c.oid,c.relowner,c.relacl) ORDER BY c.oid)
      FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname IN ('public','selfpay_directory_sync')),
    'columns', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(a.attrelid,a.attnum,a.attacl) ORDER BY a.attrelid,a.attnum)
      FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
      JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN ('public','selfpay_directory_sync')),
    'databases', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid,d.datdba,d.datacl) ORDER BY d.oid) FROM pg_catalog.pg_database d),
    'defaults', (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(d) ORDER BY d.oid) FROM pg_catalog.pg_default_acl d))
    INTO privileges_before;

  -- On managed PG the database owner has ADMIN, but cannot inherit the
  -- function owner's rights until it makes this separate, temporary grant.
  GRANT selfpay_directory_owner TO CURRENT_USER WITH INHERIT TRUE, SET FALSE;
  IF NOT pg_catalog.pg_has_role(CURRENT_USER, owner_oid, 'USAGE')
     OR pg_catalog.pg_has_role(CURRENT_USER, owner_oid, 'SET') THEN
    RAISE EXCEPTION 'directory repair: temporary owner grant has unexpected effective rights';
  END IF;
  PERFORM pg_catalog.pg_advisory_xact_lock(734512, 20261007);
  LOCK TABLE public.entries, public.offers IN SHARE MODE;
  LOCK TABLE public.settings, selfpay_directory_sync.import_ledger IN SHARE MODE;
  IF (SELECT count(*) FROM selfpay_directory_sync.import_ledger) <> 0 THEN
    RAISE EXCEPTION 'directory repair: ledger must still be empty';
  END IF;
  IF (SELECT value FROM public.settings WHERE key = 'active_batch')
       IS DISTINCT FROM '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f'
     OR (SELECT count(*) FROM public.entries WHERE batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f') <> 93
     OR (SELECT count(*) FROM public.offers WHERE batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f') <> 13 THEN
    RAISE EXCEPTION 'directory repair: reviewed active batch or baseline counts changed';
  END IF;
  IF (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) ORDER BY e.entry_key)::text, '[]'))
      FROM public.entries e WHERE e.batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f')
      IS DISTINCT FROM 'be0290bd19eff19066766e8644245122'
     OR (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o) ORDER BY o.id)::text, '[]'))
      FROM public.offers o WHERE o.batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f')
      IS DISTINCT FROM '711a7c77b51e6107e7d7326229366a4b' THEN
    RAISE EXCEPTION 'directory repair: reviewed bootstrap full-row fingerprint mismatch';
  END IF;

  IF body_hash = '9092aefd2bc6e60858b646c9163728d5510086f003d90052288dfacdb74a15f9' THEN
    EXECUTE $reviewed_apply_bundle$
CREATE OR REPLACE FUNCTION selfpay_directory_sync.apply_bundle(
  raw_document text, expected_active text, dry_run boolean DEFAULT true)
RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $function$
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
  IF bootstrap THEN
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
$function$;
$reviewed_apply_bundle$;
  END IF;
  REVOKE selfpay_directory_owner FROM CURRENT_USER;

  -- Final checks happen inside the same statement. No exception is caught.
  IF (SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(p.prosrc, 'UTF8')), 'hex')
       FROM pg_catalog.pg_proc p WHERE p.oid = function_oid)
       IS DISTINCT FROM 'bf710be762cfcc0c3eb95a7692032d27eadc05f5e202a30dcca5ef1fac794b61'
     OR (SELECT (pg_catalog.to_jsonb(p) - 'prosrc' - 'proargdefaults') ||
    pg_catalog.jsonb_build_object('argument_defaults', pg_catalog.pg_get_expr(p.proargdefaults, 0)) FROM pg_catalog.pg_proc p WHERE p.oid = function_oid)
       IS DISTINCT FROM function_before THEN
    RAISE EXCEPTION 'directory repair: final function body or metadata mismatch';
  END IF;
  IF (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(r) - 'rolpassword' ORDER BY r.oid)
        FROM pg_catalog.pg_roles r) IS DISTINCT FROM roles_before
     OR (SELECT COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(m) ORDER BY m.roleid,m.member,m.grantor), '[]'::jsonb)
        FROM pg_catalog.pg_auth_members m) IS DISTINCT FROM memberships_before
     OR (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(p) ORDER BY p.oid)
        FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
        WHERE n.nspname = 'selfpay_directory_sync' AND p.oid <> function_oid) IS DISTINCT FROM functions_before
     OR (SELECT pg_catalog.jsonb_build_object(
       'schemas', (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(n) ORDER BY n.oid) FROM pg_catalog.pg_namespace n),
       'relations', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(c.oid,c.relowner,c.relacl) ORDER BY c.oid)
         FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
         WHERE n.nspname IN ('public','selfpay_directory_sync')),
       'columns', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(a.attrelid,a.attnum,a.attacl) ORDER BY a.attrelid,a.attnum)
         FROM pg_catalog.pg_attribute a JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
         JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN ('public','selfpay_directory_sync')),
       'databases', (SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_array(d.oid,d.datdba,d.datacl) ORDER BY d.oid) FROM pg_catalog.pg_database d),
       'defaults', (SELECT pg_catalog.jsonb_agg(pg_catalog.to_jsonb(d) ORDER BY d.oid) FROM pg_catalog.pg_default_acl d)))
       IS DISTINCT FROM privileges_before THEN
    RAISE EXCEPTION 'directory repair: roles, memberships, other functions, or privileges changed';
  END IF;
  PERFORM pg_catalog.set_config('search_path', previous_search_path, true);
  PERFORM pg_catalog.set_config('lock_timeout', previous_lock_timeout, true);
  IF body_hash = 'bf710be762cfcc0c3eb95a7692032d27eadc05f5e202a30dcca5ef1fac794b61' THEN
    RAISE NOTICE 'directory repair: already correct at the verified empty-ledger baseline; no change';
  ELSE
    RAISE NOTICE 'directory repair: exact reviewed apply_bundle restored; data and access unchanged';
  END IF;
END
$directory_apply_repair$;
