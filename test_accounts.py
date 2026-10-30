import concurrent.futures
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import accounts
import core
import server
import test_functional

class AccountTests(unittest.TestCase):
    req = test_functional.FunctionalTests.req
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name)/'accounts.db'
        core.initialize(self.db)
        self.port = 8765
        self.http = SimpleNamespace(server_port=self.port, db_path=self.db, login_attempts=[])
        self.data = dict(name='Synthetic Test', email='synthetic@example.com', phone='+1 555 010 1234', password='Synthetic-only-passphrase!')

    def tearDown(self): self.temp.cleanup()

    def submit(self, action='register', data=None, auth=None, headers=None):
        return self.req('/api/'+action, self.data if data is None else data, auth=auth,
                        headers={'Origin':'http://127.0.0.1:8765', **(headers or {})})

    def test_signup_login_logout_and_secret_exclusion(self):
        status, r, headers = self.submit()
        self.assertEqual(status, 201)
        self.assertEqual(r['member']['name'], 'Synthetic Test')
        self.assertNotIn('password', str(r))
        self.assertNotIn('token', r)
        auth = {'cookie':headers['Set-Cookie'].split(';')[0], 'csrf':r['csrf']}
        self.assertEqual(self.req('/api/me', auth=auth)[0],200)
        with core.connect(self.db) as db:
            member = db.execute('SELECT * FROM members').fetchone()
            self.assertTrue(member['password_hash'].startswith('scrypt-v1$'))
            self.assertNotIn(self.data['password'], member['password_hash'])
            self.assertEqual(db.execute('SELECT phone FROM user_accounts').fetchone()['phone'],self.data['phone'])
        self.assertEqual(self.req('/api/logout', {}, auth=auth)[0],200)
        self.assertEqual(self.req('/api/me', auth=auth)[0],401)
        self.assertEqual(self.submit('login',{**self.data,'email':' SYNTHETIC@EXAMPLE.COM '})[0],200)
        self.assertEqual(self.submit('login',{**self.data,'password':'incorrect'})[0],401)

    def test_guest_upgrade_rotates_without_copying_guest_data(self):
        g=core.guest_login(self.db)
        auth={'cookie':'selfpay_session='+g['token'],'csrf':g['csrf']}
        status,r,h=self.submit(auth=auth)
        self.assertEqual(status,201)
        self.assertNotEqual(g['member']['id'],r['member']['id'])
        self.assertIsNone(core.session(g['token'],self.db))
        self.assertNotEqual(g['csrf'],r['csrf'])
        with core.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM conversations').fetchone()['n'],0)

    def test_duplicates_casefold_and_concurrency(self):
        def register(_):
            try: accounts.authenticate(self.db,self.data,'register','test-ip');return True
            except accounts.AccountError:return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(register,range(2))),1)
        self.assertEqual(self.submit(data={**self.data,'email':'SYNTHETIC@example.com'})[0],409)
        with core.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM user_accounts').fetchone()['n'],1)

    def test_validation_and_unknown_account(self):
        for field,value in [('name',''),('email','invalid'),('phone','not a number'),('password','short')]:
            with self.subTest(field=field):
                self.assertEqual(self.submit(data={**self.data,field:value})[0],400)
        self.assertEqual(self.submit('login')[0],401)

    def test_origin_and_csrf(self):
        self.assertEqual(self.req('/api/register',self.data)[0],403)
        self.assertEqual(self.submit(headers={'Origin':'https://evil.example'})[0],403)
        guest=core.guest_login(self.db)
        self.assertEqual(self.submit(auth={'cookie':'selfpay_session='+guest['token'],'csrf':'wrong'})[0],403)
        self.assertEqual(self.req('/api/register',method='GET')[0],405)

    def test_legacy_member_not_enabled_and_expiry(self):
        with core.connect(self.db) as db:
            db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)',('old','plan-a',self.data['email'],'Old test','00'*16,'unused'))
        self.assertEqual(self.submit('login')[0],401)
        self.assertEqual(self.submit()[0],409)
        self.data['email']='second@example.com'
        _,r,h=self.submit()
        with core.connect(self.db) as db:db.execute('UPDATE sessions SET expires=0')
        self.assertIsNone(core.session(h['Set-Cookie'].split(';')[0].split('=')[1],self.db))

    def test_rate_limit_persists_across_handler_instances(self):
        for _ in range(10):self.assertEqual(self.submit('login')[0],401)
        self.http.login_attempts=[]
        self.assertEqual(self.submit('login')[0],429)
        with core.connect(self.db) as db:
            keys=[row['key'] for row in db.execute('SELECT key FROM login_limits')]
        self.assertTrue(all(len(key)==64 for key in keys))

    def test_migration_idempotent_preserves_data(self):
        self.submit()
        accounts.initialize(self.db)
        accounts.initialize(self.db)
        self.assertEqual(self.submit('login')[0],200)

