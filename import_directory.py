"""Explicit staged import, publication and rollback. Live use requires approved change control."""
import argparse
import json
from pathlib import Path
import core


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', default=core.DB,
                   help='Local SQLite path; use DATABASE_URL securely for PostgreSQL')
    sub = p.add_subparsers(dest='action', required=True)
    s = sub.add_parser('stage')
    s.add_argument('source', type=Path)
    s.add_argument('--mappings', type=Path, required=True,
                   help='Explicit reviewed mappings; stage derives and validates required locations and reports unplaced entries')
    for name in ('publish', 'rollback'):
        s = sub.add_parser(name)
        s.add_argument('batch_id')
    sub.add_parser('list')
    args = p.parse_args()
    # A branch copy already contains its schema. Never initialize a hosted DB
    # implicitly, including on list. Schema setup is a separate approved change.
    hosted = str(args.db).startswith(('postgres://', 'postgresql://'))
    if not hosted:
        core.initialize(args.db)
    if args.action == 'stage':
        result = core.stage_import(args.source, args.mappings, args.db)
    elif args.action in ('publish', 'rollback'):
        result = core.publish(args.batch_id, args.db)
    else:
        with core.connect(args.db) as db:
            result = {'active': core.active_batch(db),
                      'batches': [dict(x) for x in db.execute(
                          'SELECT * FROM batches ORDER BY created DESC')]}
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

