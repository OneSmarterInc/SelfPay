"""Local POC domain and persistence. No external AI, clinical or payment integrations."""
from __future__ import annotations
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DB = os.environ.get('DATABASE_URL') or ROOT / 'data' / 'myselfpay.sqlite3'
DEMO_PASSWORD = os.environ.get('REVIEW_PASSWORD', 'DemoOnly-2026!')
ACCOUNTS = [('alex.a@example.test','plan-a','Alex'), ('sam.a@example.test','plan-a','Sam'),
            ('alex.b@example.test','plan-b','Alex'), ('jordan.b@example.test','plan-b','Jordan')]

PBKDF2_ITERATIONS = 600000  # OWASP 2023 guidance for PBKDF2-HMAC-SHA256
LEGACY_ITERATIONS = 200000  # hashes stored before the upgrade are bare hex at this count

def hash_password(password, salt_hex, iterations=PBKDF2_ITERATIONS):
    raw = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt_hex), iterations).hex()
    return raw if iterations == LEGACY_ITERATIONS else f'pbkdf2${iterations}${raw}'

def verify_password(password, salt_hex, stored):
    """Constant-time check that accepts current and legacy hash formats."""
    iterations = int(stored.split('$')[1]) if stored.startswith('pbkdf2$') else LEGACY_ITERATIONS
    return hmac.compare_digest(hash_password(password, salt_hex, iterations), stored)

