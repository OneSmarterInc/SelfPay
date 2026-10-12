# Dated Git backups — revised user scope

On 12 October 2026 the user requested a new branch named for each day, containing only that day's dump, and explicitly confirmed encryption. This supersedes the proposed Vercel Blob destination and related token requirements in earlier activation records.

Implementation in PR #15: backup-YYYY-MM-DD (India date at export start), single database-YYYY-MM-DD.dump.age, parentless commit, duplicate-date refusal, 08:00 IST daily workflow. No automatic deletion, Blob provisioning, or application files on generated backup branches. Owner-held age private key required for recovery.

Three local tests passed using a ciphertext fixture and real local Git, not live data. No actual date branch or encrypted live dump has yet been created. Missing read-only backup credential and age public recipient block activation; workflow remains gated and PR unmerged. No encrypted dump recovery is claimed. Earlier verified Neon baseline and PITR evidence remain valid for those separate operations.
