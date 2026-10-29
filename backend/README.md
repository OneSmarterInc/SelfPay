# Backend

Python API code, database access and bundled geographic lookup data. AWS entry point: `lambda_handler.lambda_handler`, using API Gateway HTTP API payload format 2.0. Dockerfile builds a Lambda Python 3.12 container image from **this directory**. Install runtime requirements before ZIP deployment, using a Lambda-compatible Linux build environment.

Required runtime configuration:
- `DATABASE_URL`: existing authorized PostgreSQL connection, set securely in AWS. Never place it in frontend files, chat, source control or Docker build arguments.
- `APP_ORIGIN`: exact frontend HTTPS origin, e.g. https://myselfpay.onesmarter.com, without a path. Only that browser origin is accepted for writes.

The adapter does not call make_server(), initialize(), seed imports or schema migrations. It requires an already initialized database. Database-backed rate limits, guest sessions, CSRF and secure host-only cookies are preserved. GET/POST/DELETE /api/* routes are supported; this Lambda does not serve static assets. Errors do not print database credentials or request contents.

Source IP is taken only from API Gateway request context. Behind CloudFront that may be an edge IP; validate rate-limit behavior before public launch. Do not blindly trust client X-Forwarded-For. Review trusted-edge forwarding/WAF separately if individual IP limits are needed behind CloudFront.

Existing application modules and seed files here are generated copies; refresh them with `python tools/sync_aws_folders.py` from the repository root. lambda_handler.py, Dockerfile and this README are AWS-specific. No AWS resources are provisioned by these files.
