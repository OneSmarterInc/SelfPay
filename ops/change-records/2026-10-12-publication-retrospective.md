# Retrospective: October 9 active catalog publication

Status: PARTIAL EVIDENCE — owner review requested; operator and SQL unverified.
This record is not retrospective approval and does not authorize live writes.

## Evidence source

Read the already-existing SQL backup from SelfPay's `backup-2026-10-12`, commit
`63071bc9f7b756cef4a2ba7a44fdcbbf87177939`, file `database-2026-10-12.sql`, Git blob
`9f36b0e0018622c62d8f1c2e8c7c1d8867890a6e`. Inspected its COPY sections locally;
no fresh live SQL was executed for this investigation. This establishes the
state captured by that backup, not subsequent live changes.

## What changed and when

`publish_events` row 9 records a publish at **2026-10-09T16:05:44.112383Z**
(21:35:44 IST), from batch `395c84be-d26d-5432-bddb-bff7c58c1200` to batch
`4974b4d5-143c-4bf2-a198-28d4e366ecd9`.

The new batch was created at 2026-10-09T16:02:03.048567Z with source_name
`US_Self_Pay_Imaging_Directory.xlsx`. A source-name label alone does not prove
which importer, SQL statement, or person performed the operation.

Entry comparison: **103 to 105; two additions, zero removals, zero changed
payloads among the existing 103 entries.** Additions:

- Advanced Radiology — Fleet Street
  (`48364be406bde50b5d00c6dd889b19c49e4fb1b87d2742e0d1637ba301654686`)
- Advanced Radiology — Maiden Choice Imaging Center
  (`d7adf9478b2d8c30156f2aa177de4f1e767d66ae956eaa05501dd55f66d6d060`)

## Unresolved attribution and safeguards

- Who ran it: **unknown**. The publish_events schema has no actor column. A Git
  commit author would not establish the database operator.
- Exact SQL and executing commit: **unknown**. No query-history evidence has been
  obtained. Vercel/Neon query and branch histories still need review.
- Backup before this publication: **not established**. The verified baseline
  `br-gentle-moon-b74wdsig` was created on 12 October at 08:46:32Z, after the
  October 9 publication. It cannot count as a preceding backup.

No further live writes until the owner has read this record, as required by
section A of MySelfPay-dev-tasks-2026-10-12.md. Missing evidence remains open;
do not fill it with assumptions or declare the audit complete.

## October 14 follow-up

A targeted search of available session context and workspace files did not locate
the original October 9 16:00–16:10 UTC execution log. Retrieved task documents
request the evidence but do not supply it. Operator, exact executing SQL and
approval remain unverified. See 2026-10-14-dev-task-status.md for the separate
Vercel creator-account evidence; it does not identify the database publisher.
