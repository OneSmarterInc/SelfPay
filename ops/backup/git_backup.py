"""Publish exactly one SQL dump on a new, parentless date branch."""
import base64
import json
import re
import urllib.request
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
    repository = BACKUP_REPOSITORY
    verify_destination()
    token = os.environ['BACKUP_REPO_TOKEN']
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
        prune_branches(tmp, remote, env, day)
    print(f'Verified backup-{day}: one SQL dump, no application history; retention completed.')



BACKUP_REPOSITORY = 'OneSmarterInc/MySelfPay_Backup'


def verify_destination():
    """Fail closed before reading/exporting data if the approved repo is not private."""
    token = os.environ['BACKUP_REPO_TOKEN']
    request = urllib.request.Request(
        'https://api.github.com/repos/' + BACKUP_REPOSITORY,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28'})
    with urllib.request.urlopen(request, timeout=30) as response:
        repository = json.load(response)
    if repository.get('full_name') != BACKUP_REPOSITORY or repository.get('private') is not True:
        raise ValueError('Approved backup repository must be private')
    if not repository.get('permissions', {}).get('push'):
        raise ValueError('Backup token needs destination Contents read/write access')


def retention_candidates(branches, today):
    """Keep newest 14 daily branches and earliest available branch of each month.

    Ignore other refs, invalid dates, and future dates. Only one-file backup refs
    in the fixed destination repository are eligible; content is checked on delete.
    """
    cutoff = date.fromisoformat(today)
    dated = []
    for branch in branches:
        if not re.fullmatch(r'backup-\d{4}-\d{2}-\d{2}', branch):
            continue
        try:
            day = date.fromisoformat(branch[7:])
        except ValueError:
            continue
        if day <= cutoff:
            dated.append((day, branch))
    dated.sort()
    keep = {branch for _, branch in dated[-14:]}
    months = set()
    for day, branch in dated:
        month = (day.year, day.month)
        if month not in months:
            keep.add(branch)
            months.add(month)
    return [branch for _, branch in dated if branch not in keep]


def prune_branches(directory, remote, env, today):
    refs = {}
    for line in git(['ls-remote', '--heads', remote], directory, env).stdout.splitlines():
        sha, ref = line.split()
        refs[ref.removeprefix('refs/heads/')] = sha
    for branch in retention_candidates(refs, today):
        ref = 'refs/heads/' + branch
        sha = refs[branch]
        # Refuse to prune a branch containing application history or other files.
        git(['fetch', '--no-tags', remote, ref], directory, env)
        if git(['rev-parse', 'FETCH_HEAD'], directory).stdout.strip() != sha:
            raise ValueError('Retention branch changed; refusing deletion')
        if git(['ls-tree', '-r', '--name-only', sha], directory).stdout.splitlines() != [f'database-{branch[7:]}.sql']:
            raise ValueError('Retention branch is not a dump-only branch')
        if git(['rev-list', '--parents', '-n', '1', sha], directory).stdout.split() != [sha]:
            raise ValueError('Retention branch has unexpected history')
        git(['push', '--porcelain', '--force-with-lease=' + ref + ':' + sha, remote, ':' + ref], directory, env)
        check = git(['ls-remote', '--exit-code', '--heads', remote, ref], directory, env, check=False)
        if check.returncode != 2:
            raise ValueError('Retention deletion verification failed')
        print('Retention removed ' + branch)
