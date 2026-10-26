#!/usr/bin/env python3
"""Restore original APK mobile UI assets and the supplied app icon for each build."""
from pathlib import Path
import base64, hashlib, io, tarfile

root = Path(__file__).resolve().parents[1]
bundle = root / 'android/original-apk-ui-assets.tar.gz.b64'
files = {
    'mobile-flow.css': ('android/app/src/main/assets/mobile-flow.css', '22cbd3dd0ed7d30e1e7d8db1efc7227d2b53422742f15ba65fb8ff1923363e20'),
    'mobile-flow.js': ('android/app/src/main/assets/mobile-flow.js', '93ddc52969088f3cde7f36273d1db26debbf5ee36bd27f85677a4ac3a936ed37'),
    'ic_launcher.jpg': ('android/app/src/main/res/drawable/ic_launcher.jpg', None),
}
with tarfile.open(fileobj=io.BytesIO(base64.b64decode(bundle.read_text().strip())), mode='r:gz') as archive:
    for name, (path, digest) in files.items():
        member = archive.getmember(name)
        if not member.isfile():
            raise ValueError('Unexpected archive member: ' + name)
        data = archive.extractfile(member).read()
        if digest and hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Original APK UI checksum mismatch: ' + name)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print('Prepared', path)
legacy = root / 'android/app/src/main/res/drawable/ic_launcher.xml'
if legacy.exists():
    legacy.unlink()
