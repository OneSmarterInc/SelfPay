"""Package the supplied MySelfPay artwork as an opaque 1024px app icon."""
from pathlib import Path
import base64
import subprocess
import tempfile
root = Path(__file__).resolve().parent
output = root / "MySelfPay/Assets.xcassets/AppIcon.appiconset/icon.png"
with tempfile.TemporaryDirectory() as temporary:
    source = Path(temporary) / "icon.jpg"
    source.write_bytes(base64.b64decode((root / "launcher-icon.jpg.base64").read_text(), validate=True))
    subprocess.run(["sips", "-s", "format", "png", str(source), "--out", str(output)], check=True)
