"""Synthetic tests only; no AWS or production database calls."""
import base64
import json
import os
import unittest
from unittest.mock import patch
from backend import lambda_handler as aws


def event(method='GET', path='/api/me', origin='https://test.example', body=''):
    return {'version': '2.0', 'rawPath': path,
            'requestContext': {'http': {'method': method, 'sourceIp': '192.0.2.10'}},
            'headers': {'origin': origin, 'content-type': 'application/json'}, 'body': body}


class AWSAdapterTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {'APP_ORIGIN': 'https://test.example', 'DATABASE_URL': 'postgresql://synthetic.invalid/test'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_unsupported_payload_and_non_api(self):
        self.assertEqual(aws.lambda_handler({}, None)['statusCode'], 400)
        self.assertEqual(aws.lambda_handler(event(path='/'), None)['statusCode'], 404)
        self.assertEqual(aws.lambda_handler(event(method='PUT'), None)['statusCode'], 405)

    def test_origin_rejected_without_database_access(self):
        with patch.object(aws.core, 'session') as lookup:
            for origin in ('https://attacker.example', ''):
                r = aws.lambda_handler(event('POST', '/api/search', origin, '{}'), None)
                self.assertEqual(r['statusCode'], 403)
            lookup.assert_not_called()

    def test_no_database_fallback(self):
        with patch.dict(os.environ, {'DATABASE_URL': ''}):
            r = aws.lambda_handler(event(), None)
            self.assertEqual(r['statusCode'], 503)
            self.assertNotIn('postgres', r['body'])

    def test_cookies_and_csrf(self):
        member = {'id': 'synthetic', 'tenant': 'guest', 'name': 'Test', 'csrf': 'synthetic-csrf'}
        request = event()
        request['cookies'] = ['__Host-selfpay_session=test-token']
        with patch.object(aws.core, 'session', return_value=member) as lookup:
            r = aws.lambda_handler(request, None)
            self.assertEqual(r['statusCode'], 200)
            self.assertEqual(lookup.call_args.args[0], 'test-token')
            self.assertEqual(json.loads(r['body'])['csrf'], 'synthetic-csrf')
            r = aws.lambda_handler(event('POST', '/api/search', body='{}'), None)
            self.assertEqual(r['statusCode'], 403)

    def test_guest_cookie_secure_and_base64(self):
        request = event('POST', '/api/guest', body=base64.b64encode(b'{}').decode())
        request['isBase64Encoded'] = True
        with patch.object(aws.AWSHandler, 'all_allowed', return_value=True), patch.object(aws.core, 'session', return_value=None), patch.object(aws.core, 'guest_login', return_value={'token':'synthetic-token','csrf':'synthetic-csrf','member':{'tenant':'guest'}}):
            r = aws.lambda_handler(request, None)
            self.assertEqual(r['statusCode'], 200)
            self.assertIn('__Host-selfpay_session=', r['cookies'][0])
            for flag in ('Secure', 'HttpOnly', 'SameSite=Strict', 'Path=/'):
                self.assertIn(flag, r['cookies'][0])
            self.assertNotIn('synthetic-token', r['body'])
            self.assertEqual(r['headers']['cache-control'], 'no-store')

    def test_request_limits_and_invalid_encoding(self):
        self.assertEqual(aws.lambda_handler(event('POST', body='x'*140001), None)['statusCode'], 413)
        request = event('POST', body='!not-base64!')
        request['isBase64Encoded'] = True
        self.assertEqual(aws.lambda_handler(request, None)['statusCode'], 400)

    def test_gateway_ip_not_forwarded_header(self):
        handler = object.__new__(aws.AWSHandler)
        handler.event = event()
        handler.headers = {'x-forwarded-for': 'attacker-supplied'}
        self.assertEqual(handler.client_ip(), '192.0.2.10')

if __name__ == '__main__':
    unittest.main()
