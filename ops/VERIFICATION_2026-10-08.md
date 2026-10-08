# Verification — 2026-10-08

Main was verified at 3899a5bee4a0f64ec70bbff9640f162e9f41e820 before this report commit. PR8 merged; PR9/10 closed unmerged; data branch kept separate.

GitHub Actions run https://github.com/OneSmarterInc/SelfPay/actions/runs/37798222860 succeeded on retry job 113400873024. Logs confirm SYNC_APPLY=false, verified=true, 99 entries, 13 offers, added=changed=removed=0. It reran original triggering main SHA 11f5398; this is proof of the restricted-secret workflow path after database repair, not newest-main CI coverage. Administrator SQL verification also passed. Installed recovery function MD5: 4183e25660850bb8c572500b078f02d4.

Canonical workbook libfile_8ba8491c8ff881918ed4868c0ee43465 version 10 was retrieved. SHA256 bcbb04024807f93943fde0dc55f439c466c1516e8231ccbc9e7ace67f5244c16. All 99 normalized entries exactly match the supplied database snapshot, including row fields. All 13 offer mappings match.

Fresh version-10 export passed importer validation and snapshot comparison. Archived on directory-data at directory/versions/v000010-1477a7680f15e2b32812a6f15fe4293c6f8ddb9e7e4302614045d3015c3340a0.json. Not activated. current.json retains the version-7 recovery metadata because the installed database guard pins that exact document and blocks live publishing.

Remaining: coordinated administrator database-guard migration plus current.json switch to the verified version-10 export, keeping dry-run-only enforcement; then verify that version through Actions. No direct database management connection is available to Codex. Recovery bundle expires 2026-10-09 10:28:42 UTC; v10 candidate expires 2026-10-10 15:46:37 UTC. Do not fake or refresh metadata to avoid freshness checks.

Reviewer acknowledgement remains external. No reviewer message was sent. No publishing was enabled and no catalog rows were changed. Project publishing-variable settings were not independently inspected.
