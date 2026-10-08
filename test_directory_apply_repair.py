"""Exact, manual-only apply_bundle repair and LOCAL-ONLY PostgreSQL tests.

No hosted connection, credential discovery, or external SQL fixture is used.
The only three installed-body edits are reconstructed from the reviewed SQL and
pinned by the independently observed prosrc hash. Database tests use the same
explicit localhost/neondb/reset opt-in as test_directory_sync_postgres.

CI: python -m unittest test_directory_apply_repair -v
Integration CI also requires DIRECTORY_SYNC_TEST_ALLOW_RESET=1 and the existing
DIRECTORY_SYNC_TEST_DATABASE_URL localhost fixture (PostgreSQL 16 or later).
"""
import copy
import hashlib
from pathlib import Path
import re
import unittest

import test_directory_sync_postgres as base
import test_directory_sync_query_postgres as query

ROOT = Path(__file__).resolve().parent
ADMIN = 'neondb_owner'
GOOD_HASH = 'bf710be762cfcc0c3eb95a7692032d27eadc05f5e202a30dcca5ef1fac794b61'
BAD_HASH = '9092aefd2bc6e60858b646c9163728d5510086f003d90052288dfacdb74a15f9'
REPAIR_SHA256 = '46717bc03ab1eae171ccadeadf956ed8ca0e2c0635c1069a6dbc214e61b4dd98'
REPAIR = (ROOT / 'ops' / 'repair_directory_apply.sql').read_text()
start = base.SQL.index('CREATE FUNCTION selfpay_directory_sync.apply_bundle(')
end = base.SQL.index('$function$;', start) + len('$function$;')
REVIEWED = base.SQL[start:end]
REPLACEMENT = REVIEWED.replace('CREATE FUNCTION', 'CREATE OR REPLACE FUNCTION', 1)
GOOD_BODY = REVIEWED.split('$function$')[1]
BAD_BODY = GOOD_BODY.replace('e.entry_key = guarded.entry_key', "e.entry_key = entry->>'entry_key'").replace(
    'l.document_hash = guarded.document_hash', 'l.document_hash = document_hash')
INSTALLED = REPLACEMENT.replace(GOOD_BODY, BAD_BODY)
FUNCTION = f'{base.SCHEMA}.apply_bundle(text,text,boolean)'


class DirectoryApplyRepairCorrespondence(unittest.TestCase):
    def test_exact_reviewed_block_embedded_without_body_edits(self):
        self.assertEqual(hashlib.sha256(query.ORIGINAL).hexdigest(), query.SOURCE_SHA256)
        self.assertEqual(hashlib.sha256(REPAIR.encode()).hexdigest(), REPAIR_SHA256)
        self.assertEqual(REPAIR.count('$reviewed_apply_bundle$'), 2)
        self.assertEqual(REPAIR.split('$reviewed_apply_bundle$')[1], '\n' + REPLACEMENT + '\n')
        self.assertEqual(hashlib.sha256(GOOD_BODY.encode()).hexdigest(), GOOD_HASH)
        self.assertEqual(hashlib.sha256(BAD_BODY.encode()).hexdigest(), BAD_HASH)
        self.assertEqual(GOOD_BODY.count('e.entry_key = guarded.entry_key'), 2)
        self.assertEqual(GOOD_BODY.count('l.document_hash = guarded.document_hash'), 1)

    def test_only_expected_mutating_commands_and_single_do_transport(self):
        outer = REPAIR.split('$reviewed_apply_bundle$')[0] + REPAIR.split('$reviewed_apply_bundle$')[2]
        without_comments = '\n'.join(line for line in outer.splitlines() if not line.lstrip().startswith('--'))
        self.assertIsNone(re.search(r'\b(?:CREATE|ALTER|DROP|INSERT|UPDATE|DELETE|TRUNCATE)\b', without_comments, re.I))
        self.assertEqual(REPAIR.count('CREATE OR REPLACE FUNCTION'), 2)  # Header + embedded definition.
        self.assertEqual(REPAIR.count('GRANT selfpay_directory_owner'), 1)
        self.assertEqual(REPAIR.count('REVOKE selfpay_directory_owner'), 1)
        self.assertIn('WITH INHERIT TRUE, SET FALSE', REPAIR)
        self.assertTrue(REPAIR.rstrip().endswith('$directory_apply_repair$;'))
        self.assertNotIn('EXCEPTION WHEN', REPAIR)


