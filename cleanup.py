"""Retention maintenance. Dry-run unless --apply; no patient content in output."""
import argparse
import json
import os
import time
import core

def cleanup(path, apply=False, now=None):
    now=time.time() if now is None else now
    rules=[('conversations','expires<=?',(now,)),('sessions','expires<=?',(now,)),
           ('login_limits','window_id<?',(int(now//60)-2880,))]
    counts={}
    with core.connect(path) as db:
        # Hold writers while checking eligibility and deleting dependent rows.
        # This prevents a concurrent save/session creation from racing deletion.
        if apply:
            if str(path).startswith(('postgres://','postgresql://')):
                db.execute('LOCK TABLE members, sessions, conversations, preferences, corrections, guest_usage IN SHARE ROW EXCLUSIVE MODE')
            else:
                db.execute('BEGIN IMMEDIATE')
        eligible="""SELECT m.id FROM members m WHERE m.tenant='guest'
            AND NOT EXISTS (SELECT 1 FROM sessions s WHERE s.member_id=m.id AND s.expires>?)"""
        args=(now,)
        counts['guest_members']=db.execute('SELECT COUNT(*) AS n FROM members WHERE id IN ('+eligible+')',args).fetchone()['n']
        for table in ('preferences','corrections'):
            counts[table]=db.execute(f'SELECT COUNT(*) AS n FROM {table} WHERE member_id IN ('+eligible+')',args).fetchone()['n']
        counts['guest_usage']=db.execute('SELECT COUNT(*) AS n FROM guest_usage WHERE session_hash IN (SELECT token_hash FROM sessions WHERE expires<=?)',(now,)).fetchone()['n']
        if apply:db.execute('DELETE FROM guest_usage WHERE session_hash IN (SELECT token_hash FROM sessions WHERE expires<=?)',(now,))
        rules[0]=('conversations','expires<=? OR member_id IN ('+eligible+')',(now,now))
        for table,condition,args in rules:
            counts[table]=db.execute(f'SELECT COUNT(*) AS n FROM {table} WHERE {condition}',args).fetchone()['n']
            if apply:db.execute(f'DELETE FROM {table} WHERE {condition}',args)
        if apply:
            for table in ('preferences','corrections'):
                db.execute(f'DELETE FROM {table} WHERE member_id IN ('+eligible+')',(now,))
            db.execute('DELETE FROM members WHERE id IN ('+eligible+')',(now,))
    return {'applied':apply,'eligible_records':counts}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    url=os.environ.get('DATABASE_URL','')
    if not url.startswith(('postgres://','postgresql://')):raise SystemExit('Set DATABASE_URL to the intended database; no implicit local fallback.')
    print(json.dumps(cleanup(url,apply=args.apply)))
