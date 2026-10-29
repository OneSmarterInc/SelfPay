"""Opt-in appointment requests. No delivery or schema changes at import time."""
import datetime as dt
import hashlib
import hmac
import json
import os
import re
import secrets
import smtplib
import ssl
import time
import uuid
from email.message import EmailMessage
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import core


SCHEMA = '''
CREATE TABLE booking_codes (
 id TEXT PRIMARY KEY, email TEXT NOT NULL, name TEXT NOT NULL,
 code_hash TEXT NOT NULL, expires DOUBLE PRECISION NOT NULL,
 attempts INTEGER NOT NULL DEFAULT 0, consumed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE booking_requests (
 id TEXT PRIMARY KEY, member_id TEXT NOT NULL REFERENCES members(id),
 entry_key TEXT NOT NULL, payload_hash TEXT NOT NULL,
 status TEXT NOT NULL, created DOUBLE PRECISION NOT NULL);
'''

class Unavailable(ValueError):
    pass

def enabled():
    return os.environ.get('BOOKING_ENABLED') == 'true'

def configured():
    return enabled() and all(os.environ.get(k) for k in ('SMTP_HOST','SMTP_USER','SMTP_PASSWORD','BOOKING_FROM_EMAIL','BOOKING_AUTH_SECRET')) and len(os.environ.get('BOOKING_AUTH_SECRET','')) >= 32

def require_config():
    if not configured():
        raise Unavailable('Appointment requests are not available yet. Please contact the center directly.')

def email_address(value):
    value=str(value or '').strip()
    if len(value)>254 or not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+',value):
        raise ValueError('Enter a valid email address.')
    return value

def contact(entry_key, entry):
    """Only explicitly reviewed recipients that still exist in the imported source."""
    if not configured():return None
    try:
        approved=json.loads(os.environ.get('BOOKING_CONTACTS_JSON','{}')).get(entry_key)
        if not isinstance(approved,dict) or approved.get('purpose')!='appointment_requests':return None
        address=email_address(approved.get('email'))
        source_addresses=[x.strip().casefold() for x in (entry.get('email') or '').split(';')]
        if address.casefold() not in source_addresses:return None
        if not approved.get('evidence_url','').startswith('https://'):return None
        return address
    except (ValueError,TypeError,AttributeError):return None

def send_email(recipient, subject, body, reply_to=None):
    require_config()
    message=EmailMessage()
    message['From']=email_address(os.environ['BOOKING_FROM_EMAIL'])
    message['To']=email_address(recipient)
    message['Subject']=subject
    if reply_to:message['Reply-To']=email_address(reply_to)
    message.set_content(body)
    # Explicit TLS only, never a plaintext SMTP fallback; debug logging stays off.
    port=int(os.environ.get('SMTP_PORT','465'))
    if port==465:
        client=smtplib.SMTP_SSL(os.environ['SMTP_HOST'],port,timeout=15,context=ssl.create_default_context())
    elif port==587:
        client=smtplib.SMTP(os.environ['SMTP_HOST'],port,timeout=15)
        client.ehlo();client.starttls(context=ssl.create_default_context());client.ehlo()
    else:raise Unavailable('Email delivery is not configured correctly.')
    with client:
        client.login(os.environ['SMTP_USER'],os.environ['SMTP_PASSWORD'])
        refused=client.send_message(message)
        if refused:raise Unavailable('Email delivery could not be confirmed.')

def code_digest(ident,code):
    return hmac.new(os.environ['BOOKING_AUTH_SECRET'].encode(),(ident+':'+code).encode(),hashlib.sha256).hexdigest()

def start_account(data,path=core.DB):
    require_config()
    address=email_address(data.get('email')).casefold()
    name=str(data.get('name','')).strip()
    if not 1<=len(name)<=100 or any(ord(c)<32 for c in name):raise ValueError('Enter your name (1–100 characters).')
    if data.get('consent') is not True:raise ValueError('Accept the Terms & Privacy to continue.')
    ident=secrets.token_urlsafe(24);code=f'{secrets.randbelow(1000000):06d}'
    with core.connect(path) as db:
        core.lock_usage(db)
        core.consume_windows(db,[('booking-code:'+hashlib.sha256(address.encode()).hexdigest(),3600,5),('booking-code-global',86400,200)])
        db.execute('INSERT INTO booking_codes(id,email,name,code_hash,expires) VALUES(?,?,?,?,?)',(ident,address,name,code_digest(ident,code),time.time()+600))
    try:send_email(address,'MySelfPay sign-in code',f'Your code is {code}. It expires in 10 minutes. If you did not request this, ignore this email.')
    except Exception:
        with core.connect(path) as db:db.execute('UPDATE booking_codes SET consumed=1 WHERE id=?',(ident,))
        raise Unavailable('We could not send your sign-in code. Please try again later.') from None
    return {'challenge_id':ident,'message':'Check your email for the six-digit code.'}

