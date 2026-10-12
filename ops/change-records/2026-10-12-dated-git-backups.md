# Dated Git backups — revised user scope

On 12 October 2026 the user requested a branch named for each day containing only that day's complete database dump, stored in Git. The latest explicit instruction is: "dont need to encryption store data directly". This supersedes the earlier encryption agreement, age-key requirements, and Vercel Blob destination. This user-directed exception to export encryption applies to this Git backup workflow; other database safeguards remain in place.

Implementation in PR #15: backup-YYYY-MM-DD (India date at export start), single unencrypted database-YYYY-MM-DD.sql, parentless commit, duplicate-date refusal, 08:00 IST daily workflow. No table filters are applied. Ownership and ACL restoration commands are excluded; cluster roles/passwords and external files are not included. No new backup database, Blob storage, automatic deletion, or application files on generated branches.

Three local tests passed using a SQL fixture and real local Git; Python compilation passed. These checks do not prove a live export or restore. No actual dated backup branch or live SQL dump has yet been created. A usable direct read-only database credential remains missing; the workflow is gated and PR unmerged. The synthetic-data gate remains. Earlier verified Neon baseline and PITR evidence describe separate completed operations, not this Git dump.
