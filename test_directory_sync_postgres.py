"""Real PostgreSQL role-boundary and guarded import integration tests.

DESTRUCTIVE, LOCAL-ONLY: point DIRECTORY_SYNC_TEST_DATABASE_URL at a throwaway
local neondb and set DIRECTORY_SYNC_TEST_ALLOW_RESET=1. Never use a hosted URL.
The suite recreates its test tables, schema, and the two named roles. PostgreSQL
must be started with -c neon.branch_id=br-rapid-mouse-b7clh18t for this fixture.
It does not retrieve credentials or connect to the real Neon project.

Example: DIRECTORY_SYNC_TEST_ALLOW_RESET=1 \
  DIRECTORY_SYNC_TEST_DATABASE_URL='postgresql://postgres@127.0.0.1:55432/neondb' \
  python -m unittest test_directory_sync_postgres -v
"""
import copy
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import threading
import time
import unittest

URL = os.environ.get('DIRECTORY_SYNC_TEST_DATABASE_URL', '')
ENABLED = bool(URL) and os.environ.get('DIRECTORY_SYNC_TEST_ALLOW_RESET') == '1'
BASELINE = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f'
BRANCH = 'br-rapid-mouse-b7clh18t'
OWNER = 'selfpay_directory_owner'
IMPORTER = 'selfpay_directory_importer'
SCHEMA = 'selfpay_directory_sync'
SQL = Path(__file__).with_name('ops').joinpath('directory_sync.sql').read_text()
FIELDS = 'row name area states entity category mri ct other coverage notes source additional checked'.split()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def entry(index):
    payload = dict.fromkeys(FIELDS, '')
    payload.update(row=str(index + 1), name=f'Synthetic center {index:03}',
                   area='Example', states='OH', source=f'https://example.com/{index}', checked='2026-01-01')
    return envelope(payload)


def envelope(payload):
    content = canonical({k: v for k, v in payload.items() if k != 'row'})
    return dict(entry_key=digest(canonical(payload['name'])), content_hash=digest(content),
                payload=canonical(payload), content=content)


