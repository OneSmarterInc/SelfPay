import copy
import http.client
import io
import json
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
import core
import server

class FunctionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.db=Path(cls.temp.name)/'test.sqlite3'
        core.initialize(cls.db)
        batch=core.stage_import(core.ROOT/'seed/directory.json',core.ROOT/'seed/mappings.json',cls.db)
        core.publish(batch['id'],cls.db)
        cls.port=8765
        cls.http=SimpleNamespace(server_port=cls.port,db_path=cls.db,login_attempts=[])
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def req(self,path,body=None,method=None,auth=None,headers=None):
        method=method or ('POST' if body is not None else 'GET');h={}
        if body is not None:h['Content-Type']='application/json'
        if auth:h.update({'Cookie':auth['cookie'],'X-CSRF-Token':auth['csrf']})
        h['Host']=f'127.0.0.1:{self.port}';h.update(headers or {})
        payload=json.dumps(body).encode() if body is not None else b''
        if payload:h['Content-Length']=str(len(payload))
        raw=(f'{method} {path} HTTP/1.0\r\n'+''.join(f'{k}: {v}\r\n' for k,v in h.items())+'\r\n').encode()+payload
        # Exercise the actual HTTP handler and parser without network sockets.
        class Wire:
            def __init__(self,data):self.input=io.BytesIO(data);self.output=io.BytesIO()
            def makefile(self,*args):return self.input
            def sendall(self,data):self.output.write(data)
        wire=Wire(raw);server.Handler(wire,('127.0.0.1',1),self.http)
        response_wire=Wire(wire.output.getvalue());res=http.client.HTTPResponse(response_wire);res.begin()
        raw=res.read();status=res.status;rh=dict(res.getheaders())
        return status,json.loads(raw) if 'application/json' in rh.get('Content-Type','') else raw,rh
    def sign_in(self,email='alex.a@example.test'):
        # Rate limits are verified separately; tests reset the local counter.
        self.http.login_attempts=[]
        status,data,h=self.req('/api/login',{'email':email,'password':core.DEMO_PASSWORD})
        self.assertEqual(status,200);return {'cookie':h['Set-Cookie'].split(';')[0],'csrf':data['csrf'],'member':data['member']}
    def payload(self):return {'messages':[{'role':'user','text':'Synthetic knee MRI search'}],'search':{'mod':'MRI','body':'Knee','contrast':'without','location':'Cincinnati','budget':500}}
    def test_01_auth_required(self):self.assertEqual(self.req('/api/catalog')[0],401)
    def test_02_password_failure(self):self.assertEqual(self.req('/api/login',{'email':'alex.a@example.test','password':'wrong'})[0],401)
    def test_03_session_cookie_security(self):
        self.http.login_attempts=[]
        status,r,h=self.req('/api/login',{'email':'alex.a@example.test','password':core.DEMO_PASSWORD})
        self.assertIn('HttpOnly',h['Set-Cookie']);self.assertIn('SameSite=Strict',h['Set-Cookie'])
    def test_04_catalog_and_shared_search(self):
        a=self.sign_in();_,data,_=self.req('/api/catalog',auth=a)
        self.assertEqual(len(data['entries']),44);self.assertEqual(len(data['offers']),13)
        s=self.payload()['search'];_,classic,_=self.req('/api/search',s,auth=a)
        _,chat,_=self.req('/api/agent',{'message':'Find knee MRI without contrast near Cincinnati under $500','search':s},auth=a)
        self.assertEqual([o['id'] for o in classic['offers']],[o['id'] for o in chat['offers']])
        self.assertEqual(classic['count'],2)
    def test_05_contrast_variants(self):
        a=self.sign_in();s=self.payload()['search'];s['contrast']='both'
        self.assertEqual(self.req('/api/search',s,auth=a)[1]['count'],0)
    def test_06_no_match_no_silent_relaxation(self):
        a=self.sign_in();s=self.payload()['search'];s['location']='Not Researched'
        r=self.req('/api/search',s,auth=a)[1];self.assertEqual(r['count'],0);self.assertEqual(r['search']['location'],'Not Researched')
    def test_07_budget_does_not_guarantee_starting(self):
        s={**self.payload()['search'],'location':'National','budget':500}
        r=core.search(s,self.db);start=next(o for o in r['offers'] if o['id']=='ga-start')
        self.assertEqual(start['budget_status'],'Budget fit unconfirmed')
        self.assertEqual(next(o for o in r['offers'] if o['id']=='ipmc-conflict')['amount'],None)
    def test_08_branch_inclusions(self):
        offers={o['id']:o for o in core.catalog(self.db)['offers']}
        self.assertEqual([offers[x]['amount'] for x in ['boise','spanish','auburn']],[550,600,750])
        self.assertIn('not itemized',offers['boise']['included']);self.assertIn('IV contrast',offers['spanish']['included'])
    def test_09_clinical_boundary(self):
        r=core.agent('What scan do I need for my symptoms?',self.payload()['search'],self.db)
        self.assertIn('cannot diagnose',r['reply'])
    def test_10_history_persists_between_sessions(self):
        a=self.sign_in();status,created,_=self.req('/api/conversations',self.payload(),auth=a);self.assertEqual(status,200)
        b=self.sign_in();_,r,_=self.req('/api/conversations',auth=b)
        self.assertIn(created['id'],[c['id'] for c in r['conversations']])
    def test_11_same_tenant_member_isolation(self):
        self.check_isolation('sam.a@example.test')
    def test_12_cross_tenant_isolation(self):
        self.check_isolation('alex.b@example.test')
    def check_isolation(self,email):
        a=self.sign_in();_,r,_=self.req('/api/conversations',self.payload(),auth=a);ident=r['id'];b=self.sign_in(email)
        self.assertNotIn(ident,[c['id'] for c in self.req('/api/conversations',auth=b)[1]['conversations']])
        self.assertEqual(self.req('/api/conversations',{**self.payload(),'id':ident},auth=b)[0],404)
        self.assertEqual(self.req('/api/conversations/'+ident,method='DELETE',auth=b)[0],404)
    def test_13_delete(self):
        a=self.sign_in();_,r,_=self.req('/api/conversations',self.payload(),auth=a)
        self.assertEqual(self.req('/api/conversations/'+r['id'],method='DELETE',auth=a)[0],200)
        with core.connect(self.db) as db:self.assertIsNone(db.execute('SELECT 1 FROM conversations WHERE id=?',(r['id'],)).fetchone())
    def test_14_private_does_not_persist(self):
        a=self.sign_in();before=len(self.req('/api/conversations',auth=a)[1]['conversations'])
        self.req('/api/agent',{'message':'MRI without contrast','search':self.payload()['search'],'private':True},auth=a)
        self.assertEqual(self.req('/api/conversations',{**self.payload(),'private':True},auth=a)[0],400)
        self.assertEqual(len(self.req('/api/conversations',auth=a)[1]['conversations']),before)
    def test_15_csrf_and_origin(self):
        a=self.sign_in();self.assertEqual(self.req('/api/search',{},auth=a,headers={'X-CSRF-Token':''})[0],403)
        self.assertEqual(self.req('/api/search',{},auth=a,headers={'Origin':'https://evil.example'})[0],403)
    def test_16_preferences_separate(self):
        a=self.sign_in();b=self.sign_in('jordan.b@example.test');self.req('/api/preferences',{'location':'Cincinnati'},auth=a)
        self.assertEqual(self.req('/api/preferences',auth=b)[1],{})
        self.req('/api/preferences',method='DELETE',auth=a);self.assertEqual(self.req('/api/preferences',auth=a)[1],{})
    def test_17_import_idempotence_and_review(self):
        original=core.catalog(self.db);r=core.stage_import(core.ROOT/'seed/directory.json',core.ROOT/'seed/mappings.json',self.db)
        self.assertTrue(r['unchanged']);self.assertEqual(original['version'],r['id'])
        rows=json.loads((core.ROOT/'seed/directory.json').read_text());next(x for x in rows if x['name']=='Affordable Imaging Services')['mri']='New published price; human review required'
        source=Path(self.temp.name)/'changed.json';source.write_text(json.dumps(rows))
        changed=core.stage_import(source,core.ROOT/'seed/mappings.json',self.db)
        self.assertEqual(changed['changed'],1);self.assertEqual(len(changed['withheld_offers']),3)
        self.assertEqual(core.catalog(self.db)['version'],original['version'])
        core.publish(changed['id'],self.db);self.assertEqual(len(core.catalog(self.db)['offers']),10)
        core.publish(original['version'],self.db);self.assertEqual(len(core.catalog(self.db)['offers']),13)
    def test_18_invalid_import_atomic(self):
        source=Path(self.temp.name)/'invalid.json';source.write_text(json.dumps([{'name':'Bad source','source':'javascript:alert(1)','checked':'bad'}]))
        before=core.catalog(self.db)['version']
        with self.assertRaises(ValueError):core.stage_import(source,core.ROOT/'seed/mappings.json',self.db)
        self.assertEqual(core.catalog(self.db)['version'],before)
    def test_19_correction_is_pending_not_publication(self):
        a=self.sign_in();before=core.catalog(self.db)
        status,r,_=self.req('/api/corrections',{'offer_id':'aff-mri','category':'Price','description':'Synthetic correction'},auth=a)
        self.assertEqual(status,201);self.assertEqual(r['status'],'pending review');self.assertEqual(core.catalog(self.db),before)
    def test_20_logout_invalidates(self):
        a=self.sign_in();self.req('/api/logout',{},auth=a);self.assertEqual(self.req('/api/me',auth=a)[0],401)
    def test_21_static_does_not_expose_database(self):
        a=self.sign_in();self.assertEqual(self.req('/data/myselfpay.sqlite3',auth=a)[0],404)
        status,body,h=self.req('/');self.assertEqual(status,200);self.assertIn(b'/functional.js',body);self.assertIn("connect-src 'self'",h['Content-Security-Policy'])
    def test_22_expiration(self):
        a=self.sign_in();_,r,_=self.req('/api/conversations',self.payload(),auth=a)
        with core.connect(self.db) as db:db.execute('UPDATE conversations SET expires=0 WHERE id=?',(r['id'],))
        self.assertNotIn(r['id'],[c['id'] for c in self.req('/api/conversations',auth=a)[1]['conversations']])
    def test_24_empty_search_and_missing_agent_fields(self):
        self.assertEqual(core.search({},self.db)['offers'],[])
        self.assertEqual(core.search({'mod':'MRI','body':'Knee','location':''},self.db)['offers'],[])
        answer=core.agent('Hello',{},self.db)
        self.assertEqual(answer['offers'],[])
        self.assertIn('What imaging service',answer['reply'])
        answer=core.agent('MRI',{},self.db)
        self.assertIn('body part',answer['reply'])
        self.assertEqual(answer['offers'],[])
        answer=core.agent('What scan do I need?',{},self.db)
        self.assertIn('cannot diagnose',answer['reply'])

    def test_25_zip_does_not_invent_distances(self):
        answer=core.agent('find options',{'mod':'MRI','body':'Knee','location':'45202'},self.db)
        self.assertEqual(answer['offers'],[])
        self.assertIn('ZIP matching is not connected',answer['reply'])

    def test_26_city_correction_requires_selection(self):
        query={'mod':'MRI','body':'Knee','contrast':'without','location':'Cincinati'}
        result=core.search(query,self.db)
        self.assertEqual(result['offers'],[])
        self.assertIn('Cincinnati, OH',result['location_suggestions'])
        query['location']='Cincinnati, OH'
        self.assertTrue(core.search(query,self.db)['offers'])
        answer=core.agent('Find knee MRI near Cincinati under $500',{'location':'Boise'},self.db)
        self.assertIn('Did you mean',answer['reply'])
        self.assertEqual(answer['offers'],[])

    def test_27_ambiguous_city_and_scope_explanation(self):
        query={'mod':'MRI','body':'Knee','location':'Auburn'}
        self.assertEqual(core.search(query,self.db)['location_suggestions'],['Auburn, WA'])
        answer=core.agent('Find knee MRI without contrast in Boise under $600',{},self.db)
        self.assertIn('does not confirm',answer['reply'])
        self.assertTrue(answer['offers'])

    def test_23_unknown_contrast_stays_unconfirmed(self):
        s={**self.payload()['search'],'location':'Boise','budget':600}
        r=core.search(s,self.db);self.assertEqual(r['offers'][0]['contrast'],'unknown');self.assertEqual(r['offers'][0]['budget_status'],'Budget fit unconfirmed')

    def test_28_register_login_and_organization_isolation(self):
        self.http.login_attempts=[]
        data={'name':'Reviewer','email':'New.Reviewer@Example.test','password':'Eight123','tenant':'plan-a'}
        first=self.req('/api/register',data)
        # A repeat registration looks identical and must not overwrite the existing password.
        second=self.req('/api/register',{**data,'password':'Different1'})
        self.assertEqual((first[0],first[1]),(second[0],second[1]));self.assertEqual(first[0],201)
        status,r,h=self.req('/api/login',{'email':' NEW.REVIEWER@example.test ','password':'Eight123'})
        self.assertEqual(status,200);self.assertEqual(r['member']['tenant'],'review')
        a={'cookie':h['Set-Cookie'].split(';')[0],'csrf':r['csrf'],'member':r['member']}
        status,saved,_=self.req('/api/conversations',self.payload(),auth=a)
        self.assertEqual(status,200)
        other=self.sign_in()
        self.assertNotIn(saved['id'],[c['id'] for c in self.req('/api/conversations',auth=other)[1]['conversations']])
        self.assertEqual(self.req('/api/conversations/'+saved['id'],method='DELETE',auth=other)[0],404)

    def test_29_registration_validation(self):
        self.http.login_attempts=[]
        for changes in [{'password':'1234567'},{'password':'a'*201},{'email':'invalid'},{'name':''}]:
            data={'name':'Test','email':'validation@example.test','password':'Eight123',**changes}
            self.assertEqual(self.req('/api/register',data)[0],400)
        self.assertEqual(self.req('/api/register',{'name':'Test','email':'origin@example.test','password':'Eight123'},headers={'Origin':'https://evil.example'})[0],403)

    def test_30_change_password_revokes_sessions(self):
        self.http.login_attempts=[]
        self.req('/api/register',{'name':'Password test','email':'password@example.test','password':'Eight123'})
        def auth():
            status,r,h=self.req('/api/login',{'email':'password@example.test','password':'Eight123'})
            self.assertEqual(status,200)
            return {'cookie':h['Set-Cookie'].split(';')[0],'csrf':r['csrf'],'member':r['member']}
        a=auth();b=auth()
        self.assertEqual(self.req('/api/password',{'current_password':'Eight123','new_password':'New12345'},auth=a,headers={'X-CSRF-Token':''})[0],403)
        self.assertEqual(self.req('/api/password',{'current_password':'wrong','new_password':'New12345'},auth=a)[0],400)
        self.assertEqual(self.req('/api/password',{'current_password':'Eight123','new_password':'New12345'},auth=a)[0],200)
        self.assertEqual(self.req('/api/me',auth=a)[0],401)
        self.assertEqual(self.req('/api/me',auth=b)[0],401)
        self.assertEqual(self.req('/api/login',{'email':'password@example.test','password':'Eight123'})[0],401)
        self.assertEqual(self.req('/api/login',{'email':'password@example.test','password':'New12345'})[0],200)

    def test_31_rate_limits_keyed_by_email_and_ip(self):
        h=object.__new__(server.Handler);h.server=SimpleNamespace(login_attempts=[])
        attacker=lambda:h.all_allowed(('login_pair','login:a@x.test|198.51.100.1'),('login_ip','login-ip:198.51.100.1'),('login_email','login-email:a@x.test'))
        member=lambda:h.all_allowed(('login_pair','login:a@x.test|203.0.113.5'),('login_ip','login-ip:203.0.113.5'),('login_email','login-email:a@x.test'))
        self.assertEqual(sum(attacker() for _ in range(15)),server.LIMITS['login_pair'])
        self.assertTrue(member(),'An attacker on another IP must not lock the member out')
        h.server.login_attempts=[]
        self.assertEqual(sum(h.all_allowed(('register_ip','register-ip:198.51.100.1'),('register_global','register:global')) for _ in range(8)),server.LIMITS['register_ip'])
        self.assertTrue(h.all_allowed(('register_ip','register-ip:203.0.113.5'),('register_global','register:global')))

    def test_32_internal_errors_are_not_echoed(self):
        a=self.sign_in()
        status,body,_=self.req('/api/agent',{'message':'knee MRI','search':'not-an-object'},auth=a)
        self.assertEqual(status,400);self.assertEqual(body['error'],'Invalid request')
        status,body,_=self.req('/api/agent',{'message':'','search':{}},auth=a)
        self.assertEqual(status,400);self.assertIn('1–2000',body['error'])

    def test_33_legacy_hash_upgrades_on_login(self):
        import hashlib,secrets
        salt=secrets.token_hex(16);legacy=hashlib.pbkdf2_hmac('sha256',b'Legacy123',bytes.fromhex(salt),200000).hex()
        with core.connect(self.db) as db:
            db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)',('legacy-id','review','legacy@example.test','Legacy',salt,legacy))
        self.http.login_attempts=[]
        self.assertEqual(self.req('/api/login',{'email':'legacy@example.test','password':'Legacy123'})[0],200)
        with core.connect(self.db) as db:
            stored=db.execute("SELECT password_hash FROM members WHERE id='legacy-id'").fetchone()['password_hash']
        self.assertTrue(stored.startswith(f'pbkdf2${core.PBKDF2_ITERATIONS}$'))
        self.assertEqual(self.req('/api/login',{'email':'legacy@example.test','password':'Legacy123'})[0],200)

if __name__=='__main__':unittest.main(verbosity=2)
