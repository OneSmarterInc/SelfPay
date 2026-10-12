# Complete remaining nearest-facility work

Status: COMPLETED — live publication and classic/agent browser checks verified on 2026-10-09.

Authorization: the user requested “now do remaning thing completly” after the remaining offer import, location research, privacy verification, and live Dayton checks were explicitly listed. The earlier user instruction to work directly in Vercel Storage without a Neon copy persists. No Neon-copy test or independent Vikram identity verification is claimed. Code remains in PR #12; no main merge or production deployment.

Target: neondb, Neon branch br-rapid-mouse-b7clh18t. Prior active batch: 85c7c95d-a9dd-5533-9427-6fdcefc74ab9. Intended batch: 395c84be-d26d-5432-bddb-bff7c58c1200.

Exact SQL/source package commit: `f32972320fbabd1e7fdc7d7671dacc1a85384d0e`. Files:
- ops/sql/publish-remaining-2026-10-09.sql
- ops/sql/rollback-remaining-2026-10-09.sql
- ops/sql/verify-coordinates-2026-10-09.sql

## Reviewed differences

Preserve all 103 entries and all 13 existing offers byte-for-byte except geography in two entries. Add 44 existing repository mappings, for 57 total: 22 fixed, 2 starting, 1 range, 1 conflict, 1 maximum and 30 quote-required. These are not 57 fixed prices. Original mapping hashes match the complete current source before deterministic geography enrichment; no source/price hashes were bypassed or rewritten.

The original directory sync preserves the existing offers and never imports seed/mappings.json. That is why 13 remained live while the repository held 57 mappings. This explicit manual publication completes the reviewed mappings import.

The source package is the 103-entry public catalog observed in Vercel Storage, not the smaller 74-entry repository seed. Its source and mappings hashes are in remaining-stage-report.json. The report's original added/changed counts describe staging into an empty disposable SQLite database; the separate added_entries/changed_entries/removed_entries fields describe the reviewed live delta (0/2/0).

Two geography refinements use official provider sources checked 2026-10-09:
- https://www.imaginghealthcare.com/locations/la-jolla/ lists 4150 Regents Park Row, Suite 195, La Jolla CA 92037. Existing other city locations are preserved; only the unresolved La Jolla location is completed.
- https://mosaicdiagnostics.com/locations/ lists Bronx 10460, Brooklyn 11204, Howard Beach 11414 and Rockville Centre 11570. Mineola, Ronkonkoma and Deer Park are explicitly professional-services-only and are excluded. This proves geography, not branch price applicability. Offer region filtering remains in effect.

The result has 96 located entries, 7 programs and no unresolved import fragments. Broad/multi-site price offers can still be excluded from distance results where branch-level price applicability is unverified; they remain visible in National browsing.

## Safeguards and tests

Single atomic publication; locks; expected active batch, entry hashes, counts and offer fingerprint guards. No deletion, credential/grant change or sync activation. Old batch retained for rollback. Local search tests cover Kettering, 45402 and the conversational interface. Exact SQL and rollback are tested against disposable PostgreSQL in GitHub CI, preserving every expected row.

## Privacy

Search/agent use POST bodies, not location-bearing URL queries. Application access logs are suppressed; no guest preference reads/writes or browser geolocation. No new external analytics service is configured. Welcome text corrected to stop claiming guest location preferences are stored. Vercel runtime request detail inspected on 2026-10-09: POST /api/search, status 200, one function log containing method/path/status only, no request body or searched location. Team Settings → Drains shows “Upgrade to Pro to create your first Drain”; no external drains configured. This verifies the current supported app flow and visible platform logs, not undisclosed provider-internal retention or arbitrary manually constructed URLs.

## Execution and verification

CI passed: https://github.com/OneSmarterInc/SelfPay/actions/runs/37927709339 (job 113810549887). 215 tests collected in discovery; 26 application PostgreSQL tests; 51 directory PostgreSQL tests, including exact publication, rollback and changed-source rejection. Live SQL executed through the authenticated Vercel Storage query UI after exact editor/committed-file comparison (64,150 characters). Verification returned active batch `395c84be-d26d-5432-bddb-bff7c58c1200`, 103 entries, 57 offers, 96 located entries. Read-only editor mode restored. Previous batch remains intact.

Live browser checks at https://myselfpay-review-git-fix-nearest-f-6fc58d-1smarterincs-projects.vercel.app/:
- Catalog loads 103 entries / 57 mapped offers.
- Kettering MRI/knee returns 8 offers, including Precision Dayton, DOC Imaging, Precision North Dayton, and ProScan Vandalia. Rounded displayed distances approximately 1, 5, 10 and 15 miles; regression assertions use unrounded distances under 15.
- ZIP 45402 returns the same four nearby facilities at approximately 6, 7, 6 and 10 miles.
- Ask MySelfPay, “knee MRI near Kettering, OH”, returns the same nearby candidates and asks for contrast clarification.
- New welcome copy correctly says searched locations are not saved.

No production code deployment or main merge. Directory sync remains paused. No database entries, historical guest preferences, or other member data were deleted. Historical guest-preference deletion is a separate privacy-maintenance action, not a prerequisite for this new search flow; it requires its own explicit irreversible-deletion confirmation.


## Owner confirmation supplied 12 October 2026

The user-provided MySelfPay-backup-tasks(2).md states: "Vikram confirmed the approvals and the copy-test waiver on Oct 9 at 11:09 am ET." Recorded as supplied owner confirmation (2026-10-09 15:09 UTC). This addendum does not claim a branch-copy test occurred or alter the original execution evidence. Future live writes still require a newly created and verified backup under POLICY.md.
