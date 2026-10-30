# Appointment request flow

Book appointment opens a two-step form: select one to three future date/time
windows in the clinic's time zone, then review clinic, exam and price. The patient
provides first name, mobile number, personal email and contact consent. They must
receive and verify an email OTP before submitting. Slots are preferences, not
availability. Email verification proves inbox access, not patient identity.

## Email behavior

Patient OTP emails are real, branded multipart HTML/plain text messages, sent via
Proton SMTP with certificate-verified STARTTLS on port 587. The sender display name
is MySelfPay and the footer says "Please do not reply to this automated email."
SMTP settings live in local .env (Git-ignored) or hosted secret configuration.
Provider setup: https://proton.me/support/smtp-submission

Patient codes expire after 10 minutes, have five failed attempts, a 60-second resend
cooldown and owner/address/global send limits. A verified proof lasts 15 minutes,
is bound to the guest owner, and is consumed by one appointment request. Duplicate
submission retries return the same request. Codes are keyed hashes; email addresses
are encrypted. Codes and personal data are never logged or returned by the API.
SMTP failures do not mark an address verified. SMTP acceptance is not proof of inbox
delivery. Mail is submitted after committing the challenge, outside DB transactions.

Clinic appointment notifications use the null transport in booking.suppress. They
are never sent, spooled, or queued for later delivery, even when SMTP is configured.
The patient sees "Request sent" with the toast and notice "No email sent to clinic
(testing mode)". No appointment is reserved and no clinic callback is promised.
The recipient for future notifications is taken only from approved scheduling
metadata in the server catalog, never from a browser-supplied email address.
Missing/unapproved recipients remain empty. Suppressed previews must never be sent
retroactively when clinic delivery is enabled.

## Patient status and local clinic demonstration

The private patient link refreshes status every 15 seconds. A local-only "Preview
clinic workflow" displays the unsent clinic notification and a separate clinic link.
For the supplied portal design, the local clinic preview uses its own displayed test
code (never emailed to the clinic), a 72-hour link, single-use 10-minute code and
15-minute session. The hosted adapter does not expose test codes or preview links.

Clinic outcomes are Scheduled, Left voicemail and Cannot accommodate. Scheduled
and unable close the request; voicemail remains open. Requests otherwise expire
after 72 hours. Closing is final; Lock revokes the clinic session. The patient sees
status updates through the private request page. There are no SMS or additional
patient status emails in this implementation. Clinic staff perform scheduling
outside MySelfPay. No fax number, callback SLA or available slot is invented.

## Storage and retention

ops/booking-schema.sql defines the schema. Local startup initializes SQLite only.
Details, email addresses, clinic snapshots and raw capability links are encrypted
with Fernet. Hashed capabilities, status, timestamps and retry fingerprints remain
plaintext. SQLite write transactions and PostgreSQL row locks protect OTP and
status mutations; unique owner-scoped retry keys prevent duplicate submissions.

Local startup creates data/booking.key unless BOOKING_ENCRYPTION_KEY is configured.
Protect the hosted key separately from backups; losing it makes requests unreadable.
Patient request details are removed 30 days after closure. Expired email-verification
records are removed after one day. The local server cleans up at startup and hourly
while running. Manual command: `.\.venv\Scripts\python.exe booking.py --cleanup`.
Backups have a separate retention policy.

## Hosted rollout and future clinic mail

No live Neon SQL or production deployment is part of this local implementation.
Follow AGENTS.md and ops/change-records/POLICY.md before hosted schema changes:
review exact SQL, branch-copy testing, approval and backups. Hosted rollout must
provision BOOKING_ENCRYPTION_KEY and SMTP secrets and schedule the retention job.

Before enabling clinic delivery, verify scheduling recipients and introduce a
transactional outbox with bounded retries, delivery-failure monitoring and a reviewed
clinic access mechanism. Send only new live requests, never previous previews.
Do not send SMTP inside a database transaction. Exercise concurrent requests against
an isolated approved PostgreSQL branch before claiming production readiness.

## Verification

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest test_booking -v
node --check static/app.js
node test_ui.mjs
```

Tests cover patient OTP mail/expiry/replay/failure, owner-bound proofs, mandatory
verification, consent, slots, recipient restrictions, clinic SMTP suppression,
encrypted storage, retries, access isolation, CSRF/origin, clinic sessions and
retention. Browser tests use synthetic patient details and an explicitly chosen
recipient inbox for the OTP. This supersedes mailto without activating old PR #47.
