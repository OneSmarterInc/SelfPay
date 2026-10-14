# Production credential containment maintenance preflight

Date: October 14, 2026. Status: BLOCKED BEFORE MUTATION.

Owner explicitly approved a brief maintenance window, coordinated credential rotation and dependent Production variable updates, redeployment of the currently deployed code only, verification, and documented recovery. No data edits or billing changes authorized.

## Verified target

Browser production overview identifies deployment dpl_32kg64VmPERotu7wY8j9i5Zar8sk, commit ae1b9ef09de5eefc86fe4e18779a891c46190447, branch fix/restore-stage-diagnostics, status Ready. No newer main code may be substituted. Ready is deployment status, not a fresh functional health test.

Neon management metadata confirms neondb_owner exists on production br-rapid-mouse-b7clh18t in project late-grass-13270808, alongside selfpay_backup_reader and directory/cleanup roles. No password was retrieved or changed in this preflight. Prior equality comparison confirmed exposure; no subsequent containment is verified.

Read core.py, postgres_store.py, api/index.py and server.py at the exact deployed commit. The inspected application connection path uses DATABASE_URL; the serverless store requires the pooled connection. Other integration variables are present but were not found as connection inputs in these files.

Browser environment metadata shows DATABASE_URL and DATABASE_URL_UNPOOLED, POSTGRES_URL, POSTGRES_URL_NON_POOLING, POSTGRES_URL_NO_SSL, POSTGRES_PRISMA_URL, PGPASSWORD, POSTGRES_PASSWORD and related host/user/database keys managed by Neon, scoped to Production and Preview. Values were not revealed or copied. Provider-wide rotation may therefore affect Preview too; a Production-only update path has not been established.

## Execution blocker

Vercel connector still returns 404 for the verified project ID and deployment ID with the verified team ID. Browser access works, but browser credential changes require user handoff under the browser safety rules. Do not rotate using Neon first while dependent secret updates cannot be completed and verified safely. No alternate API, session extraction, or browser backend requests were used.

## Recovery procedure before execution

1. Restore authorized connector access or arrange a coordinated user-performed credential update; confirm the intended scope of shared Production/Preview integration variables.
2. Pin deployment source to ae1b9ef09de5eefc86fe4e18779a891c46190447 and verify the redeploy operation retains that exact revision.
3. Prepare fresh credentials and all dependent updates without displaying values. Do not expose credentials in source, command arguments, diagnostics, screenshots or logs.
4. Complete coordinated rotation/update and deploy the pinned code. Verify database connectivity and read-only critical functionality. Avoid functional tests that create sessions, guest usage or other records under the owner's no-record-modification restriction.
5. If mutation fails, stop further unrelated changes and report the exact stage. Recover forward with an unexposed credential and the same known application revision. Never roll back to an exposed password or select an old deployment whose embedded environment still uses it. If connection integrity cannot be restored, obtain/perform the specifically authorized service-isolation step rather than claiming containment.

No rotation, environment update, redeployment, data mutation, backup activation or billing change occurred. No downtime was introduced by this inspection. Existing service health has not been independently tested in this preflight. The previously confirmed production credential exposure remains unresolved. No new executable code was changed; no post-change tests are claimed.
