"""Offline security/regression tests for the unattended public-directory importer.

Fixtures contain only the 93 reviewed public provider rows, the bundle's required
provenance, and 13 existing public offers. No live database or credential is read.
All clocks are fixed so CI does not expire when the reviewed fixture gets older.
"""
import copy
import datetime as dt
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from contextlib import redirect_stderr, redirect_stdout

import directory_sync as sync

FIXTURES = Path(__file__).parent / 'tests' / 'fixtures'
NOW = dt.datetime(2026, 10, 7, 12, 0, tzinfo=dt.timezone.utc)
WORKBOOK_SHA = 'e60778bb503442e40ce035fdf70958db65ca1d710ce0279b06c2bcea8bd42a96'
# Independently calculated from the pre-existing canonical legacy normalization.
LEGACY_ENTRY_SHA = '302c09e43c151115a33c2caf050d16340ebe55834d92bfe2394087cb4f4774e2'
ACTIVE = '25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f'
# Synthetic credential only; never connect. The driver is mocked in every test.
SYNTHETIC_URL = ('postgresql://selfpay_directory_importer:synthetic-unit-test-value'
                 '@ep-offline-unit-test.us-east-2.aws.neon.tech/neondb')


def fixture():
    return json.loads((FIXTURES / 'directory-sync-v7.json').read_text(encoding='utf-8'))


def offers_fixture():
    return json.loads((FIXTURES / 'directory-public-offers.json').read_text(encoding='utf-8'))


def normalized(entry):
    content = sync.canonical({k: v for k, v in entry.items() if k != 'row'})
    return {'entry_key': sync.digest(sync.canonical(entry['name'])),
            'content_hash': sync.digest(content), 'payload': sync.canonical(entry),
            'content': content}


def edit_entry(bundle, index=0, **changes):
    row = json.loads(bundle['entries'][index]['payload'])
    row.update(changes)
    bundle['entries'][index] = normalized(row)
    bundle['entries'].sort(key=lambda item: item['entry_key'])


def added_bundle():
    bundle = fixture()
    bundle['source']['version'] = 8
    bundle['source']['sha256'] = 'a' * 64
    row = json.loads(bundle['entries'][0]['payload'])
    row.update(name='Synthetic unit-test public provider', row='98')
    bundle['entries'].append(normalized(row))
    bundle['entries'].sort(key=lambda item: item['entry_key'])
    return bundle


def snapshot(bundle=None, source=True):
    bundle = bundle or fixture()
    fingerprint = sync.digest(sync.canonical(offers_fixture()))
    entries = [{k: v for k, v in row.items() if k != 'content'} for row in bundle['entries']]
    entry_fingerprint = sync.digest(sync.canonical(entries))
    return {'database': sync.DATABASE, 'neon_branch_id': sync.BRANCH_ID,
            'active_batch': ACTIVE, 'entry_count': len(bundle['entries']), 'offer_count': 13,
            'offer_fingerprint': fingerprint,
            'entry_fingerprint': entry_fingerprint,
            'entries': entries,
            'offers': offers_fixture(),
            'source': {**copy.deepcopy(bundle['source']), 'batch_id': ACTIVE,
                       'offer_fingerprint': fingerprint,
                       'entry_fingerprint': entry_fingerprint} if source else None}


def write_bundle(directory, bundle):
    directory = Path(directory)
    raw = sync.canonical(bundle) + '\n'
    path = directory / 'current.json'
    path.write_text(raw, encoding='utf-8')
    versions = directory / 'versions'
    versions.mkdir(exist_ok=True)
    (versions / f"v{bundle['source']['version']:06d}-{sync.digest(raw)}.json").write_text(raw, encoding='utf-8')
    return path


class FakeDatabase:
    """Records every statement, never creates a socket or accesses application data."""
    def __init__(self, before=None, after=None, result=None, role=sync.IMPORT_ROLE):
        self.before = before if before is not None else snapshot()
        self.after = after if after is not None else copy.deepcopy(self.before)
        self.result = result if result is not None else {'dry_run': True, 'active_batch': ACTIVE}
        self.role = role
        self.queries = []
        self.status_calls = 0
        self.error = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.error = exc

    def execute(self, statement, parameters=None):
        self.queries.append((statement, parameters))
        if statement == 'SELECT current_user':
            value = self.role
        elif statement == 'SELECT selfpay_directory_sync.status()':
            value = self.before if self.status_calls == 0 else self.after
            self.status_calls += 1
        elif statement == 'SELECT selfpay_directory_sync.apply_bundle(%s,%s,%s)':
            value = self.result
        else:
            raise AssertionError('Unexpected SQL: ' + statement)
        return SimpleNamespace(fetchone=lambda: (copy.deepcopy(value),))


