# MySelfPay Android test app

Internet-connected Android wrapper for https://myselfpay-review.vercel.app/.
Android 8.0 or newer. Uses the existing hosted application and backend.
It does not package Python, SQL dumps, database credentials, or an offline database.

The app keeps only the exact HTTPS site inside its WebView. Provider websites,
phone, email and map links open with Android applications. Unsafe URL schemes,
cleartext in-app traffic, file access and TLS bypasses are blocked. JavaScript and
web storage support the existing site. Location is entered through the site's
existing search fields; native location, camera, upload and push notifications are
not implemented. Deployment protection, if enabled on the site, must be handled
separately; no bypass secret is embedded.

## Download

Open the successful **Android test APK** GitHub Actions run, download the
**MySelfPay-test-apk** artifact and extract **MySelfPay-test.apk**.
Transfer to Android, open it and allow installation from that source when Android
asks. This is a debug-signed test build, not a Play Store release. CI debug keys
may differ between runs; uninstall an older test build if Android reports a
signature conflict (uninstalling clears its local app data).

## Build locally

Install JDK 17, Android SDK 35 and Gradle 8.11.1.
Set ANDROID_HOME to the SDK, then from this directory:

    gradle :app:assembleDebug :app:lintDebug

Output: app/build/outputs/apk/debug/app-debug.apk.
The release variant is intentionally unsigned. A stable owner-held signing key
and release process are needed before distribution as a production app.

## Device acceptance

Verify initial load, city/procedure search, provider links, telephone links,
Android back navigation, keyboard layout, rotation, airplane-mode failure and
retry after reconnecting. No emulator/device success is implied by a build.
