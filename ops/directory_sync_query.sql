-- Single-statement transport wrapper; execute only after administrator review.
-- Original: ops/directory_sync.sql
-- Original SHA256: d612ff80a99e0102b5f17eb7ba59eb5e932bb4d3dc58b8c7b264cc512f0ba2aa
-- The embedded bytes omit only the original outer BEGIN; and COMMIT; lines.
-- This invoker DO statement is one atomic transaction under autocommit.
-- It does not catch errors: any failure rolls back roles, schema, and grants.
DO $directory_sync_query$
BEGIN
  EXECUTE $directory_sync_package$
-- Administrator-reviewed, one-time provisioning only. Do not run from the app.
-- Target: Neon project late-grass-13270808, branch br-rapid-mouse-b7clh18t,
-- database neondb. The project ID is documentary; the live branch is checked.
-- Run with psql --set ON_ERROR_STOP=1 --file ops/directory_sync.sql.
-- No passwords are created here. After separate approval the user may run
-- \password selfpay_directory_importer in a secure administrator psql session.
-- Default PUBLIC TEMP, if present, is not changed. Temporary objects cannot
-- shadow any reference below: search_path is pg_catalog and relations qualify.
SET LOCAL search_path = pg_catalog;
SET LOCAL lock_timeout = '10s';

DO $provision$
BEGIN
  IF current_database() <> 'neondb'
     OR current_setting('neon.branch_id', true) IS DISTINCT FROM 'br-rapid-mouse-b7clh18t' THEN
    RAISE EXCEPTION 'directory sync: wrong database or Neon branch';
  END IF;
  IF EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname IN
      ('selfpay_directory_owner', 'selfpay_directory_importer'))
     OR EXISTS (SELECT FROM pg_catalog.pg_namespace WHERE nspname = 'selfpay_directory_sync') THEN
    RAISE EXCEPTION 'directory sync: role or schema already exists; inspect rather than reuse';
  END IF;
  IF (SELECT value FROM public.settings WHERE key = 'active_batch')
       IS DISTINCT FROM '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f'
     OR (SELECT count(*) FROM public.entries WHERE batch_id =
         '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f') < 93
     OR (SELECT count(*) FROM public.offers WHERE batch_id =
         '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f') <> 13 THEN
    RAISE EXCEPTION 'directory sync: reviewed bootstrap catalog no longer matches';
  END IF;
  IF (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) ORDER BY e.entry_key)::text, '[]'))
      FROM public.entries e WHERE e.batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f')
      <> 'be0290bd19eff19066766e8644245122'
     OR (SELECT pg_catalog.md5(COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o) ORDER BY o.id)::text, '[]'))
      FROM public.offers o WHERE o.batch_id = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f')
      <> '711a7c77b51e6107e7d7326229366a4b' THEN
    RAISE EXCEPTION 'directory sync: reviewed bootstrap full-row fingerprint mismatch';
  END IF;
END
$provision$;

CREATE ROLE selfpay_directory_owner NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE
  NOINHERIT NOREPLICATION NOBYPASSRLS;
CREATE ROLE selfpay_directory_importer LOGIN PASSWORD NULL NOSUPERUSER NOCREATEDB
  NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS;
-- Temporary administrator membership allows ownership transfer on managed PG.
-- It is revoked before this transaction commits, never granted to the login.
GRANT selfpay_directory_owner TO CURRENT_USER;
CREATE SCHEMA selfpay_directory_sync AUTHORIZATION selfpay_directory_owner;
REVOKE ALL ON SCHEMA selfpay_directory_sync FROM PUBLIC;
GRANT USAGE ON SCHEMA selfpay_directory_sync TO selfpay_directory_importer;
GRANT CONNECT ON DATABASE neondb TO selfpay_directory_importer;
GRANT USAGE ON SCHEMA public TO selfpay_directory_owner;
-- Only new snapshots are inserted; historical rows are never updated.
GRANT SELECT, INSERT ON public.batches, public.entries, public.offers,
  public.publish_events TO selfpay_directory_owner;
