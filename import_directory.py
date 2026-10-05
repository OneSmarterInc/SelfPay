"""Explicit staged import, publication and rollback for the local POC."""
import argparse,json
from pathlib import Path
import core

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--db',type=Path,default=core.DB)
    sub=p.add_subparsers(dest='action',required=True)
    s=sub.add_parser('stage');s.add_argument('source',type=Path);s.add_argument('--mappings',type=Path,default=core.ROOT/'seed/mappings.json')
    for name in ('publish','rollback'):
        s=sub.add_parser(name);s.add_argument('batch_id')
    sub.add_parser('list');args=p.parse_args();core.initialize(args.db)
    if args.action=='stage':r=core.stage_import(args.source,args.mappings,args.db)
    elif args.action in ('publish','rollback'):r=core.publish(args.batch_id,args.db)
    else:
        with core.connect(args.db) as db:r={'active':core.active_batch(db),'batches':[dict(x) for x in db.execute('SELECT * FROM batches ORDER BY created DESC')]}
    print(json.dumps(r,indent=2))
if __name__=='__main__':main()
