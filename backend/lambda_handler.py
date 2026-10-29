"""API Gateway HTTP API payload v2 adapter; API only, no startup migrations."""
import base64
import hashlib
import io
import json
import os
import time
from urllib.parse import urlsplit
import core
import server


class AWSHandler(server.Handler):
    cookie_name = '__Host-selfpay_session'

    def database_path(self):
        value = os.environ.get('DATABASE_URL', '')
        if not value.startswith(('postgres://', 'postgresql://')):
            raise server.ServiceUnavailableError('Database is not configured.')
        return value

    def validate_origin(self):
        configured = os.environ.get('APP_ORIGIN', '').rstrip('/')
        parsed = urlsplit(configured)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
                or parsed.password or parsed.path or parsed.query or parsed.fragment):
            return False
        origin = self.request_header('Origin')
        # Browser writes must originate at the configured frontend. Existing CSRF
        # token checks still run for authenticated writes.
        return origin == configured or (not origin and self.command == 'GET')

    def client_ip(self):
        # Trust only API Gateway context, never arbitrary X-Forwarded-For headers.
        return self.event['requestContext']['http'].get('sourceIp', 'unknown')

    def session_cookie(self, token='', max_age=28800):
        return super().session_cookie(token, max_age) + '; Secure'

    def extra_headers(self):
        return [('Strict-Transport-Security', 'max-age=31536000')]

    def login_allowed(self, key, limit=20):
        key = hashlib.sha256(key.casefold().encode()).hexdigest()
        minute = int(time.time() // 60)
        with core.connect(self.database_path()) as db:
            row = db.execute('INSERT INTO login_limits VALUES(?,?,1) ON CONFLICT(key,window_id) DO UPDATE SET attempts=login_limits.attempts+1 RETURNING attempts', (key, minute)).fetchone()
        return row['attempts'] <= limit

    def send_response(self, status, message=None):
        self.status = status

    def send_header(self, name, value):
        if name.lower() == 'set-cookie':
            self.response_cookies.append(value)
        else:
            self.response_headers[name.lower()] = str(value)

    def end_headers(self):
        pass


def error(status, message):
    return {'statusCode': status, 'headers': {'content-type': 'application/json', 'cache-control': 'no-store'}, 'body': json.dumps({'error': message})}


def lambda_handler(event, context):
    if event.get('version') != '2.0':
        return error(400, 'API Gateway payload version 2.0 required.')
    http = event.get('requestContext', {}).get('http', {})
    method, path = http.get('method'), event.get('rawPath', '')
    if not path.startswith('/api/'):
        return error(404, 'Not found')
    if method not in ('GET', 'POST', 'DELETE'):
        return error(405, 'Method not allowed')
    try:
        body = event.get('body') or ''
        # Reject before base64 decoding to avoid an oversized allocation.
        if len(body) > 140000:
            return error(413, 'Request too large')
        body = base64.b64decode(body, validate=True) if event.get('isBase64Encoded') else body.encode('utf-8')
        if len(body) > 100000:
            return error(413, 'Request too large')
    except (ValueError, TypeError, AttributeError):
        return error(400, 'Invalid request body')
    handler = object.__new__(AWSHandler)
    handler.event = event
    handler.command, handler.path = method, path
    handler.headers = {k.lower(): v for k, v in (event.get('headers') or {}).items()}
    handler.headers['content-length'] = str(len(body))
    if event.get('cookies'):
        handler.headers['cookie'] = '; '.join(event['cookies'])
    handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
    handler.response_headers, handler.response_cookies = {}, []
    handler.status = 500
    handler.dispatch(method)
    result = {'statusCode': handler.status, 'headers': handler.response_headers,
              'body': handler.wfile.getvalue().decode('utf-8'), 'isBase64Encoded': False}
    if handler.response_cookies:
        result['cookies'] = handler.response_cookies
    return result
