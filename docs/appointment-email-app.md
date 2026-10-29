# Appointment requests through the user’s email app

No SMTP service, account registration, email verification, or booking schema migration. Clicking Book appointment opens a local form. Submission opens a mailto draft. The user must press Send in their email app. MySelfPay cannot detect sending or delivery, or reserve appointments. An email app must be configured; copyable recipient/subject/body remain on screen if it is not.

Form values stay in page memory and are not sent to our API or saved in local storage. Center recipient comes from the listing. Buttons require a valid single email plus scheduling-purpose metadata (excluding billing, referral-only, privacy and other unsuitable purposes), or explicit appointment_email_approved=true. Do not label every imported email as approved.

Test link: /#booking-test. Requires the separately approved inactive test batch booking-test-20261029. The endpoint reads only that test record; the active directory and provider count remain unchanged. Test data is visibly labeled, with no invented address, coordinates, prices or services. Pending live insertion follows ops/change-records/2026-10-29-booking-email-test.md. Only synthetic form details should be used for testing.

Supersedes the SMTP/account draft in PR #47. Do not merge or activate that earlier implementation.

Validation: node test_ui.mjs; node --check static/app.js; python -m py_compile server.py. Mailto tests validate encoding, recipient handling, form rendering and past-date rejection. They are not proof of an installed mail app or delivery.
