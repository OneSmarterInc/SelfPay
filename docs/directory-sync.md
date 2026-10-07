# Unattended public provider-directory sync

## What is ready and what is gated

The source of truth remains Library item `libfile_8ba8491c8ff881918ed4868c0ee43465`,
`US_Self_Pay_Imaging_Directory.xlsx`. The verified bootstrap is version 7,
SHA-256 `e60778bb503442e40ce035fdf70958db65ca1d710ce0279b06c2bcea8bd42a96`,
93 entries and 13 existing searchable offers. The repository's older bundled
74-entry/57-offer seed is not this live catalog. `publish_directory.py` is disabled
so it cannot replace the live data.

Scheduled imports and manual apply are disabled unless repository variable
`SELFPAY_DIRECTORY_SYNC_ENABLED` is `true`. An explicitly dispatched
read-only dry-run from main is allowed while that variable remains unset/false. A merge does not provision the
database, install credentials, enable a schedule, or promote the application.
No live import is established until the one-time setup and live verification below
have completed. Daily jobs can be delayed by GitHub; do not promise an exact minute.

## Data path and deployment separation

1. Research updates the canonical Library workbook. Resolve its latest version and
   materialize its current bytes. Never substitute a cached workbook or a repo seed.
2. Run trusted `main` code locally, outside the data branch:

   ```sh
   python -m pip install --require-hashes -r ops/directory-export-requirements.txt
   python directory_sync.py export /path/to/US_Self_Pay_Imaging_Directory.xlsx \
     --library-version 7 --output /path/to/data-checkout/directory
   ```

   Replace `7` with the actual materialized Library version. Retain the returned
   workbook SHA-256, source version, entry count and document hash. The exporter
   checks the complete 13-column Directory header, rejects formulas/extra populated
   columns, and exports only public provider fields plus source row numbers. It
   never exports other tabs, member data, credentials, or private conversations.
   The source's caveats, component-only prices and quote-required distinctions are
   preserved; no numeric search offer is inferred from prose.
3. Publish `directory/current.json` and its byte-identical immutable
   `directory/versions/vNNNNNN-SHA256.json` together to private branch `directory-data`.
   Use an expected-head lease; if another writer moved the branch, reread and
   reconcile instead of force-pushing. Keep all prior versioned exports. Do not
   merge this data-only branch into main. The branch has no executable workflows;
   its `vercel.json` sets `git.deploymentEnabled=false`.
4. The trusted main-branch **Directory sync** workflow checks out only the data
   directory from `directory-data`; it never executes anything from that branch.
   It runs a daily recovery/import at 02:17 UTC, following the existing research
   schedule, and supports a manual dry-run/apply from main. After an export, run a
   main-branch dispatch if immediate publication is needed; otherwise verify the
   next daily run. No dispatch is assumed to exist if the tool used for the export
   only supports repository writes.
5. The restricted login reads a non-sensitive snapshot and invokes one validated,
   atomic database operation. After publication, it re-reads the catalog and
   verifies every entry, all offers and the source ledger before committing.

The application branch also disables Vercel Git deployments for `directory-data`
and `directory-sync-*`. On first branch publication, verify the actual GitHub
checks and Vercel deployment list before calling this separation proven. Unrelated
application branches retain their existing deployment behavior and
`github.autoAlias=false`. The workflow does not call Vercel or deploy application code.

## One-time setup (separate approvals required)

Target: Vercel team `1smarterincs-projects`, project `myselfpay-review`; Neon project
`late-grass-13270808`, branch `br-rapid-mouse-b7clh18t`, database `neondb`.
The project is documentary; SQL checks the database and actual Neon branch setting.

1. Review and approve the exact `ops/directory_sync.sql` grant package. An
   administrator executes it against that target. It is transactional, refuses
   existing role/schema names, and checks the reviewed active batch and counts.
   Vercel Query accepts only one prepared statement: use the reviewed
   `ops/directory_sync_query.sql` wrapper there, not the multi-command psql file.
   The wrapper embeds the same package with only outer BEGIN/COMMIT removed; its
   single invoker DO statement preserves atomic rollback and every guard/grant.
   The administrator must have INHERIT and CREATEROLE (verified for neondb_owner).
   Never run `core.initialize`, `setup_hosted.py`, `test_postgres`, or any unit test
   against this database. Existing data stays untouched during provisioning.
2. The package creates:
   - `selfpay_directory_owner`: NOLOGIN, no superuser/createdb/createrole/replication/
     bypass-RLS privileges; owns only the private import schema/functions/ledger
   - `selfpay_directory_importer`: LOGIN but no password; same negative privileges,
     no role memberships and no direct public-table privileges
   - Private `selfpay_directory_sync` schema. The login receives only USAGE and
     EXECUTE on `status()` and `apply_bundle(text,text,boolean)`, plus CONNECT to
     `neondb`. Every function has a fixed `pg_catalog` search path; references are
     schema-qualified and PUBLIC execution is revoked
   - The owner receives SELECT/INSERT on batches, entries, offers and publish_events;
     UPDATE on entries/offers solely because PostgreSQL requires it for the
     writer-excluding table locks; SELECT and UPDATE(value) on settings; and USAGE
     on the publication sequence. The functions never update entries or offers.
     No batch/event UPDATE or any catalog DELETE/TRUNCATE is granted.
     The functions touch only the `active_batch` setting. Members, sessions,
     conversations, preferences, corrections, guest usage and rate-limit tables are
     excluded. Default database PUBLIC TEMP, if present, is not changed; temporary
     objects cannot shadow the schema-qualified implementation
