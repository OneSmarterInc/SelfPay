# MySelfPay iOS app

Native SwiftUI/WKWebView app for https://myselfpay-review.vercel.app/.
Requires iOS 15+. Uses the existing website; internet is required.
No PWA, website, deployment, database, or backup changes.

Includes HTTPS exact-origin navigation, user-activated external links, back
navigation, reload and a retry screen. Guest web storage is ephemeral for the
app process. No native JavaScript bridge, embedded credentials, TLS exceptions,
tracking SDKs or offline database. Native camera/location/push features are not
implemented. Device UX and external links still require real-phone acceptance.

## Unsigned validation

GitHub Actions builds both a device executable and a simulator app and runs
11 URL policy checks. The simulator download only runs on a Mac iOS simulator.
It is NOT an installable iPhone IPA. No unsigned IPA is advertised as installable.

On a Mac with Xcode:
  gem install xcodeproj -v 1.27.0 --user-install --no-document
  cd ios
  ruby generate_project.rb
  python3 generate_icon.py
  open MySelfPay.xcodeproj

## Signing and TestFlight setup

Planned bundle ID: com.onesmarter.myselfpay.
Register this explicit ID in the correct Apple Developer team and create a
MySelfPay iOS app record in App Store Connect using the same bundle ID.
If the identifier is already owned by another team, choose a new one before signing.

Provide the team ID (not a password) and confirmation of the app record first.
For CI signing, use a dedicated GitHub environment named ios-signing and store:
- IOS_DISTRIBUTION_P12_BASE64: base64 Apple Distribution certificate WITH private key
- IOS_DISTRIBUTION_P12_PASSWORD: its export password
- IOS_PROFILE_BASE64: base64 App Store Connect distribution provisioning profile
  for the same bundle ID and certificate
Use IOS_TEAM_ID as an environment variable.
Never paste certificates, passwords or private keys in chat, commits or PRs.

A certificate downloaded from Apple's portal alone does not contain the private
key. The person who created its CSR must export the matching key/certificate as
a password-protected P12. A Windows OpenSSL-based CSR/export route is possible;
retain the private key locally and never send it in chat.

Once those assets are available, the signed archive/export workflow can be
completed and tested using a temporary macOS keychain with unconditional cleanup.
For TestFlight upload from Windows/CI, a separate App Store Connect API key
(Key ID, Issuer ID, and private P8 stored as secrets) can be configured after the
signed build succeeds. Do not grant broader Apple access or upload automatically
as part of pull-request tests.

Apple processing/review and any export-compliance questions must be completed
before testers can install. App Store approval of a basic website wrapper is not
guaranteed. This project has no signed device IPA or TestFlight release yet.
