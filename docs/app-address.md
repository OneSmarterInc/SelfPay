# App website address

`app-config.json` is the single reviewed website URL setting. It must be an HTTPS
root URL without credentials, query parameters, fragments, or nonstandard ports.
It currently remains https://myselfpay-review.vercel.app/.

The iOS project generator runs `tools/generate_app_config.py ios` before adding
Swift sources. Android's draft branch runs the same generator for Android before
compilation. Both derive internal-navigation host restrictions from that value.
Generated constants are ignored by Git. Changing the setting requires rebuilding
native apps; an already-uploaded IPA does not change remotely.

PWA PR #22 remains closed pending clarification of the owner's earlier cancellation
versus the October 14 task document. It currently uses same-origin relative URLs;
its integration with this setting is pending that decision. Do not claim all three
platforms have been migrated. No new app-store submission is authorized by this
record; build 4's prior owner-authorized upload remains historical fact.

Validation: configuration rejects unsafe origins; changing the setting changes both
generated constants. Swift/Android SDK compilation is not available in the local
review environment; no new runner or store upload was started for this change.
