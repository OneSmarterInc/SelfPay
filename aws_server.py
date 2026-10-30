"""EC2 loopback application behind an HTTPS reverse proxy; never seeds/migrates."""
import argparse
import hashlib
import os
import time
from urllib.parse import urlparse
import server  # Loads .env before core.
import core

class AWSHandler(server.Handler):
    booking_preview = False
    cookie_name = '__Host-selfpay_session'

    def session_cookie(self, token='', max_age=28800):
        return super().session_cookie(token, max_age) + '; Secure'

    def extra_headers(self):
        return [('Strict-Transport-Security', 'max-age=31536000')]

    def validate_origin(self):
        origin = self.server.app_origin
        host = urlparse(origin).netloc
        # Nginx must preserve Host and terminate HTTPS; forwarded Host is never trusted.
        return (self.request_header('Host') == host
                and self.request_header('Origin') in (None, origin)
                and (self.command == 'GET' or self.request_header('Origin') == origin))

    def client_ip(self):
        # Only a loopback proxy may supply X-Real-IP, and its config must overwrite it.
        if self.client_address[0] in ('127.0.0.1', '::1'):
            return self.request_header('X-Real-IP', self.client_address[0])[:64]
        return self.client_address[0]

    def login_allowed(self, key, limit=20):
        key = hashlib.sha256(key.casefold().encode()).hexdigest()
        with core.connect(self.database_path()) as db:
            row = db.execute('INSERT INTO login_limits VALUES(?,?,1) ON CONFLICT(key,window_id) DO UPDATE SET attempts=login_limits.attempts+1 RETURNING attempts', (key, int(time.time()//60))).fetchone()
        return row['attempts'] <= limit

def make_server(port=8765):
    origin = os.environ.get('APP_ORIGIN', '').rstrip('/')
    parsed = urlparse(origin)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise SystemExit('Set APP_ORIGIN to the public HTTPS origin, without a path.')
    database = os.environ.get('DATABASE_URL', '')
    if not database.startswith(('postgresql://', 'postgres://')):
        raise SystemExit('Set DATABASE_URL to the existing PostgreSQL database.')
    # Fail startup before serving traffic if the additive account migration is missing.
    with core.connect(database) as db:
        db.execute('SELECT member_id,email,phone,created FROM user_accounts LIMIT 0')
        db.execute('SELECT id,tenant,email,name,salt,password_hash FROM members LIMIT 0')
        db.execute('SELECT token_hash,member_id,csrf,expires FROM sessions LIMIT 0')
    http = server.LocalServer(('127.0.0.1', port), AWSHandler)
    http.app_origin = origin
    http.db_path = database
    http.login_attempts = []
    return http

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    try: http = make_server(args.port)
    except SystemExit: raise
    except Exception: raise SystemExit('Startup database check failed. Check configuration and account migration; credentials are not logged.') from None
    print('MySelfPay listening on loopback behind HTTPS.', flush=True)
    try: http.serve_forever()
    except KeyboardInterrupt: pass
    finally: http.server_close()
