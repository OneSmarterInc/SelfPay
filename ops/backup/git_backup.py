"""Publish exactly one SQL dump on a new, parentless date branch."""
import base64
from datetime import date, datetime
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from zoneinfo import ZoneInfo


def backup_date(now=None):
    return (now or datetime.now(ZoneInfo('Asia/Kolkata'))).astimezone(ZoneInfo('Asia/Kolkata')).date().isoformat()


def git(args, cwd, env=None, check=True):
    return subprocess.run(['git', *args], cwd=cwd, env=env, check=check,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def create_commit(directory, SQL, day):
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError('Invalid date')
    source = Path(SQL)
    with source.open('rb') as f:
        if b'PostgreSQL database dump' not in f.read(1024):
            raise ValueError('Expected a PostgreSQL SQL dump')
        f.seek(max(0, source.stat().st_size - 4096))
        if b'PostgreSQL database dump complete' not in f.read():
            raise ValueError('Missing dump completion marker')
    if not 0 < source.stat().st_size < 95 * 1024 * 1024:
        raise ValueError('Dump exceeds supported Git file size')
    directory = Path(directory)
    filename = f'database-{day}.sql'
    git(['init', '-q', '--initial-branch', f'backup-{day}'], directory)
    git(['config', 'user.name', 'SelfPay backup'], directory)
    git(['config', 'user.email', 'backup@users.noreply.github.com'], directory)
    shutil.copyfile(source, directory / filename)
    git(['add', '--', filename], directory)
    git(['-c', 'commit.gpgsign=false', 'commit', '-q', '-m', f'Plain SQL database backup {day}'], directory)
    head = git(['rev-parse', 'HEAD'], directory).stdout.strip()
    assert git(['ls-tree', '-r', '--name-only', 'HEAD'], directory).stdout.splitlines() == [filename]
    assert git(['rev-list', '--parents', '-n', '1', 'HEAD'], directory).stdout.split() == [head]
    return head


def publish(SQL, day):
    repository = os.environ['GITHUB_REPOSITORY']
    if repository != 'OneSmarterInc/SelfPay':
        raise ValueError('Unexpected repository')
    token = os.environ['GITHUB_TOKEN']
    remote = f'https://github.com/{repository}.git'
    auth = base64.b64encode(('x-access-token:' + token).encode()).decode()
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_CONFIG_COUNT='1',
               GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
               GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + auth)
    ref = f'refs/heads/backup-{day}'
    with tempfile.TemporaryDirectory(prefix='selfpay-dated-branch-') as tmp:
        # Fail before upload on duplicates or any inability to check the remote.
        existing = git(['ls-remote', '--exit-code', '--heads', remote, ref], tmp, env, check=False)
        if existing.returncode != 2:
            raise ValueError('Branch exists or remote check failed; refusing overwrite')
        head = create_commit(tmp, SQL, day)
        git(['push', '--porcelain', remote, f'HEAD:{ref}'], tmp, env)
        actual = git(['ls-remote', '--exit-code', '--heads', remote, ref], tmp, env).stdout.split()[0]
        if actual != head:
            raise ValueError('Remote verification failed')
    print(f'Verified backup-{day}: one SQL dump, no application history.')
