"""Strict public-directory bundle validation and restricted PostgreSQL synchronization.

No application initialization, mapping generation, credential discovery or user-table
access. Export runs locally against a freshly materialized canonical Library file.
"""
import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qsl, unquote, urlsplit

LIBRARY_ID = 'libfile_8ba8491c8ff881918ed4868c0ee43465'
BRANCH_ID = 'br-rapid-mouse-b7clh18t'
DATABASE = 'neondb'
IMPORT_ROLE = 'selfpay_directory_importer'
FIELDS = ('row', 'name', 'area', 'states', 'entity', 'category', 'mri', 'ct',
          'other', 'coverage', 'notes', 'source', 'additional', 'checked')
HEADERS = ('Center or operator', 'City / area', 'State', 'Entity type', 'Pricing category',
           'MRI self-pay (USD)', 'CT self-pay (USD)', 'Other imaging (USD)', 'Coverage',
           'Inclusions and caveats', 'Official pricing / program source', 'Additional official sources', 'Checked on')
MAX_BYTES = 5_000_000
HEX = re.compile(r'^[0-9a-f]{64}$')

# Only exact, reviewed server messages may become public error codes.
DATABASE_GUARD_ERRORS = {
    "directory sync: bootstrap requires the reviewed active batch": "bootstrap_active_batch_mismatch",
    "directory sync: reviewed bootstrap full-row fingerprint mismatch": "bootstrap_fingerprint_mismatch",
    "directory sync: source version or export freshness rejected": "source_version_or_freshness_rejected",
    "directory sync: first apply must exactly match the reviewed catalog": "bootstrap_catalog_mismatch",
    "directory sync: active batch changed (compare-and-swap mismatch)": "active_batch_conflict"
}

def database_guard_error(exc):
    if getattr(exc, 'sqlstate', None) != 'P0001':
        return None
    primary = getattr(getattr(exc, 'diag', None), 'message_primary', None)
    return DATABASE_GUARD_ERRORS.get(primary) if isinstance(primary, str) else None


class ValidationError(ValueError):
    """Messages are fixed safe codes; never include untrusted data or credentials."""

def require(ok, code):
    if not ok:
        raise ValidationError(code)

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()

def utcnow():
    return dt.datetime.now(dt.timezone.utc)

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate_json_key')
            result[key] = value
        return result
    def invalid_number(_):
        raise ValidationError('invalid_json_number')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_number)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as exc:
        raise ValidationError('invalid_json') from exc

def checked_date(value):
    require(bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}( 00:00:00)?', value)), 'invalid_checked_date')
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError as exc:
        raise ValidationError('invalid_checked_date') from exc

def public_url(value):
    try:
        url = urlsplit(value)
        host = (url.hostname or '').lower().rstrip('.')
        try:
            address = ipaddress.ip_address(host)
            host_ok = address.is_global
        except ValueError:
            # Require a DNS-style alphabetic TLD, excluding browser-style numeric
            # address shorthand, octal/hex IPv4, and internal/local names.
            host_ok = bool(re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{1,62}', host))
            host_ok = host_ok and not host.endswith(('.localhost', '.local', '.internal'))
        return (url.scheme == 'https' and host_ok
                and not url.username and not url.password and not any(c.isspace() for c in value)
                and url.port in (None, 443))
    except ValueError:
        return False

def validate_entry(entry, now):
    require(isinstance(entry, dict) and set(entry) == set(FIELDS), 'unexpected_entry_fields')
    require(all(isinstance(v, str) and len(v) <= 12000 and '\x00' not in v for v in entry.values()), 'invalid_entry_text')
    require(0 < len(entry['name']) <= 300 and entry['name'] == entry['name'].strip(), 'invalid_entry_name')
    require(bool(re.fullmatch(r'[0-9]{1,6}', entry['row'])), 'invalid_source_row')
    require(public_url(entry['source']), 'invalid_public_source_url')
    # This column includes official-source notes; preserve wording and validate any URLs.
    urls = re.findall(r'https?://[^\s<>]+', entry['additional'])
    require(all(public_url(u.rstrip('.,;')) for u in urls), 'invalid_additional_url')
    require(checked_date(entry['checked']) <= now.date(), 'future_source_check')

def read_workbook(path):
    import openpyxl
    require(path.suffix.lower() == '.xlsx' and path.is_file(), 'xlsx_required')
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False, keep_links=False)
    entries = []
    try:
        require('Directory' in wb.sheetnames, 'directory_sheet_missing')
        started = False
        for number, row in enumerate(wb['Directory'].iter_rows(), start=1):
            values = [cell.value for cell in row[:13]]
            values += [None] * (13 - len(values))
            if str(values[0]).strip() == HEADERS[0]:
                require(not started and tuple(str(v).strip() for v in values) == HEADERS, 'directory_header_mismatch')
                started = True
                continue
            if not started or not values[0]:
                continue
            require(all(cell.data_type != 'f' for cell in row[:13]), 'formula_in_directory')
            require(not any(cell.value not in (None, '') for cell in row[13:]), 'unexpected_directory_columns')
            values = [v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, (dt.datetime, dt.date))
                      else '' if v is None else str(v) for v in values]
            entries.append(dict(zip(FIELDS, [str(number-2), *values])))
        require(started and bool(entries), 'directory_empty')
    finally:
        wb.close()
    return entries