-- PostgreSQL requires a table-level UPDATE/DELETE/TRUNCATE privilege for
-- SHARE locks. Grant UPDATE only to the inaccessible NOLOGIN function owner;
-- neither executable function issues an UPDATE against entries or offers.
GRANT UPDATE ON public.entries, public.offers TO selfpay_directory_owner;
GRANT SELECT ON public.settings TO selfpay_directory_owner;
GRANT UPDATE(value) ON public.settings TO selfpay_directory_owner;
DO $sequence$
DECLARE seq text;
BEGIN
  seq := pg_catalog.pg_get_serial_sequence('public.publish_events', 'id');
  IF seq IS NULL THEN
    RAISE EXCEPTION 'directory sync: publish_events.id must use a sequence';
  END IF;
  EXECUTE pg_catalog.format('GRANT USAGE ON SEQUENCE %s TO selfpay_directory_owner', seq);
END
$sequence$;

SET LOCAL ROLE selfpay_directory_owner;
-- Revoke the owner's global default: a schema-local REVOKE cannot remove
-- PostgreSQL's global default PUBLIC EXECUTE on newly created functions.
ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
CREATE TABLE selfpay_directory_sync.import_ledger (
  sequence_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  document_hash text NOT NULL UNIQUE CHECK (document_hash ~ '^[0-9a-f]{64}$'),
  library_file_id text NOT NULL,
  source_version bigint NOT NULL CHECK (source_version >= 7),
  source_sha256 text NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  exported_at timestamptz NOT NULL,
  imported_at timestamptz NOT NULL DEFAULT pg_catalog.clock_timestamp(),
  previous_batch text NOT NULL,
  batch_id text NOT NULL,
  added integer NOT NULL CHECK (added >= 0),
  offer_fingerprint text NOT NULL,
  entry_fingerprint text NOT NULL,
  raw_document text NOT NULL
);
REVOKE ALL ON selfpay_directory_sync.import_ledger FROM PUBLIC, selfpay_directory_importer;

-- Narrow canonical encoder for the allowed string-only objects. C collation
-- yields Python sort_keys order for these fixed ASCII keys; to_jsonb text uses
-- UTF-8, matching ensure_ascii=False. Comparing raw text also rejects duplicate
-- JSON keys, whitespace, and alternate escape encodings in payload/content.
CREATE FUNCTION selfpay_directory_sync.canonical_strings(value jsonb)
RETURNS text LANGUAGE sql IMMUTABLE STRICT SET search_path = pg_catalog AS $function$
  SELECT '{' || COALESCE(pg_catalog.string_agg(
    pg_catalog.to_jsonb(p.key)::text || ':' || pg_catalog.to_jsonb(p.value)::text,
    ',' ORDER BY p.key COLLATE "C"), '') || '}'
  FROM pg_catalog.jsonb_each_text(value) AS p
$function$;

-- Reject duplicate JSON object keys before jsonb would silently discard them.
CREATE FUNCTION selfpay_directory_sync.unique_json_keys(value json)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE STRICT SET search_path = pg_catalog AS $function$
DECLARE child json;
BEGIN
  IF pg_catalog.json_typeof(value) = 'object' THEN
    IF (SELECT count(*) <> count(DISTINCT p.key) FROM pg_catalog.json_each(value) p) THEN
      RETURN false;
    END IF;
    FOR child IN SELECT p.value FROM pg_catalog.json_each(value) p LOOP
      IF NOT selfpay_directory_sync.unique_json_keys(child) THEN RETURN false; END IF;
    END LOOP;
  ELSIF pg_catalog.json_typeof(value) = 'array' THEN
    FOR child IN SELECT p.value FROM pg_catalog.json_array_elements(value) p LOOP
      IF NOT selfpay_directory_sync.unique_json_keys(child) THEN RETURN false; END IF;
    END LOOP;
  END IF;
  RETURN true;
