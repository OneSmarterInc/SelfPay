"""Vercel entry point. No local database fallback and no public setup endpoint."""
import os
import hashlib
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import core
from server import Handler

class handler(Handler):
    def database_path(self):
        url=os.environ.get('DATABASE_URL','')
        if not url.startswith(('postgres://','postgresql://')):
            raise RuntimeError('Hosted database not configured')
        return url
    def validate_origin(self):
        host=self.request_header('X-Forwarded-Host') or self.request_header('Host','')
        allowed=set(filter(None,[os.environ.get('VERCEL_URL'),os.environ.get('VERCEL_PROJECT_PRODUCTION_URL'),os.environ.get('VERCEL_BRANCH_URL')]))
        allowed.update(x.strip() for x in os.environ.get('APP_HOSTS','').split(',') if x.strip())
        origin=self.request_header('Origin')
        return host in allowed and (not origin or origin=='https://'+host)
    def respond(self,status,data,cookie=None,content_type='application/json'):
        if cookie:cookie+='; Secure'
        if content_type!='application/json':
            text=data.decode('utf-8')
            text=text.replace('value="DemoOnly-2026!"','value=""')
            text=text.replace('Demo password: DemoOnly-2026!','Use the review password provided by your host.')
            text=text.replace('Local use only.','Review use only.').replace('local POC','review POC')
            text=text.replace('MySelfPay POC v4.1','MySelfPay Review v5')
            data=text.encode('utf-8')
        return super().respond(status,data,cookie,content_type)
    def login_allowed(self,email):
        # Database-backed counter works across serverless instances. Store no raw email/IP.
        key=hashlib.sha256(email.casefold().encode()).hexdigest()
        minute=int(time.time()//60)
        with core.connect(self.database_path()) as db:
            db.execute('DELETE FROM login_limits WHERE window_id<?',(minute-2,))
            row=db.execute('INSERT INTO login_limits VALUES(?,?,1) ON CONFLICT(key,window_id) DO UPDATE SET attempts=login_limits.attempts+1 RETURNING attempts',(key,minute)).fetchone()
        return row['attempts']<=20
