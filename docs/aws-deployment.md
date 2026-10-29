# AWS deployment preparation

Status: folder separation and API adapter prepared; not deployed or verified against AWS. No infrastructure, database migration, domain change or paid service has been created. The current Vercel source and deployment settings remain intact.

## Layout
- frontend/public/: static website, copied from static/.
- backend/: Python API/domain modules, bundled seed/geo files, app config and Lambda adapter.
- tools/sync_aws_folders.py: reproducible deployment-folder refresh/check.

Root files remain the source of truth while Vercel is still in use. Edit those files and refresh the deployment folders in the same commit. This is a transitional deployment separation, not two independently maintained copies. Native Android/iOS project locations are unchanged.

## Before an AWS release
1. Select the AWS account, region and public test hostname. Review service costs before creating resources; AWS free allowances are not a guarantee of a $0 deployment.
2. Run `python tools/sync_aws_folders.py --check`, `python -m unittest test_aws_adapter -v`, and the existing test suite.
3. Build backend/Dockerfile for the chosen Lambda architecture (or prepare a compatible ZIP), then configure API Gateway HTTP API payload v2. Configure DATABASE_URL through an authorized secret workflow and APP_ORIGIN for the chosen hostname. Never log them. Use an isolated test database first; do not seed or migrate production on startup.
4. Configure private S3 + CloudFront for frontend/public and a noncached /api/* API Gateway behavior. Follow frontend/README.md for cookies, methods, route rewrites and headers. Set the frontend hostname in APP_ORIGIN. No broad cross-origin CORS policy is needed.
5. Verify through the public test hostname: guest sign-in, cookie persistence, state/city search, count accuracy, comparison, appointment mailto draft, refresh/deep links, sign-out, CSRF rejection and rate limits. Confirm API responses are never cached. Test mailto on actual target devices; opening a draft does not prove sending.
6. Keep production DNS/Vercel unchanged until this test deployment passes and the owner authorizes cutover. Existing Neon can remain the database; moving it to AWS RDS is a separate migration requiring a verified backup and approval.

Local adapter tests use synthetic data/mocks and do not establish AWS routing, IAM, deployment or production connectivity. No daily backup or Actions budget settings are changed.

Reference: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