END
$function$;

CREATE FUNCTION selfpay_directory_sync.check_target()
RETURNS void LANGUAGE plpgsql STABLE SET search_path = pg_catalog AS $function$
BEGIN
  IF pg_catalog.current_database() <> 'neondb'
     OR pg_catalog.current_setting('neon.branch_id', true)
        IS DISTINCT FROM 'br-rapid-mouse-b7clh18t' THEN
    RAISE EXCEPTION 'directory sync: wrong database or Neon branch';
  END IF;
END
$function$;

CREATE FUNCTION selfpay_directory_sync.catalog_fingerprints(batch text)
RETURNS jsonb LANGUAGE sql STABLE STRICT SET search_path = pg_catalog AS $function$
  SELECT pg_catalog.jsonb_build_object(
    'offer_fingerprint', (SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
      COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(o) - 'batch_id' ORDER BY o.id)::text, '[]'), 'UTF8')), 'hex')
      FROM public.offers o WHERE o.batch_id = batch),
    'entry_fingerprint', (SELECT pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(
      COALESCE(pg_catalog.jsonb_agg(pg_catalog.to_jsonb(e) - 'batch_id' ORDER BY e.entry_key)::text, '[]'), 'UTF8')), 'hex')
      FROM public.entries e WHERE e.batch_id = batch))
$function$;

CREATE FUNCTION selfpay_directory_sync.status()
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $function$
DECLARE result jsonb;
BEGIN
  PERFORM selfpay_directory_sync.check_target();
  WITH active AS (SELECT value AS id FROM public.settings WHERE key = 'active_batch'),
  latest AS (SELECT * FROM selfpay_directory_sync.import_ledger ORDER BY sequence_id DESC LIMIT 1)
  SELECT pg_catalog.jsonb_build_object(
    'database', pg_catalog.current_database(),
    'neon_branch_id', pg_catalog.current_setting('neon.branch_id', true),
    'active_batch', (SELECT id FROM active),
    'offer_fingerprint', selfpay_directory_sync.catalog_fingerprints((SELECT id FROM active))->>'offer_fingerprint',
    'entry_fingerprint', selfpay_directory_sync.catalog_fingerprints((SELECT id FROM active))->>'entry_fingerprint',
    'entry_count', (SELECT count(*) FROM public.entries WHERE batch_id = (SELECT id FROM active)),
    'offer_count', (SELECT count(*) FROM public.offers WHERE batch_id = (SELECT id FROM active)),
    'entries', COALESCE((SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'entry_key', e.entry_key, 'content_hash', e.content_hash, 'payload', e.payload)
      ORDER BY e.entry_key) FROM public.entries e WHERE e.batch_id = (SELECT id FROM active)), '[]'::jsonb),
    'offers', COALESCE((SELECT pg_catalog.jsonb_agg(pg_catalog.jsonb_build_object(
      'id', o.id, 'entry_key', o.entry_key, 'amount_cents', o.amount_cents,
      'max_cents', o.max_cents, 'price_type', o.price_type, 'payload', o.payload)
      ORDER BY o.id) FROM public.offers o WHERE o.batch_id = (SELECT id FROM active)), '[]'::jsonb),
    'source', (SELECT pg_catalog.jsonb_build_object(
      'library_file_id', library_file_id, 'version', source_version, 'sha256', source_sha256,
      'exported_at', exported_at, 'document_hash', document_hash, 'batch_id', batch_id,
      'offer_fingerprint', offer_fingerprint, 'entry_fingerprint', entry_fingerprint) FROM latest)
  ) INTO result;
  RETURN result;
END
$function$;

