# MySelfPay review POC

Self-pay MRI/CT directory with guest-only search and a limited deterministic chat.
No external AI, voice service, OCR, booking, payment or insurance calculation is
connected. Use synthetic member information only. Research listings are not a
contracted provider network, guaranteed quote or medical recommendation.

The bundle has 74 researched directory entries and 57 mapped MRI/CT offers.
Entries may cover facilities, branches or networks. Exact price scope, contrast,
source dates, restrictions and quote-required distinctions are preserved.

## Guest policy

Guests can search, filter, browse and compare freely. Chat allows 3 conversations,
5 messages each, and 500 characters/message. Chat text is not saved. Saved history
and full agent access are planned for future accounts; premium does not exist.
Only listed location preferences and server-side usage metadata may be stored.
Sessions last up to 8 hours. No password/login/register implementation remains.

See docs/guest-tier-handoff.md for all limits, tests, rollout and pending external
controls. See docs/cleanup-access.md for restricted cleanup-role provisioning.

## Local demo

```sh
pip install -r requirements.txt
python server.py
```

Open http://127.0.0.1:8765. SQLite initializes locally. Hosted deployment requires
DATABASE_URL pointing to the intended PostgreSQL database, using the pooled Neon
endpoint. Never commit or paste credentials. Do not run test_postgres against the
review database: it drops test tables.

## Live database changes — mandatory policy

Before running any operational SQL on live Neon, follow [the change-control policy](ops/change-records/POLICY.md). Commit the SQL, test it on a separate Neon branch copy, and obtain Vikram's approval of the change record before live execution. This includes read-only operational queries. Use [the record template](ops/change-records/TEMPLATE.md). Older setup instructions below do not override this policy.

## Existing hosted database

Run ops/upgrade_guest_tier.sql as owner before testing this Preview. No automatic
public migration endpoint exists. New databases use setup_hosted.py. Directory
updates use the guarded workflow described in docs/directory-sync.md. The old
74-entry seed publisher is disabled: the verified live catalog already contains
93 entries and 13 preserved offers. The canonical Library workbook is the source
of truth. One-time restricted access setup and live activation require approval.

Git integration retains github.autoAlias=false: Preview only, no production
promotion. Vercel Deployment Protection is still unverified and requires account
access. The daily cleanup workflow needs SELFPAY_CLEANUP_DATABASE_URL; use a
restricted role and dry-run before apply. Backup retention is separate.


## Unattended directory imports

See [Directory sync setup and verification](docs/directory-sync.md). Public data
exports live on the separate `directory-data` branch. The daily import stays
disabled until restricted database access, the main-only GitHub environment, the
user-entered secret, and live dry-run are verified. No application deployment is
required to publish a validated data batch.
