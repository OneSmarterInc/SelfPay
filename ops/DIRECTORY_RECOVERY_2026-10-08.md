# Directory dry-run recovery — 2026-10-08

Installed apply_bundle definition supplied by the administrator pins bootstrap to 25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f. The supplied snapshot instead has active batch b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4, 99 entries, 13 offers, and no import ledger. All incoming entries and offer mappings match the supplied snapshot.

Run ops/directory_recovery_verified.sql as an authorized database administrator/function owner in the correct database. It checks the Neon target, exact supplied function-body digest, active batch, counts, ledger absence, and both catalog fingerprints before changing the function. It retains existing guards and adds an exact-bundle recovery path that rejects live publishing. The script embeds the reviewed bundle and verifies the dry run and unchanged snapshot in the same transaction before committing. On error, roll back; do not bypass the check or alter role permissions to force it.

No directory records, prices, active pointers, source ledger rows, roles, or grants are modified. The change is function DDL. The snapshot-only recovery path deliberately cannot publish: its inherited workbook provenance is unverified. A new canonical workbook export and separately reviewed publishing transition remain necessary. Freshness checking remains active; this bundle expires 2026-10-09 10:28:42 UTC. Do not refresh its timestamp manually.

Local verification: isolated PGlite PostgreSQL engine loaded with supplied 99-entry/13-offer snapshot and installed function. Original bootstrap error reproduced. Complete migration, including transactional dry-run verification, passed. Dry run left status unchanged; live publishing, altered bundle bytes, and altered offer amount were rejected. The local Neon platform-target function was stubbed because this is not Neon; deployed branch checks and live administrator privileges have not been tested. This migration has NOT been applied to the hosted database by Codex.

PR #10 was closed without merging. directory-data remains separate from main. No workflow dispatch or live deployment performed.
