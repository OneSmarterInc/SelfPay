# Reviewer access plan — proposal, not implemented

Current decision: keep one-click guest access for synthetic review. Do not restore
email/password registration merely to satisfy the older audit instructions.

## Proposed restricted-review flow

1. Restrict the existing Vercel Preview to approved reviewers using the project's
   available deployment protection and invitations. Confirm available plan features.
2. Once admitted to the Preview, reviewers click Sign in as guest. Keep isolated
   guest histories and eight-hour sessions. A shared guest identity is not acceptable.
3. If app-level invitations are later required, an administrator invites a specific
   email. Use an approved identity provider or a short-lived, single-use link with
   stored hashed tokens, expiry and atomic redemption; do not trust a typed email.
4. Define who grants/revokes invitations and how reviewer access is audited. Revocation
   must invalidate sessions, not merely hide buttons. Validate ownership on every API.
5. For real members, replace review access with customer-approved enrollment/SSO and
   tenant assignment. Guests must not select their own health-plan tenant.

## Free text and health information

Guest access does not prevent someone entering health information. The current app
stores chat and correction text. Synthetic-only labels are instructions, not detection.
Before real use, approve whether to retain this text, for how long, who may read it,
and how access/deletion and backups are audited. Disabling text storage is a possible
review configuration but changes saved-conversation behavior and needs product approval.
Regex filtering cannot reliably guarantee removal of health information.

## Open decisions

- Owner and approved reviewer list; deployment-protection configuration and plan.
- Whether invitations are needed at the hosting layer or inside the application.
- Free-text storage decision, guest preference/correction retention and backup policy.
- Confirmed vendor agreements and infrastructure eligibility before real health data.

No invitation emails are sent and no hosting plan is changed by this proposal.
