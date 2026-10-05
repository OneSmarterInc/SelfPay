import io
import os
import unittest
from unittest.mock import patch
from api.index import handler
from postgres_store import PostgresConnection

class HostedTests(unittest.TestCase):
    def instance(self):
        h=object.__new__(handler);h.headers={};h.wfile=io.BytesIO()
        h.send_response=lambda status:None;h.end_headers=lambda:None
        h.sent={};h.send_header=lambda k,v:h.sent.update({k:v})
        return h
    def test_runtime_handle_request_does_not_shadow_app_router(self):
        # Vercel wraps the handler with its own zero-argument handle_request.
        class RuntimeHandler(handler):
            def handle_request(self):
                raise AssertionError('Application must not call runtime handle_request')
        h=object.__new__(RuntimeHandler)
        from unittest.mock import Mock
        h.route_selfpay_request=Mock()
        h.do_GET();h.do_POST();h.do_DELETE()
        self.assertEqual([c.args for c in h.route_selfpay_request.call_args_list],
                         [('GET',),('POST',),('DELETE',)])
    def test_host_and_https_origin(self):
        h=self.instance()
        with patch.dict(os.environ,{'VERCEL_URL':'review.vercel.app','APP_HOSTS':'','VERCEL_PROJECT_PRODUCTION_URL':''}):
            h.headers={'Host':'review.vercel.app','Origin':'https://review.vercel.app'}
            self.assertTrue(h.validate_origin())
            h.headers['Origin']='https://attacker.example';self.assertFalse(h.validate_origin())
            h.headers={'Host':'attacker.example'};self.assertFalse(h.validate_origin())
    def test_database_fails_closed(self):
        with patch.dict(os.environ,{'DATABASE_URL':''}):
            with self.assertRaises(RuntimeError):self.instance().database_path()
    def test_cookie_is_secure(self):
        h=self.instance();h.respond(200,{},cookie='selfpay_session=test; HttpOnly; SameSite=Strict; Path=/')
        self.assertIn('; Secure',h.sent['Set-Cookie'])
    def test_review_password_not_in_page(self):
        h=self.instance();h.respond(200,b'value="DemoOnly-2026!" Demo password: DemoOnly-2026!',content_type='text/javascript')
        self.assertNotIn(b'DemoOnly-2026!',h.wfile.getvalue())
    def test_postgres_parameters_remain_separate(self):
        class Connection:
            def execute(self,sql,args):self.received=(sql,args);return 'cursor'
        p=object.__new__(PostgresConnection);p.connection=Connection()
        value="x' OR 1=1--"
        p.execute('SELECT * FROM members WHERE email=?',(value,))
        self.assertEqual(p.connection.received,('SELECT * FROM members WHERE email=%s',(value,)))
    def test_postgres_transaction_closes(self):
        class Connection:
            calls=[]
            def commit(self):self.calls.append('commit')
            def rollback(self):self.calls.append('rollback')
            def close(self):self.calls.append('close')
        p=object.__new__(PostgresConnection);p.connection=Connection()
        p.__exit__(ValueError,None,None)
        self.assertEqual(p.connection.calls,['rollback','close'])
if __name__=='__main__':unittest.main()