class BundleValidationTests(unittest.TestCase):
    def assert_invalid(self, bundle, code, **kwargs):
        raw = bundle if isinstance(bundle, str) else sync.canonical(bundle)
        with self.assertRaisesRegex(sync.ValidationError, '^' + code + '$'):
            sync.validate_bundle(raw, now=NOW, **kwargs)

    def test_reviewed_v7_exact_legacy_93_entries(self):
        bundle = fixture()
        self.assertEqual(sync.validate_bundle(sync.canonical(bundle), now=NOW), bundle)
        self.assertEqual(len(bundle['entries']), 93)
        self.assertEqual(bundle['source']['sha256'], WORKBOOK_SHA)
        self.assertEqual(bundle['source']['version'], 7)
        legacy = [{k: v for k, v in row.items() if k != 'content'} for row in bundle['entries']]
        self.assertEqual(sync.digest(sync.canonical(legacy)), LEGACY_ENTRY_SHA)
        self.assertEqual({json.loads(row['payload'])['row'] for row in legacy},
                         {str(number) for number in range(5, 98)})

    def test_fixture_has_public_directory_fields_only(self):
        bundle = fixture()
        self.assertEqual(set(bundle), {'schema_version', 'source', 'target', 'entries'})
        for row in bundle['entries']:
            self.assertEqual(set(json.loads(row['payload'])), set(sync.FIELDS))
        for offer in offers_fixture():
            self.assertEqual(set(offer), {'id', 'entry_key', 'amount_cents', 'max_cents', 'price_type', 'payload'})
        self.assertEqual(len(offers_fixture()), 13)

    def test_unknown_fields_at_every_schema_boundary_fail(self):
        for path, code in [((), 'unexpected_bundle_fields'), (('source',), 'unexpected_source_fields'),
                           (('target',), 'wrong_target'), (('entries', 0), 'unexpected_normalized_fields')]:
            with self.subTest(path=path):
                bundle = fixture()
                obj = bundle
                for key in path:
                    obj = obj[key]
                obj['password'] = 'SYNTHETIC-PRIVATE-MARKER'
                self.assert_invalid(bundle, code)
        bundle = fixture()
        edit_entry(bundle, patient='SYNTHETIC-PRIVATE-MARKER')
        self.assert_invalid(bundle, 'unexpected_entry_fields')

    def test_schema_types_and_versions_are_strict(self):
        for value in [True, 1.0, '1', 2, None]:
            bundle = fixture(); bundle['schema_version'] = value
            with self.subTest(value=value):
                self.assert_invalid(bundle, 'unsupported_schema')
        for value in [True, 7.0, '7', 6, None]:
            bundle = fixture(); bundle['source']['version'] = value
            with self.subTest(version=value):
                self.assert_invalid(bundle, 'source_version_too_old')

    def test_source_identity_hash_and_target_are_pinned(self):
        for field, value, code in [('library_file_id', 'wrong-file', 'wrong_library_source'),
                                   ('sha256', 'G' * 64, 'invalid_workbook_hash'),
                                   ('sha256', None, 'invalid_workbook_hash')]:
            bundle = fixture(); bundle['source'][field] = value
            with self.subTest(field=field, value=value):
                self.assert_invalid(bundle, code)
        for field, value in [('database', 'other'), ('neon_branch_id', 'other')]:
            bundle = fixture(); bundle['target'][field] = value
            self.assert_invalid(bundle, 'wrong_target')

    def test_duplicate_keys_invalid_numbers_and_invalid_json_fail(self):
        for raw, code in [('{"schema_version":1,"schema_version":1}', 'duplicate_json_key'),
                          ('{"nested":{"x":1,"x":2}}', 'duplicate_json_key'),
                          ('NaN', 'invalid_json_number'), ('Infinity', 'invalid_json_number'),
                          ('-Infinity', 'invalid_json_number'), ('{', 'invalid_json')]:
            with self.subTest(raw=raw):
                self.assert_invalid(raw, code)
        bundle = fixture(); bundle['entries'][0]['payload'] = '{"name":"one","name":"two"}'
        self.assert_invalid(bundle, 'duplicate_json_key')

    def test_top_level_shape_and_size_are_bounded(self):
        for raw in ['[]', 'null', '1', '"text"']:
            self.assert_invalid(raw, 'unexpected_bundle_fields')
        self.assert_invalid(' ' * (sync.MAX_BYTES + 1), 'bundle_size_limit')
        # Size uses UTF-8 bytes, not character count.
        self.assert_invalid('é' * (sync.MAX_BYTES // 2 + 1), 'bundle_size_limit')
        for entries in [[], fixture()['entries'][:92], {}, None, [None] * 10001]:
            bundle = fixture(); bundle['entries'] = entries
            self.assert_invalid(bundle, 'invalid_entry_count')

    def test_export_timestamp_format_and_freshness_boundaries(self):
        for value in ['2026-10-07', '2026-10-07T12:00:00+00:00', '2026-99-07T12:00:00Z', None]:
            bundle = fixture(); bundle['source']['exported_at'] = value
            self.assert_invalid(bundle, 'invalid_export_timestamp')
        for offset, error in [(dt.timedelta(hours=-48), None),
                              (dt.timedelta(hours=-48, seconds=-1), 'stale_export'),
                              (dt.timedelta(minutes=5), None),
                              (dt.timedelta(minutes=5, seconds=1), 'future_export')]:
            bundle = fixture()
            bundle['source']['exported_at'] = (NOW + offset).strftime('%Y-%m-%dT%H:%M:%SZ')
            if error:
                self.assert_invalid(bundle, error)
            else:
                sync.validate_bundle(sync.canonical(bundle), now=NOW)
        bundle = fixture(); bundle['source']['exported_at'] = '2026-10-01T12:00:00Z'
        sync.validate_bundle(sync.canonical(bundle), now=NOW, require_fresh=False)
        bundle['source']['exported_at'] = '2026-10-08T12:00:00Z'
        self.assert_invalid(bundle, 'future_export', require_fresh=False)

    def test_invalid_entry_text_name_row_and_checked_date(self):
        cases = [('notes', None, 'invalid_entry_text'), ('notes', 'x' * 12001, 'invalid_entry_text'),
                 ('notes', 'null\x00byte', 'invalid_entry_text'), ('name', '', 'invalid_entry_name'),
                 ('name', ' trailing ', 'invalid_entry_name'), ('name', 'x' * 301, 'invalid_entry_name'),
                 ('row', '-1', 'invalid_source_row'), ('row', '1000000', 'invalid_source_row'),
                 ('checked', '2026-02-30', 'invalid_checked_date'), ('checked', '10/07/2026', 'invalid_checked_date'),
                 ('checked', '2026-10-08', 'future_source_check')]
        for field, value, code in cases:
            with self.subTest(field=field, value=str(value)[:30]):
                bundle = fixture(); edit_entry(bundle, **{field: value})
                self.assert_invalid(bundle, code)

    def test_source_and_additional_urls_reject_unsafe_protocols_and_credentials(self):
        urls = ['http://example.com', 'javascript:alert(1)', 'file:///tmp/data', '//example.com',
                'https://user:password@example.com/', 'https://example.com:8443/',
                'https://example.com/\nsecret', 'https://localhost/', 'https://[invalid/']
        for value in urls:
            with self.subTest(url=value):
                bundle = fixture(); edit_entry(bundle, source=value)
                self.assert_invalid(bundle, 'invalid_public_source_url')
        for value in ['http://example.com/', 'https://user:password@example.com/', 'https://example.com:123/']:
            bundle = fixture(); edit_entry(bundle, additional='Reference: ' + value)
            self.assert_invalid(bundle, 'invalid_additional_url')

    def test_public_urls_reject_nonpublic_ip_literals_and_local_names(self):
        urls = ['https://127.0.0.1/', 'https://10.0.0.1/', 'https://192.168.1.10/',
                'https://172.16.0.1/', 'https://169.254.169.254/', 'https://0.0.0.0/',
                'https://[::1]/', 'https://[fc00::1]/', 'https://[fe80::1]/',
                'https://[::ffff:127.0.0.1]/', 'https://provider.local/',
                'https://provider.internal/', 'https://provider.localhost/',
                'https://127.0.0.1./', 'https://127.1/', 'https://0177.0.0.1/',
                'https://0x7f.0.0.1/', 'https://localhost./']
        for value in urls:
            with self.subTest(url=value):
                self.assertFalse(sync.public_url(value))
                bundle = fixture(); edit_entry(bundle, source=value)
                self.assert_invalid(bundle, 'invalid_public_source_url')
                bundle = fixture(); edit_entry(bundle, additional='Reference: ' + value)
                self.assert_invalid(bundle, 'invalid_additional_url')
        self.assertTrue(sync.public_url('https://example.com/public-provider'))

    def test_payload_hash_key_canonical_content_and_order_are_verified(self):
        cases = [('payload', json.dumps(json.loads(fixture()['entries'][0]['payload']), indent=2), 'noncanonical_payload'),
                 ('content', '{}', 'content_payload_mismatch'), ('content_hash', '0' * 64, 'entry_hash_mismatch'),
                 ('entry_key', '0' * 64, 'entry_key_mismatch'), ('content', 1, 'invalid_normalized_text')]
        for field, value, code in cases:
            bundle = fixture(); bundle['entries'][0][field] = value
            with self.subTest(field=field, code=code):
                self.assert_invalid(bundle, code)
        bundle = fixture(); bundle['entries'].reverse()
        self.assert_invalid(bundle, 'unsorted_entries')

    def test_duplicate_keys_and_casefolded_names_fail(self):
        bundle = fixture(); bundle['entries'].insert(0, copy.deepcopy(bundle['entries'][0]))
        self.assert_invalid(bundle, 'duplicate_entry')
        bundle = fixture(); row = json.loads(bundle['entries'][0]['payload'])
        row['name'] = row['name'].upper(); row['row'] = '98'
        bundle['entries'].append(normalized(row)); bundle['entries'].sort(key=lambda item: item['entry_key'])
        self.assert_invalid(bundle, 'duplicate_entry')

    def test_injected_text_stays_inert_public_data(self):
        payload = "'); DROP TABLE public.members; -- <script>alert(1)</script> $(touch /tmp/never)\n::error::injected"
        bundle = added_bundle()
        index = next(i for i, item in enumerate(bundle['entries']) if json.loads(item['payload'])['row'] == '98')
        edit_entry(bundle, index, notes=payload)
        result = sync.validate_bundle(sync.canonical(bundle), now=NOW)
        added = next(json.loads(item['payload']) for item in result['entries'] if json.loads(item['payload'])['row'] == '98')
        self.assertEqual(added['notes'], payload)


class WorkbookExportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.path = self.root / 'public.xlsx'
        import openpyxl
        self.wb = openpyxl.Workbook(); self.wb.active.title = 'Directory'
        self.sheet = self.wb['Directory']
        self.sheet.append(['Public provider directory'])
        self.sheet.append([])
        self.sheet.append(sync.HEADERS)
        for item in fixture()['entries']:
            row = json.loads(item['payload'])
            for column, field in enumerate(sync.FIELDS[1:], 1):
                self.sheet.cell(int(row['row']) + 2, column, row[field])
        self.wb.save(self.path)
        self.addCleanup(self.wb.close)

    def test_export_matches_legacy_payloads_and_only_reads_directory_sheet(self):
        private = self.wb.create_sheet('Unrelated private sheet')
        private.append(['SYNTHETIC-PRIVATE-MARKER', 'Do not export'])
        self.wb.save(self.path)
        bundle = sync.make_bundle(self.path, 7, now=NOW)
        self.assertEqual(bundle['entries'], fixture()['entries'])
        self.assertNotIn('SYNTHETIC-PRIVATE-MARKER', sync.canonical(bundle))

    def test_export_archive_round_trip_is_idempotent(self):
        output = self.root / 'directory'
        first = sync.export_bundle(self.path, 7, output, now=NOW)
        second = sync.export_bundle(self.path, 7, output, now=NOW)
        self.assertEqual(first, second)
        self.assertEqual(len(list((output / 'versions').glob('*.json'))), 1)
        raw, bundle = sync.read_bundle(output / 'current.json', now=NOW)
        self.assertEqual(bundle['entries'], fixture()['entries'])
        self.assertEqual(sync.digest(raw), first['document_sha256'])
        self.assertEqual(bundle['source']['sha256'], __import__('hashlib').sha256(self.path.read_bytes()).hexdigest())

    def test_existing_immutable_archive_cannot_be_overwritten(self):
        output = self.root / 'directory'
        first = sync.export_bundle(self.path, 7, output, now=NOW)
        archive = Path(first['archive']); archive.write_text('tampered')
        with self.assertRaisesRegex(sync.ValidationError, '^immutable_archive_conflict$'):
            sync.export_bundle(self.path, 7, output, now=NOW)
        self.assertEqual(archive.read_text(), 'tampered')

    def test_formula_in_any_public_column_is_rejected(self):
        for column in [1, 6, 11, 13]:
            original = self.sheet.cell(7, column).value
            self.sheet.cell(7, column, '=HYPERLINK("https://example.com","injected")')
            self.wb.save(self.path)
            with self.subTest(column=column), self.assertRaisesRegex(sync.ValidationError, '^formula_in_directory$'):
                sync.make_bundle(self.path, 7, now=NOW)
            self.sheet.cell(7, column, original)

    def test_quoted_formula_like_plaintext_is_preserved(self):
        value = '"=HYPERLINK(\"https://example.com\",\"provider notes\")"'
        self.sheet.cell(7, 10, value); self.wb.save(self.path)
        bundle = sync.make_bundle(self.path, 8, now=NOW)
        row = next(json.loads(item['payload']) for item in bundle['entries']
                   if json.loads(item['payload'])['row'] == '5')
        self.assertEqual(row['notes'], value)

    def test_unknown_nonempty_columns_and_wrong_headers_fail(self):
        self.sheet.cell(7, 14, 'private marker'); self.wb.save(self.path)
        with self.assertRaisesRegex(sync.ValidationError, '^unexpected_directory_columns$'):
            sync.make_bundle(self.path, 7, now=NOW)
        self.sheet.cell(7, 14).value = None
        self.sheet.cell(3, 2, 'Unknown header'); self.wb.save(self.path)
        with self.assertRaisesRegex(sync.ValidationError, '^directory_header_mismatch$'):
            sync.make_bundle(self.path, 7, now=NOW)

    def test_workbook_structure_and_file_type_fail_closed(self):
        for path in [self.root / 'missing.xlsx', self.root / 'public.csv']:
            with self.assertRaisesRegex(sync.ValidationError, '^xlsx_required$'):
                sync.make_bundle(path, 7, now=NOW)
        self.sheet.title = 'Other'; self.wb.save(self.path)
        with self.assertRaisesRegex(sync.ValidationError, '^directory_sheet_missing$'):
            sync.make_bundle(self.path, 7, now=NOW)


class BundleFileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.path = write_bundle(self.root, fixture())
        self.archive = next((self.root / 'versions').glob('*.json'))

    def test_archive_must_exist_and_match_exact_bytes(self):
        self.archive.unlink()
        with self.assertRaisesRegex(sync.ValidationError, '^immutable_archive_missing$'):
            sync.read_bundle(self.path, now=NOW)
        self.archive.write_text('{}')
        with self.assertRaisesRegex(sync.ValidationError, '^immutable_archive_mismatch$'):
            sync.read_bundle(self.path, now=NOW)

    def test_missing_and_oversized_files_fail_before_parsing(self):
        with self.assertRaisesRegex(sync.ValidationError, '^invalid_bundle_file$'):
            sync.read_bundle(self.root / 'missing.json', now=NOW)
        self.path.write_bytes(b' ' * (sync.MAX_BYTES + 1))
        with self.assertRaisesRegex(sync.ValidationError, '^invalid_bundle_file$'):
            sync.read_bundle(self.path, now=NOW)

    def test_bundle_archive_and_archive_directory_symlinks_fail(self):
        original = self.path.read_bytes()
        target = self.root / 'target.json'; target.write_bytes(original)
        self.path.unlink(); self.path.symlink_to(target)
        with self.assertRaisesRegex(sync.ValidationError, '^invalid_bundle_file$'):
            sync.read_bundle(self.path, now=NOW)
        self.path.unlink(); self.path.write_bytes(original)
        self.archive.unlink(); self.archive.symlink_to(target)
        with self.assertRaisesRegex(sync.ValidationError, '^immutable_archive_missing$'):
            sync.read_bundle(self.path, now=NOW)
        self.archive.unlink(); self.archive.parent.rmdir()
        other = self.root / 'alternate'; other.mkdir(); (other / self.archive.name).write_bytes(original)
        (self.root / 'versions').symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(sync.ValidationError, '^immutable_archive_missing$'):
            sync.read_bundle(self.path, now=NOW)


class SnapshotComparisonTests(unittest.TestCase):
    def test_exact_93_entries_and_13_offers_preserved(self):
        self.assertEqual(sync.compare_snapshot(fixture(), snapshot()), 0)
        self.assertEqual(sync.compare_snapshot(added_bundle(), snapshot()), 1)
        self.assertEqual(sync.compare_snapshot(fixture(), snapshot(source=False)), 0)

    def test_removed_or_changed_existing_entries_blocked(self):
        bundle = fixture(); bundle['entries'].pop()
        with self.assertRaisesRegex(sync.ValidationError, '^existing_entry_removed$'):
            sync.compare_snapshot(bundle, snapshot())
        for field, value in [('mri', '$1'), ('row', '999'), ('name', 'Renamed')]:
            bundle = fixture(); edit_entry(bundle, **{field: value})
            with self.subTest(field=field), self.assertRaises(sync.ValidationError):
                sync.compare_snapshot(bundle, snapshot())

    def test_mapping_conflict_or_missing_source_blocks(self):
        for missing in [False, True]:
            before = snapshot()
            if missing:
                before['offers'][0]['entry_key'] = '0' * 64
            else:
                mapping = json.loads(before['offers'][0]['payload']); mapping['entry_hash'] = '0' * 64
                before['offers'][0]['payload'] = sync.canonical(mapping)
            with self.assertRaisesRegex(sync.ValidationError, '^mapping_source_conflict$'):
                sync.compare_snapshot(fixture(), before)

    def test_wrong_target_counts_and_empty_offers_block(self):
        for field, value, code in [('database', 'wrong', 'wrong_database_connection'),
                                   ('neon_branch_id', 'wrong', 'wrong_database_connection'),
                                   ('entry_count', 92, 'unexpected_live_count'),
                                   ('offer_count', 12, 'unexpected_offer_count')]:
            before = snapshot(); before[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(sync.ValidationError, '^' + code + '$'):
                sync.compare_snapshot(fixture(), before)
        before = snapshot(); before['offers'] = []; before['offer_count'] = 0
        with self.assertRaisesRegex(sync.ValidationError, '^unexpected_offer_count$'):
            sync.compare_snapshot(fixture(), before)

    def test_source_version_rollback_and_same_version_conflicts_block(self):
        before = snapshot(); before['source']['version'] = 8
        with self.assertRaisesRegex(sync.ValidationError, '^source_version_rollback$'):
            sync.compare_snapshot(fixture(), before)
        bundle = fixture(); bundle['source']['sha256'] = 'a' * 64
        with self.assertRaisesRegex(sync.ValidationError, '^source_version_conflict$'):
            sync.compare_snapshot(bundle, snapshot())
        bundle = added_bundle(); bundle['source'] = fixture()['source']
        with self.assertRaisesRegex(sync.ValidationError, '^source_version_conflict$'):
            sync.compare_snapshot(bundle, snapshot())

    def test_active_pointer_must_remain_in_sync_ledger_chain(self):
        before = snapshot(); before['source']['batch_id'] = 'different-batch'
        with self.assertRaisesRegex(sync.ValidationError, '^active_pointer_left_sync_chain$'):
            sync.compare_snapshot(fixture(), before)

    def test_offer_fingerprint_must_match_protected_ledger(self):
        before = snapshot(); before['offer_fingerprint'] = '0' * 64
        with self.assertRaisesRegex(sync.ValidationError, '^live_offer_fingerprint_changed$'):
            sync.compare_snapshot(fixture(), before)

    def test_entry_fingerprint_must_match_protected_ledger(self):
        before = snapshot(); before['entry_fingerprint'] = '0' * 64
        with self.assertRaisesRegex(sync.ValidationError, '^live_entry_fingerprint_changed$'):
            sync.compare_snapshot(fixture(), before)


class SyncBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.environment = patch.dict(os.environ, {'SELFPAY_DIRECTORY_DATABASE_URL': SYNTHETIC_URL}, clear=True)
        self.environment.start(); self.addCleanup(self.environment.stop)
        self.clock = patch.object(sync, 'utcnow', return_value=NOW)
        self.clock.start(); self.addCleanup(self.clock.stop)

    def run_sync(self, bundle=None, db=None, **kwargs):
        path = write_bundle(self.root, bundle or fixture()); db = db or FakeDatabase()
        with patch.object(sync, 'connection', return_value=db) as connect:
            result = sync.sync(path, **kwargs)
        connect.assert_called_once_with(SYNTHETIC_URL)
        return result, db

    def test_unchanged_old_export_is_verified_without_apply(self):
        bundle = fixture(); bundle['source']['exported_at'] = '2026-10-01T12:00:00Z'
        for apply in [False, True]:
            result, db = self.run_sync(bundle, apply=apply)
            self.assertTrue(result['verified']); self.assertTrue(result['unchanged']); self.assertFalse(result['applied'])
            self.assertEqual(len(db.queries), 2)
            self.assertEqual((result['entry_count'], result['offer_count']), (93, 13))

    def test_stale_new_input_is_blocked_before_any_apply(self):
        for bundle in [added_bundle(), fixture()]:
            bundle['source']['version'] = 8; bundle['source']['exported_at'] = '2026-10-01T12:00:00Z'
            db = FakeDatabase()
            with self.assertRaisesRegex(sync.ValidationError, '^stale_export$'):
                self.run_sync(bundle, db=db, apply=True)
            self.assertEqual(len(db.queries), 2)

    def test_dry_run_uses_parameters_and_does_not_mutate_snapshot(self):
        bundle = added_bundle(); before = snapshot(); db = FakeDatabase(before=before)
        result, db = self.run_sync(bundle, db=db)
        self.assertTrue(result['verified'])
        statement, parameters = db.queries[2]
        self.assertEqual(statement, 'SELECT selfpay_directory_sync.apply_bundle(%s,%s,%s)')
        self.assertEqual(parameters, (sync.canonical(bundle) + '\n', ACTIVE, True))
        self.assertEqual(db.before, db.after)
        self.assertTrue(all('public.' not in statement for statement, _ in db.queries))

    def test_apply_verifies_entries_offers_publication_and_source_ledger(self):
        bundle = added_bundle(); after = snapshot(bundle); after['active_batch'] = 'synthetic-new-batch'
        after['source']['batch_id'] = after['active_batch']
        db = FakeDatabase(after=after, result={'active_batch': after['active_batch'], 'added': 1})
        result, db = self.run_sync(bundle, db=db, apply=True, expected_active=ACTIVE)
        self.assertTrue(result['verified']); self.assertEqual(result['added'], 1)
        self.assertFalse(db.queries[2][1][2])
        self.assertEqual(len(db.queries), 4)

    def test_bootstrap_source_is_verified_without_changing_public_entries(self):
        before = snapshot(source=False)
        db = FakeDatabase(before=before, after=snapshot(), result={'active_batch': ACTIVE, 'bootstrap': True})
        result, _ = self.run_sync(db=db, apply=True)
        self.assertTrue(result['verified']); self.assertTrue(result['bootstrap'])

    def test_active_batch_and_database_role_fail_before_apply(self):
        for db, options, code in [(FakeDatabase(), {'expected_active': 'stale-batch'}, 'active_batch_conflict'),
                                  (FakeDatabase(role='owner'), {}, 'wrong_database_role')]:
            with self.assertRaisesRegex(sync.ValidationError, '^' + code + '$'):
                self.run_sync(db=db, apply=True, **options)
            self.assertFalse(any('apply_bundle' in statement for statement, _ in db.queries))

    def test_unchanged_source_does_not_hide_active_pointer_or_catalog_drift(self):
        for field, value, code in [('active_batch', 'unexpected-batch', 'active_pointer_left_sync_chain'),
                                   ('offer_fingerprint', '0' * 64, 'live_offer_fingerprint_changed'),
                                   ('entry_fingerprint', '0' * 64, 'live_entry_fingerprint_changed')]:
            before = snapshot(); before[field] = value
            db = FakeDatabase(before=before)
            with self.subTest(field=field), self.assertRaisesRegex(sync.ValidationError, '^' + code + '$'):
                self.run_sync(db=db, apply=True)
            self.assertEqual(len(db.queries), 2)

    def test_future_new_export_rejected_before_connection(self):
        bundle = added_bundle(); bundle['source']['exported_at'] = '2026-10-08T12:00:00Z'
        path = write_bundle(self.root, bundle)
        with patch.object(sync, 'connection') as connect:
            with self.assertRaisesRegex(sync.ValidationError, '^future_export$'):
                sync.sync(path, apply=True)
        connect.assert_not_called()

    def test_dry_run_mutation_detected(self):
        after = snapshot(); after['active_batch'] = 'unexpected-change'
        db = FakeDatabase(after=after)
        with self.assertRaisesRegex(sync.ValidationError, '^dry_run_mutated_state$'):
            self.run_sync(added_bundle(), db=db)
        self.assertIsInstance(db.error, sync.ValidationError)

    def test_apply_postcondition_failures_abort_transaction(self):
        bundle = added_bundle()
        wrong_source = {**snapshot(bundle)['source'], 'version': 7}
        for field, value, code in [('active_batch', 'unexpected', 'publication_not_verified'),
                                   ('offers', [], 'unexpected_offer_count'),
                                   ('source', wrong_source, 'source_ledger_mismatch')]:
            after = snapshot(bundle); after[field] = value
            db = FakeDatabase(after=after, result={'active_batch': ACTIVE})
            with self.subTest(field=field), self.assertRaisesRegex(sync.ValidationError, '^' + code + '$'):
                self.run_sync(bundle, db=db, apply=True)
            self.assertIsInstance(db.error, sync.ValidationError)
        after = snapshot(bundle); after['offers'][0]['amount_cents'] += 1
        db = FakeDatabase(after=after, result={'active_batch': ACTIVE})
        with self.assertRaisesRegex(sync.ValidationError, '^published_offers_changed$'):
            self.run_sync(bundle, db=db, apply=True)

    def test_missing_dedicated_secret_does_not_use_generic_credentials(self):
        path = write_bundle(self.root, fixture())
        with patch.dict(os.environ, {'DATABASE_URL': SYNTHETIC_URL}, clear=True), patch.object(sync, 'connection') as connect:
            with self.assertRaisesRegex(sync.ValidationError, '^directory_secret_missing$'):
                sync.sync(path, apply=True)
        connect.assert_not_called()

    def test_invalid_local_bundle_never_opens_connection(self):
        bundle = fixture(); bundle['members'] = [{'email': 'synthetic@example.test'}]
        path = write_bundle(self.root, bundle)
        with patch.object(sync, 'connection') as connect:
            with self.assertRaisesRegex(sync.ValidationError, '^unexpected_bundle_fields$'):
                sync.sync(path, apply=True)
        connect.assert_not_called()

    def test_injection_is_passed_only_as_parameter_never_sql_or_shell(self):
        bundle = added_bundle()
        index = next(i for i, row in enumerate(bundle['entries']) if json.loads(row['payload'])['row'] == '98')
        injected = "'); DROP TABLE public.members; -- $(touch /tmp/never) <script>alert(1)</script>"
        edit_entry(bundle, index, notes=injected)
        _, db = self.run_sync(bundle)
        self.assertTrue(all(injected not in sql for sql, _ in db.queries))
        self.assertIn(injected, db.queries[2][1][0])


class CredentialsAndCliTests(unittest.TestCase):
    def test_connection_rejects_wrong_roles_hosts_databases_and_libpq_options(self):
        invalid = [SYNTHETIC_URL.replace('selfpay_directory_importer:', 'owner:'),
                   SYNTHETIC_URL.replace('/neondb', '/postgres'),
                   SYNTHETIC_URL.replace('.neon.tech', '.neon.tech.attacker.test'),
                   SYNTHETIC_URL.replace('ep-offline-unit-test.us-east-2.aws.neon.tech', '127.0.0.1'),
                   SYNTHETIC_URL + '?options=-c+search_path%3Dpublic', SYNTHETIC_URL + '#fragment',
                   SYNTHETIC_URL.replace('/neondb', ':6543/neondb'),
                   SYNTHETIC_URL.replace(':synthetic-unit-test-value@', '@'),
                   'host=localhost user=owner password=SYNTHETIC',
                   SYNTHETIC_URL + '?sslmode']
        driver = SimpleNamespace(connect=Mock())
        with patch.dict('sys.modules', {'psycopg': driver}):
            for url in invalid:
                with self.subTest(url=url), self.assertRaisesRegex(sync.ValidationError, '^restricted_neon_connection_required$'):
                    sync.connection(url)
        driver.connect.assert_not_called()

    def test_tls_role_and_fixed_safe_session_settings_are_enforced(self):
        driver = SimpleNamespace(connect=Mock(return_value='fake-connection'))
        url = SYNTHETIC_URL + '?sslmode=disable&channel_binding=disable'
        with patch.dict('sys.modules', {'psycopg': driver}):
            self.assertEqual(sync.connection(url), 'fake-connection')
        driver.connect.assert_called_once_with(url, sslmode='verify-full',
            sslrootcert='/etc/ssl/certs/ca-certificates.crt', channel_binding='require',
            connect_timeout=15, prepare_threshold=None,
            options='-c search_path=pg_catalog -c statement_timeout=60000 -c lock_timeout=10000')

    def invoke(self, argv, failure=None, result=None):
        out, err = io.StringIO(), io.StringIO()
        with patch('sys.argv', ['directory_sync.py', *argv]), patch.object(sync, 'sync', side_effect=failure, return_value=result), redirect_stdout(out), redirect_stderr(err):
            status = sync.main()
        return status, out.getvalue(), err.getvalue()

    def test_cli_errors_redact_dsn_provider_data_and_database_details(self):
        marker = 'SYNTHETIC-SECRET-AND-PROVIDER-MARKER'
        error = RuntimeError(SYNTHETIC_URL + '\n' + marker + ' ::error::injected')
        error.sqlstate = '42501'
        status, out, err = self.invoke(['sync', 'unused.json'], failure=error)
        self.assertEqual(status, 1); self.assertEqual(out, '')
        self.assertEqual(json.loads(err), {'ok': False, 'error': 'sync_failed', 'sqlstate': '42501'})
        self.assertNotIn(marker, err); self.assertNotIn(SYNTHETIC_URL, err)
        self.assertNotIn('Traceback', err)

    def test_cli_validation_errors_are_stable_codes_and_success_is_json(self):
        status, out, err = self.invoke(['sync', 'unused.json'], failure=sync.ValidationError('wrong_target'))
        self.assertEqual((status, out), (1, ''))
        self.assertEqual(json.loads(err), {'ok': False, 'error': 'wrong_target'})
        result = {'verified': True, 'entry_count': 93, 'offer_count': 13}
        status, out, err = self.invoke(['sync', 'unused.json'], result=result)
        self.assertEqual((status, err), (0, '')); self.assertEqual(json.loads(out), result)

    def test_cli_non_database_errors_are_also_redacted(self):
        error = OSError('Private filename, synthetic credential, and provider content must not appear')
        status, out, err = self.invoke(['sync', 'unused.json'], failure=error)
        self.assertEqual((status, out), (1, ''))
        self.assertEqual(json.loads(err), {'ok': False, 'error': 'sync_failed', 'sqlstate': None})

    def test_cli_apply_is_explicit_and_expected_active_is_forwarded(self):
        with patch('sys.argv', ['directory_sync.py', 'sync', 'data.json', '--apply', '--expected-active', ACTIVE]), patch.object(sync, 'sync', return_value={}) as run, redirect_stdout(io.StringIO()):
            self.assertEqual(sync.main(), 0)
        run.assert_called_once_with(Path('data.json'), True, ACTIVE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
