# Backup activation — approval and secure setup pending

Status: PREPARED, NOT EXECUTED.

## Concrete proposed access
- Database: neondb in Neon project late-grass-13270808, live br-rapid-mouse-b7clh18t.
- New role selfpay_backup_reader: CONNECT and pg_read_all_data, default read-only transactions; no ownership/admin/BYPASSRLS. Initially NOLOGIN, with no password.
- Exact preparation SQL: ops/sql/create-backup-reader.sql at f93a213fcc049d8f3dfb55b139ed75a3acc2b089.
- A separate branch test and privilege audit must precede live execution. Audit inherited/PUBLIC write and SECURITY DEFINER access; do not claim this SQL alone proves read-only access. A fresh backup and matching counts are required before live grants.
- Proposed destination: dedicated private Vercel Blob store myselfpay-encrypted-backups, US East region iad1, under the existing Vercel team. Synthetic/test data only. No paid plan purchase is authorized.
- Proposed recipient of credentials: GitHub environment database-backups in OneSmarterInc/SelfPay, used only by the reviewed backup workflow.
- BACKUP_DATABASE_URL grants the dedicated login read access. BLOB_READ_WRITE_TOKEN grants access only to the dedicated private backup store. Both belong in environment secrets, never chat/source.
- BACKUP_AGE_RECIPIENT is a public encryption recipient; the matching private key stays in the owner's recovery vault. Operator must generate and retain that key, and prove decryption.
- Daily schedule: 02:30 UTC. Retention deletes this workflow's encrypted copies older than 14 days after a new verified upload.
- User must confirm no real member data is present before first export; later introduction of real data requires renewed destination approval.

## Required user interaction
Browser security guidance requires action-time confirmation for new security-sensitive access, and user handoff for entering new authentication credentials. Repository POLICY.md independently requires reviewed exact SQL, branch testing and owner approval for live grants. These are the reasons setup is paused before granting access; existing Neon console access already works.

No role has been created by this record, no private store provisioned, no secret added, no export activated. Do not mark complete until an encrypted dump is uploaded, decrypted and restored successfully. Merge/activation and monthly restore automation remain separate completion gates.
