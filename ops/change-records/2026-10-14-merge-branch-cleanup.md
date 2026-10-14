# Merge and branch cleanup — October 14, 2026

Owner requested remaining changes merged into main and unnecessary branches deleted. This supersedes the earlier Android draft hold for source merging; it does not authorize an app-store submission or newer production deployment.

Merged PR #21 at 1da747a9cbf77de60a3af5f3202904ba9dc6f0c4 after resolving conflicts in branch commit b33e648792aad91e542735a81b170116d2a89280. Resolution starts from main 61fd43e8a4dd4d7eaacc0cd4084f8c2c68455ed4, adds the reviewed Android files/workflow and preserves main's PWA, documentation, shared generator and deployment controls. Added explicit disabled Vercel deployment for feature/android-apk. All other main contents preserved. Two shared app-config tests passed. Nineteen existing backup unit tests passed. Java/Android toolchain was unavailable locally; no fresh APK build, device test or store submission claimed. Merge used skip-ci to avoid unrequested builds.

Deleted branches via GitHub's recoverable Delete branch UI; Restore controls verified:
- feature/android-apk (merged PR #21), b33e648792aad91e542735a81b170116d2a89280
- feature/cross-platform-pwa (merged PR #22), 702902fde9abd4ca91ac81e7984ebcf3c2c60302
- feature/ios-app (merged PR #23), d64d5110d3d2933b0a1ef8fcefe054881e0f69a0
- ops/complete-backup-records-2026-10-12 (merged PR #19), 55e587d86af25afd74e54ee7ea497b03b5a74944
- docs/oct12-test-user-correction (merged PR #17), ebcd0c426e0368fcbb4f248fa8a8caecf5daf385
- fix/search-coverage-summary-card (merged PR #18), 04694c96b2131c6ad2a060558a591747398db471
- fix/oct12-review-and-private-backups (merged PR #16), 1eedf68b4d25e313cc8e0a18cd2c25fd0bfc8e55
- fix/backup-publish-diagnostics, 21ba0f87b57abfaf6c27c07fd042ce3ab2d4d14a. Its only changed file ops/backup/git_backup.py was independently read from the branch and main and found byte-for-byte identical.

Remaining branches verified in refreshed GitHub UI: main, directory-data, fix/restore-stage-diagnostics. directory-data is preserved under operating policy; fix/restore-stage-diagnostics remains the currently deployed revision reference while credential recovery is unfinished. No open PRs remained after the Android merge.

No backup-repository branches, Neon recovery branches or database records were deleted. No production deployment, credential rotation, paid-service activation or budget change occurred. Credential containment still needs authorized usable access/user credential handoff; synthetic-account deletion remains blocked on original test-creation evidence. Daily backups remain disabled. October 9 attribution evidence remains outstanding.
