"""Boolean-only checks inside the same repeatable-read snapshot as pg_dump."""
from pathlib import Path


class NonSyntheticData(Exception):
    pass


def require_synthetic(cursor):
    cursor.execute((Path(__file__).parents[1] / 'sql' / 'backup-synthetic-check.sql').read_text())
    row = cursor.fetchone()
    if row is None or len(row) != 3 or any(value not in (False, 0) for value in row):
        raise NonSyntheticData()
