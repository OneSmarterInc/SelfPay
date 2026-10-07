"""Vercel entry point. No local database fallback and no public setup endpoint."""
import os
import hashlib
import json
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
import server
from postgres_store import uses_pooler

class handler(server.Handler):
    # __Host- cookies must be Secure, Path=/ and host-only, so a sibling subdomain cannot set or shadow them.
    cookie_name='__Host-selfpay_session'
    def extra_headers(self):
        return [('Strict-Transport-Security','max-age=63072000; includeSubDomains')]
    def client_ip(self):
        # Vercel overwrites these headers at its edge, so client-supplied values are not trusted through.
        real=self.request_header('X-Real-IP')
        if real:return real.strip()[:64]
        forwarded=self.request_header('X-Forwarded-For','')
        return forwarded.split(',')[0].strip()[:64] or 'unknown'
    def database_path(self):
        url=os.environ.get('DATABASE_URL','')
        if not url.startswith(('postgres://','postgresql://')):
            raise RuntimeError('Hosted database not configured')
        if not uses_pooler(url):
            print('SELFPAY_DB_WARNING DATABASE_URL is a direct Neon endpoint; use the pooled (-pooler) URL.',flush=True)
        return url
    def validate_origin(self):
        host=self.request_header('X-Forwarded-Host') or self.request_header('Host','')
        allowed=set(filter(None,[os.environ.get('VERCEL_URL'),os.environ.get('VERCEL_PROJECT_PRODUCTION_URL'),os.environ.get('VERCEL_BRANCH_URL')]))
        allowed.update(x.strip() for x in os.environ.get('APP_HOSTS','').split(',') if x.strip())
        origin=self.request_header('Origin')
        valid=host in allowed and (not origin or origin=='https://'+host)
        if not valid:
            print('SELFPAY_HOST_CHECK '+json.dumps({
                'host':str(self.request_header('Host',''))[:200],
                'forwarded_host':str(self.request_header('X-Forwarded-Host',''))[:200],
                'allowed_hosts':sorted(allowed),
                'origin_present':origin is not None,
                'origin_matches_host':origin=='https://'+host,
            }),flush=True)
        return valid
    def respond(self,status,data,cookie=None,content_type='application/json',retry_after=None):
        if cookie:cookie+='; Secure'
        if content_type!='application/json':
            text=data.decode('utf-8')
            text=text.replace('value="DemoOnly-2026!"','value=""')
            text=text.replace('Demo password: DemoOnly-2026!','Use the review password provided by your host.')
            text=text.replace('Local use only.','Review use only.').replace('local POC','review POC')
            text=text.replace('MySelfPay POC v4.1','MySelfPay Review v5')
            data=text.encode('utf-8')
        return super().respond(status,data,cookie,content_type,retry_after=retry_after)
    def login_allowed(self,key,limit=20):
        # Database-backed counter works across serverless instances. Store no raw email/IP.
        key=hashlib.sha256(key.casefold().encode()).hexdigest()
        minute=int(time.time()//60)
        with core.connect(self.database_path()) as db:
            row=db.execute('INSERT INTO login_limits VALUES(?,?,1) ON CONFLICT(key,window_id) DO UPDATE SET attempts=login_limits.attempts+1 RETURNING attempts',(key,minute)).fetchone()
        return row['attempts']<=limit
