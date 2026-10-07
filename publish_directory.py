"""Validate and publish the bundled provider directory; never resets member data."""
import argparse
import json
import os
from pathlib import Path


def main():
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).with_name('.env.local'), override=False)
    import core
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Publish after validation; otherwise stage only')
    args = parser.parse_args()
    url = os.environ.get('DATABASE_URL', '')
    if not url.startswith(('postgres://', 'postgresql://')):
        raise SystemExit('DATABASE_URL must identify your review PostgreSQL database.')
    result = core.stage_import(core.ROOT/'seed/directory.json', core.ROOT/'seed/mappings.json', url)
    print(json.dumps(result, indent=2))
    if result['entry_count'] != 74 or result['offer_count'] != 57 or result['withheld_offers']:
        raise SystemExit('Directory validation failed; nothing published.')
    if args.apply:
        publication = core.publish(result['id'], url)
        data = core.catalog(url)
        print(json.dumps({'publication': publication, 'entries': len(data['entries']), 'offers': len(data['offers'])}, indent=2))
    else:
        print('Staged only. Run with --apply to publish. Member data is unchanged.')


if __name__ == '__main__':
    main()
