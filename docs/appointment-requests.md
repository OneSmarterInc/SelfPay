# Appointment requests — deployment and acceptance

Status: implemented for testing; disabled by default. No live email has been sent.

## User flow
An approved center contact enables Book appointment beside Website. Guests enter their name/email, accept Terms & Privacy, and verify a six-digit email code. Verification creates a booking account or signs an existing booking account in. No password is stored for these accounts. Existing non-booking accounts are not silently converted. The center selection is retained.

The form requests name, phone, service, preferred date/time and the center's US time zone. It displays the verified reply email and requires consent to email these details. No medical attachments, diagnosis, insurance information or free-text medical history. Submission requests an appointment; availability is not reserved. Email-service acceptance is not proof of inbox delivery or a confirmed booking.

## Configuration — never commit secrets
BOOKING_ENABLED defaults off. Enable only after migration and acceptance.
SMTP_HOST, SMTP_PORT (465 implicit TLS or 587 STARTTLS), SMTP_USER, SMTP_PASSWORD.
BOOKING_FROM_EMAIL: an authorized sender on the configured mail service.
BOOKING_AUTH_SECRET: independent random secret, at least 32 characters.
BOOKING_CONTACTS_JSON: mapping of active entry keys to objects with email, purpose=appointment_requests and evidence_url (HTTPS). Recipient must also match the imported email field. Review location coverage and contact purpose before approval. Do not authorize privacy, media, billing-only, referral-only or unrelated addresses. Never accept the recipient from client form input.

Use an existing authorized email service only; no paid service or plan changes are included. Configure credentials through the hosting secret interface, not chat or commits. The owner must provide the sender identity and service choice. Production mail acceptance requires an explicitly authorized test destination; do not test against imaging centers without permission.

## Database migration and rollback
Apply ops/sql/20261029-booking-schema.sql only under repository change control: exact committed SQL, isolated Neon rehearsal, explicit production approval and fresh verified backup. Do not initialize hosted schema at application startup.
Rollback application activation by setting BOOKING_ENABLED=false. Preserve booking_codes and booking_requests for audit; do not delete member data. The migration adds tables and leaves all directory and existing account data unchanged.

## Storage, delivery and limits
Pending name/email and a hashed code are stored for verification, with ten-minute code validity, five attempts and one-time use. Verified accounts are stored in members. Booking requests retain request ID, member ID, center key, payload hash, status and timestamp; the form's phone/date/service body is not stored in the request table, but is transmitted by email. A mail timeout has unknown delivery status and is not automatically retried. Repeated submission with the same request ID cannot send another message. Stale sending status must be checked with the mail provider before any manual retry.
Auth has per-IP, per-email and global rate limits. Booking submission has per-IP/session route limiting, per-member and global daily limits. All messages use TLS SMTP and avoid diagnostic logging of secrets or form contents.

## Remaining activation prerequisites
1. Owner chooses authorized sender/mail service and configures secrets securely.
2. Review center recipients and populate the approved mapping with evidence.
3. Approve/test the database migration before production activation.
4. Review/update Terms & Privacy for real accounts and email appointment requests, establish retention/deletion for pending codes and booking metadata, and approve real-data backup handling. Existing synthetic-only export restrictions must remain in force.
5. Test the guest-to-verified-account flow and email delivery to an authorized test mailbox, including retries and failures. Then verify mobile/card rendering.
6. Only then enable BOOKING_ENABLED in production. Keep the Actions $0 budget unchanged.

## Tests
python -m unittest test_booking -v
node --check static/app.js
Focused tests use synthetic SQLite data and mocked email; they are not evidence of live SMTP delivery.
