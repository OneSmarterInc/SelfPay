# MySelfPay PWA

The website can be installed to Android and iOS home screens. It uses the existing
server and requires internet for directory search and chat. It is not an APK or
App Store submission.

Android: open the HTTPS website in Chrome and use Install app (when offered),
or the browser menu's Install app / Add to Home screen.
iPhone/iPad: Safari → Share → Add to Home Screen → Open as Web App (if shown) → Add.
The website's Install app button also gives these instructions when a native
installation prompt is unavailable. Installed standalone windows hide the button.

The manifest has stable root identity/scope, standalone display and 192/512 PNG
icons, a separate maskable icon and a 180px Apple touch icon. The worker lives at
/sw.js so no broader scope header is required. Existing CSP allows same-origin
workers/manifests. Static routes are allowlisted and need no database connection.

Only /offline.html, a generic reconnect page, is cached. API requests, searches,
chat, session responses, JavaScript and live pages are not cached by the worker.
Root navigations try the network first and use the generic page only on network
failure. HTTP errors stay visible. Old MySelfPay offline caches are cleaned up;
other applications' caches are untouched. Updates wait until old clients close,
avoiding forced reloads during guest chat.

Tests: python -m unittest test_pwa -v; node test_pwa.mjs.
After approved deployment, verify manifest/icon/worker response types, installation
on Android and iPhone, standalone launch, existing search flow and offline retry.
Physical device installation has not been verified.

Production auto-deployment remains paused. This feature does not change backup
workflows, run restores, or change the database. Publishing needs the owner's
deployment decision.
