"""Tests for the single-prepared-statement provisioning transport wrapper.

Uses the same explicit, LOCAL-ONLY destructive test opt-in and throwaway neondb
as test_directory_sync_postgres. No hosted connection or credential discovery.
The original reviewed SQL file is never modified by this module.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path
import unittest

import test_directory_sync_postgres as base

ROOT = Path(__file__).resolve().parent
SOURCE_SHA256 = 'd612ff80a99e0102b5f17eb7ba59eb5e932bb4d3dc58b8c7b264cc512f0ba2aa'
WRAPPER_SHA256 = 'e40eaf6a20c30320810308f18d91c56f9a0891e7c49c55deaaf51e70e873518b'
ORIGINAL = (ROOT / 'ops' / 'directory_sync.sql').read_bytes()
WRAPPER = (ROOT / 'ops' / 'directory_sync_query.sql').read_bytes()
PACKAGE_DELIMITER = b'$directory_sync_package$'
ADMIN = 'selfpay_query_test_admin'


class DirectorySyncQueryCorrespondence(unittest.TestCase):
    def test_wrapper_embeds_exact_reviewed_bytes_except_transaction_lines(self):
        self.assertEqual(hashlib.sha256(ORIGINAL).hexdigest(), SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(WRAPPER).hexdigest(), WRAPPER_SHA256)
        lines = ORIGINAL.splitlines(keepends=True)
        self.assertEqual(lines.count(b'BEGIN;\n'), 1)
        self.assertEqual(lines.count(b'COMMIT;\n'), 1)
        expected_body = b''.join(line for line in lines if line not in (b'BEGIN;\n', b'COMMIT;\n'))
        self.assertEqual(WRAPPER.count(PACKAGE_DELIMITER), 2)
        embedded = WRAPPER.split(PACKAGE_DELIMITER)[1]
        self.assertEqual(embedded, b'\n' + expected_body)
        self.assertIn(SOURCE_SHA256.encode(), WRAPPER)
        self.assertTrue(WRAPPER.endswith(b'$directory_sync_package$;\nEND\n$directory_sync_query$;\n'))


@unittest.skipUnless(base.ENABLED, 'explicit local throwaway PostgreSQL test URL/reset opt-in required')
class DirectorySyncQueryPostgres(unittest.TestCase):
    reset_roles = classmethod(base.DirectorySyncPostgres.reset_roles.__func__)
    setUpClass = classmethod(base.DirectorySyncPostgres.setUpClass.__func__)
    tearDownClass = classmethod(base.DirectorySyncPostgres.tearDownClass.__func__)
    apply = base.DirectorySyncPostgres.apply
    status = base.DirectorySyncPostgres.status
    counts = base.DirectorySyncPostgres.counts

    def setUp(self):
        self.reset_roles()
        self.db.execute('TRUNCATE public.publish_events, public.offers, public.entries, public.batches, public.settings RESTART IDENTITY CASCADE')
        self.doc = json.loads((ROOT / 'tests/fixtures/directory-sync-v7.json').read_text())
        offers = json.loads((ROOT / 'tests/fixtures/directory-public-offers.json').read_text())
        self.doc['source']['exported_at'] = dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
        self.db.execute('INSERT INTO public.batches VALUES(%s,%s,%s,0,%s,%s)',
                        (base.BASELINE, base.digest('legacy-signature'), 'reviewed', 'published', '{}'))
        with self.db.cursor() as cur:
            cur.executemany('INSERT INTO public.entries VALUES(%s,%s,%s,%s)',
                            [(base.BASELINE,e['entry_key'],e['content_hash'],e['payload']) for e in self.doc['entries']])
            cur.executemany('INSERT INTO public.offers VALUES(%s,%s,%s,%s,%s,%s,%s)',
                            [(base.BASELINE,o['id'],o['entry_key'],o['amount_cents'],o['max_cents'],o['price_type'],o['payload']) for o in offers])
        self.db.execute("INSERT INTO public.settings VALUES('active_batch',%s)", (base.BASELINE,))
        self.db.execute("INSERT INTO public.publish_events(batch_id,previous_batch,created,action) VALUES(%s,NULL,0,'publish')", (base.BASELINE,))

    def catalog_fingerprints(self):
        return tuple(self.db.execute(f"SELECT md5(coalesce(jsonb_agg(to_jsonb(x) ORDER BY {key})::text,'[]')) FROM public.{table} x WHERE batch_id=%s", (base.BASELINE,)).fetchone()[0]
                     for table,key in [('entries','entry_key'),('offers','id')])

    def grant_snapshot(self):
        queries = [
            "SELECT oid,rolname,rolcanlogin,rolcreaterole,rolsuper FROM pg_roles ORDER BY oid",
            "SELECT * FROM pg_auth_members ORDER BY roleid,member,grantor",
            "SELECT oid,nspname,nspowner,nspacl::text FROM pg_namespace ORDER BY oid",
            "SELECT c.oid,c.relname,c.relowner,c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' ORDER BY c.oid",
            "SELECT oid,datname,datdba,datacl::text FROM pg_database WHERE datname=current_database()",
            "SELECT oid,defaclrole,defaclnamespace,defaclobjtype,defaclacl::text FROM pg_default_acl ORDER BY oid",
        ]
        return [self.db.execute(query).fetchall() for query in queries]

    def verify_provisioned(self):
        state = self.status()
        self.assertEqual((state['active_batch'],state['entry_count'],state['offer_count']), (base.BASELINE,93,13))
        self.assertIsNone(state['source'])
        rows = self.db.execute("SELECT p.proname,r.rolname,p.proconfig,p.prosecdef FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace JOIN pg_roles r ON r.oid=p.proowner WHERE n.nspname=%s", (base.SCHEMA,)).fetchall()
        self.assertEqual(len(rows),6)
        self.assertTrue(all(row[1] == base.OWNER and row[2] == ['search_path=pg_catalog'] for row in rows))
        self.assertEqual({row[0] for row in rows if row[3]}, {'status','apply_bundle'})
        self.assertFalse(self.db.execute('SELECT has_table_privilege(%s,%s,%s)', (base.IMPORTER,'public.members','SELECT')).fetchone()[0])
        self.assertFalse(self.db.execute('SELECT pg_has_role(%s,%s,%s)', (base.IMPORTER,base.OWNER,'MEMBER')).fetchone()[0])
        self.assertEqual(self.catalog_fingerprints(), ('be0290bd19eff19066766e8644245122','711a7c77b51e6107e7d7326229366a4b'))

    def test_original_rejected_by_prepared_protocol_before_execution(self):
        before = self.grant_snapshot()
        with self.assertRaises(self.psycopg.errors.SyntaxError) as caught:
            self.db.execute(ORIGINAL.decode(), prepare=True)
        self.assertIn('multiple commands', str(caught.exception))
        self.assertEqual(self.grant_snapshot(), before)

    def test_prepared_wrapper_succeeds_and_retains_guarded_import_behavior(self):
        self.db.execute(WRAPPER.decode(), prepare=True)
        self.verify_provisioned()
        self.assertTrue(self.apply(self.doc, dry_run=True)['unchanged'])
        self.assertEqual(self.counts(), (1,93,13,1,0))
        self.assertTrue(self.apply(self.doc)['unchanged'])
        self.assertEqual(self.counts(), (1,93,13,1,1))
        self.assertTrue(self.apply(self.doc)['idempotent'])
        new_doc = json.loads(json.dumps(self.doc))
        new_doc['source'].update(version=8,sha256=base.digest('new-workbook'))
        new_doc['entries'].append(base.entry(1000))
        result = self.apply(new_doc)
        self.assertEqual((result['added'],result['offer_count']), (1,13))
        self.assertEqual(self.counts(), (2,187,26,2,2))

    def test_prepared_wrapper_final_audit_failure_rolls_back_every_grant(self):
        self.db.execute('GRANT SELECT ON public.members TO PUBLIC')
        try:
            before = self.grant_snapshot()
            catalog_before = self.catalog_fingerprints()
            with self.assertRaises(self.psycopg.Error) as caught:
                self.db.execute(WRAPPER.decode(), prepare=True)
            self.assertIn('unsafe effective access to public.members',str(caught.exception))
            self.assertEqual(self.grant_snapshot(), before)
            self.assertEqual(self.catalog_fingerprints(), catalog_before)
            self.assertIsNone(self.db.execute('SELECT to_regnamespace(%s)',(base.SCHEMA,)).fetchone()[0])
            self.assertFalse(self.db.execute('SELECT 1 FROM pg_roles WHERE rolname=ANY(%s)',([base.OWNER,base.IMPORTER],)).fetchone())
        finally:
            self.db.execute('REVOKE SELECT ON public.members FROM PUBLIC')

    def run_as_database_owner(self, fail_late=False, noinherit=False):
        original_user = self.db.execute('SELECT session_user').fetchone()[0]
        original_db_owner = self.db.execute('SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()').fetchone()[0]
        tables = [row[0] for row in self.db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()]
        sql = self.psycopg.sql
        inheritance = 'NOINHERIT' if noinherit else 'INHERIT'
        self.db.execute(f'CREATE ROLE {ADMIN} LOGIN NOSUPERUSER NOCREATEDB CREATEROLE {inheritance} NOREPLICATION NOBYPASSRLS')
        self.db.execute(f'ALTER DATABASE neondb OWNER TO {ADMIN}')
        self.db.execute(f'ALTER SCHEMA public OWNER TO {ADMIN}')
        for table in tables:
            self.db.execute(sql.SQL('ALTER TABLE public.{} OWNER TO {}').format(sql.Identifier(table),sql.Identifier(ADMIN)))
        if fail_late:
            self.db.execute('GRANT SELECT ON public.members TO PUBLIC')
        try:
            before = self.grant_snapshot()
            # Equivalent server permissions to an authenticated role, without
            # creating a password or changing local authentication configuration.
            self.db.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
            self.assertEqual(self.db.execute('SELECT current_user,session_user').fetchone(),(ADMIN,ADMIN))
            self.assertEqual(self.db.execute('SELECT rolsuper,rolcreaterole FROM pg_roles WHERE rolname=current_user').fetchone(),(False,True))
            if fail_late or noinherit:
                with self.assertRaises(self.psycopg.Error) as caught:
                    self.db.execute(WRAPPER.decode(), prepare=True)
                expected = 'permission denied for schema selfpay_directory_sync' if noinherit else 'unsafe effective access to public.members'
                self.assertIn(expected,str(caught.exception))
                self.db.execute('RESET SESSION AUTHORIZATION')
                self.assertEqual(self.grant_snapshot(),before)
            else:
                self.db.execute(WRAPPER.decode(), prepare=True)
                self.assertEqual(self.db.execute('SELECT current_user,session_user').fetchone(),(ADMIN,ADMIN))
                memberships = self.db.execute("SELECT m.admin_option,m.inherit_option,m.set_option,pg_get_userbyid(m.grantor) FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid JOIN pg_roles member_role ON member_role.oid=m.member WHERE r.rolname=%s AND member_role.rolname=%s", (base.OWNER,ADMIN)).fetchall()
                self.assertEqual([row[:3] for row in memberships], [(True,False,False)])
                self.assertTrue(self.db.execute('SELECT pg_has_role(%s,%s,%s)',(ADMIN,base.OWNER,'MEMBER')).fetchone()[0])
                for privilege in ('USAGE','SET'):
                    self.assertFalse(self.db.execute('SELECT pg_has_role(%s,%s,%s)',(ADMIN,base.OWNER,privilege)).fetchone()[0])
                # The automatic ADMIN-only creator membership survives; its
                # explicit maintenance grant does not widen importer access.
                self.db.execute(f'GRANT {base.OWNER} TO {ADMIN}')
                self.assertTrue(self.db.execute('SELECT pg_has_role(%s,%s,%s)',(ADMIN,base.OWNER,'SET')).fetchone()[0])
                self.db.execute(f'SET ROLE {base.OWNER}')
                self.db.execute(f'CREATE FUNCTION {base.SCHEMA}.maintenance_probe() RETURNS integer LANGUAGE sql SET search_path=pg_catalog AS $$SELECT 1$$')
                self.assertFalse(self.db.execute('SELECT has_function_privilege(%s,%s,%s)',(base.IMPORTER,f'{base.SCHEMA}.maintenance_probe()','EXECUTE')).fetchone()[0])
                self.db.execute(f'DROP FUNCTION {base.SCHEMA}.maintenance_probe()')
                self.db.execute('RESET ROLE')
                self.db.execute(f'REVOKE {base.OWNER} FROM {ADMIN}')
                self.assertFalse(self.db.execute('SELECT pg_has_role(%s,%s,%s)',(ADMIN,base.OWNER,'SET')).fetchone()[0])
                self.db.execute('RESET SESSION AUTHORIZATION')
                self.verify_provisioned()
                self.assertTrue(self.apply(self.doc)['unchanged'])
        finally:
            self.db.execute('RESET SESSION AUTHORIZATION')
            self.reset_roles()
            self.db.execute('REVOKE SELECT ON public.members FROM PUBLIC')
            self.db.execute(sql.SQL('ALTER DATABASE neondb OWNER TO {}').format(sql.Identifier(original_db_owner)))
            self.db.execute(sql.SQL('ALTER SCHEMA public OWNER TO {}').format(sql.Identifier(original_user)))
            for table in tables:
                self.db.execute(sql.SQL('ALTER TABLE public.{} OWNER TO {}').format(sql.Identifier(table),sql.Identifier(original_user)))
            self.db.execute(f'DROP OWNED BY {ADMIN}; DROP ROLE {ADMIN}')

    def test_prepared_wrapper_under_non_superuser_database_owner(self):
        self.run_as_database_owner()

    def test_noinherit_admin_original_prerequisite_fails_closed(self):
        self.run_as_database_owner(noinherit=True)

    def test_late_failure_under_non_superuser_rolls_back_memberships_and_grants(self):
        self.run_as_database_owner(fail_late=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
