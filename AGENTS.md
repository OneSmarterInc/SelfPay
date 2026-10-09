# Repository operating instructions

Before any developer/administrator SQL operation against the live Neon database, follow [ops/change-records/POLICY.md](ops/change-records/POLICY.md).

- Require a change record approved by Vikram before live SQL, including read-only operational queries.
- Commit exact SQL files first and reference their full commit SHA in the record.
- Test each live change on a separate Neon branch copy and record the results before live approval/execution.
- Never treat a general request to fix an issue as approval of an unreviewed live SQL file.
- Preserve directory-data as a separate data branch. Keep Directory sync paused unless an approved activation record authorizes it.
- Do not claim approval, branch testing or live verification without evidence.
