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

## Existing hosted database

Run ops/upgrade_guest_tier.sql as owner before testing this Preview. No automatic
public migration endpoint exists. New databases use setup_hosted.py. Directory
updates use publish_directory.py (stage) then publish_directory.py --apply, with
python-dotenv installed and DATABASE_URL in .env.local. Expected 74 entries and
57 offers; no member reset. Preserve previous_batch for rollback.

Git integration retains github.autoAlias=false: Preview only, no production
promotion. Vercel Deployment Protection is still unverified and requires account
access. The daily cleanup workflow needs SELFPAY_CLEANUP_DATABASE_URL; use a
restricted role and dry-run before apply. Backup retention is separate.
