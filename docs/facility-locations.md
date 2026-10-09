# Facility coordinates at import time

`python import_directory.py stage workbook.xlsx --mappings mappings.json` now derives and validates `locations` before storing each staged entry. No live data is modified until a separately approved publish. Existing live-change policy still applies to staging on live Neon.

Every staged entry contains:

- `locations`: list of city, state, optional five-digit ZIP, latitude, longitude and precision (`city`, `zip`, or reserved `address`).
- `location_type`: `site`, `program`, or `unresolved`.

Coordinates come only from bundled Census files. ZIP has priority; otherwise an exact city/state match is required. Spelling suggestions are not accepted automatically. Coordinates supplied in JSON are recomputed; address geocoding is not implemented. ZIP reference points can be outside a particular facility's town and never represent an exact facility address.

Semicolons and slashes separate cities. `City, ST` supports explicit state qualification. Structured JSON `locations` can supply city/state/ZIP for complex multi-state entries. A top-level JSON `zip` also works. The legacy workbook has no ZIP column: ZIPs embedded in its area field are recognized. Otherwise its existing city/state columns are used. Preserve leading zeros when preparing ZIP values.

National/nationwide area entries and explicitly marked `location_type: program` entries have an empty locations list. Multi-state entries with an empty area and a program/network entity are also marked program. Unclear regional coverage is reported for review, not guessed to be a site or program.

The stage report includes `location_count`, `program_count`, and `unplaced_entries` with entry names, unresolved fragments, reasons and successfully placed counts. Partial entries keep their verified locations. Empty locations are allowed only with the appropriate status; the locations field itself is mandatory in staged data.

Important coverage example: the bundled places Gazetteer resolves Waterbury, CT, but does not contain Prospect or Southbury, CT (not all New England towns are represented as Census places). All three fragments are processed independently; the two missing towns appear in the report. Supply verified ZIPs in structured inputs or review a future county-subdivision dataset addition. Never substitute a similarly named town in another state.

Enrichment changes entry fingerprints. Existing price mappings may therefore be withheld until reviewed against the new entry hash. No mapping is automatically rewritten, copied across locations, or broadened. No database schema migration is needed because locations live in each entry's JSON payload. Re-stage the reviewed source to populate existing entries; the deployed catalog is not backfilled automatically.

Run `python -m unittest test_facility_locations test_geo -v`. Tests use temporary SQLite and synthetic entries; no Neon connection, publication, or external geocoding occurs.