3. The user, through a secure administrator interface, personally enters and
   submits a strong unique password for the import role. In an already secure
   psql session, `\password selfpay_directory_importer` avoids putting it in SQL
   history. Do not paste passwords or connection strings into chat. Do not reuse
   the application or cleanup connection string. Do not retrieve the application's
   `DATABASE_URL` from Vercel.
4. Separately approve/configure GitHub environment `directory-sync` to allow only
   the `main` branch. The user personally saves the restricted connection string
   there as environment secret `SELFPAY_DIRECTORY_DATABASE_URL`, with role
   `selfpay_directory_importer` and database `neondb` at the correct Neon endpoint.
   TLS certificate and host verification plus channel binding are enforced by the
   client. Never put the secret in repository files, workflow inputs, artifacts,
   CLI arguments, or ordinary messages. The assistant does not need to see it.
   Do not reuse `SELFPAY_CLEANUP_DATABASE_URL`.
5. Approve/merge the reviewed code PR, leaving the live-enable variable unset.
   Workflow code and data stay separate; runtime token permissions are
   contents-read-only. Actions and pip distributions are pinned; secrets are
   exposed only during the database step, never to PR tests.
6. Dispatch **Directory sync** from main with `apply=false` and expected active
   `25c0d8d8-a6de-4f0e-b106-3d4b5ab0a48f`. This read-only check works while live
   imports remain disabled. Verify zero additions/changes/removals, 93 entries
   and 13 offers.
7. After successful dry-run and explicit approval for activation, set repository
   variable `SELFPAY_DIRECTORY_SYNC_ENABLED=true`. This permits manual apply and
   the daily scheduled import. Dispatch `apply=true` to anchor the v7 bootstrap
   ledger without replacing the current batch. Confirm the job, database source
   ledger and website catalog. A later additive export and repeat run should
   demonstrate one publication followed by an idempotent no-op.

Credential rotation/revocation or changed GitHub/Neon access can require future
manual intervention. OTP-free routine import is only a verified outcome after a
successful live workflow run; the code alone is not proof.

## Guardrails and review-required updates

- A stale export cannot be newly imported (48-hour freshness window, five-minute
  clock-skew allowance). An already imported identical workbook may be checked
  without republishing, even after that window
- Library identity is fixed; source version cannot move backwards, and the same
  version cannot identify different workbook bytes. Current/archived export bytes
  must match. Entry IDs/content hashes are recomputed both client- and server-side
- Bootstrap must match the reviewed live batch exactly. Later imports can append
  verified public entries. Existing entry changes, deletions, renames and mapping
  changes stop the run for explicit review; they are never silently discarded
- All 13 current offers, including their exact price types, amounts, caveats and
  source hashes, are copied unchanged. New directory entries may appear in Browse
  without becoming searchable priced offers. Additional offer mapping is a
  separate reviewed change, not automatic numeric extraction
- Locks plus expected-active comparison prevent races. The active pointer must
  remain on the approved sync lineage. Every failure rolls back the transaction
- Previous batches and publication events are retained. The login cannot delete
  historical catalogs or change function ownership/schema/security policy
- No database exception details/connection strings or provider-controlled text are
  printed by the CLI; error logs contain safe codes and SQLSTATE only

## Rollback / recovery

Disable the workflow variable first if a newly discovered source problem needs
review. An administrator inspects the last successful publication event and source
ledger and, with explicit approval, restores its `previous_batch` using a guarded
transaction and an expected-current-batch check. The importer deliberately has no
rollback function or arbitrary pointer-update access. Never rerun the retired seed
publisher. An out-of-band rollback causes subsequent imports to stop until the
administrator reviews/re-anchors the lineage; it cannot be silently overwritten.

Current pre-sync rollback: `bf2bbae4-8de8-4245-af34-1f6ada0a6e72` (85 entries, 13
preserved offers). It is historical context, not automatic rollback authorization.

## Verification

Run existing app checks, the new strict export tests and the isolated PostgreSQL
privilege/transaction tests. The PostgreSQL tests create/drop disposable schemas,
roles and databases; they are prohibited against hosted environments.

- SQLite/app checks: `python -m unittest test_functional test_hosted test_cleanup test_guest_limits test_guest_tier -v`
- Client checks: `node test_ui.mjs` (stub transport, not visual browser QA)
- Export/validation checks: `python -m unittest test_directory_sync -v`
- Isolated access-boundary checks: `python -m unittest test_directory_sync_postgres test_directory_sync_query_postgres -v`

## Primary implementation references

- [GitHub secure workflow guidance](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Actions secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Vercel Git deployment controls](https://vercel.com/docs/project-configuration/git-configuration)
- [PostgreSQL SECURITY DEFINER guidance](https://www.postgresql.org/docs/current/sql-createfunction.html)
- [PostgreSQL TLS verification](https://www.postgresql.org/docs/current/libpq-ssl.html)

### Guarded manual repair for the observed function variant

Read-only inspection found a manually installed `apply_bundle` variant with three
changed variable references. Its dry-run succeeds, but apply fails on an ambiguous
`document_hash` reference. `ops/repair_directory_apply.sql` restores only that
function to the exact reviewed definition. It is a single prepared statement for
authorized manual administrator execution, not a workflow or assistant operation.
It pins the observed bad body hash, correct owner/signature, original active batch,
93/13 catalog fingerprints and empty ledger. Unknown state aborts; an already
correct function is a no-op only at the same verified baseline. It preserves all
other functions, roles, ACLs, memberships and data, and rolls back on any failure.
The user must run it themselves, then have the restored body/permissions verified
before any live import or credential test. Do not rerun the initial provisioning
package after roles already exist.
