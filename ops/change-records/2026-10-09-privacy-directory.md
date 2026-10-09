# Guest privacy and coordinate/offer publication

Date: 2026-10-09. Prepared by Codex at the user's request.
Status: privacy code tested; data investigation documented; live execution NOT approved or performed.
Executor for live work: pending. Vikram approval: pending exact commit and Neon-copy evidence.

## Privacy code
Guest preference GET returns empty without database access; POST is rejected without database access. The save-location control and preference-loading request were removed. Search locations remain transient page/request data. Existing guest conversation writes are forbidden; usage counters contain counts, not search text. Application access logging remains suppressed. No browser geolocation is used. Platform-level request/body capture settings have not been independently verified.

Historical preference rows are not silently deleted. `ops/sql/guest-location-cleanup.sql` deletes guest preferences only after copy testing and approval. This deletion is intentionally not reversible by retaining copies of locations. Approve this privacy deletion explicitly. No live cleanup was executed.

## 13 versus 57 — findings and limits
Repository baseline examined: main `8325ccc0cd885f7877fdc56cdbe37d9374e7aeed`.

- `seed/mappings.json` contains 57 mappings: 22 fixed, 2 starting, 1 range, 1 conflict, 1 maximum, 30 quote-required. Calling all 57 priced offers is inaccurate.
- All 57 mapping entry hashes match entries in `directory-data/directory/current.json`, whose source version is 7 and which has 99 entries. Thus the repository snapshot comparison does NOT show 44 source-hash rejections.
- That bundle contains directory entries, not an expanded offers payload.
- `directory_sync.py` validates the existing database snapshot offers against incoming entries and requires post-publication offers to equal pre-publication offers. It does not load seed/mappings.json or generate new mappings.
- `ops/directory_recovery_verified.sql` explicitly guards offer_count=13 and the recorded offer fingerprint. Recovery was designed to preserve this set, not publish the expanded 57 mappings.
- Therefore the directory-sync/recovery path does not publish the additional repository mappings. A deliberate reviewed manual import is required to change the offer set.
- The historical status snapshot in record 4.1 reports batch b8696fb4-5db5-4de0-8c4e-6c65e8fc8cb4 with 99 entries/13 offers. No fresh live query was made here. The identity/date/command of the original 13-offer publication remain unverified; do not invent that attribution.

`ops/sql/directory-count-verification.sql` is a proposed catalog-only verification query. It still requires copy validation and approval before live execution.

## Publication preparation and blockers
Follow `docs/manual-directory-updates.md` and `ops/change-records/POLICY.md`. The specifically named `MySelfPay-dev-tasks-2026-10-09.md` was not located in the repository root or exact-title Library search; the manual process quoted in the conversation remains the provided requirement. No substitute document is represented as that file.

1. Obtain the approved workbook and pin its hash plus reviewed mappings hash. Current source/version and intended 57-offer publication need owner confirmation.
2. Create a Neon branch copy and record its ID/parent/copy time. No Neon connector or authenticated branch connection was available for this operation.
3. Stage on that copy with the pinned importer. New locations alter fingerprints: review newly withheld mappings rather than automatically rewriting their hashes.
4. Review every unresolved location, removal, offer price scope and branch applicability. Record actual stage report and exact intended counts; 57 is not an automatic publication target.
5. Complete the committed SQL review package for stage/publish/rollback and resolve the documented publish concurrency risk. The two SQL files in this change are cleanup/verification only, not a complete import package.
6. Rehearse publication and rollback on the copy. Record prior/new batch and result evidence.
7. Vikram approves exact committed files, target and expected differences. Only then stage/publish live and verify UI search.
8. Record executor and execution time, then remove the test branch after successful verification.

No live SQL, staging, publication, cleanup, branch creation/deletion or sync activation occurred. Historical batch ID is a candidate baseline, not a verified current rollback target.

## Tests
22 targeted tests pass (guest privacy, proximity, offline geo, import locations); frontend JavaScript syntax check passes. These are local tests, not Neon-copy or deployment verification.


## Follow-up audit and implementation, 9 October 2026
Supersedes the historical 99-entry baseline and coordinate-fingerprint concern above.
The last observed Vercel SQL status result reported active batch
`8e7d7758-6c76-4fb3-9803-825cc1f77567`, 103 entries and 13 offers.
Entry fingerprint: `a0c23f2d2019f448345824ef1e244efaaa3cf444f10b76256a7f9b4a71ad46aa`.
Offer fingerprint: `2a3b5859b77acfcd406614c7d2f3c49d2a4d9877edd2ea4c957067c0956976cd`.
This is observed prior-session evidence, not a new query in this change.
The user authorized direct Vercel database work without creating a copy; that overrides
his earlier copy requirement for this requested work. No branch-copy test is claimed.
No live mutation has been executed in this follow-up.

The importer now validates a mapping against the original input source fingerprint OR
the exact enriched fingerprint. Only deterministic derived coordinates are added after
the original-source hash is captured. Source price, scope, name, date and other edits
still withhold mappings. No mapping hashes or prices were rewritten.
The local 74-entry repository fixture stages 57 offers with zero withheld mappings;
this is NOT a live replacement package. Do not replace the live 103-entry catalog
with either the 74-entry seed or older 99-entry bundle.

Remaining execution requirements: obtain the complete current 103-entry source,
pin source/mapping hashes, review the resulting differences and unresolved locations,
commit the exact execution/rollback package and record its approved scope. Live
publication, historical guest preference deletion, platform logging verification and
deployed browser QA remain outstanding. Directory sync remains paused.
