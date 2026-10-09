# Nearest-facility checklist — completed implementation and verification

Updated 9 October 2026. Scope: MySelfPay-nearest-facility-tasks.md, items 1–29. Code stays in PR #12. Production code has not been deployed.

| Task group | Result and evidence |
|---|---|
| A, items 1–3 | Bundled Census city/ZIP lookup; offline resolution and ambiguity handling; socket-blocked search tests pass. |
| B, items 4–8 | Import-time coordinates, ZIP preference, multi-city splitting, program classification and validation. Live catalog: 96 located entries, 7 programs; no unresolved import fragments. |
| C, items 9–17 | Distance ordering; 25/50/100/250-mile radii; 3-nearest fallback; approximate straight-line labels; separate programs and quote leads; shared agent search; unknown-place ZIP prompt. Automated acceptance tests pass. |
| D, items 18–19 | Guest location preference access blocked; no browser geolocation; locations sent in POST bodies, not URL queries. Inspected Vercel search logs contain method/path/status without location/body. No external drains configured. |
| E, item 20 | Directory sync preserved the existing 13 offers; it never loaded the expanded seed mappings. Full explanation in the change records. |
| E, item 21 | Completed atomic manual publication: all 103 entries preserved, 44 mappings added, original 13 unchanged. 57 mappings include 30 quote-required listings, not 57 fixed prices. |
| F, items 22–28 | Tests cover Kettering, 45402, Springfield, nearest fallback, program grouping, known distance, and zero network calls. Kettering/45402 plus agent flow also verified in deployed Preview against live data. |
| F, item 29 | One follow-up PR (#12), no direct main push in this work. Existing prior main changes remain historical. Full CI passes. |

## Live publication

Active batch: `395c84be-d26d-5432-bddb-bff7c58c1200`.
103 directory entries, 57 mapped offers, 96 located entries, 130 location points and 7 programs.
Prior batch: `85c7c95d-a9dd-5533-9427-6fdcefc74ab9`, retained for rollback.
Exact SQL commit: `f32972320fbabd1e7fdc7d7671dacc1a85384d0e`.
Record: `ops/change-records/2026-10-09-remaining-publication.md`.
The user explicitly directed work in live Vercel Storage without a Neon branch copy. Tests used disposable local PostgreSQL in CI; no Neon-copy test is claimed.

## Verification

CI: https://github.com/OneSmarterInc/SelfPay/actions/runs/37927709339
215 tests collected; database-only tests skipped in SQLite discovery are exercised by the separate PostgreSQL jobs (26 application tests and 51 directory tests). Client workflow tests pass.

Preview: https://myselfpay-review-git-fix-nearest-f-6fc58d-1smarterincs-projects.vercel.app/
Kettering and ZIP 45402 return the expected four Dayton-area facilities. Ask MySelfPay gives the same nearby candidates and requests missing contrast information. Boise verification from the prior coordinate publication remains covered by regression tests.

## Data and privacy boundaries

- Source dates, exclusions, fee scope and quote-required classifications are retained. No fresh price verification or contracted-network claim is implied.
- Mosaic professional-services-only sites are excluded. La Jolla ZIP verified against the official location page. Evidence is pinned in seed/facility-location-evidence.json.
- Some multi-site offers still lack branch-specific price applicability. They are intentionally omitted from distance-priced results and available under National; facility coordinates do not establish a price at every branch.
- Visible runtime log and drain checks verify the supported app flow, not undisclosed provider-internal retention or arbitrary URLs submitted outside the app.
- Historical guest preference deletion is separate from the nearest-facility checklist and was not performed. Production promotion and PR merge remain separate release actions.
- Directory sync stays paused; directory-data remains separate.
