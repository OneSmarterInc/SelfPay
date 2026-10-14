# Restore input safety follow-up — 2026-10-14

Removed four preselected defaults from database-restore.yml: historical backup date, backup commit, old disposable branch ID and old hostname. All four inputs remain required. Each drill must explicitly select a reviewed immutable backup and a currently verified isolated target. Commit e7398d7e10d8e5255cf3d74f8ad9a1cde2fbad8f was read back and verified; no other workflow logic changed. No restore or Actions job dispatched.

Current backup publisher source confirms fixed destination OneSmarterInc/MySelfPay_Backup, private-repository and push-permission checks before upload, no overwrite of a dated backup, and guarded retention. This is source verification, not verification of current secret values or a successful fresh export.

The owner rotation and same-code redeployment are recorded in 2026-10-14-post-rotation-verification.md. Complete old-credential invalidation/dependent-configuration verification remains open. The potentially exposed password is no longer available for testing and must not be recovered from diagnostic logs or requested in chat merely to test it.

Cleanup and daily activation remain blocked on original creation evidence for each of the four member IDs; no data was deleted. Original October 9 session log remains missing. Monthly recovery review is scheduled; actual restore/PITR drill remains pending. Paid rulesets remain unavailable under the no-paid-upgrade constraint. Production, credentials, billing, $0 Actions budget and Usage blocked unchanged by this follow-up.
