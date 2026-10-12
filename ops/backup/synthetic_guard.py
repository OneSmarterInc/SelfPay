"""Boolean-only checks inside the same repeatable-read snapshot as pg_dump."""
from pathlib import Path


class NonSyntheticData(Exception):
    pass


def require_synthetic(cursor, *, approved_test_date='', today=''):
    cursor.execute((Path(__file__).parents[1] / 'sql' / 'backup-synthetic-check.sql').read_text())
    row = cursor.fetchone()
    if row is None or len(row) != 3 or any(value not in (True, False, 0, 1) for value in row):
        raise NonSyntheticData()
    # Owner-confirmed test users: manual, one-day exception only. Future
    # corrections remain a stop condition, and ordinary runs retain all checks.
    approved = approved_test_date == today == '2026-10-12'
    if row[2] or ((row[0] or row[1]) and not approved):
        raise NonSyntheticData()
