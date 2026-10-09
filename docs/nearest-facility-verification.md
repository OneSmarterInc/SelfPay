# Nearest-facility checklist: implementation and evidence

9 October 2026. Code review PR; no production deployment or live mutation.

## Completed in code
- Offline Census lookup, state disambiguation, city/ZIP coordinates, distance and radius UI.
- Import-time extraction of ZIPs from source addresses, multi-city lists, program classification.
- Original source fingerprint checks remain mandatory for unchanged legacy offer mappings.
- National coverage is inferred only from explicit nationwide evidence; "Multiple" alone is not evidence of coverage in every state.
- Quote leads exclude explicitly unavailable/unverified services and listings already represented in results.
- Naugatuck Valley Radiology's three sites have source-pinned ZIP evidence in seed/facility-location-evidence.json. Source: https://www.nvranet.com/ (checked 2026-10-09). This evidence establishes geography only, never price scope. No external requests occur during import or search.
- Guest location preference reads/writes are blocked; no browser geolocation.
- New acceptance tests exercise real Dayton records from Kettering and 45402, Springfield ambiguity, a 250-mile fallback, a real nationwide program, Dayton/Cincinnati distance, and socket-blocked full search and agent execution.
- CI now discovers all Python tests, including geography and acceptance tests.

## Local verification
`python -m unittest discover -q`: 207 collected, 152 passed, 55 skipped (database integration configuration unavailable locally).
`node test_ui.mjs`: passed with a stub transport; not visual browser testing.
Dayton/Cincinnati city reference points: approximately 47.44 straight-line miles.
The four Dayton-area fixture offers are under 15 miles from Kettering and from ZIP 45402.
Local stage report: ops/change-records/nearest-local-stage-report.json.

## Still outstanding
- Live 103-entry source package, approved publication and historical guest-preference cleanup.
- Live platform logging configuration and deployed browser verification.
- PostgreSQL integration suites must pass in CI; local skips are not passes.
- La Jolla and the broad NYC/Long Island entry still require source-supported fixed-site locations. The importer reports these as unresolved rather than inventing coordinates.
- The repository seed contains 74 entries, not the live 103. It must not overwrite live data.

Earlier changes had already gone directly to main. This follow-up uses one PR; it does not undo that historical process deviation. Keep directory-data separate and Directory sync paused.
