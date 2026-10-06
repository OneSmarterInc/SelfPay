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

# Per-minute limits. Keying by email+IP (not email alone) stops one attacker locking out a member;
# the IP and email ceilings still cap credential stuffing and distributed guessing.
LIMITS={'login_pair':10,'login_ip':60,'login_email':100,'register_ip':5,'register_global':100,'password':20,'guest_ip':20}

class Handler(BaseHTTPRequestHandler):
    server_version='MySelfPayPOC'
    cookie_name='selfpay_session'
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
        for name,value in self.extra_headers():self.send_header(name,value)
        if cookie:self.send_header('Set-Cookie',cookie)
        self.end_headers();self.wfile.write(body)
    def extra_headers(self):return []
    def session_cookie(self,token='',max_age=28800):
        return f'{self.cookie_name}={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age={max_age if token else 0}'
    def client_ip(self):return self.client_address[0] if getattr(self,'client_address',None) else 'unknown'
    def request_header(self,name,default=None):
        # Runtime adapters may supply a plain dict instead of HTTPMessage.
        return next((value for key,value in self.headers.items()
                     if key.casefold()==name.casefold()),default)
    def token(self):
        jar=SimpleCookie()
        try:jar.load(self.request_header('Cookie',''));return jar[self.cookie_name].value if self.cookie_name in jar else ''
        except Exception:return ''
    def payload(self):
        if not self.request_header('Content-Type','').startswith('application/json'):raise ValueError('JSON required')
        size=int(self.request_header('Content-Length','0'))
        if not 0<size<=100000:raise ValueError('Request size must be 1–100000 bytes')
        value=json.loads(self.rfile.read(size))
        if not isinstance(value,dict):raise ValueError('JSON object required')
        return value
    def validate_origin(self):
        host=self.request_header('Host','')
        allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
        if host not in allowed:return False
        origin=self.request_header('Origin')
        return not origin or origin==f'http://{host}'
    def database_path(self):return self.server.db_path
    def login_allowed(self,key,limit=20):
        now=time.monotonic()
        self.server.login_attempts=[(k,t) for k,t in self.server.login_attempts if now-t<60]
        if sum(1 for k,_ in self.server.login_attempts if k==key)>=limit:return False
        self.server.login_attempts.append((key,now))
        return True
    def all_allowed(self,*checks):
        # Every counter is incremented so a blocked caller cannot reset one limit by tripping another.
        return all([self.login_allowed(key,LIMITS[kind]) for kind,key in checks])
    def route_selfpay_request(self,method):
        if not self.validate_origin():return self.respond(403,{'error':'Origin or host rejected'})
        path=urlparse(self.path).path;db=self.database_path()
        if method=='GET' and path in ('/','/app.js'):
            name={'/':'index.html','/app.js':'app.js'}[path]
            return self.respond(200,(core.ROOT/'static'/name).read_bytes(),content_type='text/html' if path=='/' else 'text/javascript')
        if path in ('/api/register','/api/login','/api/password'):
            return self.respond(410,{'error':'Use Sign in as guest. Email and password sign-in is disabled.'})
        if path=='/api/guest' and method=='POST':
            if not self.all_allowed(('guest_ip','guest-ip:'+self.client_ip())):return self.respond(429,{'error':'Too many requests. Wait one minute.'})
            self.payload()
            existing=core.session(self.token(),db)
            if existing and existing['tenant']=='guest':
                return self.respond(200,{'member':{k:v for k,v in existing.items() if k!='csrf'},'csrf':existing['csrf']})
            result=core.guest_login(db);token=result.pop('token')
            return self.respond(200,result,cookie=self.session_cookie(token))
        member=core.session(self.token(),db)
        if not member:return self.respond(401,{'error':'Sign in to your account'})
        if method!='GET' and not secrets.compare_digest(self.request_header('X-CSRF-Token',''),member['csrf']):
            return self.respond(403,{'error':'CSRF token required'})
        if path=='/api/me' and method=='GET':return self.respond(200,{'member':{k:v for k,v in member.items() if k!='csrf'},'csrf':member['csrf']})
        if path=='/api/logout' and method=='POST':
            with core.connect(db) as con:con.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(self.token().encode()).hexdigest(),))
            return self.respond(200,{'ok':True},cookie=self.session_cookie())
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
        try:self.route_selfpay_request(method)
        except PermissionError:self.respond(404,{'error':'Record unavailable'})
        except ValueError as exc:
            # Validation messages are written for members. Parser and type errors are not, so they stay generic.
            message=str(exc) if type(exc) is ValueError else 'Invalid request'
            self.respond(400,{'error':message})
        except (TypeError,KeyError,AttributeError):self.respond(400,{'error':'Invalid request'})
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