def needs_rehash(stored):
    return not stored.startswith(f'pbkdf2${PBKDF2_ITERATIONS}$')

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def connect(path=DB):
    if str(path).startswith(('postgres://','postgresql://')):
        from postgres_store import PostgresConnection
        return PostgresConnection(str(path))
    con = sqlite3.connect(path, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con

def initialize(path=DB):
    if not str(path).startswith(('postgres://','postgresql://')):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    with connect(path) as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, content_hash TEXT UNIQUE NOT NULL,
            source_name TEXT NOT NULL, created REAL NOT NULL, status TEXT NOT NULL, report TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS entries(batch_id TEXT REFERENCES batches(id), entry_key TEXT,
            content_hash TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(batch_id,entry_key));
        CREATE TABLE IF NOT EXISTS offers(batch_id TEXT, id TEXT, entry_key TEXT, amount_cents INTEGER,
            max_cents INTEGER, price_type TEXT NOT NULL, payload TEXT NOT NULL, PRIMARY KEY(batch_id,id),
            FOREIGN KEY(batch_id,entry_key) REFERENCES entries(batch_id,entry_key));
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS publish_events(id INTEGER PRIMARY KEY, batch_id TEXT REFERENCES batches(id),
            previous_batch TEXT, created REAL NOT NULL, action TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS members(id TEXT PRIMARY KEY, tenant TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY, member_id TEXT REFERENCES members(id),
            csrf TEXT NOT NULL, expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS conversations(id TEXT PRIMARY KEY, tenant TEXT NOT NULL,
            member_id TEXT REFERENCES members(id), title TEXT NOT NULL, payload TEXT NOT NULL,
            updated REAL NOT NULL, expires REAL NOT NULL);
        CREATE INDEX IF NOT EXISTS conversation_owner ON conversations(tenant,member_id);
        CREATE TABLE IF NOT EXISTS preferences(member_id TEXT PRIMARY KEY REFERENCES members(id),
            tenant TEXT NOT NULL, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS corrections(id TEXT PRIMARY KEY, tenant TEXT NOT NULL,
            member_id TEXT REFERENCES members(id), offer_id TEXT NOT NULL, batch_id TEXT NOT NULL,
            category TEXT NOT NULL, description TEXT NOT NULL, created REAL NOT NULL, status TEXT NOT NULL);
        ''')
        db.execute('PRAGMA secure_delete=ON')
        for email, tenant, name in ACCOUNTS:
            if db.execute('SELECT 1 FROM members WHERE email=?', (email,)).fetchone(): continue
            salt = secrets.token_hex(16)
            pw = hash_password(DEMO_PASSWORD, salt)
            db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)', (str(uuid.uuid4()),tenant,email,name,salt,pw))
    try: os.chmod(path,0o600)
    except OSError: pass

def active_batch(db):
    row=db.execute("SELECT value FROM settings WHERE key='active_batch'").fetchone()
    return row['value'] if row else None

def read_source(path):
    path=Path(path)
    if path.suffix.lower()=='.json': return json.loads(path.read_text(encoding='utf-8'))
    if path.suffix.lower()!='.xlsx': raise ValueError('Use .json or .xlsx')
    try: import openpyxl
    except ImportError as exc: raise ValueError('XLSX import requires openpyxl; the bundled JSON seed needs no extra package.') from exc
    wb=openpyxl.load_workbook(path,read_only=True,data_only=True)
    if 'Directory' not in wb.sheetnames: raise ValueError('Workbook needs a Directory tab')
    keys=['name','area','states','entity','category','mri','ct','other','coverage','notes','source','additional','checked']
    rows=[];started=False
    for number,row in enumerate(wb['Directory'].iter_rows(values_only=True),start=1):
        cells=list(row[:13])+[None]*max(0,13-len(row))
        if str(cells[0]).strip()=='Center or operator': started=True;continue
        if not started or not cells[0]: continue
        vals=[v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v,(dt.datetime,dt.date)) else '' if v is None else str(v) for v in cells]
        rows.append({'row':str(number-2),**dict(zip(keys,vals))})
    wb.close()
    if not rows: raise ValueError('No directory entries found')
    return rows

def stage_import(source, mappings, path=DB):
    entries=read_source(source); maps=json.loads(Path(mappings).read_text(encoding='utf-8'))
    if not isinstance(entries,list) or not entries: raise ValueError('Source must contain an entry list')
    errors=[]; names=set(); normalized=[]
    for entry in entries:
        if not isinstance(entry,dict): raise ValueError('Malformed source entry')
        name=entry.get('name','').strip()
        if not name or name in names: errors.append(f'Missing or duplicate name: {name}')
        names.add(name)
        if urlparse(entry.get('source','')).scheme!='https': errors.append(f'{name}: invalid source URL')
        try: dt.date.fromisoformat(entry.get('checked','')[:10])
        except ValueError: errors.append(f'{name}: missing or invalid verification date')
        normalized.append((digest(name),digest({k:v for k,v in entry.items() if k!='row'}),entry))
    if errors: raise ValueError('; '.join(errors))
    signature=digest({'entries':entries,'mappings':maps})
    with connect(path) as db:
        existing=db.execute('SELECT id,report,status FROM batches WHERE content_hash=?',(signature,)).fetchone()
        if existing: return {'id':existing['id'],'unchanged':True,'status':existing['status'],**json.loads(existing['report'])}
        prior=active_batch(db)
        old={r['entry_key']:r['content_hash'] for r in db.execute('SELECT entry_key,content_hash FROM entries WHERE batch_id=?',(prior,))}
        current={k:h for k,h,e in normalized}
        report={'entry_count':len(entries),'added':sum(k not in old for k in current),
                'changed':sum(k in old and old[k]!=h for k,h in current.items()),
                'removed':sum(k not in current for k in old),'withheld_offers':[],'offer_count':0}
        batch=str(uuid.uuid4()); offers=[]; mapping_ids=set()
        lookup={e['name']:(k,h,e) for k,h,e in normalized}
        for m in maps:
            if m.get('id') in mapping_ids: raise ValueError('Duplicate offer mapping id')
            mapping_ids.add(m.get('id'))
            match=lookup.get(m.get('entry_name'))
            if not match or m.get('entry_hash')!=match[1]:
                report['withheld_offers'].append({'id':m.get('id'),'reason':'Source entry changed or missing; mapping needs human review'})
                continue
            if m.get('type') not in ('fixed','starting','range','maximum','conflict','average','quote'): raise ValueError('Invalid price type')
            if m.get('contrast') not in ('unknown','without','with','both'): raise ValueError('Invalid contrast')
            if m.get('mod') not in ('MRI','CT'):raise ValueError('Unsupported mapped modality')
            if m['type'] in ('fixed','starting','range','maximum','average') and m.get('amount') is None:raise ValueError('Numeric price type needs an amount')
            for field in ('amount','max'):
                if field in m:
                    from decimal import Decimal
                    value=m[field]
                    if isinstance(value,bool) or not isinstance(value,(int,float)):raise ValueError('Invalid money')
                    decimal=Decimal(str(value))
                    if not decimal.is_finite() or decimal<0 or decimal*100!=(decimal*100).to_integral_value():raise ValueError('Money must be nonnegative with at most two decimals')
            if m['type']=='range' and (m.get('max') is None or m['max']<m['amount']):raise ValueError('Invalid price range')
            offers.append((m,match[0]))
        report['offer_count']=len(offers)
        db.execute('INSERT INTO batches VALUES(?,?,?,?,?,?)',(batch,signature,Path(source).name,time.time(),'staged',canonical(report)))
        db.executemany('INSERT INTO entries VALUES(?,?,?,?)',[(batch,k,h,canonical(e)) for k,h,e in normalized])
        for m,key in offers:
            from decimal import Decimal
            cents=lambda v: int(Decimal(str(v))*100) if v is not None else None
            db.execute('INSERT INTO offers VALUES(?,?,?,?,?,?,?)',(batch,m['id'],key,cents(m.get('amount')),cents(m.get('max')),m['type'],canonical(m)))
    return {'id':batch,'unchanged':False,'status':'staged',**report}

def publish(batch,path=DB):
    with connect(path) as db:
        row=db.execute('SELECT status FROM batches WHERE id=?',(batch,)).fetchone()
        if not row: raise ValueError('Unknown batch')
        old=active_batch(db)
        if old==batch: return {'active_batch':batch,'unchanged':True}
        db.execute("INSERT INTO settings VALUES('active_batch',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(batch,))
        db.execute("UPDATE batches SET status='published' WHERE id=?",(batch,))
        db.execute('INSERT INTO publish_events(batch_id,previous_batch,created,action) VALUES(?,?,?,?)',(batch,old,time.time(),'publish' if row['status']=='staged' else 'rollback'))
    return {'active_batch':batch,'previous_batch':old}

def catalog(path=DB):
    with connect(path) as db:
        batch=active_batch(db)
        entries={r['entry_key']:json.loads(r['payload']) for r in db.execute('SELECT * FROM entries WHERE batch_id=?',(batch,))}
        offers=[]
        for r in db.execute('SELECT * FROM offers WHERE batch_id=?',(batch,)):
            o=json.loads(r['payload']);o['entry']=entries[r['entry_key']];o['version']=batch
            o['amount']=r['amount_cents']/100 if r['amount_cents'] is not None else None
            if r['max_cents'] is not None:o['max']=r['max_cents']/100
            offers.append(o)
    return {'version':batch,'entries':list(entries.values()),'offers':offers}

LOCATION_CHOICES = [('Cincinnati, OH','Cincinnati'),('Louisville, KY','Louisville'),('Lexington, KY','Lexington'),('Philadelphia, PA','Philadelphia'),('Boise, ID','Boise'),('Lawrenceville, GA','Lawrenceville'),('Auburn, WA','Auburn'),('Spanish Fork, UT','Spanish Fork'),('South Burlington, VT','South Burlington'),('Wisconsin','Wisconsin'),('National','National')]

def location_options(value):
    from difflib import SequenceMatcher
    q=value.strip().casefold()
    exact=[label for label,city in LOCATION_CHOICES if q in (label.casefold(),city.casefold())]
    if exact:return exact
    return [label for label,city in LOCATION_CHOICES if q and (city.casefold().startswith(q) or SequenceMatcher(None,q,city.casefold()).ratio()>=0.65)]

def clean_search(raw):
    mod=raw.get('mod',''); contrast=raw.get('contrast','unknown'); typ=raw.get('type','all')
    if mod not in ('','MRI','CT') or contrast not in ('unknown','without','with','both'): raise ValueError('Invalid procedure or contrast')
    if typ not in ('all','fixed','starting','range','maximum','conflict','average','quote'): raise ValueError('Invalid price filter')
    try: budget=float(raw.get('budget') or 0)
    except (TypeError,ValueError): raise ValueError('Invalid budget')
    if not 0<=budget<=1000000: raise ValueError('Invalid budget')
    return {'mod':mod,'contrast':contrast,'type':typ,'body':str(raw.get('body',''))[:100],
            'location':str(raw.get('location',''))[:120].strip(),'budget':budget,
            'sort':'price' if raw.get('sort')=='price' else 'scope',
            'selected':list(dict.fromkeys(x for x in raw.get('selected',[]) if isinstance(x,str)))[:3]}

def search(raw,path=DB):
    s=clean_search(raw); data=catalog(path); result=[]; location=s['location'].casefold()
    exact=[city for label,city in LOCATION_CHOICES if label.casefold()==location]
    if exact:location=exact[0].casefold()
    suggestions=location_options(s['location'])
    needs_choice=bool(suggestions) and (not any(location==city.casefold() for label,city in LOCATION_CHOICES) or (location=='auburn' and not exact))
    if needs_choice:location='__unconfirmed_location__'
    for o in data['offers']:
        if not s['mod'] or not s['body'].strip() or not location:continue
        e=o['entry']
        if o['mod']!=s['mod'] or (s['type']!='all' and s['type']!=o['type']):continue
        if s['contrast']!='unknown' and o['contrast'] not in (s['contrast'],'unknown'):continue
        if not (location=='national' or location in o['region'].casefold() or location in e['area'].casefold() or location==e['states'].casefold()):continue
        o['match_status']='Exact body-part and protocol applicability requires confirmation'
        o['budget_status']='Budget fit unconfirmed'
        if not s['budget']:o['budget_status']='No budget set'
        elif o['type']=='fixed' and o['amount']>s['budget']:o['budget_status']='Above your published-price budget'
        elif o['type']=='fixed' and o['contrast']!='unknown':o['budget_status']='Published amount within budget · exact scope needs confirmation'
        result.append(o)
    if s['sort']=='price':result.sort(key=lambda o:o['amount'] if o['type']=='fixed' and o['amount'] is not None else float('inf'))
    selected=set(o['id'] for o in result);s['selected']=[x for x in s['selected'] if x in selected]
    return {'version':data['version'],'search':s,'offers':result,'count':len(result),'location_suggestions':suggestions if needs_choice else []}

def agent(message,raw,path=DB):
    import re
    if not isinstance(message,str) or not message.strip() or len(message)>2000:raise ValueError('Use a message of 1–2000 characters')
    s=clean_search(raw);low=message.casefold()
    if re.search(r'what.*(test|scan).*need|diagnos|symptom|should i get',low):
        reply='I can help find published prices, but cannot diagnose or decide which test you need. Confirm the exam with your clinician.'
    elif 'second opinion' in low:
        reply='Do you mean a specialist consultation, a review of existing images, or a new exam? Consultation and image-review providers need separate research.'
    else:
        if re.search(r'\bct\b',low):s['mod']='CT'
        if re.search(r'\bmri\b',low):s['mod']='MRI'
        for body in ('knee','brain','lumbar','shoulder'):
            if body in low:s['body']=body.title()
        if 'without and with' in low or 'with and without' in low:s['contrast']='both'
        elif 'without contrast' in low or 'noncontrast' in low:s['contrast']='without'
        elif 'with contrast' in low:s['contrast']='with'
        money=re.search(r'(?:under|below|budget)\s*\$?(\d+)',low)
        if money:s['budget']=float(money[1])
        place=re.search(r'\b(?:near|in)\s+(.+?)(?=\s+(?:under|below|budget|with|without)\b|[.!?]|$)',message,re.I)
        if place:s['location']=place.group(1).strip()
        elif location_options(message.strip()):s['location']=message.strip()
        reply='Is your ordered exam without contrast, with contrast, or without and with contrast? If unsure, confirm with your clinician.' if s['contrast']=='unknown' else 'Your search has been updated. Review the sourced candidates below and confirm the exact study, eligibility and total with the facility. These are published references, not current quotes.'
    guidance_blocked=bool(re.search(r'what.*(test|scan).*need|diagnos|symptom|should i get',low)) or 'second opinion' in low
    if not guidance_blocked and not s['mod']:reply='What imaging service are you looking for: MRI or CT? Use the exam specified by your clinician.'
    elif not guidance_blocked and not s['body'].strip():reply='What body part is the exam for? Use the wording on your order, if you have one.'
    elif not guidance_blocked and not s['location']:reply='What city or state would you like to search near? ZIP and distance matching are not connected in this demo.'
    elif not guidance_blocked and s['location'].isdigit():reply='ZIP matching is not connected in this demo. Please enter a city or state in Search details.'
    result=search(s,path)
    if not guidance_blocked and result['location_suggestions']:
        reply='Did you mean '+ ' or '.join(result['location_suggestions'])+'? Select a location below to update the search.'
    elif not guidance_blocked and result['offers'] and any(o['contrast']=='unknown' for o in result['offers']):
        reply+=' Some listings have unconfirmed contrast or protocol. A published amount below your budget does not confirm that it covers your requested exam or all fees; ask the facility for the exact total.'
    return {'reply':reply,**result,'agent_mode':'deterministic-demo'}

def normalize_email(email):
    import re
    if not isinstance(email,str):raise ValueError('Enter a valid email address')
    email=email.strip().casefold()
    if len(email)>200 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):
        raise ValueError('Enter a valid email address')
    return email

def password_fields(password):
    if not isinstance(password,str) or not 8<=len(password)<=200:
        raise ValueError('Use a password between 8 and 200 characters')
    salt=secrets.token_hex(16)
    return salt,hash_password(password,salt)

def register(name,email,password,path=DB):
    email=normalize_email(email)
    if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ValueError('Enter a name of 1–80 characters')
    salt,hashed=password_fields(password)
    with connect(path) as db:
        # Same response whether or not the email exists, so registration cannot be used to probe accounts.
        db.execute('INSERT INTO members VALUES(?,?,?,?,?,?) ON CONFLICT(email) DO NOTHING',
            (str(uuid.uuid4()),'review',email,name.strip(),salt,hashed))
    return {'ok':True,'message':'If this email can be registered, your account is ready. Sign in to continue.'}

def change_password(member,current_password,new_password,path=DB):
    if not isinstance(current_password,str) or len(current_password)>200:raise ValueError('Current password is incorrect')
    salt,hashed=password_fields(new_password)
    with connect(path) as db:
        row=db.execute('SELECT salt,password_hash FROM members WHERE id=? AND tenant=?',(member['id'],member['tenant'])).fetchone()
        if not row or not verify_password(current_password,row['salt'],row['password_hash']):raise ValueError('Current password is incorrect')
        db.execute('UPDATE members SET salt=?,password_hash=? WHERE id=? AND tenant=?',(salt,hashed,member['id'],member['tenant']))
        db.execute('DELETE FROM sessions WHERE member_id=?',(member['id'],))
    return {'ok':True}

def login(email,password,path=DB):
    email=normalize_email(email)
    if not isinstance(password,str) or len(password)>200:return None
    with connect(path) as db:
        row=db.execute('SELECT * FROM members WHERE email=?',(email,)).fetchone()
        if not row:
            hash_password(password,'00'*16)  # equal work for unknown emails (no enumeration by timing)
            return None
        if not verify_password(password,row['salt'],row['password_hash']):return None
        if needs_rehash(row['password_hash']):
            salt=secrets.token_hex(16);hashed=hash_password(password,salt)
            db.execute('UPDATE members SET salt=?,password_hash=? WHERE id=?',(salt,hashed,row['id']))
        token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
        db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),row['id'],csrf,time.time()+8*3600))
        return {'token':token,'csrf':csrf,'member':{'id':row['id'],'tenant':row['tenant'],'name':row['name'],'email':row['email']}}

def session(token,path=DB):
    with connect(path) as db:
        db.execute('DELETE FROM sessions WHERE expires<=?',(time.time(),))
        row=db.execute('SELECT m.id,m.tenant,m.name,m.email,s.csrf FROM sessions s JOIN members m ON m.id=s.member_id WHERE s.token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
        return dict(row) if row else None

def history(member,path=DB):
    with connect(path) as db:
        db.execute('PRAGMA secure_delete=ON')
        db.execute('DELETE FROM conversations WHERE expires<=?',(time.time(),))
        return [{'id':r['id'],'title':r['title'],'updated':r['updated']*1000,'expires':r['expires']*1000,**json.loads(r['payload'])} for r in db.execute('SELECT * FROM conversations WHERE tenant=? AND member_id=? ORDER BY updated DESC',(member['tenant'],member['id']))]

def save_conversation(member,data,path=DB):
    if data.get('private'):raise ValueError('Private conversations cannot be persisted')
    ident=data.get('id') or str(uuid.uuid4());messages=data.get('messages',[])
    if not isinstance(messages,list) or not 0<=len(messages)<=200:raise ValueError('History must contain at most 200 messages')
    if not messages and not all(data.get('search',{}).get(k) for k in ('mod','body','location')):raise ValueError('A saved search needs exam, body part and location')
    for m in messages:
        if not isinstance(m,dict) or m.get('role') not in ('user','assistant') or not isinstance(m.get('text'),str) or len(m['text'])>4000:raise ValueError('Invalid message')
    result=search(data.get('search',{}),path); now=time.time()
    payload=canonical({'messages':messages,'search':result['search'],'version':result['version']})
    with connect(path) as db:
        row=db.execute('SELECT tenant,member_id FROM conversations WHERE id=?',(ident,)).fetchone()
        if row and (row['tenant']!=member['tenant'] or row['member_id']!=member['id']):raise PermissionError('Conversation unavailable')
        changed=db.execute('INSERT INTO conversations VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title,payload=excluded.payload,updated=excluded.updated,expires=excluded.expires WHERE conversations.tenant=excluded.tenant AND conversations.member_id=excluded.member_id',
            (ident,member['tenant'],member['id'],f"{result['search']['mod']} · {result['search']['location']}",payload,now,now+90*86400)).rowcount
        if not changed:raise PermissionError('Conversation unavailable')
    return {'id':ident}

def delete_conversation(member,ident,path=DB):
    with connect(path) as db:
        db.execute('PRAGMA secure_delete=ON')
        if ident=='all':db.execute('DELETE FROM conversations WHERE tenant=? AND member_id=?',(member['tenant'],member['id']))
        else:
            count=db.execute('DELETE FROM conversations WHERE id=? AND tenant=? AND member_id=?',(ident,member['tenant'],member['id'])).rowcount
            if not count:raise PermissionError('Conversation unavailable')

def preference(member,value=None,delete=False,path=DB):
    with connect(path) as db:
        if delete:db.execute('DELETE FROM preferences WHERE member_id=? AND tenant=?',(member['id'],member['tenant']))
        elif value is not None:
            location=str(value.get('location',''))[:120]
            db.execute('INSERT INTO preferences VALUES(?,?,?) ON CONFLICT(member_id) DO UPDATE SET payload=excluded.payload',(member['id'],member['tenant'],canonical({'location':location})))
        row=db.execute('SELECT payload FROM preferences WHERE member_id=? AND tenant=?',(member['id'],member['tenant'])).fetchone()
        return json.loads(row['payload']) if row else {}