@unittest.skipUnless(base.ENABLED, 'explicit local throwaway PostgreSQL test URL/reset opt-in required')
class DirectoryApplyRepairPostgres(unittest.TestCase):
    reset_roles = classmethod(base.DirectorySyncPostgres.reset_roles.__func__)
    apply = base.DirectorySyncPostgres.apply
    status = base.DirectorySyncPostgres.status
    counts = base.DirectorySyncPostgres.counts

    @classmethod
    def setUpClass(cls):
        base.DirectorySyncPostgres.setUpClass.__func__(cls)
        if cls.db.info.server_version < 160000:
            raise RuntimeError('Repair membership tests require PostgreSQL 16 or later')
        if cls.db.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', (ADMIN,)).fetchone():
            raise RuntimeError('Refusing to reuse an existing neondb_owner test administrator')
        cls.original_user = cls.db.execute('SELECT session_user').fetchone()[0]
        cls.original_db_owner = cls.db.execute('SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()').fetchone()[0]

    @classmethod
    def tearDownClass(cls):
        base.DirectorySyncPostgres.tearDownClass.__func__(cls)

    def setUp(self):
        query.DirectorySyncQueryPostgres.setUp(self)
        self.tables = [row[0] for row in self.db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall()]
        self.db.execute(f'CREATE ROLE {ADMIN} LOGIN NOSUPERUSER NOCREATEDB CREATEROLE INHERIT NOREPLICATION NOBYPASSRLS')
        self.db.execute(f'ALTER DATABASE neondb OWNER TO {ADMIN}')
        self.db.execute(f'ALTER SCHEMA public OWNER TO {ADMIN}')
        for table in self.tables:
            self.db.execute(self.psycopg.sql.SQL('ALTER TABLE public.{} OWNER TO {}').format(
                self.psycopg.sql.Identifier(table), self.psycopg.sql.Identifier(ADMIN)))
        self.db.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
        try:
            self.db.execute(query.WRAPPER.decode(), prepare=True)
        finally:
            self.db.execute('RESET SESSION AUTHORIZATION')
        self.db.execute(INSTALLED)
        self.assertEqual(self.body_hash(), BAD_HASH)
        self.assertEqual(self.db.execute('SHOW plpgsql.variable_conflict').fetchone()[0], 'error')
        self.assert_automatic_memberships()

    def tearDown(self):
        self.db.execute('RESET SESSION AUTHORIZATION')
        self.reset_roles()
        sql = self.psycopg.sql
        self.db.execute(sql.SQL('ALTER DATABASE neondb OWNER TO {}').format(sql.Identifier(self.original_db_owner)))
        self.db.execute(sql.SQL('ALTER SCHEMA public OWNER TO {}').format(sql.Identifier(self.original_user)))
        for table in self.tables:
            self.db.execute(sql.SQL('ALTER TABLE public.{} OWNER TO {}').format(sql.Identifier(table), sql.Identifier(self.original_user)))
        self.db.execute(f'DROP OWNED BY {ADMIN}; DROP ROLE {ADMIN}')

    def body_hash(self):
        return self.db.execute("SELECT encode(sha256(convert_to(prosrc,'UTF8')),'hex') FROM pg_proc WHERE oid=%s::regprocedure", (FUNCTION,)).fetchone()[0]

    def assert_automatic_memberships(self):
        rows = self.db.execute('''SELECT r.rolname, m.admin_option, m.inherit_option, m.set_option,
            m.grantor = m.member FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid
            JOIN pg_roles u ON u.oid=m.member WHERE r.rolname=ANY(%s) AND u.rolname=%s ORDER BY r.rolname''',
            ([base.OWNER, base.IMPORTER], ADMIN)).fetchall()
        self.assertEqual(rows, [(base.IMPORTER, True, False, False, False), (base.OWNER, True, False, False, False)])
        for role in (base.OWNER, base.IMPORTER):
            for privilege in ('USAGE', 'SET'):
                self.assertFalse(self.db.execute('SELECT pg_has_role(%s,%s,%s)', (ADMIN, role, privilege)).fetchone()[0])
        self.assertFalse(self.db.execute('SELECT pg_has_role(%s,%s,%s)', (base.IMPORTER, base.OWNER, 'MEMBER')).fetchone()[0])

    def repair(self, statement=REPAIR):
        self.db.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
        try:
            with self.db.transaction():
                self.db.execute(statement, prepare=True)
                self.assertEqual(self.db.execute('SELECT current_user,session_user').fetchone(), (ADMIN, ADMIN))
        finally:
            self.db.execute('RESET SESSION AUTHORIZATION')

    def snapshot(self, include_body=True):
        queries = [
            "SELECT to_jsonb(r)-'rolpassword' FROM pg_roles r ORDER BY oid",
            'SELECT to_jsonb(m) FROM pg_auth_members m ORDER BY roleid,member,grantor',
            'SELECT to_jsonb(n) FROM pg_namespace n ORDER BY oid',
            '''SELECT c.oid,c.relowner,c.relacl::text FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
               WHERE n.nspname IN ('public','selfpay_directory_sync') ORDER BY c.oid''',
            '''SELECT a.attrelid,a.attnum,a.attacl::text FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid
               JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname IN ('public','selfpay_directory_sync')
               ORDER BY a.attrelid,a.attnum''',
            'SELECT oid,datdba,datacl::text FROM pg_database ORDER BY oid',
            'SELECT to_jsonb(d) FROM pg_default_acl d ORDER BY oid',
        ]
        state = [self.db.execute(q).fetchall() for q in queries]
        functions = self.db.execute("SELECT (to_jsonb(p)-'proargdefaults') || jsonb_build_object('argument_defaults',pg_get_expr(p.proargdefaults,0)) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname=%s ORDER BY p.oid", (base.SCHEMA,)).fetchall()
        for (function,) in functions:
            if function['proname'] == 'apply_bundle' and not include_body:
                del function['prosrc']
        state.append(functions)
        for schema in ('public', base.SCHEMA):
            for (table,) in self.db.execute('SELECT tablename FROM pg_tables WHERE schemaname=%s ORDER BY tablename', (schema,)):
                statement = self.psycopg.sql.SQL("SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text),'[]') FROM {}.{} t").format(
                    self.psycopg.sql.Identifier(schema), self.psycopg.sql.Identifier(table))
                state.append(self.db.execute(statement).fetchall())
            for (sequence,) in self.db.execute('SELECT sequencename FROM pg_sequences WHERE schemaname=%s ORDER BY sequencename', (schema,)):
                state.append(self.db.execute(self.psycopg.sql.SQL('SELECT last_value,is_called FROM {}.{}').format(
                    self.psycopg.sql.Identifier(schema), self.psycopg.sql.Identifier(sequence))).fetchall())
        return state

    def assert_repair_rejected(self, match, statement=REPAIR):
        before = self.snapshot()
        with self.assertRaises(self.psycopg.Error) as caught:
            self.repair(statement)
        self.assertIn(match, str(caught.exception))
        self.assertEqual(self.snapshot(), before)
        return caught.exception

    def test_installed_failure_reproduced_before_repair_and_guarded_imports_work_after(self):
        before = self.snapshot()
        self.assertTrue(self.apply(self.doc, dry_run=True)['unchanged'])
        self.assertEqual(self.snapshot(), before)
        with self.assertRaises(self.psycopg.errors.AmbiguousColumn) as caught:
            self.apply(self.doc)
        self.assertIn('document_hash', str(caught.exception))
        self.assertEqual(self.snapshot(), before)
        unchanged = self.snapshot(include_body=False)
        self.repair()
        self.assertEqual(self.body_hash(), GOOD_HASH)
        self.assertEqual(self.snapshot(include_body=False), unchanged)
        self.assert_automatic_memberships()
        self.assertTrue(self.apply(self.doc, dry_run=True)['unchanged'])
        self.assertEqual(self.counts(), (1,93,13,1,0))
        self.assertTrue(self.apply(self.doc)['bootstrap'])
        self.assertEqual(self.counts(), (1,93,13,1,1))
        self.assertTrue(self.apply(self.doc)['idempotent'])
        self.assertEqual(self.counts(), (1,93,13,1,1))
        new_doc = copy.deepcopy(self.doc)
        new_doc['source'].update(version=8, sha256=base.digest('new-workbook'))
        new_doc['entries'].append(base.entry(1000))
        self.assertEqual(self.apply(new_doc, dry_run=True)['added'], 1)
        self.assertEqual(self.counts(), (1,93,13,1,1))
        result = self.apply(new_doc)
        self.assertEqual((result['added'], result['offer_count']), (1,13))
        self.assertEqual(self.counts(), (2,187,26,2,2))
        self.assertTrue(self.apply(new_doc, expected=result['active_batch'])['idempotent'])
        self.assertEqual(self.counts(), (2,187,26,2,2))
        for table, columns in [('entries','entry_key,content_hash,payload'), ('offers','id,entry_key,amount_cents,max_cents,price_type,payload')]:
            self.assertEqual(self.db.execute(f'SELECT {columns} FROM public.{table} WHERE batch_id=%s EXCEPT SELECT {columns} FROM public.{table} WHERE batch_id=%s',
                                            (base.BASELINE, result['active_batch'])).fetchall(), [])
        self.assert_repair_rejected('ledger must still be empty')

    def test_prepared_statement_autocommit_success_and_late_failure(self):
        marker = '  -- Final checks happen inside the same statement. No exception is caught.'
        injected = REPAIR.replace(marker, "  RAISE EXCEPTION 'test-only autocommit late failure';\n" + marker)
        before = self.snapshot()
        self.db.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
        try:
            self.assertTrue(self.db.autocommit)
            with self.assertRaises(self.psycopg.Error) as caught:
                self.db.execute(injected, prepare=True)
            self.assertIn('test-only autocommit late failure', str(caught.exception))
        finally:
            self.db.execute('RESET SESSION AUTHORIZATION')
        self.assertEqual(self.snapshot(), before)
        unchanged = self.snapshot(include_body=False)
        self.db.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
        try:
            self.db.execute(REPAIR, prepare=True)
        finally:
            self.db.execute('RESET SESSION AUTHORIZATION')
        self.assertEqual(self.body_hash(), GOOD_HASH)
        self.assertEqual(self.snapshot(include_body=False), unchanged)
        self.assert_automatic_memberships()

    def test_already_correct_is_exact_noop_only_at_verified_baseline(self):
        self.repair()
        before = self.snapshot()
        self.repair()
        self.assertEqual(self.snapshot(), before)
        self.assert_automatic_memberships()
        self.db.execute("UPDATE public.settings SET value='moved' WHERE key='active_batch'")
        self.assert_repair_rejected('reviewed active batch or baseline counts changed')

    def test_unknown_body_aborts_without_overwriting(self):
        self.db.execute(INSTALLED.replace(BAD_BODY, BAD_BODY + '\n-- unreviewed change\n'))
        self.assert_repair_rejected('unknown apply_bundle body')

    def test_wrong_branch_aborts(self):
        self.db.execute("SET neon.branch_id = 'wrong-branch'")
        try:
            self.assert_repair_rejected('wrong database or Neon branch')
        finally:
            self.db.execute(self.psycopg.sql.SQL('SET neon.branch_id = {}').format(self.psycopg.sql.Literal(base.BRANCH)))

    def test_wrong_database_aborts(self):
        before = self.snapshot()
        with self.psycopg.connect(base.URL, dbname='postgres', autocommit=True) as other:
            other.execute(f'SET SESSION AUTHORIZATION {ADMIN}')
            with self.assertRaises(self.psycopg.Error) as caught:
                other.execute(REPAIR, prepare=True)
            self.assertIn('wrong database or Neon branch', str(caught.exception))
        self.assertEqual(self.snapshot(), before)

    def test_nonempty_ledger_aborts(self):
        self.db.execute(REPLACEMENT)
        self.apply(self.doc)
        self.db.execute(INSTALLED)
        self.assert_repair_rejected('ledger must still be empty')

    def test_active_pointer_and_entry_and_offer_counts_are_exact(self):
        cases = [
            ("UPDATE public.settings SET value='changed' WHERE key='active_batch'", None),
            ("INSERT INTO public.entries VALUES(%s,%s,%s,%s)", (base.BASELINE, base.digest('unexpected'), base.digest('unexpected-content'), '{}')),
            ("DELETE FROM public.offers WHERE id=(SELECT min(id) FROM public.offers)", None),
        ]
        for statement, parameters in cases:
            with self.subTest(statement=statement):
                with self.db.transaction(force_rollback=True):
                    self.db.execute(statement, parameters)
                    self.assert_repair_rejected('reviewed active batch or baseline counts changed')

    def test_full_row_entry_and_offer_hash_guards(self):
        for table, statement in [
            ('entries', "UPDATE public.entries SET payload=payload || ' ' WHERE entry_key=(SELECT min(entry_key) FROM public.entries)"),
            ('offers', "UPDATE public.offers SET payload=payload || ' ' WHERE id=(SELECT min(id) FROM public.offers)"),
        ]:
            with self.subTest(table=table):
                with self.db.transaction(force_rollback=True):
                    self.db.execute(statement)
                    self.assert_repair_rejected('reviewed bootstrap full-row fingerprint mismatch')

    def test_wrong_function_metadata_aborts(self):
        for statement in [
            f'ALTER FUNCTION {FUNCTION} OWNER TO {ADMIN}',
            f'ALTER FUNCTION {FUNCTION} SECURITY INVOKER',
            f'ALTER FUNCTION {FUNCTION} SET search_path TO public',
            f'GRANT EXECUTE ON FUNCTION {FUNCTION} TO PUBLIC',
        ]:
            with self.subTest(statement=statement):
                with self.db.transaction(force_rollback=True):
                    self.db.execute(statement)
                    self.assert_repair_rejected('unexpected apply_bundle signature, owner, configuration, or permissions')

    def test_wrong_role_schema_and_memberships_abort(self):
        for statement, message in [
            (f'ALTER ROLE {base.IMPORTER} INHERIT', 'unexpected owner/importer role attributes'),
            (f'GRANT USAGE ON SCHEMA {base.SCHEMA} TO PUBLIC', 'unexpected schema owner or permissions'),
            (f'GRANT {base.OWNER} TO {base.IMPORTER}', 'expected automatic ADMIN-only memberships'),
        ]:
            with self.subTest(statement=statement):
                with self.db.transaction(force_rollback=True):
                    self.db.execute(statement)
                    self.assert_repair_rejected(message)

    def test_late_failure_after_replacement_and_revoke_rolls_back_everything(self):
        marker = '  -- Final checks happen inside the same statement. No exception is caught.'
        self.assertEqual(REPAIR.count(marker), 1)
        injected = REPAIR.replace(marker, "  RAISE EXCEPTION 'test-only late failure after replacement and revoke';\n" + marker)
        self.assert_repair_rejected('test-only late failure after replacement and revoke', injected)
        self.assertEqual(self.body_hash(), BAD_HASH)
        self.assert_automatic_memberships()

    def test_final_hash_audit_failure_rolls_back_replacement_and_membership(self):
        # Mutate only the embedded definition in this local test, not the file.
        mutated = REPAIR.replace(REPLACEMENT, REPLACEMENT.replace(GOOD_BODY, GOOD_BODY + '\n-- test-only bad replacement\n'))
        self.assert_repair_rejected('final function body or metadata mismatch', mutated)
        self.assertEqual(self.body_hash(), BAD_HASH)
        self.assert_automatic_memberships()

    def test_no_function_creation_if_signature_missing(self):
        self.db.execute(f'DROP FUNCTION {FUNCTION}')
        self.assert_repair_rejected('unexpected apply_bundle signature, owner, configuration, or permissions')

    def test_preserves_caller_settings_even_in_explicit_transaction(self):
        with self.db.transaction():
            self.db.execute("SET LOCAL search_path = public, pg_catalog; SET LOCAL lock_timeout = '4s'")
            self.repair()
            self.assertEqual(self.db.execute('SHOW search_path').fetchone()[0], 'public, pg_catalog')
            self.assertEqual(self.db.execute('SHOW lock_timeout').fetchone()[0], '4s')
        self.assertEqual(self.body_hash(), GOOD_HASH)


if __name__ == '__main__':
    unittest.main(verbosity=2)