class AWSChecks(unittest.TestCase):
    def test_secure_origin_cookie_and_preview(self):
        from aws_server import AWSHandler
        h=object.__new__(AWSHandler)
        h.server=SimpleNamespace(app_origin='https://selfpay.example.com')
        h.command='POST';h.headers={'Host':'selfpay.example.com','Origin':'https://selfpay.example.com'}
        self.assertTrue(h.validate_origin())
        h.headers['Origin']='https://evil.example.com';self.assertFalse(h.validate_origin())
        h.headers.pop('Origin');self.assertFalse(h.validate_origin())
        h.command='GET';self.assertTrue(h.validate_origin())
        self.assertIn('__Host-selfpay_session=',h.session_cookie('test'))
        self.assertIn('; Secure',h.session_cookie('test'))
        self.assertFalse(h.booking_preview)

    def test_local_postgres_tls_exception_only_loopback(self):
        import psycopg
        from postgres_store import PostgresConnection
        with patch.object(psycopg,'connect') as connect:
            PostgresConnection('postgresql://localhost/selfpay?sslmode=disable')
            self.assertEqual(connect.call_args.kwargs['sslmode'],'disable')
            with self.assertRaises(ValueError):PostgresConnection('postgresql://remote.example/selfpay?sslmode=disable')
            PostgresConnection('postgresql://localhost/selfpay')
            self.assertEqual(connect.call_args.kwargs['sslmode'],'require')

# TEST_DATABASE_URL must point only to the disposable CI/local test database.
import os
@unittest.skipUnless(os.environ.get('TEST_DATABASE_URL'), 'Disposable PostgreSQL database required')
class PostgresAccountChecks(unittest.TestCase):
    def test_migration_registration_login_and_duplicate(self):
        import uuid
        from urllib.parse import urlencode
        from psycopg import sql
        import psycopg
        base=os.environ['TEST_DATABASE_URL']
        schema='account_test_'+uuid.uuid4().hex
        with psycopg.connect(base) as admin:
            admin.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
        path=base+('&' if '?' in base else '?')+urlencode({'options':'-csearch_path='+schema})
        try:
            core.initialize(path)
            accounts.initialize(path)
            accounts.initialize(path)
            data={'name':'Synthetic Test','email':'synthetic@example.com','password':'Synthetic-passphrase!','phone':''}
            g=core.guest_login(path)
            r=accounts.authenticate(path,data,'register','synthetic-ip',g['token'])
            self.assertEqual(core.session(r['token'],path)['name'],'Synthetic Test')
            self.assertIsNone(core.session(g['token'],path))
            self.assertEqual(accounts.authenticate(path,data,'login','synthetic-ip')['member']['id'],r['member']['id'])
            with self.assertRaises(accounts.AccountError):accounts.authenticate(path,data,'register','synthetic-ip')
            with core.connect(path) as db:
                self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM user_accounts').fetchone()['n'],1)
                self.assertEqual(db.execute('SELECT COUNT(*) AS n FROM members').fetchone()['n'],2)
        finally:
            with psycopg.connect(base) as admin:
                admin.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