CREATE FUNCTION selfpay_directory_sync.apply_bundle(
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

REVOKE ALL ON ALL FUNCTIONS IN SCHEMA selfpay_directory_sync FROM PUBLIC;
GRANT EXECUTE ON FUNCTION selfpay_directory_sync.status(),
  selfpay_directory_sync.apply_bundle(text,text,boolean) TO selfpay_directory_importer;
RESET ROLE;
REVOKE selfpay_directory_owner FROM CURRENT_USER;

-- Fail closed on PUBLIC privileges that would silently bypass the function-only
-- boundary. Do not revoke global privileges or mutate unrelated app roles.
DO $audit$
DECLARE item record; role_name text;
BEGIN
  FOREACH role_name IN ARRAY ARRAY['selfpay_directory_owner','selfpay_directory_importer'] LOOP
    IF pg_catalog.has_database_privilege(role_name, 'neondb', 'CREATE') THEN
      RAISE EXCEPTION 'directory sync: unsafe effective database CREATE privilege for %', role_name;
    END IF;
    FOR item IN SELECT oid, nspname FROM pg_catalog.pg_namespace
      WHERE nspname NOT IN ('pg_catalog','information_schema','selfpay_directory_sync')
        AND nspname !~ '^pg_(toast|temp)' LOOP
      IF pg_catalog.has_schema_privilege(role_name, item.oid, 'CREATE') THEN
        RAISE EXCEPTION 'directory sync: unsafe effective schema CREATE privilege for %', role_name;
      END IF;
    END LOOP;
    FOR item IN SELECT c.oid, n.nspname, c.relname FROM pg_catalog.pg_class c
      JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relkind IN ('r','p','v','m','f') AND n.nspname !~ '^pg_'
        AND n.nspname <> 'information_schema'
        AND NOT (role_name = 'selfpay_directory_owner' AND
          (n.nspname = 'selfpay_directory_sync' OR (n.nspname = 'public' AND
            c.relname IN ('batches','entries','offers','settings','publish_events')))) LOOP
      IF pg_catalog.has_table_privilege(role_name, item.oid, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
         OR pg_catalog.has_any_column_privilege(role_name, item.oid, 'SELECT,INSERT,UPDATE,REFERENCES') THEN
        RAISE EXCEPTION 'directory sync: unsafe effective access to %.% for %', item.nspname, item.relname, role_name;
      END IF;
    END LOOP;
    FOR item IN SELECT c.oid, n.nspname, c.relname FROM pg_catalog.pg_class c
      JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
      WHERE c.relkind = 'S' AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
        AND NOT (role_name = 'selfpay_directory_owner' AND
          (n.nspname = 'selfpay_directory_sync' OR c.oid =
             pg_catalog.pg_get_serial_sequence('public.publish_events','id')::regclass)) LOOP
      IF pg_catalog.has_sequence_privilege(role_name, item.oid, 'USAGE,SELECT,UPDATE') THEN
        RAISE EXCEPTION 'directory sync: unsafe effective sequence privilege for %', role_name;
      END IF;
    END LOOP;
    FOR item IN SELECT p.oid FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid = p.pronamespace
      WHERE p.prosecdef AND n.nspname !~ '^pg_' AND n.nspname <> 'information_schema'
        AND n.nspname <> 'selfpay_directory_sync' LOOP
      IF pg_catalog.has_function_privilege(role_name, item.oid, 'EXECUTE') THEN
        RAISE EXCEPTION 'directory sync: unexpected executable security-definer function for %', role_name;
      END IF;
    END LOOP;
    IF EXISTS (SELECT FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles r ON r.oid = m.member
        WHERE r.rolname = role_name) THEN
      RAISE EXCEPTION 'directory sync: unexpected role membership for %', role_name;
    END IF;
  END LOOP;
END
$audit$;
-- No login-executable rollback function exists. An administrator can review the
-- retained previous batch and event before a separate, explicitly approved CAS
-- pointer rollback. A rollback leaves the sync chain and halts future imports.
$directory_sync_package$;
END
$directory_sync_query$;
