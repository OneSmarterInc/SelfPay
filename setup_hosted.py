"""Run once against a NEW, DEDICATED review database before deployment."""
import os
import core

def setup():
    url=os.environ.get('DATABASE_URL','')
    password=os.environ.get('REVIEW_PASSWORD','')
    if not url.startswith(('postgres://','postgresql://')):raise SystemExit('Set DATABASE_URL to the dedicated PostgreSQL database.')
    if len(password)<8 or password=='DemoOnly-2026!':raise SystemExit('Set a unique REVIEW_PASSWORD of at least 8 characters before setup.')
    core.initialize(url)
    with core.connect(url) as db:
        db.execute('CREATE TABLE IF NOT EXISTS login_limits(key TEXT NOT NULL, window_id BIGINT NOT NULL, attempts INTEGER NOT NULL, PRIMARY KEY(key,window_id))')
        active=core.active_batch(db)
    if not active:
        batch=core.stage_import(core.ROOT/'seed/directory.json',core.ROOT/'seed/mappings.json',url)
        core.publish(batch['id'],url)
    print('Review database ready. Four synthetic accounts; no local member data copied.')
if __name__=='__main__':setup()
