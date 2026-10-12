"""Read one immutable, parentless backup from the approved private repository."""
import base64
from datetime import date
import os
from pathlib import Path
import re
import sys
import tempfile

from git_backup import BACKUP_REPOSITORY, git, verify_destination


def validate_source(day, commit):
    if date.fromisoformat(day).isoformat() != day or not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Use an exact backup date and full commit SHA')


def download(day, commit, output):
    validate_source(day, commit)
    verify_destination()
    auth = base64.b64encode(('x-access-token:' + os.environ['BACKUP_REPO_TOKEN']).encode()).decode()
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_CONFIG_COUNT='1',
               GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
               GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth)
    filename = f'database-{day}.sql'
    with tempfile.TemporaryDirectory(prefix='selfpay-restore-source-') as tmp:
        git(['init', '-q'], tmp)
        git(['fetch', '--no-tags', f'https://github.com/{BACKUP_REPOSITORY}.git',
             f'refs/heads/backup-{day}'], tmp, env)
        if git(['rev-parse', 'FETCH_HEAD'], tmp).stdout.strip() != commit:
            raise ValueError('Backup ref changed')
        if git(['rev-list', '--parents', '-n', '1', commit], tmp).stdout.split() != [commit]:
            raise ValueError('Backup must have no application history')
        if git(['ls-tree', '-r', '--name-only', commit], tmp).stdout.splitlines() != [filename]:
            raise ValueError('Backup must contain exactly one dated SQL file')
        path = Path(output)
        with path.open('x', encoding='utf-8') as stream:
            path.chmod(0o600)
            stream.write(git(['show', f'{commit}:{filename}'], tmp).stdout)
    print('Verified immutable dump-only backup source.')


if __name__ == '__main__':
    try:
        download(os.environ['RESTORE_BACKUP_DATE'], os.environ['RESTORE_BACKUP_COMMIT'], sys.argv[1])
    except Exception:
        print('Backup download failed; no restore attempted.', file=sys.stderr)
        sys.exit(1)
