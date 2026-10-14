"""Validate signing inputs without printing secret values; install in a temporary keychain."""
import base64
import datetime
import hashlib
import os
from pathlib import Path
import plistlib
import re
import secrets
import subprocess
import sys

def run(*args):
    result = subprocess.run(args, capture_output=True)
    if result.returncode:
        raise RuntimeError("Signing command failed: " + args[0] + " " + args[1] + "; check certificate, password, and profile.")
    return result.stdout

def main():
    os.umask(0o077)
    required = ["IOS_DISTRIBUTION_P12_BASE64", "IOS_DISTRIBUTION_P12_PASSWORD", "IOS_PROFILE_BASE64"]
    if os.environ["RELEASE_MODE"] == "upload":
        required += ["ASC_KEY_ID", "ASC_ISSUER_ID", "ASC_PRIVATE_KEY"]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing secrets: " + ", ".join(missing))
    folder = Path(os.environ["RUNNER_TEMP"]) / "selfpay-signing"
    folder.mkdir(mode=0o700)
    for name, filename in [("IOS_DISTRIBUTION_P12_BASE64", "certificate.p12"), ("IOS_PROFILE_BASE64", "profile.mobileprovision")]:
        (folder / filename).write_bytes(base64.b64decode("".join(os.environ[name].split()), validate=True))
    profile = plistlib.loads(run("security", "cms", "-D", "-i", str(folder / "profile.mobileprovision")))
    team = os.environ["IOS_TEAM_ID"]
    bundle = os.environ["IOS_BUNDLE_ID"]
    ent = profile["Entitlements"]
    assert profile["TeamIdentifier"] == [team], "Wrong profile team"
    assert ent["com.apple.developer.team-identifier"] == team, "Wrong entitlement team"
    assert ent["application-identifier"] == team + "." + bundle, "Wrong Bundle ID"
    assert not ent.get("get-task-allow", False), "Development profile refused"
    assert ent.get("beta-reports-active") is True, "App Store profile required"
    assert not profile.get("ProvisionedDevices") and not profile.get("ProvisionsAllDevices"), "App Store profile required"
    assert profile["ExpirationDate"] > datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None), "Expired profile"
    uuid = profile["UUID"]
    assert re.fullmatch(r"[A-Fa-f0-9-]{36}", uuid), "Invalid profile UUID"
    keychain = str(folder / "signing.keychain-db")
    password = secrets.token_urlsafe(32)
    run("security", "create-keychain", "-p", password, keychain)
    run("security", "set-keychain-settings", "-lut", "1800", keychain)
    run("security", "unlock-keychain", "-p", password, keychain)
    run("security", "import", str(folder / "certificate.p12"), "-P", os.environ["IOS_DISTRIBUTION_P12_PASSWORD"], "-A", "-t", "cert", "-f", "pkcs12", "-k", keychain)
    run("security", "set-key-partition-list", "-S", "apple-tool:,apple:,codesign:", "-k", password, keychain)
    run("security", "list-keychains", "-d", "user", "-s", keychain)
    identities = run("security", "find-identity", "-v", "-p", "codesigning", keychain).decode()
    matches = re.findall(r'([A-Fa-f0-9]{40}) "(Apple Distribution:[^"]+)"', identities)
    allowed = {hashlib.sha1(cert).hexdigest().upper() for cert in profile["DeveloperCertificates"]}
    matching = [fingerprint for fingerprint, label in matches if fingerprint.upper() in allowed and "(" + team + ")" in label]
    assert len(matching) == 1, "No unique valid distribution identity matching profile and private key"
    destination = Path.home() / "Library/MobileDevice/Provisioning Profiles" / (uuid + ".mobileprovision")
    destination.parent.mkdir(parents=True, exist_ok=True)
    (folder / "profile-path").write_text(str(destination) + "\n")
    destination.write_bytes((folder / "profile.mobileprovision").read_bytes())
    export = dict(method="app-store-connect", teamID=team, signingStyle="manual", signingCertificate=matching[0], provisioningProfiles={bundle: uuid}, manageAppVersionAndBuildNumber=False, uploadSymbols=True)
    (folder / "export.plist").write_bytes(plistlib.dumps(export))
    if os.environ["RELEASE_MODE"] == "upload":
        key_id = os.environ["ASC_KEY_ID"]
        assert re.fullmatch(r"[A-Za-z0-9]+", key_id), "Invalid API key ID"
        key = folder / ("AuthKey_" + key_id + ".p8")
        key.write_text(os.environ["ASC_PRIVATE_KEY"])
        run("openssl", "pkey", "-in", str(key), "-noout")
    with open(os.environ["GITHUB_ENV"], "a") as output:
        output.write("PROFILE_UUID=" + uuid + "\nSIGNING_IDENTITY=" + matching[0] + "\n")
    print("Signing verified: expected team and Bundle ID; unexpired App Store profile; matching valid certificate and private key.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("::error::" + (str(error) if isinstance(error, (AssertionError, RuntimeError)) else "Invalid signing input; check saved secrets."))
        sys.exit(1)