def make_bundle(path, version, now=None):
    now = now or utcnow()
    require(type(version) is int and version >= 7, 'source_version_too_old')
    rows = read_workbook(path)
    entries = []
    for row in rows:
        validate_entry(row, now)
        content = canonical({k:v for k,v in row.items() if k != 'row'})
        entries.append({'entry_key': digest(canonical(row['name'])), 'content_hash': digest(content),
                        'payload': canonical(row), 'content': content})
    bundle = {'schema_version': 1,
              'source': {'library_file_id': LIBRARY_ID, 'version': version,
                         'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                         'exported_at': now.isoformat(timespec='seconds').replace('+00:00', 'Z')},
              'target': {'database': DATABASE, 'neon_branch_id': BRANCH_ID},
              'entries': sorted(entries, key=lambda x:x['entry_key'])}
    validate_bundle(canonical(bundle), now=now)
    return bundle

def validate_bundle(raw, now=None, require_fresh=True):
    now = now or utcnow()
    require(isinstance(raw, str) and len(raw.encode('utf-8')) <= MAX_BYTES, 'bundle_size_limit')
    bundle = strict_json(raw)
    require(isinstance(bundle, dict) and set(bundle) == {'schema_version','source','target','entries'}, 'unexpected_bundle_fields')
    require(type(bundle['schema_version']) is int and bundle['schema_version'] == 1, 'unsupported_schema')
    source = bundle['source']
    require(isinstance(source, dict) and set(source) == {'library_file_id','version','sha256','exported_at'}, 'unexpected_source_fields')
    require(source['library_file_id'] == LIBRARY_ID, 'wrong_library_source')
    require(type(source['version']) is int and source['version'] >= 7, 'source_version_too_old')
    require(isinstance(source['sha256'], str) and bool(HEX.fullmatch(source['sha256'])), 'invalid_workbook_hash')
    require(isinstance(source['exported_at'], str) and bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', source['exported_at'])), 'invalid_export_timestamp')
    try:
        exported = dt.datetime.fromisoformat(source['exported_at'].replace('Z', '+00:00'))
    except ValueError as exc:
        raise ValidationError('invalid_export_timestamp') from exc
    require(exported <= now + dt.timedelta(minutes=5), 'future_export')
    if require_fresh:
        require(exported >= now - dt.timedelta(hours=48), 'stale_export')
    require(bundle['target'] == {'database': DATABASE, 'neon_branch_id': BRANCH_ID}, 'wrong_target')
    entries = bundle['entries']
    require(isinstance(entries, list) and 93 <= len(entries) <= 10000, 'invalid_entry_count')
    keys, names = set(), set()
    for item in entries:
        require(isinstance(item, dict) and set(item) == {'entry_key','content_hash','payload','content'}, 'unexpected_normalized_fields')
        require(all(isinstance(v, str) for v in item.values()), 'invalid_normalized_text')
        entry, content = strict_json(item['payload']), strict_json(item['content'])
        validate_entry(entry, now)
        require(item['payload'] == canonical(entry), 'noncanonical_payload')
        require(item['content'] == canonical({k:v for k,v in entry.items() if k != 'row'}), 'content_payload_mismatch')
        require(content == {k:v for k,v in entry.items() if k != 'row'}, 'content_payload_mismatch')
        require(item['content_hash'] == digest(item['content']), 'entry_hash_mismatch')
        require(item['entry_key'] == digest(canonical(entry['name'])), 'entry_key_mismatch')
        require(item['entry_key'] not in keys and entry['name'].casefold() not in names, 'duplicate_entry')
        keys.add(item['entry_key']); names.add(entry['name'].casefold())
    require(entries == sorted(entries, key=lambda x:x['entry_key']), 'unsorted_entries')
    return bundle

def export_bundle(workbook, version, destination, now=None):
    bundle = make_bundle(workbook, version, now)
    raw = canonical(bundle) + '\n'
    destination.mkdir(parents=True, exist_ok=True)
    archive = destination/'versions'/f"v{version:06d}-{digest(raw)}.json"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        require(archive.read_text(encoding='utf-8') == raw, 'immutable_archive_conflict')
    else:
        archive.write_text(raw, encoding='utf-8')
    (destination/'current.json').write_text(raw, encoding='utf-8')
    return {'source_version': version, 'entry_count': len(bundle['entries']),
            'workbook_sha256': bundle['source']['sha256'], 'document_sha256': digest(raw),
            'archive': str(archive)}

def read_bundle(path, now=None, require_fresh=True):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES, 'invalid_bundle_file')
    raw = path.read_text(encoding='utf-8')
    bundle = validate_bundle(raw, now=now, require_fresh=require_fresh)
    archive = path.parent/'versions'/f"v{bundle['source']['version']:06d}-{digest(raw)}.json"
    require(archive.is_file() and not archive.is_symlink() and not archive.parent.is_symlink(), 'immutable_archive_missing')
    require(archive.read_bytes() == raw.encode('utf-8'), 'immutable_archive_mismatch')
    return raw, bundle

def compare_snapshot(bundle, snapshot):
    require(snapshot['database'] == DATABASE and snapshot['neon_branch_id'] == BRANCH_ID, 'wrong_database_connection')
    incoming = {x['entry_key']:x for x in bundle['entries']}
    old = snapshot['entries']
    require(snapshot['entry_count'] == len(old) and len(old) >= 93, 'unexpected_live_count')
    for entry in old:
        current = incoming.get(entry['entry_key'])
        require(current is not None, 'existing_entry_removed')
        require(current['content_hash'] == entry['content_hash'] and current['payload'] == entry['payload'], 'existing_entry_changed')
    require(snapshot['offer_count'] == len(snapshot['offers']) and snapshot['offer_count'] > 0, 'unexpected_offer_count')
    for offer in snapshot['offers']:
        source = incoming.get(offer['entry_key'])
        mapping = strict_json(offer['payload'])
        require(source is not None and mapping.get('entry_hash') == source['content_hash'], 'mapping_source_conflict')
    old_source = snapshot.get('source')
    if old_source:
        require(old_source['batch_id'] == snapshot['active_batch'], 'active_pointer_left_sync_chain')
        require(old_source['offer_fingerprint'] == snapshot['offer_fingerprint'], 'live_offer_fingerprint_changed')
        require(old_source['entry_fingerprint'] == snapshot['entry_fingerprint'], 'live_entry_fingerprint_changed')
        require(bundle['source']['version'] >= old_source['version'], 'source_version_rollback')
        if bundle['source']['version'] == old_source['version']:
            require(bundle['source']['sha256'] == old_source['sha256'] and len(incoming) == len(old), 'source_version_conflict')
    return len(incoming)-len(old)

def connection(url):
    # Never print connection strings, parsed credentials, libpq exception details or SQL data.
    import psycopg
    checks = {}
    try:
        parts = urlsplit(url)
        checks = {
            'plain_url': url == url.strip() and not any(c.isspace() for c in url),
            'scheme': parts.scheme in ('postgres', 'postgresql'),
            'restricted_role': unquote(parts.username or '') == IMPORT_ROLE,
            'password_present': bool(parts.password),
            'neon_hostname': bool(re.fullmatch(r'ep-[a-z0-9-]+\.[a-z0-9.-]+\.neon\.tech', parts.hostname or '')),
            'port': parts.port in (None, 5432),
            'database': parts.path == '/' + DATABASE,
            'no_fragment': not parts.fragment,
        }
        try:
            query = dict(parse_qsl(parts.query, strict_parsing=True))
            checks['query_format'] = True
            checks['allowed_query_parameters'] = set(query) <= {'sslmode', 'channel_binding'}
        except ValueError:
            checks['query_format'] = False
    except ValueError:
        checks['url_parse'] = False
    if not all(checks.values()):
        error = ValidationError('restricted_neon_connection_required')
        error.failed_url_checks = [name for name, passed in checks.items() if not passed]
        raise error
    return psycopg.connect(url, sslmode='verify-full', sslrootcert='/etc/ssl/certs/ca-certificates.crt',
                           channel_binding='require', connect_timeout=15, prepare_threshold=None)

def sync(path, apply=False, expected_active=None):
    raw, bundle = read_bundle(path, require_fresh=False)
    require(bool(os.environ.get('SELFPAY_DIRECTORY_DATABASE_URL')), 'directory_secret_missing')
    with connection(os.environ['SELFPAY_DIRECTORY_DATABASE_URL']) as db:
        # Transaction-local settings work through pooled connections without
        # sending unsupported startup options or leaking state to another client.
        db.execute("SET LOCAL search_path = pg_catalog")
        db.execute("SET LOCAL statement_timeout = '60000ms'")
        db.execute("SET LOCAL lock_timeout = '10000ms'")
        require(db.execute('SELECT current_user').fetchone()[0] == IMPORT_ROLE, 'wrong_database_role')
        before = db.execute('SELECT selfpay_directory_sync.status()').fetchone()[0]
        added = compare_snapshot(bundle, before)
        if expected_active is not None:
            require(before['active_batch'] == expected_active, 'active_batch_conflict')
        # Old unchanged exports can be checked without mutations, but stale new input never applies.
        old_source = before.get('source')
        if (old_source and old_source['version'] == bundle['source']['version']
                and old_source['sha256'] == bundle['source']['sha256'] and added == 0):
            return {'unchanged': True, 'verified': True, 'active_batch': before['active_batch'],
                    'entry_count': before['entry_count'], 'offer_count': before['offer_count'],
                    'source_version': old_source['version'], 'applied': False}
        validate_bundle(raw)
        result = db.execute('SELECT selfpay_directory_sync.apply_bundle(%s,%s,%s)',
                            (raw, before['active_batch'], not apply)).fetchone()[0]
        after = db.execute('SELECT selfpay_directory_sync.status()').fetchone()[0]
        if apply:
            require(after['active_batch'] == result['active_batch'], 'publication_not_verified')
            require(compare_snapshot(bundle, after) == 0, 'published_entries_mismatch')
            require(after['offers'] == before['offers'], 'published_offers_changed')
            require(after['source']['version'] == bundle['source']['version']
                    and after['source']['sha256'] == bundle['source']['sha256'], 'source_ledger_mismatch')
        else:
            require(after == before, 'dry_run_mutated_state')
        return {**result, 'verified': True}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    exp = sub.add_parser('export'); exp.add_argument('workbook', type=Path)
    exp.add_argument('--library-version', type=int, required=True)
    exp.add_argument('--output', type=Path, default=Path('directory'))
    val = sub.add_parser('validate'); val.add_argument('bundle', type=Path)
    val.add_argument('--allow-old-export', action='store_true')
    run = sub.add_parser('sync'); run.add_argument('bundle', type=Path)
    run.add_argument('--apply', action='store_true'); run.add_argument('--expected-active')
    args = parser.parse_args()
    try:
        if args.action == 'export':
            result = export_bundle(args.workbook, args.library_version, args.output)
        elif args.action == 'validate':
            raw, bundle = read_bundle(args.bundle, require_fresh=not args.allow_old_export)
            result = {'valid': True, 'entry_count': len(bundle['entries']),
                      'source_version': bundle['source']['version'], 'document_sha256': digest(raw)}
        else:
            result = sync(args.bundle, args.apply, args.expected_active)
        print(json.dumps(result, sort_keys=True))
    except ValidationError as exc:
        result = {'ok': False, 'error': str(exc)}
        if hasattr(exc, 'failed_url_checks'):
            result['failed_url_checks'] = exc.failed_url_checks
        print(json.dumps(result), file=sys.stderr)
        return 1
    except Exception as exc:
        # Never log raw exception messages, credentials, SQL values or URLs.
        frames = []
        tb = exc.__traceback__
        while tb is not None:
            frame = tb.tb_frame
            if Path(frame.f_code.co_filename).name == 'directory_sync.py':
                frames.append({'function': frame.f_code.co_name, 'line': tb.tb_lineno})
            tb = tb.tb_next
        message = str(exc).lower()
        category = 'unclassified'
        patterns = (
            ('authentication', ('password authentication failed',)),
            ('dns', ('could not translate host name', 'name or service not known')),
            ('tls_certificate', ('certificate verify failed', 'root certificate file')),
            ('channel_binding', ('channel binding',)),
            ('connection_timeout', ('connection timeout', 'timeout expired')),
            ('connection_refused', ('connection refused',)),
            ('connection_option', ('unsupported startup parameter', 'invalid connection option')),
        )
        for label, phrases in patterns:
            if any(phrase in message for phrase in phrases):
                category = label
                break
        print(json.dumps({
            'ok': False, 'error': database_guard_error(exc) or 'sync_failed',
            'exception_type': type(exc).__name__,
            'sqlstate': getattr(exc, 'sqlstate', None),
            'category': category, 'python_locations': frames,
        }), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
