"""Loopback-only MySelfPay functional POC. Run: python server.py"""
import argparse
import hashlib
import json
import secrets
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import core

class Handler(BaseHTTPRequestHandler):
    server_version='MySelfPayPOC'
    def log_message(self,*args): pass  # No searches, transcripts or member details in access logs.
    def respond(self,status,data,cookie=None,content_type='application/json'):
        body=json.dumps(data).encode() if content_type=='application/json' else data
        self.send_response(status)
        self.send_header('Content-Type',content_type+'; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(body)
    def token(self):
        jar=SimpleCookie()
        try:jar.load(self.headers.get('Cookie',''));return jar['selfpay_session'].value if 'selfpay_session' in jar else ''
        except Exception:return ''
    def payload(self):
        if not self.headers.get('Content-Type','').startswith('application/json'):raise ValueError('JSON required')
        size=int(self.headers.get('Content-Length','0'))
        if not 0<size<=100000:raise ValueError('Request size must be 1–100000 bytes')
        value=json.loads(self.rfile.read(size))
        if not isinstance(value,dict):raise ValueError('JSON object required')
        return value
    def validate_origin(self):
        host=self.headers.get('Host','')
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if host not in allowed:return False
        origin=self.headers.get('Origin')
        return not origin or origin==f'http://{host}'
    def database_path(self):return self.server.db_path
    def login_allowed(self,email):
        now=time.monotonic()
        self.server.login_attempts=[x for x in self.server.login_attempts if now-x<60]
        if len(self.server.login_attempts)>=20:return False
        self.server.login_attempts.append(now)
        return True
    def handle_request(self,method):
        if not self.validate_origin():return self.respond(403,{'error':'Origin or host rejected'})
        path=urlparse(self.path).path;db=self.database_path()
        if method=='GET' and path in ('/','/app.js','/functional.js'):
            name={'/':'index.html','/app.js':'app.js','/functional.js':'functional.js'}[path]
            return self.respond(200,(core.ROOT/'static'/name).read_bytes(),content_type='text/html' if path=='/' else 'text/javascript')
        if path=='/api/login' and method=='POST':
            data=self.payload()
            email=str(data.get('email',''))[:200];password=str(data.get('password',''))[:200]
            if not self.login_allowed(email):return self.respond(429,{'error':'Too many sign-in attempts. Wait one minute.'})
            result=core.login(email,password,db)
            if not result:return self.respond(401,{'error':'Invalid credentials'})
            token=result.pop('token')
            return self.respond(200,result,cookie=f'selfpay_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=28800')
        member=core.session(self.token(),db)
        if not member:return self.respond(401,{'error':'Sign in to a synthetic account'})
        if method!='GET' and not secrets.compare_digest(self.headers.get('X-CSRF-Token',''),member['csrf']):
            return self.respond(403,{'error':'CSRF token required'})
        if path=='/api/me' and method=='GET':return self.respond(200,{'member':{k:v for k,v in member.items() if k!='csrf'},'csrf':member['csrf']})
        if path=='/api/logout' and method=='POST':
            with core.connect(db) as con:con.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(self.token().encode()).hexdigest(),))
            return self.respond(200,{'ok':True},cookie='selfpay_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0')
        if path=='/api/catalog' and method=='GET':return self.respond(200,core.catalog(db))
        if path=='/api/search' and method=='POST':return self.respond(200,core.search(self.payload(),db))
        if path=='/api/agent' and method=='POST':
            data=self.payload();return self.respond(200,core.agent(data.get('message'),data.get('search',{}),db))
        if path=='/api/conversations':
            if method=='GET':return self.respond(200,{'conversations':core.history(member,db)})
            if method=='POST':return self.respond(200,core.save_conversation(member,self.payload(),db))
        if path.startswith('/api/conversations/') and method=='DELETE':
            core.delete_conversation(member,path.rsplit('/',1)[1],db);return self.respond(200,{'ok':True})
        if path=='/api/preferences':
            if method=='GET':return self.respond(200,core.preference(member,path=db))
            if method=='POST':
                data=self.payload()
                if data.get('private'):raise ValueError('Private preferences cannot be saved')
                return self.respond(200,core.preference(member,data,path=db))
            if method=='DELETE':return self.respond(200,core.preference(member,delete=True,path=db))
        if path=='/api/corrections' and method=='POST':
            data=self.payload()
            if data.get('private'):raise ValueError('Exit private mode before saving a correction report')
            cat=core.catalog(db);offer=next((o for o in cat['offers'] if o['id']==data.get('offer_id')),None)
            if not offer:raise ValueError('Offer unavailable')
            description=str(data.get('description','')).strip()
            if not 1<=len(description)<=1000:raise ValueError('Describe the issue in 1–1000 characters')
            ident=secrets.token_hex(12)
            with core.connect(db) as con:con.execute('INSERT INTO corrections VALUES(?,?,?,?,?,?,?,?,?)',(ident,member['tenant'],member['id'],offer['id'],cat['version'],str(data.get('category','Other'))[:80],description,time.time(),'pending review'))
            return self.respond(201,{'id':ident,'status':'pending review'})
        return self.respond(404,{'error':'Not found'})
    def dispatch(self,method):
        try:self.handle_request(method)
        except PermissionError:self.respond(404,{'error':'Record unavailable'})
        except (ValueError,TypeError,KeyError,AttributeError) as exc:self.respond(400,{'error':str(exc)})
        except Exception:self.respond(500,{'error':'Request failed. Your input has not been discarded; retry or restart the local app.'})
    def do_GET(self):self.dispatch('GET')
    def do_POST(self):self.dispatch('POST')
    def do_DELETE(self):self.dispatch('DELETE')

def make_server(port=8765,path=core.DB):
    core.initialize(path)
    with core.connect(path) as db:active=core.active_batch(db)
    if not active:
        batch=core.stage_import(core.ROOT/'seed/directory.json',core.ROOT/'seed/mappings.json',path)
        core.publish(batch['id'],path)
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.db_path=path;server.login_attempts=[]
    return server

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args();server=make_server(args.port)
    print(f'MySelfPay local POC: http://127.0.0.1:{server.server_port}',flush=True)
    print('Synthetic accounts only. Press Ctrl+C to stop.',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
