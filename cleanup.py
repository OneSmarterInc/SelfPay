"""Retention maintenance. Dry-run unless --apply; no patient content in output."""
import argparse
import json
import os
import time
import core

def cleanup(path, apply=False, now=None):
    now=time.time() if now is None else now
    rules=[('conversations','expires<=?',(now,)),('sessions','expires<=?',(now,)),
           ('login_limits','window_id<?',(int(now//60)-2,))]
    counts={}
    with core.connect(path) as db:
        for table,condition,args in rules:
            counts[table]=db.execute(f'SELECT COUNT(*) AS n FROM {table} WHERE {condition}',args).fetchone()['n']
            if apply:db.execute(f'DELETE FROM {table} WHERE {condition}',args)
    return {'applied':apply,'eligible_records':counts}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    url=os.environ.get('DATABASE_URL','')
    if not url.startswith(('postgres://','postgresql://')):raise SystemExit('Set DATABASE_URL to the intended database; no implicit local fallback.')
    print(json.dumps(cleanup(url,apply=args.apply)))
