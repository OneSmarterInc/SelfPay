# Frontend

`public/` contains the complete static website: HTML, JavaScript, fonts, logos, icons and PWA files. There are no database credentials or backend modules in this folder. Upload the **contents** of public, not the parent folder, to a private S3 bucket served through CloudFront with Origin Access Control. Do not enable a public bucket just for hosting.

Keep `/api/*` on the same HTTPS hostname and route it to the backend API Gateway origin with caching disabled. Forward cookies, Origin, Content-Type and X-CSRF-Token; allow GET, HEAD, OPTIONS, POST, PUT, PATCH and DELETE on this behavior. Do not forward the website Host header to API Gateway. HTTPS is required for guest cookies. Do not rewrite API errors to index.html.

Static clean routes must map to their HTML files: `/about` → `/about.html`, `/contact` → `/contact.html`, `/for-imaging-centers` → `/for-imaging-centers.html`, and `/privacy`, `/terms`, `/privacy-terms` → `/privacy-terms.html` (including trailing slashes). Root maps to index.html. Configure these as a CloudFront viewer-request rewrite on the static behavior only. Keep sw.js, app.js and HTML cache durations short, and invalidate changed files on release. Apply the existing server security headers through a CloudFront response headers policy.

These are generated deployment copies of root `static/`. Make edits there, then run `python tools/sync_aws_folders.py`; `--check` detects stale copies. This preserves the current Vercel/mobile build paths during migration. See docs/aws-deployment.md before deploying.
