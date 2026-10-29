"""Refresh deployment copies without changing the existing Vercel source layout."""
import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_FILES = ['server.py', 'core.py', 'geo.py', 'proximity.py', 'postgres_store.py',
                 'facility_locations.py', 'requirements.txt', 'app-config.json',
                 'tools/generate_app_config.py']


def mappings(root):
    pairs = [(root / p, root / 'backend' / p) for p in BACKEND_FILES]
    for source, target in [('static', 'frontend/public'), ('seed', 'backend/seed')]:
        pairs.extend((p, root / target / p.relative_to(root / source))
                     for p in sorted((root / source).rglob('*')) if p.is_file())
    return pairs


def sync(root=ROOT, check=False):
    pairs = mappings(root)
    expected = {dst for _, dst in pairs}
    stale = [p for base in (root / 'frontend/public', root / 'backend/seed')
             for p in base.rglob('*') if p.is_file() and p not in expected]
    changed = [dst for src, dst in pairs if not dst.exists() or src.read_bytes() != dst.read_bytes()]
    if check:
        if changed or stale:
            raise SystemExit('AWS folders are stale. Run python tools/sync_aws_folders.py and commit the results.')
    else:
        for p in stale:
            p.unlink()
        for src, dst in pairs:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    return len(pairs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    print(f'{sync(check=args.check)} deployment files verified.' if args.check else f'{sync()} deployment files refreshed.')
