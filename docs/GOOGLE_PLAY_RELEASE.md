# MySelfPay — Google Play release checklist

**Branch:** `release/google-play-preparation` — do not merge until release checks pass.

## Release configuration
- Application ID: `com.onesmarter.myselfpay`
- Version: `1.0.0` (versionCode 1)
- Android min API 26; compile/target API 36.
- Google Play needs a signed **AAB**, not the debug APK.
- Google Play App Signing must be enabled for the listing.

## Build signed bundle through GitHub Actions
1. Generate and securely back up an **upload** keystore under company custody, not in the repository.
2. In GitHub → Settings → Secrets and variables → Actions add:
   - `MYSELFPAY_UPLOAD_KEYSTORE_BASE64` (base64 of keystore bytes, single line)
   - `MYSELFPAY_KEY_ALIAS`
   - `MYSELFPAY_STORE_PASSWORD`
   - `MYSELFPAY_KEY_PASSWORD`
3. GitHub → Actions → **Android Play release** → Run workflow on `release/google-play-preparation`.
4. Download the `MySelfPay-Play-release-aab` artifact.
5. Upload signed `app-release.aab` to Play Console → Testing → Internal testing.

Never paste keystore content or passwords into chat or commit to GitHub. Do not replace the upload key between releases without key reset process.

## Critical product and policy checks
- Current Android documentation names `https://myselfpay-review.vercel.app/` as the app origin. Verify a stable production host and access before public release. A review, staging or deployment-protected site should not be used.
- Test on Android 16 for edge-to-edge display, status-bar contrast, on-screen keyboard, safe-area handling, and navigation.
- Confirm no unauthorized external pages load inside the WebView.
- Check that the app offers adequate mobile functionality and isn't a broken or minimal web wrapper.
- Complete store listing, app icon, feature graphic, screenshots, support contact, privacy policy URL, ads/content rating/data safety declarations.
- Complete Health Apps declaration accurately based on actual features and data handling.
- Run Play pre-launch report, install internal-testing app on physical devices, review issues, and only then request production rollout.
- Do not assert health or billing outcomes the app does not guarantee.

Google API policy: https://support.google.com/googleplay/android-developer/answer/11926878

**Status:** Build pipeline prepared but not yet validated; requires GitHub signing secrets and real device/Play Console checks.
