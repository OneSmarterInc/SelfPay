# Guest tier — October 7 decision

One review PR; do not merge or promote until reviewed. Premium is not implemented.

## Final limits

| Limit | Value | Configuration |
|---|---|---|
| Conversations per guest session | 3 | server.GUEST_CONVERSATIONS |
| User messages per conversation | 5 | server.GUEST_MESSAGES |
| Characters per message | 500 Unicode code points | server.GUEST_MESSAGE_CHARACTERS |
| Agent messages per IP/hour | 30 | server.GUEST_AGENT_PER_IP_HOUR |
| Agent messages globally/day | 2,000 | server.GUEST_AGENT_GLOBAL_DAY |
| Guest creation requests per IP/minute | 20 | server.LIMITS guest_ip |
| New guests globally/hour | 200 | GUEST_GLOBAL_PER_HOUR environment variable |
| New guests globally/day | 2,000 | GUEST_GLOBAL_PER_DAY environment variable |

Hourly/daily windows are UTC clock windows, not rolling windows. Change UI limits
alongside server constants if changing the per-session experience. Old
GUEST_GLOBAL_PER_MINUTE is no longer used. Remove/replace an existing
GUEST_GLOBAL_PER_DAY=1000 override to use the new 2000 default.

A conversation starts with its first accepted message. The server issues its ID;
subsequent messages must use that ID in the same session. New conversation clears
page-local messages and the first subsequent accepted send consumes a new slot.
Refresh clears text but reloads counts and the last conversation ID. Counts sent
by clients are ignored. Concurrent requests are serialized in the database.
Rate-limited sends consume no successful-message quota. A 429 disables the chat
until refresh/new session as appropriate; classic search remains usable.

## Data policy

Guest message/search text is processed but never written by these routes to the
database or browser persistent storage. guest_usage contains only session/member
IDs and conversation ID/count pairs. IP limits store hashed keys and counts.
History reads return empty, history writes and correction reports return 403.
Preferences accept only exact catalog location labels. Old free-text preferences
are not returned to guests. Old guest content is not automatically purged while
sessions remain active; cleanup removes it when no live session remains.

Cleanup deletes guests with no live sessions even if old conversations are
unexpired; dependencies are removed first, including usage rows. login_limits
retains 48 hours so hourly/daily quotas cannot be reset by minute-counter pruning.
Application functions and tests for password register/login/change_password and
PBKDF2 have been removed. Historical member columns remain to avoid a destructive
schema migration. Existing non-guest fixture records are not a premium product.

## Existing database upgrade and review

Run ops/upgrade_guest_tier.sql as database owner against the intended Preview
database before opening the Preview. Or run setup_hosted.py with that database
as owner; initialization creates the new table without resetting member data.
Update restricted cleanup role grants for guest_usage if the role already exists.
If Preview shares the Production database, use an isolated Preview branch to test.
No live database migration has been executed by this PR.

Run test_functional, test_hosted, test_cleanup, test_guest_limits, test_guest_tier,
test_postgres (throwaway database only), and node test_ui.mjs. CI exercises real
PostgreSQL; client tests use a stub DOM and do not establish browser visual QA.
Test 6th message, 4th conversation, 501 characters, refresh, concurrent sends,
new IP after global quota, hour/day rollover, blocked saves/corrections, location
validation, and cleanup of usage/preferences/old guest content.

## External completion still required

Vercel Deployment Protection: Settings → Deployment Protection → enable Vercel
Authentication for Preview (or Standard Protection), save, then verify the plain
Preview URL in a signed-out/incognito browser redirects to Vercel authentication.
The connected Vercel account cannot access the project, so this setting has not
been changed or evidenced. Do not call it completed. Do not share bypass tokens.
The cleanup database secret/role and successful scheduled execution likewise need
owner verification. No production promotion is authorized.