def document(entries=None, version=7):
    return dict(schema_version=1, source=dict(library_file_id='libfile_8ba8491c8ff881918ed4868c0ee43465',
                version=version, sha256=digest(f'workbook{version}'),
                exported_at=dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')),
                target=dict(database='neondb', neon_branch_id=BRANCH),
                entries=entries or [entry(i) for i in range(93)])


@unittest.skipUnless(ENABLED, 'explicit local throwaway PostgreSQL test URL/reset opt-in required')
class DirectorySyncPostgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg
        from psycopg.conninfo import conninfo_to_dict
        opts = conninfo_to_dict(URL)
        if opts.get('host') not in ('127.0.0.1', 'localhost', '::1') or opts.get('dbname') != 'neondb':
            raise RuntimeError('Refusing destructive tests outside local throwaway neondb')
        cls.psycopg = psycopg
        cls.db = psycopg.connect(URL, autocommit=True)
        if cls.db.execute("SELECT current_setting('neon.branch_id',true)").fetchone()[0] != BRANCH:
            raise RuntimeError('Start local PostgreSQL with the fixture neon.branch_id setting')
        cls.reset_roles()
        cls.db.execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public')
        cls.db.execute('''
          CREATE TABLE public.batches(id text PRIMARY KEY, content_hash text UNIQUE NOT NULL,
            source_name text NOT NULL, created double precision NOT NULL, status text NOT NULL, report text NOT NULL);
          CREATE TABLE public.entries(batch_id text REFERENCES public.batches(id), entry_key text,
            content_hash text NOT NULL, payload text NOT NULL, PRIMARY KEY(batch_id,entry_key));
          CREATE TABLE public.offers(batch_id text, id text, entry_key text, amount_cents integer,
            max_cents integer, price_type text NOT NULL, payload text NOT NULL, PRIMARY KEY(batch_id,id),
            FOREIGN KEY(batch_id,entry_key) REFERENCES public.entries(batch_id,entry_key));
          CREATE TABLE public.settings(key text PRIMARY KEY, value text NOT NULL);
          CREATE TABLE public.publish_events(id bigserial PRIMARY KEY, batch_id text REFERENCES public.batches(id),
            previous_batch text, created double precision NOT NULL, action text NOT NULL);
          CREATE TABLE public.members(id text PRIMARY KEY, payload text);
          CREATE TABLE public.sessions(id text PRIMARY KEY, payload text);
          CREATE TABLE public.preferences(id text PRIMARY KEY, payload text);
          CREATE TABLE public.conversations(id text PRIMARY KEY, payload text);
          CREATE TABLE public.corrections(id text PRIMARY KEY, payload text);
          INSERT INTO public.members VALUES('private','must never be visible to importer');
        ''')

    @classmethod
    def reset_roles(cls):
        cls.db.execute('RESET ROLE')
        cls.db.execute(f'DROP SCHEMA IF EXISTS {SCHEMA} CASCADE')
        for role in (IMPORTER, OWNER):
            if cls.db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (role,)).fetchone():
                cls.db.execute(f'DROP OWNED BY {role}; DROP ROLE {role}')

    @classmethod
    def tearDownClass(cls):
        cls.reset_roles()
        cls.db.close()

    def setUp(self):
        self.reset_roles()
        self.db.execute('TRUNCATE public.publish_events, public.offers, public.entries, public.batches, public.settings RESTART IDENTITY CASCADE')
        self.db.execute('INSERT INTO public.batches VALUES(%s,%s,%s,0,%s,%s)',
                        (BASELINE, digest('legacy-signature'), 'reviewed', 'published', '{}'))
        self.entries = [entry(i) for i in range(93)]
        with self.db.cursor() as cur:
            cur.executemany('INSERT INTO public.entries VALUES(%s,%s,%s,%s)',
                            [(BASELINE, e['entry_key'], e['content_hash'], e['payload']) for e in self.entries])
            cur.executemany('INSERT INTO public.offers VALUES(%s,%s,%s,%s,%s,%s,%s)',
                [(BASELINE, f'offer-{i}', e['entry_key'], 12345, None, 'fixed',
                  canonical(dict(entry_hash=e['content_hash'], id=f'offer-{i}', type='fixed', amount=123.45)))
                 for i, e in enumerate(self.entries[:13])])
        self.db.execute("INSERT INTO public.settings VALUES('active_batch',%s)", (BASELINE,))
        self.db.execute("INSERT INTO public.publish_events(batch_id,previous_batch,created,action) VALUES(%s,NULL,0,'publish')", (BASELINE,))
        # Replace only the reviewed deployment fingerprints for the synthetic
        # fixture. Production SQL has no configuration switch or bypass path.
        hashes = [self.db.execute(f"SELECT md5(coalesce(jsonb_agg(to_jsonb(x) ORDER BY {key})::text,'[]')) FROM public.{table} x WHERE batch_id=%s", (BASELINE,)).fetchone()[0]
                  for table, key in [('entries','entry_key'),('offers','id')]]
        self.install_sql = SQL.replace('be0290bd19eff19066766e8644245122', hashes[0]).replace('711a7c77b51e6107e7d7326229366a4b', hashes[1])
        self.db.execute(self.install_sql)

    def apply(self, doc=None, expected=BASELINE, dry_run=False, connection=None):
        connection = connection or self.db
        raw = doc if isinstance(doc, str) else canonical(doc or document())
        with connection.transaction():
            connection.execute(f'SET LOCAL ROLE {IMPORTER}')
            return connection.execute(f'SELECT {SCHEMA}.apply_bundle(%s,%s,%s)', (raw, expected, dry_run)).fetchone()[0]

    def status(self):
        with self.db.transaction():
            self.db.execute(f'SET LOCAL ROLE {IMPORTER}')
            return self.db.execute(f'SELECT {SCHEMA}.status()').fetchone()[0]

    def counts(self):
        return tuple(self.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
                     for table in ('public.batches', 'public.entries', 'public.offers',
                                   'public.publish_events', f'{SCHEMA}.import_ledger'))

    def assert_rejected(self, doc, match=None, expected=BASELINE):
        before = self.counts()
        with self.assertRaises(self.psycopg.Error) as caught:
            self.apply(doc, expected)
        if match:
            self.assertIn(match, str(caught.exception))
        self.assertEqual(self.counts(), before)
        return caught.exception

    def test_role_boundary_and_private_data_denied(self):
        state = self.status()
        self.assertEqual((state['active_batch'], state['entry_count'], state['offer_count']), (BASELINE, 93, 13))
        self.assertNotIn('must never', canonical(state))
        for role in (IMPORTER, OWNER):
            row = self.db.execute('SELECT rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolinherit,rolreplication,rolbypassrls FROM pg_roles WHERE rolname=%s', (role,)).fetchone()
            self.assertEqual(row, (role == IMPORTER, False, False, False, False, False, False))
        self.assertIsNone(self.db.execute('SELECT rolpassword FROM pg_authid WHERE rolname=%s', (IMPORTER,)).fetchone()[0])
        denied = [f'SELECT * FROM public.{t}' for t in
                  ('members','sessions','preferences','conversations','corrections','batches','entries','offers','settings','publish_events')]
        denied += [f'SELECT * FROM {SCHEMA}.import_ledger', f'SET ROLE {OWNER}',
                   'CREATE SCHEMA forbidden', 'CREATE TABLE public.forbidden(id int)',
                   'CREATE ROLE forbidden_role', "UPDATE public.settings SET value='bad'", f"SELECT {SCHEMA}.canonical_strings('{{}}')"]
        # Use a genuinely unprivileged session authorization: SET ROLE alone in
        # an administrator session would still let the session user switch roles.
        for statement in denied:
            with self.subTest(statement=statement):
                with self.assertRaises(self.psycopg.Error):
                    with self.db.transaction():
                        self.db.execute(f'SET LOCAL SESSION AUTHORIZATION {IMPORTER}')
                        self.db.execute(statement)
        for table in ('batches','publish_events'):
            self.assertFalse(self.db.execute('SELECT has_table_privilege(%s,%s,%s)', (OWNER, f'public.{table}', 'UPDATE,DELETE,TRUNCATE')).fetchone()[0])

    def test_owner_future_functions_do_not_grant_public_execute(self):
        with self.db.transaction():
            self.db.execute(f'SET LOCAL ROLE {OWNER}')
            self.db.execute(f"CREATE FUNCTION {SCHEMA}.future_private() RETURNS integer LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog AS $$SELECT 1$$")
        self.assertFalse(self.db.execute('SELECT has_function_privilege(%s,%s,%s)',
                         (IMPORTER, f'{SCHEMA}.future_private()', 'EXECUTE')).fetchone()[0])
        with self.assertRaises(self.psycopg.Error):
            with self.db.transaction():
                self.db.execute(f'SET LOCAL SESSION AUTHORIZATION {IMPORTER}')
                self.db.execute(f'SELECT {SCHEMA}.future_private()')

    def test_dry_run_bootstrap_and_idempotency(self):
        doc = document()
        before = self.counts()
        result = self.apply(doc, dry_run=True)
        self.assertTrue(result['bootstrap'])
        self.assertTrue(result['unchanged'])
        self.assertEqual(self.counts(), before)
        self.assertIsNone(self.status()['source'])
        result = self.apply(doc)
        self.assertEqual(self.counts(), (1, 93, 13, 1, 1))
        self.assertTrue(result['unchanged'])
        self.assertTrue(self.apply(doc)['idempotent'])
        self.assertEqual(self.counts(), (1, 93, 13, 1, 1))
        self.assertEqual(self.status()['source']['version'], 7)

    def test_append_preserves_every_prior_entry_and_offer(self):
        self.apply()
        doc = document(self.entries + [entry(93)], 8)
        self.assertEqual(self.apply(doc, dry_run=True)['added'], 1)
        self.assertEqual(self.counts(), (1, 93, 13, 1, 1))
        result = self.apply(doc)
        new = result['active_batch']
        self.assertNotEqual(new, BASELINE)
        self.assertEqual(self.counts(), (2, 187, 26, 2, 2))
        for table, cols in [('entries', 'entry_key,content_hash,payload'),
                            ('offers', 'id,entry_key,amount_cents,max_cents,price_type,payload')]:
            missing = self.db.execute(f'SELECT {cols} FROM public.{table} WHERE batch_id=%s EXCEPT SELECT {cols} FROM public.{table} WHERE batch_id=%s', (BASELINE, new)).fetchall()
            self.assertEqual(missing, [])
        self.assertTrue(self.apply(doc, expected=new)['idempotent'])
        self.assertEqual(self.db.execute('SELECT previous_batch,action FROM public.publish_events ORDER BY id DESC LIMIT 1').fetchone(), (BASELINE, 'directory_sync'))

    def test_reexport_same_version_is_noop_and_hash_mismatch_rejected(self):
        first = document()
        self.apply(first)
        reexport = copy.deepcopy(first)
        reexport['source']['exported_at'] = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=1)).isoformat().replace('+00:00','Z')
        self.assertTrue(self.apply(reexport)['unchanged'])
        self.assertEqual(self.counts(), (1,93,13,1,2))
        reexport['source']['sha256'] = 'f' * 64
        self.assert_rejected(reexport, 'different workbook hash')
        self.assert_rejected(document(self.entries + [entry(93)], 7), 'without a new source version')

    def test_bootstrap_must_be_exact_and_reviewed(self):
        self.assert_rejected(document(self.entries + [entry(93)]), 'first apply must exactly match')
        self.db.execute("UPDATE public.settings SET value='another' WHERE key='active_batch'")
        self.assert_rejected(document(), 'reviewed active batch', expected='another')

    def test_changes_removals_row_renumbering_and_duplicate_names_rejected(self):
        for field, value in [('mri','$1'),('name','Changed'),('row','10000')]:
            doc = document()
            p = json.loads(doc['entries'][0]['payload']); p[field] = value
            doc['entries'][0] = envelope(p)
            self.assert_rejected(doc)
        self.assert_rejected(document(self.entries[:-1]), 'entry count')
        self.assert_rejected(document(self.entries + [self.entries[0]]), 'duplicate')
        doc = document(self.entries[1:] + [entry(93)])
        self.assert_rejected(doc, 'removing existing')

    def test_hashes_canonicalization_and_payload_keys_rejected(self):
        for field in ('entry_key','content_hash'):
            doc = document(); doc['entries'][0][field] = '0' * 64
            self.assert_rejected(doc, 'hash mismatch')
        doc = document(); doc['entries'][0]['payload'] = ' ' + doc['entries'][0]['payload']
        self.assert_rejected(doc, 'noncanonical')
        for field, value in [('extra','forbidden'),('mri',123),('source',None)]:
            doc = document(); p = json.loads(doc['entries'][0]['payload']); p[field] = value
            doc['entries'][0] = envelope(p)
            self.assert_rejected(doc, 'string-only')
        doc = document(); doc['entries'][0]['content'] = '{}'
        self.assert_rejected(doc, 'string-only')
        doc = document(); p = json.loads(doc['entries'][0]['payload']); del p['mri']
        doc['entries'][0] = envelope(p); self.assert_rejected(doc, 'string-only')

    def test_source_target_freshness_and_no_offers(self):
        for field, value in [('version',6), ('library_file_id','wrong'),('sha256','bad'),
                             ('exported_at','2000-01-01T00:00:00Z'),('exported_at','2999-01-01T00:00:00Z')]:
            doc = document(); doc['source'][field] = value; self.assert_rejected(doc)
        doc = document(); doc['target']['neon_branch_id'] = 'wrong'; self.assert_rejected(doc, 'target')
        doc = document(); doc['offers'] = []; self.assert_rejected(doc, 'offers are never accepted')
        doc = document(); doc['schema_version'] = 2; self.assert_rejected(doc, 'schema')
        with self.db.transaction():
            self.db.execute("SET LOCAL neon.branch_id='wrong'")
            self.assert_rejected(document(), 'wrong database or Neon branch')

    def test_new_entry_url_and_date_validation(self):
        self.apply()
        for field, value in [('source','http://example.com'),('source','https:///missing-host'),
                             ('checked','2999-01-01'),('checked','2026-02-30'),('checked','not-a-date')]:
            p = json.loads(entry(93)['payload']); p[field] = value
            self.assert_rejected(document(self.entries + [envelope(p)], 8))

    def test_source_rollback_external_pointer_and_offer_hash_fail_closed(self):
        self.apply()
        doc = document(self.entries + [entry(93)],8)
        active = self.apply(doc)['active_batch']
        self.assert_rejected(document(self.entries + [entry(93)],7), 'rollback rejected', active)
        self.db.execute("UPDATE public.settings SET value=%s WHERE key='active_batch'", (BASELINE,))
        self.assert_rejected(document(version=9), 'left the import chain')
        self.db.execute("UPDATE public.settings SET value=%s WHERE key='active_batch'", (active,))
        self.db.execute("UPDATE public.offers SET payload='{}' WHERE batch_id=%s AND id='offer-0'", (active,))
        self.assert_rejected(document(self.entries + [entry(93)],9), 'fingerprint changed', active)

    def test_compare_and_swap_and_failed_transaction_leave_no_writes(self):
        self.assert_rejected(document(), 'compare-and-swap', 'stale')
        self.apply()
        before = self.counts()
        # Fail after pointer/catalog writes at the final ledger insert.
        self.db.execute(f"ALTER TABLE {SCHEMA}.import_ledger ADD CONSTRAINT force_rollback CHECK (source_version <> 8)")
        self.assert_rejected(document(self.entries + [entry(93)],8), 'force_rollback')
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.status()['active_batch'], BASELINE)

    def test_concurrent_importer_cannot_publish_over_new_pointer(self):
        self.apply()
        other = self.psycopg.connect(URL, autocommit=True)
        started = threading.Event(); outcomes = []
        def second_import():
            started.set()
            try:
                outcomes.append(self.apply(document(self.entries + [entry(94)],9), connection=other))
            except self.psycopg.Error as exc:
                outcomes.append(str(exc))
        try:
            with self.db.transaction():
                first = self.apply(document(self.entries + [entry(93)],8))
                thread = threading.Thread(target=second_import)
                thread.start(); started.wait(5); time.sleep(0.1)
            thread.join(10)
            self.assertFalse(thread.is_alive())
            self.assertIn('compare-and-swap', outcomes[0])
            self.assertEqual(self.status()['active_batch'], first['active_batch'])
            self.assertEqual(self.counts(), (2,187,26,2,2))
        finally:
            other.close()

    def test_temp_objects_cannot_shadow_security_definer(self):
        self.apply()
        with self.db.transaction():
            self.db.execute(f'SET LOCAL SESSION AUTHORIZATION {IMPORTER}')
            self.db.execute("CREATE TEMP TABLE entries(payload text); INSERT INTO entries VALUES('shadow')")
            self.db.execute("SET LOCAL search_path=pg_temp,public")
            result = self.db.execute(f'SELECT {SCHEMA}.status()').fetchone()[0]
            self.assertEqual(result['entry_count'],93)
            self.assertNotIn('shadow', canonical(result))
            result = self.db.execute(f'SELECT {SCHEMA}.apply_bundle(%s,%s)', (canonical(document()),BASELINE)).fetchone()[0]
            self.assertTrue(result['dry_run'])

    def test_actual_reviewed_fixture_unmodified_production_sql(self):
        fixture_root = Path(__file__).with_name('tests') / 'fixtures'
        doc = json.loads((fixture_root / 'directory-sync-v7.json').read_text())
        offers = json.loads((fixture_root / 'directory-public-offers.json').read_text())
        self.reset_roles()
        self.db.execute('TRUNCATE public.offers, public.entries CASCADE')
        with self.db.cursor() as cur:
            cur.executemany('INSERT INTO public.entries VALUES(%s,%s,%s,%s)',
                            [(BASELINE,e['entry_key'],e['content_hash'],e['payload']) for e in doc['entries']])
            cur.executemany('INSERT INTO public.offers VALUES(%s,%s,%s,%s,%s,%s,%s)',
                            [(BASELINE,o['id'],o['entry_key'],o['amount_cents'],o['max_cents'],o['price_type'],o['payload']) for o in offers])
        self.db.execute(SQL)  # No substitution: the reviewed real fingerprints must match.
        doc['source']['exported_at'] = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00','Z')
        self.assertTrue(self.apply(doc,dry_run=True)['unchanged'])
        self.assertTrue(self.apply(doc)['unchanged'])
        state = self.status()
        self.assertEqual((state['entry_count'],state['offer_count']), (93,13))
        self.assertEqual(state['source']['offer_fingerprint'],state['offer_fingerprint'])
        self.assertEqual(state['source']['entry_fingerprint'],state['entry_fingerprint'])

    def test_duplicate_json_keys_and_unicode_name_whitespace_rejected(self):
        raw = canonical(document()).replace('"schema_version":1', '"schema_version":0,"schema_version":1')
        self.assert_rejected(raw, 'duplicate JSON object keys')
        doc = document()
        doc['entries'][0]['payload'] = doc['entries'][0]['payload'].replace('"row":"1"','"row":"2","row":"1"')
        self.assert_rejected(doc, 'noncanonical')
        for whitespace in (' ', '\t', '\u00a0', '\u0085', '\u2007', '\u3000'):
            p = json.loads(entry(93)['payload']); p['name'] = whitespace + p['name']
            self.assert_rejected(document(self.entries + [envelope(p)],8), 'name or normalized hash')

    def test_current_offer_edit_and_entry_tamper_are_detected(self):
        self.apply()
        self.db.execute('UPDATE public.offers SET amount_cents=1 WHERE batch_id=%s AND id=%s', (BASELINE,'offer-0'))
        self.assertNotEqual(self.status()['source']['offer_fingerprint'], self.status()['offer_fingerprint'])
        self.assert_rejected(document(version=8), 'fingerprint changed')
        self.db.execute('UPDATE public.offers SET amount_cents=12345 WHERE batch_id=%s AND id=%s', (BASELINE,'offer-0'))
        self.db.execute("UPDATE public.entries SET payload=payload||' ' WHERE batch_id=%s AND entry_key=%s", (BASELINE,self.entries[0]['entry_key']))
        self.assert_rejected(document(version=8), 'fingerprint changed')

    def test_setup_rejects_column_grants_schema_creation_and_definer_bypass(self):
        self.reset_roles()
        scenarios = [
          ('GRANT SELECT(payload) ON public.members TO PUBLIC','REVOKE SELECT(payload) ON public.members FROM PUBLIC','unsafe effective access'),
          ('GRANT CREATE ON SCHEMA public TO PUBLIC','REVOKE CREATE ON SCHEMA public FROM PUBLIC','schema CREATE'),
          ("CREATE FUNCTION public.unsafe() RETURNS text LANGUAGE sql SECURITY DEFINER AS $$SELECT payload FROM public.members LIMIT 1$$",'DROP FUNCTION public.unsafe()','security-definer'),
          (f'CREATE SCHEMA {SCHEMA}',f'DROP SCHEMA {SCHEMA}','role or schema already exists'),
          (f'CREATE ROLE {IMPORTER} SUPERUSER',f'DROP ROLE {IMPORTER}','role or schema already exists'),
        ]
        for setup, cleanup, message in scenarios:
            with self.subTest(setup=setup):
                self.db.execute(setup)
                try:
                    with self.assertRaises(self.psycopg.Error) as caught:
                        self.db.execute(self.install_sql)
                    self.assertIn(message,str(caught.exception))
                    self.db.execute('ROLLBACK')
                finally:
                    self.db.execute(cleanup)

    def test_existing_role_and_public_access_abort_setup(self):
        with self.assertRaises(self.psycopg.Error):
            self.db.execute(self.install_sql)
        self.db.execute('ROLLBACK')
        self.reset_roles()
        try:
            self.db.execute('GRANT SELECT ON public.members TO PUBLIC')
            with self.assertRaises(self.psycopg.Error) as caught:
                self.db.execute(self.install_sql)
            self.assertIn('unsafe effective access', str(caught.exception))
            self.db.execute('ROLLBACK')
            self.assertFalse(self.db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (IMPORTER,)).fetchone())
        finally:
            self.db.execute('REVOKE SELECT ON public.members FROM PUBLIC')


if __name__ == '__main__':
    unittest.main(verbosity=2)