def verify_account(data,path=core.DB):
    require_config()
    ident=str(data.get('challenge_id',''));code=str(data.get('code',''))
    if len(ident)>100 or not re.fullmatch(r'\d{6}',code):raise ValueError('Enter the six-digit code.')
    result=None
    with core.connect(path) as db:
        core.lock_usage(db)
        row=db.execute('SELECT * FROM booking_codes WHERE id=?',(ident,)).fetchone()
        if row and not row['consumed'] and row['expires']>time.time() and row['attempts']<5:
            db.execute('UPDATE booking_codes SET attempts=attempts+1 WHERE id=?',(ident,))
            if hmac.compare_digest(row['code_hash'],code_digest(ident,code)):
                member=db.execute('SELECT id,tenant,name,email FROM members WHERE email=?',(row['email'],)).fetchone()
                if member is None:
                    mid=str(uuid.uuid4())
                    db.execute('INSERT INTO members VALUES(?,?,?,?,?,?)',(mid,'booking',row['email'],row['name'],secrets.token_hex(16),secrets.token_hex(32)))
                    member=dict(id=mid,tenant='booking',name=row['name'],email=row['email'])
                if member['tenant']=='booking':
                    token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(24)
                    db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),member['id'],csrf,time.time()+28800))
                    result=dict(member=dict(member),csrf=csrf,token=token)
                db.execute('UPDATE booking_codes SET consumed=1 WHERE id=?',(ident,))
    if result is None:raise ValueError('Code invalid or expired. Request a new code.')
    return result

def submit(member,data,path=core.DB):
    require_config()
    if member.get('tenant')!='booking':raise PermissionError('Verified account required')
    ident=str(data.get('request_id',''))
    try:uuid.UUID(ident)
    except ValueError:raise ValueError('Invalid request identifier.') from None
    key=str(data.get('entry_key',''))
    with core.connect(path) as db:
        row=db.execute('SELECT payload FROM entries WHERE batch_id=? AND entry_key=?',(core.active_batch(db),key)).fetchone()
    if not row:raise ValueError('Center no longer available.')
    entry=json.loads(row['payload']);recipient=contact(key,entry)
    if not recipient:raise ValueError('This center does not have an approved appointment email. Contact it directly.')
    name=str(data.get('name','')).strip();phone=str(data.get('phone','')).strip()
    if not 1<=len(name)<=100 or any(ord(c)<32 for c in name):raise ValueError('Enter your name.')
    if not re.fullmatch(r'[+0-9() .-]{7,30}',phone):raise ValueError('Enter a contact phone number.')
    zone=str(data.get('timezone',''))
    if zone not in ('America/New_York','America/Chicago','America/Denver','America/Phoenix','America/Los_Angeles','America/Anchorage','Pacific/Honolulu'):raise ValueError('Select the center’s time zone.')
    try:
        naive=dt.datetime.fromisoformat(str(data.get('datetime','')))
        if naive.tzinfo is not None:raise ValueError()
        requested=naive.replace(tzinfo=ZoneInfo(zone))
        if requested.astimezone(dt.timezone.utc).astimezone(ZoneInfo(zone)).replace(tzinfo=None)!=naive:raise ValueError()
        remaining=requested.timestamp()-time.time()
        if not 0<remaining<=366*86400:raise ValueError()
    except (ValueError,ZoneInfoNotFoundError):raise ValueError('Choose a valid future date and time within one year.') from None
    service=str(data.get('service',''))
    if service not in ('MRI','CT','Other imaging','Please contact me'):raise ValueError('Select a service.')
    if data.get('consent') is not True:raise ValueError('Consent is required to send your contact details to the center.')
    payload_hash=core.digest(dict(entry_key=key,name=name,phone=phone,datetime=requested.isoformat(),timezone=zone,service=service))
    with core.connect(path) as db:
        core.lock_usage(db)
        previous=db.execute('SELECT * FROM booking_requests WHERE id=?',(ident,)).fetchone()
        if previous:
            if previous['member_id']!=member['id'] or previous['payload_hash']!=payload_hash:raise ValueError('Request identifier already used.')
            return {'status':previous['status'],'request_id':ident}
        core.consume_windows(db,[('appointment-member:'+member['id'],86400,5),('appointment-global',86400,200)])
        db.execute('INSERT INTO booking_requests VALUES(?,?,?,?,?,?)',(ident,member['id'],key,payload_hash,'sending',time.time()))
    body=f'''Appointment request — not a confirmed booking
Reference: {ident}
Center: {entry['name']}
Location / coverage: {entry.get('coverage','')}
Name: {name}
Reply email: {member['email']}
Phone: {phone}
Preferred date/time: {requested.strftime('%Y-%m-%d %H:%M')} ({zone})
Service: {service}
Please contact the requester to confirm availability, location, preparation, referral requirements and total price. This is a preferred time, not a reserved appointment.
'''
    status='delivery_unknown'
    try:
        send_email(recipient,'MySelfPay appointment request',body,reply_to=member['email'])
        status='email_accepted'
    except Exception:pass  # Never expose SMTP credentials, errors or patient details.
    with core.connect(path) as db:db.execute('UPDATE booking_requests SET status=? WHERE id=?',(status,ident))
    return {'status':status,'request_id':ident}
